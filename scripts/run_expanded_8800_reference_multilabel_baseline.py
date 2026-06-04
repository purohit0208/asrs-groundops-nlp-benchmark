#!/usr/bin/env python
"""
Run record-level multi-label event tagging for the expanded 8,800 training design.

Train includes verified seed train rows plus 3,800 expanded agent-silver rows.
Dev/test remain verified reference rows. This is not event-span extraction.
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

from run_record_level_baselines import load_records, text_for_row


ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "splits"
OUTPUT_ROOT = ROOT / "outputs" / "baselines" / f"expanded_8800_reference_multilabel_{date.today().isoformat()}"

SPLIT_FILES = {
    "train": SPLIT_DIR / "expanded_8800_reference_eval_train_records_2026-06-04.csv",
    "dev": SPLIT_DIR / "expanded_8800_reference_eval_dev_records_2026-06-04.csv",
    "test": SPLIT_DIR / "expanded_8800_reference_eval_test_records_2026-06-04.csv",
}

MODEL_LABEL = "expanded_tfidf_word13_char36_ovr_linear_svc_multilabel"
TRAINING_DESIGN = "expanded_8800_weak_train_verified_dev_test"
RANDOM_STATE = 20260604

METRIC_FIELDS = [
    "training_design",
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
    "training_design",
    "task",
    "model",
    "split",
    "corpus_id",
    "acn",
    "gold_labels",
    "predicted_labels",
    "exact_match",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def event_labels(row: dict[str, str]) -> list[str]:
    labels = []
    primary = row.get("silver_primary_event_type", "").strip()
    if primary and primary != "not_relevant":
        labels.append(primary)
    secondary = row.get("silver_secondary_event_types", "").strip()
    if secondary:
        labels.extend(label.strip() for label in secondary.split(";") if label.strip() and label.strip() != "not_relevant")
    return list(dict.fromkeys(labels))


def relevant_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("silver_screening_status") == "include_ground_cabin_event" and event_labels(row)]


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
        "training_design": TRAINING_DESIGN,
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
                "training_design": TRAINING_DESIGN,
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
        f.write("# Expanded Multi-Label Per-Label Report\n\n")
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
            f.write(f"| `{label}` | {int(true_col.sum())} | {int(pred_col.sum())} | {precision:.6f} | {recall:.6f} | {f1:.6f} |\n")


def write_summary(metrics: list[dict[str, str]], label_counts: Counter, split_counts: dict[str, int], role_counts: Counter) -> None:
    with (OUTPUT_ROOT / "expanded_8800_reference_multilabel_summary.md").open("w", encoding="utf-8") as f:
        f.write("# Expanded 8,800 Reference-Evaluation Multi-Label Baseline Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("This is record-level multi-label event tagging from primary plus secondary labels. Train includes the expanded weak-label rows; dev/test remain verified reference rows. It is not event-span extraction.\n\n")
        f.write("## Relevant-Record Split Counts\n\n")
        for split, count in split_counts.items():
            f.write(f"- `{split}`: {count}\n")
        f.write("\n## Relevant Training Role Counts\n\n")
        for key, value in role_counts.most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Label Counts In Relevant Training Set\n\n")
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
        f.write("\n## Interpretation Boundary\n\n")
        f.write("- Use this as the expanded-training multi-label result against verified dev/test labels.\n")
        f.write("- Do not call it event-span or event-mention extraction.\n")


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

    model = OneVsRestClassifier(LinearSVC(class_weight="balanced", random_state=RANDOM_STATE, max_iter=7000))
    model.fit(x_train, y_train)

    metrics = []
    predictions = []
    for split in ["dev", "test"]:
        x_split = transform_texts(split_texts[split], word_vectorizer, char_vectorizer)
        y_true = mlb.transform(split_label_sets[split])
        y_pred = model.predict(x_split)
        metrics.append(metrics_row(split, y_true, y_pred, len(mlb.classes_)))
        predictions.extend(prediction_rows(split, split_rows[split], y_true, y_pred, mlb))
        write_label_report(OUTPUT_ROOT / f"expanded_per_label_report_{split}.md", y_true, y_pred, list(mlb.classes_))

    write_csv(OUTPUT_ROOT / "expanded_8800_reference_multilabel_metrics.csv", metrics, METRIC_FIELDS)
    write_csv(OUTPUT_ROOT / "expanded_8800_reference_multilabel_predictions.csv", predictions, PREDICTION_FIELDS)
    label_counts = Counter(label for labels in split_label_sets["train"] for label in labels)
    role_counts = Counter(row["expanded_corpus_role"] for row in split_rows["train"])
    config = {
        "created": date.today().isoformat(),
        "training_design": TRAINING_DESIGN,
        "model": MODEL_LABEL,
        "task": "record_level_event_multilabel_relevant_only",
        "labels": list(mlb.classes_),
        "split_files": {key: str(value) for key, value in SPLIT_FILES.items()},
        "split_counts": split_counts,
        "boundary": "Expanded weak-label train; verified dev/test; record-level multi-label only.",
    }
    (OUTPUT_ROOT / "expanded_8800_reference_multilabel_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    write_summary(metrics, label_counts, split_counts, role_counts)

    print(f"output_dir={OUTPUT_ROOT}")
    for row in metrics:
        print(row)


if __name__ == "__main__":
    main()
