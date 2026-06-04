---
type: annotation_schema
domain: aviation-nlp
status: draft
created: 2026-06-02
tags:
  - asrs
  - annotation
  - schema
---

# Annotation Schema v0.2 Draft

## Boundary

This schema is for the standalone ASRS GroundOps NLP benchmark only.

It is not PhD `SCHEMA_V1`, not INTACT validation, and not an OCC deployment schema.

The schema was revised from v0.1 after the Q02/Q04 pilot pre-screening pass:

`protocols\PILOT_SCREENING_RESULTS_2026-06-02.md`

Current label-provenance rule:

- `agent_silver_v0_2` labels remain the original silver-standard provenance layer.
- The derived file `author_verified_single_reviewer_labels_5000_2026-06-03.csv` records the user's author-reported verification.
- `author_verified=true` or `verification_status=author_verified_single_reviewer` is allowed only for that derived layer or for future rows actually checked by a human.
- The current 5,000-record corpus may be described as author-verified reference labels with local consistency-audit support, not formal expert consensus, independently adjudicated gold, or multi-annotator ground truth.

## Unit Of Annotation

Primary unit:

`record_level_report`

One ASRS record is one benchmark row in the active 5,000-record corpus. If one report describes multiple separable operational issues, keep one row, assign the best primary event type, add secondary event types where supported, and mark the multi-event flag when appropriate.

Do not describe the current corpus as event-span or event-mention extraction. A future event-level extension would require a separate protocol and new artifacts.

Examples:

- wheelchair battery paperwork plus pushback delay: one or two events depending on whether the pushback event has independent operational content;
- towbar detachment plus ramp communication issue: likely one event with multiple contributing factors;
- airborne malfunction followed by towing to gate: usually exclude unless the ground/towing event is described with enough operational detail to annotate independently.

## Record-Level Screening Fields

Use these before event-level annotation:

| Field | Type | Values / rule |
|---|---|---|
| `candidate_id` | string | From candidate manifest. |
| `acn` | string/int | ASRS ACN. |
| `query_id` | string | Query or query combination. |
| `screening_status` | categorical | `include_ground_cabin_event`, `include_multi_event`, `exclude_not_ground_or_cabin`, `exclude_insufficient_detail`, `exclude_duplicate`, `uncertain_needs_review`. |
| `primary_candidate_event_type` | categorical | Screening-level best guess. |
| `secondary_candidate_event_types` | semicolon list | Optional secondary record-level event types. |
| `possible_multi_event` | categorical/bool | Whether the record appears to contain multiple operational issues. |
| `author_verified` | boolean | `true` only after actual author/human review. |
| `verification_status` | categorical | `not_human_verified`, `author_verified_single_reviewer`, `external_human_verified`, `adjudicated`. |
| `reviewer` | string | `agent_prescreen`, `agent_silver_v0_2`, `parth_verified`, or similar. |
| `review_date` | date | ISO date. |

## Deferred Event-Level Extension Fields

These fields are not part of the active 5,000-record corpus. They define a possible future span-level extension only.

| Field | Type | Notes |
|---|---|---|
| `event_id` | string | Stable ID such as `ACN_EVENT_001`. |
| `acn` | string/int | ASRS ACN. |
| `source_person_index` | int/string | Which reporter narrative if multiple people are present. |
| `evidence_span` | text span | Short quoted or copied span from narrative/synopsis. Keep concise. |
| `evidence_source` | categorical | `synopsis`, `narrative`, `callback`, `multiple`. |
| `operational_phase` | categorical | See phase labels below. |
| `event_type` | categorical | See event-type labels below. |
| `actor` | categorical/string | Main actor if stated. |
| `object_or_asset` | categorical/string | Aircraft, towbar, tug, gate, jetway, battery, wheelchair, cargo, etc. |
| `location_context` | categorical/string | Gate, ramp, taxiway, runway, cargo hold, cabin, jetway, unknown. |
| `trigger_or_issue` | short text | What initiated the event. |
| `action_taken` | short text | Operational response. |
| `outcome` | short text | Delay, damage, no injury, return to gate, paperwork corrected, etc. |
| `severity_or_urgency` | categorical | `low`, `medium`, `high`, `unknown_or_not_stated`. |
| `ambiguity_flag` | categorical | `none`, `phase_ambiguous`, `actor_ambiguous`, `event_boundary_ambiguous`, `insufficient_detail`, `query_false_positive`. |
| `annotation_confidence` | categorical | `high`, `medium`, `low`. |
| `notes` | short text | Keep short and source-grounded. |

## Operational Phase Labels

Use one:

- `gate_pre_departure`
- `boarding`
- `deboarding`
- `jetway_or_gate_area`
- `ramp`
- `pushback`
- `towing`
- `taxi_out`
- `taxi_in`
- `runway_or_movement_area_ground`
- `cargo_or_baggage_loading`
- `fueling`
- `maintenance_pre_departure`
- `post_arrival_ground_handling`
- `unknown_or_ambiguous`

## Event-Type Labels

Use one primary event type:

- `hazmat_mobility_device`
- `passenger_assistance`
- `jetway_or_gate_infrastructure`
- `gate_or_boarding`
- `pushback_towing_chocks`
- `ramp_ground_handling`
- `baggage_cargo_weight_balance`
- `fueling`
- `maintenance_readiness`
- `dispatch_or_coordination`
- `cabin_service`
- `other_ground_operation`
- `not_relevant`

## Label Definitions

### `hazmat_mobility_device`

Wheelchair, mobility scooter, battery-powered assistive device, lithium/dry-cell/wet-cell battery, dangerous-goods notification, NOTOC/DG paperwork, or related loading/documentation.

Include:

- powered wheelchair battery documentation;
- battery loaded in cabin/cargo without correct paperwork;
- gate/ramp uncertainty about mobility-device handling.

Exclude:

- passenger illness or medical assistance unrelated to mobility-device handling.

### `pushback_towing_chocks`

Pushback, tug, towbar, towing, chocks, aircraft movement under ground-assist control.

Include:

- tug brake failure;
- towbar detachments;
- aircraft rolls after chocks removed;
- pushback clearance/communication failures.

Exclude:

- aircraft is towed after an airborne technical malfunction unless towing itself is described as the operational event.

### `jetway_or_gate_infrastructure`

Jetway, jet bridge, gate markings, lead-in lines, gate signage, gate-area walkways or physical infrastructure.

### `gate_or_boarding`

Boarding/deboarding flow, gate-agent interaction, armed door opened from outside, boarding ramp/stair use, door/boarding readiness.

### `ramp_ground_handling`

Ramp personnel, ground crew, GSE, ramp vehicle, marshalling, ramp communication, non-pushback ground-handling event.

### `baggage_cargo_weight_balance`

Baggage, cargo, load closeout, load sheet, weight-and-balance, ULD, cargo/bag handling.

### `fueling`

Fueling/refueling event, fuel truck, fuel spill/leak at gate/ramp, fueling infrastructure event.

### `maintenance_readiness`

Maintenance, mechanic, MEL, deferred item, aircraft swap, pre-departure maintenance readiness, maintenance release/documentation issue.

### `dispatch_or_coordination`

Dispatch/company/operations coordination when it is the main event, not merely background wording.

### `cabin_service`

Catering, cleaning, lavatory service, galley, trash, cabin readiness/service tasks during ground phase.

Do not use this label just because a flight attendant appears in the report.

### `other_ground_operation`

Ground movement or airport-surface event that is within ground operations but outside the narrower categories, such as taxiway/movement-area issues.

This category needs author decision:

- keep it if the paper scope is broad "ground operations";
- exclude it if the paper scope is narrowed to turnaround/ramp/cabin operations.

## Exclusion Guidance

Exclude if:

- the central event is airborne, en-route, cruise, approach, wake turbulence, cabin pressure/fumes, or technical malfunction with only incidental gate/ramp wording;
- `PRM` means Precision Runway Monitor rather than passenger reduced mobility;
- the record mentions gate only as destination arrival or debrief location;
- there is no operational event span that can be annotated.

## Required Quality Controls

Before model training on the current silver-corpus path:

1. Keep `verification_status=not_human_verified` for the original agent-only labels.
2. Create an annotation-ready event table from included records.
3. Run evidence-span availability checks.
4. Run duplicate and near-duplicate checks before splitting.
5. Run per-class false-positive audits and confidence distribution checks.
6. Report model scores as agreement with silver labels, not as accuracy against human ground truth.
7. Report AI assistance honestly if agent pre-screening or draft labels are used.

Required for current and future human-verification claims:

1. Use the derived author-verified file for the current benchmark, or create a future external-human-verified subset.
2. Record reviewer role, review date, schema version, and decision fields.
3. Preserve original agent labels separately from human-reviewed labels.
4. Use human-verification wording only for the verified layer or subset.
5. Avoid unqualified gold-standard wording unless independent verification/adjudication artifacts are disclosed clearly.

## Schema Decisions Still Open

1. Should `other_ground_operation` remain in scope?
2. Should `hazmat_mobility_device` remain a primary event type or be folded into passenger assistance / cargo handling?
3. Should final annotation include `secondary_event_type`, or should multi-event records be split into separate rows only?
4. How much raw narrative text can be released publicly, if any, under ASRS/NASA use constraints?
5. Will a future formal adjudication/disagreement subset be added, or will the submission remain author-verified with local consistency-audit support?
