# Manuscript Result Tables With Bootstrap Confidence Intervals

Created: 2026-06-03

## Boundary

These tables are computed from prediction CSV files only. They do not access raw ASRS narrative text. Confidence intervals are percentile bootstrap intervals over test records using 1,000 resamples.

## screening_status

| model family | model | n | accuracy | macro F1 | weighted F1 |
|---|---|---:|---:|---:|---:|
| Supervised MiniLM | `supervised_minilm_l6v2_local_finetune` | 751 | 0.888 [0.866, 0.912] | 0.537 [0.512, 0.828] | 0.890 [0.868, 0.913] |
| TF-IDF LinearSVC | `tfidf_char36_linear_svc_balanced` | 751 | 0.880 [0.855, 0.901] | 0.514 [0.487, 0.795] | 0.877 [0.852, 0.899] |
| TF-IDF LinearSVC | `tfidf_word13_linear_svc_balanced` | 751 | 0.884 [0.862, 0.905] | 0.512 [0.483, 0.791] | 0.878 [0.853, 0.902] |
| TF-IDF LinearSVC | `tfidf_word13_char36_linear_svc_balanced` | 751 | 0.881 [0.858, 0.904] | 0.509 [0.479, 0.784] | 0.876 [0.849, 0.899] |
| TF-IDF logistic regression | `tfidf_char35_logreg_balanced` | 751 | 0.872 [0.847, 0.895] | 0.505 [0.476, 0.776] | 0.870 [0.843, 0.892] |
| TF-IDF LinearSVC | `tfidf_word13_char36_calibrated_svc_balanced` | 751 | 0.880 [0.856, 0.901] | 0.505 [0.475, 0.779] | 0.873 [0.847, 0.897] |
| TF-IDF logistic regression | `tfidf_word12_logreg_balanced` | 751 | 0.879 [0.853, 0.901] | 0.503 [0.472, 0.776] | 0.872 [0.844, 0.896] |
| Frozen MiniLM embeddings | `sbert_all_minilm_l6v2_logreg_balanced` | 751 | 0.787 [0.759, 0.816] | 0.470 [0.444, 0.494] | 0.811 [0.787, 0.838] |
| Majority | `majority` | 751 | 0.840 [0.812, 0.866] | 0.304 [0.299, 0.461] | 0.767 [0.728, 0.803] |

## primary_event_type

| model family | model | n | accuracy | macro F1 | weighted F1 |
|---|---|---:|---:|---:|---:|
| TF-IDF LinearSVC | `tfidf_word13_char36_linear_svc_balanced` | 751 | 0.566 [0.533, 0.599] | 0.499 [0.452, 0.537] | 0.559 [0.525, 0.595] |
| TF-IDF LinearSVC | `tfidf_word13_char36_calibrated_svc_balanced` | 751 | 0.571 [0.538, 0.605] | 0.496 [0.449, 0.536] | 0.564 [0.529, 0.599] |
| TF-IDF LinearSVC | `tfidf_char36_linear_svc_balanced` | 751 | 0.557 [0.521, 0.590] | 0.493 [0.446, 0.530] | 0.553 [0.517, 0.587] |
| TF-IDF LinearSVC | `tfidf_word13_linear_svc_balanced` | 751 | 0.575 [0.542, 0.610] | 0.493 [0.446, 0.530] | 0.566 [0.532, 0.602] |
| TF-IDF logistic regression | `tfidf_char35_logreg_balanced` | 751 | 0.535 [0.501, 0.567] | 0.472 [0.429, 0.507] | 0.533 [0.497, 0.566] |
| TF-IDF logistic regression | `tfidf_word12_logreg_balanced` | 751 | 0.534 [0.499, 0.570] | 0.463 [0.416, 0.501] | 0.521 [0.486, 0.559] |
| Frozen MiniLM embeddings | `sbert_all_minilm_l6v2_logreg_balanced` | 751 | 0.493 [0.457, 0.527] | 0.436 [0.399, 0.471] | 0.507 [0.472, 0.543] |
| Supervised MiniLM | `supervised_minilm_l6v2_local_finetune` | 751 | 0.506 [0.471, 0.542] | 0.408 [0.371, 0.442] | 0.462 [0.426, 0.502] |
| Majority | `majority` | 751 | 0.157 [0.132, 0.185] | 0.023 [0.019, 0.026] | 0.043 [0.031, 0.058] |

## record_level_event_multilabel_relevant_only

| model | n | labels | micro F1 | macro F1 | samples F1 | subset accuracy | samples Jaccard | hamming loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `tfidf_word13_char36_ovr_linear_svc_multilabel` | 631 | 11 | 0.609 [0.586, 0.633] | 0.554 [0.520, 0.585] | 0.595 [0.569, 0.624] | 0.298 [0.265, 0.333] | 0.517 [0.490, 0.546] | 0.113 [0.105, 0.121] |

## Interpretation Notes

- Screening-status and primary-event-type are single-label record-level tasks.
- The multi-label task applies only to included records and uses primary-plus-secondary event labels.
- Multi-label results must not be described as event-span extraction.
- Rule-reproduction checks are excluded because they are label-consistency checks, not independent baselines.
- Screening-status macro-F1 intervals are unstable because the rare `uncertain_needs_review` class has very low test support; use per-class reports when discussing that task.
