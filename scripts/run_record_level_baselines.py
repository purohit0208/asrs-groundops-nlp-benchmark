#!/usr/bin/env python
"""
Run first record-level baselines for the ASRS GroundOps verified corpus.

Outputs do not include full raw ASRS narrative text. Raw text is loaded locally
from the private raw JSON files by ACN and discarded after vectorization.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from pilot_prescreen import classify, record_text


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "asrs_api"
SPLIT_DIR = ROOT / "data" / "splits"
OUTPUT_ROOT = ROOT / "outputs" / "baselines" / f"record_level_{date.today().isoformat()}"

RAW_FILES = [
    RAW_DIR / "Q02_details_2026-06-02.json",
    RAW_DIR / "Q04_details_2026-06-02.json",
    RAW_DIR / "Q09_details_2026-06-03.json",
    RAW_DIR / "Q10_details_2026-06-03.json",
    RAW_DIR / "Q11_details_2026-06-03.json",
    RAW_DIR / "Q12_details_2026-06-03.json",
]

SPLIT_FILES = {
    "train": SPLIT_DIR / "train_records_2026-06-04.csv",
    "dev": SPLIT_DIR / "dev_records_2026-06-04.csv",
    "test": SPLIT_DIR / "test_records_2026-06-04.csv",
}

TASKS = {
    "screening_status": "silver_screening_status",
    "primary_event_type": "silver_primary_event_type",
}

PREDICTION_FIELDS = [
    "task",
    "model",
    "split",
    "corpus_id",
    "acn",
    "gold_label",
    "predicted_label",
    "correct",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_records() -> dict[str, dict]:
    records: dict[str, dict] = {}
    for path in RAW_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for record in data:
            records[str(record.get("acn"))] = record
    return records


def text_for_row(row: dict[str, str], records: dict[str, dict]) -> str:
    record = records[row["acn"]]
    synopsis, narrative, all_text = record_text(record)
    return all_text


def build_dataset(rows: list[dict[str, str]], records: dict[str, dict], label_field: str) -> tuple[list[str], list[str]]:
    texts = []
    labels = []
    for row in rows:
        texts.append(text_for_row(row, records))
        labels.append(row[label_field])
    return texts, labels


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


def rule_reproduction_predictions(task: str, rows: list[dict[str, str]], records: dict[str, dict]) -> list[str]:
    predictions = []
    for row in rows:
        record = records[row["acn"]]
        synopsis, narrative, all_text = record_text(record)
        predicted = classify(row["query_id"], synopsis, narrative, all_text)
        if task == "screening_status":
            predictions.append(predicted["screening_status"])
        elif task == "primary_event_type":
            predictions.append(predicted["primary_candidate_event_type"])
        else:
            raise ValueError(task)
    return predictions


def run_task(task: str, label_field: str, split_rows: dict[str, list[dict[str, str]]], records: dict[str, dict]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    x_train, y_train = build_dataset(split_rows["train"], records, label_field)
    split_texts = {}
    split_labels = {}
    for split, rows in split_rows.items():
        split_texts[split], split_labels[split] = build_dataset(rows, records, label_field)

    models = {
        "majority": DummyClassifier(strategy="most_frequent"),
        "tfidf_word12_logreg_balanced": Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        lowercase=True,
                        strip_accents="unicode",
                        ngram_range=(1, 2),
                        min_df=2,
                        max_df=0.95,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        solver="liblinear",
                        random_state=20260603,
                    ),
                ),
            ]
        ),
        "tfidf_char35_logreg_balanced": Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        lowercase=True,
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        min_df=2,
                        max_df=0.95,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        solver="liblinear",
                        random_state=20260603,
                    ),
                ),
            ]
        ),
    }

    metrics = []
    predictions = []

    for model_name, model in models.items():
        model.fit(x_train, y_train)
        for split in ["dev", "test"]:
            y_true = split_labels[split]
            y_pred = list(model.predict(split_texts[split]))
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

    # This reproduces the label-generation rule and is not an independent ML baseline.
    for split in ["dev", "test"]:
        y_true = split_labels[split]
        y_pred = rule_reproduction_predictions(task, split_rows[split], records)
        model_name = "rule_reproduction_check_not_independent"
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
    summary_path = OUTPUT_ROOT / "record_level_baseline_summary.md"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Record-Level Baseline Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("These are first record-level baselines for the author-verified ASRS label corpus with local consistency-audit support. Full raw ASRS narratives are loaded locally from raw JSON and are not written to output files.\n\n")
        f.write("The `rule_reproduction_check_not_independent` rows reproduce the rule family used to draft labels. They are a consistency check, not an independent model baseline.\n\n")
        f.write("## Split Counts\n\n")
        for split in ["train", "dev", "test"]:
            f.write(f"- `{split}`: {len(split_rows[split])}\n")
        f.write("\n## Metrics\n\n")
        f.write("| task | model | split | n | accuracy | macro_f1 | weighted_f1 | micro_f1 |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|\n")
        for row in metrics:
            f.write(
                f"| `{row['task']}` | `{row['model']}` | `{row['split']}` | {row['n']} | {row['accuracy']} | {row['macro_f1']} | {row['weighted_f1']} | {row['micro_f1']} |\n"
            )

        f.write("\n## Interpretation Rules\n\n")
        f.write("- Prefer TF-IDF results over the rule-reproduction check when discussing independent baselines.\n")
        f.write("- Treat record-level primary event-type metrics as classification against reference labels, not full event-mention extraction.\n")
        f.write("- Do not use these results to infer ASRS event prevalence or real-world operational frequency.\n")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    records = load_records()
    split_rows = {split: read_csv(path) for split, path in SPLIT_FILES.items()}

    missing = sorted(
        {
            row["acn"]
            for rows in split_rows.values()
            for row in rows
            if row["acn"] not in records
        }
    )
    if missing:
        raise RuntimeError(f"Missing raw records for {len(missing)} ACNs: {missing[:10]}")

    all_metrics = []
    all_predictions = []
    for task, label_field in TASKS.items():
        metrics, predictions = run_task(task, label_field, split_rows, records)
        all_metrics.extend(metrics)
        all_predictions.extend(predictions)

    metrics_fields = ["task", "model", "split", "n", "accuracy", "macro_f1", "weighted_f1", "micro_f1"]
    write_csv(OUTPUT_ROOT / "record_level_baseline_metrics.csv", all_metrics, metrics_fields)
    write_csv(OUTPUT_ROOT / "record_level_baseline_predictions.csv", all_predictions, PREDICTION_FIELDS)

    config = {
        "created": date.today().isoformat(),
        "tasks": TASKS,
        "split_files": {key: str(value) for key, value in SPLIT_FILES.items()},
        "raw_files": [str(path) for path in RAW_FILES],
        "models": [
            "majority",
            "tfidf_word12_logreg_balanced",
            "tfidf_char35_logreg_balanced",
            "rule_reproduction_check_not_independent",
        ],
        "boundary": "Raw ASRS text is loaded locally and not written to outputs.",
    }
    (OUTPUT_ROOT / "baseline_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    write_summary(all_metrics, split_rows)

    print(f"output_dir={OUTPUT_ROOT}")
    print(f"metrics={OUTPUT_ROOT / 'record_level_baseline_metrics.csv'}")
    print(f"summary={OUTPUT_ROOT / 'record_level_baseline_summary.md'}")
    for row in all_metrics:
        if row["split"] == "test":
            print(row)


if __name__ == "__main__":
    main()
