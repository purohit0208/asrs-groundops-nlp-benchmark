#!/usr/bin/env python
"""
Run local classical baselines for the expanded 8,800 training design.

Train uses the original verified train rows plus the 3,800 expanded agent-silver
rows. Dev/test remain the original author-verified local-audit rows.
Raw ASRS text is loaded locally and is not written to output files.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from scipy.sparse import hstack
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.svm import LinearSVC

from run_record_level_baselines import load_records, text_for_row


ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "splits"
OUTPUT_ROOT = ROOT / "outputs" / "baselines" / f"expanded_8800_reference_classical_{date.today().isoformat()}"

SPLIT_FILES = {
    "train": SPLIT_DIR / "expanded_8800_reference_eval_train_records_2026-06-04.csv",
    "dev": SPLIT_DIR / "expanded_8800_reference_eval_dev_records_2026-06-04.csv",
    "test": SPLIT_DIR / "expanded_8800_reference_eval_test_records_2026-06-04.csv",
}

TASKS = {
    "screening_status": "silver_screening_status",
    "primary_event_type": "silver_primary_event_type",
}

METRIC_FIELDS = [
    "training_design",
    "task",
    "model",
    "split",
    "n",
    "accuracy",
    "macro_f1",
    "weighted_f1",
    "micro_f1",
]
PREDICTION_FIELDS = [
    "training_design",
    "task",
    "model",
    "split",
    "corpus_id",
    "acn",
    "gold_label",
    "predicted_label",
    "correct",
]

TRAINING_DESIGN = "expanded_8800_weak_train_verified_dev_test"
SEED = 20260604


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def metrics_row(task: str, model: str, split: str, y_true: list[str], y_pred: list[str]) -> dict[str, str]:
    return {
        "training_design": TRAINING_DESIGN,
        "task": task,
        "model": model,
        "split": split,
        "n": str(len(y_true)),
        "accuracy": f"{accuracy_score(y_true, y_pred):.6f}",
        "macro_f1": f"{f1_score(y_true, y_pred, average='macro', zero_division=0):.6f}",
        "weighted_f1": f"{f1_score(y_true, y_pred, average='weighted', zero_division=0):.6f}",
        "micro_f1": f"{f1_score(y_true, y_pred, average='micro', zero_division=0):.6f}",
    }


def prediction_rows(
    task: str,
    model: str,
    split: str,
    rows: list[dict[str, str]],
    y_true: list[str],
    y_pred: list[str],
) -> list[dict[str, str]]:
    return [
        {
            "training_design": TRAINING_DESIGN,
            "task": task,
            "model": model,
            "split": split,
            "corpus_id": row["corpus_id"],
            "acn": row["acn"],
            "gold_label": true_label,
            "predicted_label": pred_label,
            "correct": str(true_label == pred_label).lower(),
        }
        for row, true_label, pred_label in zip(rows, y_true, y_pred)
    ]


def write_classification_report(path: Path, task: str, model: str, split: str, y_true: list[str], y_pred: list[str]) -> None:
    labels = sorted(set(y_true) | set(y_pred))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Classification Report: {task} / {model} / {split}\n\n")
        f.write("```text\n")
        f.write(classification_report(y_true, y_pred, zero_division=0))
        f.write("\n```\n\n")
        f.write("## Confusion Matrix\n\n")
        f.write("| gold \\ predicted | " + " | ".join(labels) + " |\n")
        f.write("|---" + "|---" * len(labels) + "|\n")
        for label, values in zip(labels, matrix):
            f.write("| `" + label + "` | " + " | ".join(str(int(value)) for value in values) + " |\n")


def build_texts(split_rows: dict[str, list[dict[str, str]]]) -> dict[str, list[str]]:
    records = load_records()
    return {split: [text_for_row(row, records) for row in rows] for split, rows in split_rows.items()}


def fit_vectorizers(train_texts: list[str]) -> tuple[TfidfVectorizer, TfidfVectorizer]:
    word_vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 3),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        max_features=120000,
    )
    char_vectorizer = TfidfVectorizer(
        lowercase=True,
        analyzer="char_wb",
        ngram_range=(3, 6),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        max_features=160000,
    )
    word_vectorizer.fit(train_texts)
    char_vectorizer.fit(train_texts)
    return word_vectorizer, char_vectorizer


def transform_splits(split_texts: dict[str, list[str]], word_vectorizer: TfidfVectorizer, char_vectorizer: TfidfVectorizer):
    matrices = {}
    for split, texts in split_texts.items():
        word = word_vectorizer.transform(texts)
        char = char_vectorizer.transform(texts)
        matrices[split] = {"word": word, "char": char, "combined": hstack([word, char], format="csr")}
    return matrices


def labels_for(split_rows: dict[str, list[dict[str, str]]], label_field: str) -> dict[str, list[str]]:
    return {split: [row[label_field] for row in rows] for split, rows in split_rows.items()}


def run_model(task: str, model_name: str, model, train_matrix, split_matrices, split_rows, split_labels):
    model.fit(train_matrix, split_labels["train"])
    metrics = []
    predictions = []
    for split in ["dev", "test"]:
        y_true = split_labels[split]
        y_pred = list(model.predict(split_matrices[split]))
        metrics.append(metrics_row(task, model_name, split, y_true, y_pred))
        predictions.extend(prediction_rows(task, model_name, split, split_rows[split], y_true, y_pred))
        write_classification_report(
            OUTPUT_ROOT / f"classification_report_{task}_{model_name}_{split}.md",
            task,
            model_name,
            split,
            y_true,
            y_pred,
        )
    return metrics, predictions


def write_summary(metrics: list[dict[str, str]], split_rows: dict[str, list[dict[str, str]]]) -> None:
    train_role_counts = {}
    for row in split_rows["train"]:
        train_role_counts[row["expanded_corpus_role"]] = train_role_counts.get(row["expanded_corpus_role"], 0) + 1

    with (OUTPUT_ROOT / "expanded_8800_reference_classical_summary.md").open("w", encoding="utf-8") as f:
        f.write("# Expanded 8,800 Reference-Evaluation Classical Baseline Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("Train contains the original verified train rows plus 3,800 expanded agent-silver rows. Dev/test are the original verified reference rows. Full raw ASRS narratives are loaded locally and not written to output files.\n\n")
        f.write("## Train Provenance Counts\n\n")
        for key, value in sorted(train_role_counts.items()):
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Metrics\n\n")
        f.write("| task | model | split | n | accuracy | macro_f1 | weighted_f1 | micro_f1 |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|\n")
        for row in metrics:
            f.write(
                f"| `{row['task']}` | `{row['model']}` | `{row['split']}` | {row['n']} | {row['accuracy']} | {row['macro_f1']} | {row['weighted_f1']} | {row['micro_f1']} |\n"
            )
        f.write("\n## Interpretation Boundary\n\n")
        f.write("- Use these as expanded weak-label training results against verified dev/test labels.\n")
        f.write("- Do not claim all 8,800 labels are human verified.\n")
        f.write("- Do not interpret record-level labels as event-span extraction.\n")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    split_rows = {split: read_csv(path) for split, path in SPLIT_FILES.items()}
    split_texts = build_texts(split_rows)
    word_vectorizer, char_vectorizer = fit_vectorizers(split_texts["train"])
    matrices = transform_splits(split_texts, word_vectorizer, char_vectorizer)

    metrics = []
    predictions = []
    for task, label_field in TASKS.items():
        split_labels = labels_for(split_rows, label_field)
        model_specs = [
            ("majority_most_frequent", DummyClassifier(strategy="most_frequent"), "word"),
            (
                "tfidf_word13_logreg_balanced",
                LogisticRegression(max_iter=4000, class_weight="balanced", solver="liblinear", random_state=SEED),
                "word",
            ),
            (
                "tfidf_char36_logreg_balanced",
                LogisticRegression(max_iter=4000, class_weight="balanced", solver="liblinear", random_state=SEED),
                "char",
            ),
            ("tfidf_word13_linear_svc_balanced", LinearSVC(class_weight="balanced", random_state=SEED, max_iter=7000), "word"),
            ("tfidf_char36_linear_svc_balanced", LinearSVC(class_weight="balanced", random_state=SEED, max_iter=7000), "char"),
            (
                "tfidf_word13_char36_linear_svc_balanced",
                LinearSVC(class_weight="balanced", random_state=SEED, max_iter=7000),
                "combined",
            ),
            (
                "tfidf_word13_char36_calibrated_svc_balanced",
                CalibratedClassifierCV(
                    estimator=LinearSVC(class_weight="balanced", random_state=SEED, max_iter=7000),
                    method="sigmoid",
                    cv=3,
                ),
                "combined",
            ),
        ]
        for model_name, model, matrix_key in model_specs:
            model_metrics, model_predictions = run_model(
                task,
                model_name,
                model,
                matrices["train"][matrix_key],
                {split: split_matrices[matrix_key] for split, split_matrices in matrices.items()},
                split_rows,
                split_labels,
            )
            metrics.extend(model_metrics)
            predictions.extend(model_predictions)

    write_csv(OUTPUT_ROOT / "expanded_8800_reference_classical_metrics.csv", metrics, METRIC_FIELDS)
    write_csv(OUTPUT_ROOT / "expanded_8800_reference_classical_predictions.csv", predictions, PREDICTION_FIELDS)
    config = {
        "created": date.today().isoformat(),
        "training_design": TRAINING_DESIGN,
        "split_files": {key: str(value) for key, value in SPLIT_FILES.items()},
        "tasks": TASKS,
        "seed": SEED,
    }
    (OUTPUT_ROOT / "expanded_8800_reference_classical_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    write_summary(metrics, split_rows)

    print(f"output={OUTPUT_ROOT}")
    for row in metrics:
        if row["split"] == "test":
            print(row)


if __name__ == "__main__":
    main()
