"""Remote OCR boundaries and private service; no live resume transmission."""
import io
import json
import requests
import pytest
from config import BASE_DIR
from extraction import extract_document
from remote_ocr import extract_remote
from ocr_service.app import create_app

SECRET='isolated-test-secret-'+'x'*32
CFG=dict(VERCEL_HOSTED=True,EXTRACTION_ENGINE='ocr',UPLOAD_MAX_MB=4,
         OCR_SERVICE_URL='https://ocr.example.com',OCR_SERVICE_SECRET=SECRET)
TEXT='Python SQL and Git portfolio with documented analytical projects. '*3
RESULT=dict(pages=[dict(number=1,text=TEXT,engine='RapidOCR',confidence=0.95)],source_type='Image',notes=[])


def mock_transport(monkeypatch, payload=RESULT, code=200, error=None):
    calls=[]
    class Transport:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def post(self,url,**kwargs):
            calls.append((url,kwargs))
            if error: raise error
            class Response:
                ok=code==200
                content=json.dumps(payload).encode()
                def json(self): return payload
            return Response()
    monkeypatch.setattr('remote_ocr.requests.Session',Transport)
    return calls


def test_remote_scan_integration(monkeypatch):
    calls=mock_transport(monkeypatch)
    result=extract_document((BASE_DIR/'samples/sample_resume.png').read_bytes(),'resume.png',CFG)
    assert result['pages'][0]['engine']=='Remote RapidOCR'
    assert result['pages'][0]['text']==TEXT
    assert len(calls)==1
    assert calls[0][1]['headers']['Authorization']=='Bearer '+SECRET
    assert SECRET not in calls[0][0]
    assert calls[0][1]['allow_redirects'] is False
    assert calls[0][1]['timeout']==(5,35)


def test_text_pdf_does_not_call_service(monkeypatch):
    calls=mock_transport(monkeypatch)
    result=extract_document((BASE_DIR/'samples/sample_resume.pdf').read_bytes(),'resume.pdf',CFG)
    assert result['pages'][0]['engine']=='PDF text'
    assert not calls


def test_mixed_pdf_single_request(monkeypatch):
    import fitz
    with fitz.open() as doc:
        doc.new_page().insert_text((30,30),TEXT)
        doc.new_page()
        blob=doc.tobytes()
    result=dict(pages=[dict(number=1,text=TEXT,engine='PDF text',confidence=None),
                       dict(number=2,text=TEXT,engine='RapidOCR',confidence=0.8)],source_type='PDF')
    calls=mock_transport(monkeypatch,result)
    assert len(extract_document(blob,'mixed.pdf',CFG)['pages'])==2
    assert len(calls)==1


@pytest.mark.parametrize('payload',[{},dict(RESULT,pages=[]),dict(RESULT,source_type='PDF'),
    dict(RESULT,pages=[dict(number=1,text=TEXT,engine='invented',confidence=None)]),
    dict(RESULT,pages=[dict(number=1,text='a'*12001,engine='RapidOCR',confidence=None)]),
    dict(RESULT,pages=[dict(number=1,text=TEXT,engine='RapidOCR',confidence=float('nan'))])])
def test_malformed_service_output(monkeypatch,payload):
    mock_transport(monkeypatch,payload)
    with pytest.raises(ValueError,match='temporarily unavailable'):
        extract_remote(b'bytes','resume.png',CFG)


@pytest.mark.parametrize('code',[401,413,422,429,500,503])
def test_service_errors(monkeypatch,code):
    mock_transport(monkeypatch,code=code)
    with pytest.raises(ValueError,match='temporarily unavailable'):
        extract_remote(b'bytes','resume.png',CFG)


def test_timeout_and_configuration(monkeypatch):
    calls=mock_transport(monkeypatch,error=requests.Timeout('private error not shown'))
    with pytest.raises(ValueError,match='temporarily unavailable'):
        extract_remote(b'bytes','resume.png',CFG)
    for url in ['http://localhost:8080','https://name:password@example.com','https://example.com/?key=bad']:
        with pytest.raises(ValueError,match='configuration'):
            extract_remote(b'bytes','resume.png',dict(CFG,OCR_SERVICE_URL=url))
    assert len(calls)==1


@pytest.fixture
def service():
    return create_app(dict(TESTING=True,OCR_SERVICE_SECRET=SECRET))


def test_private_service_auth_and_text_pdf(service):
    client=service.test_client()
    assert client.get('/health').status_code==200
    assert client.post('/extract').status_code==401
    assert client.post('/extract',headers={'Authorization':'Bearer wrong'}).status_code==401
    headers={'Authorization':'Bearer '+SECRET}
    assert client.post('/extract',headers=headers).status_code==400
    response=client.post('/extract',headers=headers,data={'resume':(io.BytesIO((BASE_DIR/'samples/sample_resume.pdf').read_bytes()),'resume.pdf')})
    assert response.status_code==200
    assert response.json['pages'][0]['engine']=='PDF text'
    assert client.post('/extract',headers=headers,data={'resume':(io.BytesIO(b'not image'),'bad.png')}).status_code==422
    assert client.post('/extract',headers=headers,data={'resume':(io.BytesIO(b'x'*(5*1024*1024)),'big.pdf')}).status_code==413


def test_private_service_image_ocr(service):
    client=service.test_client()
    response=client.post('/extract',headers={'Authorization':'Bearer '+SECRET},
        data={'resume':(io.BytesIO((BASE_DIR/'samples/sample_resume.png').read_bytes()),'resume.png')})
    assert response.status_code==200
    assert response.json['pages'][0]['engine']=='RapidOCR'
    assert 'Python' in response.json['pages'][0]['text']


def test_service_requires_strong_secret():
    with pytest.raises(ValueError): create_app(dict(OCR_SERVICE_SECRET=''))
