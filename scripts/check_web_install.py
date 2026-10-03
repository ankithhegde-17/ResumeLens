"""Web-only import and route checks; no auth/DB configuration."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.update(VERCEL='1',SECRET_KEY='isolated-install-check',COOKIE_SECURE='true')
from app import app
from analysis import model_bundle
client=app.test_client()
for route in ['/','/dashboard','/upload','/roles','/careers/full-stack-developer','/skills/react','/profile','/history','/static/style.css']:
    assert client.get(route).status_code==200,route
assert len(model_bundle()['pipeline'].predict_proba(['Python SQL Git'])[0])==8
print('Web-only checks passed: public routes, saved model, no authentication/database dependency.')
