"""Offline hosted checks: no real credentials or cloud writes."""
import base64
import json
import pytest
from config import settings, BASE_DIR
from app import app, create_app
from serverless_runtime import SupabaseRuntime

SERVICE_KEY = 'fixture.' + base64.urlsafe_b64encode(b'{"role":"service_role"}').decode().rstrip('=') + '.fixture'

def hosted_env(monkeypatch, tmp_path):
    for key,value in dict(VERCEL='1',APP_MODE='supabase',SECRET_KEY='isolated-test-key',
        COOKIE_SECURE='true',SUPABASE_URL='https://example.supabase.co',
        SUPABASE_PUBLISHABLE_KEY='test-public',SUPABASE_SERVICE_ROLE_KEY=SERVICE_KEY,
        APP_INSTANCE_DIR=str(tmp_path/'never-created')).items():
        monkeypatch.setenv(key,value)

def test_exported_app():
    assert app.name == 'app'
    assert '/login' in {rule.rule for rule in app.url_map.iter_rules()}

def test_hosted_import_and_public_routes_without_disk_or_network(monkeypatch,tmp_path):
    hosted_env(monkeypatch,tmp_path)
    application=create_app()
    assert isinstance(application.extensions['runtime'],SupabaseRuntime)
    client=application.test_client()
    assert client.get('/').status_code==302
    assert client.get('/login').status_code==200
    assert SERVICE_KEY.encode() not in client.get('/login').data
    assert client.get('/verify').status_code==302
    assert client.get('/static/style.css').status_code==200
    for route in ['/dashboard','/upload','/roles','/profile','/history']:
        assert client.get(route).status_code==302
    assert application.config['SESSION_COOKIE_SECURE'] is True
    assert not (tmp_path/'never-created').exists()

@pytest.mark.parametrize('missing',['SECRET_KEY','SUPABASE_SERVICE_ROLE_KEY','COOKIE_SECURE','APP_MODE'])
def test_hosted_rejects_unsafe_configuration(monkeypatch,tmp_path,missing):
    hosted_env(monkeypatch,tmp_path)
    monkeypatch.setenv(missing,'')
    with pytest.raises(ValueError): settings()

def test_vercel_config():
    config=json.loads((BASE_DIR/'vercel.json').read_text())
    assert config['framework']=='flask'
    assert 'builds' not in config and 'rewrites' not in config
    assert config['functions']['app.py']['maxDuration']==60
    assert (BASE_DIR/'.python-version').read_text().strip()=='3.12'
