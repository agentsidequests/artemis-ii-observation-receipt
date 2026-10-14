# Stage 10T — Task-Conditioned Unit Ladder

- Verification: `PASS`
- Evidence state: `VERIFIED_TASK_CONDITIONED_UNIT_LADDER`
- Products → exposures → actions → conditional bursts → event: `2,535` → `845` → `169` → `24` → `1`
- Whole-event binary allocations / valid two-sided allocations: `2` / `0`
- Pixel payload bytes opened: `0`

## Verified

One plan-bounded Sunset event can be counted as 2,535 archive products, 845 exposure identities, 169 complete bracket actions, 24 conditional same-camera bursts, or one scheduled event. These are task-conditioned candidate units, not five interchangeable or independently validated sample counts. With one event there are two whole-event binary allocations and zero that place distinct Sunset events in both train and test.

## Decision use

For new-Sunset-event generalization, a two-sided internal Artemis II event split is infeasible: the single event must be entirely in train or test, or the claim must narrow. Within-event temporal, HDR, representation, and retrieval tasks remain possible, but require their own grouping and evaluation contracts.

## Claim ceiling

Stage 10T may establish that the same fixed eight-minute block has five task-relevant counts—2,535 products, 845 exposure identities, 169 complete bracket actions, 24 conditional same-camera bursts, and one scheduled Sunset event—and that none is a universal independent-sample count. With one event, there are two binary whole-event allocations and zero allocations that put at least one distinct Sunset event in both train and test. Splitting at any finer listed level can support only a narrower within-event or representation-level estimand, not new-Sunset-event generalization. It cannot establish visual similarity, independence at any listed level, actual leakage, model performance, a universally correct split, cross-mission representativeness, scientific discovery, novelty, or priority.

## Hard negatives

- `call_every_unit_independent`: REJECTED
- `choose_one_universal_unit`: REJECTED
- `claim_event_level_modeling_impossible`: REJECTED
- `call_within_event_evaluation_invalid`: REJECTED
- `invent_second_sunset_event`: REJECTED
- `call_hypothetical_split_observed_leakage`: REJECTED
- `infer_model_performance_effect`: REJECTED
- `claim_cross_mission_representativeness`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_unit_ladder`: REJECTED
