# Processed Data Folder

This folder is reserved for processed candidate manifests, screened records, annotation-ready records, train/dev/test splits, and model-ready files.

No processed file should be treated as manuscript evidence unless its raw source, query ID, and processing script are traceable.

Expected future files:

- `annotation_units_v0_1.csv`
- `train.csv`
- `dev.csv`
- `test.csv`
- `label_distribution.md`

## Current Manifest State

Current generated manifests live in:

`data\manifests`

Key files:

- `query_counts_2026-06-02.csv` - ASRS current search counts for Q01-Q08 before local date filtering.
- `query_counts_2026-06-03.csv` - ASRS current search counts for Q01-Q14 before local date filtering.
- `Q02_candidate_manifest_2026-06-02.csv` - Q02 records kept after 2011-2025 date filtering.
- `Q04_candidate_manifest_2026-06-02.csv` - Q04 records kept after 2011-2025 date filtering.
- `Q09_candidate_manifest_2026-06-03.csv` - Q09 records kept after 2011-2025 date filtering.
- `Q10_candidate_manifest_2026-06-03.csv` - Q10 records kept after 2011-2025 date filtering.
- `Q11_candidate_manifest_2026-06-03.csv` - Q11 records kept after 2011-2025 date filtering.
- `Q12_candidate_manifest_2026-06-03.csv` - Q12 records kept after 2011-2025 date filtering.
- `candidate_records_manifest.csv` - deduplicated Q02/Q04/Q09/Q10/Q11/Q12 candidate pool, 8,801 unique ACNs.
- `candidate_records_manifest_expanded_2026-06-03.csv` - dated copy of the expanded candidate pool.
- `pilot_screening_sample_200_2026-06-02.csv` - deterministic 200-record screening sample.
- `screening_manifest.csv` - active pilot screening file.
- `silver_corpus_5000_manifest_2026-06-03.csv` - deterministic 5,000-record silver-corpus manifest.
- `silver_corpus_5000_labels_2026-06-03.csv` - agent-generated silver labels, not human verified.
- `silver_corpus_5000_summary_2026-06-03.md` - 5,000-record corpus coverage summary.
- `silver_corpus_5000_label_summary_2026-06-03.md` - silver-label distribution summary.
- `author_verified_single_reviewer_labels_5000_2026-06-03.csv` - derived label file recording the user's author-reported verification of all 5,000 rows.
- `expanded_corpus_8800_manifest_2026-06-04.csv` - exact 8,800-row expanded corpus manifest built from the existing 8,801-record candidate pool.
- `expanded_corpus_8800_labels_2026-06-04.csv` - expanded label file containing the 5,000 author-verified seed rows with local consistency-audit support plus 3,800 train-only agent-silver expansion rows.
- `expanded_corpus_8800_summary_2026-06-04.md` - expanded-corpus composition summary.

The original `silver_corpus_5000_labels_2026-06-03.csv` remains the agent-generated provenance layer. The derived `author_verified_single_reviewer_labels_5000_2026-06-03.csv` is the active label file for baseline work, with the limitation that the workspace does not contain inter-annotator agreement, disagreement ledger, independent expert review, or formal adjudication artifacts.

For the expanded 8,800-row setup, the 3,800 added rows are weak-label augmentation rows only. They are not newly human verified and should not be used for dev/test evaluation.

## Current Split State

Current generated split files live in:

`data\splits`

Key files:

- `record_level_split_assignments_2026-06-03.csv` - full record-level split assignment file.
- `train_records_2026-06-03.csv` - 3,499 training records.
- `dev_records_2026-06-03.csv` - 750 development records.
- `test_records_2026-06-03.csv` - 751 test records.
- `split_summary_2026-06-03.md` - split distribution and leakage audit.
- `expanded_8800_reference_eval_split_assignments_2026-06-04.csv` - full expanded split assignment file with 7,299 train, 750 dev, and 751 test records.
- `expanded_8800_reference_eval_train_records_2026-06-04.csv` - 7,299 training records, including all 3,800 agent-silver expansion rows.
- `expanded_8800_reference_eval_dev_records_2026-06-04.csv` - 750 development records from the verified seed corpus only.
- `expanded_8800_reference_eval_test_records_2026-06-04.csv` - 751 test records from the verified seed corpus only.
- `expanded_8800_reference_eval_split_summary_2026-06-04.md` - expanded split distribution and leakage audit.

Raw ASRS narrative text is not included in these split files.

## Current Baseline Output State

Current baseline outputs live in:

`outputs\baselines\record_level_2026-06-03`

Key files:

- `record_level_baseline_summary.md` - first metrics table and interpretation rules.
- `record_level_baseline_metrics.csv` - machine-readable metrics.
- `record_level_baseline_predictions.csv` - prediction rows without raw narrative text.
- `baseline_config.json` - split/raw-source/model configuration.
- `classification_report_*` - per-task/per-model reports and confusion matrices.

The `rule_reproduction_check_not_independent` rows are consistency checks, not independent ML baselines.

Additional baseline and comparison outputs now live in:

- `outputs\baselines\record_level_2026-06-03\error_analysis` - first TF-IDF error analysis, without full raw narratives.
- `outputs\baselines\sentence_embedding_2026-06-03` - frozen `sentence-transformers/all-MiniLM-L6-v2` plus balanced logistic-regression baseline.
- `outputs\baselines\stronger_classical_2026-06-03` - word/character TF-IDF LinearSVC baselines.
- `outputs\baselines\supervised_minilm_2026-06-03` - local CPU supervised MiniLM fine-tuning baseline.
- `outputs\baselines\record_multilabel_2026-06-03` - record-level multi-label event-type baseline for included records.
- `outputs\baselines\comparison_2026-06-03` - metric-only comparison across completed baseline families.
- `outputs\baselines\expanded_8800_reference_classical_2026-06-04` - expanded-corpus classical baselines.
- `outputs\baselines\expanded_8800_reference_multilabel_2026-06-04` - expanded-corpus record-level multi-label baseline.
- `outputs\baselines\hf_qwen_structured_dev_2026-06-04` - bounded Qwen2.5-7B structured-output development-split diagnostic.
- `outputs\baselines\hf_qwen_structured_test_2026-06-04` - bounded Qwen2.5-7B structured-output test-split diagnostic.

Current best independent test metrics by macro F1:

- screening status: `supervised_minilm_l6v2_local_finetune`, accuracy 0.888, macro F1 0.537.
- primary event type: expanded `tfidf_word13_char36_linear_svc_balanced`, accuracy 0.603, macro F1 0.557.

Frozen MiniLM underperformed TF-IDF on both tasks. Supervised MiniLM improved screening but underperformed TF-IDF LinearSVC for the harder primary-event taxonomy. The next major model addition should be a clearly bounded LLM structured-output baseline only if the raw-narrative external-processing decision is recorded.

Current record-level multi-label event-tagging result for included records:

- original verified-seed relevant train/dev/test counts: 2,941 / 631 / 631.
- original verified-seed test micro F1 0.609, macro F1 0.554, samples F1 0.595, subset accuracy 0.298, hamming loss 0.113.
- expanded-training test micro F1 0.633, macro F1 0.598, samples F1 0.614, subset accuracy 0.317, hamming loss 0.111.
- This is not event-span extraction; it uses primary-plus-secondary record labels.

## Current Manuscript Table State

Current manuscript-ready metric tables live in:

`outputs\manuscript_tables\results_2026-06-03`

Expanded-training manuscript-ready metric tables live in:

`outputs\manuscript_tables\expanded_8800_results_2026-06-04`

Key files:

- `manuscript_results_with_ci.md` - Markdown tables with 1,000-sample bootstrap confidence intervals.
- `single_label_test_results_with_ci.csv` - machine-readable single-label test results with CIs.
- `multilabel_test_results_with_ci.csv` - machine-readable multi-label test results with CIs.

Main values:

- screening best: supervised MiniLM, accuracy 0.888 [0.866, 0.912], macro F1 0.537 [0.512, 0.828].
- expanded primary-event best: TF-IDF word+char LinearSVC, accuracy 0.603 [0.570, 0.639], macro F1 0.557 [0.510, 0.600].
- expanded multi-label event tagging: micro F1 0.633 [0.611, 0.656], macro F1 0.598 [0.563, 0.628].
- Qwen2.5-7B diagnostic test result: 751/751 valid JSON rows, 741 schema-valid rows, screening macro F1 0.436, primary-event macro F1 0.260.

Screening-status macro-F1 intervals are wide because `uncertain_needs_review` has very low test support.

## Current Release Candidate State

Current internal release candidate lives in:

`outputs\release_package\release_candidate_2026-06-04`

Key files:

- `README_RELEASE_CANDIDATE.md` - package purpose and upload boundary.
- `DATA_USE_AND_REDISTRIBUTION_BOUNDARY.md` - raw ASRS narrative and label-provenance boundary.
- `REPRODUCIBILITY_NOTES.md` - reproduction order and observed package versions.
- `RELEASE_QA_REPORT.md` - sanitized data and copied-material checks.
- `release_candidate_manifest.csv` - file list with SHA256 hashes.
- `data\sanitized_labels_5000_2026-06-04.csv` - 5,000 labels without evidence snippets.
- `data\sanitized_record_level_split_assignments_2026-06-04.csv` - 5,000 split rows without evidence snippets or local raw paths.
- `data\sanitized_expanded_corpus_8800_labels_2026-06-04.csv` - 8,800 expanded labels without evidence snippets.
- `data\sanitized_expanded_8800_reference_eval_split_assignments_2026-06-04.csv` - 8,800 expanded split rows without evidence snippets or local raw paths.

QA result:

- manifest rows: 90.
- sanitized labels: 5,000 rows.
- sanitized splits: 5,000 rows, with 3,499 train / 750 dev / 751 test.
- sanitized expanded labels: 8,800 rows.
- sanitized expanded splits: 8,800 rows, with 7,299 train / 750 dev / 751 test.
- forbidden evidence/raw-path columns present in sanitized CSVs: none.
- raw ASRS JSON, downloaded PDFs, and Consensus reports copied: none.
- all manifest hashes validated.

This is an internal release candidate, not a public upload package.
