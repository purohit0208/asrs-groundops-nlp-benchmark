#!/usr/bin/env python
"""
Create a single-author verified derivative of the 5,000-record ASRS corpus and
run consistency checks against the original raw records and labeling rules.

The script does not erase the original agent-silver labels. It records the
author-reported verification as a separate provenance layer.
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

SOURCE_LABEL_FILE = MANIFEST_DIR / "silver_corpus_5000_labels_2026-06-03.csv"
SOURCE_MANIFEST_FILE = MANIFEST_DIR / "silver_corpus_5000_manifest_2026-06-03.csv"

RAW_FILES = [
    RAW_DIR / "Q02_details_2026-06-02.json",
    RAW_DIR / "Q04_details_2026-06-02.json",
    RAW_DIR / "Q09_details_2026-06-03.json",
    RAW_DIR / "Q10_details_2026-06-03.json",
    RAW_DIR / "Q11_details_2026-06-03.json",
    RAW_DIR / "Q12_details_2026-06-03.json",
]

AUTHOR_VERIFICATION_STATUS = "author_verified_single_reviewer"
AUTHOR_VERIFICATION_SOURCE = (
    "User/author stated in the local Codex thread on 2026-06-03 that the corpus "
    "was verified and no problems were found; no independent second reviewer."
)


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


def year_from_value(value: str) -> int | None:
    match = re.match(r"^(\d{4})", value or "")
    if not match:
        return None
    return int(match.group(1))


def create_author_verified_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    verified_rows: list[dict[str, str]] = []
    for row in rows:
        updated = dict(row)
        updated["verification_status"] = AUTHOR_VERIFICATION_STATUS
        updated["author_verification_status"] = "author_reported_no_issues"
        updated["author_verification_date"] = date.today().isoformat()
        updated["author_verification_source"] = AUTHOR_VERIFICATION_SOURCE
        updated["author_verification_scope"] = (
            "Assumed to cover all 5,000 rows in silver_corpus_5000_labels_2026-06-03.csv."
        )
        updated["notes"] = (
            f"{updated.get('notes', '')} Author-reported verification recorded; "
            "treat as single-reviewer reference labels, not independently adjudicated multi-reviewer gold."
        ).strip()
        verified_rows.append(updated)
    return verified_rows


def audit(rows: list[dict[str, str]], manifest_rows: list[dict[str, str]], records: dict[str, dict]) -> dict:
    manifest_by_acn = {row["acn"]: row for row in manifest_rows}
    corpus_ids = [row["corpus_id"] for row in rows]
    acns = [row["acn"] for row in rows]

    status_counts = Counter(row["silver_screening_status"] for row in rows)
    type_counts = Counter(row["silver_primary_event_type"] for row in rows)
    verification_counts = Counter(row["verification_status"] for row in rows)
    multi_event_counts = Counter(row["silver_multi_event_flag"] for row in rows)
    query_counts = Counter()
    for row in rows:
        for query_id in row["query_id"].split(";"):
            query_counts[query_id] += 1

    missing_raw = []
    missing_manifest = []
    date_outside_window = []
    rule_mismatches = []
    include_without_evidence = []
    include_with_not_relevant = []
    exclude_with_relevant_type = []
    evidence_not_found = []
    blank_required = []

    required_fields = [
        "corpus_id",
        "candidate_id",
        "acn",
        "query_id",
        "silver_screening_status",
        "silver_primary_event_type",
        "labeler",
        "verification_status",
    ]

    for row in rows:
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

        evidence_values = [
            row.get("ground_phase_evidence", ""),
            row.get("cabin_or_service_evidence", ""),
        ]
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
        "row_count": len(rows),
        "unique_corpus_ids": len(set(corpus_ids)),
        "unique_acns": len(set(acns)),
        "status_counts": status_counts,
        "type_counts": type_counts,
        "verification_counts": verification_counts,
        "multi_event_counts": multi_event_counts,
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
    }


def write_report(path: Path, result: dict, verified_path: Path) -> None:
    status = "PASS_WITH_CAVEATS" if result["blocking_errors"] == 0 else "FAIL"
    with path.open("w", encoding="utf-8") as f:
        f.write("# Author Verification And Agent Cross-Audit\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Verification Event\n\n")
        f.write("- Author statement: user/author reported in this local Codex thread that the corpus was verified and no problems were found.\n")
        f.write("- Recorded status: `author_verified_single_reviewer`.\n")
        f.write("- Scope assumption: all 5,000 rows in `silver_corpus_5000_labels_2026-06-03.csv`.\n")
        f.write("- Boundary: this is single-author verification, not independent multi-reviewer adjudication.\n")
        f.write(f"- Derived label file: `{verified_path}`.\n\n")

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

        f.write("## Screening Status Counts\n\n")
        for key, value in result["status_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")

        f.write("\n## Primary Event-Type Counts\n\n")
        for key, value in result["type_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")

        f.write("\n## Multi-Event Flag Counts\n\n")
        for key, value in result["multi_event_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")

        f.write("\n## Non-Exclusive Query Coverage\n\n")
        for key, value in result["query_counts"].most_common():
            f.write(f"- `{key}`: {value}\n")

        f.write("\n## Scientific Caveats\n\n")
        f.write("- Use `single-author-verified reference labels` or `author-verified single-reviewer labels` in the manuscript.\n")
        f.write("- Avoid unqualified `gold standard` wording unless the manuscript defines it narrowly and discloses that there is only one human reviewer.\n")
        f.write("- ASRS reports remain voluntary, self-reported, not NASA-verified, and unsuitable for prevalence estimation.\n")
        f.write("- Raw ASRS narrative text redistribution remains unresolved; public release should prioritize ACNs, protocol, code, and labels unless redistribution terms are confirmed.\n")
        f.write("- Rows marked `needs_author_review` in `silver_multi_event_flag` indicate multi-event structure; event-level extraction may still need splitting before final model training.\n")

        if result["rule_mismatches"]:
            f.write("\n## Rule Mismatch Examples\n\n")
            for item in result["rule_mismatches"][:20]:
                corpus_id, acn, field, actual, expected = item
                f.write(f"- `{corpus_id}` / ACN `{acn}` / `{field}`: actual `{actual}`; expected `{expected}`\n")

        if result["include_without_evidence"]:
            f.write("\n## Included Rows Without Evidence Examples\n\n")
            for corpus_id, acn, event_type in result["include_without_evidence"][:20]:
                f.write(f"- `{corpus_id}` / ACN `{acn}` / `{event_type}`\n")


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(SOURCE_LABEL_FILE)
    manifest_rows = read_csv(SOURCE_MANIFEST_FILE)
    records = load_records()

    verified_rows = create_author_verified_rows(rows)
    fieldnames = list(rows[0].keys())
    for field in [
        "author_verification_status",
        "author_verification_date",
        "author_verification_source",
        "author_verification_scope",
    ]:
        if field not in fieldnames:
            fieldnames.append(field)

    verified_path = MANIFEST_DIR / f"author_verified_single_reviewer_labels_5000_{date.today().isoformat()}.csv"
    write_csv(verified_path, verified_rows, fieldnames)

    result = audit(verified_rows, manifest_rows, records)
    report_path = REPORT_DIR / f"author_verification_cross_audit_5000_{date.today().isoformat()}.md"
    write_report(report_path, result, verified_path)

    print(f"verified={verified_path}")
    print(f"report={report_path}")
    print(f"rows={result['row_count']}")
    print(f"blocking_errors={result['blocking_errors']}")
    print(f"rule_mismatches={len(result['rule_mismatches'])}")
    print(f"include_without_evidence={len(result['include_without_evidence'])}")
    print(f"evidence_not_found={len(result['evidence_not_found'])}")


if __name__ == "__main__":
    main()
