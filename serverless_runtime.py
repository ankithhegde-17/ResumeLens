"""Persist server-only session/draft state in existing Supabase Postgres.

No network calls or schema writes at import. The private schema is not exposed
through PostgREST. Each short transaction uses the Supabase transaction pooler.
"""
import hashlib
import json
import time
from contextlib import contextmanager
from storage import StoreError


class PostgresRuntime:
    def __init__(self, database_url):
        self.database_url = database_url

    @contextmanager
    def connect(self):
        import psycopg
        from psycopg.rows import dict_row
        try:
            with psycopg.connect(self.database_url, sslmode='require', connect_timeout=5,
                                 prepare_threshold=None, row_factory=dict_row) as db:
                # Transaction-local, compatible with transaction pooling.
                db.execute("SET LOCAL statement_timeout = '10000ms'")
                yield db
        except psycopg.Error:
            # Never expose the connection string/password or token payload.
            raise StoreError('Cloud runtime storage is unavailable. Check the runtime migration and server database connection.') from None

    @staticmethod
    def key(value):
        return hashlib.sha256(str(value).encode()).hexdigest()

    def _put(self, kind, key, owner, payload, expires):
        with self.connect() as db:
            db.execute('''INSERT INTO resumelens_private.runtime_state
                (kind,key,owner,payload,expires) VALUES (%s,%s,%s,%s::jsonb,%s)
                ON CONFLICT(kind,key) DO UPDATE SET owner=EXCLUDED.owner,
                payload=EXCLUDED.payload,expires=EXCLUDED.expires
                WHERE runtime_state.owner=EXCLUDED.owner''',
                (kind,self.key(key),owner,json.dumps(payload),expires))

    def _get(self, kind, key, owner):
        with self.connect() as db:
            db.execute('DELETE FROM resumelens_private.runtime_state WHERE kind=%s AND key=%s AND expires<=%s',
                       (kind,self.key(key),time.time()))
            row = db.execute('''SELECT payload FROM resumelens_private.runtime_state
                WHERE kind=%s AND key=%s AND owner=%s AND expires>%s''',
                (kind,self.key(key),owner,time.time())).fetchone()
        return row['payload'] if row else None

    def _delete(self, kind, key, owner):
        with self.connect() as db:
            db.execute('DELETE FROM resumelens_private.runtime_state WHERE kind=%s AND key=%s AND owner=%s',
                       (kind,self.key(key),owner))

    def set_session(self, sid, mode, data, expires):
        self._put('session',sid,mode,data,expires)

    def get_session(self, sid, mode):
        return self._get('session',sid,mode)

    def delete_session(self, sid):
        with self.connect() as db:
            db.execute("DELETE FROM resumelens_private.runtime_state WHERE key=%s AND kind IN ('session','chat')",
                       (self.key(sid),))

    def save_draft(self, draft_id, uid, data):
        self._put('draft',draft_id,uid,data,time.time()+3600)

    def get_draft(self, draft_id, uid):
        return self._get('draft',draft_id,uid)

    def delete_draft(self, draft_id, uid):
        self._delete('draft',draft_id,uid)

    def chat(self, sid, uid):
        return self._get('chat',sid,uid) or []

    def save_chat(self, sid, uid, messages):
        self._put('chat',sid,uid,messages[-8:],time.time()+3600)

    def rate_allow(self, bucket, maximum=6, window=600):
        stamp = time.time()
        with self.connect() as db:
            # One atomic UPSERT; parallel Vercel instances share the same limit.
            row = db.execute('''INSERT INTO resumelens_private.rate_limits AS limits
                (bucket,count,reset) VALUES (%s,1,%s)
                ON CONFLICT(bucket) DO UPDATE SET
                count=CASE WHEN limits.reset<=%s THEN 1 ELSE limits.count+1 END,
                reset=CASE WHEN limits.reset<=%s THEN EXCLUDED.reset ELSE limits.reset END
                WHERE limits.reset<=%s OR limits.count<%s RETURNING count''',
                (self.key(bucket),stamp+window,stamp,stamp,stamp,maximum)).fetchone()
        return row is not None
