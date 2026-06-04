---
type: decision_record
domain: aviation-nlp
status: active
created: 2026-06-03
tags:
  - asrs
  - splits
  - event-handling
  - leakage-control
---

# Record-Level Split And Event-Handling Decision

## Decision

Proceed with a record-level benchmark first.

The current verified corpus supports:

- relevance screening: ground/cabin event versus not relevant/uncertain;
- primary event-type classification;
- optional secondary-event multi-label analysis;
- evidence-snippet analysis;
- later structured extraction baselines if the task is framed carefully.

Do not yet claim a full event-mention extraction benchmark for all records because 1,965 rows are marked as possible multi-event records.

## Current Split Package

Created by:

`scripts\build_record_level_splits.py`

Input labels:

`data\manifests\author_verified_single_reviewer_labels_5000_2026-06-03.csv`

Outputs:

- `data\splits\record_level_split_assignments_2026-06-03.csv`
- `data\splits\train_records_2026-06-03.csv`
- `data\splits\dev_records_2026-06-03.csv`
- `data\splits\test_records_2026-06-03.csv`
- `data\splits\split_summary_2026-06-03.md`

Split counts:

| Split | Records |
|---|---:|
| train | 3,499 |
| dev | 750 |
| test | 751 |

Leakage checks:

- duplicate ACNs: 0;
- exact normalized text hashes crossing splits: 0;
- raw ASRS text included in split files: false.

## Verification Layer

The split package uses the author-verified label layer with local consistency-audit support:

`verification_status=author_verified_single_reviewer`

Boundary:

- The user/author reports that the labels were verified and no problems were found.
- The workspace does not contain independent reviewer identity, exact verification protocol, disagreement ledger, inter-annotator agreement, or adjudication details.
- Manuscript-safe wording: `author-verified reference labels with local consistency-audit support`.
- Avoid claiming formal expert consensus, inter-annotator agreement, or adjudicated gold unless those artifacts are added later.

## Multi-Event Handling

Rows with:

`multi_event_structure_flag=possible_multi_event_needs_event_level_policy`

should be treated as record-level labels for now.

Current counts:

| Split | Single-record labels | Possible multi-event records |
|---|---:|---:|
| train | 2,118 | 1,381 |
| dev | 465 | 285 |
| test | 452 | 299 |
| total | 3,035 | 1,965 |

## Modeling Path

Phase 1 baselines should use:

- input: ASRS synopsis + narrative loaded locally from raw JSON by ACN;
- task A: binary/three-way screening status classification;
- task B: primary event-type classification;
- task C: optional multi-label secondary event-family prediction;
- task D: optional evidence-snippet retrieval or structured extraction only if framed as record-level extraction.

Do not report:

- full event-mention recall;
- event-boundary detection;
- per-event slot extraction across all records;
- inter-annotator agreement;
- adjudicated gold-standard accuracy.

## Future Event-Level Option

If the paper needs a stronger extraction contribution, create a separate event-level file:

`event_level_reference_labels_v0_1.csv`

That file should:

- split one ASRS record into multiple event rows where needed;
- retain source `corpus_id` and ACN;
- include evidence spans for each event;
- distinguish primary and secondary record-level event types;
- preserve train/dev/test assignment from the parent record to avoid leakage.

Until that file exists, the manuscript should describe the dataset as a record-level aviation narrative benchmark with verified event-family labels.
