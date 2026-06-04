---
type: decision_record
domain: aviation-nlp
status: active
created: 2026-06-03
tags:
  - asrs
  - dataset-size
  - annotation
  - publication-strategy
---

# Dataset Size And Verification Decision

## Decision

The 200-record pilot sample is not the final dataset.

It is only a pilot screening sample used to:

- test query precision;
- expose false-positive patterns;
- refine event categories;
- draft annotation schema v0.2;
- decide which additional query families are needed.

After the user rejected a 1,000-record final corpus as too small, the manuscript dataset strategy was revised as follows:

- expanded screened candidate pool: at least 5,000 ASRS records;
- current final working corpus: 5,000 records sampled from the expanded public-ASRS candidate pool;
- original label status: agent-generated silver labels;
- author verification status: user/author reported on 2026-06-03 that all 5,000 labels were verified and no problems were found;
- derived label file: `data\manifests\author_verified_single_reviewer_labels_5000_2026-06-03.csv`;
- active derived label file: `data\manifests\author_verified_single_reviewer_labels_5000_2026-06-03.csv`;
- recommended manuscript-grade wording: `author-verified reference labels with local consistency-audit support`;
- wording to avoid unless carefully defined: unqualified `gold standard`, `expert consensus`, or `adjudicated ground truth`.

The agent cross-audit can verify reproducible consistency, evidence-span traceability, and data integrity. It is not a second human annotator.

## Why 200 Is Too Small

Two hundred records would be too small for the paper's intended contribution if presented as the final benchmark.

Main risks:

- weak train/dev/test splits;
- too few examples in smaller event classes such as fueling, cabin service, gate infrastructure, and maintenance readiness;
- high variance in model evaluation;
- reviewer concern that the paper is a small pilot rather than a reusable benchmark;
- limited ability to compare rules, classical ML, encoder models, and LLM structured extraction.

## Practical Target

Implemented final screened record plan:

| Source family | Target screened records | Purpose |
|---|---:|---|
| Q02 passenger assistance / mobility-device handling | 216 in 5,000 corpus | Keep strong wheelchair/battery/hazmat cluster without letting it dominate. |
| Q04 ramp / pushback / towing / chocks | 1,310 in 5,000 corpus | Core ground-handling cluster. |
| Q09 cabin service / cabin readiness | 1,174 in 5,000 corpus | Add missing cabin-service category. |
| Q10 gate / boarding / door events | 1,564 in 5,000 corpus | Add gate/boarding/door-handling events. |
| Q11 baggage / cargo / weight-and-balance | 1,455 in 5,000 corpus | Add loading and weight/balance context. |
| Q12 fueling | 936 in 5,000 corpus | Add distinct fueling events. |
| Q13 refined maintenance readiness | not collected | Too broad at current query definition. |
| Q14 refined dispatch/coordination | not collected | Too broad at current query definition. |

Working total:

- 5,000 silver-labeled records.

Current silver screening result:

- 4,203 likely relevant ground/cabin records;
- 783 likely exclusions;
- 14 uncertain records.

Current verification result:

- `author_verified_single_reviewer` derivative created after user/author reported verification;
- agent cross-audit checked all 5,000 rows;
- blocking internal-consistency errors: 0;
- duplicate ACNs: 0;
- missing raw records: 0;
- label-rule mismatches: 0;
- included rows without evidence snippets: 0.

Current record-level benchmark size:

- 5,000 ASRS records in the active label corpus.
- Multi-event records are represented through primary and secondary event-type labels, not split into event-span or event-mention rows.
- Event-level extraction can be added only through a separate future protocol.

## Verification Rule

The agent can perform:

- query design;
- data collection;
- pre-screening;
- draft annotation;
- consistency checks;
- label-distribution analysis;
- error-spotting.

Manuscript-grade claims may say that the active derived label file was verified by the author and passed local consistency audits. The manuscript should avoid unqualified "gold standard", "expert consensus", "independently adjudicated", or "multi-annotator ground truth" language because independent annotation, inter-annotator agreement, disagreement, and adjudication artifacts are not present in this workspace.

Recommended final wording for the current path:

> Candidate records were retrieved from NASA ASRS Database Online using a reproducible query protocol. Draft labels were generated through an agent-assisted workflow based on predefined screening and event-type rules. The resulting 5,000-record label file was reviewed by the author. The labels are treated as author-verified reference labels with local consistency-audit support; no formal inter-annotator-agreement or adjudication ledger is included in the release artifacts.

Allowed wording if an independent subset is later added:

> An independently checked evaluation subset was created by an external reviewer or adjudicated review; remaining labels were used as author-verified or agent-assisted labels, as explicitly identified.

## Best Decision For This Paper

Use a transparent two-layer dataset:

1. `agent_silver_v0_2`
   - 5,000 records;
   - agent-labeled using the predefined schema;
   - includes evidence-oriented fields and uncertainty flags;
   - preserved as the original silver-label provenance layer.

2. `author_verified_single_reviewer`
   - 5,000 records;
   - derived after the user/author reported verification;
   - passed agent cross-audit with zero blocking consistency errors;
   - may be used as single-author-verified reference labels.

3. Local consistency-audit support
   - 5,000 records checked for row uniqueness, raw-record traceability, rule consistency, date-window consistency, evidence-snippet availability in working files, duplicate ACNs, and split leakage;
   - passed agent cross-audit with zero blocking consistency errors;
   - supports reproducibility and internal consistency, not independent human adjudication.

This is defensible if the manuscript is transparent that the labels are author verified with local consistency-audit support, while not overstating formal adjudication or expert consensus.

## Current Status

As of 2026-06-03:

- 8,801 unique Q02/Q04/Q09/Q10/Q11/Q12 candidates exist after local 2011-2025 filtering.
- A 5,000-record silver corpus manifest has been generated.
- Agent silver labeling produced 4,203 likely relevant records, 783 likely exclusions, and 14 uncertain records.
- The 200-record pilot remains useful as a schema/query-development pilot, not as the final dataset.
- The user/author reported verifying the full 5,000-label file and finding no problems.
- Leakage-safe record-level splits were generated: 3,499 train, 750 dev, 751 test.
- Exact normalized text hashes crossing splits: 0.

## Next Data Action

Run the next modeling-preparation tasks:

- decide how to handle the 1,965 rows marked `needs_author_review` for possible multi-event splitting;
- create event-level extraction rows for included records;
- keep the original agent-silver and author-verified layers separate in all release artifacts.

Use `author-verified reference labels with local consistency-audit support` in manuscript text. Avoid unqualified `gold standard` unless the paper explicitly defines the term and discloses the available verification artifacts.
