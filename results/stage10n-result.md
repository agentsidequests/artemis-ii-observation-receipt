# Stage 10N — Temporal-Adjacency Split Sensitivity

- Verification: `PASS`
- Evidence state: `VERIFIED_TEMPORAL_ADJACENCY_SPLIT_SENSITIVITY`
- Verified complete actions: `2,166`
- Hypothetical split: `80%/20%` at the action level
- Pixel payload bytes opened: `0`

## Verified conditional result

Action-level grouping removes the exact representation and bracket-sibling crossings modeled in Stage 10M, but it does not guarantee temporal-episode independence. Under a conditional five-second same-camera adjacency rule, 1,656 of 2,166 actions lie in multi-action clusters; independent 80/20 action assignment puts an expected 1,239.004 actions (57.202%) in clusters that cross the partition. The conditional rate ranges from 4.046% at one second to 86.193% at thirty seconds. At five seconds, 290 of 306 multi-action clusters carry one activity value across all admitted exposures, and 132 of 139 target-bearing clusters carry one target value. Because those facets are time-derived and partly curated, this is structural concordance rather than independent scene validation.

## Threshold sensitivity

- `1s`: `181` actions in multi-action clusters; expected `87.626` actions (`4.046%`) in crossing clusters
- `2s`: `1,017` actions in multi-action clusters; expected `699.984` actions (`32.317%`) in crossing clusters
- `5s`: `1,656` actions in multi-action clusters; expected `1239.004` actions (`57.202%`) in crossing clusters
- `10s`: `1,912` actions in multi-action clusters; expected `1533.155` actions (`70.783%`) in crossing clusters
- `30s`: `2,108` actions in multi-action clusters; expected `1866.950` actions (`86.193%`) in crossing clusters

## Non-independent facet diagnostic

At five seconds, `290` / `306` multi-action clusters (`94.771%`) carry one activity value across their admitted exposures. Of `139` clusters with any target value, `132` (`94.964%`) carry one target value. These time-derived and partly curated facets corroborate archive structure; they do not independently validate scene identity, label correctness, or image similarity.

## Decision use

Treat reconstructed action identity as a necessary minimum grouping key, not a complete evaluation design. A real task must freeze whether scene, target, time, operator, or acquisition episode creates broader dependence before a split is built.

## Claim ceiling

Stage 10N may establish a threshold-sensitive conditional split hazard for temporally adjacent same-camera complete actions in the verified cohort and report non-independent concordance with archive activity and target facets. It cannot call temporal clusters semantic scenes or independent observations, claim observed leakage or a performance effect, designate a universal time threshold, call action grouping universally sufficient, treat time-derived and partly curated facets as independent validation or ground truth, infer facet correctness or image similarity, include unadmitted records as actions, mix cameras into one temporal sequence, infer image content, or claim global novelty or priority.

## Hard negatives

- `call_temporal_clusters_semantic_scenes`: REJECTED
- `call_expected_crossing_observed_leakage`: REJECTED
- `claim_action_grouping_is_universally_sufficient`: REJECTED
- `promote_one_threshold_to_ground_truth`: REJECTED
- `mix_camera_serials_in_clusters`: REJECTED
- `count_unadmitted_records_as_actions`: REJECTED
- `infer_model_performance_effect`: REJECTED
- `claim_global_priority`: REJECTED
- `call_facet_concordance_independent_validation`: REJECTED
- `infer_facets_are_correct_or_images_are_similar`: REJECTED
- `open_pixels_for_temporal_sensitivity`: REJECTED
