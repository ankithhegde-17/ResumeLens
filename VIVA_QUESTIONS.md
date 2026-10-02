# Viva questions — Multimodal Resume Analyzer

1. **What is the objective?** Help students find evidenced skills, compare role requirements and plan what to learn or document next.
2. **What problem does it solve?** Resumes may be PDFs, scans or photos, and unexplained matching scores are difficult to use.
3. **Who uses the project?** Students and early-career job seekers.
4. **Why is it called multimodal?** The vision-language path accepts visual page pixels together with a language instruction to extract resume text.
5. **Which vision-language model is used?** Qwen2.5-VL 3B, served locally by Ollama after its weights are installed.
6. **Is OCR the same as a VLM?** No. OCR reads text in images; a VLM combines visual understanding and language processing. The UI labels the engine used.
7. **What happens before Ollama is installed?** Images and scans use pretrained RapidOCR. The core app runs in local demo mode.
8. **Why use Flask?** It provides simple routes and templates, and is easy to run and explain in a small project.
9. **What is the frontend?** HTML and CSS templates with small JavaScript helpers for file selection, search and loading messages.
10. **How is PDF text read?** PyMuPDF reads selectable text or renders an image-only page for visual extraction.
11. **Why have a review screen?** OCR and VLMs can misread text. The user corrects it and confirms genuine skill evidence before scoring.
12. **How are skills extracted?** A small alias dictionary searches the reviewed text and stores the actual supporting line and page.
13. **What does a missing skill mean?** It is not evidenced in this resume. It does not prove the person cannot use that skill.
14. **How is the coverage score calculated?** Matched required weights divided by all required weights, multiplied by 100.
15. **Give a score example.** Python weight 3 plus SQL weight 2 against a total required weight of 10 gives 50%.
16. **Do optional skills change that score?** No. They are displayed separately so the required-coverage formula stays transparent.
17. **Which model is trained?** A TF-IDF and logistic regression role classifier, saved as one Scikit-learn pipeline.
18. **What is the dataset?** Ninety-six fictional examples: 72 train and 24 held out, across eight role categories.
19. **What evaluation is shown?** Accuracy, macro F1, per-class precision/recall/F1 and a confusion matrix. The shipped test accuracy is 87.5% on fictional examples.
20. **Does classifier accuracy describe OCR accuracy?** No. They are different components with separate evaluations.
21. **Why save the vectorizer with the model?** Training and prediction must use the same feature vocabulary and transformation.
22. **What does the Careers section do?** It shows more roles, unevidenced requirements, learning steps and a portfolio project idea.
23. **How does email OTP work?** Supabase emails and verifies a numeric code. Cloud mode accepts the full 6–10 digit code, including eight digits. Local demo mode uses a six-digit terminal code without sending email.
24. **Which database is used?** SQLite for local demonstration and runtime sessions; Supabase Postgres for cloud profiles and analysis history.
25. **What is Row Level Security?** A database rule that lets a user access only rows owned by their authenticated user ID.
26. **How is history versioned?** Each confirmed analysis is a new record. The highest version in a collection is current; earlier records remain separate.
27. **What can users edit?** Their display name, headline, location and career goal. Existing analysis versions remain immutable.
28. **Are raw resumes retained?** Original uploaded files are discarded after extraction. Reviewed text and results are saved for history.
29. **What testing is performed?** Complete local flows, wrong OTPs, ownership, file validation, score checks, actual OCR, and model/API compatibility checks.
30. **What are the limitations?** Poor images, a small English vocabulary/catalog, limited negation handling and a fictional classifier dataset.
31. **Can the project guarantee a job?** No. It measures documented requirement coverage and gives learning guidance; employers make hiring decisions.
32. **What is the future scope?** Evaluated real data, more roles and languages, better evidence extraction and verified job listings.
