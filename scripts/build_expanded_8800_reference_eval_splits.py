#!/usr/bin/env python
"""
Build expanded 8,800 reference-evaluation splits.

Design:
- keep the original 5,000-row verified split assignments unchanged;
- add the 3,800 expanded agent-silver rows to train only;
- evaluate main models on the original verified dev/test rows.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from pilot_prescreen import record_text


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "asrs_api"
MANIFEST_DIR = ROOT / "data" / "manifests"
SPLIT_DIR = ROOT / "data" / "splits"

LABEL_FILE = MANIFEST_DIR / "expanded_corpus_8800_labels_2026-06-04.csv"
MANIFEST_FILE = MANIFEST_DIR / "expanded_corpus_8800_manifest_2026-06-04.csv"
SEED_SPLIT_FILE = SPLIT_DIR / "record_level_split_assignments_2026-06-04.csv"

RAW_FILES = [
    RAW_DIR / "Q02_details_2026-06-02.json",
    RAW_DIR / "Q04_details_2026-06-02.json",
    RAW_DIR / "Q09_details_2026-06-03.json",
    RAW_DIR / "Q10_details_2026-06-03.json",
    RAW_DIR / "Q11_details_2026-06-03.json",
    RAW_DIR / "Q12_details_2026-06-03.json",
]

SPLIT_FIELDS = [
    "split",
    "split_design",
    "corpus_id",
    "candidate_id",
    "acn",
    "query_id",
    "report_date_or_year",
    "silver_screening_status",
    "silver_primary_event_type",
    "silver_secondary_event_types",
    "multi_event_structure_flag",
    "ground_phase_evidence",
    "cabin_or_service_evidence",
    "reason_for_exclusion",
    "verification_status",
    "author_verification_status",
    "expanded_corpus_role",
    "expanded_label_provenance",
    "text_sha256",
    "text_char_count",
    "raw_text_included",
    "raw_export_file",
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


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().lower()


def text_hash_and_length(record: dict) -> tuple[str, int]:
    synopsis, narrative, all_text = record_text(record)
    normalized = normalize_text(all_text)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest, len(all_text)


def multi_event_structure_flag(value: str) -> str:
    if value == "needs_author_review":
        return "possible_multi_event_needs_event_level_policy"
    return "single_record_label"


def main() -> None:
    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    labels = read_csv(LABEL_FILE)
    manifests = read_csv(MANIFEST_FILE)
    seed_splits = read_csv(SEED_SPLIT_FILE)
    records = load_records()

    manifest_by_acn = {row["acn"]: row for row in manifests}
    seed_split_by_acn = {row["acn"]: row["split"] for row in seed_splits}

    output_rows: list[dict[str, str]] = []
    missing_raw: list[str] = []
    missing_seed_split: list[str] = []
    for row in labels:
        acn = row["acn"]
        record = records.get(acn)
        if not record:
            missing_raw.append(acn)
            text_sha256 = ""
            text_char_count = "0"
        else:
            text_sha256, char_count = text_hash_and_length(record)
            text_char_count = str(char_count)

        role = row["expanded_corpus_role"]
        if role == "seed_5000_author_verified_local_audit":
            split = seed_split_by_acn.get(acn)
            if not split:
                missing_seed_split.append(acn)
                split = "missing_seed_split"
        else:
            split = "train"

        manifest_row = manifest_by_acn.get(acn, {})
        output_rows.append(
            {
                "split": split,
                "split_design": "expanded_8800_weak_train_verified_dev_test",
                "corpus_id": row["corpus_id"],
                "candidate_id": row["candidate_id"],
                "acn": acn,
                "query_id": row["query_id"],
                "report_date_or_year": manifest_row.get("report_date_or_year", ""),
                "silver_screening_status": row["silver_screening_status"],
                "silver_primary_event_type": row["silver_primary_event_type"],
                "silver_secondary_event_types": row["silver_secondary_event_types"],
                "multi_event_structure_flag": multi_event_structure_flag(row["silver_multi_event_flag"]),
                "ground_phase_evidence": row["ground_phase_evidence"],
                "cabin_or_service_evidence": row["cabin_or_service_evidence"],
                "reason_for_exclusion": row["reason_for_exclusion"],
                "verification_status": row["verification_status"],
                "author_verification_status": row.get("author_verification_status", ""),
                "expanded_corpus_role": role,
                "expanded_label_provenance": row["expanded_label_provenance"],
                "text_sha256": text_sha256,
                "text_char_count": text_char_count,
                "raw_text_included": "false",
                "raw_export_file": manifest_row.get("raw_export_file", ""),
            }
        )

    if missing_raw:
        raise RuntimeError(f"Missing raw records for {len(missing_raw)} ACNs: {missing_raw[:10]}")
    if missing_seed_split:
        raise RuntimeError(f"Missing seed split for {len(missing_seed_split)} ACNs: {missing_seed_split[:10]}")

    assignment_path = SPLIT_DIR / f"expanded_8800_reference_eval_split_assignments_{date.today().isoformat()}.csv"
    write_csv(assignment_path, output_rows, SPLIT_FIELDS)

    split_rows = defaultdict(list)
    for row in output_rows:
        split_rows[row["split"]].append(row)

    for split in ["train", "dev", "test"]:
        write_csv(SPLIT_DIR / f"expanded_8800_reference_eval_{split}_records_{date.today().isoformat()}.csv", split_rows[split], SPLIT_FIELDS)

    split_counts = Counter(row["split"] for row in output_rows)
    role_by_split = defaultdict(Counter)
    status_by_split = defaultdict(Counter)
    type_by_split = defaultdict(Counter)
    provenance_by_split = defaultdict(Counter)
    text_hash_splits = defaultdict(set)
    for row in output_rows:
        split = row["split"]
        role_by_split[split][row["expanded_corpus_role"]] += 1
        status_by_split[split][row["silver_screening_status"]] += 1
        type_by_split[split][row["silver_primary_event_type"]] += 1
        provenance_by_split[split][row["expanded_label_provenance"]] += 1
        text_hash_splits[row["text_sha256"]].add(split)

    cross_split_hashes = {h: s for h, s in text_hash_splits.items() if len(s) > 1}
    duplicate_acns = [acn for acn, count in Counter(row["acn"] for row in output_rows).items() if count > 1]

    summary_path = SPLIT_DIR / f"expanded_8800_reference_eval_split_summary_{date.today().isoformat()}.md"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Expanded 8,800 Reference-Evaluation Split Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("The 3,800 expanded agent-silver rows are added to train only. Dev and test remain the original author-verified seed rows with local consistency-audit support.\n\n")
        f.write("## Split Counts\n\n")
        for split in ["train", "dev", "test"]:
            f.write(f"- `{split}`: {split_counts[split]}\n")
        f.write("\n## Leakage Checks\n\n")
        f.write(f"- Duplicate ACNs across corpus: {len(duplicate_acns)}\n")
        f.write(f"- Exact normalized text hashes appearing in more than one split: {len(cross_split_hashes)}\n")
        f.write("- Raw ASRS narrative text included in split CSVs: `false`\n")
        f.write("\n## Role Counts By Split\n\n")
        for split in ["train", "dev", "test"]:
            f.write(f"### `{split}`\n\n")
            for key, value in role_by_split[split].most_common():
                f.write(f"- `{key}`: {value}\n")
            f.write("\n")
        f.write("## Screening Status By Split\n\n")
        for split in ["train", "dev", "test"]:
            f.write(f"### `{split}`\n\n")
            for key, value in status_by_split[split].most_common():
                f.write(f"- `{key}`: {value}\n")
            f.write("\n")
        f.write("## Primary Event Type By Split\n\n")
        for split in ["train", "dev", "test"]:
            f.write(f"### `{split}`\n\n")
            for key, value in type_by_split[split].most_common():
                f.write(f"- `{key}`: {value}\n")
            f.write("\n")
        f.write("## Provenance By Split\n\n")
        for split in ["train", "dev", "test"]:
            f.write(f"### `{split}`\n\n")
            for key, value in provenance_by_split[split].most_common():
                f.write(f"- `{key}`: {value}\n")
            f.write("\n")

    print(f"assignments={assignment_path}")
    print(f"summary={summary_path}")
    print("split_counts", dict(split_counts))
    print("cross_split_hashes", len(cross_split_hashes))
    print("duplicate_acns", len(duplicate_acns))


if __name__ == "__main__":
    main()
