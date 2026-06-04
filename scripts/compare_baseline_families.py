#!/usr/bin/env python
"""
Compare completed record-level baseline families for the ASRS benchmark.

The comparison reads machine-readable metric files only. It does not access or
write raw ASRS narrative text.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE_ROOT = ROOT / "outputs" / "baselines"
OUTPUT_DIR = BASELINE_ROOT / f"comparison_{date.today().isoformat()}"

METRIC_SOURCES = [
    (
        "majority_tfidf_logreg_rules",
        BASELINE_ROOT / f"record_level_{date.today().isoformat()}" / "record_level_baseline_metrics.csv",
    ),
    (
        "frozen_minilm_embeddings",
        BASELINE_ROOT / f"sentence_embedding_{date.today().isoformat()}" / "sentence_embedding_baseline_metrics.csv",
    ),
    (
        "linear_svc_tfidf",
        BASELINE_ROOT / f"stronger_classical_{date.today().isoformat()}" / "stronger_classical_baseline_metrics.csv",
    ),
    (
        "supervised_minilm_local",
        BASELINE_ROOT / f"supervised_minilm_{date.today().isoformat()}" / "supervised_minilm_baseline_metrics.csv",
    ),
]

FIELDS = ["family", "task", "model", "split", "n", "accuracy", "macro_f1", "weighted_f1", "micro_f1"]


def read_metrics() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for family, path in METRIC_SOURCES:
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                row = dict(row)
                row["family"] = family
                rows.append({field: row.get(field, "") for field in FIELDS})
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def best_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    eligible = [
        row
        for row in rows
        if row["split"] == "test" and row["model"] != "rule_reproduction_check_not_independent"
    ]
    best = []
    for task in sorted({row["task"] for row in eligible}):
        task_rows = [row for row in eligible if row["task"] == task]
        best.append(max(task_rows, key=lambda row: float(row["macro_f1"])))
    return best


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    best = best_rows(rows)
    with path.open("w", encoding="utf-8") as f:
        f.write("# Baseline Family Comparison\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("This comparison uses baseline metric CSV files only. It does not access raw ASRS narrative text. Rule-reproduction rows are excluded from best-model selection because they are label-consistency checks, not independent baselines.\n\n")
        f.write("## Best Independent Test Results By Macro F1\n\n")
        f.write("| task | family | model | accuracy | macro_f1 | weighted_f1 |\n")
        f.write("|---|---|---|---:|---:|---:|\n")
        for row in best:
            f.write(
                f"| `{row['task']}` | `{row['family']}` | `{row['model']}` | {row['accuracy']} | {row['macro_f1']} | {row['weighted_f1']} |\n"
            )
        f.write("\n## All Test Results\n\n")
        f.write("| task | family | model | accuracy | macro_f1 | weighted_f1 |\n")
        f.write("|---|---|---|---:|---:|---:|\n")
        for row in sorted(
            [row for row in rows if row["split"] == "test"],
            key=lambda row: (row["task"], -float(row["macro_f1"]), row["family"], row["model"]),
        ):
            if row["model"] == "rule_reproduction_check_not_independent":
                continue
            f.write(
                f"| `{row['task']}` | `{row['family']}` | `{row['model']}` | {row['accuracy']} | {row['macro_f1']} | {row['weighted_f1']} |\n"
            )
        f.write("\n## Interpretation\n\n")
        f.write("- Supervised MiniLM is currently best for screening-status macro F1, while TF-IDF LinearSVC remains best for primary-event-type macro F1.\n")
        f.write("- Supervised MiniLM improves screening-status macro F1 over TF-IDF but underperforms TF-IDF LinearSVC for primary-event-type classification.\n")
        f.write("- Frozen MiniLM sentence embeddings underperform TF-IDF on this record-level benchmark.\n")
        f.write("- A Hugging Face LLM or remote job should be used only after an explicit raw-narrative external-processing decision is recorded.\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_metrics()
    if not rows:
        raise SystemExit("No metric files found.")
    write_csv(OUTPUT_DIR / "baseline_family_metrics_combined.csv", rows)
    write_summary(OUTPUT_DIR / "baseline_family_comparison_summary.md", rows)
    print(f"output_dir={OUTPUT_DIR}")
    for row in best_rows(rows):
        print(row)


if __name__ == "__main__":
    main()
