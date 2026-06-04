#!/usr/bin/env python
"""
Build the expanded ASRS GroundOps candidate pool and 5,000-record corpus sample.

The output is a corpus manifest only. It does not create human-verified labels.
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "asrs_api"
MANIFEST_DIR = ROOT / "data" / "manifests"

RAW_FILES = {
    "Q02": RAW_DIR / "Q02_details_2026-06-02.json",
    "Q04": RAW_DIR / "Q04_details_2026-06-02.json",
    "Q09": RAW_DIR / "Q09_details_2026-06-03.json",
    "Q10": RAW_DIR / "Q10_details_2026-06-03.json",
    "Q11": RAW_DIR / "Q11_details_2026-06-03.json",
    "Q12": RAW_DIR / "Q12_details_2026-06-03.json",
}

SAMPLE_TARGETS = {
    "Q02": 216,
    "Q04": 1000,
    "Q09": 1000,
    "Q10": 1000,
    "Q11": 984,
    "Q12": 800,
}


def load_records() -> dict[str, dict]:
    merged: dict[str, dict] = {}
    for query_id, path in RAW_FILES.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        for record in data:
            acn = str(record.get("acn"))
            if acn not in merged:
                merged[acn] = {"record": record, "queries": set(), "files": set()}
            merged[acn]["queries"].add(query_id)
            merged[acn]["files"].add(str(path))
    return merged


def row_from_record(candidate_id: str, acn: str, item: dict) -> dict:
    record = item["record"]
    people = record.get("people") or []
    narrative_present = any(bool(person.get("9107")) for person in people)
    return {
        "candidate_id": candidate_id,
        "acn": acn,
        "query_id": ";".join(sorted(item["queries"])),
        "report_date_or_year": record.get("dateOfOccurrence", ""),
        "local_time": "not_extracted",
        "location": "not_extracted",
        "aircraft_make_model": "not_extracted",
        "operator_type": "not_extracted",
        "event_type_field": "not_extracted",
        "flight_phase_field": "not_extracted",
        "narrative_present": narrative_present,
        "analyst_synopsis_present": bool(record.get("synopsis")),
        "raw_export_file": ";".join(sorted(item["files"])),
        "screening_status": "unscreened",
        "screening_notes": "",
    }


def write_candidate_pool(merged: dict[str, dict]) -> list[dict]:
    rows = []
    for i, (acn, item) in enumerate(sorted(merged.items(), key=lambda kv: int(kv[0]), reverse=True), start=1):
        rows.append(row_from_record(f"CAND_{i:06d}", acn, item))

    for path in [
        MANIFEST_DIR / "candidate_records_manifest.csv",
        MANIFEST_DIR / f"candidate_records_manifest_expanded_{date.today().isoformat()}.csv",
    ]:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    return rows


def build_sample(rows: list[dict], seed: int = 20260603) -> list[dict]:
    rng = random.Random(seed)
    by_query: dict[str, list[dict]] = defaultdict(list)
    selected_acns: set[str] = set()
    selected: list[dict] = []

    for row in rows:
        for query_id in row["query_id"].split(";"):
            by_query[query_id].append(row)

    for query_id in sorted(by_query):
        rng.shuffle(by_query[query_id])

    for query_id, target in SAMPLE_TARGETS.items():
        added = 0
        for row in by_query[query_id]:
            if row["acn"] in selected_acns:
                continue
            selected.append(dict(row))
            selected_acns.add(row["acn"])
            added += 1
            if added >= target:
                break

    if len(selected) < 5000:
        remaining = [row for row in rows if row["acn"] not in selected_acns]
        rng.shuffle(remaining)
        for row in remaining:
            selected.append(dict(row))
            selected_acns.add(row["acn"])
            if len(selected) >= 5000:
                break

    selected = selected[:5000]
    for i, row in enumerate(selected, start=1):
        row["corpus_id"] = f"ASRS_GOPS_{i:05d}"
        row["screening_status"] = "pending_agent_silver_label"
        row["screening_notes"] = "Selected for 5,000-record silver-standard corpus; not human verified."

    return selected


def write_sample(sample: list[dict]) -> None:
    fieldnames = ["corpus_id"] + [field for field in sample[0].keys() if field != "corpus_id"]
    path = MANIFEST_DIR / f"silver_corpus_5000_manifest_{date.today().isoformat()}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample)

    summary_path = MANIFEST_DIR / f"silver_corpus_5000_summary_{date.today().isoformat()}.md"
    query_counter = Counter()
    for row in sample:
        for query_id in row["query_id"].split(";"):
            query_counter[query_id] += 1

    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Silver Corpus 5000 Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("This is a 5,000-record silver-standard / agent-labeling corpus manifest. It is not human verified and must not be called a human gold-standard dataset.\n\n")
        f.write("## Counts\n\n")
        f.write(f"- Records: {len(sample)}\n")
        f.write("- Query-family coverage counts are non-exclusive because records can match multiple queries.\n\n")
        for query_id, count in query_counter.most_common():
            f.write(f"- `{query_id}`: {count}\n")

    print(f"sample={path}")
    print(f"summary={summary_path}")
    print("sample_query_counts", dict(query_counter))


def main() -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    merged = load_records()
    rows = write_candidate_pool(merged)
    sample = build_sample(rows)
    write_sample(sample)
    print(f"unique_candidates={len(rows)}")
    print(f"sample_size={len(sample)}")


if __name__ == "__main__":
    main()
