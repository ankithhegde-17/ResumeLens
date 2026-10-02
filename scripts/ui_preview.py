r"""Isolated browser QA server. Uses temporary demo data, never Supabase records.

Run from the project: .venv\Scripts\python.exe scripts\ui_preview.py
The temporary database is removed when this process exits normally.
"""
import os
import secrets
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask import redirect, render_template, request, session, url_for


def main():
    with tempfile.TemporaryDirectory(prefix='resumelens-ui-') as directory:
        os.environ['APP_INSTANCE_DIR'] = directory
        os.environ['APP_MODE'] = 'demo'
        os.environ['SECRET_KEY'] = secrets.token_hex(32)
        from app import create_app
        from analysis import analyze
        from config import BASE_DIR
        from extraction import extract_document
        from skills import candidates
        from storage import LocalRepository

        app = create_app(dict(TESTING=True, APP_MODE='demo', DB_PATH=Path(directory) / 'qa.sqlite3',
                             EXTRACTION_ENGINE='ocr', OLLAMA_TIMEOUT=1, GEMINI_API_KEY='', TEMPLATES_AUTO_RELOAD=True))
        runtime = app.extensions['runtime']
        auth = app.extensions['authentication']
        user = dict(id=str(uuid.uuid4()), email='career.explorer.with.a.long.email.address@example.com')
        sid = secrets.token_urlsafe(32)
        runtime.set_session(sid, 'demo', user, time.time() + 86400)
        repository = LocalRepository(runtime, user)
        repository.save_profile(dict(display_name='Career Explorer', headline='Student · building a path into data science',
                                     location='Mysuru, India', goal_role='data-analyst'))
        series = str(uuid.uuid4())
        identifiers = []
        for filename in ['sample_resume.pdf', 'sample_resume_v2.pdf']:
            extraction = extract_document((BASE_DIR / 'samples' / filename).read_bytes(), filename,
                                          app.config, 'ocr')
            selected = [skill['name'] for skill in candidates(extraction['pages']) if not skill['caution']]
            output = analyze(extraction['pages'], selected, '')
            output['extraction_notes'] = extraction['notes']
            identifier = str(uuid.uuid4())
            repository.save(identifier, series, 'My data science career resume', filename, 'PDF', output)
            identifiers.append(identifier)
        draft_id = str(uuid.uuid4())
        runtime.save_draft(draft_id, user['id'], dict(extraction, series_id=series,
            title='Resume review', source_name='a-very-long-resume-filename-for-mobile-layout-verification.pdf',
            job_description=''))

        # This fixture replaces email sending only in this separate demo process.
        def fixture_send(email, ip):
            with runtime.connect() as db:
                db.execute('INSERT OR REPLACE INTO challenges VALUES (?,?,?,0)',
                           (email, auth.digest(email, '123456'), time.time() + 600))
        auth.send = fixture_send

        @app.route('/__preview/session')
        def preview_session():
            session.clear()
            session['sid'] = sid
            return redirect(url_for('dashboard'))

        @app.route('/__preview/verify')
        def preview_verify():
            session.clear()
            session['pending_email'] = user['email']
            return render_template('verify.html', email=user['email'], signed_user=None,
                                   mode='supabase' if request.args.get('cloud') else 'demo')

        @app.route('/__preview/paths')
        def preview_paths():
            return dict(result=url_for('result', analysis_id=identifiers[-1]),
                        previous=url_for('result', analysis_id=identifiers[0]),
                        review=url_for('review', draft_id=draft_id))

        print('Isolated UI preview: http://127.0.0.1:5051', flush=True)
        app.run(host='127.0.0.1', port=5051, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
