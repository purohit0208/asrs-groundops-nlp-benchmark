---
type: protocol
domain: aviation-nlp
status: v0.1
created: 2026-06-02
tags:
  - asrs
  - data-protocol
  - query-protocol
---

# ASRS Access And Query Protocol

## Purpose

Build a reproducible candidate corpus of NASA ASRS records for a public aviation NLP benchmark on ground-operation and cabin-service event extraction.

This protocol is designed for candidate discovery and screening, not for prevalence estimation.

## Official ASRS Source Rules

Official pages checked on 2026-06-02:

- ASRS Database Online: https://asrsdbol.arc.nasa.gov/
- ASRS search strategies: https://asrs.arc.nasa.gov/search/dbol/strategies.html
- ASRS data caveats: https://asrs.arc.nasa.gov/search/dbol/aboutdata.html
- ASRS data requests: https://asrs.arc.nasa.gov/search/requesting.html

Relevant official constraints:

- ASRS records are de-identified before entering the incident database.
- Multiple reports about one incident can be combined into one database record.
- ASRS data are voluntary "soft data" and subject to self-reporting bias.
- NASA ASRS does not verify or validate report details.
- ASRS records cannot be used to infer prevalence of a problem in the National Airspace System.
- ASRS Database Online includes records from 1988 to current and is updated monthly.
- The ASRS search page recommends iterative searching, broad initial searches, and saving final strategies/ACN lists.
- Text search supports operators such as `AND`, `OR`, `NEAR`, `NOT`, phrase quotes, and wildcard `%`.

## Time Window

Working initial window:

`2011-01-01` to `2025-12-31`

Rationale:

- Dou et al. (2024) used 2011-2021 partly because ASRS moved from abbreviated text to full-length narrative format in 2009.
- Using complete calendar years avoids partial-2026 update ambiguity.
- The window remains broad enough for ground/cabin/ramp event discovery.

If the ASRS interface does not support exact date filtering in the needed export path, record the available date/year metadata and filter after export.

## Search Strategy

Use iterative searches. Do not rely on one giant query.

For each query:

1. Record exact query text.
2. Record fixed-field filters used.
3. Record result count.
4. Export available fields to CSV/XLS/DOC if possible.
5. Save ACN list.
6. Add query metadata to `data\manifests\query_log.csv`.

## Candidate Query Groups

These text expressions are starting points. They must be tested in ASRS Database Online and refined based on returned counts and relevance.

### Q01 - Cabin Service

```text
((CABIN OR "FLIGHT ATTENDANT" OR FA OR PAX OR PASSENGER) AND (CLEAN% OR CATER% OR LAV% OR "CABIN SERVICE" OR GALLEY OR TRASH))
```

Purpose:

- cabin service, cleaning, catering, lavatory, galley, passenger/cabin context.

Risk:

- may retrieve in-flight cabin events not related to ground operations.

### Q02 - Passenger Assistance / Wheelchair / PRM

```text
((WHEELCHAIR OR "WHEEL CHAIR" OR PRM OR "PASSENGER ASSIST%" OR "SPECIAL ASSIST%" OR MOBILITY) AND (BOARD% OR DEBOARD% OR GATE OR RAMP OR "JET BRIDGE" OR JETWAY))
```

Purpose:

- passenger assistance events around boarding, deboarding, gate, jet bridge, and ramp.

Risk:

- PRM may not be common ASRS terminology; keep wheelchair variants.

### Q03 - Gate / Boarding / Deboarding

```text
((GATE OR "JET BRIDGE" OR JETWAY OR BOARD% OR DEBOARD%) AND (DELAY% OR HOLD% OR "NOT READY" OR WAIT% OR MISSING OR BOARDING))
```

Purpose:

- gate readiness, boarding/deboarding coordination, waiting/missing-resource situations.

Risk:

- broad query; requires relevance screening.

### Q04 - Ramp / Ground Handling / Pushback

```text
((RAMP OR "GROUND CREW" OR "GROUND PERSONNEL" OR "GROUND HANDLING" OR "RAMP AGENT") AND (TUG OR TOW% OR PUSHBACK OR "PUSH BACK" OR CHOCK% OR MARSHAL% OR WAND OR "GROUND EQUIPMENT" OR GSE))
```

Purpose:

- ramp, pushback/towing, chocks, marshalling, ground equipment.

Grounding:

- Muecklich et al. (2023) identify pushback/towing and arrival/departure preparation as critical ground-operation areas.

### Q05 - Baggage / Cargo / Weight And Balance

```text
((BAGGAGE OR BAG OR CARGO OR LOAD% OR ULD OR "WEIGHT AND BALANCE" OR "WT AND BAL") AND (RAMP OR GATE OR BOARD% OR LOAD%))
```

Purpose:

- baggage/cargo loading, unit load device, weight-and-balance, ground loading context.

Grounding:

- Muecklich et al. (2023) identify weight and balance as a critical action area.

### Q06 - Fueling

```text
((FUEL OR FUEL% OR REFUEL% OR "FUEL TRUCK") AND (RAMP OR GATE OR DELAY% OR SPILL% OR FUELING))
```

Purpose:

- fueling/refueling events in ramp/gate context.

Risk:

- fuel appears in many non-ground contexts; screen carefully.

### Q07 - Maintenance Readiness At Gate/Ramp

```text
((MAINT% OR MEL OR "MINIMUM EQUIPMENT LIST" OR DEFECT OR DEFER% OR "AIRCRAFT SWAP") AND (GATE OR RAMP OR BOARD% OR CABIN OR PASSENGER OR "BEFORE DEPARTURE" OR PREFLIGHT OR "PRE FLIGHT"))
```

Purpose:

- maintenance readiness and defect handling around gate, ramp, cabin, boarding, preflight.

Risk:

- overlaps with general maintenance ASRS literature; keep only records with ground/cabin/readiness relevance.

### Q08 - Dispatch / Operations Coordination

```text
((DISPATCH OR "OPERATIONS" OR "OPERATION CONTROL" OR COMPANY OR COORDINAT% OR COMMUNICAT%) AND (GATE OR RAMP OR BOARD% OR PUSHBACK OR MAINT% OR FUEL%))
```

Purpose:

- coordination failures across dispatch, company operations, gate, ramp, maintenance, fueling.

Risk:

- very broad; likely needs narrowing with `NEAR`.

## Optional NEAR Queries

If broad queries return too many irrelevant records, use proximity variants:

```text
NEAR((GATE, BOARD%),10)
NEAR((RAMP, PUSHBACK),15)
NEAR((WHEELCHAIR, BOARD%),20)
NEAR((MAINT%, GATE),20)
NEAR((FUEL%, RAMP),20)
NEAR((BAGGAGE, LOAD%),15)
```

## Inclusion Criteria

Include a record if the narrative or analyst synopsis contains at least one ground-operation or cabin-service occurrence involving:

- gate operation;
- boarding or deboarding;
- cabin service or cabin readiness;
- passenger assistance during ground phase;
- ramp operation;
- ground handling;
- pushback, towing, chocking, marshalling, de-icing, or GSE interaction;
- baggage/cargo/weight-and-balance ground handling;
- fueling/refueling at gate or ramp;
- maintenance readiness or defect handling in gate/ramp/pre-departure/post-arrival context;
- dispatch/company/ground coordination related to aircraft readiness or ground operation.

## Exclusion Criteria

Exclude a record if:

- it is only an en-route, cruise, approach, airborne ATC, or cockpit procedural issue with no ground/cabin/ramp relevance;
- it is only weather/ATC delay with no aircraft-side ground operation or cabin-service event;
- it is only passenger behavior in flight without ground-operation relevance;
- it only concerns aircraft technical malfunction with no gate/ramp/pre-departure/post-arrival readiness connection;
- it lacks enough narrative detail to identify a ground/cabin occurrence;
- it duplicates an already included ACN.

## Screening Labels

Use these screening labels:

- `include_ground_cabin_event`
- `include_multi_event`
- `exclude_not_ground_or_cabin`
- `exclude_insufficient_detail`
- `exclude_duplicate`
- `uncertain_needs_review`

## Candidate Event Types

Initial event types for screening:

- `cabin_service`
- `passenger_assistance`
- `gate_or_boarding`
- `ramp_ground_handling`
- `pushback_towing_chocks`
- `baggage_cargo_weight_balance`
- `fueling`
- `maintenance_readiness`
- `dispatch_or_coordination`
- `other_ground_operation`
- `not_relevant`

These are screening-level categories. The annotation schema may refine them after pilot review.

## Sampling Plan

Target candidate pool:

- 1,000 to 2,000 candidate records after de-duplication.

Pilot screen:

- Screen at least 200 candidate records first.
- Track relevance by query group.
- Drop or narrow query groups with poor precision.

Annotation target:

- 5,000 record-level reference labels for the current benchmark.
- If one record has multiple distinct operational issues, keep one record and mark secondary labels or `possible_multi_event`; do not split into event-span or event-mention rows unless a separate span-level protocol is created.

Balanced-sampling rule:

- Do not treat query frequency as prevalence.
- Oversample low-frequency but scientifically relevant event types so the benchmark is useful.

## Release Policy v0.1

Conservative release plan:

- release query protocol;
- release query logs;
- release ACNs/record IDs where allowed;
- release labels and annotation schema;
- release scripts and environment;
- do not redistribute raw ASRS narrative text until ASRS/NASA use and redistribution terms are confirmed.

Manuscript wording:

> The benchmark uses public, de-identified ASRS records and reports results as extraction performance on the sampled corpus. It does not estimate event prevalence and does not validate operational deployment.

## Output Files

Create/update:

- `data\manifests\query_log.csv`
- `data\manifests\candidate_records_manifest.csv`
- `data\manifests\screening_manifest.csv`
- `data\raw\README_RAW_DATA.md`
- `data\processed\README_PROCESSED_DATA.md`

## API Status Update - 2026-06-02

The public ASRS DBOL web interface was inspected with browser automation and direct API calls.

Observed public endpoints:

- `GET https://asrsdbol.arc.nasa.gov/dbol/reference/`
- `POST https://asrsdbol.arc.nasa.gov/dbol/search/`
- `POST https://asrsdbol.arc.nasa.gov/dbol/details/`

Direct API access works without a login for the current public interface. The successful `dbol/search/` payload and workflow are documented in:

`protocols\ASRS_API_ACCESS_NOTES.md`

Local reproducibility script:

`scripts\asrs_api_workflow.py`

Generated candidate pool:

- Q02 passenger assistance / wheelchair / PRM: 216 records kept after 2011-2025 date filtering.
- Q04 ramp / ground handling / pushback: 2,692 records kept after 2011-2025 date filtering.
- Combined deduplicated pool: 2,899 unique ACNs.
- Pilot screening sample: 200 records in `data\manifests\screening_manifest.csv`.

The remaining broad queries should be refined after pilot screening rather than bulk-collected immediately.

## Stop Conditions

Stop and revise if:

- ASRS export cannot provide enough candidate records;
- raw narrative redistribution constraints block the intended release model;
- query precision is too low after two refinement rounds;
- the resulting corpus overlaps too strongly with delay-only ASRS work;
- the selected records are mostly non-ground/non-cabin safety reports.
