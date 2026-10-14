# Stage 10M — AI Split Related-Group Crossing Hazard

- Verification: `PASS`
- Evidence state: `VERIFIED_EXPECTED_RANDOM_SPLIT_GROUP_CROSSING_HAZARD`
- Complete three-/five-exposure actions: `1,612` / `554`
- 80/20 product-split expected action crossing: `1930.148` / `2,166` (`89.111%`)
- 80/20 exposure-split expected action crossing: `1146.048` / `2,166` (`52.911%`)
- Action-group split crossing: `0%` by construction
- Pixel payload bytes opened: `0`

## Verified model

Under the frozen independent 80/20 product-level split model, an expected 1,930.148 of 2,166 complete actions (89.111%) place related products on both sides. Grouping the three representations by exposure but splitting exposure identities independently still crosses an expected 1,146.048 actions (52.911%). Splitting by complete action crosses zero by construction.

## Decision use

For image-model evaluation on this verified cohort, use the reconstructed action identity as the minimum split key rather than product or exposure ID. This controls the exact representation and bracket-sibling dependence measured here; a real task may require broader grouping by scene, target, time, or source episode.

## Claim ceiling

Stage 10M may establish expected related-group crossing under the frozen independent Bernoulli split model for the verified complete-action cohort. It may show why product-, exposure-, and action-level splits are different evaluation designs. It cannot claim observed leakage, contamination of any actual pipeline, byte-identical representations, identical bracket siblings, universal sufficiency of action grouping, statistical significance, performance impact, archive defect, image content, or global novelty or priority.

## Robustness scenarios

- `70%/30%`: product-level action crossing `96.874%`; exposure-level `68.103%`
- `80%/20%`: product-level action crossing `89.111%`; exposure-level `52.911%`
- `90%/10%`: product-level action crossing `65.901%`; exposure-level `30.568%`

## Hard negatives

- `call_expected_crossing_observed_leakage`: REJECTED
- `claim_an_existing_pipeline_is_contaminated`: REJECTED
- `treat_three_representations_as_byte_identical`: REJECTED
- `call_bracket_siblings_identical_images`: REJECTED
- `generalize_beyond_complete_action_cohort`: REJECTED
- `claim_action_grouping_solves_every_evaluation_leak`: REJECTED
- `claim_statistical_significance`: REJECTED
- `claim_global_priority`: REJECTED
- `open_pixels_for_split_model`: REJECTED
