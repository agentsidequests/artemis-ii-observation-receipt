# Stage 11H — Protocol–Context Alignment

- Verification: `PASS`
- Evidence state: `VERIFIED_PROTOCOL_CONTEXT_ALIGNMENT`
- Plan-associated action union: `1540`
- Three- / five-exposure actions: `994` / `546`
- Five-exposure action / product shares: `35.455%` / `47.794%`
- Product-share amplification: `1.348039×`
- Camera 3500015 run shape: `3 → 5 → 3` with `2` transitions
- Camera 3500017: `7` / `7` three-exposure actions
- Camera 3920019: `156` / `156` five-exposure actions
- Camera 3920019 action / product shares: `10.130%` / `13.655%`
- Pixel payload bytes opened: `0`

## Verified

Within the deduplicated plan-associated action union, the five-exposure protocol is aligned with camera and contiguous time regimes. Five-exposure actions are 35.455% of actions but 47.794% of flat products; camera 3920019 rises from 10.130% of actions to 13.655% of products.

## Decision use

A flat product table can inherit operational camera/time structure from the acquisition protocol before any pixel feature is measured. Preserve the intentional exposures, but make the sampling estimand and protocol strata explicit.

## Claim ceiling

Stage 11H may establish that the deduplicated union of plan-associated actions contains 994 three-exposure and 546 five-exposure actions; five-exposure actions are 35.455% of actions but 47.794% of flat products. It may establish that camera 3920019's 156 associated actions are all five-exposure and rise from 10.130% of actions to 13.655% of flat products, camera 3500017's seven are all three-exposure, and camera 3500015's 390 five-exposure actions form one contiguous in-sample time run between three-exposure runs. It cannot treat plan memberships as a partition, call the fitted camera/time description held out or generalizable, make bracket length a target or content label, assert an actual sampler or observed model bias, recommend discarding intentional exposures, nominate a universal correction, extend beyond admitted records, or make a novelty, priority, or physical-science claim.

## Hard negatives

- `call_plan_memberships_a_partition`: REJECTED
- `call_fitted_regime_rule_held_out`: REJECTED
- `call_bracket_length_a_target_or_content_label`: REJECTED
- `claim_actual_sampler_is_uniform_products`: REJECTED
- `claim_observed_model_bias`: REJECTED
- `recommend_dropping_bracket_exposures`: REJECTED
- `claim_one_universal_correct_weighting`: REJECTED
- `generalize_to_unadmitted_archive_records`: REJECTED
- `claim_novelty_or_priority`: REJECTED
- `open_pixels_during_alignment_test`: REJECTED
