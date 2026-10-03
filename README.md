# ResumeLens

Explainable AI-based resume analysis and career guidance. Open `/` and use the
dashboard directly—no account, email, OTP, login or Supabase setup is required.
The existing blue/white glass UI, branding and responsive layouts are retained.

## Features

- PDF direct-text extraction before OCR; local images/scans through RapidOCR
  or Ollama vision, hosted images/scans through the private HTTPS OCR service.
- Editable extracted-text review and explicit skill confirmation.
- Skill evidence sentences, optional job-description matching, explainable
  weighted coverage scores and saved trained-classifier suggestions.
- 18 curated careers, skill guides, roadmaps, resources and portfolio projects.
- Temporary browser-local analysis versions, comparisons, JSON exports,
  learning progress and optional display/career preferences.
- Server-side Gemini Career AI with bounded context, topic restrictions,
  plain-text replies, curated fallback resources and no browser API key.
- Terms/contact footer: support@prayogmanch.in.

Scores are guidance, not hiring predictions or proof of proficiency. The trained
model is evaluated on fictional educational examples; see `/evaluation`.

## Anonymous state and privacy

JavaScript and browser storage are required for the interactive workspace.
The browser stores a signed (not encrypted) localStorage payload. Flask verifies
its signature and binds it to an opaque random browser-cookie identifier. The
cookie contains only that identifier, CSRF state and flash messages—not resume
contents, access tokens, refresh tokens or an authenticated identity.

Flask is stateless: the browser submits the signed payload with reads/forms and
saves updated state before following redirects. Thus versions/drafts can survive
Vercel cold starts without SQLite, server-memory document storage, Supabase or
database migrations. Backend inference still processes your submitted content.
Different browsers cannot submit each other's workspace without its signed cookie.
This is browser isolation, not an account login or protection from someone using
the same device/browser. Client storage can be read by browser users or malicious
extensions; do not use it for highly confidential documents.

Analyses expire after 24 hours from saving; drafts/chat after one hour. Preferences
and progress use a 24-hour inactivity window. Browser data is capped at 2 MiB
uncompressed; delete older collections or export JSON if full. Storage expiry
is enforced when the site next loads; localStorage may retain expired bytes until
then or until manually cleared. No cross-device sync or permanent cloud history.
Clear data in `/profile` (Browser preferences). Previously exported files remain.
Old SQLite/Supabase account records are not deleted or imported into public mode.

Chat uses instance-local browser/network limits and eight recent messages; limits
are best-effort and reset on cold starts. Configure provider quotas/budget and,
for higher-traffic production, platform abuse/rate controls. Anonymous visitors
can clear cookies to get a new identifier; do not treat these limits as a global
spending guarantee. Questions and limited skill/roadmap context may go to Google;
raw resume text, source quotes and contact details are not added to model context.

## Local Windows setup

Use supported 64-bit Python 3.12 (Vercel is pinned to 3.12).

```powershell
cd "C:\Users\hegde\OneDrive\Desktop\Multimodal Resume Analyzer"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe app.py
```

Do not overwrite an existing .env; edit only needed settings instead. Open
http://127.0.0.1:5000/. Keep the server running; stop with Ctrl+C. No training
step is required. Optional Ollama setup is in `docs/VISION_SETUP.md`.

## Environment

- `SECRET_KEY`: stable signing secret; required on Vercel. Local development
  generates/reuses instance/secret.key if absent. Rotating it invalidates browser
  state; keep it private, never in frontend code or Git.
- `COOKIE_SECURE=true`: required for Vercel HTTPS; false for local HTTP.
- `EXTRACTION_ENGINE=ocr`: hosted direct-PDF/OCR mode. Local auto/ocr/vlm supported.
- `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_TIMEOUT`: optional server-side chat.
- `OCR_SERVICE_URL`, `OCR_SERVICE_SECRET`: required for hosted images/scans only.
- `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`: optional local vision.
- `PORT`: optional local development port (default 5000).

Remove obsolete `APP_MODE`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`,
`SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`, `APP_INSTANCE_DIR` (unless using
a local secret location), OTP settings and `VERCEL_SUPPORT_LARGE_FUNCTIONS`
from Vercel. Vercel sets `VERCEL` automatically. Supabase is not used by this
active application; its old SQL files remain historical and must not be run for
this deployment. No psycopg, auth.py, storage.py or serverless_runtime.py is needed.

## Vercel

Follow [deployment instructions](docs/VERCEL_DEPLOYMENT.md). Keep the existing
Flask preset, root directory, entrypoint and small vercel.json. The lean main
requirements exclude local OCR and raw Postgres. Hosted upload files are limited
to 3 MiB and combined request bodies (file + state + multipart overhead) to
4 MiB; text PDFs need no external OCR. An unavailable OCR service returns a
clear error for scans/images without breaking navigation or text-PDF analysis.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check_web_install.py
```

Tests model the same browser-state transport as workspace.js, test cold-start
restoration with a second app, isolation, tampering, CSRF, versions/JD evidence,
extraction, all career/skill pages and mocked Gemini failures. Retired OTP/cloud
account tests are removed, not silently left testing a nonexistent login flow.
Actual provider availability, final Vercel bundle and cloud deployment require
your private configuration and deployment checks. Future optional accounts can
add cross-device history later without making login mandatory.
