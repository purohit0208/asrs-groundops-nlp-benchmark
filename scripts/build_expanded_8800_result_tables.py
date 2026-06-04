#!/usr/bin/env python
"""
Build result tables for the expanded 8,800 training design.

This script reads prediction CSV files only. It does not access raw ASRS text.
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
OUTPUT_ROOT = ROOT / "outputs" / "manuscript_tables" / f"expanded_8800_results_{date.today().isoformat()}"

EXPANDED_CLASSICAL = BASELINE_ROOT / "expanded_8800_reference_classical_2026-06-04" / "expanded_8800_reference_classical_predictions.csv"
SUPERVISED_MINILM = BASELINE_ROOT / "supervised_minilm_2026-06-03" / "supervised_minilm_baseline_predictions.csv"
HF_QWEN_TEST = BASELINE_ROOT / "hf_qwen_structured_test_2026-06-04" / "hf_qwen_structured_predictions.csv"
EXPANDED_MULTILABEL = BASELINE_ROOT / "expanded_8800_reference_multilabel_2026-06-04" / "expanded_8800_reference_multilabel_predictions.csv"
ORIGINAL_MULTILABEL = BASELINE_ROOT / "record_multilabel_2026-06-03" / "record_multilabel_event_baseline_predictions.csv"

BOOTSTRAP_SAMPLES = 1000
SEED = 20260604


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


def expanded_classical_rows() -> list[dict[str, str]]:
    output = []
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(EXPANDED_CLASSICAL):
        if row["split"] == "test":
            grouped[(row["task"], row["model"])].append(row)
    for (task, model), rows in grouped.items():
        metrics = bootstrap_single([r["gold_label"] for r in rows], [r["predicted_label"] for r in rows])
        output.append(
            {
                "training_design": "expanded_8800_weak_train_verified_test",
                "task": task,
                "model": model,
                "split": "test",
                "n": str(len(rows)),
                "validity_scope": "all_test_rows",
                **metrics,
            }
        )
    return output


def supervised_minilm_rows() -> list[dict[str, str]]:
    output = []
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(SUPERVISED_MINILM):
        if row["split"] == "test":
            grouped[(row["task"], row["model"])].append(row)
    for (task, model), rows in grouped.items():
        metrics = bootstrap_single([r["gold_label"] for r in rows], [r["predicted_label"] for r in rows])
        output.append(
            {
                "training_design": "seed_5000_verified_train_local_cpu",
                "task": task,
                "model": model,
                "split": "test",
                "n": str(len(rows)),
                "validity_scope": "all_test_rows",
                **metrics,
            }
        )
    return output


def hf_qwen_rows() -> list[dict[str, str]]:
    rows = [row for row in read_csv(HF_QWEN_TEST) if row.get("schema_valid") == "true"]
    output = []
    for task, gold_field, pred_field in [
        ("screening_status", "gold_screening_status", "llm_screening_status"),
        ("primary_event_type", "gold_primary_event_type", "llm_primary_event_type"),
    ]:
        task_rows = [row for row in rows if row.get(pred_field)]
        metrics = bootstrap_single([r[gold_field] for r in task_rows], [r[pred_field] for r in task_rows])
        output.append(
            {
                "training_design": "zero_shot_remote_hf_verified_test",
                "task": task,
                "model": "hf_qwen2_5_7b_instruct_structured_zero_shot",
                "split": "test",
                "n": str(len(task_rows)),
                "validity_scope": "schema_valid_rows_only",
                **metrics,
            }
        )
    return output


def label_set(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def subset_accuracy(y_true, y_pred) -> float:
    return float(((y_true != y_pred).sum(axis=1) == 0).mean())


def bootstrap_multilabel(rows: list[dict[str, str]], training_design: str) -> dict[str, str]:
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

    micro = f1_score(y_true, y_pred, average="micro", zero_division=0)
    macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    samples = f1_score(y_true, y_pred, average="samples", zero_division=0)
    subset = subset_accuracy(y_true, y_pred)
    jaccard = jaccard_score(y_true, y_pred, average="samples", zero_division=0)
    hamming = hamming_loss(y_true, y_pred)
    return {
        "training_design": training_design,
        "task": "record_level_event_multilabel_relevant_only",
        "model": rows[0]["model"] if rows else "",
        "split": "test",
        "n": str(n),
        "label_count": str(len(labels)),
        "micro_f1": f"{micro:.6f}",
        "micro_f1_ci": format_ci(micro, *ci(micro_values)),
        "macro_f1": f"{macro:.6f}",
        "macro_f1_ci": format_ci(macro, *ci(macro_values)),
        "samples_f1": f"{samples:.6f}",
        "samples_f1_ci": format_ci(samples, *ci(samples_values)),
        "subset_accuracy": f"{subset:.6f}",
        "subset_accuracy_ci": format_ci(subset, *ci(subset_values)),
        "samples_jaccard": f"{jaccard:.6f}",
        "samples_jaccard_ci": format_ci(jaccard, *ci(jaccard_values)),
        "hamming_loss": f"{hamming:.6f}",
        "hamming_loss_ci": format_ci(hamming, *ci(hamming_values)),
    }


def model_family(model: str) -> str:
    if "majority" in model:
        return "Majority"
    if "qwen" in model:
        return "Remote Qwen structured output"
    if "supervised_minilm" in model:
        return "Supervised MiniLM"
    if "logreg" in model:
        return "TF-IDF logistic regression"
    if "linear_svc" in model or "calibrated_svc" in model:
        return "TF-IDF LinearSVC"
    return model


def write_markdown(single_rows: list[dict[str, str]], multilabel_rows: list[dict[str, str]]) -> None:
    path = OUTPUT_ROOT / "expanded_8800_results_with_ci.md"
    with path.open("w", encoding="utf-8") as f:
        f.write("# Expanded 8,800 Result Tables With Bootstrap Confidence Intervals\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("These tables are computed from prediction CSV files only. They do not access raw ASRS narrative text. The expanded design uses 7,299 training rows, with the 3,800 expanded agent-silver rows added only to train; dev/test remain the verified reference rows.\n\n")
        for task in ["screening_status", "primary_event_type"]:
            f.write(f"## {task}\n\n")
            f.write("| model family | training design | model | n | validity scope | accuracy | macro F1 | weighted F1 |\n")
            f.write("|---|---|---|---:|---|---:|---:|---:|\n")
            rows = [row for row in single_rows if row["task"] == task]
            rows.sort(key=lambda row: float(row["macro_f1"]), reverse=True)
            for row in rows:
                f.write(
                    f"| {model_family(row['model'])} | `{row['training_design']}` | `{row['model']}` | {row['n']} | `{row['validity_scope']}` | {row['accuracy_ci']} | {row['macro_f1_ci']} | {row['weighted_f1_ci']} |\n"
                )
            f.write("\n")

        f.write("## record_level_event_multilabel_relevant_only\n\n")
        f.write("| training design | model | n | labels | micro F1 | macro F1 | samples F1 | subset accuracy | samples Jaccard | hamming loss |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in multilabel_rows:
            f.write(
                f"| `{row['training_design']}` | `{row['model']}` | {row['n']} | {row['label_count']} | {row['micro_f1_ci']} | {row['macro_f1_ci']} | {row['samples_f1_ci']} | {row['subset_accuracy_ci']} | {row['samples_jaccard_ci']} | {row['hamming_loss_ci']} |\n"
            )
        f.write("\n## Interpretation Notes\n\n")
        f.write("- The main expanded-training gain is on primary-event classification and multi-label event tagging.\n")
        f.write("- The zero-shot Qwen 7B baseline produced mostly valid JSON, but it underperformed local TF-IDF models; present it as a bounded negative/diagnostic LLM baseline, not the main result.\n")
        f.write("- The earlier supervised MiniLM remains useful for screening-status comparison, but it was trained on the 5,000-row seed train split because the local environment has CPU-only PyTorch.\n")
        f.write("- Multi-label results are record-level primary-plus-secondary label tagging, not event-span extraction.\n")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    single_rows = expanded_classical_rows() + supervised_minilm_rows() + hf_qwen_rows()
    single_fields = [
        "training_design",
        "task",
        "model",
        "split",
        "n",
        "validity_scope",
        "accuracy",
        "accuracy_ci",
        "macro_f1",
        "macro_f1_ci",
        "weighted_f1",
        "weighted_f1_ci",
    ]
    write_csv(OUTPUT_ROOT / "expanded_single_label_test_results_with_ci.csv", single_rows, single_fields)

    multilabel_rows = []
    original_rows = [row for row in read_csv(ORIGINAL_MULTILABEL) if row["split"] == "test"]
    if original_rows:
        multilabel_rows.append(bootstrap_multilabel(original_rows, "seed_5000_verified_train"))
    expanded_rows = [row for row in read_csv(EXPANDED_MULTILABEL) if row["split"] == "test"]
    if expanded_rows:
        multilabel_rows.append(bootstrap_multilabel(expanded_rows, "expanded_8800_weak_train_verified_test"))
    multilabel_fields = list(multilabel_rows[0].keys()) if multilabel_rows else []
    if multilabel_rows:
        write_csv(OUTPUT_ROOT / "expanded_multilabel_test_results_with_ci.csv", multilabel_rows, multilabel_fields)

    write_markdown(single_rows, multilabel_rows)
    print(f"output_dir={OUTPUT_ROOT}")
    print(f"single_label_rows={len(single_rows)}")
    print(f"multilabel_rows={len(multilabel_rows)}")


if __name__ == "__main__":
    main()
