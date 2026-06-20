# Hugging Face Qwen Structured Baseline Summary

Created: 2026-06-20

## Boundary

This run sends raw ASRS text to Hugging Face Inference Providers under the approval recorded in `protocols/EXPANDED_8800_CORPUS_AND_REMOTE_LLM_DECISION.md`. Output files do not store raw prompts, raw ASRS text, or raw model responses.

- Model: `Qwen/Qwen2.5-72B-Instruct`
- Base model for report: `Qwen/Qwen2.5-7B-Instruct`
- Split file: `..\data\splits\expanded_8800_reference_eval_test_records_2026-06-04.csv`
- Completed rows in prediction file: 751
- Valid JSON rows: 751
- Schema-valid rows: 738
- Estimated total token cost: $0.368192

## Metrics On Schema-Valid Rows

| task | accuracy | macro_f1 | weighted_f1 |
|---|---:|---:|---:|
| `screening_status` | 0.745257 | 0.445841 | 0.775966 |
| `primary_event_type` | 0.398374 | 0.325224 | 0.373963 |

## Reproducibility Note

Use `--limit` for smoke tests and rerun without `--limit` to complete the selected split. The script resumes from the existing prediction CSV by ACN.
