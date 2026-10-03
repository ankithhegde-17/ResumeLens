# Performance audit — 2026-10-03

Baseline: main e782578. Design, branding, glass styling and classifier are unchanged. Benchmarks use fictional data. No live OCR/Gemini requests or private-user records were used; secrets were not printed.

## Findings and optimizations

- Ordinary pages imported PyMuPDF, NumPy, Pillow and joblib. These are now imported only inside extraction/model functions. OCR was already lazy/cached. The model loader is cached and locked so concurrent first analyses cannot deserialize it twice.
- Browser navigation previously made GET + restore POST, including for an empty saved workspace. Same-origin links/GET filters now send signed state on the first request. Empty workspace reloads skip restoration. Form redirects use the same reader. Modified clicks, external links, fragment links, downloads and Back/Forward remain supported.
- Summary/detail lookup deep-copied every full saved analysis. Summaries now copy only displayed result projections; details copy the selected record only. Repeated export within one request reuses signing/compression until state changes. Ownership, CSRF, expiry and no-store private responses remain unchanged.
- Asset versions use content fingerprints cached per app instance: unchanged files retain URLs across redeploys, with no repeated file reads/stats per page. Stable catalog was already cached; evaluation JSON is now cached. Catalog context is only added to pages that use it. Python career/skill metadata was already loaded once.
- Original login artwork is preserved, but retired PNG/WebP and unused favicon SVG are excluded from publication/function packaging. Build cleanup removes only their generated CDN copies. Active images were already small; no recompression or quality loss was necessary. Logo retains explicit dimensions and uses asynchronous decoding.
- Versioned Flask static URLs retain immutable caching; unversioned assets use one-hour caching. Vercel CDN uses explicit one-hour browser/one-day edge caching. Private HTML/JSON remain no-store.
- Added bounded browser requests, inference/template/route timings and optional PERFORMANCE_DIAGNOSTICS=true logs/Server-Timing. Logs contain stages/template names/endpoints/durations, not IDs, prompts, contents or secrets. Normal production emits no new timing logs. Removed unused account-era UserTTLCache.
- Added /careers as a direct alias of /roles (previously 404); existing URLs remain valid.

## Local before/after measurements

Windows Python 3.14 virtualenv, isolated hosted-mode test client. Import median: three fresh processes. Route warm median: five requests after initial render. These are local execution timings, not forced Vercel cold starts; OS caches/CPU contention affect results.

| Measurement | Before | After |
|---|---:|---:|
| Fresh app import | 490.75 ms | 327.83 ms |
| First / including template compilation | 30.89 ms | 27.45 ms |
| Warm / | 1.22 ms | 0.93 ms |
| Warm /dashboard | 1.21 ms | 0.90 ms |
| Warm /upload | 1.23 ms | 0.95 ms |
| Warm /roles | 2.36 ms | 2.03 ms |
| Warm representative career | 2.54 ms | 2.41 ms |
| Warm /skills/react | 1.50 ms | 0.90 ms |
| Warm /evaluation | 1.60 ms | 0.94 ms |
| /careers | 404 | 200; 2.02 ms warm |
| Same-browser navigation requests | GET + POST (2) | POST (1) |
| Summary projection of 20 independent analyses | 22.15 ms | 1.25 ms |
| Published static total | 182,427 bytes | 97,707 bytes |

Summary baseline is the exact previous implementation run on the same decoded fictional dataset in the same benchmark. First analysis/model load: 1,496.81 → 959.93 ms; cached analysis: 1.61 → 1.36 ms. Heavy work now happens on the first actual analysis, not homepage import. Filesystem differences mean model timings are not a guaranteed speedup. Live provider latency was not measured.

## Assets, frontend and dependencies

Source static total: 6,110,686 → 6,114,143 bytes. Source art remains; single-request navigation/loading feedback adds about 3.5 KB. The CDN reduction is unused-file cleanup, not a 6 MB normal-page download saving: the old PNG was already excluded and normal pages did not request login art.

| Image | Bytes | Status |
|---|---:|---|
| login-hero.png | 5,928,259 | Source retained; already excluded |
| login-hero.webp | 87,938 | Source retained; newly excluded |
| apple-touch-icon.png | 22,665 | Kept; largest published image |
| logo.png | 12,138 | Kept, identical appearance |
| favicon.ico | 5,071 | Kept |
| favicon.png | 1,526 | Kept |
| favicon.svg | 239 | Source retained; publication excluded |

CSS remains 35,920 bytes. JS totals 19,890 → 23,408 bytes. Scripts already defer; chat exists on all pages, so career.js remains shared. Fonts use the existing system stack, with no blocking remote font requests. Existing mobile blur/glass styling, layout, shadows and reduced-motion rules are preserved. No measured reason justified design changes or minification dependencies.

No requirements removed: Flask, requests, dotenv, PyMuPDF, Pillow, NumPy, sklearn and joblib all have active uses. Removing ML/image libraries would break features. psycopg/auth packages were already absent.

## Production/browser/Lighthouse evidence

Read-only baseline at https://resumelens.prayogmanch.in: sampled TTFB 62–74 ms; DOMContentLoaded 295–341 ms across homepage/dashboard/upload/roles/career/skill. These are warmed samples from one machine, not global field metrics.

Production Lighthouse baseline: performance 65, FCP 1,078 ms, LCP 1,315 ms, CLS 0.796, TBT 432 ms. Production layout shift requires post-deployment measurement; do not claim local results prove it is resolved.

Post-deployment check (October 3): the optimized workspace script and fingerprinted assets are live. Production Lighthouse performance is 75, FCP 1,154 ms, LCP 1,222 ms, CLS 0.796 and TBT 0 ms. Warmed page samples across homepage, dashboard, upload, careers, career detail and skill detail measured TTFB 60–71 ms and DOMContentLoaded 289–323 ms. Browser navigation uses one state-carrying POST. These are individual lab runs, not field metrics or guaranteed cold-start results.

Remaining issue: the production layout shift is not fixed. An uncached 390 px browser check with 150 ms network latency reproduced CLS 0.776 at stylesheet completion, with the body and statistic cards attributed as sources. A cached check recorded no shifts. The stylesheet is a normal head stylesheet link in the served HTML; the precise reason for the early paint remains unconfirmed. Do not infer that the local CLS 0 result resolves this production issue. Reports are saved in ignored output/playwright/lighthouse-production-after.json.

Isolated historical/current hosted-mode local builds, Lighthouse mobile simulation: performance 94 → 96; FCP 1,909 → 2,084 ms; LCP 2,134 → 2,159 ms; CLS 0 → 0; TBT 0 → 0. Single-run noise prevents claiming faster LCP. TBT is a lab measure, not field INP. A separate non-isolated local run scored 91. Reports/screenshots remain in ignored output/playwright. Historical benchmark copy/helper servers were removed/stopped; source history remains recoverable from Git. Main local server remains running.

## API/data conclusions

- Supabase/Postgres/auth runtime is absent: zero database calls to optimize.
- Gemini runs only on explicit chat POSTs after scope/consent checks, never page navigation. Defaults remain connect/read 5/25 seconds; browser chat timeout 35 seconds. OCR transport remains 5/35 seconds. Diagnostic timings include failed attempts but no raw provider errors or prompts.
- Hosted PDFs inspect embedded text before remote OCR. Pillow imports only when validating/rendering images; NumPy/RapidOCR import only for local OCR. Hosted OCR remains a separate private service.
- Debug is off; no hosted local-secret disk fallback. Populated workspace state still travels with navigation (existing 2 MiB uncompressed cap). Direct reload/Back with real saved state may still need restoration. Cross-user HTML caching is intentionally prohibited.

## Verification/deployment

77 tests passed, including lazy import, model reuse, export cache, optional diagnostics and CDN/cache checks. Four existing sklearn 1.7.2-model/1.9.1-local-runtime warnings remain; Vercel requirements pin 1.7.2. Installation/import and static build checks pass.

Browser fictional PDF → review → results, JSON export, GET resource filtering, curated chat, history/Back, mobile menu and 56 page-width checks at 320, 390, 430, 768, 820, 1024, 1440 and 1920 pixels passed; no horizontal overflow. Console had no errors/warnings. Gemini/OCR provider behavior uses mocks/local fixtures; no live success claim.

Push main triggers the linked deployment if Vercel Git integration is configured. Redeploy latest main if needed; no new required variables/migrations. Keep stable SECRET_KEY, COOKIE_SECURE=true and optional providers. Diagnostics default false. Check final Vercel build/bundle logs and remeasure production after deployment; local import gains are not a measured Vercel cold-start guarantee.

Repeat: python scripts/performance_audit.py; python -m pytest tests -q. Isolated preview: python scripts/performance_server.py --port 5053 (provider credentials disabled).
