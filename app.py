"""Beginner-friendly Flask routes. Run with: python app.py"""
import hmac
import io
import json
import os
import secrets
import uuid
from functools import wraps
import time
from pathlib import Path
from flask import Flask, abort, flash, g, redirect, render_template, request, send_file, session, url_for
from werkzeug.utils import secure_filename
from config import BASE_DIR, settings
from auth import Authentication, AuthError
from storage import RuntimeDB, LocalRepository, SupabaseRepository, StoreError
from extraction import extract_document, vision_status, MAX_PAGE_TEXT, MAX_TOTAL_TEXT
from skills import candidates
from analysis import analyze, compare_results, load_catalog, match_role
from performance import PerformanceMetrics, UserTTLCache


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(settings())
    if overrides:
        app.config.update(overrides)
    if app.config.get('VERCEL_HOSTED'):
        from serverless_runtime import PostgresRuntime
        runtime = PostgresRuntime(app.config['SUPABASE_DB_URL'])
    else:
        runtime = RuntimeDB(app.config['DB_PATH'])
    auth = Authentication(app.config, runtime)
    app.extensions['runtime'] = runtime
    app.extensions['authentication'] = auth
    app.extensions['metrics'] = PerformanceMetrics()
    app.extensions['profile_cache'] = UserTTLCache(ttl=30)

    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return session['csrf']

    def asset_url(filename):
        path = BASE_DIR / 'static' / filename
        version = int(path.stat().st_mtime) if path.exists() else 0
        return url_for('static', filename=filename, v=version)

    @app.before_request
    def prepare():
        # Static files must never create sessions or query profile/history storage.
        if request.endpoint == 'static':
            g.user = g.repo = None
            g.profile = {}
            return
        if request.method == 'POST':
            received = request.form.get('csrf_token', '')
            if not received or not hmac.compare_digest(received, session.get('csrf', '')):
                abort(400, description='The form expired. Reload the page and try again.')
        g.user = auth.current(session.get('sid'))
        g.repo = (SupabaseRepository(app.config, g.user, app.extensions['metrics']) if app.config['APP_MODE'] == 'supabase'
                  else LocalRepository(runtime, g.user)) if g.user else None
        # Sign-out remains available even if cloud profile/table setup is broken.
        cache = app.extensions['profile_cache']
        g.profile = cache.get(g.user['id']) if g.repo and request.endpoint != 'logout' else None
        if g.repo and request.endpoint != 'logout' and g.profile is None:
            g.profile = g.repo.profile()
            cache.put(g.user['id'], g.profile)
        g.profile = g.profile or {}

    @app.before_request
    def start_timing():
        g.request_started = time.perf_counter()

    @app.context_processor
    def common():
        return dict(csrf_token=csrf_token, asset_url=asset_url, mode=app.config['APP_MODE'], upload_max_mb=app.config['UPLOAD_MAX_MB'], hosted=app.config.get('VERCEL_HOSTED'), profile=g.get('profile', {}),
                    signed_user=g.get('user'), role_catalog=load_catalog()['roles'])

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        response.headers['Cache-Control'] = 'no-store' if request.endpoint != 'static' else 'public, max-age=31536000, immutable'
        if hasattr(g, 'request_started'):
            app.extensions['metrics'].record('page:' + (request.endpoint or 'unknown'), time.perf_counter() - g.request_started)
        return response

    def login_required(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if not g.user:
                flash('Sign in to access your private workspace.', 'info')
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return decorated

    def groups(records):
        latest = {}
        for record in records:
            if record['series_id'] not in latest or record['version'] > latest[record['series_id']]['version']:
                latest[record['series_id']] = record
        return sorted(latest.values(), key=lambda r: r['created_at'], reverse=True)

    def owned_record(analysis_id):
        try:
            uuid.UUID(analysis_id)
        except ValueError:
            abort(404)
        record = g.repo.get(analysis_id)
        if not record:
            abort(404)
        return record

    @app.route('/')
    def index():
        return redirect(url_for('dashboard' if g.user else 'login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if g.user:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            try:
                auth.send(email, request.remote_addr or 'local')
                session['pending_email'] = email
                flash('Code sent to your email.' if app.config['APP_MODE'] == 'supabase' else 'Local demo code printed in your VS Code terminal.', 'success')
                return redirect(url_for('verify'))
            except AuthError as exc:
                flash(str(exc), 'error')
        return render_template('login.html', email=request.form.get('email', ''))

    @app.route('/verify', methods=['GET', 'POST'])
    def verify():
        if g.user:
            return redirect(url_for('dashboard'))
        email = session.get('pending_email')
        if not email:
            return redirect(url_for('login'))
        if request.method == 'POST':
            try:
                sid = auth.verify(email, request.form.get('code', '').strip())
                session.clear()  # Rotate state and CSRF token after authentication.
                session['sid'] = sid
                return redirect(url_for('dashboard'))
            except AuthError as exc:
                flash(str(exc), 'error')
        return render_template('verify.html', email=email)

    @app.route('/logout', methods=['POST'])
    def logout():
        if g.user:
            app.extensions['profile_cache'].invalidate(g.user['id'])
        auth.logout(session.get('sid'))
        session.clear()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        records = g.repo.list(); latest = groups(records)
        return render_template('dashboard.html', latest=latest, records=records, current=latest[0] if latest else None)

    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        existing = groups(g.repo.list())
        if request.method == 'POST':
            try:
                series_id = request.form.get('series_id', '')
                match = next((r for r in existing if r['series_id'] == series_id), None)
                if series_id and not match:
                    raise ValueError('Choose one of your saved resumes or start a new resume.')
                title = match['title'] if match else request.form.get('title', '').strip()
                if not 2 <= len(title) <= 80:
                    raise ValueError('Resume title must be between 2 and 80 characters.')
                jd = request.form.get('job_description', '').strip()
                if len(jd) > 10000:
                    raise ValueError('Job description must be at most 10,000 characters.')
                sample = request.form.get('sample', '')
                if sample:
                    sample_map = {'pdf': 'sample_resume.pdf', 'image': 'sample_resume.png',
                                  'scan': 'sample_scanned_resume.pdf', 'v2': 'sample_resume_v2.pdf'}
                    if sample not in sample_map:
                        raise ValueError('Unknown sample.')
                    filename = sample_map[sample]
                    blob = (BASE_DIR / 'samples' / filename).read_bytes()
                else:
                    file = request.files.get('resume')
                    if not file or not file.filename:
                        raise ValueError('Choose a resume file first.')
                    filename = secure_filename(file.filename)[:120]
                    blob = file.read(10 * 1024 * 1024 + 1)
                extraction = extract_document(blob, filename, app.config, request.form.get('engine', 'default'),
                                              observer=lambda stage, seconds: app.extensions['metrics'].record('inference:' + stage, seconds))
                draft_id = str(uuid.uuid4())
                draft = dict(extraction, series_id=series_id or str(uuid.uuid4()), title=title,
                             source_name=filename, job_description=jd)
                runtime.save_draft(draft_id, g.user['id'], draft)
                return redirect(url_for('review', draft_id=draft_id))
            except ValueError as exc:
                flash(str(exc), 'error')
        return render_template('upload.html', existing=existing, selected_series=request.args.get('series', ''), values=request.form)

    @app.route('/review/<draft_id>', methods=['GET', 'POST'])
    @login_required
    def review(draft_id):
        draft = runtime.get_draft(draft_id, g.user['id'])
        if not draft:
            saved = g.repo.get(draft_id)
            if saved:
                return redirect(url_for('result', analysis_id=draft_id))
            flash('This draft expired or was already removed. Please upload the resume again.', 'info')
            return redirect(url_for('upload'))
        selected = None
        if request.method == 'POST':
            try:
                pages = [dict(p, text=request.form.get(f'page_{p["number"]}', '').strip()) for p in draft['pages']]
                if any(not p['text'] or len(p['text']) > MAX_PAGE_TEXT for p in pages) or sum(len(p['text']) for p in pages) > MAX_TOTAL_TEXT:
                    raise ValueError('Keep every page non-empty and below the displayed text limits.')
                draft['pages'] = pages
                runtime.save_draft(draft_id, g.user['id'], draft)
                if request.form.get('action') == 'refresh':
                    flash('Skill list refreshed from your edited text. Confirm it below.', 'success')
                else:
                    selected = request.form.getlist('skills')
                    if request.form.get('confirmed') != 'yes':
                        raise ValueError('Confirm that you reviewed the extracted text and selected skills.')
                    supported = {s['name'] for s in candidates(pages)}
                    if not set(selected).issubset(supported):
                        raise ValueError('The text changed. Refresh the skill list before analyzing.')
                    output = analyze(pages, selected, draft['job_description'])
                    output['extraction_notes'] = draft['notes']
                    g.repo.save(draft_id, draft['series_id'], draft['title'], draft['source_name'], draft['source_type'], output)
                    runtime.delete_draft(draft_id, g.user['id'])
                    return redirect(url_for('result', analysis_id=draft_id))
            except ValueError as exc:
                flash(str(exc), 'error')
        found = candidates(draft['pages'])
        if selected is None:
            selected = [s['name'] for s in found if not s['caution']]
        return render_template('review.html', draft=draft, draft_id=draft_id, found=found, selected=selected)

    @app.route('/results/<analysis_id>')
    @login_required
    def result(analysis_id):
        record = owned_record(analysis_id)
        history = [r for r in g.repo.list() if r['series_id'] == record['series_id']]
        previous = next((r for r in history if r['version'] == record['version'] - 1), None)
        return render_template('result.html', record=record, output=record['result'], history=history,
                               is_current=record['version'] == max(r['version'] for r in history),
                               comparison=compare_results(record, previous))

    @app.route('/roles')
    @login_required
    def roles():
        analysis_id = request.args.get('analysis', '')
        record = owned_record(analysis_id) if analysis_id else None
        if not record:
            records = groups(g.repo.list())
            record = records[0] if records else None
        # Current guidance is recomputed; saved version scores remain immutable.
        catalog=load_catalog()
        mapping={s['name']:s for s in record['result']['skills']} if record else {}
        role_list=sorted([match_role(r,mapping,catalog['learning']) for r in catalog['roles']],key=lambda r:(-r['score'],r['title'])) if record else catalog['roles']
        from career_data import CATEGORIES
        query=request.args.get('q','').strip()[:80]; category=request.args.get('category','')
        if query: role_list=[r for r in role_list if query.lower() in (r['title']+' '+r['category']+' '+r['description']+' '+' '.join(i['skill'] for i in r['required'])).lower()]
        if category: role_list=[r for r in role_list if r['category']==category]
        return render_template('roles.html', roles=role_list, record=record,categories=CATEGORIES,query=query,category=category)

    @app.route('/history')
    @login_required
    def history():
        try:
            page = max(1, int(request.args.get('page', 1)))
        except ValueError:
            page = 1
        page_size = 25
        summaries = g.repo.all_summaries()
        start = (page - 1) * page_size
        return render_template('history.html', records=summaries[start:start + page_size],
                               latest_ids={r['id'] for r in groups(summaries)}, page=page,
                               has_previous=page > 1, has_next=start + page_size < len(summaries))

    @app.route('/history/delete', methods=['POST'])
    @login_required
    def delete_history():
        sid = request.form.get('series_id', '')
        if not any(r['series_id'] == sid for r in g.repo.list()):
            abort(404)
        if request.form.get('confirm') != 'DELETE':
            flash('Type DELETE to remove this resume and all its versions.', 'error')
        else:
            g.repo.delete_series(sid)
            flash('Resume history removed.', 'success')
        return redirect(url_for('history'))

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile_page():
        data = g.profile
        if request.method == 'POST':
            data = {key: request.form.get(key, '').strip() for key in ('display_name', 'headline', 'location', 'goal_role')}
            if not 2 <= len(data['display_name']) <= 60 or len(data['headline']) > 120 or len(data['location']) > 80:
                flash('Use a name of 2–60 characters, a headline up to 120, and a location up to 80.', 'error')
            elif data['goal_role'] and data['goal_role'] not in {r['id'] for r in load_catalog()['roles']}:
                flash('Choose a goal role from the list.', 'error')
            else:
                g.repo.save_profile(data)
                app.extensions['profile_cache'].invalidate(g.user['id'])
                flash('Profile saved.', 'success')
                return redirect(url_for('profile_page'))
        return render_template('profile.html', data=data)

    @app.route('/evaluation')
    @login_required
    def evaluation():
        path = BASE_DIR / 'model/evaluation.json'
        metrics = json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
        extraction_path = BASE_DIR / 'model/extraction_evaluation.json'
        extraction_metrics = json.loads(extraction_path.read_text(encoding='utf-8')) if extraction_path.exists() else None
        return render_template('evaluation.html', metrics=metrics, extraction_metrics=extraction_metrics)

    @app.route('/help')
    @login_required
    def help_page():
        ready, message = vision_status(app.config)
        return render_template('help.html', vision_ready=ready, vision_message=message, vision_model=app.config['OLLAMA_MODEL'])

    @app.route('/results/<analysis_id>/download')
    @login_required
    def download(analysis_id):
        record = owned_record(analysis_id)
        payload = json.dumps(record, indent=2, ensure_ascii=False).encode('utf-8')
        return send_file(io.BytesIO(payload), mimetype='application/json', as_attachment=True,
                         download_name=f'resume_analysis_v{record["version"]}.json')

    @app.route('/samples/<filename>')
    @login_required
    def sample_file(filename):
        allowed = {'sample_resume.pdf', 'sample_resume.png', 'sample_phone_photo.jpg', 'sample_scanned_resume.pdf', 'sample_resume_v2.pdf', 'sample_job_description.txt'}
        if filename not in allowed:
            abort(404)
        return send_file(BASE_DIR / 'samples' / filename, as_attachment=True)

    @app.errorhandler(StoreError)
    def store_error(error):
        return render_template('error.html', code=503, message=str(error)), 503

    @app.errorhandler(413)
    def too_big(error):
        return render_template('error.html', code=413, message=f'This request is too large. Upload a resume smaller than {app.config["UPLOAD_MAX_MB"]} MB.'), 413

    @app.errorhandler(400)
    @app.errorhandler(404)
    def http_error(error):
        return render_template('error.html', code=error.code, message=error.description if error.code == 400 else 'This page or private record was not found.'), error.code

    @app.errorhandler(500)
    def unexpected(error):
        return render_template('error.html', code=500, message='The operation failed. Check the terminal, then try again.'), 500

    from career_routes import register_career_routes
    register_career_routes(app,login_required,owned_record)
    return app


app = create_app()

if __name__ == '__main__':
    print(f'Multimodal Resume Analyzer | mode={app.config["APP_MODE"]} | http://127.0.0.1:{os.getenv("PORT", "5000")}', flush=True)
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
