# Expanded 8,800 Result Tables With Bootstrap Confidence Intervals

Created: 2026-06-04

## Boundary

These tables are computed from prediction CSV files only. They do not access raw ASRS narrative text. The expanded design uses 7,299 training rows, with the 3,800 expanded agent-silver rows added only to train; dev/test remain the verified reference rows.

## screening_status

| model family | training design | model | n | validity scope | accuracy | macro F1 | weighted F1 |
|---|---|---|---:|---|---:|---:|---:|
| Supervised MiniLM | `seed_5000_verified_train_local_cpu` | `supervised_minilm_l6v2_local_finetune` | 751 | `all_test_rows` | 0.888 [0.867, 0.911] | 0.537 [0.513, 0.823] | 0.890 [0.869, 0.912] |
| TF-IDF LinearSVC | `expanded_8800_weak_train_verified_test` | `tfidf_word13_linear_svc_balanced` | 751 | `all_test_rows` | 0.881 [0.858, 0.904] | 0.513 [0.486, 0.789] | 0.877 [0.851, 0.901] |
| TF-IDF logistic regression | `expanded_8800_weak_train_verified_test` | `tfidf_char36_logreg_balanced` | 751 | `all_test_rows` | 0.870 [0.843, 0.892] | 0.510 [0.482, 0.784] | 0.870 [0.843, 0.894] |
| TF-IDF logistic regression | `expanded_8800_weak_train_verified_test` | `tfidf_word13_logreg_balanced` | 751 | `all_test_rows` | 0.872 [0.847, 0.894] | 0.502 [0.475, 0.772] | 0.868 [0.841, 0.892] |
| TF-IDF LinearSVC | `expanded_8800_weak_train_verified_test` | `tfidf_word13_char36_calibrated_svc_balanced` | 751 | `all_test_rows` | 0.880 [0.855, 0.903] | 0.501 [0.470, 0.773] | 0.872 [0.844, 0.898] |
| TF-IDF LinearSVC | `expanded_8800_weak_train_verified_test` | `tfidf_char36_linear_svc_balanced` | 751 | `all_test_rows` | 0.866 [0.840, 0.888] | 0.501 [0.472, 0.773] | 0.865 [0.839, 0.888] |
| TF-IDF LinearSVC | `expanded_8800_weak_train_verified_test` | `tfidf_word13_char36_linear_svc_balanced` | 751 | `all_test_rows` | 0.871 [0.846, 0.894] | 0.498 [0.470, 0.766] | 0.866 [0.840, 0.891] |
| Remote Qwen structured output | `zero_shot_remote_hf_verified_test` | `hf_qwen2_5_7b_instruct_structured_zero_shot` | 741 | `schema_valid_rows_only` | 0.748 [0.714, 0.777] | 0.436 [0.410, 0.671] | 0.776 [0.748, 0.803] |
| Majority | `expanded_8800_weak_train_verified_test` | `majority_most_frequent` | 751 | `all_test_rows` | 0.840 [0.814, 0.864] | 0.304 [0.299, 0.460] | 0.767 [0.730, 0.801] |

## primary_event_type

| model family | training design | model | n | validity scope | accuracy | macro F1 | weighted F1 |
|---|---|---|---:|---|---:|---:|---:|
| TF-IDF LinearSVC | `expanded_8800_weak_train_verified_test` | `tfidf_word13_char36_linear_svc_balanced` | 751 | `all_test_rows` | 0.603 [0.570, 0.639] | 0.557 [0.510, 0.600] | 0.599 [0.564, 0.636] |
| TF-IDF LinearSVC | `expanded_8800_weak_train_verified_test` | `tfidf_word13_linear_svc_balanced` | 751 | `all_test_rows` | 0.605 [0.571, 0.642] | 0.547 [0.499, 0.588] | 0.601 [0.568, 0.638] |
| TF-IDF LinearSVC | `expanded_8800_weak_train_verified_test` | `tfidf_word13_char36_calibrated_svc_balanced` | 751 | `all_test_rows` | 0.593 [0.558, 0.629] | 0.540 [0.492, 0.582] | 0.589 [0.552, 0.627] |
| TF-IDF LinearSVC | `expanded_8800_weak_train_verified_test` | `tfidf_char36_linear_svc_balanced` | 751 | `all_test_rows` | 0.574 [0.538, 0.610] | 0.530 [0.485, 0.569] | 0.577 [0.541, 0.612] |
| TF-IDF logistic regression | `expanded_8800_weak_train_verified_test` | `tfidf_word13_logreg_balanced` | 751 | `all_test_rows` | 0.569 [0.534, 0.605] | 0.518 [0.474, 0.558] | 0.568 [0.532, 0.604] |
| TF-IDF logistic regression | `expanded_8800_weak_train_verified_test` | `tfidf_char36_logreg_balanced` | 751 | `all_test_rows` | 0.547 [0.513, 0.581] | 0.500 [0.456, 0.540] | 0.550 [0.516, 0.586] |
| Supervised MiniLM | `seed_5000_verified_train_local_cpu` | `supervised_minilm_l6v2_local_finetune` | 751 | `all_test_rows` | 0.506 [0.473, 0.542] | 0.408 [0.372, 0.440] | 0.462 [0.427, 0.500] |
| Remote Qwen structured output | `zero_shot_remote_hf_verified_test` | `hf_qwen2_5_7b_instruct_structured_zero_shot` | 741 | `schema_valid_rows_only` | 0.359 [0.321, 0.394] | 0.260 [0.230, 0.294] | 0.339 [0.301, 0.374] |
| Majority | `expanded_8800_weak_train_verified_test` | `majority_most_frequent` | 751 | `all_test_rows` | 0.145 [0.120, 0.169] | 0.021 [0.018, 0.024] | 0.037 [0.026, 0.049] |

## record_level_event_multilabel_relevant_only

| training design | model | n | labels | micro F1 | macro F1 | samples F1 | subset accuracy | samples Jaccard | hamming loss |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `seed_5000_verified_train` | `tfidf_word13_char36_ovr_linear_svc_multilabel` | 631 | 11 | 0.609 [0.585, 0.633] | 0.554 [0.521, 0.584] | 0.595 [0.569, 0.623] | 0.298 [0.265, 0.331] | 0.517 [0.489, 0.545] | 0.113 [0.105, 0.121] |
| `expanded_8800_weak_train_verified_test` | `expanded_tfidf_word13_char36_ovr_linear_svc_multilabel` | 631 | 11 | 0.633 [0.611, 0.656] | 0.598 [0.563, 0.628] | 0.614 [0.588, 0.642] | 0.317 [0.282, 0.353] | 0.537 [0.510, 0.566] | 0.111 [0.103, 0.119] |

## Interpretation Notes

- The main expanded-training gain is on primary-event classification and multi-label event tagging.
- The zero-shot Qwen 7B baseline produced mostly valid JSON, but it underperformed local TF-IDF models; present it as a bounded negative/diagnostic LLM baseline, not the main result.
- The earlier supervised MiniLM remains useful for screening-status comparison, but it was trained on the 5,000-row seed train split because the local environment has CPU-only PyTorch.
- Multi-label results are record-level primary-plus-secondary label tagging, not event-span extraction.
