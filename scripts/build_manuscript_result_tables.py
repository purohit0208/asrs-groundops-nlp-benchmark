#!/usr/bin/env python
"""
Build manuscript-ready result tables with bootstrap confidence intervals.

This script reads prediction CSV files only. It does not access raw ASRS
narrative text.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, hamming_loss, jaccard_score
from sklearn.preprocessing import MultiLabelBinarizer


ROOT = Path(__file__).resolve().parents[1]
BASELINE_ROOT = ROOT / "outputs" / "baselines"
OUTPUT_ROOT = ROOT / "outputs" / "manuscript_tables" / f"results_{date.today().isoformat()}"

SINGLE_LABEL_SOURCES = [
    BASELINE_ROOT / f"record_level_{date.today().isoformat()}" / "record_level_baseline_predictions.csv",
    BASELINE_ROOT / f"stronger_classical_{date.today().isoformat()}" / "stronger_classical_baseline_predictions.csv",
    BASELINE_ROOT / f"sentence_embedding_{date.today().isoformat()}" / "sentence_embedding_baseline_predictions.csv",
    BASELINE_ROOT / f"supervised_minilm_{date.today().isoformat()}" / "supervised_minilm_baseline_predictions.csv",
]

MULTILABEL_SOURCE = BASELINE_ROOT / f"record_multilabel_{date.today().isoformat()}" / "record_multilabel_event_baseline_predictions.csv"

BOOTSTRAP_SAMPLES = 1000
SEED = 20260603


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ci(values: list[float]) -> tuple[float, float]:
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def format_ci(value: float, lower: float, upper: float) -> str:
    return f"{value:.3f} [{lower:.3f}, {upper:.3f}]"


def bootstrap_single(y_true: list[str], y_pred: list[str]) -> dict[str, str]:
    rng = np.random.default_rng(SEED)
    n = len(y_true)
    true = np.array(y_true)
    pred = np.array(y_pred)
    accuracy_values = []
    macro_values = []
    weighted_values = []
    for _ in range(BOOTSTRAP_SAMPLES):
        index = rng.integers(0, n, n)
        yt = true[index]
        yp = pred[index]
        accuracy_values.append(accuracy_score(yt, yp))
        macro_values.append(f1_score(yt, yp, average="macro", zero_division=0))
        weighted_values.append(f1_score(yt, yp, average="weighted", zero_division=0))

    accuracy = accuracy_score(true, pred)
    macro = f1_score(true, pred, average="macro", zero_division=0)
    weighted = f1_score(true, pred, average="weighted", zero_division=0)
    acc_low, acc_high = ci(accuracy_values)
    macro_low, macro_high = ci(macro_values)
    weighted_low, weighted_high = ci(weighted_values)
    return {
        "accuracy": f"{accuracy:.6f}",
        "accuracy_ci": format_ci(accuracy, acc_low, acc_high),
        "macro_f1": f"{macro:.6f}",
        "macro_f1_ci": format_ci(macro, macro_low, macro_high),
        "weighted_f1": f"{weighted:.6f}",
        "weighted_f1_ci": format_ci(weighted, weighted_low, weighted_high),
    }


def build_single_label_tables() -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for source in SINGLE_LABEL_SOURCES:
        for row in read_csv(source):
            if row["split"] != "test":
                continue
            if row["model"] == "rule_reproduction_check_not_independent":
                continue
            grouped[(row["task"], row["model"], row["split"])].append(row)

    output = []
    for (task, model, split), rows in sorted(grouped.items()):
        y_true = [row["gold_label"] for row in rows]
        y_pred = [row["predicted_label"] for row in rows]
        metrics = bootstrap_single(y_true, y_pred)
        output.append(
            {
                "task": task,
                "model": model,
                "split": split,
                "n": str(len(rows)),
                **metrics,
            }
        )
    return output


def label_set(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def subset_accuracy(y_true, y_pred) -> float:
    return float(((y_true != y_pred).sum(axis=1) == 0).mean())


def bootstrap_multilabel(rows: list[dict[str, str]]) -> dict[str, str]:
    label_sets_true = [label_set(row["gold_labels"]) for row in rows]
    label_sets_pred = [label_set(row["predicted_labels"]) for row in rows]
    labels = sorted({label for labels_ in label_sets_true + label_sets_pred for label in labels_})
    mlb = MultiLabelBinarizer(classes=labels)
    y_true = mlb.fit_transform(label_sets_true)
    y_pred = mlb.transform(label_sets_pred)
    rng = np.random.default_rng(SEED)
    n = y_true.shape[0]

    micro_values = []
    macro_values = []
    samples_values = []
    subset_values = []
    jaccard_values = []
    hamming_values = []
    for _ in range(BOOTSTRAP_SAMPLES):
        index = rng.integers(0, n, n)
        yt = y_true[index]
        yp = y_pred[index]
        micro_values.append(f1_score(yt, yp, average="micro", zero_division=0))
        macro_values.append(f1_score(yt, yp, average="macro", zero_division=0))
        samples_values.append(f1_score(yt, yp, average="samples", zero_division=0))
        subset_values.append(subset_accuracy(yt, yp))
        jaccard_values.append(jaccard_score(yt, yp, average="samples", zero_division=0))
        hamming_values.append(hamming_loss(yt, yp))

    metrics = {
        "micro_f1": f1_score(y_true, y_pred, average="micro", zero_division=0),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "samples_f1": f1_score(y_true, y_pred, average="samples", zero_division=0),
        "subset_accuracy": subset_accuracy(y_true, y_pred),
        "samples_jaccard": jaccard_score(y_true, y_pred, average="samples", zero_division=0),
        "hamming_loss": hamming_loss(y_true, y_pred),
    }
    ci_values = {
        "micro_f1_ci": ci(micro_values),
        "macro_f1_ci": ci(macro_values),
        "samples_f1_ci": ci(samples_values),
        "subset_accuracy_ci": ci(subset_values),
        "samples_jaccard_ci": ci(jaccard_values),
        "hamming_loss_ci": ci(hamming_values),
    }
    return {
        "task": "record_level_event_multilabel_relevant_only",
        "model": rows[0]["model"] if rows else "",
        "split": "test",
        "n": str(n),
        "label_count": str(len(labels)),
        "micro_f1": f"{metrics['micro_f1']:.6f}",
        "micro_f1_ci": format_ci(metrics["micro_f1"], *ci_values["micro_f1_ci"]),
        "macro_f1": f"{metrics['macro_f1']:.6f}",
        "macro_f1_ci": format_ci(metrics["macro_f1"], *ci_values["macro_f1_ci"]),
        "samples_f1": f"{metrics['samples_f1']:.6f}",
        "samples_f1_ci": format_ci(metrics["samples_f1"], *ci_values["samples_f1_ci"]),
        "subset_accuracy": f"{metrics['subset_accuracy']:.6f}",
        "subset_accuracy_ci": format_ci(metrics["subset_accuracy"], *ci_values["subset_accuracy_ci"]),
        "samples_jaccard": f"{metrics['samples_jaccard']:.6f}",
        "samples_jaccard_ci": format_ci(metrics["samples_jaccard"], *ci_values["samples_jaccard_ci"]),
        "hamming_loss": f"{metrics['hamming_loss']:.6f}",
        "hamming_loss_ci": format_ci(metrics["hamming_loss"], *ci_values["hamming_loss_ci"]),
    }


def model_family(model: str) -> str:
    if model == "majority":
        return "Majority"
    if model.startswith("tfidf") and "logreg" in model:
        return "TF-IDF logistic regression"
    if model.startswith("tfidf") and ("linear_svc" in model or "calibrated_svc" in model):
        return "TF-IDF LinearSVC"
    if model.startswith("sbert"):
        return "Frozen MiniLM embeddings"
    if model.startswith("supervised_minilm"):
        return "Supervised MiniLM"
    return model


def write_markdown(single_rows: list[dict[str, str]], multilabel_row: dict[str, str]) -> None:
    path = OUTPUT_ROOT / "manuscript_results_with_ci.md"
    with path.open("w", encoding="utf-8") as f:
        f.write("# Manuscript Result Tables With Bootstrap Confidence Intervals\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("These tables are computed from prediction CSV files only. They do not access raw ASRS narrative text. Confidence intervals are percentile bootstrap intervals over test records using 1,000 resamples.\n\n")
        for task in ["screening_status", "primary_event_type"]:
            f.write(f"## {task}\n\n")
            f.write("| model family | model | n | accuracy | macro F1 | weighted F1 |\n")
            f.write("|---|---|---:|---:|---:|---:|\n")
            task_rows = [row for row in single_rows if row["task"] == task]
            task_rows.sort(key=lambda row: float(row["macro_f1"]), reverse=True)
            for row in task_rows:
                f.write(
                    f"| {model_family(row['model'])} | `{row['model']}` | {row['n']} | {row['accuracy_ci']} | {row['macro_f1_ci']} | {row['weighted_f1_ci']} |\n"
                )
            f.write("\n")

        f.write("## record_level_event_multilabel_relevant_only\n\n")
        f.write("| model | n | labels | micro F1 | macro F1 | samples F1 | subset accuracy | samples Jaccard | hamming loss |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        f.write(
            f"| `{multilabel_row['model']}` | {multilabel_row['n']} | {multilabel_row['label_count']} | {multilabel_row['micro_f1_ci']} | {multilabel_row['macro_f1_ci']} | {multilabel_row['samples_f1_ci']} | {multilabel_row['subset_accuracy_ci']} | {multilabel_row['samples_jaccard_ci']} | {multilabel_row['hamming_loss_ci']} |\n\n"
        )
        f.write("## Interpretation Notes\n\n")
        f.write("- Screening-status and primary-event-type are single-label record-level tasks.\n")
        f.write("- The multi-label task applies only to included records and uses primary-plus-secondary event labels.\n")
        f.write("- Multi-label results must not be described as event-span extraction.\n")
        f.write("- Rule-reproduction checks are excluded because they are label-consistency checks, not independent baselines.\n")
        f.write("- Screening-status macro-F1 intervals are unstable because the rare `uncertain_needs_review` class has very low test support; use per-class reports when discussing that task.\n")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    single_rows = build_single_label_tables()
    single_fields = [
        "task",
        "model",
        "split",
        "n",
        "accuracy",
        "accuracy_ci",
        "macro_f1",
        "macro_f1_ci",
        "weighted_f1",
        "weighted_f1_ci",
    ]
    write_csv(OUTPUT_ROOT / "single_label_test_results_with_ci.csv", single_rows, single_fields)

    multilabel_rows = [row for row in read_csv(MULTILABEL_SOURCE) if row["split"] == "test"]
    multilabel_row = bootstrap_multilabel(multilabel_rows)
    multilabel_fields = list(multilabel_row.keys())
    write_csv(OUTPUT_ROOT / "multilabel_test_results_with_ci.csv", [multilabel_row], multilabel_fields)
    write_markdown(single_rows, multilabel_row)

    print(f"output_dir={OUTPUT_ROOT}")
    print(f"single_label_rows={len(single_rows)}")
    print(multilabel_row)


if __name__ == "__main__":
    main()
