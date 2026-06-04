# Record-Level Baseline Error Analysis

Created: 2026-06-04

## Boundary

This analysis uses prediction outputs and split metadata only. It does not export full ASRS narratives. Evidence snippets are the short fields already present in the split files.

Rule-reproduction rows are excluded because they are label-consistency checks, not independent baselines.

## Error Counts By Task, Model, And Split

| task | model | split | errors |
|---|---|---:|---:|
| `primary_event_type` | `tfidf_char35_logreg_balanced` | `dev` | 314 |
| `primary_event_type` | `tfidf_char35_logreg_balanced` | `test` | 349 |
| `primary_event_type` | `tfidf_word12_logreg_balanced` | `dev` | 327 |
| `primary_event_type` | `tfidf_word12_logreg_balanced` | `test` | 350 |
| `screening_status` | `tfidf_char35_logreg_balanced` | `dev` | 95 |
| `screening_status` | `tfidf_char35_logreg_balanced` | `test` | 96 |
| `screening_status` | `tfidf_word12_logreg_balanced` | `dev` | 97 |
| `screening_status` | `tfidf_word12_logreg_balanced` | `test` | 91 |

## Main Findings

- Screening-status errors are dominated by confusion between `include_ground_cabin_event` and `exclude_not_ground_or_cabin`; the rare `uncertain_needs_review` class is not learned by TF-IDF because only two test rows exist.
- Primary-event-type classification is much harder than screening. Stronger classes include `hazmat_mobility_device`, `pushback_towing_chocks`, and `other_ground_operation`; weak classes include `jetway_or_gate_infrastructure`, `dispatch_or_coordination`, `cabin_service`, and small support classes.
- Many errors occur in rows flagged as possible multi-event records, so event-level conversion or multi-label treatment is likely needed before claiming fine-grained extraction performance.

## Top Confusions

### `screening_status`

- `exclude_not_ground_or_cabin` -> `include_ground_cabin_event`: 107
- `include_ground_cabin_event` -> `exclude_not_ground_or_cabin`: 76
- `uncertain_needs_review` -> `include_ground_cabin_event`: 4

### `primary_event_type`

- `baggage_cargo_weight_balance` -> `not_relevant`: 40
- `maintenance_readiness` -> `not_relevant`: 35
- `ramp_ground_handling` -> `pushback_towing_chocks`: 28
- `other_ground_operation` -> `not_relevant`: 24
- `baggage_cargo_weight_balance` -> `maintenance_readiness`: 24
- `not_relevant` -> `gate_or_boarding`: 21
- `pushback_towing_chocks` -> `maintenance_readiness`: 18
- `baggage_cargo_weight_balance` -> `other_ground_operation`: 16
- `ramp_ground_handling` -> `other_ground_operation`: 15
- `gate_or_boarding` -> `not_relevant`: 15
- `ramp_ground_handling` -> `gate_or_boarding`: 15
- `baggage_cargo_weight_balance` -> `hazmat_mobility_device`: 14

## Recommended Next Model Step

Run an encoder-transformer or sentence-embedding baseline next. The primary-event-type TF-IDF ceiling is only about 0.47 macro F1 on test, and the confusion profile suggests contextual language representation may help with broad classes such as maintenance readiness, baggage/cargo, and ramp/ground-handling. LLM structured extraction should wait until after one stronger non-LLM baseline is available.
