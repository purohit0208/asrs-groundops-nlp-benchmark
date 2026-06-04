# Baseline Family Comparison

Created: 2026-06-03

## Boundary

This comparison uses baseline metric CSV files only. It does not access raw ASRS narrative text. Rule-reproduction rows are excluded from best-model selection because they are label-consistency checks, not independent baselines.

## Best Independent Test Results By Macro F1

| task | family | model | accuracy | macro_f1 | weighted_f1 |
|---|---|---|---:|---:|---:|
| `primary_event_type` | `linear_svc_tfidf` | `tfidf_word13_char36_linear_svc_balanced` | 0.565912 | 0.498839 | 0.558969 |
| `screening_status` | `supervised_minilm_local` | `supervised_minilm_l6v2_local_finetune` | 0.888149 | 0.536756 | 0.890488 |

## All Test Results

| task | family | model | accuracy | macro_f1 | weighted_f1 |
|---|---|---|---:|---:|---:|
| `primary_event_type` | `linear_svc_tfidf` | `tfidf_word13_char36_linear_svc_balanced` | 0.565912 | 0.498839 | 0.558969 |
| `primary_event_type` | `linear_svc_tfidf` | `tfidf_word13_char36_calibrated_svc_balanced` | 0.571238 | 0.496402 | 0.563523 |
| `primary_event_type` | `linear_svc_tfidf` | `tfidf_char36_linear_svc_balanced` | 0.556591 | 0.492938 | 0.553064 |
| `primary_event_type` | `linear_svc_tfidf` | `tfidf_word13_linear_svc_balanced` | 0.575233 | 0.492634 | 0.566233 |
| `primary_event_type` | `majority_tfidf_logreg_rules` | `tfidf_char35_logreg_balanced` | 0.535286 | 0.472302 | 0.532551 |
| `primary_event_type` | `majority_tfidf_logreg_rules` | `tfidf_word12_logreg_balanced` | 0.533955 | 0.463305 | 0.521191 |
| `primary_event_type` | `frozen_minilm_embeddings` | `sbert_all_minilm_l6v2_logreg_balanced` | 0.492676 | 0.436172 | 0.506805 |
| `primary_event_type` | `supervised_minilm_local` | `supervised_minilm_l6v2_local_finetune` | 0.505992 | 0.408335 | 0.462481 |
| `primary_event_type` | `majority_tfidf_logreg_rules` | `majority` | 0.157124 | 0.022631 | 0.042671 |
| `screening_status` | `supervised_minilm_local` | `supervised_minilm_l6v2_local_finetune` | 0.888149 | 0.536756 | 0.890488 |
| `screening_status` | `linear_svc_tfidf` | `tfidf_char36_linear_svc_balanced` | 0.880160 | 0.514427 | 0.877244 |
| `screening_status` | `linear_svc_tfidf` | `tfidf_word13_linear_svc_balanced` | 0.884154 | 0.512316 | 0.878332 |
| `screening_status` | `linear_svc_tfidf` | `tfidf_word13_char36_linear_svc_balanced` | 0.881491 | 0.508696 | 0.875563 |
| `screening_status` | `majority_tfidf_logreg_rules` | `tfidf_char35_logreg_balanced` | 0.872170 | 0.505238 | 0.869609 |
| `screening_status` | `linear_svc_tfidf` | `tfidf_word13_char36_calibrated_svc_balanced` | 0.880160 | 0.505010 | 0.873405 |
| `screening_status` | `majority_tfidf_logreg_rules` | `tfidf_word12_logreg_balanced` | 0.878828 | 0.502534 | 0.871745 |
| `screening_status` | `frozen_minilm_embeddings` | `sbert_all_minilm_l6v2_logreg_balanced` | 0.786951 | 0.470314 | 0.811418 |
| `screening_status` | `majority_tfidf_logreg_rules` | `majority` | 0.840213 | 0.304390 | 0.767257 |

## Interpretation

- Supervised MiniLM is currently best for screening-status macro F1, while TF-IDF LinearSVC remains best for primary-event-type macro F1.
- Supervised MiniLM improves screening-status macro F1 over TF-IDF but underperforms TF-IDF LinearSVC for primary-event-type classification.
- Frozen MiniLM sentence embeddings underperform TF-IDF on this record-level benchmark.
- A Hugging Face LLM or remote job should be used only after an explicit raw-narrative external-processing decision is recorded.
