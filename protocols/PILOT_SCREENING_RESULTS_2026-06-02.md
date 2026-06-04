---
type: screening_result
domain: aviation-nlp
status: agent_prescreen_complete
created: 2026-06-02
tags:
  - asrs
  - screening
  - pilot
---

# Pilot Screening Results - Agent Pre-Screen

## Boundary

This is an agent pre-screening result, not final human annotation.

The active file is:

`data\manifests\screening_manifest.csv`

Every row currently has:

- `reviewer = agent_prescreen`
- `review_date = 2026-06-02`

Before manuscript submission or model-training use, the labels should be author-verified and the verification status should be recorded.

## Input

Pilot sample:

`data\manifests\pilot_screening_sample_200_2026-06-02.csv`

Raw files:

- `data\raw\asrs_api\Q02_details_2026-06-02.json`
- `data\raw\asrs_api\Q04_details_2026-06-02.json`

Pre-screen script:

`scripts\pilot_prescreen.py`

## Result Counts

| Screening status | Count |
|---|---:|
| `include_ground_cabin_event` | 181 |
| `exclude_not_ground_or_cabin` | 19 |

| Primary candidate event type | Count |
|---|---:|
| `hazmat_mobility_device` | 63 |
| `pushback_towing_chocks` | 50 |
| `other_ground_operation` | 22 |
| `not_relevant` | 19 |
| `gate_or_boarding` | 15 |
| `ramp_ground_handling` | 12 |
| `baggage_cargo_weight_balance` | 8 |
| `maintenance_readiness` | 5 |
| `jetway_or_gate_infrastructure` | 4 |
| `dispatch_or_coordination` | 1 |
| `fueling` | 1 |

Potential event-splitting review:

- `multi_event_flag = false`: 137
- `multi_event_flag = needs_author_review`: 63

## Interpretation

Q02 and Q04 are useful candidate-source queries:

- The pre-screen relevance rate is 181 / 200, or 90.5%.
- The candidate pool is strong enough to continue, but it is concentrated in two clusters:
  - mobility-device / battery / hazmat-documentation handling;
  - pushback / towing / chocking / ramp-control events.

The sample is not yet balanced enough for the final benchmark.

## Query Lessons

1. Keep Q02, but treat `PRM` carefully.
   - In ASRS, `PRM` can mean Precision Runway Monitor, not passenger reduced mobility.
   - Future query revisions should avoid `PRM` by itself or pair it with passenger/wheelchair context.

2. Keep Q04 as a high-value ramp/pushback query.
   - It retrieves many relevant pushback, tug, towbar, chock, and ramp-communication events.
   - It also retrieves some technical/airborne events where towing or gate handling appears only as an outcome; these should be screened out.

3. Add one or two underrepresented query families before full annotation:
   - Q01 cabin service, probably narrowed to catering/cleaning/lavatory/galley and ground phase;
   - a narrower Q06 fueling query;
   - a narrower Q07 maintenance-readiness-at-gate query.

## Annotation Implications

The event schema should preserve `hazmat_mobility_device` at least during pilot annotation. It may later be merged into passenger assistance or baggage/cargo handling, but early evidence shows it is a recurring, operationally distinct ASRS cluster.

The schema also needs:

- `jetway_or_gate_infrastructure`;
- `other_ground_operation`, probably for taxiway/movement-area events;
- an explicit `not_relevant` screening class;
- an `event_split_required` flag for records with more than one candidate event.

## Next Gate

This pilot gate has been superseded by the 2026-06-03 expanded-corpus work.

Current status:

1. P3 is complete.
2. Q09-Q12 were added as underrepresented query families.
3. The final working corpus is now 5,000 records sampled from an 8,801-record expanded candidate pool.
4. The user/author reported verifying the 5,000-row label file; a derived `author_verified_single_reviewer` file and cross-audit report were created on 2026-06-03.
5. The remaining open scope issue is whether `other_ground_operation` belongs in the final benchmark or should be excluded to keep the paper closer to turnaround/ramp/cabin operations.
