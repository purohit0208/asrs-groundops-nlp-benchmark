#!/usr/bin/env python
"""
Create agent-generated silver labels for the 5,000-record ASRS corpus.

These labels are not human verified and must not be called human gold labels.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

from pilot_prescreen import classify, record_text


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "asrs_api"
MANIFEST_DIR = ROOT / "data" / "manifests"

RAW_FILES = [
    RAW_DIR / "Q02_details_2026-06-02.json",
    RAW_DIR / "Q04_details_2026-06-02.json",
    RAW_DIR / "Q09_details_2026-06-03.json",
    RAW_DIR / "Q10_details_2026-06-03.json",
    RAW_DIR / "Q11_details_2026-06-03.json",
    RAW_DIR / "Q12_details_2026-06-03.json",
]

OUTPUT_FIELDS = [
    "corpus_id",
    "candidate_id",
    "acn",
    "query_id",
    "silver_screening_status",
    "silver_primary_event_type",
    "silver_secondary_event_types",
    "silver_multi_event_flag",
    "ground_phase_evidence",
    "cabin_or_service_evidence",
    "reason_for_exclusion",
    "labeler",
    "label_date",
    "verification_status",
    "notes",
]


def load_records() -> dict[str, dict]:
    records: dict[str, dict] = {}
    for path in RAW_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for record in data:
            records[str(record.get("acn"))] = record
    return records


def main() -> None:
    records = load_records()
    manifest_path = MANIFEST_DIR / f"silver_corpus_5000_manifest_{date.today().isoformat()}.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    rows = list(csv.DictReader(manifest_path.open(encoding="utf-8")))

    output_rows = []
    for row in rows:
        acn = row["acn"]
        record = records.get(acn)
        if not record:
            prediction = {
                "screening_status": "uncertain_needs_review",
                "primary_candidate_event_type": "not_relevant",
                "secondary_candidate_event_types": "",
                "multi_event_flag": "false",
                "ground_phase_evidence": "",
                "cabin_or_service_evidence": "",
                "reason_for_exclusion": "raw_record_not_found",
                "notes": "Raw record not found in local Q02/Q04/Q09/Q10/Q11/Q12 JSON.",
            }
        else:
            synopsis, narrative, all_text = record_text(record)
            prediction = classify(row["query_id"], synopsis, narrative, all_text)

        output_rows.append(
            {
                "corpus_id": row["corpus_id"],
                "candidate_id": row["candidate_id"],
                "acn": acn,
                "query_id": row["query_id"],
                "silver_screening_status": prediction["screening_status"],
                "silver_primary_event_type": prediction["primary_candidate_event_type"],
                "silver_secondary_event_types": prediction["secondary_candidate_event_types"],
                "silver_multi_event_flag": prediction["multi_event_flag"],
                "ground_phase_evidence": prediction["ground_phase_evidence"],
                "cabin_or_service_evidence": prediction["cabin_or_service_evidence"],
                "reason_for_exclusion": prediction["reason_for_exclusion"],
                "labeler": "agent_silver_v0_2",
                "label_date": date.today().isoformat(),
                "verification_status": "not_human_verified",
                "notes": "Agent-generated silver label; do not describe as human gold-standard annotation.",
            }
        )

    label_path = MANIFEST_DIR / f"silver_corpus_5000_labels_{date.today().isoformat()}.csv"
    with label_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    status_counts = Counter(row["silver_screening_status"] for row in output_rows)
    type_counts = Counter(row["silver_primary_event_type"] for row in output_rows)
    query_counts = Counter()
    for row in output_rows:
        for query_id in row["query_id"].split(";"):
            query_counts[query_id] += 1

    summary_path = MANIFEST_DIR / f"silver_corpus_5000_label_summary_{date.today().isoformat()}.md"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Silver Corpus 5000 Label Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("These are agent-generated silver labels. They are not human verified and must not be described as human gold-standard labels.\n\n")
        f.write("## Screening Status Counts\n\n")
        for key, value in status_counts.most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Primary Event-Type Counts\n\n")
        for key, value in type_counts.most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Non-Exclusive Query Coverage\n\n")
        for key, value in query_counts.most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Recommended Manuscript Boundary\n\n")
        f.write("Use these labels as a silver-standard benchmark or AI-assisted weak-label corpus. Do not claim human annotation unless a separate author/human verification step is completed and logged.\n")

    print(f"labels={label_path}")
    print(f"summary={summary_path}")
    print("status_counts", dict(status_counts))
    print("type_counts", dict(type_counts))


if __name__ == "__main__":
    main()
