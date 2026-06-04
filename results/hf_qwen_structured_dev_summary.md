# Hugging Face Qwen Structured Baseline Summary

Created: 2026-06-04

## Boundary

This run sends raw ASRS text to Hugging Face Inference Providers under the approval recorded in `protocols/EXPANDED_8800_CORPUS_AND_REMOTE_LLM_DECISION.md`. Output files do not store raw prompts, raw ASRS text, or raw model responses.

- Model: `Qwen/Qwen2.5-7B-Instruct:cheapest`
- Base model for report: `Qwen/Qwen2.5-7B-Instruct`
- Split file: `data\splits\expanded_8800_reference_eval_dev_records_2026-06-04.csv`
- Completed rows in prediction file: 750
- Valid JSON rows: 750
- Schema-valid rows: 743
- Estimated total token cost: $0.287954

## Metrics On Schema-Valid Rows

| task | accuracy | macro_f1 | weighted_f1 |
|---|---:|---:|---:|
| `screening_status` | 0.761777 | 0.453114 | 0.789194 |
| `primary_event_type` | 0.376851 | 0.272166 | 0.352374 |

## Reproducibility Note

Use `--limit` for smoke tests and rerun without `--limit` to complete the selected split. The script resumes from the existing prediction CSV by ACN.
