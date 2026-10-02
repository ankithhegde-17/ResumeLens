"""Verify an isolated headless service environment without classifier packages."""
import io
import importlib.metadata
import importlib.util
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))

if __name__=='__main__':
    installed={d.metadata['Name'].lower() for d in importlib.metadata.distributions()}
    assert 'opencv-python-headless' in installed
    assert 'opencv-python' not in installed
    assert importlib.util.find_spec('sklearn') is None
    from ocr_service.app import create_app
    secret='isolated-headless-test-'+'x'*32
    service=create_app(dict(TESTING=True,OCR_SERVICE_SECRET=secret))
    response=service.test_client().post('/extract',headers={'Authorization':'Bearer '+secret},
        data={'resume':(io.BytesIO((root/'samples/sample_resume.png').read_bytes()),'sample.png')})
    assert response.status_code==200
    assert 'Python' in response.json['pages'][0]['text']
    print('Headless service install passed: one cv2 provider, no sklearn, authenticated real image OCR.')
