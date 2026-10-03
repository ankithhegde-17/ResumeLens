"""Isolated hosted-mode browser benchmark; never loads .env or calls Gemini."""
import argparse
import os
from pathlib import Path
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
parser.add_argument('--port',type=int,default=5053)
args=parser.parse_args()
sys.path.insert(0,str(Path(args.root).resolve()))
os.environ.update(VERCEL='1',SECRET_KEY='isolated-local-performance-server',COOKIE_SECURE='true',GEMINI_API_KEY='',OCR_SERVICE_URL='',OCR_SERVICE_SECRET='')
from app import app
app.run(host='127.0.0.1',port=args.port,debug=False)
