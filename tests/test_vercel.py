"""Hosted public routes must work without Supabase, authentication or disk state."""
import json
import pytest
from app import create_app
from config import BASE_DIR,settings
from browser_client import browser_app
from extraction import extract_document

def hosted_env(monkeypatch):
    monkeypatch.setenv('VERCEL','1')
    monkeypatch.setenv('SECRET_KEY','isolated-hosted-test')
    monkeypatch.setenv('COOKIE_SECURE','true')
    for key in ['APP_MODE','SUPABASE_URL','SUPABASE_PUBLISHABLE_KEY','SUPABASE_SERVICE_ROLE_KEY','SUPABASE_DB_URL']:
        monkeypatch.delenv(key,raising=False)

def test_hosted_public_import_routes_without_db_or_network(monkeypatch):
    hosted_env(monkeypatch)
    def no_network(*args,**kwargs): raise AssertionError('Public navigation must not call a database or auth provider.')
    monkeypatch.setattr('requests.request',no_network)
    monkeypatch.setattr('requests.Session',no_network)
    app=browser_app(create_app({'TESTING':True}))
    assert 'runtime' not in app.extensions and 'authentication' not in app.extensions
    client=app.test_client()
    for route in ['/','/dashboard','/upload','/roles','/careers/full-stack-developer','/skills/react','/profile','/history','/evaluation','/help','/terms','/static/style.css']:
        assert client.get(route).status_code==200,route
    assert extract_document((BASE_DIR/'samples/sample_resume.pdf').read_bytes(),'resume.pdf',app.config,'vlm')['pages'][0]['engine']=='PDF text'
    assert app.config['SESSION_COOKIE_SECURE'] is True
    assert 'SUPABASE_SERVICE_ROLE_KEY' not in app.config
    with client.session_transaction() as cookie:
        assert set(cookie).issubset({'visitor','csrf','_flashes'})

@pytest.mark.parametrize('missing',['SECRET_KEY','COOKIE_SECURE'])
def test_hosted_configuration(monkeypatch,missing):
    hosted_env(monkeypatch);monkeypatch.setenv(missing,'')
    with pytest.raises(ValueError): settings()

def test_vercel_config():
    config=json.loads((BASE_DIR/'vercel.json').read_text())
    assert config['framework']=='flask'
    assert config['functions']['app.py']['maxDuration']==60
    assert (BASE_DIR/'.python-version').read_text().strip()=='3.12'
