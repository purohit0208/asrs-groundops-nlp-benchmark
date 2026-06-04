#!/usr/bin/env python
"""
Run a frozen sentence-embedding baseline for record-level ASRS labels.

The model encodes local ASRS text in memory, fits balanced logistic-regression
classifiers, and writes only metrics/predictions/configs. Full raw narratives
are not exported.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from pilot_prescreen import record_text
from run_record_level_baselines import load_records, read_csv, text_for_row, write_csv


ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "splits"
OUTPUT_ROOT = ROOT / "outputs" / "baselines" / f"sentence_embedding_{date.today().isoformat()}"

SPLIT_FILES = {
    "train": SPLIT_DIR / "train_records_2026-06-03.csv",
    "dev": SPLIT_DIR / "dev_records_2026-06-03.csv",
    "test": SPLIT_DIR / "test_records_2026-06-03.csv",
}

TASKS = {
    "screening_status": "silver_screening_status",
    "primary_event_type": "silver_primary_event_type",
}

MODEL_REPO_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_LABEL = "sbert_all_minilm_l6v2_logreg_balanced"
BATCH_SIZE = 32
MAX_SEQ_LENGTH = 256

METRIC_FIELDS = ["task", "model", "split", "n", "accuracy", "macro_f1", "weighted_f1", "micro_f1"]
PREDICTION_FIELDS = ["task", "model", "split", "corpus_id", "acn", "gold_label", "predicted_label", "correct"]


def metrics_row(task: str, split: str, y_true: list[str], y_pred: list[str]) -> dict[str, str]:
    return {
        "task": task,
        "model": MODEL_LABEL,
        "split": split,
        "n": str(len(y_true)),
        "accuracy": f"{accuracy_score(y_true, y_pred):.6f}",
        "macro_f1": f"{f1_score(y_true, y_pred, average='macro', zero_division=0):.6f}",
        "weighted_f1": f"{f1_score(y_true, y_pred, average='weighted', zero_division=0):.6f}",
        "micro_f1": f"{f1_score(y_true, y_pred, average='micro', zero_division=0):.6f}",
    }


def prediction_rows(task: str, split: str, rows: list[dict[str, str]], y_true: list[str], y_pred: list[str]) -> list[dict[str, str]]:
    output = []
    for row, true_label, pred_label in zip(rows, y_true, y_pred):
        output.append(
            {
                "task": task,
                "model": MODEL_LABEL,
                "split": split,
                "corpus_id": row["corpus_id"],
                "acn": row["acn"],
                "gold_label": true_label,
                "predicted_label": pred_label,
                "correct": str(true_label == pred_label).lower(),
            }
        )
    return output


def write_classification_report(path: Path, task: str, split: str, y_true: list[str], y_pred: list[str]) -> None:
    report = classification_report(y_true, y_pred, zero_division=0)
    labels = sorted(set(y_true) | set(y_pred))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Classification Report: {task} / {MODEL_LABEL} / {split}\n\n")
        f.write("```text\n")
        f.write(report)
        f.write("\n```\n\n")
        f.write("## Confusion Matrix\n\n")
        f.write("| gold \\ predicted | " + " | ".join(labels) + " |\n")
        f.write("|---" + "|---" * len(labels) + "|\n")
        for label, values in zip(labels, matrix):
            f.write("| `" + label + "` | " + " | ".join(str(int(value)) for value in values) + " |\n")


def write_summary(metrics: list[dict[str, str]]) -> None:
    summary_path = OUTPUT_ROOT / "sentence_embedding_baseline_summary.md"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Sentence-Embedding Baseline Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("This is a frozen sentence-embedding baseline using `sentence-transformers/all-MiniLM-L6-v2` plus balanced logistic regression. It is not fine-tuned. Full raw ASRS narratives are loaded locally and are not written to output files.\n\n")
        f.write("## Metrics\n\n")
        f.write("| task | model | split | n | accuracy | macro_f1 | weighted_f1 | micro_f1 |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|\n")
        for row in metrics:
            f.write(
                f"| `{row['task']}` | `{row['model']}` | `{row['split']}` | {row['n']} | {row['accuracy']} | {row['macro_f1']} | {row['weighted_f1']} | {row['micro_f1']} |\n"
            )
        f.write("\n## Interpretation\n\n")
        f.write("- Compare these results against TF-IDF as the first non-generative neural representation baseline.\n")
        f.write("- Do not interpret scores as event-mention extraction performance; this is still record-level classification.\n")


def resolve_model_path() -> str:
    cache_root = Path.home() / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots"
    if cache_root.exists():
        snapshots = sorted([path for path in cache_root.iterdir() if path.is_dir()])
        if snapshots:
            return str(snapshots[-1])
    return MODEL_REPO_ID


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    records = load_records()
    split_rows = {split: read_csv(path) for split, path in SPLIT_FILES.items()}

    model_path = resolve_model_path()
    model = SentenceTransformer(model_path)
    model.max_seq_length = MAX_SEQ_LENGTH

    split_texts = {
        split: [text_for_row(row, records) for row in rows]
        for split, rows in split_rows.items()
    }
    split_embeddings = {
        split: model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        for split, texts in split_texts.items()
    }

    metrics = []
    predictions = []

    for task, label_field in TASKS.items():
        y_train = [row[label_field] for row in split_rows["train"]]
        clf = LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
            random_state=20260603,
        )
        clf.fit(split_embeddings["train"], y_train)

        for split in ["dev", "test"]:
            y_true = [row[label_field] for row in split_rows[split]]
            y_pred = list(clf.predict(split_embeddings[split]))
            metrics.append(metrics_row(task, split, y_true, y_pred))
            predictions.extend(prediction_rows(task, split, split_rows[split], y_true, y_pred))
            write_classification_report(
                OUTPUT_ROOT / f"classification_report_{task}_{MODEL_LABEL}_{split}.md",
                task,
                split,
                y_true,
                y_pred,
            )

    write_csv(OUTPUT_ROOT / "sentence_embedding_baseline_metrics.csv", metrics, METRIC_FIELDS)
    write_csv(OUTPUT_ROOT / "sentence_embedding_baseline_predictions.csv", predictions, PREDICTION_FIELDS)
    config = {
        "created": date.today().isoformat(),
        "model_repo_id": MODEL_REPO_ID,
        "model_path_used": model_path,
        "model_label": MODEL_LABEL,
        "max_seq_length": MAX_SEQ_LENGTH,
        "batch_size": BATCH_SIZE,
        "tasks": TASKS,
        "split_files": {key: str(value) for key, value in SPLIT_FILES.items()},
        "boundary": "Full raw ASRS narratives are loaded locally and not written to outputs.",
    }
    (OUTPUT_ROOT / "sentence_embedding_baseline_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    write_summary(metrics)

    print(f"output_dir={OUTPUT_ROOT}")
    print(f"metrics={OUTPUT_ROOT / 'sentence_embedding_baseline_metrics.csv'}")
    for row in metrics:
        if row["split"] == "test":
            print(row)


if __name__ == "__main__":
    main()
