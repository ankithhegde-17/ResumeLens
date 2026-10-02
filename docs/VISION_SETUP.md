# Enable the actual vision-language model on Windows

## Why this component is included

The approved architecture uses **Qwen2.5-VL 3B via Ollama** for page images. It accepts image pixels plus a language instruction, then transcribes the page into JSON text. The Flask app has a working `/api/generate` integration; it does not substitute a text-only model and call it multimodal.

The ZIP contains the app, integration and a small trained role classifier. It does **not** contain Qwen's multi-GB pretrained weights. You download those through Ollama. Qwen and OCR use pretrained weights; this project does not claim to train a foundation vision model.

## Windows steps

1. Install Ollama for Windows from https://ollama.com/download/windows. Open the installed app and keep it running. Restart your VS Code terminal if `ollama` is not recognized.
2. In a separate terminal, download the vision model:

```powershell
ollama pull qwen2.5vl:3b
ollama list
```

3. If Ollama is not running, start it with `ollama serve` in that separate terminal. If it reports that port 11434 is already in use, the Ollama application is already serving; do not start a duplicate.
4. In the project `.env`, keep:

```dotenv
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5vl:3b
OLLAMA_TIMEOUT=180
EXTRACTION_ENGINE=auto
```

5. In the project's activated Python terminal:

```powershell
python check_setup.py
python app.py
```

6. Open **Help & setup**. It should show that the model is ready.
7. Upload the sample PNG or scanned PDF. **To prove the VLM path explicitly**, select **Vision-language model for every page**. This also renders a text PDF into an image before sending it to Qwen. The review page must show **Qwen vision-language**.
8. Review the text, correct errors, refresh the skill list, then confirm it. The model can misread or hallucinate text; review remains necessary.

## Engine choices

| Choice | Behavior |
|---|---|
| Automatic | Selectable PDF text is read directly. Image/scan pages use Qwen if its model is available; otherwise RapidOCR. A failed VLM request can fall back to OCR with a visible note. |
| PDF text + OCR | Selectable PDFs use direct text; scans/images use local pretrained RapidOCR. No Ollama needed. |
| Vision-language for every page | Every PDF page is rendered and every image goes through Qwen. If unavailable or failed, show an error rather than claim a VLM result. |

The OCR wheel includes neural OCR models and runs on CPU; Tesseract is not required. OCR is a visual text reader, but it is **not a vision-language foundation model**. The UI always records which engine ran.

## Hardware and speed

- The Flask/OCR/classifier demo works on a normal 64-bit Windows computer with Python 3.11 or 3.12. 8 GB RAM is a practical minimum; 16 GB is preferable.
- For local Qwen, memory depends on the installed quantization and Ollama build. Your RTX 4060 laptop is a reasonable machine on which to try the 3B variant, but available VRAM, page size and other running apps affect speed. CPU inference is possible and can be much slower.
- Check `ollama list` for the actual download size. Allow several GB of disk space for the model. No performance guarantee is made.
- Pages are processed sequentially, maximum five. The first request loads the model and can be slower. For a live demo use a clear one-page resume. Increase OLLAMA_TIMEOUT if a valid local request needs longer.

## Evaluate your installed vision model

```powershell
python evaluate_extraction.py --engine vlm
```

This writes a new `model/extraction_evaluation.json` for the actual VLM. The bundled report was measured with direct PDF extraction/RapidOCR, not Qwen. It measures skill-name detection on five controlled fictional samples, not general text transcription or real-world resume quality.

Official references:

- https://ollama.com/library/qwen2.5vl
- https://docs.ollama.com/api/generate
- https://github.com/RapidAI/RapidOCR

