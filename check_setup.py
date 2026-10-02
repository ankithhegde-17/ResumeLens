"""A read-only setup check. It does not send OTP emails or upload resumes."""
import sys
from importlib.metadata import version
from config import BASE_DIR, settings
from analysis import load_catalog, model_bundle
from extraction import vision_status


def main():
    print('Python:', sys.version.split()[0], '| project:', BASE_DIR)
    if not (3, 10) <= sys.version_info[:2] <= (3, 12):
        print('Use 64-bit Python 3.11 or 3.12 for the tested package versions.')
    for name in ('Flask','requests','python-dotenv','PyMuPDF','Pillow','numpy','scikit-learn','joblib','rapidocr-onnxruntime','onnxruntime'):
        print(name, version(name))
    catalog = load_catalog(); model = model_bundle()
    assert set(model['pipeline'].classes_) == {r['id'] for r in catalog['roles']}
    print('Model loaded:', model['version'], '| roles:', len(catalog['roles']))
    for relative in ('data/role_examples.csv','samples/sample_resume.pdf','samples/sample_resume.png','database/supabase_schema.sql'):
        assert (BASE_DIR / relative).is_file(), relative
    cfg = settings()
    print('Account mode:', cfg['APP_MODE'])
    print('Supabase configured:', bool(cfg['SUPABASE_URL'] and cfg['SUPABASE_PUBLISHABLE_KEY']))
    ready, message = vision_status(cfg)
    print('Vision model:', cfg['OLLAMA_MODEL'], '| ready:', ready, '|', message)
    print('Core setup is ready. For real email/cloud history follow docs/SUPABASE_SETUP.md.')


if __name__ == '__main__':
    main()

