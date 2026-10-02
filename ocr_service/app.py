"""Private OCR endpoint: original bytes are processed in memory, never saved."""
import hmac
import os
from flask import Flask, jsonify, request
from extraction import extract_document


def create_app(overrides=None):
    app=Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=5*1024*1024,OCR_SERVICE_SECRET=os.getenv('OCR_SERVICE_SECRET',''),
                      EXTRACTION_ENGINE='ocr',UPLOAD_MAX_MB=4,VERCEL_HOSTED=False,
                      OLLAMA_URL='',OLLAMA_MODEL='')
    if overrides: app.config.update(overrides)
    if len(app.config['OCR_SERVICE_SECRET'])<32:
        raise ValueError('Set a random server-only OCR_SERVICE_SECRET of at least 32 characters.')

    @app.before_request
    def authenticate():
        if request.path=='/health' and request.method=='GET': return
        expected='Bearer '+app.config['OCR_SERVICE_SECRET']
        if not hmac.compare_digest(request.headers.get('Authorization','').encode(),expected.encode()):
            return jsonify(error='Unauthorized.'),401

    @app.get('/health')
    def health(): return jsonify(status='ok')

    @app.post('/extract')
    def extract():
        file=request.files.get('resume')
        if not file or not file.filename:
            return jsonify(error='Supply a PDF, JPG or PNG resume.'),400
        try:
            result=extract_document(file.read(4*1024*1024+1),file.filename,app.config,'ocr')
            return jsonify(result)
        except ValueError:
            return jsonify(error='Unable to extract this document. Check its format, size and readability.'),422

    @app.errorhandler(413)
    def too_large(error): return jsonify(error='Request too large.'),413

    @app.errorhandler(500)
    def unexpected(error): return jsonify(error='OCR processing failed. Try a clearer document.'),500
    return app
