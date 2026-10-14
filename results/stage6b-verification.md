# Stage 6B — Specialist Literature Pressure Test

- Result: `PASS`
- Evidence state: `VERIFIED_SPECIALIST_PRESSURE_CORRECTION`
- Disposition: `STOP_QUANTIFIED_HEADLINE_CONTINUE_BOUNDED_TEST`
- Retired claim: `orientale_aggregate_texture_10_60x_below_object_resolution`
- Replacement candidate: `held_out_semantic_cross_instrument_concordance`
- Scored network bytes: `0`

## Decision-changing correction

The Stage 6A 10–60× arithmetic is numerically correct but scientifically non-diagnostic. It divides a nominal LOLA roughness measurement baseline by a task-specific object-recognition bound. Specialist sources show that those quantities have different meanings and cannot measure the crew's perceptual reach.

LOLA computes roughness over short horizontal baselines and aggregates many measurements into regional windows. The crew could see a large regional pattern correlated with short-baseline roughness without detecting individual features at the roughness baseline. NASA's 1–6 km range comes from one rille-recognition case whose visibility also depended on range, angle, illumination, contrast, and competing visual stimuli.

The subresolution texture paper remains mechanism plausibility for controlled hair-like line textures only. It does not validate lunar-terrain perception.

## Adjudication

- `stage6a_ratio_arithmetic`: `CORRECT`
- `stage6a_ratio_commensurability`: `REJECTED_UNLIKE_QUANTITIES`
- `stage6a_ratio_explanatory_status`: `NON_DIAGNOSTIC`
- `nasa_orientale_component_status`: `ALREADY_PUBLISHED_QUALITATIVE_CONCORDANCE`
- `rimae_resolution_status`: `TASK_SPECIFIC_BOUND_NOT_GLOBAL_FLOOR`
- `psychophysics_transfer_status`: `PLAUSIBILITY_ONLY_NO_ARTEMIS_VALIDATION`
- `public_lead_status`: `STOP_10_60X_HEADLINE`

## Replacement bounded test

**Question:** Across Artemis II observations not used in NASA's Orientale example, do blindly coded crew texture descriptors predict independent terrain layers better than competing layers and simple large-scale morphology?

**Treatment:** Blind-code texture terms by target, time, observer, and optical tool; localize each episode using existing target, image, annotation, and geometry evidence; compare predeclared LOLA roughness scales against Diviner rock abundance, topography, albedo, and large-scale geologic-unit controls; reserve Orientale as prior evidence rather than evaluation data.

**Oracle:** A predeclared held-out result must show that texture-language classifications discriminate one or more roughness products beyond competing map layers and large-scale unit identity, with viewing geometry and optical tool recorded as covariates.

**Hard negative:** If performance disappears after controlling for broad terrain class, illumination, view geometry, or map-layer correlation, retain NASA's qualitative one-case result and stop.

**Novelty ceiling:** `NOVELTY_UNESTABLISHED until a held-out result survives and current prior art is rechecked.`

## Claim ceiling

- NASA already reports one qualitative correspondence between crew-described Orientale texture and a LOLA roughness map rather than a Diviner rock-abundance map.
- The Stage 6A 10-60x arithmetic is numerically correct but compares a roughness measurement baseline with a task-specific object-recognition bound; it is not a validated measure of perceptual reach.
- LOLA roughness products aggregate short-baseline measurements into regional map patterns, so concordance does not show that the crew directly or indirectly sensed individual hectometer-scale features.
- Primary psychophysics supports subresolution texture discrimination under controlled line-texture conditions but does not validate an Artemis II lunar-terrain mechanism.
- A held-out multi-target semantic-to-map comparison could establish a new bounded relation; no such result exists yet.

## Next-step logic

**Recommended:** Do not draft the 10-60x article. Run the smallest held-out semantic cross-instrument concordance canary on non-Orientale observations first.

Why: It replaces a non-diagnostic ratio with a falsifiable result that could distinguish genuine terrain information in crew language from broad geology, illumination, and correlated map layers.

Fallback: If localization or independent controls are inadequate, publish no new scientific claim; retain NASA's qualitative human-plus-instrument interpretation and use the archive only as a methodological case study.

Stop: Do not widen to full-archive imagery, train on Orientale and test on Orientale, or revive the sub-resolution headline without a task-native specialist oracle.

## Hard negatives

- `equate_baseline_with_visible_object_size`: REJECTED
- `promote_rimae_case_to_global_acuity_floor`: REJECTED
- `transfer_hair_texture_mechanism_to_lunar_terrain`: REJECTED
- `claim_nasa_orientale_component_as_new`: REJECTED
- `retain_10_60x_as_public_headline`: REJECTED
- `use_orientale_as_both_prior_and_held_out_test`: REJECTED
