# Historical notes (pre-authentication-removal)

This document describes the former account-based implementation. Login, OTP,
Supabase persistence and server runtime setup below are obsolete for the current
anonymous app. See README.md and docs/VERCEL_DEPLOYMENT.md for active behavior.

# Suggested academic demonstration

## Explain the objective in 20 seconds

“Our system accepts a resume as a PDF, scan or photo, extracts its text, lets the user review the skills, and explains alignment with role requirements. It also recommends learning steps for other roles and keeps private analysis versions.”

## Demonstration sequence

1. Start with `python app.py` and open localhost. Demonstrate email OTP using the terminal code in local demo mode, or your inbox after Supabase configuration.
2. Save a display name, headline and career goal in My Profile.
3. Try the fictional sample PDF. Point to the **PDF text** badge on review. Show Python's exact evidence and page number.
4. Confirm the reviewed skills. Open the Data Analyst card: 10 matched weight / 10 required weight = 100%. Explain that this is a small rubric, not a hiring or ATS probability.
5. Show the backend role's lower coverage, its missing Flask and REST API requirements, and the suggested portfolio project.
6. Open Explore Careers. Expand Machine Learning Intern. Point to Machine Learning, Scikit-learn, NumPy and Statistics as requirements not evidenced in v1. Show the learning and practice steps.
7. Download `sample_resume_v2.pdf`, select a new version of the same collection and upload it. Show the four added skills and the ML coverage increase from 30% to 100%. Both versions remain in History.
8. Download the PNG or simulated phone photo and analyze it. If Ollama is not installed, show the **RapidOCR** badge and explain the fallback. Correct `PowerBl` to `Power BI` and `DataVisualization` to `Data Visualization` if those spellings were misread, then refresh skills and confirm genuine corrections.
9. With Qwen installed, select **Vision-language for every page**, upload the PNG and show the **Qwen vision-language** badge. This is the explicit multimodal demonstration.
10. Open Model Evaluation. Explain 72 training examples, 24 held out and 87.5% measured accuracy on fictional data. The saved classifier is separate from the transparent coverage rubric.
11. Sign out and sign in with the same account to show persistence. Use another account to show private separation.

## Presentation screenshots

`docs/screenshots/` contains real screenshots captured from this application's local demo: login, dashboard, results, careers and a mobile view. They use a fictional demo account. They are examples for presentation, not preloaded user data.

## Talking points

- The VLM receives image pixels and a text instruction; the classifier receives only confirmed skills.
- The original files are discarded. Reviewed text is retained for history until a collection is deleted.
- An absence from the resume is different from absence of knowledge.
- The user reviews evidence and employers make hiring decisions.
- Supabase and Ollama are configured externally. Their absence is clearly labeled, and no cloud credentials are embedded in the package.
