"""Small route extension; current routes and saved analysis snapshots stay intact."""
import hashlib
import time
from flask import abort, flash, g, jsonify, redirect, render_template, request, url_for
from analysis import load_catalog, match_role
from career_data import BY_SLUG, BY_ID, DISCLAIMER, alignment_label, personalize
from skill_guides import SKILL_GUIDES, GUIDES_BY_SLUG
from career_assistant import REFUSAL, AssistantError, clean_message, in_scope, curated_answer, gemini_reply

STATUSES = {'not_started','learning','completed'}

def register_career_routes(app, owned_record):

    def selected_record():
        analysis_id = request.values.get('analysis','')
        if analysis_id:
            return owned_record(analysis_id)
        # Get complete evidence only for the selected/latest owned record.
        rows = g.repo.all_summaries()
        return g.repo.get(rows[0]['id']) if rows else None

    def state():
        progress,hours=g.repo.learning_state()
        return progress,hours,True

    @app.context_processor
    def career_common():
        return dict(career_slug=lambda id: BY_ID[id]['slug'] if id in BY_ID else '', career_disclaimer=DISCLAIMER)

    @app.route('/careers/<slug>')
    def career_detail(slug):
        career = BY_SLUG.get(slug)
        if not career: abort(404)
        record = selected_record()
        progress,hours,available = state()
        mapping = {s['name']:s for s in record['result']['skills']} if record else {}
        spec = next(r for r in load_catalog()['roles'] if r['id']==career['id'])
        alignment = match_role(spec,mapping,load_catalog()['learning']) if record else None
        return render_template('career_detail.html',career=career,guides=SKILL_GUIDES,record=record,alignment=alignment,
                               alignment_label=alignment_label(alignment['score']) if alignment else 'Upload a resume to personalize',
                               plan=personalize(career,record,progress,hours),hours=hours,progress_available=available,
                               evidenced=[name for name in dict.fromkeys(career['core']+career['supporting']+career['tools']+career['fundamentals']) if name in mapping],
                               strengthen=[name for name in career['core'] if progress.get(SKILL_GUIDES[name]['slug'])=='learning'],
                               missing=[name for name in career['core'] if name not in mapping])

    @app.route('/skills/<slug>')
    def skill_detail(slug):
        skill = GUIDES_BY_SLUG.get(slug)
        if not skill: abort(404)
        record=selected_record()
        progress,hours,available=state()
        career=BY_SLUG.get(request.args.get('career',''))
        cost=request.args.get('cost','Free'); level=request.args.get('level',''); kind=request.args.get('format','')
        resources=[r for r in skill['resources'] if (not cost or r['cost']==cost) and (not level or r['level']==level) and (not kind or r['format']==kind)]
        return render_template('skill_detail.html',skill=skill,career=career,record=record,
                               detected=any(s['name']==skill['name'] for s in record['result']['skills']) if record else False,
                               status=progress.get(slug,'not_started'),hours=hours,progress_available=available,
                               weeks=tuple(round(n/hours,1) for n in skill['hours']), resources=resources,
                               guides=SKILL_GUIDES,filters=dict(cost=cost,level=level,format=kind),
                               related_careers=[item for item in BY_ID.values() if skill['name'] in
                                                item['core'] + item['supporting'] + item['tools'] + item['fundamentals'] + item['advanced']])

    @app.route('/learning/progress',methods=['POST'])
    def learning_progress():
        slug=request.form.get('skill',''); status=request.form.get('status','')
        if slug not in GUIDES_BY_SLUG or status not in STATUSES: abort(400,description='Choose a supported skill and progress status.')
        career=BY_SLUG.get(request.form.get('career',''))
        analysis_id=request.form.get('analysis','')
        if analysis_id: owned_record(analysis_id)
        g.repo.save_learning(slug,status)
        flash('Learning progress saved. This does not change your resume evidence or alignment score.','success')
        return redirect(url_for('career_detail',slug=career['slug'],analysis=analysis_id)) if career else redirect(url_for('skill_detail',slug=slug,analysis=analysis_id))

    @app.route('/learning/schedule',methods=['POST'])
    def learning_schedule():
        try: hours=int(request.form.get('hours',''))
        except ValueError: abort(400)
        career=BY_SLUG.get(request.form.get('career',''))
        if hours not in (5,10,20) or not career: abort(400)
        analysis_id=request.form.get('analysis','')
        if analysis_id: owned_record(analysis_id)
        g.repo.save_schedule(hours)
        flash('Study schedule updated. Estimates are planning ranges, not proficiency guarantees.','success')
        return redirect(url_for('career_detail',slug=career['slug'],analysis=analysis_id))

    @app.route('/api/career-assistant',methods=['POST'])
    def career_chat():
        # Both browser and network limits; no account or provider tokens needed.
        bucket=g.repo.owner
        network=hashlib.sha256((request.remote_addr or 'local').encode()).hexdigest()
        if request.form.get('action')=='new':
            g.repo.save_chat([])
            return jsonify(answer='New conversation started.',source='local')
        message=request.form.get('message','').strip()
        if not 1<=len(message)<=1200:
            return jsonify(error='Use a message of 1–1,200 characters.'),400
        try: message=clean_message(message)
        except ValueError as exc: return jsonify(error=str(exc)),400
        # Fail closed for clearly unrelated/injection requests without API usage.
        if not in_scope(message): return jsonify(answer=REFUSAL,source='scope')
        limits=app.extensions['rate_limits']
        if not limits.allow('career:network:'+network,30,60) or not limits.allow('career:minute:'+bucket,12,60) or not limits.allow('career:day:'+bucket,60,86400) or not limits.allow('career:gap:'+bucket,1,2):
            return jsonify(error='Please slow down. Career AI has a browser request limit; try again later.'),429
        local=curated_answer(message)
        if local: return jsonify(answer=local,source='curated')
        if request.form.get('consent')!='yes':
            return jsonify(error='Opt in to sending your question and limited skill context to Google, or use the local skill guides.'),400
        # Only use server-checked owned analysis and normalized catalog values.
        record=selected_record()
        career=BY_SLUG.get(request.form.get('career',''))
        context={}
        if record:
            context['detected_skills']=[s['name'] for s in record['result']['skills'] if s['name'] in SKILL_GUIDES][:60]
            context['recommended_careers']=[dict(title=r['title'],score=r['score']) for r in record['result']['roles'][:3]]
            jd=record['result'].get('jd')
            if jd: context['jd']={'matched':[s['skill'] for s in jd['matched']][:30],'not_detected':[s['skill'] for s in jd['missing']][:30]}
        if career:
            progress,hours,_=state()
            plan=personalize(career,record,progress,hours)
            context.update(selected_career=career['title'],schedule_hours=hours,
                           roadmap=[dict(skill=s['name'],detected=s['detected'],progress=s['status'],effort_hours=s['hours']) for s in plan['steps']],
                           next_step=plan['next_step']['name'] if plan['next_step'] else 'Review and build projects')
        history=g.repo.chat()
        started = time.perf_counter()
        try: answer=gemini_reply(app.config,message,context,history)
        except AssistantError as exc: return jsonify(error=str(exc)),exc.status
        finally: app.extensions['metrics'].record('inference:gemini',time.perf_counter()-started)
        g.repo.save_chat(history+[dict(role='user',text=message),dict(role='assistant',text=answer)])
        return jsonify(answer=answer,source='gemini')
