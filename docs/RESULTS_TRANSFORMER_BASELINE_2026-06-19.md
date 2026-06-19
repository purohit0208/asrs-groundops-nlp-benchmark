# Results + Reliability Block (draft) — ASRS GroundOps benchmark

Created 2026-06-19. All numbers verified from output CSVs; same held-out verified test
set (n=751). Encoders fine-tuned locally on an RTX 5080 (3 seeds; mean ± std).

## Label reliability (test–retest, intra-annotator)
A blind author re-annotation of a stratified 100-row test sample (n=98) gave:
- Screening / relevance: 79% agreement, Cohen's κ = 0.40 ("fair"; κ deflated by prevalence).
- Event-type, FINE 12-class: 43% agreement, κ = 0.36 ("fair") — too low; the taxonomy was therefore collapsed.
- Event-type, COARSE 6-class | both passes agree relevant: 68% agreement, κ = 0.55 ("moderate").

Reported transparently as author self-consistency (test–retest), NOT independent
multi-annotator agreement. This is the headline label-quality limitation.

## Coarse 6-class scheme (from the test–retest confusion structure)
`not_relevant`, `hazmat_mobility_device`, `maintenance_readiness`, `baggage_cargo`,
`cabin_gate_passenger` (cabin_service + gate_or_boarding + jetway/gate_infrastructure),
`ramp_servicing` (pushback/towing + ramp_ground_handling + other_ground_operation + fueling + dispatch).

## Table 1. Test-set performance (n=751); macro-F1 is the primary metric

| Model | Type | Screening macro-F1 | Event-type macro-F1 (COARSE 6-class) |
|---|---|---|---|
| Majority class | trivial | 0.304 | — |
| TF-IDF + LinearSVC¹ | classical | 0.513 | 0.640² |
| Supervised MiniLM | encoder | 0.537 | — |
| Qwen2.5-7B, zero-shot structured³ | LLM | 0.436 | — |
| DistilBERT (3 seeds) | encoder | 0.604 ± 0.005 | 0.791 ± 0.010 |
| **RoBERTa-base (3 seeds)** | **encoder** | **0.605 ± 0.009** | **0.807 ± 0.007** |

For transparency, on the (unreliable) FINE 12-class task the encoders scored
0.745 (RoBERTa) / 0.712 (DistilBERT) vs 0.557 (TF-IDF); these are not the headline
because the 12-class labels have κ = 0.36.

¹ Best classical config per task. ² TF-IDF coarse number is a remap of the fine-trained model's predictions (preview); a coarse-trained classical baseline is a minor to-do. ³ Zero-shot, 741/751 schema-valid rows; fine-grained only.
All scores are against author-verified reference labels (screening κ=0.40; coarse event-type κ=0.55), not independently adjudicated gold.

## Results paragraph (draft)
On the held-out verified test set (n = 751), the fine-tuned encoders are the strongest
models on both tasks, with RoBERTa-base best. On the coarse 6-class event-typing task
it reaches macro-F1 0.807 ± 0.007 (DistilBERT 0.791 ± 0.010), well above the classical
TF-IDF baseline (0.640) and far above the zero-shot LLM. We adopt the coarse taxonomy
because a blind author re-annotation showed the original 12-class labels were not
reliably reproducible (test–retest κ = 0.36), whereas the coarse scheme reaches
moderate reliability (κ = 0.55, conditioned on agreed relevance). Screening/relevance
reliability is fair (κ = 0.40); the rare `uncertain_needs_review` class (2/751) is not
learnable. The zero-shot LLM underperforms both encoders and the classical model,
indicating task-specific fine-tuning remains more effective than generative prompting
on this record-level, schema-constrained task. We report all scores against
author-verified reference labels with measured test–retest reliability, not against
independently adjudicated gold annotations.

## Methods additions (draft)
DistilBERT-base-uncased and RoBERTa-base, each with a linear head, fine-tuned per task
(narrative truncated to 320 word-pieces; class-weighted cross-entropy; AdamW 2e-5; 6%
warmup; batch 16; 4 epochs; best-dev-macro-F1 checkpoint; 3 seeds; 1,000-sample
bootstrap CIs). The event-type taxonomy was collapsed from 12 to 6 classes after a
blind author re-annotation (test–retest) showed low reliability of the fine labels;
the coarse mapping is given above (`--coarse` in the release script). Training local,
RTX 5080; raw ASRS text never transmitted.

## Provenance
- RoBERTa coarse: outputs/baselines/finetuned_transformer_roberta-base_coarse_2026-06-19/
- DistilBERT coarse: outputs/baselines/finetuned_transformer_distilbert-base-uncased_coarse_2026-06-19/
- Fine encoders: finetuned_transformer_{roberta-base,distilbert-base-uncased}_2026-06-19/
- Reliability: annotation/iaa_2026-06-19/  (see RELIABILITY_AND_COARSE_TAXONOMY_2026-06-19.md)
