"""Authentication-free configuration; no database credentials are required."""
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR=Path(__file__).resolve().parent

def settings():
    hosted=os.getenv('VERCEL')=='1'
    if not hosted: load_dotenv(BASE_DIR/'.env')
    key=os.getenv('SECRET_KEY','').strip()
    if not key:
        if hosted: raise ValueError('Set a stable SECRET_KEY in Vercel for signed browser workspaces.')
        directory=Path(os.getenv('APP_INSTANCE_DIR',str(BASE_DIR/'instance')))
        directory.mkdir(parents=True,exist_ok=True)
        path=directory/'secret.key'
        if not path.exists(): path.write_text(secrets.token_hex(32),encoding='utf-8')
        key=path.read_text(encoding='utf-8').strip()
    secure=os.getenv('COOKIE_SECURE','false').lower()=='true'
    if hosted and not secure: raise ValueError('Set COOKIE_SECURE=true for Vercel HTTPS.')
    engine='ocr' if hosted else os.getenv('EXTRACTION_ENGINE','auto').lower()
    if engine not in ('auto','ocr','vlm'): raise ValueError('EXTRACTION_ENGINE must be auto, ocr or vlm.')
    return dict(SECRET_KEY=key,VERCEL_HOSTED=hosted,APP_MODE='anonymous',EXTRACTION_ENGINE=engine,
        PERFORMANCE_DIAGNOSTICS=os.getenv('PERFORMANCE_DIAGNOSTICS','false').lower()=='true',
        OCR_SERVICE_URL=os.getenv('OCR_SERVICE_URL','').rstrip('/'),OCR_SERVICE_SECRET=os.getenv('OCR_SERVICE_SECRET','').strip(),
        UPLOAD_MAX_MB=3 if hosted else 10,MAX_CONTENT_LENGTH=(4 if hosted else 13)*1024*1024,
        OLLAMA_URL=os.getenv('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/'),
        OLLAMA_MODEL=os.getenv('OLLAMA_MODEL','qwen2.5vl:3b'),OLLAMA_TIMEOUT=int(os.getenv('OLLAMA_TIMEOUT','180')),
        GEMINI_API_KEY=os.getenv('GEMINI_API_KEY','').strip(),GEMINI_MODEL=os.getenv('GEMINI_MODEL','gemini-3.5-flash-lite').strip(),
        GEMINI_TIMEOUT=int(os.getenv('GEMINI_TIMEOUT','25')),
        SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=secure,
        SESSION_COOKIE_NAME='resumelens_browser')
