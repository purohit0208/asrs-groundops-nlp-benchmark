# Fine-Tuned Transformer Baseline Summary

Created: 2026-06-19

Model: `roberta-base` | Split: `expanded8800` | Seeds: [20260619, 20260620, 20260621] | Device: `cuda`

## Boundary

- Local fine-tuning. Raw ASRS narratives loaded locally and never written to outputs; only public model weights downloaded.
- Train = verified seed train + 3,800 agent-silver weak-label rows. Dev/test = author-verified reference rows only.
- DistilBERT/RoBERTa truncate at 512 word-pieces; use Longformer for long narratives.

## Aggregate test results (mean +/- std over seeds)

| task | model | split | n_seeds | n | accuracy | macro_f1 | micro_f1 |
|---|---|---|---:|---:|---|---|---|
| `screening_status` | `finetuned_roberta_base` | test | 3 | 751 | 0.948513+/-0.003818 | 0.605746+/-0.005132 | 0.948513+/-0.003818 |
| `primary_event_type` | `finetuned_roberta_base` | test | 3 | 751 | 0.778961+/-0.008698 | 0.745246+/-0.007516 | 0.778961+/-0.008698 |

## Interpretation

- Compare test macro_f1 against TF-IDF LinearSVC (current best) and supervised MiniLM.
- Report mean +/- std over seeds and the per-seed 1,000-sample bootstrap 95% CIs (metrics CSV).
- If the encoder does not beat TF-IDF, report that honestly as a benchmark finding.
