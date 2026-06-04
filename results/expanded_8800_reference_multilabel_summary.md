# Expanded 8,800 Reference-Evaluation Multi-Label Baseline Summary

Created: 2026-06-04

## Boundary

This is record-level multi-label event tagging from primary plus secondary labels. Train includes the expanded weak-label rows; dev/test remain verified reference rows. It is not event-span extraction.

## Relevant-Record Split Counts

- `train`: 6218
- `dev`: 631
- `test`: 631

## Relevant Training Role Counts

- `expanded_3800_agent_silver`: 3277
- `seed_5000_author_verified_local_audit`: 2941

## Label Counts In Relevant Training Set

| label | count |
|---|---:|
| `baggage_cargo_weight_balance` | 1824 |
| `maintenance_readiness` | 1822 |
| `pushback_towing_chocks` | 1730 |
| `dispatch_or_coordination` | 1321 |
| `ramp_ground_handling` | 1121 |
| `hazmat_mobility_device` | 807 |
| `other_ground_operation` | 757 |
| `gate_or_boarding` | 621 |
| `cabin_service` | 354 |
| `fueling` | 284 |
| `jetway_or_gate_infrastructure` | 250 |

## Metrics

| split | n | label_count | subset_accuracy | micro_f1 | macro_f1 | samples_f1 | samples_jaccard | hamming_loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `dev` | 631 | 11 | 0.386688 | 0.667950 | 0.622043 | 0.671920 | 0.598593 | 0.099409 |
| `test` | 631 | 11 | 0.316957 | 0.633286 | 0.598366 | 0.614213 | 0.537292 | 0.110791 |

## Interpretation Boundary

- Use this as the expanded-training multi-label result against verified dev/test labels.
- Do not call it event-span or event-mention extraction.
