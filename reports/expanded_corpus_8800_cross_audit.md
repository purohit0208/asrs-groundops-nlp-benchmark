# Expanded 8,800 Corpus Cross-Audit

Created: 2026-06-04

## Files

- Expanded manifest: `data\manifests\expanded_corpus_8800_manifest_2026-06-04.csv`
- Expanded labels: `data\manifests\expanded_corpus_8800_labels_2026-06-04.csv`

## Selection Boundary

- Source pool: 8,801 unique ASRS candidate records from Q02/Q04/Q09/Q10/Q11/Q12.
- Target corpus: 8,800 records.
- Preserved seed: all 5,000 author-verified seed rows with local consistency-audit support.
- Added records: 3,800 agent-labeled remaining candidates.
- Excluded record: ACN `1546910` / candidate `CAND_005021` / query `Q11` / date `2018-05`; selected for exclusion because it had the lowest combined synopsis/narrative text length among remaining candidates.

## Cross-Audit Result

- Overall result: `PASS_WITH_CAVEATS`
- Blocking internal-consistency errors: 0
- Rows checked: 8800
- Unique corpus IDs: 8800
- Unique ACNs: 8800
- Missing raw records: 0
- Missing manifest records: 0
- Duplicate corpus IDs: 0
- Duplicate ACNs: 0
- Label-rule mismatches against current classifier: 0
- Included rows without evidence snippet: 0
- Evidence snippets not found in source text: 0
- Rows outside 2011-2025 manifest window: 0

## Label Provenance Counts

- `seed_5000_author_verified_local_audit`: 5000
- `expanded_3800_agent_silver`: 3800

## Verification Status Counts

- `author_verified_single_reviewer`: 5000
- `agent_silver_expansion_not_human_verified`: 3800

## Screening Status Counts

- `include_ground_cabin_event`: 7480
- `exclude_not_ground_or_cabin`: 1303
- `uncertain_needs_review`: 17

## Primary Event-Type Counts

- `pushback_towing_chocks`: 1496
- `not_relevant`: 1303
- `baggage_cargo_weight_balance`: 1059
- `hazmat_mobility_device`: 983
- `other_ground_operation`: 926
- `ramp_ground_handling`: 890
- `maintenance_readiness`: 695
- `gate_or_boarding`: 658
- `jetway_or_gate_infrastructure`: 297
- `dispatch_or_coordination`: 234
- `cabin_service`: 159
- `fueling`: 100

## Multi-Event Flag Counts

- `false`: 5489
- `needs_author_review`: 3311

## Non-Exclusive Query Coverage

- `Q04`: 2692
- `Q10`: 2658
- `Q11`: 2529
- `Q09`: 1804
- `Q12`: 936
- `Q02`: 216

## Manuscript Boundary

- Do not call all 8,800 records human verified.
- Use the 5,000-row author-verified subset with local consistency-audit support as the verified reference split.
- Use the added 3,800 rows as weak-label training augmentation or robustness data.
- Raw ASRS narratives remain local except for the separately approved bounded remote LLM baseline.
