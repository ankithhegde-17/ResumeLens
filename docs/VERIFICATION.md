# Historical notes (pre-authentication-removal)

This document describes the former account-based implementation. Login, OTP,
Supabase persistence and server runtime setup below are obsolete for the current
anonymous app. See README.md and docs/VERCEL_DEPLOYMENT.md for active behavior.

# Verification before packaging

## Email-login update — 1 October 2026

- **31 automated tests passed** on 64-bit Python 3.12, including the original project checks plus full-length 6–10 digit Supabase OTPs, eight/ten-digit Flask sign-in routes, leading zeros, malformed input, demo-mode compatibility and provider rejection without creating a session.
- Browser verification was attempted, but the current agent-browser daemon could not start and the earlier Chromium executable is unavailable. The updated form's pattern, maximum length and route submission are verified through Flask regression tests; no new visual browser pass is claimed.
- Supabase responses are mocked in these tests. This environment does not have the user's Supabase credentials or Gmail app password; real email delivery, spam placement and the sender change need to be tested in the user's configured project.
- The small update ZIP excludes `.env`, runtime databases, sessions, keys and virtual environments. It requires no new dependencies and no SQL migration.

The original package verification follows below; its browser results belong to that earlier build.

Verified on 30 September 2026 using 64-bit Python 3.12 on Linux. Windows-compatible dependency wheels were resolved separately. The app has not been executed on the user's Windows laptop yet.

## Results

| Check | Result and evidence |
|---|---|
| Python source/imports | All source parsed/compiled; app and scripts imported with the supplied dependencies |
| Dependencies | `pip check`: no broken requirements; Windows x64 Python 3.12 binary dependency resolution succeeded |
| Files and paths | Required root files, saved model, metrics, CSV, role catalog, sample files and SQL all present; paths resolve from `__file__` |
| Routes/templates/static | Seventeen Flask route rules including static; all fourteen templates compiled; browser requests succeeded |
| Automated tests | **18 passed**, including owner isolation, profile/version/history flow, CSRF, OTP attempts/replay/throttling, invalid uploads, duplicate saves, deletion, score arithmetic, actual extraction and API contracts |
| Classifier | 72 training examples; 24 held-out examples; accuracy 0.875; macro F1 approximately 0.873; evaluated pipeline saved without fitting on test data |
| Visual extraction | Actual direct-PDF/RapidOCR execution on five annotated fictional samples; report in `model/extraction_evaluation.json` |
| Browser flow | Actual Chromium: OTP → profile → sample PDF → review → result → learning steps → v2 upload → history; two records saved; ML role gain +70 percentage points |
| Browser errors | No JavaScript console/page errors and no failed app HTTP responses in that flow |
| Mobile | Dashboard rendered at 390 px wide without horizontal overflow; screenshot included |
| Fresh ZIP smoke test | Extracted into a clean temporary folder; sign-in, upload, review, saved result and evaluation all passed |
| Package layout | `app.py` and `requirements.txt` at ZIP root; runtime database, sessions, keys, virtual environment and caches excluded |

PyMuPDF emits harmless native-extension deprecation warnings under the tested Python version; they did not affect test results.

## External configuration still needed

- **Supabase:** request contracts are tested with mocks and owner policies are supplied in SQL. No user's live Supabase project was connected. Real OTP delivery, SQL application, token refresh and database isolation must be tested after the project URL/public key/SMTP settings are supplied. Follow the two-account steps in `SUPABASE_SETUP.md`.
- **Qwen:** the genuine Ollama image API request and response validation are tested with mocks. The multi-GB Qwen model was not installed or run in this build environment. Therefore no actual Qwen accuracy/performance claim is made. Install and run it on the target machine using `VISION_SETUP.md` and then evaluate it separately.
- **Windows:** the commands and package wheel compatibility were checked; native execution on Windows remains the first local run.

These are setup dependencies; the corresponding application code is implemented. The default demo mode exercises the complete workflow with actual local PDF/OCR extraction and persistence.

## Reproduce

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
python check_setup.py
python train_model.py
python evaluate_extraction.py --engine ocr
```

See `DEMO_GUIDE.md` for the browser workflow. The included screenshots were captured from the working local app with fictional data.
