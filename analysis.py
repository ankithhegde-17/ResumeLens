"""The score is an explicit skill rubric; ML is a separate educational signal."""
import json
from functools import lru_cache
import joblib
from config import BASE_DIR
from skills import candidates, names_from_text


@lru_cache(maxsize=1)
def load_catalog():
    catalog = json.loads((BASE_DIR / 'data/role_catalog.json').read_text(encoding='utf-8'))
    from career_data import CAREERS, BY_ID, compact_role
    from skill_guides import SKILL_GUIDES
    original_ids = {r['id'] for r in catalog['roles']}
    # Preserve the original eight rubrics and the existing classifier/evaluation.
    for role in catalog['roles']:
        career = BY_ID[role['id']]
        role.update(slug=career['slug'], category=career['category'])
    catalog['roles'].extend(compact_role(c) for c in CAREERS if c['id'] not in original_ids)
    catalog['version'] = '2026.10-careers-v2'
    catalog['scope'] = '18 educational career paths; not hiring predictions or live jobs.'
    catalog['learning'].update({name: dict(step=s['description'], practice=s['practice'], url=s['resources'][0]['url']) for name,s in SKILL_GUIDES.items()})
    return catalog


@lru_cache(maxsize=1)
def model_bundle():
    path = BASE_DIR / 'model/role_classifier.joblib'
    if not path.exists():
        raise ValueError('Model missing. Run python train_model.py, then restart the app.')
    return joblib.load(path)


def match_role(role, skills, learning):
    matched = [dict(item, evidence=skills[item['skill']]['evidence'])
               for item in role['required'] if item['skill'] in skills]
    missing = [dict(item, learning=learning.get(item['skill'], {}))
               for item in role['required'] if item['skill'] not in skills]
    earned = sum(i['weight'] for i in matched)
    total = sum(i['weight'] for i in role['required'])
    return dict(role, matched=matched, missing=missing, earned_weight=earned, total_weight=total,
                score=round(100 * earned / total, 1),
                optional_found=[s for s in role['optional'] if s in skills])


def analyze(pages, selected, jd=''):
    all_skills = candidates(pages)
    present = {s['name']: dict(s, reviewed=True) for s in all_skills if s['name'] in selected}
    if not present:
        raise ValueError('Confirm at least one evidenced skill before analysis.')
    catalog = load_catalog()
    roles = sorted([match_role(r, present, catalog['learning']) for r in catalog['roles']],
                   key=lambda r: (-r['score'], r['title']))
    # Avoid names, contact lines and unrelated resume prose in the classifier input.
    # The classifier consumes only user-confirmed normalized skill names.
    classifier_text = ' '.join(sorted(present))
    bundle = model_bundle()
    probabilities = bundle['pipeline'].predict_proba([classifier_text])[0]
    labels = bundle['pipeline'].classes_
    indexes = probabilities.argsort()[::-1][:3]
    title_map = {r['id']: r['title'] for r in roles}
    ml = [dict(role_id=str(labels[i]), title=title_map[str(labels[i])], probability=round(float(probabilities[i]) * 100, 1)) for i in indexes]
    jd_result = None
    if jd.strip():
        requirements = names_from_text(jd)
        if not requirements:
            raise ValueError('The job description contains no supported skill names. Add explicit requirements or clear the optional field.')
        spec = dict(id='custom-jd', title='Your job description', description='All recognized mentions are treated as equal requirements.',
                    required=[dict(skill=s, weight=1) for s in requirements], optional=[], project='Review the actual employer requirements before applying.')
        jd_result = match_role(spec, present, catalog['learning'])
    text = '\n'.join(p['text'] for p in pages)
    sections = []
    headings = {'education': 'Education', 'projects': 'Projects', 'experience': 'Experience',
                'work experience': 'Experience', 'certifications': 'Certifications', 'skills': 'Skills',
                'technical skills': 'Skills'}
    for line in text.splitlines():
        normalized = line.strip().rstrip(':').lower()
        if normalized in headings and headings[normalized] not in sections:
            sections.append(headings[normalized])
    return dict(skills=list(present.values()), roles=roles, ml=ml, jd=jd_result,
                job_description=jd, pages=pages, sections=sections,
                suggestions=['Keep clear headings for skills, education and projects.',
                             'Support skills with a specific project or experience example.',
                             'Document relevant skills truthfully; an absent skill is not proof that you lack it.'],
                catalog_version=catalog['version'], model_version=bundle['version'],
                classifier_input=classifier_text)


def compare_results(current, previous):
    if not previous:
        return None
    now = current['result']; old = previous['result']
    a, b = {s['name'] for s in now['skills']}, {s['name'] for s in old['skills']}
    old_scores = {r['id']: r['score'] for r in old['roles']}
    top = now['roles'][0]
    comparable = now['catalog_version'] == old['catalog_version']
    return dict(added=sorted(a - b), removed=sorted(b - a), previous_version=previous['version'],
                same_catalog=comparable, role=top['title'],
                delta=round(top['score'] - old_scores.get(top['id'], 0), 1) if comparable else None,
                score_changes=[dict(title=r['title'], delta=round(r['score'] - old_scores.get(r['id'], 0), 1))
                               for r in now['roles'] if comparable and r['score'] != old_scores.get(r['id'], 0)])
