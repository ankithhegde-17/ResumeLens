# Vercel bundle reduction (2026-10-02)

## Measured before making changes

User's Vercel build: **588.02 MB**, rejected by the standard 500 MB limit.
Resolved Linux x86-64 CPython 3.12 wheels: **604,909,831 bytes / 576.9 MiB**
uncompressed. Wheel bytes are a dependency estimate, not a deployed bundle.

| Dependency | MiB | Proven runtime use |
|---|---:|---|
| GUI OpenCV | 186.9 | RapidOCR image processing only; transitive |
| SciPy | 106.8 | scikit-learn trained pipeline; retain |
| NumPy | 55.1 | trained classifier and local image arrays; retain |
| PyMuPDF | 54.7 | direct PDF text/rendering; retain |
| ONNX Runtime | 44.7 | RapidOCR inference only |
| scikit-learn | 31.8 | `analysis.model_bundle` / saved classifier; retain |
| SymPy | 25.6 | ONNX runtime dependency, not web analysis |
| Pillow | 16.7 | genuine image validation/conversion; retain |
| RapidOCR | ~14 | OCR implementation and models only |

Explicit ONNX pin and RapidOCR's ONNX dependency resolve to **one wheel**, not
two copies. Removing just the explicit ONNX line would not remove it. SciPy is
pulled by scikit-learn; training-only removal cannot eliminate it while retaining
the saved sklearn model. `joblib` is needed to load that existing pipeline.

## Safe headless attempt

Downloaded and measured `opencv-python-headless==4.11.0.86`: **135.4 MiB**.
Replacing the GUI wheel, not adding a second cv2 provider, yields **525.4 MiB**
before app/bytecode overhead. Still too large. No application dependencies were
changed during this measurement. Official OpenCV guidance identifies headless
as the server/no-GUI variant:
[OpenCV installation](https://docs.opencv.org/5.0/py_tutorials/py_setup/py_pip_install/py_pip_install.html).

## Final web requirements

`requirements.txt` retains Flask, Requests, python-dotenv, PyMuPDF, Pillow,
NumPy, scikit-learn, joblib and psycopg. OCR-only dependencies leave the Vercel
graph: RapidOCR/models, ONNX Runtime, OpenCV, pyclipper, Shapely, PyYAML, SymPy
and other ONNX/OCR-only transitives. No classifier feature is removed.

Resolved lean Linux wheels: **296,660,210 bytes / 282.9 MiB**, 23 wheels.
App/templates/catalog/model/retained small samples add less than 2 MiB; an
estimated **~285 MiB before installation/bytecode overhead** leaves over 200 MiB
under the 500 MB cap. Final Vercel logs remain authoritative. Resolved transitives
can change; the measurements describe this resolution, not a permanent ceiling.

Native OCR moves to `ocr_service/`; the container uses coordinated headless
OpenCV and RapidOCR `--no-deps` installation. Local full development uses
`requirements-ocr.txt`; tests use `requirements-dev.txt` including full OCR.

Exclude development tests/docs/cache, training script/data, OCR-service code,
source hero PNG and oversized scanned sample. Retain saved classifier and its
evaluation JSON, role catalog, all templates, displayed assets and small samples
actually referenced by the UI/help routes. `/samples/sample_scanned_resume.pdf`
is unavailable on Vercel because it also exceeds the function payload limit;
it remains available locally. Web code cannot accidentally invoke local OCR on
Vercel: scan/image branches route to the private service, direct text PDFs do not.

## Verification

85 tests passed in the final run (23.33 seconds), including the original classifier/full version-history flow,
real local OCR, hosted text PDF extraction with no remote call, mixed PDF one-call
transport, authorization, size/type errors, output validation, timeout and remote
4xx/5xx handling. Existing four sklearn version warnings remain. Separate isolated
Python 3.12 web-only installation passed import, login/static/dashboard/careers/
profile/history, saved classifier prediction and text PDF extraction, with no
RapidOCR/ONNX/OpenCV installed. A second isolated Python 3.12 service installation
passed authenticated real image OCR with only headless OpenCV and no sklearn.
The default Python 3.14 install attempt failed on pinned NumPy; these checks used
the compatible 3.12 interpreter matching the deployment pin. Docker/live OCR
deployment was not run. No real resume was sent to an external service during testing.

Modified files: `requirements.txt`, `requirements-dev.txt`, `config.py`,
`extraction.py`, `app.py`, `vercel.json`, `.env.example`, `README.md`,
`START_HERE_WINDOWS.txt`, `docs/VERCEL_DEPLOYMENT.md`.
Created: `requirements-ocr.txt`, `remote_ocr.py`, `.dockerignore`,
`ocr_service/{__init__.py,app.py,wsgi.py,requirements.txt,Dockerfile,README.md}`,
`tests/test_remote_ocr.py`, `scripts/check_web_install.py`,
`scripts/check_ocr_install.py`, this report.
