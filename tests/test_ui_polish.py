"""UI hierarchy and transport contracts; fictional browser state only."""
import re
from pathlib import Path

from app import create_app
from browser_client import browser_app
from career_data import CAREERS
from test_app import analyze_sample


def client():
    return browser_app(create_app(dict(TESTING=True, SECRET_KEY='ui-test-only',
                                      EXTRACTION_ENGINE='ocr', GEMINI_API_KEY=''))).test_client()


def test_empty_dashboard_has_actions_not_zero_stats():
    html = client().get('/dashboard').get_data(as_text=True)
    assert 'class="stats-grid"' not in html
    assert 'Try sample resume' in html and 'Explore careers →' in html
    assert 'action="/upload"' in html and 'name="sample" value="pdf"' in html
    assert 'notice-mobile' in html and 'Export important results on shared devices.' in html


def test_upload_keeps_fields_and_promotes_optional_jd():
    html = client().get('/upload').get_data(as_text=True)
    assert html.index('id="job_description"') < html.index('class="upload-options"')
    assert 'Advanced options' in html
    for name in ['resume', 'title', 'series_id', 'engine', 'job_description', 'csrf_token']:
        assert f'name="{name}"' in html


def test_filters_reset_and_roadmap_actions_are_grouped():
    html = client().get('/roles?q=Python').get_data(as_text=True)
    assert html.index('Reset filters') < html.index('</form>')
    assert 'button ghost career-card-link' in html
    assert 'for="role-search"' in html and 'for="career-category"' in html


def test_result_hierarchy_keeps_evidence_models_and_deterministic_next_step():
    c = client()
    record, _ = analyze_sample(c)
    html = c.get('/results/' + record['id']).get_data(as_text=True)
    headings = ['Analysis summary', 'Top career matches', 'Your evidence profile',
                'Skills worth developing', 'YOUR NEXT STEP', 'Resume improvement notes',
                'Technical details · classifier', 'Reviewed source text']
    positions = [html.index(title) for title in headings]
    assert positions == sorted(positions)
    assert record['result']['roles'][0]['title'] in html
    assert 'Classifier role suggestions' in html and 'Source sample_resume.pdf' in html
    assert 'Recent analyses' in c.get('/dashboard').get_data(as_text=True)


def test_related_careers_only_use_existing_skill_membership():
    html = client().get('/skills/react').get_data(as_text=True)
    related = html.split('<h2>Related careers</h2>', 1)[1]
    for career in CAREERS:
        expected = 'React' in sum((career[key] for key in
                                  ['core', 'supporting', 'tools', 'fundamentals', 'advanced']), [])
        assert (f'/careers/{career["slug"]}' in related) == expected


def test_roadmap_learning_state_is_explicit_and_not_mastery():
    c = client()
    c.get('/skills/react')
    c.post('/learning/progress', data=dict(csrf_token=c.csrf, skill='react',
                                         status='learning', career='full-stack-developer'))
    html = c.get('/careers/full-stack-developer').get_data(as_text=True)
    assert '◐ Learning' in html and '○ Not yet evidenced' in html
    assert 'Detected in your resume does not necessarily mean mastered.' in html
    c.post('/learning/progress', data=dict(csrf_token=c.csrf, skill='react',
                                         status='completed', career='full-stack-developer'))
    assert 'Completed · self-reported' in c.get('/careers/full-stack-developer').get_data(as_text=True)


def test_css_tokens_and_single_phone_query():
    css = (Path(__file__).resolve().parents[1] / 'static/style.css').read_text(encoding='utf-8')
    assert len(re.findall(r'--text-[\w-]+:\d+px', css)) == 9  # eight UI sizes + the existing compact brand caption
    assert len(re.findall(r'--radius-[\w-]+:\d+px', css)) == 6
    assert not re.search(r'font-size:\d+px|border-radius:\d+(?:px|%)', css)
    assert css.count('@media(max-width:600px)') == 1
