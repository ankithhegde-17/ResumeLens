"""Beginner-friendly Flask routes. Run with: python app.py"""
import hmac
import hashlib
import io
import json
import os
import secrets
import uuid
import time
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.utils import secure_filename
from config import BASE_DIR, settings
from browser_workspace import BrowserWorkspace, BrowserStateRequired, ReadTransport, InstanceRateLimits
from extraction import extract_document, vision_status, MAX_PAGE_TEXT, MAX_TOTAL_TEXT
from skills import candidates
from analysis import analyze, compare_results, load_catalog, match_role, evaluation_data
from performance import PerformanceMetrics
from flask import before_render_template, template_rendered


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(settings())
    if overrides:
        app.config.update(overrides)
    app.wsgi_app = ReadTransport(app.wsgi_app)
    app.extensions['metrics'] = PerformanceMetrics(diagnostics=app.config.get('PERFORMANCE_DIAGNOSTICS',False))
    app.extensions['rate_limits'] = InstanceRateLimits()
    # Content fingerprints survive redeploys; unchanged assets stay browser-cached.
    asset_versions = {}

    def template_start(sender, **extra):
        g.template_started = time.perf_counter()

    def template_end(sender, template, **extra):
        app.extensions['metrics'].record('template:' + (template.name or 'inline'), time.perf_counter() - g.template_started)

    before_render_template.connect(template_start, app, weak=False)
    template_rendered.connect(template_end, app, weak=False)

    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return session['csrf']

    def asset_url(filename):
        if filename not in asset_versions:
            path = BASE_DIR / 'static' / filename
            asset_versions[filename] = hashlib.sha256(path.read_bytes()).hexdigest()[:12] if path.exists() else 'missing'
        version = asset_versions[filename]
        return url_for('static', filename=filename, v=version)

    @app.before_request
    def prepare():
        g.request_started = time.perf_counter()
        # Static files must never create cookies or load browser workspace data.
        if request.endpoint == 'static':
            g.repo = None
            g.profile = {}
            return
        body = request.get_json(silent=True) if request.is_json else {}
        body = body if isinstance(body,dict) else {}
        if request.method == 'POST' or request.environ.get('resumelens.read_transport'):
            received = request.form.get('csrf_token', '') or body.get('csrf_token','')
            if not isinstance(received,str) or not received or not hmac.compare_digest(received, session.get('csrf', '')):
                abort(400, description='The form expired. Reload the page and try again.')
        # Retire old authentication cookie contents; keep only anonymous UI state.
        for key in list(session):
            if key not in ('visitor','csrf','_flashes'): session.pop(key,None)
        visitor=session.get('visitor')
        if not isinstance(visitor,str) or len(visitor)!=43:
            visitor=secrets.token_urlsafe(32)
            session['visitor']=visitor
        state=request.form.get('workspace_state','') or body.get('workspace_state','')
        if request.endpoint=='clear_workspace': state=''  # Clear must work even for invalid/expired stored state.
        if not isinstance(state,str): abort(400,description='Invalid browser workspace data.')
        g.state_loaded=bool(state)
        g.repo=BrowserWorkspace(app.config['SECRET_KEY'],visitor,state)
        g.profile=g.repo.profile()
        if g.repo.expired: flash('Your temporary browser workspace expired. Start a new analysis.','info')

    @app.context_processor
    def common():
        repo=g.get('repo')
        return dict(csrf_token=csrf_token, asset_url=asset_url, upload_max_mb=app.config['UPLOAD_MAX_MB'], hosted=app.config.get('VERCEL_HOSTED'), profile=g.get('profile', {}),
                    workspace_payload={'owner':repo.owner,'state':repo.export(),'loaded':g.get('state_loaded',False),'has_data':repo.has_data()} if repo else None,
                    role_catalog=load_catalog()['roles'] if request.endpoint in ('dashboard', 'profile_page') else [])

    @app.after_request
    def headers(response):
        if g.get('repo') and request.headers.get('X-Workspace-Client'):
            state=g.repo.export()
            if 300<=response.status_code<400 and response.headers.get('Location'):
                location=response.headers['Location']
                code=response.status_code if request.headers.get('X-Workspace-Client')=='test' else 200
                response=jsonify(redirect=location,workspace_state=state,workspace_has_data=g.repo.has_data())
                response.status_code=code
                response.headers['Location']=location
            elif response.is_json and request.endpoint=='career_chat':
                body=response.get_json()
                body['workspace_state']=state
                body['workspace_has_data']=g.repo.has_data()
                response.set_data(app.json.dumps(body))
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        # Allow only the exact early appearance initializer, not arbitrary inline JS.
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self' 'sha256-dwPoMm1GbJJod5KxqugXSbhGObxG59VSQrFKebdn+wI='; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        response.headers['Cache-Control'] = ('public, max-age=31536000, immutable' if request.args.get('v') else 'public, max-age=3600') if request.endpoint == 'static' else 'no-store'
        if hasattr(g, 'request_started'):
            elapsed = time.perf_counter() - g.request_started
            app.extensions['metrics'].record('page:' + (request.endpoint or 'unknown'), elapsed)
            if app.config.get('PERFORMANCE_DIAGNOSTICS'):
                response.headers['Server-Timing'] = f'app;dur={elapsed*1000:.2f}'
        return response

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
            if not g.state_loaded and request.method=='GET': raise BrowserStateRequired()
            abort(404)
        return record

    @app.route('/login')
    @app.route('/verify')
    def retired_auth():
        return redirect(url_for('dashboard'))

    @app.route('/terms')
    def terms_page():
        return render_template('terms.html')

    @app.route('/workspace/clear', methods=['POST'])
    def clear_workspace():
        if request.form.get('confirm')!='CLEAR': abort(400,description='Type CLEAR to remove this browser workspace.')
        g.repo.clear()
        session['visitor']=secrets.token_urlsafe(32)
        g.repo=BrowserWorkspace(app.config['SECRET_KEY'],session['visitor'])
        g.profile={}
        flash('Temporary browser data cleared.','success')
        return redirect(url_for('dashboard'))

    @app.route('/')
    @app.route('/dashboard')
    def dashboard():
        records = g.repo.list(); latest = groups(records)
        return render_template('dashboard.html', latest=latest, records=records, current=latest[0] if latest else None)

    @app.route('/upload', methods=['GET', 'POST'])
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
                g.repo.save_draft(draft_id, draft)
                return redirect(url_for('review', draft_id=draft_id))
            except ValueError as exc:
                flash(str(exc), 'error')
        return render_template('upload.html', existing=existing, selected_series=request.args.get('series', ''), values=request.form)

    @app.route('/review/<draft_id>', methods=['GET', 'POST'])
    def review(draft_id):
        draft = g.repo.get_draft(draft_id)
        if not draft:
            if not g.state_loaded and request.method=='GET': raise BrowserStateRequired()
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
                g.repo.save_draft(draft_id, draft)
                if request.form.get('action') == 'refresh':
                    flash('Skill list refreshed from your edited text. Confirm it below.', 'success')
                else:
                    selected = request.form.getlist('skills')
                    if request.form.get('confirmed') != 'yes':
                        raise ValueError('Confirm that you reviewed the extracted text and selected skills.')
                    supported = {s['name'] for s in candidates(pages)}
                    if not set(selected).issubset(supported):
                        raise ValueError('The text changed. Refresh the skill list before analyzing.')
                    analysis_started = time.perf_counter()
                    output = analyze(pages, selected, draft['job_description'])
                    app.extensions['metrics'].record('inference:analysis', time.perf_counter()-analysis_started)
                    output['extraction_notes'] = draft['notes']
                    g.repo.save(draft_id, draft['series_id'], draft['title'], draft['source_name'], draft['source_type'], output)
                    g.repo.delete_draft(draft_id)
                    return redirect(url_for('result', analysis_id=draft_id))
            except ValueError as exc:
                flash(str(exc), 'error')
        found = candidates(draft['pages'])
        if selected is None:
            selected = [s['name'] for s in found if not s['caution']]
        return render_template('review.html', draft=draft, draft_id=draft_id, found=found, selected=selected)

    @app.route('/results/<analysis_id>')
    def result(analysis_id):
        record = owned_record(analysis_id)
        history = [r for r in g.repo.list() if r['series_id'] == record['series_id']]
        previous = next((r for r in history if r['version'] == record['version'] - 1), None)
        return render_template('result.html', record=record, output=record['result'], history=history,
                               is_current=record['version'] == max(r['version'] for r in history),
                               comparison=compare_results(record, previous))

    @app.route('/careers')
    @app.route('/roles')
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
                flash('Browser preferences saved.', 'success')
                return redirect(url_for('profile_page'))
        return render_template('profile.html', data=data)

    @app.route('/evaluation')
    def evaluation():
        metrics = evaluation_data('evaluation.json')
        extraction_metrics = evaluation_data('extraction_evaluation.json')
        return render_template('evaluation.html', metrics=metrics, extraction_metrics=extraction_metrics)

    @app.route('/help')
    def help_page():
        ready, message = vision_status(app.config)
        return render_template('help.html', vision_ready=ready, vision_message=message, vision_model=app.config['OLLAMA_MODEL'])

    @app.route('/results/<analysis_id>/download')
    def download(analysis_id):
        record = owned_record(analysis_id)
        payload = json.dumps(record, indent=2, ensure_ascii=False).encode('utf-8')
        return send_file(io.BytesIO(payload), mimetype='application/json', as_attachment=True,
                         download_name=f'resume_analysis_v{record["version"]}.json')

    @app.route('/samples/<filename>')
    def sample_file(filename):
        allowed = {'sample_resume.pdf', 'sample_resume.png', 'sample_phone_photo.jpg', 'sample_scanned_resume.pdf', 'sample_resume_v2.pdf', 'sample_job_description.txt'}
        if filename not in allowed or (app.config.get('VERCEL_HOSTED') and filename=='sample_scanned_resume.pdf'):
            abort(404)
        return send_file(BASE_DIR / 'samples' / filename, as_attachment=True)

    @app.errorhandler(BrowserStateRequired)
    def restore_workspace(error):
        return render_template('workspace_restore.html')

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
    register_career_routes(app,owned_record)
    return app


app = create_app()

if __name__ == '__main__':
    print(f'Multimodal Resume Analyzer | mode={app.config["APP_MODE"]} | http://127.0.0.1:{os.getenv("PORT", "5000")}', flush=True)
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
