# Authentication-free Vercel deployment

No Supabase, raw PostgreSQL, SQLite runtime database or authentication migrations
are required. `/` renders the dashboard directly; `/login` and `/verify` GET
bookmarks redirect only to `/dashboard`; their POST auth forms and `/logout` are
retired. Browser-local workspace data is carried in signed POST bodies; static
requests do not create cookies or load state. See README for privacy/TTL limits.

## Required Vercel Production settings

```dotenv
SECRET_KEY=YOUR-STABLE-LONG-RANDOM-SECRET
COOKIE_SECURE=true
EXTRACTION_ENGINE=ocr
```

Keep optional feature settings:

```dotenv
GEMINI_API_KEY=YOUR-PRIVATE-GEMINI-KEY
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TIMEOUT=25
OCR_SERVICE_URL=https://YOUR-PRIVATE-OCR-SERVICE
OCR_SERVICE_SECRET=YOUR-PRIVATE-SHARED-SECRET
```

Never paste actual keys in source/Git/browser code. Use the same stable SECRET_KEY
across production instances/deployments; rotating it invalidates saved browser
payloads. Use separate keys/domains for previews. Provider keys stay server-only.

## Remove obsolete settings

APP_MODE, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_SERVICE_ROLE_KEY,
SUPABASE_DB_URL, OTP/auth variables, hosted APP_INSTANCE_DIR and the old
VERCEL_SUPPORT_LARGE_FUNCTIONS flag. Do not set VERCEL manually.
Keep Supabase's existing project/data if wanted; it is not connected to this
application and old records are not exposed or migrated to anonymous visitors.

## Exact redeploy steps

1. In Vercel import/use `ankithhegde-17/ResumeLens`, production branch main.
2. Framework Flask; repository root; Python 3.12 is pinned by .python-version.
3. Build `python scripts/vercel_build.py`; default install/output settings.
4. Add required Production environment values above; remove obsolete variables.
5. Keep Gemini/OCR configuration for those features. Hosted text PDFs work
   without either. Set provider budget/quotas and platform abuse controls.
6. Redeploy the latest main commit, disabling Build Cache for the first redeploy.
   No SQL migration or Supabase Auth setting is needed.
7. In a fresh browser open `/`, upload a small text PDF, review/confirm, analyze,
   export JSON, revisit history and add a version. Try careers, skills, progress,
   preferences, chat and an image/scan with OCR configured.
8. Reload after a cold start; confirm same-browser history restores. Test a
   separate browser: it must not see the first browser's data. Clear workspace
   data and check it disappears. Test narrow/portrait/landscape navigation.

Browser JavaScript/storage is required for dynamic data. Local storage is not
encrypted or a backup. Histories are browser-local with 24-hour analysis expiry,
2 MiB uncompressed state cap and one-hour drafts/chat. File limit is 3 MiB;
combined multipart/body limit is 4 MiB. Existing Vercel config keeps 60s maximum
processing duration. Instance-local AI limits reset on cold starts; they are not
distributed billing protection. Configured provider availability and Vercel's
final build/deployment remain separate verification steps.

Main requirements keep the trained classifier, direct PDF and image-validation
dependencies. psycopg and OCR inference packages are not in the main bundle.
The previous 282.9 MiB Linux estimate included psycopg, so current dependency
contents are smaller; build logs remain authoritative for the exact bundle.
Use [private OCR setup](../ocr_service/README.md) for hosted multimodal processing.
