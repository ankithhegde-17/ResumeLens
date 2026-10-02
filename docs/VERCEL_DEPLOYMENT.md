# ResumeLens on Vercel

Prepared 2026-10-02. No redesign, existing routes/forms/auth logic preserved.
This preparation is not a successful cloud build/deployment: real credentials,
SQL migrations and the Vercel account's Large Functions eligibility still need setup.

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
VERCEL_SUPPORT_LARGE_FUNCTIONS=1
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
RapidOCR models remain lazily loaded once per warm process from installed wheel
assets. Heavy OCR cold starts, five-page scans and memory use need real Vercel
testing; a 60-second limit is not a promise that every document will finish.

Vercel has a [4.5 MB function payload limit](https://vercel.com/docs/functions/limitations).
Hosted multipart requests are limited to 4 MiB including form overhead, while
local uploads remain 10 MiB files. UI/client/server checks reflect the hosted
limit. The 6 MB scanned sample is hidden on Vercel. For larger real files the
smallest future adjustment is direct private Supabase Storage upload with
short-lived owner-scoped access, not increasing Flask's limit; not implemented
because it changes the existing upload workflow.

## Dependencies and deployment blocker

All 40 resolved wheels were downloadable for Linux x86-64 Python 3.12. Their
combined uncompressed wheel entries measure **604,909,831 bytes / 576.9 MiB**:
OpenCV 186.9 MiB, SciPy 106.8, NumPy 55.1, PyMuPDF 54.7, ONNX Runtime 44.7,
scikit-learn 31.8, SymPy 25.6 and Pillow 16.7. This is a reproducible dependency
estimate, not Vercel's measured final bundle size; installation/bytecode/app data
and resolver changes can alter it. Existing pinned runtime dependencies remain;
only `psycopg[binary]==3.2.10` was added for server state.

The standard Python bundle limit is 500 MB. Current official documentation lists
[Large Functions up to 5 GB, public beta](https://vercel.com/docs/frameworks/backend/flask),
enabled with `VERCEL_SUPPORT_LARGE_FUNCTIONS=1` per the
[official announcement](https://vercel.com/changelog/vercel-functions-can-now-be-up-to-5-gb-in-package-size-7yAwSyCig0IQDXUIDistvS/eadf06d6c3).
Confirm account/plan availability before deployment. If unavailable, **this full
OCR application will not fit standard Vercel Functions as currently resolved**.

Wheels establish binary availability, not successful import on Vercel. OpenCV's
GUI wheel can additionally need system `libGL`/GUI libraries; ONNX/OpenCV native
imports and memory must be checked in cloud build/runtime logs. If native OCR or
size limits prevent deployment, the smallest reliable architecture adjustment
is hosting the unchanged Flask OCR backend on a persistent Python/container
service (or moving only OCR to such a worker). Replacing the GUI OpenCV package
with headless OpenCV requires coordinated RapidOCR dependency handling; blindly
adding both does not fix it because both provide `cv2`. No required OCR/ML feature
was removed or falsely marked as deploy-verified.

## Import GitHub into Vercel

1. Sign into Vercel → Add New → Project → Import Git Repository.
2. Select `ankithhegde-17/ResumeLens`, production branch `main`.
3. Select **Flask** preset and keep Root Directory at the repository root.
4. Keep default install/output settings and the supplied Build Command.
5. Complete the Supabase migrations/restricted runtime password setup above.
6. Add all environment settings, including Large Functions, to Production.
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
66 tests (58 existing + 8 deployment cases), four pre-existing sklearn model
version warnings. Hosted configuration tests use fake values and no network:
no disk writes, import/runtime adapter, homepage/login/static/protected redirects,
cookie security, forced OCR/direct PDF, missing-setting rejection and parameterized
owner-aware runtime operations. Real Postgres SQL/RLS/pooler connections, Linux
native imports, final Vercel build and live deployment have **not** been verified.

Modified: `app.py`, `config.py`, `extraction.py`, `requirements.txt`, `.env.example`,
`.gitignore`, `static/script.js`, `templates/upload.html`, `README.md`.
Created: `.python-version`, `vercel.json`, `serverless_runtime.py`,
`database/vercel_runtime_migration.sql`, `scripts/vercel_build.py`,
`tests/test_vercel.py`, this guide. No secrets added; `.env` remains ignored.

Local Windows checks (local .env/demo/Supabase behavior unchanged):

```powershell
cd "C:\Users\hegde\OneDrive\Desktop\Multimodal Resume Analyzer"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "from app import app; print(app.url_map)"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe app.py
```
