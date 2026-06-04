# Expanded 8,800 Reference-Evaluation Classical Baseline Summary

Created: 2026-06-04

## Boundary

Train contains the original verified train rows plus 3,800 expanded agent-silver rows. Dev/test are the original verified reference rows. Full raw ASRS narratives are loaded locally and not written to output files.

## Train Provenance Counts

- `expanded_3800_agent_silver`: 3800
- `seed_5000_author_verified_local_audit`: 3499

## Metrics

| task | model | split | n | accuracy | macro_f1 | weighted_f1 | micro_f1 |
|---|---|---:|---:|---:|---:|---:|---:|
| `screening_status` | `majority_most_frequent` | `dev` | 750 | 0.841333 | 0.304610 | 0.768836 | 0.841333 |
| `screening_status` | `majority_most_frequent` | `test` | 751 | 0.840213 | 0.304390 | 0.767257 | 0.840213 |
| `screening_status` | `tfidf_word13_logreg_balanced` | `dev` | 750 | 0.870667 | 0.719385 | 0.867644 | 0.870667 |
| `screening_status` | `tfidf_word13_logreg_balanced` | `test` | 751 | 0.872170 | 0.501707 | 0.868187 | 0.872170 |
| `screening_status` | `tfidf_char36_logreg_balanced` | `dev` | 750 | 0.868000 | 0.731759 | 0.871165 | 0.868000 |
| `screening_status` | `tfidf_char36_logreg_balanced` | `test` | 751 | 0.869507 | 0.509511 | 0.869960 | 0.869507 |
| `screening_status` | `tfidf_word13_linear_svc_balanced` | `dev` | 750 | 0.870667 | 0.718115 | 0.867131 | 0.870667 |
| `screening_status` | `tfidf_word13_linear_svc_balanced` | `test` | 751 | 0.881491 | 0.513390 | 0.877479 | 0.881491 |
| `screening_status` | `tfidf_char36_linear_svc_balanced` | `dev` | 750 | 0.878667 | 0.737715 | 0.878905 | 0.878667 |
| `screening_status` | `tfidf_char36_linear_svc_balanced` | `test` | 751 | 0.865513 | 0.500770 | 0.864512 | 0.865513 |
| `screening_status` | `tfidf_word13_char36_linear_svc_balanced` | `dev` | 750 | 0.882667 | 0.734679 | 0.879676 | 0.882667 |
| `screening_status` | `tfidf_word13_char36_linear_svc_balanced` | `test` | 751 | 0.870839 | 0.498098 | 0.866073 | 0.870839 |
| `screening_status` | `tfidf_word13_char36_calibrated_svc_balanced` | `dev` | 750 | 0.882667 | 0.720561 | 0.873871 | 0.882667 |
| `screening_status` | `tfidf_word13_char36_calibrated_svc_balanced` | `test` | 751 | 0.880160 | 0.501088 | 0.871778 | 0.880160 |
| `primary_event_type` | `majority_most_frequent` | `dev` | 750 | 0.145333 | 0.021149 | 0.036883 | 0.145333 |
| `primary_event_type` | `majority_most_frequent` | `test` | 751 | 0.145140 | 0.021124 | 0.036791 | 0.145140 |
| `primary_event_type` | `tfidf_word13_logreg_balanced` | `dev` | 750 | 0.580000 | 0.515705 | 0.581647 | 0.580000 |
| `primary_event_type` | `tfidf_word13_logreg_balanced` | `test` | 751 | 0.568575 | 0.518468 | 0.567769 | 0.568575 |
| `primary_event_type` | `tfidf_char36_logreg_balanced` | `dev` | 750 | 0.585333 | 0.530256 | 0.590157 | 0.585333 |
| `primary_event_type` | `tfidf_char36_logreg_balanced` | `test` | 751 | 0.547270 | 0.499516 | 0.550365 | 0.547270 |
| `primary_event_type` | `tfidf_word13_linear_svc_balanced` | `dev` | 750 | 0.613333 | 0.544225 | 0.610047 | 0.613333 |
| `primary_event_type` | `tfidf_word13_linear_svc_balanced` | `test` | 751 | 0.604527 | 0.547159 | 0.601375 | 0.604527 |
| `primary_event_type` | `tfidf_char36_linear_svc_balanced` | `dev` | 750 | 0.614667 | 0.547552 | 0.611855 | 0.614667 |
| `primary_event_type` | `tfidf_char36_linear_svc_balanced` | `test` | 751 | 0.573901 | 0.529572 | 0.576646 | 0.573901 |
| `primary_event_type` | `tfidf_word13_char36_linear_svc_balanced` | `dev` | 750 | 0.616000 | 0.535579 | 0.611009 | 0.616000 |
| `primary_event_type` | `tfidf_word13_char36_linear_svc_balanced` | `test` | 751 | 0.603196 | 0.557255 | 0.599189 | 0.603196 |
| `primary_event_type` | `tfidf_word13_char36_calibrated_svc_balanced` | `dev` | 750 | 0.617333 | 0.545127 | 0.612113 | 0.617333 |
| `primary_event_type` | `tfidf_word13_char36_calibrated_svc_balanced` | `test` | 751 | 0.592543 | 0.540006 | 0.589211 | 0.592543 |

## Interpretation Boundary

- Use these as expanded weak-label training results against verified dev/test labels.
- Do not claim all 8,800 labels are human verified.
- Do not interpret record-level labels as event-span extraction.
