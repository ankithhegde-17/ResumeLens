# ResumeLens on Vercel

Prepared 2026-10-02. No redesign, existing routes/forms/auth logic preserved.
This preparation is not a successful cloud build/deployment: real credentials,
SQL migrations and the separate private OCR service still need setup.

## Entrypoint and build

`app.py` exports `app = create_app()` at module scope. Import does not run the
development server. Local `python app.py` runs that same instance.

- Framework Preset: **Flask**, not an old generic Python `builds` configuration.
- Root Directory: repository root (`./`); leave the field empty in the dashboard.
- Python: **3.12**, pinned by `.python-version` for the native dependency wheels.
- Build Command: `python scripts/vercel_build.py` (provided by `vercel.json`).
- Install Command: leave at the framework default; dependencies are in `requirements.txt`.
- Output Directory: leave at the framework default, no `dist` override.
- Function: `app.py`, maximum duration 60 seconds; actual plan limits still apply.
- `vercel.json` is not needed for basic Flask detection but is included here for
  the necessary static build step, exclusions and explicit processing duration.

Current [official Flask documentation](https://vercel.com/docs/frameworks/backend/flask)
recognizes `app.py:app`, uses a single function, and recommends CDN assets in
`public/` rather than relying on Flask's static folder. The build copies the
existing small static assets into `public/static/`, preserving every `/static/*`
URL. It omits the unused 5.9 MB source hero PNG; the displayed WebP stays included.
Templates stay in `templates/`. Local Flask continues using `static/` directly.
Generated `public/` is ignored by Git; no assets were moved or design changed.

## Environment variables (Vercel dashboard only)

```dotenv
APP_MODE=supabase
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_PUBLISHABLE_KEY=YOUR-PUBLISHABLE-KEY
SECRET_KEY=YOUR-LONG-RANDOM-SECRET
COOKIE_SECURE=true
EXTRACTION_ENGINE=ocr
SUPABASE_DB_URL=YOUR-PRIVATE-TRANSACTION-POOLER-URL
GEMINI_API_KEY=YOUR-REPLACEMENT-GEMINI-KEY
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TIMEOUT=25
OCR_SERVICE_URL=https://YOUR-OCR-DOMAIN
OCR_SERVICE_SECRET=YOUR-SHARED-PRIVATE-SECRET
```

Do not paste real values into Git or documentation. Generate SECRET_KEY locally
with `python -c "import secrets; print(secrets.token_hex(32))"`; store its output
privately in Vercel. Do not set `VERCEL` manually; Vercel supplies it. Hosted
configuration fails closed if mode, database URL, secret or HTTPS cookie settings
are missing. No hosted read of `.env`, generation of `instance/secret.key`, or
creation of runtime SQLite/files occurs. Module imports are network-free when
valid placeholder settings are supplied; no live connection is needed at build.

## Why one additional database setting is necessary

Previously Supabase mode still stored server authentication tokens, pending
review drafts, chat history and rate limits in `instance/app.sqlite3`.
Moving that file to `/tmp` would only fix writability, not persistence/isolation
between serverless instances. Putting tokens into a readable Flask signed cookie
would weaken the existing security model. Neither workaround is used.

`serverless_runtime.py` implements the existing runtime interface with the
**same Supabase Postgres project**, using a private, non-Data-API schema.
`SUPABASE_DB_URL` is necessary because the publishable key must not grant access
to server authentication tokens or pre-login rate limits. Existing public
profiles, analyses and learning progress still use user-token REST + owner RLS.
Local Supabase/demo sessions keep SQLite unless running on Vercel.

1. Run existing `database/supabase_schema.sql` if not already configured.
2. Run `database/career_learning_migration.sql` for progress, if not already run.
3. Run new `database/vercel_runtime_migration.sql` in Supabase SQL Editor.
   It adds only `resumelens_private.runtime_state` and `rate_limits`, indexes,
   a restricted runtime login and policies; existing rows/tables remain intact.
4. Give `resumelens_runtime` a strong password **privately** in Supabase, never
   in a saved SQL file. Copy the transaction-pooler host from Supabase's Connect
   dialog, port 6543. For the restricted login, username is
   `resumelens_runtime.YOUR-PROJECT-REF`; URL-encode special password characters.
   Set this complete URL as `SUPABASE_DB_URL` in Vercel only.
   The project's postgres connection also works but is much more privileged;
   the restricted login is recommended.

See [Supabase connection guidance](https://supabase.com/docs/guides/database/connecting-to-postgres).
Transactions use SSL, five-second connect timeout, ten-second statement timeout,
and `prepare_threshold=None` for transaction-pooler compatibility. Parameterized
queries and owner checks protect drafts/chat; session identifiers/rate bucket
identifiers are hashed in storage. Tokens remain server-only. Rate limits are
atomic and shared across instances. Logout removes session/chat. TTL reads reject
expired entries; periodically run the two cleanup statements in the migration
to remove untouched expired rows. Runtime state contains sensitive token/text
payloads: keep this schema out of exposed Data API schemas and restrict DB access.

## Uploads, OCR and filesystem

Original uploads are processed in memory, never saved permanently. Temporary
review text lives for one hour in private Postgres; finished analyses persist in
existing owner-protected Supabase tables. In-memory profile/model caches are
only optimizations; losing them does not lose authenticated state or records.

Use `EXTRACTION_ENGINE=ocr`. Hosted requests force direct PDF text + OCR even
if a manipulated form requests VLM; no localhost Ollama request is attempted.
Local `auto`/`vlm` and Ollama continue working. Text PDFs are read before OCR.
Hosted image/scanned documents use one authenticated HTTPS request to the private
OCR container. Text-only PDFs never call it. Set OCR_SERVICE_URL and the same
OCR_SERVICE_SECRET on both sides; see [OCR deployment](../ocr_service/README.md).
The original local RapidOCR/Ollama path remains available with requirements-ocr.txt.
Timeouts and unavailable service errors are friendly and do not break other pages.

Vercel has a [4.5 MB function payload limit](https://vercel.com/docs/functions/limitations).
Hosted multipart requests are limited to 4 MiB including form overhead, while
local uploads remain 10 MiB files. UI/client/server checks reflect the hosted
limit. The 6 MB scanned sample is hidden on Vercel. For larger real files the
smallest future adjustment is direct private Supabase Storage upload with
short-lived owner-scoped access, not increasing Flask's limit; not implemented
because it changes the existing upload workflow.

## Dependencies and bundle reduction

The original Vercel build was 588.02 MB. Measured headless-only reduction was
still 525.4 MiB, so only OCR was separated. Main Linux wheel contents now total
282.9 MiB (approximately 285 MiB including app assets before installation overhead).
No Large Functions beta is required; remove its old environment flag. Keep the
saved sklearn classifier and all its runtime dependencies. See the detailed
[dependency analysis](BUNDLE_SIZE_ANALYSIS.md) and [private OCR service setup](../ocr_service/README.md).
Final Vercel build logs remain authoritative; Linux cloud execution is not yet verified.

## Import GitHub into Vercel

1. Sign into Vercel → Add New → Project → Import Git Repository.
2. Select `ankithhegde-17/ResumeLens`, production branch `main`.
3. Select **Flask** preset and keep Root Directory at the repository root.
4. Keep default install/output settings and the supplied Build Command.
5. Complete the Supabase migrations/restricted runtime password setup above.
6. Deploy the private OCR service using ocr_service/README.md, then add all
   environment settings including its HTTPS URL and shared secret to Production.
   For preview testing add the same settings to Preview using a separate test
   Supabase project where possible; never enable public demo OTPs on Vercel.
7. Deploy. If size/native dependencies fail, use the adjustments above, not
   legacy `@vercel/python` rewrites or deleting packages needed by routes.
8. In Supabase Auth settings set the hosted Site URL and required redirect URLs,
   retain the existing OTP email template/SMTP settings. Do not change to magic
   links unintentionally. Redeploy after changing environment settings.
9. Verify login/OTP/logout, profile, small text PDF, small image OCR, review/save,
   history/version comparison, progress and Career AI on the deployed domain.
   Test two separate browser accounts and instance/cold-start continuity.

## Verification and changed files

Flask import printed all existing routes without starting a server. Static
build passed; public/static contains existing CSS/JS/logos/WebP. Suite passed
85 tests including 19 new OCR-service/transport cases, four pre-existing sklearn model
version warnings. Hosted configuration tests use fake values and no network:
no disk writes, import/runtime adapter, homepage/login/static/protected redirects,
cookie security, forced OCR/direct PDF, missing-setting rejection and parameterized
owner-aware runtime operations. Real Postgres SQL/RLS/pooler connections, Linux
native imports, final Vercel build and live deployment have **not** been verified.

Modified: `app.py`, `config.py`, `extraction.py`, `requirements.txt`, `.env.example`,
`.gitignore`, `static/script.js`, `templates/upload.html`, `README.md`.
Created: `.python-version`, `vercel.json`, `serverless_runtime.py`,
`database/vercel_runtime_migration.sql`, `scripts/vercel_build.py`,
`tests/test_vercel.py`, this guide. OCR split adds `remote_ocr.py`,
`requirements-ocr.txt`, `.dockerignore`, `ocr_service/`, `tests/test_remote_ocr.py`
and `docs/BUNDLE_SIZE_ANALYSIS.md`; requirements-dev includes local OCR. No secrets added; `.env` remains ignored.

Local Windows checks (local .env/demo/Supabase behavior unchanged):

```powershell
cd "C:\Users\hegde\OneDrive\Desktop\Multimodal Resume Analyzer"
.\.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
.\.venv\Scripts\python.exe -c "from app import app; print(app.url_map)"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe app.py
```
