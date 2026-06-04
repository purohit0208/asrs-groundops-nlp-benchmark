# Excluded Materials

Created: 2026-06-04

| path or pattern | reason |
|---|---|
| `data/raw/asrs_api` | Raw ASRS detail JSON and narratives; do not redistribute until ASRS text redistribution/use terms are resolved. |
| `literature/papers` | Downloaded full-text papers; local reading evidence only, not part of release package. |
| `literature/consensus_reports` | Consensus reports are search aids/subscription outputs, not public release material. |
| `outputs/baselines/*/classification_report_*` | Detailed model diagnostic files are reproducible from predictions; not needed in compact release candidate. |
| `outputs/baselines/record_level_2026-06-04/error_analysis/tfidf_error_samples*` | Error sample files may contain evidence snippets; excluded from sanitized release. |
| `data/manifests/*labels*.csv original files` | Original label files contain evidence-snippet columns; sanitized derivative is included instead. |
| `data/splits/*records*.csv original files` | Original split files contain evidence-snippet/raw-path columns; sanitized derivative is included instead. |
