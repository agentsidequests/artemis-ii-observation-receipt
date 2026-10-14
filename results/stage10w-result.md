# Stage 10W — Target-Tag Selection Canary

- Verification: `PASS`
- Evidence state: `VERIFIED_NONUNIFORM_TARGET_TAG_COVERAGE`
- Tagged / blank / total source exposures: `3,413` / `4,193` / `7,606`
- Target-tag coverage: `44.872%`
- Zero / complete / partial activity values: `17` / `8` / `20`
- Activity association Cramér's V: `0.820465`
- Activity-majority lookup / global majority: `87.484%` / `55.128%`
- Pixel payload bytes opened: `0`

## Verified

Target tags are present for 3,413 of 7,606 source exposures (44.872%). Across 45 activity values, 17 have zero tag coverage, eight have complete coverage, and 20 are partial; an in-sample activity-majority lookup classifies tag presence at 87.484% versus a 55.128% global-majority baseline.

## Decision use

Treat target tags as curated navigation metadata unless a task-specific audit establishes a label population. Before supervised target modeling, measure and control label presence itself; do not convert blank tags into negative labels or interpret the Stage 10U association as acquisition-only.

## Activity examples

- `24_Sunset`: `1,294` / `1,294` tagged
- `12_Orientale Basin (2/2)`: `0` / `399` tagged
- `07_Whole Moon`: `3` / `456` tagged
- `h_Observation Break`: `259` / `284` tagged

## Claim ceiling

Stage 10W may establish that target tags are present for 3,413 of 7,606 source exposures in the verified complete-action cohort and that tag presence is strongly nonuniform across scheduled activities and more modestly nonuniform across cameras. It may qualify Stage 10U by showing that camera-target association in the tagged subset can reflect both acquisition and curation structure. It cannot treat blanks as negative examples, validate the nonblank tags, call missingness statistically random or formally MNAR, infer labeler intent, impute targets, call an in-sample lookup a held-out model, estimate archive-wide target prevalence, inspect pixels, or claim scientific discovery, novelty, or priority.

## Hard negatives

- `call_blank_tags_negative_examples`: REJECTED
- `call_target_tags_ground_truth`: REJECTED
- `call_missingness_random`: REJECTED
- `infer_labeler_intent`: REJECTED
- `impute_targets_from_activity`: REJECTED
- `call_activity_lookup_held_out_model`: REJECTED
- `attribute_stage10u_association_only_to_acquisition`: REJECTED
- `generalize_tagged_class_prevalence_to_archive`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_tag_selection_canary`: REJECTED
