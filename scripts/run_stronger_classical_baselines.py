#!/usr/bin/env python
"""
Run stronger local classical baselines for record-level ASRS labels.

The script loads full ASRS text locally from raw JSON files, fits word/character
TF-IDF linear classifiers, and writes only metrics, predictions, and configs.
No full raw narrative text is exported.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from scipy.sparse import hstack
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.svm import LinearSVC

from run_record_level_baselines import load_records, read_csv, text_for_row, write_csv


ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "splits"
OUTPUT_ROOT = ROOT / "outputs" / "baselines" / f"stronger_classical_{date.today().isoformat()}"

SPLIT_FILES = {
    "train": SPLIT_DIR / "train_records_2026-06-04.csv",
    "dev": SPLIT_DIR / "dev_records_2026-06-04.csv",
    "test": SPLIT_DIR / "test_records_2026-06-04.csv",
}

TASKS = {
    "screening_status": "silver_screening_status",
    "primary_event_type": "silver_primary_event_type",
}

METRIC_FIELDS = ["task", "model", "split", "n", "accuracy", "macro_f1", "weighted_f1", "micro_f1"]
PREDICTION_FIELDS = ["task", "model", "split", "corpus_id", "acn", "gold_label", "predicted_label", "correct"]

WORD_MODEL = "tfidf_word13_linear_svc_balanced"
CHAR_MODEL = "tfidf_char36_linear_svc_balanced"
COMBINED_MODEL = "tfidf_word13_char36_linear_svc_balanced"
CALIBRATED_MODEL = "tfidf_word13_char36_calibrated_svc_balanced"


def metrics_row(task: str, model: str, split: str, y_true: list[str], y_pred: list[str]) -> dict[str, str]:
    return {
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
    output = []
    for row, true_label, pred_label in zip(rows, y_true, y_pred):
        output.append(
            {
                "task": task,
                "model": model,
                "split": split,
                "corpus_id": row["corpus_id"],
                "acn": row["acn"],
                "gold_label": true_label,
                "predicted_label": pred_label,
                "correct": str(true_label == pred_label).lower(),
            }
        )
    return output


def write_classification_report(path: Path, task: str, model: str, split: str, y_true: list[str], y_pred: list[str]) -> None:
    report = classification_report(y_true, y_pred, zero_division=0)
    labels = sorted(set(y_true) | set(y_pred))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Classification Report: {task} / {model} / {split}\n\n")
        f.write("```text\n")
        f.write(report)
        f.write("\n```\n\n")
        f.write("## Confusion Matrix\n\n")
        f.write("| gold \\ predicted | " + " | ".join(labels) + " |\n")
        f.write("|---" + "|---" * len(labels) + "|\n")
        for label, values in zip(labels, matrix):
            f.write("| `" + label + "` | " + " | ".join(str(int(value)) for value in values) + " |\n")


def build_texts(split_rows: dict[str, list[dict[str, str]]]) -> dict[str, list[str]]:
    records = load_records()
    return {
        split: [text_for_row(row, records) for row in rows]
        for split, rows in split_rows.items()
    }


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


def transform_splits(
    split_texts: dict[str, list[str]],
    word_vectorizer: TfidfVectorizer,
    char_vectorizer: TfidfVectorizer,
) -> dict[str, dict[str, object]]:
    matrices: dict[str, dict[str, object]] = {}
    for split, texts in split_texts.items():
        word_matrix = word_vectorizer.transform(texts)
        char_matrix = char_vectorizer.transform(texts)
        matrices[split] = {
            "word": word_matrix,
            "char": char_matrix,
            "combined": hstack([word_matrix, char_matrix], format="csr"),
        }
    return matrices


def labels_for(split_rows: dict[str, list[dict[str, str]]], label_field: str) -> dict[str, list[str]]:
    return {
        split: [row[label_field] for row in rows]
        for split, rows in split_rows.items()
    }


def run_model(
    task: str,
    model_name: str,
    model,
    train_matrix,
    split_matrices: dict[str, object],
    split_rows: dict[str, list[dict[str, str]]],
    split_labels: dict[str, list[str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
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


def write_summary(metrics: list[dict[str, str]]) -> None:
    summary_path = OUTPUT_ROOT / "stronger_classical_baseline_summary.md"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Stronger Classical Baseline Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("These are local TF-IDF plus LinearSVC baselines for the author-verified record-level ASRS corpus with local consistency-audit support. Full raw ASRS narratives are loaded locally and are not written to output files.\n\n")
        f.write("## Metrics\n\n")
        f.write("| task | model | split | n | accuracy | macro_f1 | weighted_f1 | micro_f1 |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|\n")
        for row in metrics:
            f.write(
                f"| `{row['task']}` | `{row['model']}` | `{row['split']}` | {row['n']} | {row['accuracy']} | {row['macro_f1']} | {row['weighted_f1']} | {row['micro_f1']} |\n"
            )
        f.write("\n## Interpretation\n\n")
        f.write("- Treat these as independent classical ML baselines.\n")
        f.write("- Compare against logistic-regression TF-IDF, frozen MiniLM, and supervised MiniLM before deciding whether an LLM structured-output baseline is worth the extra complexity.\n")
        f.write("- Do not interpret record-level scores as full event-mention extraction performance.\n")


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
            (
                WORD_MODEL,
                LinearSVC(class_weight="balanced", random_state=20260603, max_iter=6000),
                "word",
            ),
            (
                CHAR_MODEL,
                LinearSVC(class_weight="balanced", random_state=20260603, max_iter=6000),
                "char",
            ),
            (
                COMBINED_MODEL,
                LinearSVC(class_weight="balanced", random_state=20260603, max_iter=6000),
                "combined",
            ),
            (
                CALIBRATED_MODEL,
                CalibratedClassifierCV(
                    estimator=LinearSVC(class_weight="balanced", random_state=20260603, max_iter=6000),
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

    write_csv(OUTPUT_ROOT / "stronger_classical_baseline_metrics.csv", metrics, METRIC_FIELDS)
    write_csv(OUTPUT_ROOT / "stronger_classical_baseline_predictions.csv", predictions, PREDICTION_FIELDS)
    config = {
        "created": date.today().isoformat(),
        "models": [WORD_MODEL, CHAR_MODEL, COMBINED_MODEL, CALIBRATED_MODEL],
        "tasks": TASKS,
        "split_files": {key: str(value) for key, value in SPLIT_FILES.items()},
        "word_vectorizer": {
            "ngram_range": [1, 3],
            "min_df": 2,
            "max_df": 0.95,
            "sublinear_tf": True,
            "max_features": 120000,
        },
        "char_vectorizer": {
            "analyzer": "char_wb",
            "ngram_range": [3, 6],
            "min_df": 2,
            "max_df": 0.95,
            "sublinear_tf": True,
            "max_features": 160000,
        },
        "boundary": "Full raw ASRS narratives are loaded locally and not written to outputs.",
    }
    (OUTPUT_ROOT / "stronger_classical_baseline_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    write_summary(metrics)

    print(f"output_dir={OUTPUT_ROOT}")
    print(f"metrics={OUTPUT_ROOT / 'stronger_classical_baseline_metrics.csv'}")
    for row in metrics:
        if row["split"] == "test":
            print(row)


if __name__ == "__main__":
    main()
