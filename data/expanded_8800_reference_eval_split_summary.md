# Expanded 8,800 Reference-Evaluation Split Summary

Created: 2026-06-04

## Boundary

The 3,800 expanded agent-silver rows are added to train only. Dev and test remain the original author-verified seed rows with local consistency-audit support.

## Split Counts

- `train`: 7299
- `dev`: 750
- `test`: 751

## Leakage Checks

- Duplicate ACNs across corpus: 0
- Exact normalized text hashes appearing in more than one split: 0
- Raw ASRS narrative text included in split CSVs: `false`

## Role Counts By Split

### `train`

- `expanded_3800_agent_silver`: 3800
- `seed_5000_author_verified_local_audit`: 3499

### `dev`

- `seed_5000_author_verified_local_audit`: 750

### `test`

- `seed_5000_author_verified_local_audit`: 751

## Screening Status By Split

### `train`

- `include_ground_cabin_event`: 6218
- `exclude_not_ground_or_cabin`: 1068
- `uncertain_needs_review`: 13

### `dev`

- `include_ground_cabin_event`: 631
- `exclude_not_ground_or_cabin`: 117
- `uncertain_needs_review`: 2

### `test`

- `include_ground_cabin_event`: 631
- `exclude_not_ground_or_cabin`: 118
- `uncertain_needs_review`: 2

## Primary Event Type By Split

### `train`

- `pushback_towing_chocks`: 1278
- `not_relevant`: 1068
- `baggage_cargo_weight_balance`: 878
- `hazmat_mobility_device`: 807
- `other_ground_operation`: 770
- `ramp_ground_handling`: 742
- `maintenance_readiness`: 565
- `gate_or_boarding`: 547
- `jetway_or_gate_infrastructure`: 250
- `dispatch_or_coordination`: 193
- `cabin_service`: 130
- `fueling`: 71

### `dev`

- `not_relevant`: 117
- `pushback_towing_chocks`: 109
- `baggage_cargo_weight_balance`: 91
- `hazmat_mobility_device`: 88
- `other_ground_operation`: 78
- `ramp_ground_handling`: 74
- `maintenance_readiness`: 65
- `gate_or_boarding`: 56
- `jetway_or_gate_infrastructure`: 24
- `dispatch_or_coordination`: 20
- `fueling`: 14
- `cabin_service`: 14

### `test`

- `not_relevant`: 118
- `pushback_towing_chocks`: 109
- `baggage_cargo_weight_balance`: 90
- `hazmat_mobility_device`: 88
- `other_ground_operation`: 78
- `ramp_ground_handling`: 74
- `maintenance_readiness`: 65
- `gate_or_boarding`: 55
- `jetway_or_gate_infrastructure`: 23
- `dispatch_or_coordination`: 21
- `cabin_service`: 15
- `fueling`: 15

## Provenance By Split

### `train`

- `new_agent_silver_expansion`: 3800
- `preserved_seed_label`: 3499

### `dev`

- `preserved_seed_label`: 750

### `test`

- `preserved_seed_label`: 751

