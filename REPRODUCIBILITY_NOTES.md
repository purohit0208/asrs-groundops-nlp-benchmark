# Reproducibility Notes

Created: 2026-06-04

## Environment Observed

- `python`: `3.11.9`
- `platform`: `Windows-10-10.0.26200-SP0`
- `numpy`: `2.2.1`
- `scipy`: `1.17.1`
- `scikit-learn`: `1.6.0`
- `pandas`: `2.2.3`
- `torch`: `2.12.0+cpu`
- `transformers`: `5.8.1`
- `sentence-transformers`: `5.5.0`

## Main Reproduction Order

Run from the project root after ASRS raw records have been reconstructed locally:

```powershell
python scripts\build_record_level_splits.py
python scripts\run_record_level_baselines.py
python scripts\analyze_record_level_errors.py
python scripts\run_stronger_classical_baselines.py
python scripts\run_sentence_embedding_baseline.py
python scripts\run_supervised_minilm_baseline.py
python scripts\compare_baseline_families.py
python scripts\run_record_multilabel_event_baseline.py
python scripts\build_manuscript_result_tables.py
python scripts\build_expanded_8800_corpus.py
python scripts\build_expanded_8800_reference_eval_splits.py
python scripts\run_expanded_8800_reference_classical_baselines.py
python scripts\run_expanded_8800_reference_multilabel_baseline.py
python scripts\run_hf_qwen_structured_baseline.py --workers 4 --output-dir outputs\baselines\hf_qwen_structured_test_2026-06-04
python scripts\build_expanded_8800_result_tables.py
python scripts\build_release_candidate.py
```

The supervised MiniLM run is CPU-compatible but slow in the observed environment because installed PyTorch is CPU-only.
