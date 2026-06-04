# Supervised MiniLM Baseline Summary

Created: 2026-06-03

## Boundary

This is a local CPU fine-tuning baseline using the cached `sentence-transformers/all-MiniLM-L6-v2` checkpoint with a classification head. Full raw ASRS narratives are loaded locally and are not written to output files. No Hugging Face remote job, hosted inference call, or paid API is used.

## Metrics

| task | model | split | epoch | n | accuracy | macro_f1 | weighted_f1 | micro_f1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `screening_status` | `supervised_minilm_l6v2_local_finetune` | `dev` | `best_dev_epoch_2` | 750 | 0.881333 | 0.536955 | 0.886755 | 0.881333 |
| `screening_status` | `supervised_minilm_l6v2_local_finetune` | `test` | `best_dev_epoch_2` | 751 | 0.888149 | 0.536756 | 0.890488 | 0.888149 |
| `primary_event_type` | `supervised_minilm_l6v2_local_finetune` | `dev` | `best_dev_epoch_2` | 750 | 0.545333 | 0.446321 | 0.503411 | 0.545333 |
| `primary_event_type` | `supervised_minilm_l6v2_local_finetune` | `test` | `best_dev_epoch_2` | 751 | 0.505992 | 0.408335 | 0.462481 | 0.505992 |

## Interpretation

- Treat this as the first supervised encoder baseline, not as a final multi-seed transformer study.
- Compare against TF-IDF LinearSVC before deciding whether additional GPU/multi-seed fine-tuning is justified.
- Do not interpret record-level scores as full event-mention extraction performance.
