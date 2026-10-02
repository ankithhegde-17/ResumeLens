"""Two small repositories with the same interface: demo SQLite and Supabase REST."""
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
import requests


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class StoreError(Exception):
    pass


class RuntimeDB:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS auth_sessions (
                id TEXT PRIMARY KEY, mode TEXT NOT NULL, payload TEXT NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS challenges (
                email TEXT PRIMARY KEY, digest TEXT NOT NULL, expires REAL NOT NULL, attempts INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS rate_limits (bucket TEXT PRIMARY KEY, count INTEGER NOT NULL, reset REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS drafts (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, payload TEXT NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, series_id TEXT NOT NULL,
                title TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL,
                source_name TEXT NOT NULL, source_type TEXT NOT NULL, result TEXT NOT NULL,
                UNIQUE(user_id, series_id, version));
            CREATE INDEX IF NOT EXISTS analyses_owner ON analyses(user_id, created_at);
            CREATE TABLE IF NOT EXISTS learning_progress (
                user_id TEXT NOT NULL, skill_slug TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('not_started','learning','completed')),
                updated_at TEXT NOT NULL, PRIMARY KEY(user_id,skill_slug));
            CREATE TABLE IF NOT EXISTS learning_settings (
                user_id TEXT PRIMARY KEY, hours INTEGER NOT NULL CHECK(hours IN (5,10,20)));
            CREATE TABLE IF NOT EXISTS career_chats (
                session_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, payload TEXT NOT NULL, expires REAL NOT NULL);
            ''')
            stamp = time.time()
            for table in ('auth_sessions', 'challenges', 'drafts', 'career_chats'):
                db.execute(f'DELETE FROM {table} WHERE expires < ?', (stamp,))
            db.execute('DELETE FROM rate_limits WHERE reset < ?', (stamp,))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def rate_allow(self, bucket, maximum=6, window=600):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM rate_limits WHERE bucket=?', (bucket,)).fetchone()
            if not row or row['reset'] <= time.time():
                db.execute('INSERT OR REPLACE INTO rate_limits VALUES (?,1,?)', (bucket, time.time() + window))
                return True
            if row['count'] >= maximum:
                return False
            db.execute('UPDATE rate_limits SET count=count+1 WHERE bucket=?', (bucket,))
            return True

    def set_session(self, session_id, mode, data, expires):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO auth_sessions VALUES (?,?,?,?)',
                       (session_id, mode, json.dumps(data), expires))

    def get_session(self, session_id, mode):
        with self.connect() as db:
            row = db.execute('SELECT * FROM auth_sessions WHERE id=? AND mode=? AND expires>?',
                             (session_id, mode, time.time())).fetchone()
        return json.loads(row['payload']) if row else None

    def delete_session(self, session_id):
        with self.connect() as db:
            db.execute('DELETE FROM auth_sessions WHERE id=?', (session_id,))
            db.execute('DELETE FROM career_chats WHERE session_id=?', (session_id,))

    def chat(self, sid, uid):
        with self.connect() as db:
            db.execute('DELETE FROM career_chats WHERE expires < ?', (time.time(),))
            row = db.execute('SELECT payload FROM career_chats WHERE session_id=? AND user_id=?', (sid, uid)).fetchone()
        return json.loads(row['payload']) if row else []

    def save_chat(self, sid, uid, messages):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO career_chats VALUES (?,?,?,?)', (sid,uid,json.dumps(messages[-8:]),time.time()+3600))

    def save_draft(self, draft_id, uid, data):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO drafts VALUES (?,?,?,?)',
                       (draft_id, uid, json.dumps(data), time.time() + 3600))

    def get_draft(self, draft_id, uid):
        with self.connect() as db:
            db.execute('DELETE FROM drafts WHERE expires < ?', (time.time(),))
            row = db.execute('SELECT payload FROM drafts WHERE id=? AND user_id=?', (draft_id, uid)).fetchone()
        return json.loads(row['payload']) if row else None

    def delete_draft(self, draft_id, uid):
        with self.connect() as db:
            db.execute('DELETE FROM drafts WHERE id=? AND user_id=?', (draft_id, uid))


class LocalRepository:
    def __init__(self, runtime, user):
        self.runtime, self.uid = runtime, user['id']

    def profile(self):
        with self.runtime.connect() as db:
            row = db.execute('SELECT payload FROM profiles WHERE user_id=?', (self.uid,)).fetchone()
        return json.loads(row['payload']) if row else {}

    def save_profile(self, profile):
        with self.runtime.connect() as db:
            db.execute('INSERT OR REPLACE INTO profiles VALUES (?,?)', (self.uid, json.dumps(profile)))

    def learning_state(self):
        with self.runtime.connect() as db:
            rows = db.execute('SELECT skill_slug,status FROM learning_progress WHERE user_id=?',(self.uid,)).fetchall()
            row = db.execute('SELECT hours FROM learning_settings WHERE user_id=?',(self.uid,)).fetchone()
        return {r['skill_slug']:r['status'] for r in rows}, row['hours'] if row else 10

    def save_learning(self, skill_slug, status):
        with self.runtime.connect() as db:
            db.execute('INSERT OR REPLACE INTO learning_progress VALUES (?,?,?,?)',(self.uid,skill_slug,status,now_iso()))

    def save_schedule(self, hours):
        with self.runtime.connect() as db:
            db.execute('INSERT OR REPLACE INTO learning_settings VALUES (?,?)',(self.uid,hours))

    @staticmethod
    def decode(row):
        if not row:
            return None
        record = dict(row)
        record['result'] = json.loads(record['result'])
        return record

    def list(self):
        with self.runtime.connect() as db:
            rows = db.execute('SELECT * FROM analyses WHERE user_id=? ORDER BY created_at DESC, version DESC', (self.uid,)).fetchall()
        return [self.decode(row) for row in rows]

    def list_summaries(self, page=1, page_size=25):
        """History rows only need metadata plus the small score/skill summary."""
        offset = (page - 1) * page_size
        with self.runtime.connect() as db:
            total = db.execute('SELECT COUNT(*) FROM analyses WHERE user_id=?', (self.uid,)).fetchone()[0]
            rows = db.execute('SELECT id,series_id,title,version,created_at,source_name,source_type,result FROM analyses WHERE user_id=? ORDER BY created_at DESC,version DESC LIMIT ? OFFSET ?',
                              (self.uid, page_size, offset)).fetchall()
        output = []
        for row in rows:
            record = dict(row); result = json.loads(record.pop('result'))
            record['result'] = {'roles': result.get('roles', [])[:1], 'skills': result.get('skills', [])}
            output.append(record)
        return output, total

    def all_summaries(self):
        with self.runtime.connect() as db:
            rows = db.execute("SELECT id,series_id,title,version,created_at,source_name,source_type,json_extract(result,'$.roles[0]') AS top_role,json_array_length(result,'$.skills') AS skill_count FROM analyses WHERE user_id=? ORDER BY created_at DESC,version DESC", (self.uid,)).fetchall()
        return [dict(row, result={'roles': [json.loads(row['top_role'])] if row['top_role'] else [],
                                       'skills': [None] * (row['skill_count'] or 0)}) for row in rows]

    def get(self, analysis_id):
        with self.runtime.connect() as db:
            row = db.execute('SELECT * FROM analyses WHERE id=? AND user_id=?', (analysis_id, self.uid)).fetchone()
        return self.decode(row)

    def save(self, draft_id, series_id, title, source_name, source_type, result):
        with self.runtime.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT * FROM analyses WHERE id=? AND user_id=?', (draft_id, self.uid)).fetchone()
            if existing:
                return self.decode(existing)
            previous = db.execute('SELECT MAX(version) FROM analyses WHERE series_id=? AND user_id=?', (series_id, self.uid)).fetchone()[0]
            record = dict(id=draft_id, user_id=self.uid, series_id=series_id, title=title,
                          version=(previous or 0) + 1, created_at=now_iso(), source_name=source_name,
                          source_type=source_type, result=result)
            db.execute('INSERT INTO analyses VALUES (?,?,?,?,?,?,?,?,?)',
                       tuple(record[k] for k in ('id', 'user_id', 'series_id', 'title', 'version', 'created_at', 'source_name', 'source_type')) + (json.dumps(result),))
        return record

    def delete_series(self, series_id):
        with self.runtime.connect() as db:
            db.execute('DELETE FROM analyses WHERE user_id=? AND series_id=?', (self.uid, series_id))


class SupabaseRepository:
    def __init__(self, cfg, user, metrics=None):
        self.url = cfg['SUPABASE_URL'] + '/rest/v1/'
        self.headers = {'apikey': cfg['SUPABASE_PUBLISHABLE_KEY'],
                        'Authorization': 'Bearer ' + user['access_token'], 'Content-Type': 'application/json'}
        self.uid = user['id']
        self.metrics = metrics
        # A repository is created per request/user, so its pooled connection never crosses auth identities.
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        started = time.perf_counter()
        try:
            response = self.session.request(method, self.url + path, headers=self.headers, timeout=20, **kwargs)
        except requests.RequestException as exc:
            raise StoreError('Cannot reach Supabase. Check your internet connection and project URL.') from exc
        finally:
            if self.metrics:
                self.metrics.record('supabase:' + method + ':' + path.split('?', 1)[0], time.perf_counter() - started)
        if not response.ok:
            if response.status_code == 401:
                raise StoreError('Your cloud session expired. Sign out and request a new code.')
            if response.status_code in (404, 400):
                raise StoreError('Supabase setup is incomplete. Run database/supabase_schema.sql and check the public key.')
            raise StoreError('Supabase rejected the operation. Check the database grants and owner policies in the setup guide.')
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise StoreError('Supabase returned an invalid response.') from exc

    def profile(self):
        rows = self.request('GET', 'profiles', params={'user_id': 'eq.' + self.uid, 'select': '*'})
        return rows[0] if rows else {}

    def learning_state(self):
        rows = self.request('GET','learning_progress',params={'user_id':'eq.'+self.uid,'select':'skill_slug,status','limit':200})
        settings = self.request('GET','learning_settings',params={'user_id':'eq.'+self.uid,'select':'hours'})
        return {r['skill_slug']:r['status'] for r in rows}, settings[0]['hours'] if settings else 10

    def learning_upsert(self, table, data, conflict):
        old = self.headers.get('Prefer')
        self.headers['Prefer'] = 'resolution=merge-duplicates'
        try:
            self.request('POST',table,params={'on_conflict':conflict},json=dict(data,user_id=self.uid))
        finally:
            if old: self.headers['Prefer'] = old
            else: self.headers.pop('Prefer',None)

    def save_learning(self, skill_slug, status):
        self.learning_upsert('learning_progress',dict(skill_slug=skill_slug,status=status,updated_at=now_iso()),'user_id,skill_slug')

    def save_schedule(self, hours):
        self.learning_upsert('learning_settings',dict(hours=hours),'user_id')

    def save_profile(self, profile):
        # Upsert needs both INSERT and UPDATE policies, both restricted to auth.uid().
        old = self.headers.get('Prefer')
        self.headers['Prefer'] = 'resolution=merge-duplicates'
        try:
            self.request('POST', 'profiles', params={'on_conflict': 'user_id'}, json=dict(profile, user_id=self.uid))
        finally:
            if old:
                self.headers['Prefer'] = old
            else:
                self.headers.pop('Prefer', None)

    def list(self):
        rows, offset = [], 0
        # Avoid Supabase's default 1000-row truncation when finding latest versions.
        while True:
            batch = self.request('GET', 'analyses', params={'user_id': 'eq.' + self.uid, 'select': '*',
                                'order': 'created_at.desc,version.desc', 'limit': 500, 'offset': offset})
            rows.extend(batch)
            if len(batch) < 500:
                return rows
            offset += len(batch)

    def list_summaries(self, page=1, page_size=25):
        # Keep list pages fast: full result JSON is fetched only by get() on a detail page.
        rows = self.request('GET', 'analyses', params={'user_id': 'eq.' + self.uid,
                            'select': 'id,series_id,title,version,created_at,source_name,source_type,result->roles,result->skills',
                            'order': 'created_at.desc,version.desc', 'limit': page_size,
                            'offset': (page - 1) * page_size, 'count': 'exact'})
        # PostgREST count lives in Content-Range, which this small client intentionally does not retain.
        # A separate HEAD request gives exact pagination without transferring analysis results.
        response = self.session.head(self.url + 'analyses', headers=dict(self.headers, Prefer='count=exact'),
                                     params={'user_id': 'eq.' + self.uid}, timeout=20)
        total = int(response.headers.get('Content-Range', '*/0').split('/')[-1]) if response.ok else len(rows)
        normalized = []
        for row in rows:
            item = dict(row)
            roles = item.pop('result->roles', item.pop('roles', []))
            skills = item.pop('result->skills', item.pop('skills', []))
            item['result'] = {'roles': roles or [], 'skills': skills or []}
            normalized.append(item)
        return normalized, total

    def all_summaries(self):
        rows, offset = [], 0
        fields = 'id,series_id,title,version,created_at,source_name,source_type,result->roles,result->skills'
        while True:
            batch = self.request('GET', 'analyses', params={'user_id': 'eq.' + self.uid, 'select': fields,
                                 'order': 'created_at.desc,version.desc', 'limit': 200, 'offset': offset})
            for row in batch:
                item = dict(row)
                roles = item.pop('result->roles', item.pop('roles', [])) or []
                skills = item.pop('result->skills', item.pop('skills', [])) or []
                item['result'] = {'roles': roles[:1], 'skills': [None] * len(skills)}
                rows.append(item)
            if len(batch) < 200:
                return rows
            offset += len(batch)

    def get(self, analysis_id):
        rows = self.request('GET', 'analyses', params={'id': 'eq.' + analysis_id, 'user_id': 'eq.' + self.uid, 'select': '*'})
        return rows[0] if rows else None

    def save(self, draft_id, series_id, title, source_name, source_type, result):
        return self.request('POST', 'rpc/save_resume_analysis', json=dict(p_id=draft_id, p_series_id=series_id,
                            p_title=title, p_source_name=source_name, p_source_type=source_type, p_result=result))

    def delete_series(self, series_id):
        self.request('DELETE', 'analyses', params={'user_id': 'eq.' + self.uid, 'series_id': 'eq.' + series_id})
