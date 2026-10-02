"""Isolated REST emulator; actual SQL privileges need deployment verification."""
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import pytest
import requests
from app import create_app
from config import BASE_DIR
from storage import StoreError, SupabaseRepository
from serverless_runtime import SupabaseRuntime
from test_vercel import hosted_env, SERVICE_KEY

@pytest.fixture
def backend(monkeypatch):
    rows, limits, calls = {}, {}, []
    lock = threading.Lock()
    clock = [1000.0]
    monkeypatch.setattr('serverless_runtime.time.time', lambda: clock[0])
    def request(method, url, **kw):
        assert kw['headers']['apikey'] == SERVICE_KEY
        assert kw['headers']['Authorization'] == 'Bearer ' + SERVICE_KEY
        assert kw['allow_redirects'] is False
        calls.append((method,url,kw))
        with lock:
            if '/rpc/' in url:
                body=kw['json']; bucket=body['p_bucket']
                count,reset=limits.get(bucket,(0,0))
                if reset<=clock[0]: count,reset=0,clock[0]+body['p_window']
                allowed=count<body['p_maximum']
                if allowed: limits[bucket]=(count+1,reset)
                value=allowed
            elif method=='POST':
                row=kw['json']; rows[(row['kind'],row['key'],row['owner'])]=row
                value=None
            else:
                params=kw['params']
                def matches(row):
                    for key,val in params.items():
                        if val.startswith('eq.') and str(row[key])!=val[3:]: return False
                        if val.startswith('in.') and row[key] not in val[4:-1].split(','): return False
                        if val.startswith('gt.') and row[key]<=float(val[3:]): return False
                        if val.startswith('lte.') and row[key]>float(val[4:]): return False
                    return True
                found=[key for key,row in rows.items() if matches(row)]
                if method=='DELETE':
                    for key in found: del rows[key]
                    value=None
                else: value=[{'payload':rows[key]['payload']} for key in found][:1]
        return SimpleNamespace(ok=True,content=b'x' if value is not None else b'',json=lambda:value)
    class Transport:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def request(self,*args,**kwargs): return request(*args,**kwargs)
    monkeypatch.setattr('serverless_runtime.requests.Session',Transport)
    runtime=SupabaseRuntime({'SUPABASE_URL':'https://example.supabase.co','SUPABASE_SERVICE_ROLE_KEY':SERVICE_KEY})
    return SimpleNamespace(runtime=runtime,rows=rows,limits=limits,calls=calls,clock=clock)

def test_sessions_drafts_chat_ownership_expiry_logout(backend):
    r=backend.runtime
    r.set_session('sid','supabase',{'id':'a'},backend.clock[0]+7*86400)
    assert r.get_session('sid','supabase')=={'id':'a'}
    assert r.get_session('sid','demo') is None
    r.save_draft('draft','a',{'pages':[]})
    assert r.get_draft('draft','b') is None
    r.delete_draft('draft','b')
    assert r.get_draft('draft','a')=={'pages':[]}
    r.delete_draft('draft','a')
    assert r.get_draft('draft','a') is None
    r.save_chat('sid','a',list(range(12)))
    assert r.chat('sid','a')==list(range(4,12))
    assert r.chat('sid','b')==[]
    assert all(row['key'] not in ('sid','draft') for row in backend.rows.values())
    backend.clock[0]+=3601
    assert r.chat('sid','a')==[]
    assert r.get_session('sid','supabase') is not None
    r.save_chat('sid','a',['new'])
    r.delete_session('sid')
    assert not backend.rows
    r.save_draft('expired','a',{})
    backend.clock[0]+=3601
    assert r.get_draft('expired','a') is None
    r.set_session('expired','supabase',{},backend.clock[0]-1)
    assert r.get_session('expired','supabase') is None

def test_atomic_rpc_contract_and_concurrent_clients(backend):
    with ThreadPoolExecutor(max_workers=12) as pool:
        results=list(pool.map(lambda _:backend.runtime.rate_allow('private@email',6,60),range(30)))
    assert sum(results)==6
    assert all('/rpc/runtime_rate_allow' in call[1] for call in backend.calls)
    assert all(call[2]['json']['p_bucket']==backend.runtime.key('private@email') for call in backend.calls)
    backend.clock[0]+=61
    assert backend.runtime.rate_allow('private@email',6,60)
    sql=(BASE_DIR/'database/vercel_rest_runtime_migration.sql').read_text().lower()
    assert 'on conflict(bucket) do update' in sql
    assert 'security invoker' in sql and "set search_path=''" in sql
    assert 'from public,anon,authenticated' in sql
    assert 'enable row level security' in sql
    statements='\n'.join(line for line in sql.splitlines() if not line.lstrip().startswith('--'))
    assert 'drop table' not in statements and 'truncate' not in statements

@pytest.mark.parametrize('key',['','test-public','sb_secret_example','fixture.eyJyb2xlIjoiYW5vbiJ9.fixture'])
def test_invalid_service_keys(key):
    with pytest.raises(ValueError):
        SupabaseRuntime({'SUPABASE_URL':'https://example.supabase.co','SUPABASE_SERVICE_ROLE_KEY':key})

@pytest.mark.parametrize('failure',['network','http','json'])
def test_errors_never_leak_secrets(backend,monkeypatch,capsys,failure):
    def fail(*args,**kwargs):
        if failure=='network': raise requests.ConnectionError(SERVICE_KEY+' private-token')
        def bad_json(): raise ValueError(SERVICE_KEY)
        return SimpleNamespace(ok=failure!='http',content=SERVICE_KEY.encode(),json=bad_json)
    class Transport:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        request=staticmethod(fail)
    monkeypatch.setattr('serverless_runtime.requests.Session',Transport)
    with pytest.raises(StoreError) as error: backend.runtime.rate_allow('bucket')
    assert SERVICE_KEY not in str(error.value)
    assert 'private-token' not in str(error.value)
    assert capsys.readouterr().out==''

def test_hosted_login_otp_session_logout(backend,monkeypatch,tmp_path):
    hosted_env(monkeypatch,tmp_path)
    auth_calls=[]
    def auth_request(method,url,**kw):
        auth_calls.append((url,kw))
        assert kw['headers']['apikey']=='test-public'
        assert SERVICE_KEY not in str(kw)
        body={'user':{'id':'user-a','email':'a@example.com'},'access_token':'user-access',
              'refresh_token':'user-refresh','expires_in':3600}
        return SimpleNamespace(ok=True,content=b'x',json=lambda:body)
    monkeypatch.setattr('auth.requests.request',auth_request)
    monkeypatch.setattr(SupabaseRepository,'profile',lambda self: {})
    application=create_app({'TESTING':True})
    client=application.test_client()
    html=client.get('/login').get_data(as_text=True)
    csrf=re.search(r'name="csrf_token" value="([^"]+)"',html).group(1)
    assert client.post('/login',data={'email':'a@example.com','csrf_token':csrf}).status_code==302
    assert auth_calls[0][0].endswith('/otp')
    client.post('/login',data={'email':'a@example.com','csrf_token':csrf})
    assert len(auth_calls)==1
    assert client.post('/verify',data={'code':'12345678','csrf_token':csrf}).status_code==302
    assert auth_calls[-1][1]['json']['token']=='12345678'
    with client.session_transaction() as session: sid=session['sid']
    auth=application.extensions['authentication']
    assert auth.current(sid)['id']=='user-a'
    session_row=next(row for row in backend.rows.values() if row['kind']=='session')
    assert session_row['expires']==backend.clock[0]+7*86400
    profile=client.get('/profile').get_data(as_text=True)
    assert SERVICE_KEY not in profile and 'user-access' not in profile
    logout_csrf=re.search(r'name="csrf_token" value="([^"]+)"',profile).group(1)
    assert client.post('/logout',data={'csrf_token':logout_csrf}).status_code==302
    assert auth.current(sid) is None
    assert auth_calls[-1][1]['headers']['Authorization']=='Bearer user-access'
