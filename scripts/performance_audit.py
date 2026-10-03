"""Repeatable local hosted-mode benchmark using fictional data, never .env."""
import json
import os
import copy
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.update(VERCEL='1', SECRET_KEY='isolated-performance-benchmark', COOKIE_SECURE='true', GEMINI_API_KEY='')

if '--import-only' in sys.argv:
    started = time.perf_counter()
    import app
    print(json.dumps({'import_ms': round((time.perf_counter()-started)*1000, 2),
        'heavy_imports': [name for name in ('fitz', 'numpy', 'PIL.Image', 'joblib', 'sklearn') if name in sys.modules]}))
else:
    cold = [json.loads(subprocess.check_output([sys.executable, __file__, '--import-only'], text=True).strip().splitlines()[-1]) for _ in range(3)]
    from app import create_app
    app = create_app({'TESTING': True})
    client = app.test_client()
    routes = {}
    for route in ('/', '/dashboard', '/upload', '/careers', '/roles', '/careers/full-stack-developer', '/skills/react', '/evaluation', '/help'):
        timings = []
        for _ in range(6):
            started = time.perf_counter()
            response = client.get(route)
            timings.append((time.perf_counter()-started)*1000)
        routes[route] = {'status': response.status_code, 'first_ms': round(timings[0],2),
            'warm_median_ms': round(statistics.median(timings[1:]),2), 'html_bytes': len(response.data)}
    from analysis import analyze
    pages = [dict(number=1, text='Skills\nPython SQL Pandas Excel Git React HTML CSS\nProjects\nBuilt reports using Python and SQL.', engine='PDF text', confidence=None)]
    timings = []
    for _ in range(2):
        started = time.perf_counter()
        analyze(pages, {'Python','SQL','Pandas','Excel','Git','React','HTML','CSS'})
        timings.append(round((time.perf_counter()-started)*1000,2))
    from browser_workspace import BrowserWorkspace
    workspace=BrowserWorkspace('benchmark-secret','fictional-browser')
    result=analyze(pages,{'Python','SQL','Pandas','Excel','Git','React','HTML','CSS'})
    for index in range(20): workspace.save(str(index),str(index),'Fictional resume','fictional.pdf','PDF',result)
    # Real requests decode JSON: each record is independent, not shared Python objects.
    workspace=BrowserWorkspace('benchmark-secret','fictional-browser',workspace.export())
    old_times=[]; new_times=[]
    for _ in range(20):
        started=time.perf_counter()
        # Exact pre-optimization list-summary implementation, for CPU comparison.
        rows=sorted(copy.deepcopy(workspace.data['records']),key=lambda r:(r['created_at'],r['version']),reverse=True)
        old=[dict(r,result={'roles':r['result']['roles'][:1],'skills':[None]*len(r['result']['skills'])}) for r in rows]
        old_times.append((time.perf_counter()-started)*1000)
        started=time.perf_counter(); new=workspace.all_summaries(); new_times.append((time.perf_counter()-started)*1000)
    assert old==new
    files = sorted(({'name':p.name,'bytes':p.stat().st_size} for p in (ROOT/'static').iterdir() if p.is_file()), key=lambda p:-p['bytes'])
    published=sum(p.stat().st_size for p in (ROOT/'public/static').iterdir() if p.is_file()) if (ROOT/'public/static').exists() else None
    print(json.dumps({'import_median_ms': statistics.median(row['import_ms'] for row in cold),
        'heavy_imports':cold[0]['heavy_imports'], 'routes':routes, 'analysis_first_cached_ms':timings,
        'summary_20_records_before_after_ms':[round(statistics.median(old_times),2),round(statistics.median(new_times),2)],
        'static_total_bytes':sum(row['bytes'] for row in files),'published_static_bytes':published,'assets':files}, indent=2))
