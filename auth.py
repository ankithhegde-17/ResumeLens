"""Email OTP and server-side sessions. The browser cookie never holds Supabase tokens."""
import hashlib
import hmac
import re
import secrets
import time
import uuid
import requests


class AuthError(Exception):
    pass


def valid_email(email):
    return bool(len(email) <= 254 and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email))


class Authentication:
    def __init__(self, cfg, runtime):
        self.cfg, self.runtime = cfg, runtime

    def digest(self, email, token):
        return hmac.new(self.cfg['SECRET_KEY'].encode(), (email + ':' + token).encode(), hashlib.sha256).hexdigest()

    def api(self, method, path, payload=None, bearer=None):
        headers = {'apikey': self.cfg['SUPABASE_PUBLISHABLE_KEY'], 'Content-Type': 'application/json'}
        if bearer:
            headers['Authorization'] = 'Bearer ' + bearer
        try:
            r = requests.request(method, self.cfg['SUPABASE_URL'] + '/auth/v1/' + path,
                                 json=payload, headers=headers, timeout=20)
        except requests.RequestException as exc:
            raise AuthError('Cannot reach Supabase Auth. Check your connection and .env settings.') from exc
        if not r.ok:
            if r.status_code == 429:
                raise AuthError('Email sending limit reached. Wait before retrying; see the SMTP setup guide.')
            raise AuthError('Authentication failed. Check the code or Supabase email settings, then request a new code.')
        try:
            return r.json() if r.content else {}
        except ValueError as exc:
            raise AuthError('Authentication returned an unreadable response.') from exc

    def send(self, email, ip):
        if not valid_email(email):
            raise AuthError('Enter a valid email address.')
        if not self.runtime.rate_allow('send-email:' + email, 1, 60):
            raise AuthError('Wait 60 seconds before requesting another code.')
        if not self.runtime.rate_allow('send-ip:' + ip, 10, 3600):
            raise AuthError('Too many code requests from this connection. Try again later.')
        if self.cfg['APP_MODE'] == 'supabase':
            self.api('POST', 'otp', {'email': email, 'create_user': True})
        else:
            token = f'{secrets.randbelow(1000000):06d}'
            with self.runtime.connect() as db:
                db.execute('INSERT OR REPLACE INTO challenges VALUES (?,?,?,0)',
                           (email, self.digest(email, token), time.time() + 600))
            print(f'\n[LOCAL DEMO ONLY] OTP for {email}: {token} (valid 10 minutes)\n', flush=True)

    def verify(self, email, token):
        if not valid_email(email):
            raise AuthError('Enter a valid email address.')
        # Supabase can send 6–10 digits. Pass the entire code unchanged so the
        # provider, rather than a local length assumption, verifies its value.
        cloud_mode = self.cfg['APP_MODE'] == 'supabase'
        pattern = r'[0-9]{6,10}' if cloud_mode else r'[0-9]{6}'
        if not re.fullmatch(pattern, token):
            raise AuthError('Enter the complete 6–10 digit code from your email.' if cloud_mode
                            else 'Enter the six-digit code from the VS Code terminal.')
        if not self.runtime.rate_allow('verify:' + email, 10, 600):
            raise AuthError('Too many verification attempts. Wait 10 minutes.')
        if self.cfg['APP_MODE'] == 'supabase':
            body = self.api('POST', 'verify', {'email': email, 'token': token, 'type': 'email'})
            try:
                data = dict(id=body['user']['id'], email=body['user']['email'],
                            access_token=body['access_token'], refresh_token=body['refresh_token'],
                            token_expires=time.time() + body.get('expires_in', 3600))
            except KeyError as exc:
                raise AuthError('Supabase did not return a valid signed-in session.') from exc
        else:
            with self.runtime.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute('SELECT * FROM challenges WHERE email=?', (email,)).fetchone()
                valid = row and row['expires'] > time.time() and row['attempts'] < 5
                if not valid:
                    raise AuthError('This code expired or too many attempts were made. Request a new code.')
                matches = hmac.compare_digest(row['digest'], self.digest(email, token))
                if matches:
                    db.execute('DELETE FROM challenges WHERE email=?', (email,))
                else:
                    db.execute('UPDATE challenges SET attempts=attempts+1 WHERE email=?', (email,))
            if not matches:
                raise AuthError('The code is incorrect. Check the VS Code terminal in local demo mode.')
            data = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'resume-demo:' + email)), email=email)
        sid = secrets.token_urlsafe(32)
        self.runtime.set_session(sid, self.cfg['APP_MODE'], data, time.time() + 7 * 86400)
        return sid

    def current(self, sid):
        if not sid:
            return None
        data = self.runtime.get_session(sid, self.cfg['APP_MODE'])
        if data and self.cfg['APP_MODE'] == 'supabase' and data['token_expires'] < time.time() + 60:
            try:
                body = self.api('POST', 'token?grant_type=refresh_token', {'refresh_token': data['refresh_token']})
                data.update(access_token=body['access_token'], refresh_token=body['refresh_token'],
                            token_expires=time.time() + body.get('expires_in', 3600))
                self.runtime.set_session(sid, 'supabase', data, time.time() + 7 * 86400)
            except (AuthError, KeyError):
                self.runtime.delete_session(sid)
                return None
        return data

    def logout(self, sid):
        data = self.runtime.get_session(sid, self.cfg['APP_MODE']) if sid else None
        if data and self.cfg['APP_MODE'] == 'supabase':
            try:
                self.api('POST', 'logout?scope=local', bearer=data['access_token'])
            except AuthError:
                pass  # Local sign-out must still work if cloud logout is unavailable.
        if sid:
            self.runtime.delete_session(sid)
