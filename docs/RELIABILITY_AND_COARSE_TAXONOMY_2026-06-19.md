# Label Reliability (Test–Retest) and Coarse Taxonomy — Findings, 2026-06-19

## Method
Author **blind re-annotation** (intra-annotator / test–retest) of a stratified
100-row sample of the held-out verified test set; n = 98 fully labelled. Reported as
author self-consistency, NOT independent inter-annotator agreement (no second human).

## Reliability results
| Task | n | % agreement | Cohen's κ | Reading |
|---|---:|---:|---:|---|
| Fine 12-class primary-event | 98 | 0.43 | 0.36 | "fair" — taxonomy too fine |
| Coarse 6-class primary-event | 98 | 0.58 | 0.47 | "moderate" |
| Screening / relevance (3-class) | 98 | 0.79 | 0.40 | "fair" (κ deflated by 84% prevalence) |
| Coarse event-type \| both-relevant | 66 | 0.68 | 0.55 | "moderate" |

Interpretation: the 12-class taxonomy was the weak point. Coarsening, and separating
the *relevance* judgment from *event typing*, gives a coherent two-stage story —
screening κ 0.40, and coarse event-type κ 0.55 once both passes agree the record is a
relevant ground/cabin event. The residual disagreement is concentrated at the
relevance boundary (records re-judged `not_relevant`), not within event typing.

## Coarse 6-class scheme (from the test–retest confusion structure)
- `not_relevant`
- `hazmat_mobility_device`
- `maintenance_readiness`
- `baggage_cargo`  ← baggage_cargo_weight_balance
- `cabin_gate_passenger`  ← cabin_service + gate_or_boarding + jetway_or_gate_infrastructure
- `ramp_servicing`  ← pushback_towing_chocks + ramp_ground_handling + other_ground_operation + fueling + dispatch_or_coordination

(Encoded as `COARSE_PRIMARY` in `scripts/run_finetuned_transformer_baseline.py`; use `--coarse`.)

## Coarse-task model performance — PREVIEW only
Remapped from the saved fine-grained predictions (single seed); NOT a coarse retrain.
| Model | accuracy | macro-F1 |
|---|---:|---:|
| RoBERTa-base | 0.816 | 0.798 |
| DistilBERT | 0.796 | 0.773 |
| TF-IDF LinearSVC | 0.672 | 0.640 |

## Honesty / limitations (state these in the paper)
- Intra-annotator (test–retest), single annotator — not independent multi-annotator IAA.
- κ are moderate (0.40–0.55), not high; report them as a transparent reliability bound, not as proof of gold-quality labels.
- The rare `uncertain_needs_review` class (2/751) did not fall in the sample; screening reliability reflects include vs exclude.
- The coarse model numbers above are a remap PREVIEW; definitive numbers require training on coarse labels (`--coarse`).

## Next step
Definitive coarse-task numbers via `--coarse` retrain (RoBERTa + DistilBERT, 3 seeds),
then finalise the results table and a reliability paragraph.
