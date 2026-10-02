# Career extension — implementation and verification

## Architecture found and retained

Flask server-rendered Jinja pages, local CSS/JavaScript, no frontend build/framework. Email OTP is handled by the existing `Authentication` class; server sessions/drafts use runtime SQLite. Demo profiles/history use SQLite; cloud profiles/history use Supabase REST with user tokens and owner RLS. PDF text precedes OCR/VLM. Confirmed aliases and genuine page quotes feed a weighted deterministic rubric. The saved TF-IDF classifier has eight evaluated categories and remains unchanged.

## Created files

- `career_data.py`: 18 distinct paths, five requirement groups, role-specific stages, three graded projects per path, effort ranges, explainability and personalization.
- `skill_guides.py`: reusable skill records and verified source registry. No duplicated Git/React/Python guides per career.
- `career_routes.py`: career/skill pages, search integration, progress/schedule posts, authenticated bounded chat endpoint.
- `career_assistant.py`: deterministic answers, scope gates, secret checks/redaction, server-only Gemini REST transport, failure/response handling.
- `templates/career_detail.html`, `templates/skill_detail.html`, `templates/career_chat.html`: roadmap timeline, learning guides and accessible modeless assistant.
- `static/career.js`: same-origin chat requests, quick prompts, loading/retry/reset, plain-text messages, Escape/focus return.
- `database/career_learning_migration.sql`: additive Supabase learning tables and owner policies.
- `tests/test_careers.py`: isolated data, routes, persistence, ownership, personalization and mocked provider checks.
- `output/career-roadmaps/`: representative screenshots and layout measurements.

## Modified files

`app.py`, `analysis.py`, `skills.py`, `storage.py`, `config.py`, `.env.example`, `templates/base.html`, `templates/macros.html`, `templates/result.html`, `templates/roles.html`, `static/style.css`, `static/script.js`, `scripts/ui_preview.py`, `tests/test_app.py`, `README.md`.

`.gitignore` already excludes `.env`; it was preserved. No real key was added. No unrelated branding, palette, image, login, profile, history or analysis routes were replaced.

## Database/schema

SQLite adds `learning_progress(user_id,skill_slug,status,updated_at)`, `learning_settings(user_id,hours)`, and expiring `career_chats(session_id,user_id,payload,expires)`. Existing tables and rows remain intact. Progress is scoped to each authenticated owner; chat is also session-scoped. Supabase migration adds the first two tables, foreign keys to `auth.users`, status/schedule constraints and authenticated owner RLS. Chat uses the existing private runtime database in both modes, not a new service.

Curated career/skill/resource content is versioned static Python data, analogous to the project's existing JSON catalog—not user-editable database rows. Compact role metadata is cached once for matching; full roadmap HTML/resources are sent only by detail routes, never embedded into every dashboard. New-version rubrics are explicit educational design choices, not empirical employer models. The original eight score rubrics are retained. Historical records are immutable; exploration computes current guidance from an owned record's confirmed skills.

## All 18 paths

Frontend Developer; UI/UX Designer; Data Analyst; Machine Learning Intern; Python Backend Developer; QA Engineer; Cloud Support Associate; Cybersecurity Analyst; Full Stack Developer; Software Engineer; Data Scientist; AI/ML Engineer; DevOps Engineer; Cloud Engineer; Business Analyst; Mobile App Developer; SOC Analyst; MLOps Engineer.

Intern ML emphasizes basic supervised experiments. AI/ML Engineering adds deep learning and production serving. Data Science adds statistics, experimentation and business interpretation. MLOps focuses on tracking, automated pipelines, release gates and monitoring. Support/cloud engineering and broad cybersecurity/SOC triage have different sequences and projects.

## Research and estimates

Source pages were checked on 2026-10-02. Exact URLs/provider/cost/level/format are in `skill_guides.SOURCES`; guide resource cards cite them directly. Key source families:

- Web/frontend: [MDN curriculum](https://developer.mozilla.org/en-US/docs/Learn_web_development), [React](https://react.dev/learn), [TypeScript](https://www.typescriptlang.org/docs/handbook/intro.html).
- Backend/software: [Python](https://docs.python.org/3/tutorial/), [Flask](https://flask.palletsprojects.com/en/stable/tutorial/), [PostgreSQL](https://www.postgresql.org/docs/current/tutorial.html), [Git](https://git-scm.com/book/en/v2), [Java](https://dev.java/learn/).
- Data/ML: [OpenIntro](https://www.openintro.org/book/os/), [pandas](https://pandas.pydata.org/docs/getting_started/index.html), [scikit-learn](https://scikit-learn.org/stable/getting_started.html), [PyTorch](https://docs.pytorch.org/tutorials/), [MLflow](https://mlflow.org/docs/latest/ml/).
- Infrastructure: [Docker](https://docs.docker.com/get-started/), [Kubernetes](https://kubernetes.io/docs/tutorials/kubernetes-basics/), [Actions](https://docs.github.com/en/actions), [Terraform](https://developer.hashicorp.com/terraform/tutorials), [AWS](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/introduction.html), [Prometheus](https://prometheus.io/docs/introduction/overview/).
- Security/SOC: [PortSwigger](https://portswigger.net/web-security), [OWASP](https://owasp.org/projects/web-security-testing-guide), [Wireshark](https://www.wireshark.org/docs/wsug_html_chunked/), [MITRE](https://attack.mitre.org/), [Elastic Security](https://www.elastic.co/docs/solutions/security).
- Design/business/mobile/QA: [NN/g](https://www.nngroup.com/articles/ux-basics-study-guide/), [Figma](https://help.figma.com/hc/en-us/categories/360002042553-Figma-Design), [IIBA](https://www.iiba.org/professional-development/career-centre/what-is-business-analysis/), [Flutter](https://docs.flutter.dev/learn), [Android](https://developer.android.com/courses), [Selenium](https://www.selenium.dev/documentation/), [Postman](https://learning.postman.com/docs/getting-started/overview/).

These references inform prerequisites and topic scope. They do not establish a universal time to mastery. All hour/journey ranges are explicitly editorial effort estimates for the chosen topics/projects. Different complexities receive different ranges. Whole-path effort allows overlap; schedule conversion is effort ÷ weekly hours, not a sum of every skill's duration. Strong proficiency remains ongoing. Free refers to the linked learning material, not a guaranteed certificate, hosted lab entitlement, software license or cloud compute. Some beginner concept guides link advanced reference material as a second resource; filters make each resource's own level explicit.

## Gemini and privacy

Default `GEMINI_MODEL=gemini-3.5-flash-lite`: stable text output/structured output and latency/cost-conscious use per [official model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) and [pricing](https://ai.google.dev/gemini-api/docs/pricing). `GEMINI_API_KEY` stays server-only in environment/ignored `.env`. `GEMINI_TIMEOUT=25` is optional. No new dependency is required; existing Requests is used.

The browser calls only `/api/career-assistant`. API keys are sent in a Google request header, never URL/browser code. Consent precedes provider use. Structured context contains only known skill names, owned scores, selected career, self-reported progress and schedule; no full resume/JD/source quotes/account identity is added. Incidental emails/phone-like text are redacted from questions; obvious credentials are rejected. Free-tier data policy is disclosed in the UI. Users must still avoid typing private details.

Scope regex/injection rejection, fixed provider system instruction, structured `in_scope` output and response gates form layered safeguards. They are deliberately conservative and can falsely reject or miss ambiguous wording. No heuristic or prompt can guarantee perfect semantic enforcement. No assistant tools/actions/code execution are exposed. Curated resources/prerequisites/time questions bypass Gemini. New conversation clears the eight-message runtime history; logout removes it. UI displays text, not HTML; generated URLs are replaced with a reference to curated guides. CSRF, owner checks, message/context/output bounds, local user rate limits and network timeout apply. Raw prompts, credentials and provider error payloads are not logged.

## Verification

Final automated suite: 58 passed in 31.73 seconds. JavaScript syntax checking passed. Existing four sklearn 1.7.2-vs-1.9.1 model-load warnings remain. The original model was not retrained on fabricated extra categories.

New tests render all 18 careers and all shared guides; validate references/projects/ranges; cover no-resume, Python/SQL, frontend and ML profiles; save Learning/Completed status and schedule; protect two-user ownership; preserve saved output; search machine/cloud/category; filter resources; exercise scope/injection/consent/no-key behavior; mock Gemini success, invalid/denied keys, 429, 5xx, timeout, malformed/blocked responses and unsafe promises; enforce request limits and logout cleanup; verify Supabase owner request contracts. Real PDF/OCR and the existing app flows remain in the original suite.

Browser verification uses a separate temporary demo instance, no real OTP emails or user records. Careers, Full Stack roadmap and React guide checked at 320,390,430,768,820,1024,1440,1920px: no whole-page horizontal overflow observed. Browser interactions confirm progress and schedule saves, quick prompts, off-topic refusal, local Git resource answers and New conversation. Final assistant checks at those eight widths plus 844×390 and 1180×820 landscape found no page horizontal overflow and the panel stayed within the viewport. Mobile reverse-Tab wrapping and Escape/focus restoration passed. No browser console errors/warnings were observed. Screenshots and measurements are in `output/career-roadmaps/`.

## Remaining deployment steps and limits

1. Revoke the key pasted into chat, create a replacement in Google AI Studio and set it privately in `.env` if AI is wanted. The supplied key was not used or saved.
2. Run `database/career_learning_migration.sql` in the existing Supabase SQL Editor before using cloud progress. It was not executed remotely during this task.
3. Restart with `.\.venv\Scripts\python.exe app.py` and hard-refresh.

Live Gemini success/quota availability and the real Supabase migration/RLS have not been tested with real credentials; mocked contracts are not live verification. Roadmap content is curated educational guidance, not a comprehensive accredited course or hiring predictor. Browser checks are representative, not an exhaustive accessibility audit. External links can change. Rate limits are local to this app's runtime DB, suitable for this single-host academic project, not a distributed production quota system.

Exact Windows checks and start commands are in the README. No package/framework migration is required.
