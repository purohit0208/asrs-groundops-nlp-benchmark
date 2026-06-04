# ASRS-GroundOps NLP Benchmark

Sanitized reproducibility package for a public NASA ASRS aviation-narrative benchmark focused on ground-operation and cabin-service event classification.

## What Is Included

- sanitized 5,000-record author-verified seed labels with local consistency-audit support;
- sanitized 8,800-record expanded corpus labels, where 3,800 added records are train-only agent-silver augmentation rows;
- leakage-safe split assignments for the 5,000-row seed corpus and the 8,800-row reference-evaluation design;
- baseline metrics, prediction files without raw narrative text, and bootstrap confidence-interval tables;
- protocols and scripts needed to reconstruct/evaluate the benchmark after locally obtaining ASRS records.

## What Is Not Included

- raw NASA ASRS narratives or raw ASRS JSON detail files;
- downloaded literature PDFs;
- Consensus or subscription search reports;
- manuscript DOCX files or private project-history artifacts;
- evidence snippets used during local auditing.

## Label Provenance

Use the following wording: `author-verified reference labels with local consistency-audit support` for the 5,000-row seed subset. The 3,800 expanded rows are not human verified and must be treated as train-only agent-silver augmentation.

Do not describe this dataset as expert-adjudicated, multi-annotator, independently adjudicated, or formal gold-standard data unless new annotation artifacts are added.

## ASRS Source Boundary

The repository does not redistribute raw ASRS narrative text. Users should obtain ASRS records through NASA ASRS Database Online and follow the official ASRS caveats and use conditions. See `DATASET_NOTICE.md` and `protocols/ASRS_ACCESS_AND_QUERY_PROTOCOL.md`.

## Reproducibility

The main reproduction notes are in `REPRODUCIBILITY_NOTES.md`. The scripts assume raw ASRS records have been reconstructed locally in the expected project layout; raw records are intentionally absent from this public package.

## Citation

A manuscript citation will be added after publication or preprint release.
