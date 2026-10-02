FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY ocr_service/requirements.txt /srv/ocr_service/requirements.txt
RUN pip install --no-cache-dir -r ocr_service/requirements.txt \
    && pip install --no-cache-dir --no-deps rapidocr-onnxruntime==1.4.4
COPY extraction.py remote_ocr.py /srv/
COPY ocr_service /srv/ocr_service
RUN useradd --create-home appuser
USER appuser
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 1 --timeout 45 --access-logfile /dev/null ocr_service.wsgi:app"]
