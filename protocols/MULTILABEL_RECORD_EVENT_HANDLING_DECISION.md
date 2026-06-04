# Multi-Label Record Event Handling Decision

Created: 2026-06-03
Status: active protocol decision

## Decision

Use a record-level multi-label event-type task as the manuscript-safe intermediate handling for records flagged as possible multi-event cases.

The label set for an included record is:

- `silver_primary_event_type`
- plus any semicolon-separated `silver_secondary_event_types`

Excluded or uncertain records are not part of this event-type multi-label task. Screening remains a separate task.

## Why This Is Needed

The current 5,000-record corpus contains many records with possible multiple operational event types. Treating each record as only one primary class hides this structure and partly explains the weak primary-event-type macro F1.

At the same time, the workspace does not yet contain event-span annotations. Therefore, it would be inaccurate to claim event-mention extraction or event-level ground truth.

## Allowed Wording

Allowed:

- record-level multi-label event tagging;
- multi-label classification over included ASRS records;
- primary-plus-secondary event-type reference labels;
- intermediate handling for possible multi-event narratives.

Not allowed:

- event-span extraction;
- event-mention benchmark;
- adjudicated event-level gold standard;
- full event extraction unless span-level annotations are created later.

## Evaluation Boundary

Report:

- micro F1;
- macro F1;
- samples F1;
- samples Jaccard;
- exact-set/subset accuracy;
- hamming loss;
- per-label precision, recall, and F1.

Do not compare these numbers directly to single-label primary-event accuracy as if they were the same task.

## Release Boundary

The multi-label output files contain ACNs, corpus IDs, and label sets only. They should not contain full ASRS narrative text.
