# ResumeLens on Vercel

## Build settings

- Import GitHub `ankithhegde-17/ResumeLens`, branch main, repository root.
- Framework preset Flask; Python 3.12 is pinned in `.python-version`.
- Build command: `python scripts/vercel_build.py` from `vercel.json`.
- Leave install/output settings at framework defaults. Function maximum 60s.
- `app.py` exports `app = create_app()` without running a development server.

The build copies existing lightweight assets to public/static for CDN delivery,
omitting the unused source hero PNG. The displayed WebP and design are unchanged.
Hosted imports do not write SQLite or local files. Local `python app.py` remains
supported with the existing .env and SQLite behavior.

## Supabase runtime setup

Follow [HTTPS runtime migration, exact environment list and redeploy steps](SUPABASE_REST_RUNTIME.md).
Use the existing public schema and career-learning migrations if not yet applied,
then run `database/vercel_rest_runtime_migration.sql`. The former raw Postgres
adapter and SUPABASE_DB_URL are obsolete. Dedicated runtime tables use backend
service-role HTTPS only; normal profiles/analyses/progress remain user-scoped REST.
Never put server credentials in Git, browser code or logs.

## OCR and uploads

Keep EXTRACTION_ENGINE=ocr. Text PDFs are extracted directly on Vercel; hosted
scans/images use the authenticated HTTPS OCR container. Local Ollama/RapidOCR
remain available through requirements-ocr.txt. Follow [OCR setup](../ocr_service/README.md)
and retain OCR_SERVICE_URL/OCR_SERVICE_SECRET for multimodal functionality.
Hosted multipart uploads are limited to 4 MiB including overhead; local files
remain 10 MiB. No resume upload is permanently stored on disk. Drafts last one hour.

The previous OCR split brought measured Linux wheel contents to 282.9 MiB;
removing psycopg reduces this further. Final Vercel build logs are authoritative.
See [historical bundle analysis](BUNDLE_SIZE_ANALYSIS.md). Large Functions beta
is not required. Do not delete sklearn/model dependencies or alter Flask routes.

## Production checks

After migration/environment setup, redeploy main (first time without Build Cache).
Retain Supabase Auth OTP email/SMTP settings, set hosted Site URL/redirect URLs,
then verify OTP login/logout, profile, PDF/image upload, review/save, history,
version comparison, progress and Career AI. Verify two-user ownership and
cold-start continuity. Active sessions must sign in again after the runtime change.

Offline tests cover mocked REST/Auth and existing analyzer/local flows. They do
not execute live SQL, send real OTPs or verify a completed production deployment.

## Local Windows commands

```powershell
cd "C:\Users\hegde\OneDrive\Desktop\Multimodal Resume Analyzer"
.\.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe app.py
```
