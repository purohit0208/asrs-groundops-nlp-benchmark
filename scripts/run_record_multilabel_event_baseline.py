#!/usr/bin/env python
"""
Run a record-level multi-label event-type baseline for ASRS records.

This handles possible multi-event records without claiming event-span
annotation. Full ASRS narratives are loaded locally for vectorization, but only
metrics, label sets, and predictions are written.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, hamming_loss, jaccard_score
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC

from run_record_level_baselines import load_records, read_csv, text_for_row, write_csv


ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "splits"
OUTPUT_ROOT = ROOT / "outputs" / "baselines" / f"record_multilabel_{date.today().isoformat()}"

SPLIT_FILES = {
    "train": SPLIT_DIR / "train_records_2026-06-03.csv",
    "dev": SPLIT_DIR / "dev_records_2026-06-03.csv",
    "test": SPLIT_DIR / "test_records_2026-06-03.csv",
}

MODEL_LABEL = "tfidf_word13_char36_ovr_linear_svc_multilabel"
RANDOM_STATE = 20260603

METRIC_FIELDS = [
    "task",
    "model",
    "split",
    "n",
    "label_count",
    "subset_accuracy",
    "micro_f1",
    "macro_f1",
    "samples_f1",
    "samples_jaccard",
    "hamming_loss",
]

PREDICTION_FIELDS = [
    "task",
    "model",
    "split",
    "corpus_id",
    "acn",
    "gold_labels",
    "predicted_labels",
    "exact_match",
]


def event_labels(row: dict[str, str]) -> list[str]:
    labels = []
    primary = row.get("silver_primary_event_type", "").strip()
    if primary and primary != "not_relevant":
        labels.append(primary)
    secondary = row.get("silver_secondary_event_types", "").strip()
    if secondary:
        labels.extend(label.strip() for label in secondary.split(";") if label.strip() and label.strip() != "not_relevant")
    # Preserve deterministic order while removing duplicates.
    return list(dict.fromkeys(labels))


def relevant_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("silver_screening_status") == "include_ground_cabin_event" and event_labels(row)
    ]


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


def transform_texts(texts: list[str], word_vectorizer: TfidfVectorizer, char_vectorizer: TfidfVectorizer):
    word_matrix = word_vectorizer.transform(texts)
    char_matrix = char_vectorizer.transform(texts)
    return hstack([word_matrix, char_matrix], format="csr")


def subset_accuracy(y_true, y_pred) -> float:
    if y_true.shape[0] == 0:
        return 0.0
    exact = (y_true != y_pred).sum(axis=1) == 0
    return float(exact.mean())


def metrics_row(split: str, y_true, y_pred, label_count: int) -> dict[str, str]:
    return {
        "task": "record_level_event_multilabel_relevant_only",
        "model": MODEL_LABEL,
        "split": split,
        "n": str(y_true.shape[0]),
        "label_count": str(label_count),
        "subset_accuracy": f"{subset_accuracy(y_true, y_pred):.6f}",
        "micro_f1": f"{f1_score(y_true, y_pred, average='micro', zero_division=0):.6f}",
        "macro_f1": f"{f1_score(y_true, y_pred, average='macro', zero_division=0):.6f}",
        "samples_f1": f"{f1_score(y_true, y_pred, average='samples', zero_division=0):.6f}",
        "samples_jaccard": f"{jaccard_score(y_true, y_pred, average='samples', zero_division=0):.6f}",
        "hamming_loss": f"{hamming_loss(y_true, y_pred):.6f}",
    }


def prediction_rows(split: str, rows: list[dict[str, str]], y_true, y_pred, mlb: MultiLabelBinarizer) -> list[dict[str, str]]:
    true_sets = mlb.inverse_transform(y_true)
    pred_sets = mlb.inverse_transform(y_pred)
    output = []
    for row, true_labels, pred_labels in zip(rows, true_sets, pred_sets):
        true_list = sorted(true_labels)
        pred_list = sorted(pred_labels)
        output.append(
            {
                "task": "record_level_event_multilabel_relevant_only",
                "model": MODEL_LABEL,
                "split": split,
                "corpus_id": row["corpus_id"],
                "acn": row["acn"],
                "gold_labels": ";".join(true_list),
                "predicted_labels": ";".join(pred_list),
                "exact_match": str(true_list == pred_list).lower(),
            }
        )
    return output


def write_label_report(path: Path, y_true, y_pred, labels: list[str]) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("# Multi-Label Per-Label Report\n\n")
        f.write("| label | support | predicted_positive | precision | recall | f1 |\n")
        f.write("|---|---:|---:|---:|---:|---:|\n")
        for index, label in enumerate(labels):
            true_col = y_true[:, index]
            pred_col = y_pred[:, index]
            tp = int(((true_col == 1) & (pred_col == 1)).sum())
            fp = int(((true_col == 0) & (pred_col == 1)).sum())
            fn = int(((true_col == 1) & (pred_col == 0)).sum())
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
            f.write(
                f"| `{label}` | {int(true_col.sum())} | {int(pred_col.sum())} | {precision:.6f} | {recall:.6f} | {f1:.6f} |\n"
            )


def write_summary(metrics: list[dict[str, str]], label_counts: Counter, split_counts: dict[str, int]) -> None:
    summary_path = OUTPUT_ROOT / "record_multilabel_event_baseline_summary.md"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Record-Level Multi-Label Event Baseline Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("This baseline treats each included ASRS record as a set of event-type labels assembled from `silver_primary_event_type` plus `silver_secondary_event_types`. It does not create event spans and must not be described as event-mention extraction. Full raw ASRS narratives are loaded locally and are not written to output files.\n\n")
        f.write("## Relevant-Record Split Counts\n\n")
        for split, count in split_counts.items():
            f.write(f"- `{split}`: {count}\n")
        f.write("\n## Label Counts In Training Set\n\n")
        f.write("| label | count |\n")
        f.write("|---|---:|\n")
        for label, count in sorted(label_counts.items(), key=lambda item: (-item[1], item[0])):
            f.write(f"| `{label}` | {count} |\n")
        f.write("\n## Metrics\n\n")
        f.write("| split | n | label_count | subset_accuracy | micro_f1 | macro_f1 | samples_f1 | samples_jaccard | hamming_loss |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in metrics:
            f.write(
                f"| `{row['split']}` | {row['n']} | {row['label_count']} | {row['subset_accuracy']} | {row['micro_f1']} | {row['macro_f1']} | {row['samples_f1']} | {row['samples_jaccard']} | {row['hamming_loss']} |\n"
            )
        f.write("\n## Interpretation\n\n")
        f.write("- This is the manuscript-safe alternative for multi-event records until event-span annotation exists.\n")
        f.write("- Use these scores to discuss record-level multi-label tagging, not event-level extraction.\n")
        f.write("- Compare with primary-event single-label metrics to show why multi-event handling matters.\n")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    all_split_rows = {split: read_csv(path) for split, path in SPLIT_FILES.items()}
    split_rows = {split: relevant_rows(rows) for split, rows in all_split_rows.items()}
    split_counts = {split: len(rows) for split, rows in split_rows.items()}
    split_texts = build_texts(split_rows)
    split_label_sets = {split: [event_labels(row) for row in rows] for split, rows in split_rows.items()}

    mlb = MultiLabelBinarizer()
    y_train = mlb.fit_transform(split_label_sets["train"])
    word_vectorizer, char_vectorizer = fit_vectorizers(split_texts["train"])
    x_train = transform_texts(split_texts["train"], word_vectorizer, char_vectorizer)

    model = OneVsRestClassifier(
        LinearSVC(class_weight="balanced", random_state=RANDOM_STATE, max_iter=6000)
    )
    model.fit(x_train, y_train)

    metrics = []
    predictions = []
    for split in ["dev", "test"]:
        x_split = transform_texts(split_texts[split], word_vectorizer, char_vectorizer)
        y_true = mlb.transform(split_label_sets[split])
        y_pred = model.predict(x_split)
        metrics.append(metrics_row(split, y_true, y_pred, len(mlb.classes_)))
        predictions.extend(prediction_rows(split, split_rows[split], y_true, y_pred, mlb))
        write_label_report(
            OUTPUT_ROOT / f"per_label_report_{split}.md",
            y_true,
            y_pred,
            list(mlb.classes_),
        )

    write_csv(OUTPUT_ROOT / "record_multilabel_event_baseline_metrics.csv", metrics, METRIC_FIELDS)
    write_csv(OUTPUT_ROOT / "record_multilabel_event_baseline_predictions.csv", predictions, PREDICTION_FIELDS)
    label_counts = Counter(label for labels in split_label_sets["train"] for label in labels)
    config = {
        "created": date.today().isoformat(),
        "model": MODEL_LABEL,
        "task": "record_level_event_multilabel_relevant_only",
        "labels": list(mlb.classes_),
        "split_files": {key: str(value) for key, value in SPLIT_FILES.items()},
        "split_counts": split_counts,
        "boundary": "Record-level multi-label event tagging from primary+secondary labels; no event spans; raw narratives are not written.",
    }
    (OUTPUT_ROOT / "record_multilabel_event_baseline_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    write_summary(metrics, label_counts, split_counts)

    print(f"output_dir={OUTPUT_ROOT}")
    for row in metrics:
        print(row)


if __name__ == "__main__":
    main()
