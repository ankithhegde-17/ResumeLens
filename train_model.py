"""Reproducible supervised role classification on a clearly labeled sample dataset."""
import csv
import hashlib
import json
from datetime import datetime, timezone
import joblib
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from config import BASE_DIR
from skills import names_from_text


def normalized(text):
    return ' '.join(sorted(names_from_text(text)))


def train():
    data_path = BASE_DIR / 'data/role_examples.csv'
    with data_path.open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    training = [r for r in rows if r['split'] == 'train']
    testing = [r for r in rows if r['split'] == 'test']
    x_train = [normalized(r['text']) for r in training]
    x_test = [normalized(r['text']) for r in testing]
    if not training or not testing or set(x_train) & set(x_test):
        raise ValueError('Use non-empty, disjoint training/test normalized skill inputs.')
    if not all(x_train + x_test):
        raise ValueError('Every example must contain supported skills.')
    labels_train, labels_test = [r['role_id'] for r in training], [r['role_id'] for r in testing]
    pipe = Pipeline([('tfidf', TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
                     ('classifier', LogisticRegression(max_iter=2000, C=4, random_state=42))])
    pipe.fit(x_train, labels_train)
    predictions = pipe.predict(x_test)
    labels = list(pipe.classes_)
    report = classification_report(labels_test, predictions, labels=labels, output_dict=True, zero_division=0)
    version = 'role-tfidf-v1'
    metrics = dict(version=version, trained_at=datetime.now(timezone.utc).isoformat(),
                   sklearn_version=sklearn.__version__, train_count=len(training), test_count=len(testing),
                   accuracy=float(accuracy_score(labels_test, predictions)),
                   macro_f1=float(f1_score(labels_test, predictions, average='macro')),
                   labels=labels, per_class={label: report[label] for label in labels},
                   confusion_matrix=confusion_matrix(labels_test, predictions, labels=labels).tolist(),
                   dataset_sha256=hashlib.sha256(data_path.read_bytes()).hexdigest(),
                   dataset_note='96 fictional skill-profile examples, authored for this mini project; 72 train and 24 held-out scenarios. No real candidate or employer data. Generalization is unproven.')
    output = BASE_DIR / 'model'; output.mkdir(exist_ok=True)
    # Save the evaluated pipeline without refitting on the test split.
    joblib.dump(dict(pipeline=pipe, version=version, metrics=metrics), output / 'role_classifier.joblib')
    (output / 'evaluation.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(f'Train: {len(training)} | Held-out: {len(testing)}')
    print(f'Held-out accuracy: {metrics["accuracy"]:.3f} | Macro F1: {metrics["macro_f1"]:.3f}')
    print('Saved model/role_classifier.joblib and model/evaluation.json')
    return metrics


if __name__ == '__main__':
    train()

