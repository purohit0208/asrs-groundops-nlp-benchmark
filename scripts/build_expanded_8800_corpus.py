#!/usr/bin/env python
"""
Build the 8,800-record expanded ASRS GroundOps corpus from the existing
8,801-record candidate pool.

The 5,000 seed labels keep their author-verified local-audit provenance.
The additional 3,800 records are agent-generated expanded labels and must
not be described as newly human verified.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from pilot_prescreen import classify, record_text


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "asrs_api"
MANIFEST_DIR = ROOT / "data" / "manifests"
REPORT_DIR = ROOT / "reports"

CANDIDATE_FILE = MANIFEST_DIR / "candidate_records_manifest.csv"
SEED_LABEL_FILE = MANIFEST_DIR / "author_verified_single_reviewer_labels_5000_2026-06-03.csv"

RAW_FILES = [
    RAW_DIR / "Q02_details_2026-06-02.json",
    RAW_DIR / "Q04_details_2026-06-02.json",
    RAW_DIR / "Q09_details_2026-06-03.json",
    RAW_DIR / "Q10_details_2026-06-03.json",
    RAW_DIR / "Q11_details_2026-06-03.json",
    RAW_DIR / "Q12_details_2026-06-03.json",
]

TARGET_SIZE = 8800
SEED_SIZE = 5000

BASE_LABEL_FIELDS = [
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
    "author_verification_status",
    "author_verification_date",
    "author_verification_source",
    "author_verification_scope",
    "expanded_corpus_role",
    "expanded_label_provenance",
    "expanded_selection_note",
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


def year_from_value(value: str) -> int | None:
    match = re.match(r"^(\d{4})", value or "")
    if not match:
        return None
    return int(match.group(1))


def content_length_for_candidate(row: dict[str, str], records: dict[str, dict]) -> tuple[int, int, int]:
    record = records.get(row["acn"])
    if not record:
        return (0, 0, 0)
    synopsis, narrative, all_text = record_text(record)
    return (len(all_text.strip()), len(synopsis.strip()), len(narrative.strip()))


def select_rows(
    candidates: list[dict[str, str]], seed_rows: list[dict[str, str]], records: dict[str, dict]
) -> tuple[list[dict[str, str]], dict[str, str]]:
    seed_acns = {row["acn"] for row in seed_rows}
    by_acn = {row["acn"]: row for row in candidates}
    seed_candidate_rows = [by_acn[row["acn"]] for row in seed_rows]

    remaining = [row for row in candidates if row["acn"] not in seed_acns]
    if len(remaining) != 3801:
        raise RuntimeError(f"Expected 3,801 remaining candidates, found {len(remaining)}")

    ranked_remaining = sorted(
        remaining,
        key=lambda row: (
            content_length_for_candidate(row, records)[0],
            content_length_for_candidate(row, records)[1],
            content_length_for_candidate(row, records)[2],
            row["candidate_id"],
            int(row["acn"]),
        ),
    )
    excluded = ranked_remaining[0]
    selected_remaining = [row for row in remaining if row["acn"] != excluded["acn"]]
    selected = seed_candidate_rows + selected_remaining
    if len(selected) != TARGET_SIZE:
        raise RuntimeError(f"Expected {TARGET_SIZE} selected records, found {len(selected)}")
    return selected, excluded


def make_manifest_rows(selected: list[dict[str, str]], seed_acns: set[str], excluded_acn: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for i, row in enumerate(selected, start=1):
        output = dict(row)
        if row["acn"] in seed_acns:
            output["corpus_id"] = next_seed_id(row["acn"])
            output["expanded_corpus_role"] = "seed_5000_author_verified_local_audit"
            output["expanded_selection_note"] = "Preserved from 5,000-row seed corpus."
        else:
            output["corpus_id"] = f"ASRS_GOPS_{i:05d}"
            output["expanded_corpus_role"] = "expanded_3800_agent_silver"
            output["expanded_selection_note"] = (
                "Added from remaining candidate pool; one lowest-information remaining record excluded "
                f"to reach 8,800. Excluded ACN: {excluded_acn}."
            )
        rows.append(output)
    return rows


_SEED_ID_BY_ACN: dict[str, str] = {}


def next_seed_id(acn: str) -> str:
    return _SEED_ID_BY_ACN[acn]


def create_label_rows(
    manifest_rows: list[dict[str, str]], seed_labels: list[dict[str, str]], records: dict[str, dict]
) -> list[dict[str, str]]:
    seed_by_acn = {row["acn"]: row for row in seed_labels}
    output_rows: list[dict[str, str]] = []

    for row in manifest_rows:
        acn = row["acn"]
        if acn in seed_by_acn:
            label = {field: seed_by_acn[acn].get(field, "") for field in BASE_LABEL_FIELDS}
            label["corpus_id"] = row["corpus_id"]
            label["candidate_id"] = row["candidate_id"]
            label["query_id"] = row["query_id"]
            label["expanded_corpus_role"] = "seed_5000_author_verified_local_audit"
            label["expanded_label_provenance"] = "preserved_seed_label"
            label["expanded_selection_note"] = row["expanded_selection_note"]
            output_rows.append(label)
            continue

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
                "labeler": "agent_silver_v0_2_expanded",
                "label_date": date.today().isoformat(),
                "verification_status": "agent_silver_expansion_not_human_verified",
                "notes": (
                    "Expanded 8,800-corpus agent label; not human verified. Use for training-scale "
                    "or robustness experiments, not as independently adjudicated gold."
                ),
                "author_verification_status": "",
                "author_verification_date": "",
                "author_verification_source": "",
                "author_verification_scope": "",
                "expanded_corpus_role": "expanded_3800_agent_silver",
                "expanded_label_provenance": "new_agent_silver_expansion",
                "expanded_selection_note": row["expanded_selection_note"],
            }
        )
    return output_rows


def audit(
    labels: list[dict[str, str]],
    manifest_rows: list[dict[str, str]],
    records: dict[str, dict],
    excluded: dict[str, str],
) -> dict:
    manifest_by_acn = {row["acn"]: row for row in manifest_rows}
    corpus_ids = [row["corpus_id"] for row in labels]
    acns = [row["acn"] for row in labels]

    status_counts = Counter(row["silver_screening_status"] for row in labels)
    type_counts = Counter(row["silver_primary_event_type"] for row in labels)
    verification_counts = Counter(row["verification_status"] for row in labels)
    role_counts = Counter(row["expanded_corpus_role"] for row in labels)
    multi_counts = Counter(row["silver_multi_event_flag"] for row in labels)
    query_counts = Counter()
    for row in labels:
        for query_id in row["query_id"].split(";"):
            query_counts[query_id] += 1

    missing_raw: list[str] = []
    missing_manifest: list[str] = []
    date_outside_window: list[tuple[str, str]] = []
    rule_mismatches: list[tuple[str, str, str, str, str]] = []
    include_without_evidence: list[tuple[str, str, str]] = []
    include_with_not_relevant: list[tuple[str, str]] = []
    exclude_with_relevant_type: list[tuple[str, str, str]] = []
    evidence_not_found: list[tuple[str, str]] = []
    blank_required: list[tuple[str, str]] = []

    required_fields = [
        "corpus_id",
        "candidate_id",
        "acn",
        "query_id",
        "silver_screening_status",
        "silver_primary_event_type",
        "labeler",
        "verification_status",
        "expanded_corpus_role",
        "expanded_label_provenance",
    ]

    for row in labels:
        for field in required_fields:
            if not row.get(field):
                blank_required.append((row.get("corpus_id", ""), field))

        acn = row["acn"]
        record = records.get(acn)
        if not record:
            missing_raw.append(acn)
            continue

        manifest_row = manifest_by_acn.get(acn)
        if not manifest_row:
            missing_manifest.append(acn)
        else:
            year = year_from_value(manifest_row.get("report_date_or_year", ""))
            if year is None or year < 2011 or year > 2025:
                date_outside_window.append((acn, manifest_row.get("report_date_or_year", "")))

        synopsis, narrative, all_text = record_text(record)
        expected = classify(row["query_id"], synopsis, narrative, all_text)
        comparison_fields = [
            ("silver_screening_status", "screening_status"),
            ("silver_primary_event_type", "primary_candidate_event_type"),
            ("silver_secondary_event_types", "secondary_candidate_event_types"),
            ("silver_multi_event_flag", "multi_event_flag"),
            ("reason_for_exclusion", "reason_for_exclusion"),
        ]
        for actual_field, expected_field in comparison_fields:
            if row.get(actual_field, "") != expected.get(expected_field, ""):
                rule_mismatches.append(
                    (row["corpus_id"], acn, actual_field, row.get(actual_field, ""), expected.get(expected_field, ""))
                )

        status = row["silver_screening_status"]
        event_type = row["silver_primary_event_type"]
        if status == "include_ground_cabin_event" and event_type == "not_relevant":
            include_with_not_relevant.append((row["corpus_id"], acn))
        if status.startswith("exclude") and event_type != "not_relevant":
            exclude_with_relevant_type.append((row["corpus_id"], acn, event_type))

        evidence_values = [row.get("ground_phase_evidence", ""), row.get("cabin_or_service_evidence", "")]
        if status == "include_ground_cabin_event" and not any(value.strip() for value in evidence_values):
            include_without_evidence.append((row["corpus_id"], acn, event_type))

        normalized_source = normalize_text(all_text)
        for evidence in evidence_values:
            evidence_norm = normalize_text(evidence)
            if len(evidence_norm) >= 30 and evidence_norm not in normalized_source:
                evidence_not_found.append((row["corpus_id"], acn))
                break

    duplicate_corpus_ids = [item for item, count in Counter(corpus_ids).items() if count > 1]
    duplicate_acns = [item for item, count in Counter(acns).items() if count > 1]
    blocking_errors = (
        len(duplicate_corpus_ids)
        + len(duplicate_acns)
        + len(missing_raw)
        + len(missing_manifest)
        + len(rule_mismatches)
        + len(blank_required)
        + len(include_with_not_relevant)
        + len(exclude_with_relevant_type)
    )
    return {
        "row_count": len(labels),
        "unique_corpus_ids": len(set(corpus_ids)),
        "unique_acns": len(set(acns)),
        "status_counts": status_counts,
        "type_counts": type_counts,
        "verification_counts": verification_counts,
        "role_counts": role_counts,
        "multi_counts": multi_counts,
        "query_counts": query_counts,
        "duplicate_corpus_ids": duplicate_corpus_ids,
        "duplicate_acns": duplicate_acns,
        "missing_raw": missing_raw,
        "missing_manifest": missing_manifest,
        "date_outside_window": date_outside_window,
        "rule_mismatches": rule_mismatches,
        "include_without_evidence": include_without_evidence,
        "include_with_not_relevant": include_with_not_relevant,
        "exclude_with_relevant_type": exclude_with_relevant_type,
        "evidence_not_found": evidence_not_found,
        "blank_required": blank_required,
        "blocking_errors": blocking_errors,
        "excluded": excluded,
    }


def write_report(path: Path, result: dict, manifest_path: Path, label_path: Path) -> None:
    status = "PASS_WITH_CAVEATS" if result["blocking_errors"] == 0 else "FAIL"
    excluded = result["excluded"]
    with path.open("w", encoding="utf-8") as f:
        f.write("# Expanded 8,800 Corpus Cross-Audit\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Files\n\n")
        f.write(f"- Expanded manifest: `{manifest_path}`\n")
        f.write(f"- Expanded labels: `{label_path}`\n\n")
        f.write("## Selection Boundary\n\n")
        f.write("- Source pool: 8,801 unique ASRS candidate records from Q02/Q04/Q09/Q10/Q11/Q12.\n")
        f.write("- Target corpus: 8,800 records.\n")
        f.write("- Preserved seed: all 5,000 author-verified seed rows with local consistency-audit support.\n")
        f.write("- Added records: 3,800 agent-labeled remaining candidates.\n")
        f.write(
            "- Excluded record: ACN `{}` / candidate `{}` / query `{}` / date `{}`; selected for exclusion because it had the lowest combined synopsis/narrative text length among remaining candidates.\n\n".format(
                excluded["acn"],
                excluded["candidate_id"],
                excluded["query_id"],
                excluded.get("report_date_or_year", ""),
            )
        )
        f.write("## Cross-Audit Result\n\n")
        f.write(f"- Overall result: `{status}`\n")
        f.write(f"- Blocking internal-consistency errors: {result['blocking_errors']}\n")
        f.write(f"- Rows checked: {result['row_count']}\n")
        f.write(f"- Unique corpus IDs: {result['unique_corpus_ids']}\n")
        f.write(f"- Unique ACNs: {result['unique_acns']}\n")
        f.write(f"- Missing raw records: {len(result['missing_raw'])}\n")
        f.write(f"- Missing manifest records: {len(result['missing_manifest'])}\n")
        f.write(f"- Duplicate corpus IDs: {len(result['duplicate_corpus_ids'])}\n")
        f.write(f"- Duplicate ACNs: {len(result['duplicate_acns'])}\n")
        f.write(f"- Label-rule mismatches against current classifier: {len(result['rule_mismatches'])}\n")
        f.write(f"- Included rows without evidence snippet: {len(result['include_without_evidence'])}\n")
        f.write(f"- Evidence snippets not found in source text: {len(result['evidence_not_found'])}\n")
        f.write(f"- Rows outside 2011-2025 manifest window: {len(result['date_outside_window'])}\n\n")

        f.write("## Label Provenance Counts\n\n")
        for key, value in result["role_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Verification Status Counts\n\n")
        for key, value in result["verification_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Screening Status Counts\n\n")
        for key, value in result["status_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Primary Event-Type Counts\n\n")
        for key, value in result["type_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Multi-Event Flag Counts\n\n")
        for key, value in result["multi_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Non-Exclusive Query Coverage\n\n")
        for key, value in result["query_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")

        f.write("\n## Manuscript Boundary\n\n")
        f.write("- Do not call all 8,800 records human verified.\n")
        f.write("- Use the 5,000-row author-verified subset with local consistency-audit support as the verified reference split.\n")
        f.write("- Use the added 3,800 rows as weak-label training augmentation or robustness data.\n")
        f.write("- Raw ASRS narratives remain local except for the separately approved bounded remote LLM baseline.\n")


def write_summary(path: Path, rows: list[dict[str, str]], excluded: dict[str, str]) -> None:
    role_counts = Counter(row["expanded_corpus_role"] for row in rows)
    query_counts = Counter()
    for row in rows:
        for query_id in row["query_id"].split(";"):
            query_counts[query_id] += 1
    with path.open("w", encoding="utf-8") as f:
        f.write("# Expanded 8,800 Corpus Manifest Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write(f"- Records: {len(rows)}\n")
        f.write(f"- Excluded ACN: `{excluded['acn']}`\n")
        f.write("\n## Role Counts\n\n")
        for key, value in role_counts.most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Non-Exclusive Query Coverage\n\n")
        for key, value in query_counts.most_common():
            f.write(f"- `{key}`: {value}\n")


def main() -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    candidates = read_csv(CANDIDATE_FILE)
    seed_labels = read_csv(SEED_LABEL_FILE)
    if len(candidates) != 8801:
        raise RuntimeError(f"Expected 8,801 candidates, found {len(candidates)}")
    if len(seed_labels) != SEED_SIZE:
        raise RuntimeError(f"Expected {SEED_SIZE} seed labels, found {len(seed_labels)}")

    global _SEED_ID_BY_ACN
    _SEED_ID_BY_ACN = {row["acn"]: row["corpus_id"] for row in seed_labels}

    records = load_records()
    selected, excluded = select_rows(candidates, seed_labels, records)
    seed_acns = {row["acn"] for row in seed_labels}
    manifest_rows = make_manifest_rows(selected, seed_acns, excluded["acn"])
    label_rows = create_label_rows(manifest_rows, seed_labels, records)

    manifest_fields = list(manifest_rows[0].keys())
    manifest_path = MANIFEST_DIR / f"expanded_corpus_8800_manifest_{date.today().isoformat()}.csv"
    write_csv(manifest_path, manifest_rows, manifest_fields)

    label_path = MANIFEST_DIR / f"expanded_corpus_8800_labels_{date.today().isoformat()}.csv"
    write_csv(label_path, label_rows, BASE_LABEL_FIELDS)

    summary_path = MANIFEST_DIR / f"expanded_corpus_8800_summary_{date.today().isoformat()}.md"
    write_summary(summary_path, manifest_rows, excluded)

    result = audit(label_rows, manifest_rows, records, excluded)
    report_path = REPORT_DIR / f"expanded_corpus_8800_cross_audit_{date.today().isoformat()}.md"
    write_report(report_path, result, manifest_path, label_path)

    print(f"manifest={manifest_path}")
    print(f"labels={label_path}")
    print(f"summary={summary_path}")
    print(f"report={report_path}")
    print(f"rows={result['row_count']}")
    print(f"excluded_acn={excluded['acn']}")
    print(f"blocking_errors={result['blocking_errors']}")
    print(f"rule_mismatches={len(result['rule_mismatches'])}")
    print(f"include_without_evidence={len(result['include_without_evidence'])}")
    print(f"evidence_not_found={len(result['evidence_not_found'])}")
    print("role_counts", dict(result["role_counts"]))
    print("status_counts", dict(result["status_counts"]))


if __name__ == "__main__":
    main()
