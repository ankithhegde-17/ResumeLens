"""Meaningful regression checks for ownership, scoring and the complete anonymous flow."""
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
from browser_client import browser_app
from analysis import load_catalog, model_bundle


@pytest.fixture
def app(tmp_path, monkeypatch):
    return browser_app(create_app(dict(TESTING=True, EXTRACTION_ENGINE='ocr', SECRET_KEY='test-key-only')))


def token(client, page='/dashboard'):
    html = client.get(page).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def open_workspace(client):
    assert client.get('/dashboard').status_code == 200


def analyze_sample(client, kind='pdf', series_id=''):
    csrf = token(client, '/upload')
    response = client.post('/upload', data=dict(csrf_token=csrf, sample=kind, title='Demo Resume', engine='ocr', series_id=series_id))
    assert response.status_code == 302
    review_url = response.location
    client.get(review_url)
    draft_id = review_url.rsplit('/', 1)[1]
    draft = client.workspace().get_draft(draft_id)
    found = candidates(draft['pages'])
    data = dict(csrf_token=csrf, confirmed='yes', action='analyze', skills=[s['name'] for s in found if not s['caution']])
    data.update({f'page_{p["number"]}': p['text'] for p in draft['pages']})
    response = client.post(review_url, data=data)
    assert response.status_code == 302
    assert client.get(response.location).status_code == 200
    record = json.loads(client.get(response.location + '/download').data)
    return record, review_url


def test_complete_version_profile_and_history_flow(app):
    c = app.test_client(); open_workspace(c)
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
    open_workspace(a); record, draft_url = analyze_sample(a)
    open_workspace(b)
    assert b.get('/results/' + record['id']).status_code == 404
    assert b.get('/results/' + record['id'] + '/download').status_code == 404
    assert b'Demo Resume' not in b.get('/history').data
    assert b.get(draft_url).status_code == 302
    csrf = token(b, '/history')
    assert b.post('/history/delete', data=dict(csrf_token=csrf, series_id=record['series_id'], confirm='DELETE')).status_code == 404


def test_csrf_and_anonymous_access(app):
    c = app.test_client()
    assert c.post('/upload', data=dict(title='Sample')).status_code == 400
    assert c.get('/history').status_code == 200
    assert c.get('/samples/sample_resume.pdf').status_code == 200


def test_bad_input_and_confirmation(app):
    c = app.test_client(); csrf = token(c)
    open_workspace(c); csrf = token(c, '/upload')
    response = c.post('/upload', data=dict(csrf_token=csrf, title='Bad', engine='ocr', resume=(io.BytesIO(b'not pdf'), 'bad.pdf')))
    assert b'genuine PDF' in response.data
    response = c.post('/upload', data=dict(csrf_token=csrf, title='Good title', sample='pdf', engine='ocr'))
    review_url = response.location
    assert b'Confirm that you reviewed' in c.post(review_url, data=dict(csrf_token=csrf, action='analyze', page_1='Python SQL resume document example')).data
    assert b'name of 2' in c.post('/profile', data=dict(csrf_token=csrf, display_name='X')).data


def test_double_submit_is_idempotent(app):
    c = app.test_client(); open_workspace(c); record, review_url = analyze_sample(c)
    csrf = token(c, '/history')
    assert c.post(review_url, data=dict(csrf_token=csrf)).location.endswith(record['id'])
    assert len(c.workspace().list()) == 1


def test_delete_all_versions(app):
    c = app.test_client(); open_workspace(c); one, _ = analyze_sample(c)
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


def test_malformed_vision_response_is_handled(monkeypatch, app):
    from PIL import Image
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'response': '42'}
    monkeypatch.setattr('extraction.requests.post', lambda *args, **kwargs: Response())
    with pytest.raises(ValueError, match='Vision extraction failed'):
        read_vision(Image.new('RGB', (400,600), 'white'), app.config)


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
