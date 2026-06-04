---
type: protocol_note
domain: aviation-nlp
status: v0.1
created: 2026-06-02
tags:
  - asrs
  - api
  - reproducibility
---

# ASRS API Access Notes

## Evidence Boundary

These notes describe local access to the public ASRS Database Online endpoints as observed on 2026-06-02 and used for Q09-Q12 expansion on 2026-06-03. They do not change the official ASRS caveats: ASRS reports are voluntary, self-reported, not verified by NASA, and not valid for prevalence estimation.

Official source:

`https://asrsdbol.arc.nasa.gov/`

## Endpoints Observed

The official web interface calls:

- `GET https://asrsdbol.arc.nasa.gov/dbol/reference/`
- `POST https://asrsdbol.arc.nasa.gov/dbol/search/`
- `POST https://asrsdbol.arc.nasa.gov/dbol/details/`

The reference endpoint returned:

- `totalReports`: 329112
- `requireLogon`: false
- metadata groups including `Person.Narrative`, `Person.Callback`, `Time.Date`, `Events.Anomaly.Ground Event / Encounter`, `Person.Function.Ground Personnel`, and other ASRS fields.

## Search Payload

The successful browser-captured text-search payload for `GATE` was:

```json
{
  "narrative": true,
  "synopsis": true,
  "callback": true,
  "searchRelatedWords": false,
  "eavs": [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
  "fullformOnly": true,
  "abbreviatedOnly": false,
  "generalAviation": false,
  "uas": false,
  "acns": "",
  "text": "GATE",
  "locations": [],
  "stateProvinces": [],
  "makeModels": []
}
```

Direct API verification:

- The same `GATE` payload returned 33,150 ACNs from `dbol/search/`.
- The details endpoint accepted comma-separated ACN lists and returned full detail records, including `acn`, `dateOfOccurrence`, `synopsis`, `people`, `equipment`, `components`, and EAV metadata.

## Reproducibility Script

Local script:

`scripts\asrs_api_workflow.py`

Commands run on 2026-06-02:

```powershell
python scripts\asrs_api_workflow.py --counts
python scripts\asrs_api_workflow.py --collect Q02
python scripts\asrs_api_workflow.py --collect Q04
```

Commands run on 2026-06-03:

```powershell
python scripts\asrs_api_workflow.py --collect Q09
python scripts\asrs_api_workflow.py --collect Q10
python scripts\asrs_api_workflow.py --collect Q11
python scripts\asrs_api_workflow.py --collect Q12
python scripts\asrs_api_workflow.py --counts
python scripts\build_expanded_corpus.py
python scripts\silver_label_corpus.py
```

Generated files:

- `data\manifests\query_counts_2026-06-02.csv`
- `data\raw\asrs_api\Q02_details_2026-06-02.json`
- `data\raw\asrs_api\Q04_details_2026-06-02.json`
- `data\manifests\Q02_candidate_manifest_2026-06-02.csv`
- `data\manifests\Q04_candidate_manifest_2026-06-02.csv`
- `data\manifests\candidate_records_manifest.csv`
- `data\manifests\pilot_screening_sample_200_2026-06-02.csv`
- `data\manifests\screening_manifest.csv`
- `data\manifests\query_counts_2026-06-03.csv`
- `data\raw\asrs_api\Q09_details_2026-06-03.json`
- `data\raw\asrs_api\Q10_details_2026-06-03.json`
- `data\raw\asrs_api\Q11_details_2026-06-03.json`
- `data\raw\asrs_api\Q12_details_2026-06-03.json`
- `data\manifests\candidate_records_manifest_expanded_2026-06-03.csv`
- `data\manifests\silver_corpus_5000_manifest_2026-06-03.csv`
- `data\manifests\silver_corpus_5000_labels_2026-06-03.csv`

## Query Counts

The counts below are current ASRS search counts before local date filtering. They are not prevalence estimates.

| Query | Count |
|---|---:|
| Q01 Cabin service | 4,090 |
| Q02 passenger assistance / wheelchair / PRM | 298 |
| Q03 gate / boarding / deboarding | 11,723 |
| Q04 ramp / ground handling / pushback | 4,380 |
| Q05 baggage / cargo / weight and balance | 10,566 |
| Q06 fueling | 8,100 |
| Q07 maintenance readiness | 26,018 |
| Q08 dispatch / operations coordination | 30,467 |
| Q09 refined cabin service / ground | 3,052 |
| Q10 refined gate / boarding / door | 5,266 |
| Q11 refined baggage / cargo / weight-balance | 5,923 |
| Q12 refined fueling | 1,960 |
| Q13 refined maintenance readiness | 22,949 |
| Q14 refined dispatch / coordination | 16,267 |

## Collected Candidate Sets

Date filter applied locally:

`2011-2025`

Collected sets:

| Query | Search ACNs | Detail records fetched | Kept in 2011-2025 |
|---|---:|---:|---:|
| Q02 | 298 | 298 | 216 |
| Q04 | 4,380 | 4,380 | 2,692 |
| Q09 | 3,052 | 3,052 | 1,804 |
| Q10 | 5,266 | 5,266 | 2,658 |
| Q11 | 5,923 | 5,923 | 2,530 |
| Q12 | 1,960 | 1,960 | 936 |

Deduplicated combined candidate pool:

- 8,801 unique ACNs across Q02/Q04/Q09/Q10/Q11/Q12.
- Main manifest: `data\manifests\candidate_records_manifest.csv`.

Pilot screening sample:

- 200 records.
- Deterministic random seed: `20260602`.
- 95 Q02-only records, 100 Q04-only records, and 5 Q02/Q04-overlap records.
- Active screening file: `data\manifests\screening_manifest.csv`.

Silver corpus:

- 5,000 records.
- Manifest: `data\manifests\silver_corpus_5000_manifest_2026-06-03.csv`.
- Labels: `data\manifests\silver_corpus_5000_labels_2026-06-03.csv`.
- Original label provenance: agent-generated silver labels, `not_human_verified`.
- Author-verified derivative: `data\manifests\author_verified_single_reviewer_labels_5000_2026-06-03.csv`.
- Cross-audit: `reports\author_verification_cross_audit_5000_2026-06-03.md`.
- Record-level splits: `data\splits\record_level_split_assignments_2026-06-03.csv`.

## Method Risk Notes

- Q03, Q05, Q06, Q07, and Q08 are broad. They should not be bulk-collected until screening results show which query refinements improve relevance.
- Q13 and Q14 remain too broad at the current refined definitions and should not be bulk-collected without further narrowing.
- Q02 is relevant but thematically narrow; many records involve mobility-device batteries, wheelchair paperwork, passenger-assistance documents, and jetway/gate events.
- Q04 is broader and important for ramp/pushback/towing/chocking/ground-handling coverage.
- Search counts are ASRS current counts and include records outside the initial 2011-2025 manuscript window until details are fetched and date-filtered locally.
- Raw JSON contains ASRS narrative text and should remain local until redistribution terms are confirmed.
- The 5,000-record labels now have an author-verified derivative with local consistency-audit support. They should not be described as formal expert consensus, independently adjudicated gold, second-reviewer verified, or inter-annotator-agreement-backed unless those artifacts are added later.
