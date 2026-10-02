# Private ResumeLens OCR service

Only native image/scanned PDF extraction runs here. The web UI, Supabase, Gemini,
classifier, history and roadmaps remain on Vercel. Text PDFs are processed by
Vercel first. A mixed/scanned PDF uses one service request for all its pages.

## Railway deployment

1. Create a Railway service from `ankithhegde-17/ResumeLens`, branch `main`.
2. Keep Root Directory at repository root: the Docker build needs shared
   `extraction.py`. Set `RAILWAY_DOCKERFILE_PATH=ocr_service/Dockerfile`.
3. Set `OCR_SERVICE_SECRET` to a privately generated random secret (at least
   32 characters). Generate one locally with
   `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
   Never paste it into Git, browser JavaScript, logs or documentation.
4. Set Healthcheck Path `/health`. The container listens on Railway's `PORT`.
5. Deploy and Generate Domain under Networking; use the HTTPS domain.
6. In Vercel set `OCR_SERVICE_URL=https://YOUR-OCR-DOMAIN` (no `/extract` suffix)
   and the identical server-only `OCR_SERVICE_SECRET`, then redeploy ResumeLens.
7. Test a small image/scanned resume through ResumeLens's normal upload/review
   workflow. Do not call the OCR endpoint from frontend JavaScript.

[Railway Dockerfile variables](https://docs.railway.com/variables/reference),
[healthchecks](https://docs.railway.com/deployments/healthchecks).
No service has been provisioned or charged during this task. Check current host
plan/trial terms before deploying; Railway is not assumed free indefinitely.
Any Docker-compatible Python host can run the same image.

## Container behavior and security

`POST /extract`, multipart field `resume`, requires
`Authorization: Bearer <OCR_SERVICE_SECRET>`. Successful JSON contains
`pages[{number,text,engine,confidence}]`, `source_type`, `notes`.
`GET /health` is public and returns only readiness of the HTTP process, not
document data or proof the OCR model has finished warming.

4 MiB file limit, 5 MiB HTTP-body limit, five pages, image dimension validation,
genuine PDF checks and bounded text output. Original documents are never saved
permanently; Werkzeug may spool a multipart upload temporarily before bytes are
read. Gunicorn uses one worker/thread to avoid duplicated model memory and a
45-second processing timeout. The ResumeLens client uses 5-second connect and
35-second response timeouts; cold starts/queues can still cause friendly failure.
No access/body/authorization logging is enabled by this app. Hosting-level logs
must also avoid request bodies/auth headers. Failed OCR/validation returns safe
errors. No CORS endpoint, authentication tokens, Supabase keys or Gemini keys are
needed by this service. `.dockerignore` restricts build context to the service
and shared extraction modules; the image runs as a non-root user.

The Dockerfile installs **only headless OpenCV**, then installs RapidOCR with
`--no-deps` after supplying its dependencies explicitly. RapidOCR's default
metadata requests GUI OpenCV, so merely adding headless to a regular RapidOCR
install would install both and duplicate/conflict in `cv2`. ONNX/models stay in
the OCR container. No trained role classifier or scikit-learn/SciPy is required.

Local Docker check, if Docker is installed:

```powershell
docker build -f ocr_service/Dockerfile -t resumelens-ocr .
# Set OCR_SERVICE_SECRET privately in your current shell first.
docker run --rm -p 8080:8080 -e OCR_SERVICE_SECRET resumelens-ocr
```

Hosted client requires HTTPS. For local OCR/Ollama development, use the original
direct extraction path and `pip install -r requirements-ocr.txt`; do not route
private files through an untrusted endpoint.

Docker was unavailable in the implementation environment. Private service routes
and real image OCR passed local tests and an isolated Python 3.12 headless-only
install check, but a Linux container build and live
Railway/Vercel connection still need verification.
