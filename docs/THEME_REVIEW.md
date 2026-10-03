# Local appearance and mobile-header review

## Changes in this refinement

- `templates/base.html`: removed the Browser workspace header pill; early preference resolver before the stylesheet.
- `templates/profile.html`: accessible Automatic / Light / Dark radio cards, immediate selection and live status.
- `templates/dashboard.html`: requested compact mobile storage disclaimer.
- `static/script.js`: localStorage `resumelens-theme` (`system`, `light`, `dark`); default system; live OS changes only in system mode; safe storage failures; one OS listener across document replacements.
- `static/style.css`: exact existing light paint values moved into shared surface/border/shadow tokens; a single dark override block; calm layered slate colours, desaturated primary/active navigation, readable controls and chat; 64px mobile header with 44px touch targets. Existing desktop grids, spacing and dimensions retained. Appearance adds a section only on Preferences.
- `app.py`: security header only, permitting the exact early script SHA-256 hash. No unsafe-inline and no application/analysis/storage changes. The hash regression test must pass after any initializer edits.
- `tests/test_appearance.py`: head order, CSP hash, preferences and sidebar contracts.
- `tests/test_ui_polish.py`: updated expected mobile disclaimer copy.

## Verification

85 tests passed; eight pre-existing scikit-learn model-version warnings. JavaScript syntax and git whitespace checks passed.

216 real-browser theme/width checks: dashboard, upload, career list, history, preferences, help, evaluation, terms, fictional extracted-text review, fictional analysis results, Data Analyst roadmap and Experimentation guide. Light and dark at 360, 375, 390, 412, 430, 768, 1024, 1366 and 1920px: no horizontal page overflow. Mobile toolbar 64px; hamburger and AI targets 44px.

Verified system light/dark and live changes, explicit overrides, refresh persistence, native-radio arrow-key operation, menu Escape closure, and chat opening/closure. No JavaScript runtime errors in the page sweep. Initial blocked inline-script console error was corrected with the hash allowlist and covered by the test.

Dark palette contrast checks (solid token pairs): primary 10.82+, secondary 6.0+, links 5.0+, primary buttons 5.0+, active navigation 6.0+, semantic success/warning/error 7.0+. These are token checks, not a full WCAG audit of every translucent composite.

Screenshots under ignored `output/playwright/`: theme-light-dashboard-mobile.png, theme-dark-dashboard-mobile.png, theme-light-tablet.png, theme-light-desktop.png, theme-dark-desktop.png, theme-dark-chat.png and theme-dark-results-desktop.png.

## Limits

Chromium desktop emulation only; no physical phone, Safari or Firefox checks. Appearance controls, theme refresh and native scheme tested locally; no production deployment. No real records, remote OCR or Gemini requests were used. No new dependencies. The local isolated preview is at http://127.0.0.1:5053/.

All changes remain unstaged/uncommitted. Existing unrelated local refinements were preserved.
