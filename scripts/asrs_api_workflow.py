#!/usr/bin/env python
"""
Public ASRS DBOL API helper for the ASRS GroundOps NLP benchmark.

This script uses the same public endpoints called by the official ASRS Database
Online web interface. It is intended for reproducible local corpus construction,
not for prevalence estimation and not for redistributing raw ASRS narratives.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import date
from pathlib import Path
from typing import Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
SEARCH_URL = "https://asrsdbol.arc.nasa.gov/dbol/search/"
DETAILS_URL = "https://asrsdbol.arc.nasa.gov/dbol/details/"

QUERY_GROUPS = {
    "Q01": '((CABIN OR "FLIGHT ATTENDANT" OR FA OR PAX OR PASSENGER) AND (CLEAN% OR CATER% OR LAV% OR "CABIN SERVICE" OR GALLEY OR TRASH))',
    "Q02": '((WHEELCHAIR OR "WHEEL CHAIR" OR PRM OR "PASSENGER ASSIST%" OR "SPECIAL ASSIST%" OR MOBILITY) AND (BOARD% OR DEBOARD% OR GATE OR RAMP OR "JET BRIDGE" OR JETWAY))',
    "Q03": '((GATE OR "JET BRIDGE" OR JETWAY OR BOARD% OR DEBOARD%) AND (DELAY% OR HOLD% OR "NOT READY" OR WAIT% OR MISSING OR BOARDING))',
    "Q04": '((RAMP OR "GROUND CREW" OR "GROUND PERSONNEL" OR "GROUND HANDLING" OR "RAMP AGENT") AND (TUG OR TOW% OR PUSHBACK OR "PUSH BACK" OR CHOCK% OR MARSHAL% OR WAND OR "GROUND EQUIPMENT" OR GSE))',
    "Q05": '((BAGGAGE OR BAG OR CARGO OR LOAD% OR ULD OR "WEIGHT AND BALANCE" OR "WT AND BAL") AND (RAMP OR GATE OR BOARD% OR LOAD%))',
    "Q06": '((FUEL OR FUEL% OR REFUEL% OR "FUEL TRUCK") AND (RAMP OR GATE OR DELAY% OR SPILL% OR FUELING))',
    "Q07": '((MAINT% OR MEL OR "MINIMUM EQUIPMENT LIST" OR DEFECT OR DEFER% OR "AIRCRAFT SWAP") AND (GATE OR RAMP OR BOARD% OR CABIN OR PASSENGER OR "BEFORE DEPARTURE" OR PREFLIGHT OR "PRE FLIGHT"))',
    "Q08": '((DISPATCH OR "OPERATIONS" OR "OPERATION CONTROL" OR COMPANY OR COORDINAT% OR COMMUNICAT%) AND (GATE OR RAMP OR BOARD% OR PUSHBACK OR MAINT% OR FUEL%))',
    "Q09": '((CATER% OR CLEAN% OR LAV% OR GALLEY OR "CABIN SERVICE" OR "CABIN READY" OR "CABIN NOT READY") AND (GATE OR BOARD% OR DEBOARD% OR "BEFORE DEPARTURE" OR PREFLIGHT OR "PRE FLIGHT" OR RAMP))',
    "Q10": '(("GATE AGENT" OR "BOARDING DOOR" OR "CABIN DOOR" OR "JET BRIDGE" OR JETWAY OR BOARD% OR DEBOARD%) AND (ARM% OR OPEN% OR CLOSE% OR DELAY% OR WAIT% OR "NOT READY" OR "HAND SIGNAL" OR PAPERWORK))',
    "Q11": '((BAGGAGE OR CARGO OR ULD OR "WEIGHT AND BALANCE" OR "WT AND BAL" OR "LOAD CLOSEOUT" OR "LOAD SHEET") AND (GATE OR RAMP OR BOARD% OR LOAD% OR DEPARTURE OR "BEFORE DEPARTURE"))',
    "Q12": '((FUELING OR REFUEL% OR "FUEL TRUCK" OR FUELER OR "FUEL SPILL" OR "FUEL LEAK") AND (GATE OR RAMP OR "BEFORE DEPARTURE" OR BOARD% OR PUSHBACK))',
    "Q13": '((MAINT% OR MEL OR "MINIMUM EQUIPMENT LIST" OR MECHANIC OR DEFECT OR DEFER% OR "AIRCRAFT SWAP") AND (GATE OR RAMP OR BOARD% OR "BEFORE DEPARTURE" OR PREFLIGHT OR "PRE FLIGHT" OR "CABIN DOOR"))',
    "Q14": '((DISPATCH OR "OPERATIONS" OR "OPERATION CONTROL" OR COORDINAT% OR COMMUNICAT%) AND ("GATE AGENT" OR RAMP OR PUSHBACK OR "LOAD CLOSEOUT" OR FUELING OR MAINT% OR BOARD%))',
}


def base_payload(text: str) -> dict:
    return {
        "narrative": True,
        "synopsis": True,
        "callback": True,
        "searchRelatedWords": False,
        "eavs": [[] for _ in range(44)],
        "fullformOnly": True,
        "abbreviatedOnly": False,
        "generalAviation": False,
        "uas": False,
        "acns": "",
        "text": text,
        "locations": [],
        "stateProvinces": [],
        "makeModels": [],
    }


def post_json(url: str, payload: dict, timeout: int = 120) -> object:
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def search_acns(text: str) -> list[int]:
    data = post_json(SEARCH_URL, base_payload(text))
    if not isinstance(data, list):
        raise TypeError(f"Expected list search response, got {type(data).__name__}")
    return [int(item["acn"]) for item in data if "acn" in item]


def chunks(values: list[int], size: int) -> Iterable[list[int]]:
    for i in range(0, len(values), size):
        yield values[i : i + size]


def fetch_details(text: str, acns: list[int], batch_size: int = 300, pause_seconds: float = 0.25) -> list[dict]:
    records: list[dict] = []
    for batch in chunks(acns, batch_size):
        payload = {
            "text": text,
            "narrative": True,
            "synopsis": True,
            "callback": True,
            "searchRelatedWords": False,
            "acns": ",".join(str(acn) for acn in batch),
        }
        data = post_json(DETAILS_URL, payload)
        if not isinstance(data, list):
            raise TypeError(f"Expected list details response, got {type(data).__name__}")
        records.extend(data)
        time.sleep(pause_seconds)
    return records


def in_year_window(record: dict, start_year: int, end_year: int) -> bool:
    value = str(record.get("dateOfOccurrence") or "")
    if len(value) < 4:
        return False
    try:
        year = int(value[:4])
    except ValueError:
        return False
    return start_year <= year <= end_year


def write_counts(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    run_date = date.today().isoformat()
    for query_id, query_text in QUERY_GROUPS.items():
        acns = search_acns(query_text)
        rows.append(
            {
                "query_id": query_id,
                "run_date": run_date,
                "asrs_url_or_interface": SEARCH_URL,
                "query_text": query_text,
                "fixed_filters": "narrative=true;synopsis=true;callback=true;fullformOnly=true;generalAviation=false;uas=false",
                "date_window": "not_filtered_in_search",
                "export_format": "search_acn_json",
                "result_count": len(acns),
                "records_exported": 0,
                "notes": "ASRS current search count before local date filtering; not a prevalence estimate",
            }
        )
        print(f"{query_id}: {len(acns)} ACNs")

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def collect_query(query_id: str, out_dir: Path, start_year: int, end_year: int, limit: int | None) -> None:
    if query_id not in QUERY_GROUPS:
        raise KeyError(f"Unknown query_id {query_id}. Options: {', '.join(QUERY_GROUPS)}")
    query_text = QUERY_GROUPS[query_id]
    out_dir.mkdir(parents=True, exist_ok=True)
    acns = search_acns(query_text)
    if limit is not None:
        acns = acns[:limit]
    records = fetch_details(query_text, acns)
    filtered = [record for record in records if in_year_window(record, start_year, end_year)]

    raw_path = out_dir / f"{query_id}_details_{date.today().isoformat()}.json"
    manifest_path = ROOT / "data" / "manifests" / f"{query_id}_candidate_manifest_{date.today().isoformat()}.csv"
    raw_path.write_text(json.dumps(filtered, indent=2), encoding="utf-8")

    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "query_id",
            "acn",
            "date_of_occurrence",
            "is_abbreviated",
            "is_general_aviation",
            "is_uas",
            "people_count",
            "has_synopsis",
            "initial_screening_status",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in filtered:
            writer.writerow(
                {
                    "query_id": query_id,
                    "acn": record.get("acn", ""),
                    "date_of_occurrence": record.get("dateOfOccurrence", ""),
                    "is_abbreviated": record.get("isAbbreviated", ""),
                    "is_general_aviation": record.get("isGeneralAviation", ""),
                    "is_uas": record.get("isUas", ""),
                    "people_count": len(record.get("people") or []),
                    "has_synopsis": bool(record.get("synopsis")),
                    "initial_screening_status": "unscreened",
                }
            )

    print(f"{query_id}: searched {len(acns)} ACNs, fetched {len(records)} records, kept {len(filtered)} in {start_year}-{end_year}")
    print(f"raw_json={raw_path}")
    print(f"manifest={manifest_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ASRS DBOL search/details helper")
    parser.add_argument("--counts", action="store_true", help="Write count CSV for Q01-Q08")
    parser.add_argument("--collect", choices=sorted(QUERY_GROUPS), help="Collect details for one query ID")
    parser.add_argument("--limit", type=int, default=None, help="Optional ACN limit for collection")
    parser.add_argument("--start-year", type=int, default=2011)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--out-dir", default=str(ROOT / "data" / "raw" / "asrs_api"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.counts and not args.collect:
        raise SystemExit("Use --counts and/or --collect QID")
    if args.counts:
        write_counts(ROOT / "data" / "manifests" / f"query_counts_{date.today().isoformat()}.csv")
    if args.collect:
        collect_query(args.collect, Path(args.out_dir), args.start_year, args.end_year, args.limit)


if __name__ == "__main__":
    main()
