# Obsolete: former account runtime

The authentication-free ResumeLens app no longer uses Supabase REST runtime
storage, auth sessions, rate-limit RPCs or service-role keys. Do not follow the
old runtime setup for current deployments. No runtime migration is required.

Historical SQL files are retained to document existing deployments. Existing
tables and data are not deleted, but they are no longer read by this app. Account
records must never be reinterpreted as public anonymous history.

Use [current deployment instructions](VERCEL_DEPLOYMENT.md) and README instead.
