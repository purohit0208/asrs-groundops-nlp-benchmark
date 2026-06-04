---
type: protocol
domain: aviation-nlp
status: v0.1
created: 2026-06-02
tags:
  - asrs
  - screening
  - annotation
---

# Pilot Screening Protocol

## Purpose

Screen the first 200 ASRS candidate records for relevance before hardening the annotation schema.

Active screening manifest:

`data\manifests\screening_manifest.csv`

Raw source files:

- `data\raw\asrs_api\Q02_details_2026-06-02.json`
- `data\raw\asrs_api\Q04_details_2026-06-02.json`

## Screening Boundary

Screening is a relevance decision, not final annotation.

Do not use screening labels as final model-training labels unless they are later converted into record-level reference labels under a separate annotation guideline.

## AI-Assisted Work Boundary

Agent pre-screening may be used to accelerate triage, but it must be recorded as agent pre-screening.

For manuscript-grade reference labels:

- final labels should be author-verified;
- AI assistance should be disclosed if used for screening or annotation;
- do not describe labels as purely manual human labels if they are only AI-generated;
- keep an audit column or log showing which records were author-verified.

Recommended column convention:

- `reviewer = agent_prescreen` for AI triage;
- `reviewer = parth_verified` for author-verified labels;
- `reviewer = parth_primary_agent_assisted` only if the author actively verifies and edits agent suggestions record by record.

## Screening Labels

Use `screening_status` values:

- `include_ground_cabin_event`
- `include_multi_event`
- `exclude_not_ground_or_cabin`
- `exclude_insufficient_detail`
- `exclude_duplicate`
- `uncertain_needs_review`

## Event-Type Candidates

Use `primary_candidate_event_type` values:

- `cabin_service`
- `passenger_assistance`
- `gate_or_boarding`
- `ramp_ground_handling`
- `pushback_towing_chocks`
- `baggage_cargo_weight_balance`
- `fueling`
- `maintenance_readiness`
- `dispatch_or_coordination`
- `jetway_or_gate_infrastructure`
- `hazmat_mobility_device`
- `other_ground_operation`
- `not_relevant`

`hazmat_mobility_device` is included because early Q02 inspection showed many wheelchair/mobility-device battery paperwork records. This may later be merged into passenger assistance, baggage/cargo, or safety-documentation depending on pilot findings.

## Inclusion Rule

Include if the record contains at least one ground-operation or cabin-service occurrence involving:

- ground operation;
- gate, boarding, or deboarding;
- cabin readiness or cabin-service task;
- passenger assistance during ground phase;
- wheelchair/mobility-device handling, documentation, loading, or battery safety;
- ramp, pushback, tug, towing, chocking, marshalling, GSE, or ground personnel;
- dispatch/company/ground coordination directly tied to aircraft readiness or ground operation.

## Exclusion Rule

Exclude if the record is only:

- en-route, cruise, approach, ATC, airborne weather, or cockpit procedural content;
- routine passenger behavior without ground/cabin-service relevance;
- a technical malfunction without gate/ramp/pre-departure/post-arrival readiness relevance;
- too sparse to identify a ground/cabin occurrence;
- a duplicate ACN already screened.

## Evidence Columns

Use:

- `ground_phase_evidence`: short phrase from synopsis/narrative showing ground-phase relevance.
- `cabin_or_service_evidence`: short phrase showing cabin/passenger/service relevance where applicable.
- `notes`: short ambiguity or schema note.

Do not paste long narrative passages into the screening manifest.

## Exit Gate

P3 pilot screening is complete when:

- all 200 records in `screening_manifest.csv` have a non-empty `screening_status`;
- at least 150 records are confidently include/exclude rather than uncertain;
- recurring ambiguity patterns are summarized;
- annotation schema v0.2 is updated based on pilot findings;
- author verification status is clear.

## Status Update - 2026-06-02

Agent pre-screening has been completed for all 200 pilot records.

Result note:

`protocols\PILOT_SCREENING_RESULTS_2026-06-02.md`

Active screening file:

`data\manifests\screening_manifest.csv`

Current boundary:

- all 200 rows are agent-pre-screened;
- 181 rows are likely relevant;
- 19 rows are likely not ground/cabin relevant;
- final labels still require author verification before manuscript-grade use.
