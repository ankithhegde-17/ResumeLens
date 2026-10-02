"""Meaningful regression checks for ownership, scoring and the complete demo flow."""
import io
import json
import re
import time
from pathlib import Path
import fitz
import pytest
from app import create_app
from config import BASE_DIR
from extraction import extract_document, read_vision
from skills import candidates, names_from_text
from storage import SupabaseRepository, StoreError
from analysis import load_catalog, model_bundle


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr('auth.secrets.randbelow', lambda upper: 123456)
    return create_app(dict(TESTING=True, APP_MODE='demo', EXTRACTION_ENGINE='ocr', SECRET_KEY='test-key-only', DB_PATH=tmp_path / 'test.sqlite3'))


def token(client, page='/login'):
    html = client.get(page).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def sign_in(client, email='student@example.com'):
    csrf = token(client)
    assert client.post('/login', data=dict(email=email, csrf_token=csrf)).status_code == 302
    assert client.post('/verify', data=dict(code='123456', csrf_token=csrf)).status_code == 302


def analyze_sample(client, kind='pdf', series_id=''):
    csrf = token(client, '/upload')
    response = client.post('/upload', data=dict(csrf_token=csrf, sample=kind, title='Demo Resume', engine='ocr', series_id=series_id))
    assert response.status_code == 302
    review_url = response.location
    client.get(review_url)
    with client.session_transaction() as s:
        sid = s['sid']
    app = client.application
    user = app.extensions['authentication'].current(sid)
    draft_id = review_url.rsplit('/', 1)[1]
    draft = app.extensions['runtime'].get_draft(draft_id, user['id'])
    found = candidates(draft['pages'])
    data = dict(csrf_token=csrf, confirmed='yes', action='analyze', skills=[s['name'] for s in found if not s['caution']])
    data.update({f'page_{p["number"]}': p['text'] for p in draft['pages']})
    response = client.post(review_url, data=data)
    assert response.status_code == 302
    assert client.get(response.location).status_code == 200
    record = json.loads(client.get(response.location + '/download').data)
    return record, review_url


def test_complete_version_profile_and_history_flow(app):
    c = app.test_client(); sign_in(c)
    csrf = token(c, '/profile')
    c.post('/profile', data=dict(csrf_token=csrf, display_name='Demo Student', headline='AI Student', location='Mysuru', goal_role='ml-intern'))
    assert b'Demo Student' in c.get('/dashboard').data
    first, _ = analyze_sample(c)
    second, _ = analyze_sample(c, 'v2', first['series_id'])
    assert second['version'] == 2 and first['version'] == 1
    assert second['result']['roles'][0]['score'] == 100
    ml = next(r for r in second['result']['roles'] if r['id'] == 'ml-intern')
    assert ml['score'] == 100
    assert c.get('/history').data.count(b'Demo Resume') >= 2
    assert b'NumPy' in c.get('/results/' + second['id']).data
    for route in ['/roles','/evaluation','/help','/profile','/static/style.css','/static/script.js']:
        assert c.get(route).status_code == 200


def test_private_records_and_drafts(app):
    a, b = app.test_client(), app.test_client()
    sign_in(a, 'first@example.com'); record, draft_url = analyze_sample(a)
    sign_in(b, 'second@example.com')
    assert b.get('/results/' + record['id']).status_code == 404
    assert b.get('/results/' + record['id'] + '/download').status_code == 404
    assert b'Demo Resume' not in b.get('/history').data
    assert b.get(draft_url).status_code == 302
    csrf = token(b, '/history')
    assert b.post('/history/delete', data=dict(csrf_token=csrf, series_id=record['series_id'], confirm='DELETE')).status_code == 404


def test_otp_invalid_attempts_replay_and_rate_limit(app):
    c = app.test_client(); csrf = token(c)
    c.post('/login', data=dict(csrf_token=csrf, email='otp@example.com'))
    for _ in range(5):
        assert b'incorrect' in c.post('/verify', data=dict(csrf_token=csrf, code='000000')).data
    assert b'expired' in c.post('/verify', data=dict(csrf_token=csrf, code='123456')).data
    assert b'Wait 60 seconds' in c.post('/login', data=dict(csrf_token=csrf, email='otp@example.com')).data
    d = app.test_client(); sign_in(d, 'valid@example.com')
    auth = app.extensions['authentication']
    from auth import AuthError
    with pytest.raises(AuthError):
        auth.verify('valid@example.com', '123456')


def test_csrf_and_anonymous_access(app):
    c = app.test_client()
    assert c.post('/login', data=dict(email='a@example.com')).status_code == 400
    assert c.get('/history').status_code == 302
    assert c.get('/samples/sample_resume.pdf').status_code == 302


def test_bad_input_and_confirmation(app):
    c = app.test_client(); csrf = token(c)
    assert b'valid email' in c.post('/login', data=dict(csrf_token=csrf, email='wrong')).data
    sign_in(c); csrf = token(c, '/upload')
    response = c.post('/upload', data=dict(csrf_token=csrf, title='Bad', engine='ocr', resume=(io.BytesIO(b'not pdf'), 'bad.pdf')))
    assert b'genuine PDF' in response.data
    response = c.post('/upload', data=dict(csrf_token=csrf, title='Good title', sample='pdf', engine='ocr'))
    review_url = response.location
    assert b'Confirm that you reviewed' in c.post(review_url, data=dict(csrf_token=csrf, action='analyze', page_1='Python SQL resume document example')).data
    assert b'name of 2' in c.post('/profile', data=dict(csrf_token=csrf, display_name='X')).data


def test_double_submit_is_idempotent(app):
    c = app.test_client(); sign_in(c); record, review_url = analyze_sample(c)
    csrf = token(c, '/history')
    assert c.post(review_url, data=dict(csrf_token=csrf)).location.endswith(record['id'])
    with c.session_transaction() as s:
        user = app.extensions['authentication'].current(s['sid'])
    from storage import LocalRepository
    assert len(LocalRepository(app.extensions['runtime'], user).list()) == 1


def test_delete_all_versions(app):
    c = app.test_client(); sign_in(c); one, _ = analyze_sample(c)
    analyze_sample(c, 'v2', one['series_id'])
    c.post('/history/delete', data=dict(csrf_token=token(c,'/history'), series_id=one['series_id'], confirm='DELETE'))
    assert b'Your history starts here' in c.get('/history').data


@pytest.mark.parametrize('filename', ['sample_resume.pdf','sample_resume.png','sample_phone_photo.jpg','sample_scanned_resume.pdf'])
def test_actual_extraction(app, filename):
    doc = extract_document((BASE_DIR/'samples'/filename).read_bytes(), filename, app.config, 'ocr')
    assert 'Python' in names_from_text(doc['pages'][0]['text'])
    assert doc['pages'][0]['engine'] == ('PDF text' if filename == 'sample_resume.pdf' else 'RapidOCR')


def test_pdf_limits_and_empty_upload(app):
    with fitz.open() as doc:
        for _ in range(6): doc.new_page()
        blob = doc.tobytes()
    with pytest.raises(ValueError, match='pages'):
        extract_document(blob, 'six.pdf', app.config, 'ocr')
    with pytest.raises(ValueError, match='non-empty'):
        extract_document(b'', 'empty.pdf', app.config, 'ocr')


def test_alias_boundaries_negation_and_weighted_score():
    assert 'Java' not in names_from_text('JavaScript React project')
    assert 'Git' not in names_from_text('GitHub profile')
    item = candidates([dict(number=2, text='No experience with Python')])[0]
    assert item['caution'] and item['evidence'][0]['page'] == 2
    from analysis import analyze
    output = analyze([dict(number=1, text='Skills: Python SQL', engine='PDF text', confidence=None)], ['Python','SQL'])
    backend = next(r for r in output['roles'] if r['id']=='python-backend')
    assert backend['score'] == 50 and backend['earned_weight'] == 5
    assert all(s['reviewed'] for s in output['skills'])


def test_vision_api_contract(monkeypatch, app):
    from PIL import Image
    class Response:
        def raise_for_status(self): pass
        def json(self): return dict(response=json.dumps(dict(text='Skills: Python, SQL, Git. This is a resume.')), done=True)
    def post(url, **kwargs):
        assert url.endswith('/api/generate')
        assert kwargs['json']['images'] and kwargs['json']['stream'] is False
        assert kwargs['json']['model'] == 'qwen2.5vl:3b'
        assert kwargs['json']['format']['required'] == ['text']
        return Response()
    monkeypatch.setattr('extraction.requests.post', post)
    text, confidence = read_vision(Image.new('RGB',(400,600),'white'), app.config)
    assert 'Python' in text and confidence is None


def test_supabase_repository_auth_headers_and_rpc(monkeypatch):
    observed = []
    class Response:
        ok=True; content=b'{}'; status_code=200
        def json(self): return {'id':'saved'}
    def remote(_session, method,url,**kwargs):
        observed.append((method,url,kwargs)); return Response()
    monkeypatch.setattr('storage.requests.sessions.Session.request', remote)
    repo=SupabaseRepository(dict(SUPABASE_URL='https://example.supabase.co',SUPABASE_PUBLISHABLE_KEY='public'),dict(id='user-1',access_token='signed-user-token'))
    assert repo.save('draft','series','Title','file.pdf','PDF',{}) == {'id':'saved'}
    method,url,data=observed[0]
    assert method=='POST' and url.endswith('/rpc/save_resume_analysis')
    assert data['headers']['Authorization']=='Bearer signed-user-token' and data['headers']['apikey']=='public'
    assert 'user_id' not in data['json']  # RPC derives identity from auth.uid().


def test_malformed_vision_response_is_handled(monkeypatch, app):
    from PIL import Image
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'response': '42'}
    monkeypatch.setattr('extraction.requests.post', lambda *args, **kwargs: Response())
    with pytest.raises(ValueError, match='Vision extraction failed'):
        read_vision(Image.new('RGB', (400,600), 'white'), app.config)


@pytest.mark.parametrize('code', ['123456', '1234567', '01234567', '123456789', '0123456789'])
def test_supabase_auth_otp_and_refresh_contract(monkeypatch, app, code):
    from auth import Authentication
    observed = []
    class Response:
        ok = True; content = b'{}'; status_code = 200
        def __init__(self, body): self.body = body
        def json(self): return self.body
    def remote(method, url, **kwargs):
        observed.append((method, url, kwargs))
        if url.endswith('/otp'): return Response({})
        if url.endswith('/verify'):
            assert kwargs['json']['type'] == 'email'
            assert kwargs['json']['token'] == code  # Preserve length and leading zeros.
            return Response(dict(user=dict(id='cloud-user',email='cloud@example.com'),access_token='access',refresh_token='refresh',expires_in=0))
        if 'grant_type=refresh_token' in url:
            assert kwargs['json']['refresh_token'] == 'refresh'
            return Response(dict(access_token='new-access',refresh_token='new-refresh',expires_in=3600))
        return Response({})
    monkeypatch.setattr('auth.requests.request', remote)
    cfg = dict(app.config, APP_MODE='supabase', SUPABASE_URL='https://example.supabase.co',SUPABASE_PUBLISHABLE_KEY='public')
    auth = Authentication(cfg, app.extensions['runtime'])
    auth.send('cloud@example.com', '127.0.0.1')
    sid = auth.verify('cloud@example.com', code)
    assert auth.current(sid)['access_token'] == 'new-access'
    assert observed[0][2]['headers']['apikey'] == 'public'
    auth.logout(sid)
    assert auth.current(sid) is None


def test_models_and_catalog_agree():
    catalog=load_catalog(); bundle=model_bundle()
    # The evaluated model retains its original eight classes; deterministic
    # career coverage now supports 18. Do not invent training/evaluation data.
    original=json.loads((BASE_DIR/'data/role_catalog.json').read_text(encoding='utf-8'))
    assert set(bundle['pipeline'].classes_) == {r['id'] for r in original['roles']}
    assert set(bundle['pipeline'].classes_).issubset({r['id'] for r in catalog['roles']})
    assert len(catalog['roles'])==18
    for role in catalog['roles']:
        assert sum(r['weight'] for r in role['required']) > 0
        assert all(r['skill'] in catalog['learning'] for r in role['required'])
    assert bundle['metrics']['train_count']==72 and bundle['metrics']['test_count']==24


@pytest.mark.parametrize('code', ['12345', '12345678901', '12345x', '１２３４５６', '1234 5678'])
def test_cloud_otp_rejects_malformed_input_without_calling_provider(app, monkeypatch, code):
    from auth import Authentication, AuthError
    authentication = Authentication(dict(app.config, APP_MODE='supabase'), app.extensions['runtime'])
    calls = []
    monkeypatch.setattr(authentication, 'api', lambda *args, **kwargs: calls.append(args))
    with pytest.raises(AuthError, match='complete'):
        authentication.verify('student@example.com', code)
    assert calls == []


def test_demo_still_requires_its_six_digit_code(app):
    from auth import AuthError
    authentication = app.extensions['authentication']
    authentication.send('demo@example.com', 'local')
    with pytest.raises(AuthError, match='six-digit'):
        authentication.verify('demo@example.com', '12345678')
    assert authentication.current(authentication.verify('demo@example.com', '123456'))


@pytest.mark.parametrize('code', ['00123456', '0012345678'])
def test_cloud_verify_form_and_route_preserve_full_code(app, monkeypatch, code):
    # Exercise the actual Flask route and generated input, not just the helper.
    app.config.update(APP_MODE='supabase')
    authentication = app.extensions['authentication']
    calls = []
    def provider(method, path, payload=None, bearer=None):
        calls.append((path, payload))
        if path == 'verify':
            assert payload['token'] == code and payload['type'] == 'email'
            return dict(user=dict(id='cloud-user', email='cloud@example.com'),
                        access_token='access', refresh_token='refresh', expires_in=3600)
        return {}
    monkeypatch.setattr(authentication, 'api', provider)
    client = app.test_client(); csrf = token(client)
    assert client.post('/login', data=dict(email='cloud@example.com', csrf_token=csrf)).status_code == 302
    html = client.get('/verify').get_data(as_text=True)
    assert 'maxlength="10"' in html and 'pattern="[0-9]{6,10}"' in html
    response = client.post('/verify', data=dict(code=code, csrf_token=csrf))
    assert response.status_code == 302 and response.location.endswith('/dashboard')
    with client.session_transaction() as state:
        assert 'pending_email' not in state
        assert authentication.current(state['sid'])['email'] == 'cloud@example.com'
    assert calls[-1] == ('verify', dict(email='cloud@example.com', token=code, type='email'))


def test_wrong_cloud_otp_cannot_create_a_local_session(app, monkeypatch):
    from auth import AuthError
    app.config.update(APP_MODE='supabase')
    authentication = app.extensions['authentication']
    def provider(method, path, payload=None, bearer=None):
        if path == 'verify':
            raise AuthError('The code is incorrect or expired. Request a new code.')
        return {}
    monkeypatch.setattr(authentication, 'api', provider)
    client = app.test_client(); csrf = token(client)
    client.post('/login', data=dict(email='cloud@example.com', csrf_token=csrf))
    response = client.post('/verify', data=dict(code='00123456', csrf_token=csrf))
    assert response.status_code == 200 and b'incorrect or expired' in response.data
    with client.session_transaction() as state:
        assert 'sid' not in state and state['pending_email'] == 'cloud@example.com'
