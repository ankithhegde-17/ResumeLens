"""Isolated anonymous UI preview; no OTP, databases or real user records."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['GEMINI_API_KEY']=''
from app import create_app
if __name__=='__main__':
    app=create_app({'SECRET_KEY':'isolated-preview-only','GEMINI_API_KEY':'','EXTRACTION_ENGINE':'ocr','SESSION_COOKIE_SECURE':False})
    app.run(host='127.0.0.1',port=5051,debug=False,use_reloader=False)
