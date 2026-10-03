"""Appearance rendering and strict early-script CSP contract."""
import base64
import hashlib
import re

from app import create_app
from browser_client import browser_app


def test_appearance_initializes_before_css_and_is_allowed_by_csp():
    app = browser_app(create_app(dict(TESTING=True, SECRET_KEY='theme-test-only')))
    response = app.test_client().get('/profile')
    html = response.get_data(as_text=True)
    script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    assert f"'sha256-{digest}'" in response.headers['Content-Security-Policy']
    assert "'unsafe-inline'" not in response.headers['Content-Security-Policy']
    assert html.index('resumelens-theme') < html.index('rel="stylesheet"')
    assert 'mode-pill' not in html
    assert 'No account · This browser only' in html
    for value in ('system', 'light', 'dark'):
        assert f'name="appearance" value="{value}"' in html
