from app import create_app

def test_terms_and_footer_public(tmp_path):
    app=create_app({'TESTING':True,'APP_MODE':'demo','SECRET_KEY':'test-only','DB_PATH':tmp_path/'test.sqlite3','VERCEL_HOSTED':False})
    client=app.test_client()
    for path in ['/terms','/dashboard']:
        response=client.get(path)
        assert response.status_code==200
        assert b'href="/terms"' in response.data
        assert b'mailto:support@prayogmanch.in' in response.data
    assert b'Terms &amp; Conditions' in client.get('/terms').data
