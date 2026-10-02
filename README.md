# Multimodal Resume Analyzer — ResumeLens

**Vercel preparation:** see [deployment setup and limits](docs/VERCEL_DEPLOYMENT.md).
Hosted operation requires private Supabase runtime state, production settings,
and the optional private OCR service for images/scans. The lean web dependency
bundle is approximately 283 MiB; see [bundle analysis](docs/BUNDLE_SIZE_ANALYSIS.md). A successful
local test is not a verified Vercel deployment.

A complete Flask mini project for students: PDF/image resume extraction, reviewed skill evidence, explainable role coverage, learning guidance, email OTP accounts and version history.

**First run:** the project opens in local demo mode, without cloud keys. It includes an evaluated trained classifier, fictional sample resumes, a neural OCR fallback and the Supabase/VLM integrations. Real email delivery and cloud records require your Supabase settings. The actual vision-language model requires a separate Ollama model download.

## 1. Project objective

Help students understand the skills evidenced in a resume uploaded as a PDF, scan, or photograph. Explain alignment with a small role catalog and show which additional requirements to learn or document. Let each user review extraction, edit a profile, and revisit earlier analysis versions through email OTP accounts.

## 2. Problem statement

Resumes arrive in different visual formats. Text-only parsers fail on scans; an unexplained score offers little guidance. Students need reviewable skill evidence, a clear requirement-coverage formula and practical next steps. This app gives educational career guidance. It does not predict whether a candidate will be hired or establish that an absent skill is unknown to the candidate.

## 3. Main users and features

**Users:** college students and early-career job seekers. No admin portal is needed for this scope; the role catalog is a clearly editable JSON file.

1. Email OTP sign-in: terminal-only codes for local demo, real email via Supabase when configured.
2. Genuine PDF/JPG/PNG upload validation: up to 10 MB, five PDF pages and bounded image dimensions.
3. Selectable PDF text extraction; neural OCR for scans/photos; actual Qwen2.5-VL image-plus-language extraction through Ollama.
4. Editable text review, per-page engine badges, cautious skill selection and real source quotes.
5. Eighteen curated career paths with explicit weighted required-skill coverage, personalized roadmaps, shared skill guides and private learning progress. The evaluated classifier remains a separate eight-class signal.
6. Explore Careers: more role options, unevidenced requirements, learning resources and portfolio project ideas.
7. Optional pasted job-description matching with a separate equal-weight skill comparison.
8. Profile edits: display name, headline, location and goal role.
9. Immutable version history, current-version labels, skill changes and coverage comparisons.
10. Trained TF-IDF role classifier, held-out evaluation page, JSON report export and owner-only history deletion.

## 4. Technologies used

| Technology | Purpose |
|---|---|
| Python 3.11/3.12, Flask | Simple routes, forms and server-rendered pages |
| HTML, CSS, JavaScript | Responsive professional frontend, validation and loading messages; no Node build required |
| PyMuPDF, Pillow | PDF extraction/rendering, image validation and orientation |
| RapidOCR + ONNX Runtime | Pretrained neural text extraction for scans/images on CPU |
| Ollama + Qwen2.5-VL 3B | Actual local vision-language page transcription, configured separately |
| Scikit-learn, NumPy, Joblib | TF-IDF/logistic regression classifier, metrics and saved model |
| SQLite | Immediately runnable demo data, local short-lived drafts and server-side sessions |
| Supabase Auth + Postgres REST | Real email OTP and private cloud profiles/history when enabled |
| Requests, python-dotenv | Small API clients and local environment settings |

Supabase follows the agreed account architecture. SQLite makes the supplied package runnable before cloud configuration. Ollama keeps the vision model local; RapidOCR provides an image path without a multi-GB model download. OCR and VLM results are labeled separately.

## 5. Folder structure

| Path | Contents |
|---|---|
| `app.py` | Web routes and form validation |
| `config.py`, `auth.py`, `storage.py` | Settings, OTP sessions, local/cloud repositories |
| `extraction.py`, `skills.py`, `analysis.py` | PDF/OCR/VLM extraction, vocabulary/evidence, scoring |
| `train_model.py`, `evaluate_extraction.py` | Reproducible classifier training and extraction checks |
| `check_setup.py`, `make_samples.py` | Read-only setup diagnostics and sample regeneration |
| `templates/` | Login, verification, dashboard, upload, review, results, careers, history, profile, evaluation and help |
| `static/` | Local CSS and JavaScript; no remote CDN assets |
| `data/` | Role catalog/learning steps, 96-example CSV and annotated sample truth |
| `model/` | Saved classifier, classification metrics and extraction metrics |
| `samples/` | Text PDF, scan PDF, PNG, simulated phone JPG, improved v2 PDF, text and JD |
| `database/supabase_schema.sql` | Tables, grants, owner policies and version-saving RPC |
| `docs/` | Supabase/VLM setup, architecture, demonstration and verification notes |
| `tests/test_app.py` | Flow, scoring, ownership, validation and extraction regression checks |
| `requirements.txt`, `requirements-dev.txt`, `.env.example` | Installation/configuration |
| `VIVA_QUESTIONS.md` | Project-specific questions and short answers |
| `instance/` *(created when running)* | Runtime SQLite, random signing key and account/draft data; excluded from ZIP |

## 6. How the system works

1. Sign in with an OTP: six digits in local demo mode, or the complete 6–10 digit code emailed by Supabase in cloud mode. A signed browser cookie holds an opaque session reference. Supabase tokens stay in the local server-side runtime database.
2. Upload a resume or select a fictional sample. The backend validates actual file contents, size and pages.
3. Directly read selectable PDF text. For visual pages, use Qwen if installed in automatic mode; otherwise use RapidOCR. Explicit VLM mode requires the vision model and returns an error if it fails.
4. Review each page's text and extraction engine. Correct mistakes, **refresh the skill list**, and select only genuinely evidenced skills.
5. Normalize aliases such as JS → JavaScript. Word boundaries prevent Java matching JavaScript. Basic negative phrases are flagged for review. The dictionary does not infer SQL from a database name or infer competency from a mere mention.
6. Compare confirmed skills with the catalog. For each role:

   `Coverage (%) = 100 × sum of matched required weights / sum of all required weights`

   Example: Python (weight 3) and SQL (weight 2) match a backend rubric with total weight 10 → **50% coverage**. Optional skills are displayed separately and do not change this score.
7. Run the saved classifier on the same normalized skill representation used in training. Show its three category estimates separately; they do not alter the coverage score.
8. Save the reviewed text, evidence, result and model/catalog versions as a new immutable analysis. A later upload can be added to the same resume collection; the latest version is labeled current.
9. Open a more ambitious role, review unevidenced requirements, follow learning steps, build the portfolio project and document truthful evidence in a future resume.

The role catalog contains examples of entry-level profiles, **not current job advertisements**. Actual employers may require different tools, experience and qualifications. A requirement mention in a pasted job description is treated as required in this simple project, even if the description calls it optional; the UI explains this limitation.

## 7. Database details

### Local demo

The app creates `instance/app.sqlite3` automatically. `profiles` stores editable details; `analyses` stores per-user results and version numbers. `auth_sessions` holds opaque sessions; `challenges` holds hashed local demo OTPs; `rate_limits` throttles requests; `drafts` expires after one hour. Demo email is a local identity for demonstration, not proof of mailbox ownership. Demo codes are printed to the terminal and are **never emailed**.

### Supabase mode

Run the SQL and use `APP_MODE=supabase`. `profiles` references the Supabase user's UUID. `analyses` stores the collection UUID, version, source, reviewed text/evidence/result JSON and catalog/model identifiers. Owner-only RLS applies to all API reads and writes. A transaction assigns versions and makes duplicate saves idempotent. Profiles can be updated; analysis versions cannot. Only the owner's entire selected collection can be deleted through the UI.

Original uploaded files are processed in memory and discarded. Reviewed text contains personal data and is retained for history until the user deletes the collection. Local drafts and sessions remain local even in cloud mode. Protect the `instance/` directory and `.env`; neither is supplied in the ZIP. Local history is not automatically migrated into Supabase.

## 8. Machine learning model details

### Trained role classifier (included)

- Dataset: `data/role_examples.csv` — **96 fictional skill-profile examples**, eight labels, 72 training and 24 specified held-out scenarios.
- Input: confirmed normalized skill names. Names, email, age, gender and photo appearance are not classifier features.
- Features: TF-IDF word unigrams and bigrams.
- Model: logistic regression; fixed random seed, max 2,000 iterations.
- One scikit-learn pipeline saves the feature transformation and classifier together. Training checks that normalized inputs do not overlap across splits.
- The shipped pipeline is fit only on the training split. Its test accuracy is **87.5%**, macro F1 approximately **0.873**. See the actual per-class report/confusion matrix in `model/evaluation.json` and the Evaluation page. Retraining may produce slight numerical differences if you change packages/data.
- This small authored dataset is educational, not representative of real resumes. Classifier estimates are not calibrated employment probabilities. Coverage is computed by the explicit rubric, independently.

### Visual models

RapidOCR and Qwen use existing pretrained models. They are not retrained here. The ZIP includes the OCR dependency and VLM client; Qwen weights are downloaded separately. The bundled extraction report measures supported skill names on five controlled fictional sample files: direct PDF extraction found all annotated skills; OCR missed some phrase/name spellings in image samples. Correcting those errors is part of the review workflow. This is not a real-world benchmark or full text accuracy claim. No measured Qwen result is included before you install and evaluate it locally.

## 9. How to run on Windows in VS Code

**Use 64-bit Python 3.11 or 3.12.** Node.js, CUDA installation, Tesseract and a Supabase account are not needed for the initial OCR demo. Internet is needed to install Python packages and later download Qwen.

### STEP 1 — Download and extract the ZIP

Extract `Multimodal Resume Analyzer.zip` completely. Do not run files from inside the ZIP preview.

### STEP 2 — Open the extracted project folder in VS Code

Choose **File → Open Folder** and select the folder that directly contains **`app.py` and `requirements.txt`**. The ZIP puts those files at its root to avoid the earlier nested-folder problem.

### STEP 3 — Open Terminal in VS Code

Choose **Terminal → New Terminal**. In PowerShell, check:

```powershell
Get-Location
dir app.py, requirements.txt
python --version
```

If `app.py` or `requirements.txt` is missing, open the correct extracted folder before continuing. Do not create the virtual environment in a parent folder.

### STEP 4 — Create a virtual environment

```powershell
python -m venv venv
```

If multiple Python versions are installed, you can use `py -3.12 -m venv venv` instead.

### STEP 5 — Activate the virtual environment

```powershell
venv\Scripts\activate
```

In PowerShell the explicit form is:

```powershell
.\venv\Scripts\Activate.ps1
```

If activation is blocked by your PowerShell policy, activation is optional. Use the virtual environment's Python directly for every following command:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
.\venv\Scripts\python.exe check_setup.py
.\venv\Scripts\python.exe app.py
```

### STEP 6 — Install dependencies

```powershell
pip install -r requirements-ocr.txt
```

With an activated environment, `python -m pip install -r requirements-ocr.txt` is equivalent and ensures the intended Python is used. A pip update notice is informational; it does not explain a missing requirements file.

### STEP 7 — Check setup

```powershell
python check_setup.py
```

The trained model and sample files are already included. Local database creation is automatic. “Vision model ready: False” is expected before Ollama setup; the OCR demo still runs. No training command is mandatory for the first run.

To reproduce model training and extraction evaluation, run:

```powershell
python train_model.py
python evaluate_extraction.py --engine ocr
```

To prepare later cloud/VLM settings:

```powershell
Copy-Item .env.example .env
```

Edit `.env` in VS Code. Follow `docs/SUPABASE_SETUP.md` for the SQL/email configuration and `docs/VISION_SETUP.md` for the real vision model. Restart Flask after changing environment values. No cloud key is prefilled or required for demo mode.

### STEP 8 — Run the application

```powershell
python app.py
```

Keep this terminal running. The server listens only on your local computer. Stop it with **Ctrl+C**. This Flask development server is for local academic demonstration.

### STEP 9 — Open the browser

Open **http://127.0.0.1:5000/**.

Enter an email such as `student@example.com` in demo mode. Click Send sign-in code. Copy the six digits from the VS Code terminal into the verification page. In Supabase mode, use your actual inbox instead.

If port 5000 is already in use, stop the other server or set `PORT=5001` in `.env`; then open http://127.0.0.1:5001/.

## 10. Sample inputs and outputs

| Input | Expected demonstration |
|---|---|
| `samples/sample_resume.pdf` | Direct PDF text; eight reviewed skills; Data Analyst coverage 100% against the small rubric |
| `samples/sample_resume.png` | Visual path; RapidOCR by default before Ollama, or Qwen in explicit VLM mode; review misread phrase spellings before saving |
| `samples/sample_phone_photo.jpg` | Simulated tilted/softened phone image; shows why photo quality and review matter |
| `samples/sample_scanned_resume.pdf` | Image-only PDF routed to OCR/VLM |
| `samples/sample_resume_v2.pdf` | Four extra skills; Machine Learning Intern coverage rises from 30% to 100% when all sample skills are confirmed |
| `samples/sample_job_description.txt` | Optional custom comparison; v1 matches all recognized requirements except Statistics (after reviewing all eight v1 skills) |

For a version demonstration, first analyze the text sample. Download the v2 PDF from Help, go to Analyze Resume, select **New version of the same collection**, and upload it. The history must show v1 and v2 with only v2 current. Both Data Analyst scores may remain 100%; the ML role gains coverage because the newly evidenced skills match its rubric.

For a learning demonstration, open Explore Careers and expand **Machine Learning Intern** or **Python Backend Developer**. Explain the missing requirements, their weights, suggested practice and portfolio project.

## Validation and basic security

- Server-side file type/content, size, PDF page count, image pixels, text length, email, OTP and profile validation.
- CSRF protection on every POST; escaped templates; secure cookie options; opaque server-side sessions; no browser exposure of cloud tokens.
- Short OTP expiry/attempt cap in demo; request throttling; Supabase controls real OTP validity.
- Every draft/history/read/export/delete is tied to the signed-in owner; Supabase enforces RLS too.
- Local session database contains sensitive runtime tokens. Keep it private. Hosted operation needs HTTPS, managed server sessions, stronger distributed rate limiting and deployment hardening.
- Only load the project's trusted Joblib model. Never load an unknown model file uploaded by a user.

## Testing and verification

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

The tests cover the full local flow, versioning, profile changes, cross-user isolation, CSRF, OTP failure/replay/rate limits, input errors, real OCR/PDF extraction, score arithmetic, saved model/catalog compatibility and mocked VLM/Supabase request contracts. See `docs/VERIFICATION.md` for actual packaging checks and the limits of testing without your cloud/model configuration.

## Limitations and future scope

English, printed resumes and 18 curated career paths are supported. Blurry photos, unusual layouts, compact OCR text and model hallucinations need manual correction. Keyword evidence does not prove skill proficiency. Basic negation detection is incomplete; users must check context. The classifier's fictional eight-class dataset does not establish general accuracy or fairness. This app does not inspect faces, infer protected attributes, analyze video/audio, search live jobs or promise employment.

Future work can add evaluated real/consented data, more languages, a larger validated role catalog, stronger extraction metrics, verified job feeds, richer skill proficiency evidence and production deployment controls. Keep users in control of their career choices.

## Career Roadmaps and Learning Resources

All 18 careers have distinct learning sequences and beginner/intermediate/advanced projects: Frontend Developer, UI/UX Designer, Data Analyst, Machine Learning Intern, Python Backend Developer, QA Engineer, Cloud Support Associate, Cybersecurity Analyst, Full Stack Developer, Software Engineer, Data Scientist, AI/ML Engineer, DevOps Engineer, Cloud Engineer, Business Analyst, Mobile App Developer, SOC Analyst and MLOps Engineer.

Use Explore Careers to search names, descriptions and skill requirements, or filter by category. Open a career, then a clickable skill to view prerequisites, topics, a practice milestone and curated external resources. Filters support free-only, level and format. Free reading does not imply free certification, software licenses, cloud compute or every linked service feature.

Learning progress is private and shared by skill across paths. Not Started / Learning / Completed are explicit user choices, never inferred from resume detection. Study schedules use 5, 10 or 20 hours/week. Effort/time ranges are editorial planning estimates based on curriculum scope, not universal empirically validated learning durations. Whole-path effort includes overlapping practice instead of adding every skill's range.

Saved analysis versions are never rewritten. Current exploration recomputes alignment across 18 paths from reviewed skill evidence; original eight rubrics are retained. The existing trained model and evaluation remain eight-class and separate from deterministic coverage.

### Database setup

SQLite learning tables are created additively on restart. For Supabase, run `database/career_learning_migration.sql` in the existing project's SQL Editor. It adds owner-RLS-protected `learning_progress` and `learning_settings`; it does not replace profiles, analyses or authentication. Without this migration, new pages explain why cloud progress cannot be saved; the existing analyzer still works.

## Gemini Career Assistant

The optional floating R. Career AI uses our Flask backend, not browser-to-Google requests. Curated resource/time/prerequisite answers are local. Other career questions require explicit consent before a bounded question, recent conversation and necessary skill/roadmap context are sent to Google. Raw resume pages, JD text, source quotes, names, authentication tokens and OTPs are not added to model context. Do not put personal details or secrets in questions.

Get a replacement key from [Google AI Studio](https://aistudio.google.com/apikey). Never paste keys into chat, source code or frontend code. Put these server-only variables in the existing ignored `.env`:

```dotenv
GEMINI_API_KEY=your_new_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TIMEOUT=25
```

The default is the stable, text-capable, low-latency `gemini-3.5-flash-lite`, checked against the [official model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) and [pricing](https://ai.google.dev/gemini-api/docs/pricing). Free-tier availability/quota depends on the account and may change. Free-tier provider data policies differ from paid service policies: the chat consent includes Google's possible product-improvement use. No paid service is automatically enabled. Model selection is configurable.

### AI Scope and controls

Only resume, skill, learning, career, project, internship, interview, LinkedIn and job-preparation topics are intended. Server-side domain/injection checks refuse clearly unrelated requests before provider calls; fixed system instructions and structured response checks add safeguards. This is defense in depth, not a guarantee against every semantic prompt injection. No tools or code execution are enabled for the assistant.

CSRF and authentication apply to chat. A 1,200-character input cap, eight-message server history (six previous messages sent), a 700-output-token budget, rapid-submit suppression, 12 requests/minute and 60/day per user bound usage. Missing/invalid keys, timeouts, quota and provider failures return friendly messages without disabling the analyzer. New conversation clears history; local session-bound chat expires in one hour and is removed on logout. Chat is not placed in the signed browser cookie. Responses render as plain text, never executable HTML.

### Verify locally (Windows PowerShell)

```powershell
Set-Location 'C:\Users\hegde\OneDrive\Desktop\Multimodal Resume Analyzer'
.\.venv\Scripts\python.exe -m pytest -q
node --check static\script.js
node --check static\career.js
.\.venv\Scripts\python.exe app.py
```

If the app is already running, stop its terminal with Ctrl+C first. Open `http://127.0.0.1:5000/roles`, then hard-refresh with Ctrl+F5. The optional isolated fixture UI server is `.\.venv\Scripts\python.exe scripts\ui_preview.py` on port 5051, with Gemini disabled and temporary demo data only.

See [implementation and source notes](docs/CAREER_ROADMAPS.md) for files, schema, researched source families, verification and remaining limits. Live Gemini and Supabase migration verification require your replacement key and cloud setup; mocks are not evidence of live provider availability.
