"""Offline deployment checks: no real keys, OTP email, or cloud writes."""
import json
from contextlib import contextmanager
from pathlib import Path
import pytest
from config import settings, BASE_DIR
from app import app, create_app
from extraction import vision_status, extract_document
from serverless_runtime import PostgresRuntime


def hosted_env(monkeypatch, tmp_path):
    for key,value in dict(VERCEL='1',APP_MODE='supabase',SECRET_KEY='isolated-test-key',
        COOKIE_SECURE='true',SUPABASE_URL='https://example.supabase.co',
        SUPABASE_PUBLISHABLE_KEY='test-public',SUPABASE_DB_URL='postgresql://test:placeholder@localhost/test',
        APP_INSTANCE_DIR=str(tmp_path/'never-created')).items():
        monkeypatch.setenv(key,value)


def test_exported_app():
    assert app.name == 'app'
    assert '/login' in {rule.rule for rule in app.url_map.iter_rules()}


def test_hosted_import_and_public_routes_without_disk_or_network(monkeypatch,tmp_path):
    hosted_env(monkeypatch,tmp_path)
    config=settings()
    assert config['EXTRACTION_ENGINE']=='ocr'
    assert config['UPLOAD_MAX_MB']==4
    assert not (tmp_path/'never-created').exists()
    application=create_app()
    assert isinstance(application.extensions['runtime'],PostgresRuntime)
    client=application.test_client()
    assert client.get('/').status_code==302
    assert client.get('/login').status_code==200
    assert client.get('/verify').status_code==302
    assert client.get('/static/style.css').status_code==200
    for route in ['/dashboard','/upload','/roles','/careers/full-stack-developer','/skills/react','/profile','/history']:
        assert client.get(route).status_code==302
    assert application.config['SESSION_COOKIE_SECURE'] is True
    assert not (tmp_path/'never-created').exists()
    assert vision_status(config)[0] is False
    assert extract_document((BASE_DIR/'samples/sample_resume.pdf').read_bytes(),'resume.pdf',config,'vlm')['pages'][0]['engine']=='PDF text'


@pytest.mark.parametrize('missing',['SECRET_KEY','SUPABASE_DB_URL','COOKIE_SECURE','APP_MODE'])
def test_hosted_rejects_unsafe_configuration(monkeypatch,tmp_path,missing):
    hosted_env(monkeypatch,tmp_path)
    monkeypatch.setenv(missing,'')
    with pytest.raises(ValueError): settings()


def test_runtime_parameterization_and_ownership(monkeypatch):
    runtime=PostgresRuntime('not-used')
    calls=[]
    class Result:
        def fetchone(self): return {'payload':{'safe':'test'},'count':1}
    class DB:
        def execute(self,sql,params):
            calls.append((sql,params))
            return Result()
    @contextmanager
    def fake_connect(): yield DB()
    monkeypatch.setattr(runtime,'connect',fake_connect)
    runtime.set_session('opaque-sid','supabase',{'id':'user-a'},9999999999)
    assert runtime.get_session('opaque-sid','supabase')=={'safe':'test'}
    runtime.save_draft('draft','user-a',{'pages':[]})
    runtime.get_draft('draft','user-b')
    assert calls[-1][1][2]=='user-b'
    assert 'opaque-sid' not in calls[0][1]
    runtime.save_chat('opaque-sid','user-a',[{'text':'x'}]*12)
    assert len(json.loads(calls[-1][1][3]))==8
    assert runtime.rate_allow('private-email@example.com')
    assert 'private-email@example.com' not in calls[-1][1]
    assert 'ON CONFLICT' in calls[-1][0]
    runtime.delete_session('opaque-sid')
    assert "'session','chat'" in calls[-1][0]


def test_vercel_config():
    config=json.loads((BASE_DIR/'vercel.json').read_text())
    assert config['framework']=='flask'
    assert 'builds' not in config and 'rewrites' not in config
    assert config['functions']['app.py']['maxDuration']==60
    assert (BASE_DIR/'.python-version').read_text().strip()=='3.12'
