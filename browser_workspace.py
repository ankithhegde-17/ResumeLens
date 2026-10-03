"""Stateless, signed browser workspace. No database, account or cloud tokens.

The browser owns the payload; a signed anonymous cookie binds it to that browser.
Never trust unsigned JSON. Nothing sensitive is placed in the cookie or logs.
"""
import copy
import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import abort

MAX_STATE_BYTES = 2 * 1024 * 1024
LIFETIME = 86400

class BrowserStateRequired(Exception):
    pass

class ReadTransport:
    """POST body carries large browser state while routing as a read-only GET.

    The original POST is still CSRF-checked by prepare(). Only same-origin JS
    uses this marker. Form mutations never use it.
    """
    def __init__(self, application): self.application = application
    def __call__(self, environ, start_response):
        if environ.get('REQUEST_METHOD') == 'POST' and environ.get('HTTP_X_WORKSPACE_READ') == '1':
            environ['resumelens.read_transport'] = True
            environ['REQUEST_METHOD'] = 'GET'
        return self.application(environ, start_response)

class BrowserWorkspace:
    def __init__(self, secret, visitor, token=''):
        self.owner = hashlib.sha256(visitor.encode()).hexdigest()
        self.signer = URLSafeTimedSerializer(secret, salt='resumelens-browser-workspace-v1')
        self.data = {'owner':self.owner, 'records':[], 'drafts':{}, 'preferences':{}, 'progress':{}, 'hours':10, 'chat':{}}
        self.expired = False
        if token:
            if len(token) > MAX_STATE_BYTES * 2: abort(413)
            try: data = self.signer.loads(token, max_age=LIFETIME)
            except SignatureExpired:
                self.expired = True
                data = self.data
            except BadSignature: abort(400, description='Browser workspace data is invalid. Clear browser data and try again.')
            if not isinstance(data,dict) or data.get('owner') != self.owner:
                abort(404)
            self.data = data
        stamp=time.time()
        self.data['records'] = [r for r in self.data['records'] if r['expires'] > stamp]
        self.data['drafts'] = {k:v for k,v in self.data['drafts'].items() if v['expires'] > stamp}
        if self.data['chat'].get('expires',0) <= stamp: self.data['chat'] = {}

    def export(self):
        # Bound storage and request size; users can export JSON before expiry.
        raw=json.dumps(self.data,ensure_ascii=False).encode()
        if len(raw)>MAX_STATE_BYTES:
            raise ValueError('This browser workspace is full. Export or delete older analyses before adding another resume.')
        return self.signer.dumps(self.data)

    def profile(self): return copy.deepcopy(self.data['preferences'])
    def save_profile(self, value): self.data['preferences']=dict(value)
    def learning_state(self): return dict(self.data['progress']), self.data['hours']
    def save_learning(self, slug, status): self.data['progress'][slug]=status
    def save_schedule(self, hours): self.data['hours']=hours
    def list(self): return sorted(copy.deepcopy(self.data['records']),key=lambda r:(r['created_at'],r['version']),reverse=True)
    def all_summaries(self):
        return [dict(r,result={'roles':r['result']['roles'][:1], 'skills':[None]*len(r['result']['skills'])}) for r in self.list()]
    def get(self, analysis_id): return next((r for r in self.list() if r['id']==analysis_id),None)
    def save(self, draft_id, series_id, title, source_name, source_type, result):
        existing=self.get(draft_id)
        if existing: return existing
        version=max([r['version'] for r in self.data['records'] if r['series_id']==series_id] or [0])+1
        record=dict(id=draft_id,series_id=series_id,title=title,source_name=source_name,source_type=source_type,
                    version=version,created_at=datetime.now(timezone.utc).isoformat(),result=result,expires=time.time()+LIFETIME)
        self.data['records'].append(record)
        try: self.export()
        except ValueError:
            self.data['records'].pop()
            raise
        return copy.deepcopy(record)
    def delete_series(self, series_id): self.data['records']=[r for r in self.data['records'] if r['series_id']!=series_id]
    def save_draft(self, draft_id, data):
        old=self.data['drafts'].get(draft_id)
        self.data['drafts'][draft_id]={'payload':copy.deepcopy(data),'expires':time.time()+3600}
        try: self.export()
        except ValueError:
            if old: self.data['drafts'][draft_id]=old
            else: del self.data['drafts'][draft_id]
            raise
    def get_draft(self, draft_id):
        row=self.data['drafts'].get(draft_id)
        return copy.deepcopy(row['payload']) if row and row['expires']>time.time() else None
    def delete_draft(self, draft_id): self.data['drafts'].pop(draft_id,None)
    def chat(self): return copy.deepcopy(self.data['chat'].get('messages',[]))
    def save_chat(self, messages): self.data['chat']={'messages':messages[-8:],'expires':time.time()+3600}
    def clear(self):
        self.data.update(records=[],drafts={},preferences={},progress={},hours=10,chat={})

class InstanceRateLimits:
    """Bounded best-effort abuse protection, not a distributed quota guarantee."""
    def __init__(self): self.rows={}; self.lock=threading.Lock()
    def allow(self, bucket, maximum=6, window=600):
        key=hashlib.sha256(bucket.encode()).hexdigest(); stamp=time.time()
        with self.lock:
            self.rows={k:v for k,v in self.rows.items() if v[1]>stamp}
            count,reset=self.rows.get(key,(0,stamp+window))
            if count>=maximum or (key not in self.rows and len(self.rows)>=10000): return False
            self.rows[key]=(count+1,reset)
            return True
