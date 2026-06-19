# ASRS-GroundOps NLP Benchmark

Sanitized reproducibility package for a public NASA ASRS aviation-narrative benchmark
focused on ground-operation and cabin-service event classification.

> Update 2026-06-19: adds fine-tuned transformer baselines (DistilBERT, RoBERTa; 3 seeds,
> bootstrap CIs), a six-class coarse event taxonomy, and a measured test-retest
> label-reliability protocol (Cohen's kappa). See `scripts/`, `outputs/baselines/`, and `docs/`.

## Tasks
- Screening / relevance: is a record a relevant ground/cabin event (include / exclude / uncertain)?
- Event-type classification: a six-class coarse taxonomy (see `docs/COARSE_TAXONOMY.md`); the
  original 12-class scheme is retained for transparency.

## Headline results (held-out verified test set, n = 751; macro-F1)
| Model | Screening | Event-type (coarse 6-class) |
|---|---|---|
| TF-IDF + LinearSVC | 0.513 | 0.640* |
| Supervised MiniLM | 0.537 | - |
| Qwen2.5-7B (zero-shot) | 0.436 | - |
| DistilBERT (fine-tuned, 3 seeds) | 0.604 +/- 0.005 | 0.791 +/- 0.010 |
| RoBERTa-base (fine-tuned, 3 seeds) | 0.605 +/- 0.009 | 0.807 +/- 0.007 |

*Best fine-grained TF-IDF model, predictions remapped to the coarse classes.

## Measured label reliability (test-retest, intra-annotator)
A blind author re-annotation of a stratified test sample (n = 98) gives: screening
Cohen's kappa = 0.40; event-type kappa = 0.36 on the 12-class scheme (low), rising to
kappa = 0.47 on the coarse 6-class scheme and kappa = 0.55 conditioned on agreed relevance.
This is reported transparently as author self-consistency, NOT independent inter-annotator
agreement. See `docs/RELIABILITY_AND_COARSE_TAXONOMY_2026-06-19.md`.

## What is included
- Sanitized 5,000-record author-verified seed labels with local consistency-audit support.
- Sanitized 8,800-record expanded corpus (3,800 train-only agent-silver augmentation rows).
- Leakage-safe split assignments (5,000-seed and 8,800 reference-evaluation designs).
- Baseline scripts (`scripts/`), incl. `run_finetuned_transformer_baseline.py` (use `--coarse`)
  and `build_iaa_worksheet.py` (reliability re-annotation builder/scorer).
- Baseline metrics, predictions without raw narrative text, and bootstrap CI tables (`outputs/baselines/`).
- Coarse-taxonomy mapping and reliability/results docs (`docs/`).

## What is not included
- Raw NASA ASRS narratives or raw ASRS JSON detail files.
- Literature PDFs, subscription/search reports, manuscript files, or local audit evidence snippets.

## Reproduce the transformer baseline
After reconstructing raw ASRS records locally in the expected layout:
```
python scripts/run_finetuned_transformer_baseline.py --model roberta-base --coarse \
    --seeds "20260619,20260620,20260621" --epochs 4 --batch-size 16 --fp16
```
Reliability: `python scripts/build_iaa_worksheet.py --make` then `--score`.

## Label provenance
Use the wording `author-verified reference labels with local consistency-audit support` for
the 5,000-row seed subset; reliability is now additionally measured as intra-annotator
(test-retest) agreement. The 3,800 expanded rows are train-only agent-silver augmentation.
Do not describe the dataset as expert-adjudicated, multi-annotator, or formal gold-standard.

## ASRS source boundary
Raw ASRS narrative text is not redistributed. Obtain ASRS records via NASA ASRS Database
Online under the official ASRS caveats. See `DATASET_NOTICE.md` and
`protocols/ASRS_ACCESS_AND_QUERY_PROTOCOL.md`.

## Generative AI disclosure
AI-assisted tools (OpenAI ChatGPT/Codex and Anthropic Claude) were used for code generation,
experiment scripting, table organization, and drafting; the author verified all outputs and
takes full responsibility.

## Citation
A manuscript/preprint citation will be added on release. Target venue: Machine Learning with Applications.
