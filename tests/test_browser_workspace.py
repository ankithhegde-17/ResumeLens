import json
import uuid
import pytest
from app import create_app
from browser_workspace import BrowserWorkspace, InstanceRateLimits
from browser_client import browser_app
from test_app import token,analyze_sample

def test_cold_start_browser_state_and_tamper(tmp_path):
    cfg={'TESTING':True,'SECRET_KEY':'stable-secret','EXTRACTION_ENGINE':'ocr'}
    first=browser_app(create_app(cfg)).test_client()
    record,_=analyze_sample(first)
    saved=first.workspace_state
    with first.session_transaction() as cookie: copied=dict(cookie)
    second=browser_app(create_app(cfg)).test_client()
    with second.session_transaction() as cookie: cookie.update(copied)
    second.workspace_state=saved;second.csrf=first.csrf
    assert second.get('/results/'+record['id']).status_code==200
    unrelated=browser_app(create_app(cfg)).test_client();unrelated.get('/')
    unrelated.workspace_state=saved
    assert unrelated.get('/history').status_code==404
    second.workspace_state=saved[:-3]+'bad'
    assert second.get('/history').status_code==400

def test_cookie_has_no_resume_or_auth_tokens():
    client=browser_app(create_app({'TESTING':True,'SECRET_KEY':'test-cookie','EXTRACTION_ENGINE':'ocr'})).test_client()
    analyze_sample(client)
    with client.session_transaction() as cookie:
        assert set(cookie).issubset({'visitor','csrf','_flashes'})
        assert 'Python' not in str(dict(cookie))
    assert client.get('/login').location.endswith('/dashboard')
    assert client.get('/verify').location.endswith('/dashboard')
    assert client.post('/logout',data={'csrf_token':client.csrf}).status_code==404

def test_draft_chat_expiry_and_bounded_size(monkeypatch):
    stamp=[1000.0];monkeypatch.setattr('browser_workspace.time.time',lambda:stamp[0])
    w=BrowserWorkspace('secret','a'*43)
    w.save_draft('id',{'pages':[]});w.save_chat(list(range(20)))
    assert w.chat()==list(range(12,20))
    signed=w.export();stamp[0]+=3601
    w=BrowserWorkspace('secret','a'*43,signed)
    assert w.get_draft('id') is None and w.chat()==[]
    with pytest.raises(ValueError,match='full'):
        w.save_draft('huge',{'text':'x'*(3*1024*1024)})
    assert w.get_draft('huge') is None

def test_jd_review_analysis_export():
    client=browser_app(create_app({'TESTING':True,'SECRET_KEY':'jd-test','EXTRACTION_ENGINE':'ocr'})).test_client()
    csrf=token(client,'/upload')
    response=client.post('/upload',data={'csrf_token':csrf,'sample':'pdf','title':'JD test','job_description':'Python SQL React Docker','engine':'ocr'})
    draft_id=response.location.rsplit('/',1)[1]
    draft=client.workspace().get_draft(draft_id)
    from skills import candidates
    fields={f'page_{p["number"]}':p['text'] for p in draft['pages']}
    response=client.post(response.location,data=dict(fields,csrf_token=csrf,confirmed='yes',action='analyze',skills=[s['name'] for s in candidates(draft['pages']) if not s['caution']]))
    record=json.loads(client.get(response.location+'/download').data)
    assert record['result']['jd']['matched'] and record['result']['jd']['missing']

def test_size_and_rate_limiter():
    limits=InstanceRateLimits()
    assert limits.allow('anon',1,60)
    assert not limits.allow('anon',1,60)
    assert len(limits.rows)==1

def test_clear_rotates_browser_binding_and_discards_old_state():
    client=browser_app(create_app({'TESTING':True,'SECRET_KEY':'clear-test','EXTRACTION_ENGINE':'ocr'})).test_client()
    analyze_sample(client)
    old=client.workspace_state
    response=client.post('/workspace/clear',data={'csrf_token':client.csrf,'confirm':'CLEAR'})
    assert response.status_code==302 and client.workspace().list()==[]
    client.workspace_state=old
    assert client.get('/history').status_code==404
    # Clearing must also recover from corrupt local storage.
    response=client.post('/workspace/clear',data={'csrf_token':client.csrf,'confirm':'CLEAR'})
    assert response.status_code==302 and client.get('/dashboard').status_code==200
