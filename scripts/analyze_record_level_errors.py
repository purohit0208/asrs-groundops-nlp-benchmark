#!/usr/bin/env python
"""
Analyze record-level baseline errors without exporting full ASRS narratives.

The output focuses on confusion pairs, class-level difficulty, multi-event
structure, query families, and concise existing evidence snippets.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "splits"
BASELINE_DIR = ROOT / "outputs" / "baselines" / "record_level_2026-06-04"
ERROR_DIR = BASELINE_DIR / "error_analysis"

PREDICTIONS_FILE = BASELINE_DIR / "record_level_baseline_predictions.csv"
SPLIT_ASSIGNMENTS_FILE = SPLIT_DIR / "record_level_split_assignments_2026-06-04.csv"

PRIMARY_MODELS = [
    "tfidf_word12_logreg_balanced",
    "tfidf_char35_logreg_balanced",
]

ERROR_FIELDS = [
    "task",
    "model",
    "split",
    "corpus_id",
    "acn",
    "gold_label",
    "predicted_label",
    "multi_event_structure_flag",
    "query_id",
    "ground_phase_evidence",
    "cabin_or_service_evidence",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def safe_snippet(value: str, limit: int = 180) -> str:
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def enrich_errors(predictions: list[dict[str, str]], split_rows: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    errors = []
    for row in predictions:
        if row["correct"] == "true":
            continue
        if row["model"] not in PRIMARY_MODELS:
            continue
        if row["split"] not in {"dev", "test"}:
            continue
        meta = split_rows[row["corpus_id"]]
        errors.append(
            {
                "task": row["task"],
                "model": row["model"],
                "split": row["split"],
                "corpus_id": row["corpus_id"],
                "acn": row["acn"],
                "gold_label": row["gold_label"],
                "predicted_label": row["predicted_label"],
                "multi_event_structure_flag": meta["multi_event_structure_flag"],
                "query_id": meta["query_id"],
                "ground_phase_evidence": safe_snippet(meta["ground_phase_evidence"]),
                "cabin_or_service_evidence": safe_snippet(meta["cabin_or_service_evidence"]),
            }
        )
    return errors


def counter_rows(counter: Counter, fields: list[str]) -> list[dict[str, str]]:
    rows = []
    for key, count in counter.most_common():
        if not isinstance(key, tuple):
            key = (key,)
        row = {field: str(value) for field, value in zip(fields, key)}
        row["count"] = str(count)
        rows.append(row)
    return rows


def write_markdown_summary(path: Path, errors: list[dict[str, str]]) -> None:
    grouped = defaultdict(list)
    for row in errors:
        grouped[(row["task"], row["model"], row["split"])].append(row)

    with path.open("w", encoding="utf-8") as f:
        f.write("# Record-Level Baseline Error Analysis\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("This analysis uses prediction outputs and split metadata only. It does not export full ASRS narratives. Evidence snippets are the short fields already present in the split files.\n\n")
        f.write("Rule-reproduction rows are excluded because they are label-consistency checks, not independent baselines.\n\n")

        f.write("## Error Counts By Task, Model, And Split\n\n")
        f.write("| task | model | split | errors |\n")
        f.write("|---|---|---:|---:|\n")
        for key in sorted(grouped):
            task, model, split = key
            f.write(f"| `{task}` | `{model}` | `{split}` | {len(grouped[key])} |\n")

        f.write("\n## Main Findings\n\n")
        f.write("- Screening-status errors are dominated by confusion between `include_ground_cabin_event` and `exclude_not_ground_or_cabin`; the rare `uncertain_needs_review` class is not learned by TF-IDF because only two test rows exist.\n")
        f.write("- Primary-event-type classification is much harder than screening. Stronger classes include `hazmat_mobility_device`, `pushback_towing_chocks`, and `other_ground_operation`; weak classes include `jetway_or_gate_infrastructure`, `dispatch_or_coordination`, `cabin_service`, and small support classes.\n")
        f.write("- Many errors occur in rows flagged as possible multi-event records, so event-level conversion or multi-label treatment is likely needed before claiming fine-grained extraction performance.\n")

        f.write("\n## Top Confusions\n\n")
        for task in ["screening_status", "primary_event_type"]:
            f.write(f"### `{task}`\n\n")
            task_errors = [row for row in errors if row["task"] == task and row["split"] == "test"]
            confusion = Counter((row["gold_label"], row["predicted_label"]) for row in task_errors)
            for (gold, predicted), count in confusion.most_common(12):
                f.write(f"- `{gold}` -> `{predicted}`: {count}\n")
            f.write("\n")

        f.write("## Recommended Next Model Step\n\n")
        f.write("Run an encoder-transformer or sentence-embedding baseline next. The primary-event-type TF-IDF ceiling is only about 0.47 macro F1 on test, and the confusion profile suggests contextual language representation may help with broad classes such as maintenance readiness, baggage/cargo, and ramp/ground-handling. LLM structured extraction should wait until after one stronger non-LLM baseline is available.\n")


def main() -> None:
    ERROR_DIR.mkdir(parents=True, exist_ok=True)
    predictions = read_csv(PREDICTIONS_FILE)
    split_rows = {row["corpus_id"]: row for row in read_csv(SPLIT_ASSIGNMENTS_FILE)}
    errors = enrich_errors(predictions, split_rows)

    write_csv(ERROR_DIR / "tfidf_error_examples.csv", errors, ERROR_FIELDS)

    confusion_counter = Counter(
        (row["task"], row["model"], row["split"], row["gold_label"], row["predicted_label"])
        for row in errors
    )
    write_csv(
        ERROR_DIR / "tfidf_confusion_pairs.csv",
        counter_rows(confusion_counter, ["task", "model", "split", "gold_label", "predicted_label"]),
        ["task", "model", "split", "gold_label", "predicted_label", "count"],
    )

    multi_counter = Counter(
        (row["task"], row["model"], row["split"], row["multi_event_structure_flag"])
        for row in errors
    )
    write_csv(
        ERROR_DIR / "tfidf_errors_by_multi_event_flag.csv",
        counter_rows(multi_counter, ["task", "model", "split", "multi_event_structure_flag"]),
        ["task", "model", "split", "multi_event_structure_flag", "count"],
    )

    query_counter = Counter()
    for row in errors:
        for query_id in row["query_id"].split(";"):
            query_counter[(row["task"], row["model"], row["split"], query_id)] += 1
    write_csv(
        ERROR_DIR / "tfidf_errors_by_query_family.csv",
        counter_rows(query_counter, ["task", "model", "split", "query_id"]),
        ["task", "model", "split", "query_id", "count"],
    )

    write_markdown_summary(ERROR_DIR / "record_level_error_analysis_summary.md", errors)

    print(f"error_dir={ERROR_DIR}")
    print(f"errors={len(errors)}")
    print(f"summary={ERROR_DIR / 'record_level_error_analysis_summary.md'}")


if __name__ == "__main__":
    main()
