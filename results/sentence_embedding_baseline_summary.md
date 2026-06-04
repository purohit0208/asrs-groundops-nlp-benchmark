# Sentence-Embedding Baseline Summary

Created: 2026-06-03

## Boundary

This is a frozen sentence-embedding baseline using `sentence-transformers/all-MiniLM-L6-v2` plus balanced logistic regression. It is not fine-tuned. Full raw ASRS narratives are loaded locally and are not written to output files.

## Metrics

| task | model | split | n | accuracy | macro_f1 | weighted_f1 | micro_f1 |
|---|---|---:|---:|---:|---:|---:|---:|
| `screening_status` | `sbert_all_minilm_l6v2_logreg_balanced` | `dev` | 750 | 0.789333 | 0.552780 | 0.813571 | 0.789333 |
| `screening_status` | `sbert_all_minilm_l6v2_logreg_balanced` | `test` | 751 | 0.786951 | 0.470314 | 0.811418 | 0.786951 |
| `primary_event_type` | `sbert_all_minilm_l6v2_logreg_balanced` | `dev` | 750 | 0.524000 | 0.463724 | 0.539763 | 0.524000 |
| `primary_event_type` | `sbert_all_minilm_l6v2_logreg_balanced` | `test` | 751 | 0.492676 | 0.436172 | 0.506805 | 0.492676 |

## Interpretation

- Compare these results against TF-IDF as the first non-generative neural representation baseline.
- Do not interpret scores as event-mention extraction performance; this is still record-level classification.
