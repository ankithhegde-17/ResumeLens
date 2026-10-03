# Obsolete: historical email OTP and cloud history setup

Current ResumeLens is authentication-free and does not use Supabase. Do not
follow this historical guide for current deployment; use README.md and
docs/VERCEL_DEPLOYMENT.md. Existing Supabase data is retained but not exposed.

The app is already integrated with Supabase Auth and its REST database API. You supply configuration after downloading. No paid AI API key or service-role key is needed.

## 1. Create the project and tables

1. Create or open a Supabase project at https://supabase.com/dashboard.
2. Open **SQL Editor**, create a query, paste the entire contents of `database/supabase_schema.sql`, and run it. This creates `profiles`, `analyses`, owner-only policies, and the transactional version-saving function.
3. Use a fresh project for the demonstration, or review existing tables with those names before running the script.

## 2. Configure email OTP

1. Enable the Email provider in **Authentication → Sign In / Providers**. Keep email sign-up enabled so a new student can sign in for the first time.
2. Open **Authentication → Email Templates → Magic Link**. The app uses the numeric OTP flow. Use a template containing the token, for example:

```html
<h2>Your ResumeLens sign-in code</h2>
<p>Your code is: <strong>{{ .Token }}</strong></p>
<p>Enter this code in the app. If you did not request it, ignore this email.</p>
```

3. Set OTP expiration to 10 minutes for the demo if desired. Cloud sign-in accepts the full 6–10 digit email code, including eight digits; Supabase verifies the actual value. Local demo codes remain six digits. You can retain your existing Supabase OTP length. Never shorten an emailed code to make it fit.
4. Set the Site URL to `http://127.0.0.1:5000` for local testing. Numeric OTP verification does not require a magic-link redirect.
5. Supabase's default email service can restrict recipients to authorized team addresses and impose low rate limits. **For real users/team demonstrations, configure custom SMTP** in the Supabase Authentication settings. Use your own provider's SMTP host, port, sender and credentials. Sender restrictions and quotas depend on that provider. Do not put SMTP passwords in this Flask app: Supabase sends the email.
6. This mini project does not implement a CAPTCHA widget. Leave Auth CAPTCHA disabled for the local demo. A hosted public service needs its own CAPTCHA integration and deployment review.

## 3. Edit `.env` locally

In VS Code, copy `.env.example` to `.env` if you have not done so. Set:

```dotenv
APP_MODE=supabase
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
EXTRACTION_ENGINE=auto
```

Get the exact project URL from the project's API settings. Get the **publishable key** (`sb_publishable_...`) from API Keys. A legacy `anon` key also works. Do not use `sb_secret_...` or `service_role`: those keys bypass owner policies and are rejected by the app.

These examples are configuration values to supply, not missing application code. Keep `.env`, `instance/`, tokens and database files out of Git. You do not need to paste any secret key into chat. The public key identifies the project; the user's signed-in token is what grants access to their records.

## 4. Restart and test

```powershell
python check_setup.py
python app.py
```

1. Open http://127.0.0.1:5000/. Request a code for your email and enter the code from your inbox.
2. Edit your profile, analyze a sample, and save a second version to the same collection.
3. Confirm the `profiles` and `analyses` rows in Supabase Table Editor.
4. Sign out, log in with the same email, and confirm history is present.
5. Use a second account: its dashboard must be empty until it saves its own analyses. A direct results URL copied from the first account must return 404 for the second.
6. Review the policies in Authentication/Database before exposing the app publicly. The supplied app binds to localhost and is intended for academic demonstration.

The app sends the publishable key plus the **current user's access token** to database requests. RLS compares `auth.uid()` with each row's `user_id`. Profiles can be edited; analysis versions cannot be updated. Deleting a collection removes only the signed-in owner's rows. Version numbers are assigned in a database transaction.

## What is stored where?

- **Supabase:** profiles, reviewed resume text, evidence, scores, role results, version history and model/catalog identifiers. The role results are stored together in the analysis JSON for simplicity.
- **Local `instance/app.sqlite3`:** short-lived drafts, request rate counters and server-side authentication sessions. Tokens are never placed in the browser's Flask cookie. Protect this runtime directory like other local account data.
- **Original PDF/image:** processed in memory and discarded; not uploaded to a storage bucket.
- Local demo records are separate. Changing to Supabase does not migrate local users or history.

## Troubleshooting

| Symptom | What to check |
|---|---|
| Code appears only in terminal | APP_MODE is still demo; restart after changing it. |
| Email contains a link rather than digits | Put `{{ .Token }}` in the Magic Link email template. |
| Eight-digit code cannot be entered | Install the email-login update: both `auth.py` and `templates/verify.html` must support 6–10 digits in Supabase mode. Restart Flask and reload the page. |
| Change the sender Gmail account | Replace SMTP sender email, SMTP username, and app password together in Supabase. Generate the password on the new Google account. This does not change user login emails or history. |
| Email not received / rate-limit error | Spam folder, sender verification, SMTP setup, allowed recipients and Auth email logs. Wait before resending. |
| Sign-in works but pages show database error | Run the entire SQL script, including grants and policies. |
| History disappears | Confirm mode, project URL and the same sign-in email. |
| Session expired | Sign out, request a fresh OTP, and sign in again. |
| Tables already exist with different columns | Use a fresh project, or review and reconcile the schema before applying this script. |

Official references checked for this integration:

- https://supabase.com/docs/guides/auth/auth-email-passwordless
- https://supabase.com/docs/guides/auth/auth-email-templates
- https://supabase.com/docs/guides/auth/auth-smtp
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://supabase.com/docs/guides/api/api-keys

For exact Gmail sender-change steps, spam-folder guidance, and installation instructions, see `EMAIL_LOGIN_FIX.md`.
