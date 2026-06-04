#!/usr/bin/env python
"""
Agent pre-screening helper for the ASRS GroundOps NLP pilot sample.

This is not a final annotation script. It creates an auditable relevance
pre-screening pass that must be author-verified before manuscript-grade labels
or model-training labels are claimed.
"""

from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "data" / "manifests"
RAW_DIR = ROOT / "data" / "raw" / "asrs_api"
RAW_FILES = [
    RAW_DIR / "Q02_details_2026-06-02.json",
    RAW_DIR / "Q04_details_2026-06-02.json",
]

OUTPUT_FIELDS = [
    "candidate_id",
    "acn",
    "query_id",
    "screening_status",
    "primary_candidate_event_type",
    "secondary_candidate_event_types",
    "multi_event_flag",
    "ground_phase_evidence",
    "cabin_or_service_evidence",
    "reason_for_exclusion",
    "reviewer",
    "review_date",
    "notes",
]


PATTERNS = {
    "hazmat_mobility_device": [
        "wheelchair",
        "wheel chair",
        "scooter",
        "lithium",
        "battery",
        "dangerous goods",
        "hazmat",
        "notoc",
        "dg ",
    ],
    "passenger_assistance": [
        "passenger assist",
        "special assist",
        "wheelchair",
        "mobility",
        "boarding assistance",
    ],
    "jetway_or_gate_infrastructure": [
        "jetway",
        "jet bridge",
        "gate marking",
        "gate number",
        "walkway",
        "lead-in line",
        "lead in line",
    ],
    "gate_or_boarding": [
        "gate agent",
        "boarding",
        "deboarding",
        "deplan",
        "cabin door",
        "entry door",
        "boarding door",
        "aircraft door",
        "ramp door",
    ],
    "pushback_towing_chocks": [
        "pushback",
        "push back",
        "towbar",
        "tow bar",
        "tug",
        "towing",
        "tow ",
        "chock",
        "pushed",
    ],
    "ramp_ground_handling": [
        "ramp",
        "ground crew",
        "ground personnel",
        "ground agent",
        "ground handling",
        "ramp agent",
        "marshaller",
        "marshalling",
        "marshal",
        "gse",
        "ground equipment",
        "belt loader",
        "vehicle",
        "truck",
    ],
    "baggage_cargo_weight_balance": [
        "baggage",
        "bag ",
        "bags ",
        "cargo",
        "load closeout",
        "load sheet",
        "weight and balance",
        "weight/balance",
        "uld",
    ],
    "fueling": [
        "fueling",
        "refuel",
        "fuel truck",
        "fuel spill",
        "fueler",
    ],
    "maintenance_readiness": [
        "maintenance",
        "mechanic",
        "mel",
        "minimum equipment list",
        "defect",
        "deferred",
        "aircraft swap",
    ],
    "dispatch_or_coordination": [
        "dispatch",
        "operations",
        "coordinat",
        "communicat",
        "company",
        "station",
    ],
    "cabin_service": [
        "catering",
        "cleaning",
        "lavatory",
        "galley",
        "trash",
        "cabin service",
    ],
    "other_ground_operation": [
        "taxiway",
        "taxi clearance",
        "taxiing",
        "runway incursion",
        "runway excursion",
        "movement area",
        "taxiway excursion",
        "wrong taxiway",
        "ground frequency",
        "tower frequency",
    ],
}

EXCLUSION_AIRBORNE = [
    "wake turbulence",
    "during cruise",
    "during flight",
    "enroute",
    "en route",
    "climb",
    "descent",
    "approach",
    "final approach",
    "departure climb",
    "diversion",
    "diverted",
    "hydraulic",
    "navigation system",
    "cabin altitude",
    "cabin rate",
    "pressurization",
    "fume event",
    "fumes event",
    "physiological symptoms",
    "turbulence",
    "loss of hydraulic",
    "low engine oil",
    "engine power loss",
    "landing gear",
    "heavy vibrations",
    "autopilot",
    "ils",
    "localizer",
    "runway condition",
]

GROUND_CONTEXT = [
    "gate",
    "ramp",
    "pushback",
    "push back",
    "taxi",
    "tow",
    "tug",
    "chock",
    "jetway",
    "jet bridge",
    "boarding",
    "deboarding",
    "preflight",
    "before departure",
    "maintenance",
    "cargo",
    "baggage",
    "wheelchair",
    "mobility",
    "battery",
    "ground crew",
    "ground personnel",
]


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def load_records() -> dict[str, dict]:
    records: dict[str, dict] = {}
    for path in RAW_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for record in data:
            records[str(record.get("acn"))] = record
    return records


def record_text(record: dict) -> tuple[str, str, str]:
    synopsis = clean_text(record.get("synopsis") or "")
    narratives = []
    for person in record.get("people") or []:
        narratives.append(clean_text(person.get("9107") or ""))
        notes = person.get("11330")
        if notes:
            narratives.append(clean_text(str(notes)))
    narrative = " ".join(narratives)
    all_text = f"{synopsis} {narrative}".strip()
    return synopsis, narrative, all_text


def contains_any(text_lower: str, terms: list[str]) -> bool:
    return any(term in text_lower for term in terms)


def find_snippet(text: str, terms: list[str], length: int = 140) -> str:
    lower = text.lower()
    positions = [lower.find(term) for term in terms if lower.find(term) >= 0]
    if not positions:
        return ""
    start = max(0, min(positions) - 45)
    snippet = text[start : start + length]
    return re.sub(r"\s+", " ", snippet).strip()


def classify(query_id: str, synopsis: str, narrative: str, all_text: str) -> dict:
    synopsis_lower = synopsis.lower()
    lower = all_text.lower()
    lower_without_precision_prm = lower.replace("precision runway monitor", "")
    synopsis_without_precision_prm = synopsis_lower.replace("precision runway monitor", "")
    synopsis_hits = [label for label, terms in PATTERNS.items() if contains_any(synopsis_without_precision_prm, terms)]
    all_hits = [label for label, terms in PATTERNS.items() if contains_any(lower_without_precision_prm, terms)]
    hits = synopsis_hits or all_hits

    # Prioritize precise ground/cabin categories over broad coordination words.
    priority = [
        "hazmat_mobility_device",
        "jetway_or_gate_infrastructure",
        "other_ground_operation",
        "pushback_towing_chocks",
        "gate_or_boarding",
        "ramp_ground_handling",
        "baggage_cargo_weight_balance",
        "fueling",
        "cabin_service",
        "passenger_assistance",
        "maintenance_readiness",
        "dispatch_or_coordination",
    ]
    ordered_hits = [label for label in priority if label in hits]

    strong_synopsis_target = any(
        label
        in {
            "hazmat_mobility_device",
            "jetway_or_gate_infrastructure",
            "pushback_towing_chocks",
            "ramp_ground_handling",
            "baggage_cargo_weight_balance",
            "fueling",
            "maintenance_readiness",
            "gate_or_boarding",
            "other_ground_operation",
        }
        for label in synopsis_hits
    )
    airborne_synopsis = contains_any(synopsis_lower, EXCLUSION_AIRBORNE)
    no_synopsis_ground_context = not contains_any(synopsis_lower, GROUND_CONTEXT)
    airborne_only = airborne_synopsis and not strong_synopsis_target
    weak_gate_only = "gate" in lower and not ordered_hits and airborne_synopsis
    incidental_query_match = airborne_synopsis and not synopsis_hits and no_synopsis_ground_context

    if airborne_only or weak_gate_only or incidental_query_match:
        return {
            "screening_status": "exclude_not_ground_or_cabin",
            "primary_candidate_event_type": "not_relevant",
            "secondary_candidate_event_types": "",
            "multi_event_flag": "false",
            "ground_phase_evidence": "",
            "cabin_or_service_evidence": "",
            "reason_for_exclusion": "airborne_or_non_ground_context_only",
            "notes": "Agent pre-screen: ground/cabin relevance not evident from synopsis/narrative.",
        }

    if ordered_hits and ordered_hits[0] == "passenger_assistance" and not contains_any(synopsis_lower, GROUND_CONTEXT):
        return {
            "screening_status": "exclude_not_ground_or_cabin",
            "primary_candidate_event_type": "not_relevant",
            "secondary_candidate_event_types": "",
            "multi_event_flag": "false",
            "ground_phase_evidence": "",
            "cabin_or_service_evidence": "",
            "reason_for_exclusion": "passenger_assistance_not_ground_phase",
            "notes": "Agent pre-screen: passenger assistance appears unrelated to ground phase.",
        }

    if not ordered_hits:
        if any(term in lower for term in ["taxi", "gate", "ramp", "ground", "airport"]):
            primary = "other_ground_operation"
            status = "uncertain_needs_review"
            reason = ""
            note = "Agent pre-screen: possible ground event, but no precise schema category matched."
        else:
            primary = "not_relevant"
            status = "exclude_not_ground_or_cabin"
            reason = "no_ground_cabin_keyword_evidence"
            note = "Agent pre-screen: no clear ground/cabin-service event evidence."
    else:
        primary = ordered_hits[0]
        secondary_hits = meaningful_secondary_hits(primary, ordered_hits, lower)
        status = "include_ground_cabin_event"
        reason = ""
        note = "Agent pre-screen: author verification required before manuscript-grade labeling."

    ground_terms = []
    cabin_terms = []
    for label in ordered_hits or [primary]:
        if label in {
            "pushback_towing_chocks",
            "ramp_ground_handling",
            "jetway_or_gate_infrastructure",
            "gate_or_boarding",
            "baggage_cargo_weight_balance",
            "fueling",
            "maintenance_readiness",
            "dispatch_or_coordination",
            "other_ground_operation",
        }:
            ground_terms.extend(PATTERNS.get(label, ["taxi", "gate", "ramp", "ground"]))
        if label in {"hazmat_mobility_device", "passenger_assistance", "cabin_service", "gate_or_boarding"}:
            cabin_terms.extend(PATTERNS.get(label, []))

    return {
        "screening_status": status,
        "primary_candidate_event_type": primary,
        "secondary_candidate_event_types": ";".join(meaningful_secondary_hits(primary, ordered_hits, lower)),
        "multi_event_flag": "needs_author_review" if meaningful_secondary_hits(primary, ordered_hits, lower) else "false",
        "ground_phase_evidence": find_snippet(all_text, ground_terms)[:160],
        "cabin_or_service_evidence": find_snippet(all_text, cabin_terms)[:160],
        "reason_for_exclusion": reason,
        "notes": note,
    }


def meaningful_secondary_hits(primary: str, ordered_hits: list[str], lower: str) -> list[str]:
    """Return only likely distinct event families, not parent/child keyword overlap."""
    secondary = ordered_hits[1:]

    # Passenger assistance is usually the context for wheelchair/battery records,
    # not a separate event by itself in this pilot screening task.
    if primary == "hazmat_mobility_device":
        secondary = [
            hit
            for hit in secondary
            if hit
            in {
                "pushback_towing_chocks",
                "fueling",
                "maintenance_readiness",
                "dispatch_or_coordination",
                "cabin_service",
            }
        ]

    # Pushback/towing is a specific ramp-ground-handling subtype.
    if primary == "pushback_towing_chocks":
        secondary = [
            hit
            for hit in secondary
            if hit
            in {
                "hazmat_mobility_device",
                "baggage_cargo_weight_balance",
                "fueling",
                "maintenance_readiness",
                "dispatch_or_coordination",
                "cabin_service",
            }
        ]

    # Ramp-ground-handling is often the parent context for gate, cargo, vehicle,
    # and pushback records; keep only clearly distinct operational functions.
    if primary == "ramp_ground_handling":
        secondary = [
            hit
            for hit in secondary
            if hit
            in {
                "pushback_towing_chocks",
                "baggage_cargo_weight_balance",
                "fueling",
                "maintenance_readiness",
                "gate_or_boarding",
                "hazmat_mobility_device",
            }
        ]

    if primary == "baggage_cargo_weight_balance":
        secondary = [
            hit
            for hit in secondary
            if hit
            in {
                "hazmat_mobility_device",
                "pushback_towing_chocks",
                "fueling",
                "maintenance_readiness",
                "dispatch_or_coordination",
            }
        ]

    if primary in {"gate_or_boarding", "jetway_or_gate_infrastructure", "passenger_assistance"}:
        secondary = [
            hit
            for hit in secondary
            if hit
            in {
                "hazmat_mobility_device",
                "pushback_towing_chocks",
                "fueling",
                "maintenance_readiness",
                "dispatch_or_coordination",
                "cabin_service",
            }
        ]

    # Company/communication language appears in many ASRS narratives. Treat
    # coordination as distinct only when it is explicit dispatch/operations
    # coordination, not generic company wording.
    if "dispatch_or_coordination" in secondary:
        explicit_coordination = any(term in lower for term in ["dispatch", "operations", "coordinat"])
        if not explicit_coordination:
            secondary = [hit for hit in secondary if hit != "dispatch_or_coordination"]

    # Maintenance is distinct only if it is more than a passing reference to a
    # mechanic in a passenger-assistance or pushback narrative.
    if "maintenance_readiness" in secondary and primary in {"hazmat_mobility_device", "passenger_assistance"}:
        if not any(term in lower for term in ["mel", "minimum equipment list", "deferred", "aircraft swap", "maintenance delay"]):
            secondary = [hit for hit in secondary if hit != "maintenance_readiness"]

    return secondary


def main() -> None:
    records = load_records()
    input_path = MANIFEST_DIR / "screening_manifest.csv"
    rows = list(csv.DictReader(input_path.open(encoding="utf-8")))

    output_rows = []
    missing = []
    for row in rows:
        acn = row["acn"]
        record = records.get(acn)
        if not record:
            missing.append(acn)
            updated = dict(row)
            updated.update(
                {
                    "screening_status": "uncertain_needs_review",
                    "primary_candidate_event_type": "not_relevant",
                    "reason_for_exclusion": "raw_record_not_found",
                    "reviewer": "agent_prescreen",
                    "review_date": date.today().isoformat(),
                    "notes": "Agent pre-screen: raw record not found in Q02/Q04 JSON.",
                }
            )
            output_rows.append(updated)
            continue

        synopsis, narrative, all_text = record_text(record)
        prediction = classify(row["query_id"], synopsis, narrative, all_text)
        updated = {field: row.get(field, "") for field in OUTPUT_FIELDS}
        updated.update(prediction)
        updated["reviewer"] = "agent_prescreen"
        updated["review_date"] = date.today().isoformat()
        output_rows.append(updated)

    for path in [
        input_path,
        MANIFEST_DIR / f"pilot_screening_agent_prescreen_200_{date.today().isoformat()}.csv",
    ]:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
            writer.writeheader()
            writer.writerows(output_rows)

    status_counts = Counter(row["screening_status"] for row in output_rows)
    type_counts = Counter(row["primary_candidate_event_type"] for row in output_rows)
    summary_path = MANIFEST_DIR / f"pilot_screening_agent_prescreen_summary_{date.today().isoformat()}.md"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Pilot Screening Agent Pre-Screen Summary\n\n")
        f.write(f"Created: {date.today().isoformat()}\n\n")
        f.write("## Boundary\n\n")
        f.write("This is an agent pre-screening pass, not final manuscript-grade annotation. Author verification is required before using labels as gold-standard data.\n\n")
        f.write("## Counts By Screening Status\n\n")
        for key, value in status_counts.most_common():
            f.write(f"- `{key}`: {value}\n")
        f.write("\n## Counts By Primary Candidate Event Type\n\n")
        for key, value in type_counts.most_common():
            f.write(f"- `{key}`: {value}\n")
        if missing:
            f.write("\n## Missing Raw Records\n\n")
            for acn in missing:
                f.write(f"- `{acn}`\n")
        f.write("\n## Early Ambiguity Patterns\n\n")
        f.write("- Q02 creates a large mobility-device/hazmat-documentation cluster that may need its own event type or a documented merge into passenger assistance/baggage-cargo handling.\n")
        f.write("- Q04 creates broad ramp/pushback/ground-handling coverage, but some records are multi-event records with dispatch, maintenance, cargo, or vehicle interaction sub-events.\n")
        f.write("- Some records mention gate or ramp only as a location after an airborne event; these require careful exclusion during author verification.\n")
        f.write("- Event-level annotation will likely need one-report-to-many-event splitting for records with pushback plus paperwork, ramp personnel plus vehicle, or wheelchair battery plus cabin/gate handling.\n")

    print(f"rows={len(output_rows)}")
    print("status_counts", dict(status_counts))
    print("type_counts", dict(type_counts))
    print(f"updated={input_path}")
    print(f"copy={MANIFEST_DIR / f'pilot_screening_agent_prescreen_200_{date.today().isoformat()}.csv'}")
    print(f"summary={summary_path}")


if __name__ == "__main__":
    main()
