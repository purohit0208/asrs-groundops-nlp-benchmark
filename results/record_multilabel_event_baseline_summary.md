# Record-Level Multi-Label Event Baseline Summary

Created: 2026-06-03

## Boundary

This baseline treats each included ASRS record as a set of event-type labels assembled from `silver_primary_event_type` plus `silver_secondary_event_types`. It does not create event spans and must not be described as event-mention extraction. Full raw ASRS narratives are loaded locally and are not written to output files.

## Relevant-Record Split Counts

- `train`: 2941
- `dev`: 631
- `test`: 631

## Label Counts In Training Set

| label | count |
|---|---:|
| `maintenance_readiness` | 936 |
| `baggage_cargo_weight_balance` | 873 |
| `pushback_towing_chocks` | 707 |
| `dispatch_or_coordination` | 663 |
| `ramp_ground_handling` | 523 |
| `hazmat_mobility_device` | 412 |
| `other_ground_operation` | 355 |
| `gate_or_boarding` | 296 |
| `fueling` | 271 |
| `cabin_service` | 195 |
| `jetway_or_gate_infrastructure` | 110 |

## Metrics

| split | n | label_count | subset_accuracy | micro_f1 | macro_f1 | samples_f1 | samples_jaccard | hamming_loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `dev` | 631 | 11 | 0.377179 | 0.651209 | 0.590911 | 0.650741 | 0.581171 | 0.101859 |
| `test` | 631 | 11 | 0.297940 | 0.609258 | 0.554028 | 0.595244 | 0.517270 | 0.113096 |

## Interpretation

- This is the manuscript-safe alternative for multi-event records until event-span annotation exists.
- Use these scores to discuss record-level multi-label tagging, not event-level extraction.
- Compare with primary-event single-label metrics to show why multi-event handling matters.
