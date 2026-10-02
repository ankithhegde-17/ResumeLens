"""Run inside a fresh web-only venv to prove OCR libraries aren't required."""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

if __name__=='__main__':
    for module in ['rapidocr_onnxruntime','onnxruntime','cv2']:
        assert importlib.util.find_spec(module) is None, f'{module} must be absent for this isolated check.'
    with tempfile.TemporaryDirectory(prefix='resumelens-web-check-') as folder:
        os.environ.update(APP_MODE='demo',SECRET_KEY='isolated-check-only',APP_INSTANCE_DIR=folder,COOKIE_SECURE='false')
        from app import app
        from analysis import model_bundle
        from extraction import extract_document
        from config import BASE_DIR
        client=app.test_client()
        assert client.get('/login').status_code==200
        assert client.get('/static/style.css').status_code==200
        app.extensions['authentication'].current=lambda sid: {'id':'00000000-0000-0000-0000-000000000001','email':'fixture@example.com'}
        for route in ['/dashboard','/roles','/careers/full-stack-developer','/skills/react','/profile','/history']:
            assert client.get(route).status_code==200,route
        probabilities=model_bundle()['pipeline'].predict_proba(['Python SQL Git'])
        assert probabilities.shape==(1,8)
        result=extract_document((BASE_DIR/'samples/sample_resume.pdf').read_bytes(),'sample.pdf',dict(app.config,VERCEL_HOSTED=True),'ocr')
        assert result['pages'][0]['engine']=='PDF text'
        print('Web-only install passed: import, login/static/dashboard/careers/profile/history, saved 8-class model and hosted text PDF; no OCR packages installed.')
