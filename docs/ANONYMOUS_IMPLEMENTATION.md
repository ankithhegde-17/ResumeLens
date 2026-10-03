# Anonymous workspace implementation — 2026-10-03

OTP sending/verification, login guards, logout, Supabase authentication, account repositories and authentication runtime storage were removed. No fake user identity is created. Root opens the dashboard; legacy GET /login and /verify bookmarks redirect to /dashboard; their POST forms and /logout are retired.

All analysis, evidence, JD matching, recommendations, careers, skills, roadmaps, progress, preferences and server-side Gemini integrations remain. State is signed and browser-local, bound to an opaque browser cookie. Analyses expire after 24 hours; drafts/chat after one hour; signed state is capped at 2 MiB uncompressed. It is not encrypted, permanent, cross-device or a backup. JavaScript and localStorage are required. Existing Supabase/database records were not deleted or migrated.

## Verification

- 71 tests passed; four existing scikit-learn saved-model version warnings.
- Hosted public navigation tested with network calls prohibited and no Supabase settings.
- Upload/review/results/JD/version/history/export/preferences/progress and browser isolation covered by tests.
- Mocked Gemini/OCR provider paths tested; no live provider success claim.
- Browser sample PDF → review → results completed; saved result restored after restarting Flask.
- 64 rendered page/width combinations passed horizontal-overflow checks: dashboard, upload, roles, history, preferences, career, skill and results at 320, 390, 430, 768, 820, 1024, 1440 and 1920 pixels.
- Landscape 844×390 checked; mobile navigation closes with Escape and link selection.
- Browser console: zero errors/warnings. Screenshots saved locally under output/playwright (ignored by Git).
- Static Vercel build script and installation/import checks passed.
- Production Vercel build/bundle size and live Gemini/private OCR availability remain unverified. Public Gemini rate limiting is instance-local and resets on cold starts; configure provider budgets/platform controls.

## Deployment

See [exact redeployment steps](VERCEL_DEPLOYMENT.md). Required hosted settings: stable SECRET_KEY, COOKIE_SECURE=true, EXTRACTION_ENGINE=ocr. Gemini/OCR keys remain optional server-only feature configuration. Supabase, serverless_runtime.py and psycopg are not required. Retire APP_MODE, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_URL and OTP/runtime-only settings. No SQL migration is required.

## Files changed/deleted

The following includes preserved Terms & Conditions/footer work from the preceding request. Deleted files are auth.py, storage.py, serverless_runtime.py, templates/login.html, templates/verify.html and tests/test_rest_runtime.py. Historical migration files are marked obsolete, not executed.

- `.env.example`
- `.gitignore`
- `README.md`
- `app.py`
- `auth.py`
- `career_routes.py`
- `config.py`
- `database/vercel_rest_runtime_migration.sql`
- `database/vercel_runtime_migration.sql`
- `docs/ARCHITECTURE.md`
- `docs/CAREER_ROADMAPS.md`
- `docs/DEMO_GUIDE.md`
- `docs/EMAIL_LOGIN_FIX.md`
- `docs/SUPABASE_REST_RUNTIME.md`
- `docs/SUPABASE_SETUP.md`
- `docs/VERCEL_DEPLOYMENT.md`
- `docs/VERIFICATION.md`
- `scripts/check_web_install.py`
- `scripts/ui_preview.py`
- `serverless_runtime.py`
- `static/career.js`
- `static/style.css`
- `storage.py`
- `templates/base.html`
- `templates/career_detail.html`
- `templates/components.html`
- `templates/dashboard.html`
- `templates/error.html`
- `templates/help.html`
- `templates/login.html`
- `templates/profile.html`
- `templates/review.html`
- `templates/upload.html`
- `templates/verify.html`
- `tests/test_app.py`
- `tests/test_careers.py`
- `tests/test_rest_runtime.py`
- `tests/test_vercel.py`
- `browser_workspace.py`
- `static/workspace.js`
- `templates/footer.html`
- `templates/terms.html`
- `templates/workspace_restore.html`
- `tests/browser_client.py`
- `tests/test_browser_workspace.py`
- `tests/test_terms.py`

