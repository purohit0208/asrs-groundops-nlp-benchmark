# Release Candidate QA Report

Created: 2026-06-04

## Checks

- Included non-manifest files checked: 81
- Sanitized label rows: 5000
- Sanitized split rows: 5000
- Split counts: {'dev': 750, 'test': 751, 'train': 3499}
- Sanitized expanded label rows: 8800
- Sanitized expanded split rows: 8800
- Expanded split counts: {'dev': 750, 'test': 751, 'train': 7299}
- Forbidden label columns present: []
- Forbidden split columns present: []
- Forbidden expanded label columns present: []
- Forbidden expanded split columns present: []
- Raw/PDF/subscription material paths copied: []

## Interpretation

- Sanitized CSV files remove evidence-snippet and raw-path columns.
- Raw ASRS JSON files, downloaded PDFs, and Consensus reports are not copied into this release candidate.
- Scripts and protocols may contain textual references to raw file names because those references are needed for local reconstruction; these are not raw data files.
- This package remains an internal release candidate until ASRS redistribution and repository policy are checked.
