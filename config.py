"""One place for paths and environment settings; independent of terminal location."""
import os
import secrets
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


def settings():
    hosted = os.getenv('VERCEL') == '1'
    if not hosted:
        load_dotenv(BASE_DIR / '.env')
    runtime = Path(os.getenv('APP_INSTANCE_DIR', str(BASE_DIR / 'instance')))
    key_path = runtime / 'secret.key'
    key = os.getenv('SECRET_KEY', '').strip()
    if not key:
        if hosted:
            raise ValueError('Set SECRET_KEY in Vercel environment settings.')
        runtime.mkdir(parents=True, exist_ok=True)
        if not key_path.exists():
            key_path.write_text(secrets.token_hex(32), encoding='utf-8')
            try:
                key_path.chmod(0o600)
            except OSError:
                pass
        key = key_path.read_text(encoding='utf-8').strip()
    mode = os.getenv('APP_MODE', 'demo').lower()
    engine = os.getenv('EXTRACTION_ENGINE', 'auto').lower()
    database_url = os.getenv('SUPABASE_DB_URL', '').strip()
    if hosted and (mode != 'supabase' or not database_url):
        raise ValueError('Vercel requires APP_MODE=supabase and the server-only SUPABASE_DB_URL transaction-pooler connection.')
    if hosted and os.getenv('COOKIE_SECURE', '').lower() != 'true':
        raise ValueError('Set COOKIE_SECURE=true for Vercel HTTPS.')
    if hosted:
        engine = 'ocr'  # A hosted request must never probe localhost Ollama.
    else:
        runtime.mkdir(parents=True, exist_ok=True)
    if mode not in {'demo', 'supabase'} or engine not in {'auto', 'ocr', 'vlm'}:
        raise ValueError('APP_MODE must be demo or supabase; EXTRACTION_ENGINE must be auto, ocr or vlm.')
    url = os.getenv('SUPABASE_URL', '').rstrip('/')
    pubkey = os.getenv('SUPABASE_PUBLISHABLE_KEY', '').strip()
    if mode == 'supabase':
        parsed = urlparse(url)
        if parsed.scheme != 'https' or not parsed.netloc or not pubkey:
            raise ValueError('Set the HTTPS SUPABASE_URL and public/publishable key in .env first.')
        if pubkey.startswith('sb_secret_'):
            raise ValueError('Use a publishable key, never a Supabase secret key.')
        # Reject legacy service-role JWTs too; their database requests bypass RLS.
        if pubkey.startswith('eyJ'):
            import base64, json
            try:
                role = json.loads(base64.urlsafe_b64decode(pubkey.split('.')[1] + '==='))['role']
            except (ValueError, KeyError, IndexError):
                role = ''
            if role == 'service_role':
                raise ValueError('Use the legacy anon key, never the service_role key.')
    return dict(SECRET_KEY=key, APP_MODE=mode, DB_PATH=runtime / 'app.sqlite3',
                VERCEL_HOSTED=hosted, SUPABASE_DB_URL=database_url,
                UPLOAD_MAX_MB=4 if hosted else 10,
                SUPABASE_URL=url, SUPABASE_PUBLISHABLE_KEY=pubkey,
                EXTRACTION_ENGINE=engine, OLLAMA_URL=os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/'),
                OLLAMA_MODEL=os.getenv('OLLAMA_MODEL', 'qwen2.5vl:3b'),
                OLLAMA_TIMEOUT=int(os.getenv('OLLAMA_TIMEOUT', '180')),
                GEMINI_API_KEY=os.getenv('GEMINI_API_KEY','').strip(),
                GEMINI_MODEL=os.getenv('GEMINI_MODEL','gemini-3.5-flash-lite').strip(),
                GEMINI_TIMEOUT=int(os.getenv('GEMINI_TIMEOUT','25')),
                MAX_CONTENT_LENGTH=(4 if hosted else 11) * 1024 * 1024,
                SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true')
