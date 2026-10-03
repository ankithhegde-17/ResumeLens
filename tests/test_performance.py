"""Regression checks for lazy startup, caching, timings and static publication."""
import json
import subprocess
import sys
from browser_workspace import BrowserWorkspace
from config import BASE_DIR
from app import create_app


def test_homepage_import_has_no_heavy_extraction_or_ml_libraries():
    result=subprocess.check_output([sys.executable,str(BASE_DIR/'scripts/performance_audit.py'),'--import-only'],text=True)
    assert json.loads(result.strip().splitlines()[-1])['heavy_imports']==[]


def test_export_compresses_once_until_changed(monkeypatch):
    workspace=BrowserWorkspace('test-secret','browser-one')
    original=workspace.signer.dumps
    calls=[]
    def dump(value):
        calls.append(1)
        return original(value)
    monkeypatch.setattr(workspace.signer,'dumps',dump)
    assert workspace.export()==workspace.export()
    assert len(calls)==1
    workspace.save_profile({'display_name':'Fictional tester'})
    workspace.export()
    assert len(calls)==2
    assert workspace.has_data()
    workspace.clear()
    assert not workspace.has_data()


def test_static_caching_and_optional_private_timings(monkeypatch,caplog):
    monkeypatch.setenv('VERCEL','1')
    monkeypatch.setenv('SECRET_KEY','performance-test-secret')
    monkeypatch.setenv('COOKIE_SECURE','true')
    app=create_app({'TESTING':True,'PERFORMANCE_DIAGNOSTICS':False})
    client=app.test_client()
    response=client.get('/dashboard')
    assert response.headers['Cache-Control']=='no-store'
    assert 'Server-Timing' not in response.headers
    assert b'"has_data": false' in response.data
    assert not caplog.records
    assert 'immutable' not in client.get('/static/style.css').headers['Cache-Control']
    assert 'immutable' in client.get('/static/style.css?v=test').headers['Cache-Control']
    assert client.get('/careers').status_code==200
    diagnostics=create_app({'TESTING':True,'PERFORMANCE_DIAGNOSTICS':True}).test_client().get('/upload')
    assert 'app;dur=' in diagnostics.headers['Server-Timing']
    assert any('stage=template:upload.html' in record.message for record in caplog.records)
    assert any('stage=page:upload' in record.message for record in caplog.records)


def test_model_is_loaded_once(monkeypatch):
    from analysis import model_bundle
    import joblib
    calls=[]
    monkeypatch.setattr(joblib,'load',lambda path: calls.append(path) or {'test':True})
    model_bundle.cache_clear()
    try:
        assert model_bundle() is model_bundle()
        assert len(calls)==1
    finally: model_bundle.cache_clear()


def test_evaluation_json_is_cached():
    from analysis import evaluation_data
    evaluation_data.cache_clear()
    assert evaluation_data('evaluation.json') is evaluation_data('evaluation.json')


def test_cdn_build_skips_retired_artwork():
    subprocess.check_call([sys.executable,str(BASE_DIR/'scripts/vercel_build.py')])
    for filename in ('login-hero.png','login-hero.webp','favicon.svg'):
        assert not (BASE_DIR/'public/static'/filename).exists()
    assert (BASE_DIR/'public/static/logo.png').exists()
