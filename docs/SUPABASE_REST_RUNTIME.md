# Hosted runtime over HTTPS

Run the entire `database/vercel_rest_runtime_migration.sql` in your project's
Supabase SQL Editor before deploying this revision. It adds dedicated tables
and an atomic UPSERT RPC, enables RLS with no public policies, revokes PUBLIC,
anon and authenticated privileges, and grants only required runtime privileges
to service_role. Existing profiles, analyses, progress and old private runtime
tables are not deleted. Active cloud users must sign in again; old unfinished
drafts/chats remain in the old tables but are not read by the new adapter.

## Vercel Production environment

Required settings:

```dotenv
APP_MODE=supabase
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_PUBLISHABLE_KEY=YOUR-PUBLISHABLE-KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR-LEGACY-SERVICE_ROLE-JWT
SECRET_KEY=YOUR-EXISTING-LONG-RANDOM-SECRET
COOKIE_SECURE=true
EXTRACTION_ENGINE=ocr
```

Set the service key privately in Vercel only. Use Supabase Project Settings →
API Keys → Legacy anon/service_role keys → service_role. The required apikey +
Bearer headers need this legacy JWT: newer sb_secret keys cannot be used as
Bearer JWTs. The adapter rejects publishable, anon and sb_secret keys. This key
has broad project privileges; never put it in frontend code, HTML, logs or Git.
Normal authentication and user data still use the publishable key and user
access token, never this elevated key.

Keep optional feature settings if currently used:

```dotenv
GEMINI_API_KEY=YOUR-PRIVATE-KEY
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TIMEOUT=25
OCR_SERVICE_URL=https://YOUR-PRIVATE-OCR-SERVICE
OCR_SERVICE_SECRET=YOUR-PRIVATE-SHARED-SECRET
```

Delete obsolete SUPABASE_DB_URL from Vercel. VERCEL_SUPPORT_LARGE_FUNCTIONS is
also unnecessary after the previous OCR split. Do not set VERCEL manually.
Do not run the old vercel_runtime_migration.sql for this adapter.

## Redeploy

1. Run the new REST migration in Supabase SQL Editor.
2. Add the service_role JWT and verify the required Production settings above.
3. In Vercel Deployments, redeploy the latest main commit; disable existing Build
   Cache for this first redeploy to ensure the removed psycopg dependency is gone.
4. GET /login, send one OTP, verify it, reload a protected page, then sign out.
5. Verify a text PDF, review/save, history, profile, OCR and chat. Use two isolated
   accounts to confirm ownership. Public/anon/authenticated REST access to both
   runtime tables and the RPC must be denied. Never inspect token payloads in logs.

No raw database socket or psycopg is used by the hosted app. Local SQLite is
unchanged. IDs/buckets are SHA-256 hashed; reads enforce owner and TTL, sessions
last seven days, drafts/chat one hour, chat retains eight messages. Errors are
generic with no response/header logging. Periodic expired-row cleanup SQL is
included as comments in the migration; configure it with your existing scheduler.

Offline tests use an isolated REST emulator, mock Auth and inspect SQL contracts.
They do not prove live PostgREST permissions or execute the migration. Production
verification needs your private Vercel configuration and migration execution.
