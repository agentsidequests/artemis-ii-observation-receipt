# Stage 10U — Camera-Target Shortcut Canary

- Verification: `PASS`
- Evidence state: `VERIFIED_CAMERA_TARGET_ASSOCIATION_CANARY`
- Labeled source exposures / target classes / cameras: `3,413` / `23` / `3`
- Camera-exclusive target classes / exposures: `19` / `807` (`23.645%`)
- Z9 labeled exposures carrying Sunset: `593` / `734` (`80.790%`)
- Camera-only rule accuracy / majority baseline / lift: `67.741%` / `54.498%` / `13.243%`
- Rule balanced accuracy / sensitivity / specificity: `65.302%` / `38.184%` / `92.419%`
- Pixel payload bytes opened: `0`

## Verified

Among 3,413 source exposures with nonblank target labels in the verified complete-action cohort, 19 of 23 target classes occur on one camera only and account for 807 exposures. The Data User Guide independently identifies the Z9 as the primary eclipse camera; 593 of its 734 labeled exposures carry Sunset. The descriptive rule 'predict Sunset iff Z9' scores 67.741% accuracy against a 54.498% majority baseline, but only 38.184% sensitivity.

## Decision use

Treat camera identity as a prospective shortcut variable for any later target classifier. Require a camera-only baseline and camera/event-stratified evaluation before interpreting pixel performance. The metadata association does not prove that pixels reveal camera identity or that a model would exploit it.

## Claim ceiling

Stage 10U may establish a descriptive acquisition-device/target-label association in the verified complete-action cohort: among 3,413 source exposures with nonblank target labels, 19 of 23 target classes occur on one camera only and account for 807 exposures; 593 of 734 labeled Z9 exposures carry Sunset. The document-nominated rule 'predict Sunset iff Z9' scores 67.741% accuracy versus a 54.498% majority baseline, 65.302% balanced accuracy, 80.790% precision, and 38.184% sensitivity. Sunset itself spans two cameras, so camera identity is neither necessary nor sufficient. The result cannot establish target-label correctness, causation, pixel-encoded camera identity, actual model shortcut use, leakage, a held-out performance gain, archive-wide or cross-mission prevalence, scientific discovery, novelty, or priority.

## Hard negatives

- `call_target_labels_ground_truth`: REJECTED
- `claim_camera_causes_target`: REJECTED
- `claim_camera_identity_sufficient`: REJECTED
- `call_diagnostic_rule_held_out_model`: REJECTED
- `infer_pixels_encode_camera`: REJECTED
- `claim_image_model_uses_shortcut`: REJECTED
- `call_association_observed_leakage`: REJECTED
- `infer_model_performance_effect`: REJECTED
- `generalize_association_beyond_cohort`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_camera_target_canary`: REJECTED
