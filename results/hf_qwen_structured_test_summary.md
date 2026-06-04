# Hugging Face Qwen Structured Baseline Summary

Created: 2026-06-04

## Boundary

This run sends raw ASRS text to Hugging Face Inference Providers under the approval recorded in `protocols/EXPANDED_8800_CORPUS_AND_REMOTE_LLM_DECISION.md`. Output files do not store raw prompts, raw ASRS text, or raw model responses.

- Model: `Qwen/Qwen2.5-7B-Instruct:cheapest`
- Base model for report: `Qwen/Qwen2.5-7B-Instruct`
- Split file: `data\splits\expanded_8800_reference_eval_test_records_2026-06-04.csv`
- Completed rows in prediction file: 751
- Valid JSON rows: 751
- Schema-valid rows: 741
- Estimated total token cost: $0.289346

## Metrics On Schema-Valid Rows

| task | accuracy | macro_f1 | weighted_f1 |
|---|---:|---:|---:|
| `screening_status` | 0.747638 | 0.436463 | 0.776167 |
| `primary_event_type` | 0.358974 | 0.260304 | 0.338927 |

## Reproducibility Note

Use `--limit` for smoke tests and rerun without `--limit` to complete the selected split. The script resumes from the existing prediction CSV by ACN.
