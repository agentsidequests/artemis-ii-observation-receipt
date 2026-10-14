# Stage 10Z — Action-to-Plan Membership Ledger

- Verification: `PASS`
- Evidence state: `VERIFIED_MANY_TO_MANY_ACTION_PLAN_LEDGER`
- Complete actions / relationship rows: `2,166` / `1,602`
- Actions with 0 / 1 / 2 / 3 memberships: `626` / `1,482` / `54` / `4`
- Unassigned cohort-byte share: `25.316%`
- Overlapping-window byte inflation without deduplication: `5.432%`
- Ledger: `results/stage10z-action-plan-membership.csv`
- Ledger bytes / SHA-256: `398,284` / `819e1da2f132488b99d403cdc9b9335fe5e55228fec4fd6277629ddbaf21ab38`
- Pixel payload bytes opened: `0`

## Verified

Scheduled plan windows do not partition the 2,166 complete actions. Of those actions, 626 match no timed plan window, 1,482 match one, 54 match two, and four match three. The deterministic ledger preserves all actions and all 1,602 action-window relationships without forcing a single owner.

## Decision use

Use the ledger as a many-to-many join. Dropping unmatched actions would omit 25.316% of cohort bytes; summing overlapping plan windows without action-level deduplication would overcount assigned bytes by 5.432%.

## Claim ceiling

Stage 10Z may establish that scheduled-window membership is many-to-many and incomplete for the verified complete-action cohort: 626 actions match no timed plan window, 1,482 match one, 54 match two, and four match three. It may provide a deterministic 2,228-row ledger that preserves all 2,166 actions and all 1,602 action-window relationships. It may quantify that naïvely summing plan-window totals would overcount assigned exposure rows by 4.342% and assigned bytes by 5.432%, while dropping unmatched actions would omit 25.316% of cohort bytes. It may establish that the two deterministic relationship ledgers total 10,470,310 bytes—0.000644% of the 1.625-TB cohort footprint. It cannot establish a canonical event ontology, independence, one true owner, target correctness, target imputation, a model partition, archive defect, scientific discovery, novelty, or priority.

## Hard negatives

- `force_single_plan_membership`: REJECTED
- `drop_unassigned_actions`: REJECTED
- `call_plan_windows_a_partition`: REJECTED
- `sum_overlapping_windows_without_deduplication`: REJECTED
- `call_unassigned_actions_out_of_scope`: REJECTED
- `infer_target_from_plan_membership`: REJECTED
- `call_membership_an_independent_event`: REJECTED
- `assign_model_partition_from_membership`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_membership_ledger`: REJECTED
