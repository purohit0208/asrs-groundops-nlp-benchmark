# Coarse 6-class event taxonomy (adopted 2026-06-19)

Derived from the test-retest disagreement structure; the original 12-class scheme had
test-retest Cohen's kappa = 0.36, the coarse scheme reaches kappa = 0.47 (0.55 given
agreed relevance). Mapping (fine -> coarse):

- not_relevant -> not_relevant
- hazmat_mobility_device -> hazmat_mobility_device
- maintenance_readiness -> maintenance_readiness
- baggage_cargo_weight_balance -> baggage_cargo
- cabin_service, gate_or_boarding, jetway_or_gate_infrastructure -> cabin_gate_passenger
- pushback_towing_chocks, ramp_ground_handling, other_ground_operation, fueling, dispatch_or_coordination -> ramp_servicing

Encoded as COARSE_PRIMARY in scripts/run_finetuned_transformer_baseline.py (use --coarse).
