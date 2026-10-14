# Stage 7A — Held-Out Semantic-to-LOLA Canary

- Verification: `PASS`
- Signal state: `COARSE_SEMANTIC_LOLA_CONCORDANCE`
- Disposition: `CONTINUE_CONTROLLED_MULTI_TARGET`
- Frozen prediction: `Vavilov rougher than Hertzsprung`
- Acquisition bytes: `2362387`
- Scored verification network bytes: `0`

## Result

The pre-instrument transcript direction survived the frozen canary: equal-size regions centered on Vavilov are rougher in the LOLA products than equal-size regions centered on Hertzsprung at all required baselines, with the required robustness across radii.

| LOLA baseline | Radius | Vavilov median slope | Hertzsprung median slope | Ratio | Descriptive superiority |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 57 m | 10 km | 5.1300° | 2.9902° | 1.716 | 0.963 |
| 57 m | 20 km | 5.5125° | 3.0727° | 1.794 | 0.825 |
| 57 m | 30 km | 6.1297° | 3.1282° | 1.959 | 0.818 |
| 225 m | 10 km | 4.2285° | 1.9560° | 2.162 | 0.987 |
| 225 m | 20 km | 5.0107° | 2.0888° | 2.399 | 0.844 |
| 225 m | 30 km | 5.4668° | 2.2425° | 2.438 | 0.821 |
| 560 m | 10 km | 3.7065° | 1.0605° | 3.495 | 0.982 |
| 560 m | 20 km | 4.2180° | 1.3807° | 3.055 | 0.826 |
| 560 m | 30 km | 4.7370° | 1.5945° | 2.971 | 0.797 |

Primary thresholds: `PASS`. Robustness: `9/9` comparisons reached the frozen 1.10 ratio threshold.

The superiority value is descriptive only. LOLA values are interpolated from overlapping windows and are not treated as independent observations; no p-value is claimed.

## Scientific ceiling

A pass establishes only coarse directional concordance for one same-observer, two-target contrast under fixed map sampling. It does not establish causation, perception below resolution, observer generality, independence from geology or morphology, statistical significance, novelty, or a publishable scientific result.

The comparison uses one observer, two morphologically different craters, coarse center-disk localization, and no independent control for crater age, geology, illumination, albedo, or exact optical tool. Even a strong match cannot distinguish a subtle human sensing mechanism from obvious regional morphology.

## Next-step logic

- If passed: Admit one larger prospectively coded multi-target test with competing map layers, morphology and geologic-unit controls, illumination and viewing metadata, and at least one additional observer if available.
- If failed: Stop the semantic roughness lane and retain NASA's qualitative Orientale interpretation only.
- If indeterminate: Stop acquisition and repair only the named source or localization boundary if existing metadata can do so without bulk imagery.

## Hard negatives

- `use_orientale_as_evaluation_data`: REJECTED
- `change_semantic_direction_after_lola_access`: REJECTED
- `compare_unequal_physical_radii`: REJECTED
- `accept_only_one_lola_baseline`: REJECTED
- `accept_a_ratio_below_the_frozen_threshold`: REJECTED
- `treat_interpolated_pixels_as_independent_samples`: REJECTED
- `claim_control_for_geology_illumination_albedo_or_morphology`: REJECTED
- `claim_novel_science_from_a_two-target_same-observer_canary`: REJECTED
- `claim_sub_resolution_perception`: REJECTED
