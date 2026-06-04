# Data Use And Redistribution Boundary

Created: 2026-06-04

## Current Position

Raw NASA ASRS narrative text remains local. This release candidate does not redistribute full narratives or raw ASRS JSON.

## Conservative Public Release Plan

Release only:

- exact query protocol;
- ASRS ACNs/record identifiers where allowed;
- sanitized labels and split assignments;
- scripts for reconstruction/evaluation;
- metrics and manuscript result tables.

Do not release raw ASRS narrative text unless permission/use terms are confirmed and the manuscript data-availability statement is updated accordingly.

## Label Provenance Boundary

Use `author-verified reference labels with local consistency-audit support` for the 5,000-row seed subset. The expanded 3,800 rows are agent-silver training augmentation rows, not newly human verified. Do not claim formal expert consensus, inter-annotator agreement, second-reviewer verification, or independently adjudicated gold-standard labels unless new artifacts are created.
