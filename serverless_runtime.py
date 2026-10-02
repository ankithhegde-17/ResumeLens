"""Backend-only HTTPS runtime state; never logs headers, tokens or responses."""
import hashlib
import base64
import json
import time
from urllib.parse import urlparse
import requests
from storage import StoreError

UNAVAILABLE = 'Cloud runtime storage is unavailable. Check the REST runtime migration and server service-role configuration.'


class SupabaseRuntime:
    def __init__(self, cfg):
        url = cfg.get('SUPABASE_URL', '').rstrip('/')
        key = cfg.get('SUPABASE_SERVICE_ROLE_KEY', '').strip()
        parsed = urlparse(url)
        if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or not key:
            raise ValueError('Configure HTTPS SUPABASE_URL and server-only SUPABASE_SERVICE_ROLE_KEY.')
        self.url = url + '/rest/v1/'
        try:
            encoded = key.split('.')[1]
            role = json.loads(base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4)))['role']
        except (ValueError, KeyError, IndexError, TypeError):
            role = None
        if role != 'service_role':
            raise ValueError('SUPABASE_SERVICE_ROLE_KEY must be the legacy service_role JWT (not a publishable or sb_secret key).')
        # Never reuse normal user repository headers or mutate shared session auth.
        self.headers = {'apikey': key, 'Authorization': 'Bearer ' + key}

    @staticmethod
    def key(value):
        return hashlib.sha256(str(value).encode()).hexdigest()

    def request(self, method, path, **kwargs):
        headers = dict(self.headers)
        headers.update(kwargs.pop('headers', {}))
        try:
            # Request-local transport avoids sharing tokens/state across threads.
            with requests.Session() as transport:
                response = transport.request(method, self.url + path, headers=headers,
                                             timeout=(5, 15), allow_redirects=False, **kwargs)
            if not response.ok:
                raise StoreError(UNAVAILABLE)
            if not response.content:
                return None
            return response.json()
        except (requests.RequestException, ValueError):
            # Raw errors can include credentials, request headers and row payload.
            raise StoreError(UNAVAILABLE) from None

    def _put(self, kind, key, owner, payload, expires):
        self.request('POST', 'server_runtime_state',
            params={'on_conflict': 'kind,key,owner'},
            headers={'Prefer': 'resolution=merge-duplicates,return=minimal'},
            json=dict(kind=kind, key=self.key(key), owner=owner, payload=payload, expires=expires))

    def _filters(self, kind, key, owner):
        return {'kind': 'eq.' + kind, 'key': 'eq.' + self.key(key), 'owner': 'eq.' + owner}

    def _get(self, kind, key, owner):
        filters = self._filters(kind, key, owner)
        # Only delete the caller's expired row; no global destructive operation.
        self.request('DELETE', 'server_runtime_state', params=dict(filters, expires='lte.' + str(time.time())))
        rows = self.request('GET', 'server_runtime_state',
                            params=dict(filters, expires='gt.' + str(time.time()), select='payload', limit='1'))
        if not isinstance(rows, list) or (rows and (not isinstance(rows[0], dict) or 'payload' not in rows[0])):
            raise StoreError(UNAVAILABLE)
        return rows[0]['payload'] if rows else None

    def _delete(self, kind, key, owner):
        self.request('DELETE', 'server_runtime_state', params=self._filters(kind, key, owner))

    def set_session(self, sid, mode, data, expires):
        self._put('session', sid, mode, data, expires)

    def get_session(self, sid, mode):
        return self._get('session', sid, mode)

    def delete_session(self, sid):
        self.request('DELETE', 'server_runtime_state',
                     params={'key': 'eq.' + self.key(sid), 'kind': 'in.(session,chat)'})

    def save_draft(self, draft_id, uid, data):
        self._put('draft', draft_id, uid, data, time.time() + 3600)

    def get_draft(self, draft_id, uid):
        return self._get('draft', draft_id, uid)

    def delete_draft(self, draft_id, uid):
        self._delete('draft', draft_id, uid)

    def chat(self, sid, uid):
        return self._get('chat', sid, uid) or []

    def save_chat(self, sid, uid, messages):
        self._put('chat', sid, uid, messages[-8:], time.time() + 3600)

    def rate_allow(self, bucket, maximum=6, window=600):
        result = self.request('POST', 'rpc/runtime_rate_allow',
                              json=dict(p_bucket=self.key(bucket), p_maximum=maximum, p_window=window))
        if not isinstance(result, bool):
            raise StoreError(UNAVAILABLE)
        return result
