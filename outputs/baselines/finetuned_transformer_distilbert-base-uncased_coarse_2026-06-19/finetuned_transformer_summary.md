# Fine-Tuned Transformer Baseline Summary

Created: 2026-06-19

Model: `distilbert-base-uncased` | Split: `expanded8800` | Seeds: [20260619, 20260620, 20260621] | Device: `cuda`

## Boundary

- Local fine-tuning. Raw ASRS narratives loaded locally and never written to outputs; only public model weights downloaded.
- Train = verified seed train + 3,800 agent-silver weak-label rows. Dev/test = author-verified reference rows only.
- DistilBERT/RoBERTa truncate at 512 word-pieces; use Longformer for long narratives.

## Aggregate test results (mean +/- std over seeds)

| task | model | split | n_seeds | n | accuracy | macro_f1 | micro_f1 |
|---|---|---|---:|---:|---|---|---|
| `screening_status` | `finetuned_distilbert_base_uncased_coarse` | test | 3 | 751 | 0.948069+/-0.003766 | 0.603626+/-0.004686 | 0.948069+/-0.003766 |
| `primary_event_type` | `finetuned_distilbert_base_uncased_coarse` | test | 3 | 751 | 0.806036+/-0.007239 | 0.791213+/-0.009629 | 0.806036+/-0.007239 |

## Interpretation

- Compare test macro_f1 against TF-IDF LinearSVC (current best) and supervised MiniLM.
- Report mean +/- std over seeds and the per-seed 1,000-sample bootstrap 95% CIs (metrics CSV).
- If the encoder does not beat TF-IDF, report that honestly as a benchmark finding.
