#!/usr/bin/env python
"""
Build leakage-safe record-level train/dev/test splits for the author-verified
GroundOps label corpus.

The split files do not include full raw ASRS narrative text. They include labels,
metadata, evidence snippets, and normalized text hashes so public release can
avoid redistributing raw narratives unless ASRS redistribution terms are cleared.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from pilot_prescreen import record_text


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "asrs_api"
MANIFEST_DIR = ROOT / "data" / "manifests"
SPLIT_DIR = ROOT / "data" / "splits"

LABEL_FILE = MANIFEST_DIR / "author_verified_single_reviewer_labels_5000_2026-06-03.csv"
MANIFEST_FILE = MANIFEST_DIR / "silver_corpus_5000_manifest_2026-06-03.csv"

RAW_FILES = [
    RAW_DIR / "Q02_details_2026-06-02.json",
    RAW_DIR / "Q04_details_2026-06-02.json",
    RAW_DIR / "Q09_details_2026-06-03.json",
    RAW_DIR / "Q10_details_2026-06-03.json",
    RAW_DIR / "Q11_details_2026-06-03.json",
    RAW_DIR / "Q12_details_2026-06-03.json",
]

SEED = 20260603
TARGET_RATIOS = {
    "train": 0.70,
    "dev": 0.15,
    "test": 0.15,
}

SPLIT_FIELDS = [
    "split",
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
    value = re.sub(r"\s+", " ", value or "")
    return value.strip().lower()


def text_hash_and_length(record: dict) -> tuple[str, int]:
    synopsis, narrative, all_text = record_text(record)
    normalized = normalize_text(all_text)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest, len(all_text)


def split_targets(count: int) -> dict[str, int]:
    train = round(count * TARGET_RATIOS["train"])
    dev = round(count * TARGET_RATIOS["dev"])
    test = count - train - dev
    return {"train": train, "dev": dev, "test": test}


def assign_stratified_groups(rows: list[dict[str, str]]) -> dict[str, str]:
    rng = random.Random(SEED)
    by_stratum: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        stratum = f"{row['silver_screening_status']}::{row['silver_primary_event_type']}"
        by_stratum[stratum][row["text_sha256"]].append(row)

    assignments: dict[str, str] = {}
    for stratum, groups in sorted(by_stratum.items()):
        group_items = list(groups.items())
        rng.shuffle(group_items)
        total = sum(len(group_rows) for _, group_rows in group_items)
        targets = split_targets(total)
        counts = Counter()

        for group_hash, group_rows in group_items:
            group_size = len(group_rows)
            deficits = {
                split: targets[split] - counts[split]
                for split in ["train", "dev", "test"]
            }
            split = max(deficits, key=lambda key: (deficits[key], TARGET_RATIOS[key]))
            if deficits[split] <= 0:
                split = min(counts, key=lambda key: counts[key] / max(targets[key], 1))
            for row in group_rows:
                assignments[row["corpus_id"]] = split
            counts[split] += group_size

    return assignments


def multi_event_structure_flag(value: str) -> str:
    if value == "needs_author_review":
        return "possible_multi_event_needs_event_level_policy"
    return "single_record_label"


def main() -> None:
    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    labels = read_csv(LABEL_FILE)
    manifest_rows = read_csv(MANIFEST_FILE)
    manifest_by_acn = {row["acn"]: row for row in manifest_rows}
    records = load_records()

    enriched_rows: list[dict[str, str]] = []
    missing_raw: list[str] = []
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

        manifest_row = manifest_by_acn.get(acn, {})
        enriched_rows.append(
            {
                "split": "",
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
                "text_sha256": text_sha256,
                "text_char_count": text_char_count,
                "raw_text_included": "false",
                "raw_export_file": manifest_row.get("raw_export_file", ""),
            }
        )

    if missing_raw:
        raise RuntimeError(f"Missing raw records for {len(missing_raw)} ACNs: {missing_raw[:10]}")

    assignments = assign_stratified_groups(enriched_rows)
    for row in enriched_rows:
        row["split"] = assignments[row["corpus_id"]]

    assignment_path = SPLIT_DIR / f"record_level_split_assignments_{date.today().isoformat()}.csv"
    write_csv(assignment_path, enriched_rows, SPLIT_FIELDS)

    split_rows = defaultdict(list)
    for row in enriched_rows:
        split_rows[row["split"]].append(row)

    for split in ["train", "dev", "test"]:
        split_path = SPLIT_DIR / f"{split}_records_{date.today().isoformat()}.csv"
        write_csv(split_path, split_rows[split], SPLIT_FIELDS)

    split_counts = Counter(row["split"] for row in enriched_rows)
    type_by_split = defaultdict(Counter)
    status_by_split = defaultdict(Counter)
    multi_by_split = defaultdict(Counter)
    query_by_split = defaultdict(Counter)
    text_hash_splits = defaultdict(set)

    for row in enriched_rows:
        split = row["split"]
        type_by_split[split][row["silver_primary_event_type"]] += 1
        status_by_split[split][row["silver_screening_status"]] += 1
        multi_by_split[split][row["multi_event_structure_flag"]] += 1
        for query_id in row["query_id"].split(";"):
            query_by_split[split][query_id] += 1
        text_hash_splits[row["text_sha256"]].add(split)

    cross_split_hashes = {hash_value: splits for hash_value, splits in text_hash_splits.items() if len(splits) > 1}
    duplicate_acns = [acn for acn, count in Counter(row["acn"] for row in enriched_rows).items() if count > 1]

    summary_path = SPLIT_DIR / f"split_summary_{date.today().isoformat()}.md"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Record-Level Split Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("These are record-level splits for the author-verified ASRS label corpus with local consistency-audit support. Full raw ASRS narratives are not included in these split files.\n\n")
        f.write("## Split Counts\n\n")
        for split in ["train", "dev", "test"]:
            f.write(f"- `{split}`: {split_counts[split]}\n")
        f.write("\n## Leakage Checks\n\n")
        f.write(f"- Duplicate ACNs across corpus: {len(duplicate_acns)}\n")
        f.write(f"- Exact normalized text hashes appearing in more than one split: {len(cross_split_hashes)}\n")
        f.write("- Split grouping key: normalized full ASRS text SHA256 hash.\n")
        f.write("- Stratification key: `silver_screening_status` + `silver_primary_event_type`.\n")
        f.write(f"- Random seed: `{SEED}`\n")

        f.write("\n## Screening Status By Split\n\n")
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

        f.write("## Multi-Event Structure By Split\n\n")
        for split in ["train", "dev", "test"]:
            f.write(f"### `{split}`\n\n")
            for key, value in multi_by_split[split].most_common():
                f.write(f"- `{key}`: {value}\n")
            f.write("\n")

        f.write("## Non-Exclusive Query Coverage By Split\n\n")
        for split in ["train", "dev", "test"]:
            f.write(f"### `{split}`\n\n")
            for key, value in query_by_split[split].most_common():
                f.write(f"- `{key}`: {value}\n")
            f.write("\n")

        f.write("## Modeling Recommendation\n\n")
        f.write("- Use these splits first for record-level screening and primary event-type classification.\n")
        f.write("- Use `silver_secondary_event_types` for optional multi-label auxiliary experiments.\n")
        f.write("- Do not claim full event-mention extraction until rows marked `possible_multi_event_needs_event_level_policy` are converted into event-level units or explicitly scoped out.\n")

    print(f"assignments={assignment_path}")
    print(f"summary={summary_path}")
    print("split_counts", dict(split_counts))
    print(f"cross_split_hashes={len(cross_split_hashes)}")
    print(f"duplicate_acns={len(duplicate_acns)}")


if __name__ == "__main__":
    main()
