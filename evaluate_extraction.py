"""Measure skill-name precision/recall on bundled, manually annotated samples."""
import argparse
import json
from config import BASE_DIR, settings
from extraction import extract_document
from skills import candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=['ocr','vlm'], default='ocr')
    args = parser.parse_args()
    cfg = settings()
    annotations = json.loads((BASE_DIR / 'data/sample_annotations.json').read_text(encoding='utf-8'))
    rows = []
    for filename, expected in annotations.items():
        document = extract_document((BASE_DIR / 'samples' / filename).read_bytes(), filename, cfg, args.engine)
        found = {s['name'] for s in candidates(document['pages']) if not s['caution']}
        truth = set(expected); tp = len(found & truth)
        precision = tp / len(found) if found else 0
        recall = tp / len(truth)
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        row = dict(file=filename, precision=precision, recall=recall, f1=f1, found=sorted(found),
                   missed=sorted(truth - found), extra=sorted(found - truth),
                   engines=sorted({p['engine'] for p in document['pages']}))
        rows.append(row)
        print(f'{filename}: precision={precision:.3f}, recall={recall:.3f}, F1={f1:.3f}')
    result = dict(engine='PDF text + RapidOCR' if args.engine == 'ocr' else cfg['OLLAMA_MODEL'],
                  note='Five controlled fictional sample files; not an independent real-world benchmark. VLM has not been evaluated unless this report explicitly lists that engine.', samples=rows)
    (BASE_DIR / 'model/extraction_evaluation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

