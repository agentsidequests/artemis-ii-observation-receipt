# Stage 11B — Paired-Window Task Admission

- Verification: `PASS`
- Evidence state: `VERIFIED_PAIRED_WINDOW_TASK_CANDIDATE`
- Targets / windows / actions / exposures: `3` / `6` / `262` / `786`
- Products / footprint: `2,358` / `145.162317082 GB`
- Exact same-name tag coverage: `18` / `786` (`2.290%`)
- Pixel payload bytes opened: `0`

## Verified

Three geolocated lunar targets have two disjoint active plan windows on the same camera serial. Glushko is the strongest positive task candidate because the plan explicitly defines first and second photometric observations intended to inform how changing viewing conditions affect perceived brightness, color, and texture.

## Decision use

Admit a pixel-blind registration and protocol gate for Glushko, not a model run. Plan membership and same camera make the comparison plausible; sparse exact tags and absent pixel registration prevent an image-content or evaluation claim.

## Pair details

- `Glushko Crater`: orders `3` / `11`, gap `107.0` min, actions `8` / `34`, intent `explicit_photometric_viewing_condition_repeat`
- `Ohm Crater`: orders `4` / `16`, gap `169.0` min, actions `16` / `8`, intent `same_name_revisit_no_explicit_photometric_repeat`
- `Orientale Basin`: orders `8` / `12`, gap `47.0` min, actions `62` / `134`, intent `same_name_two_part_plan`

## Claim ceiling

Stage 11B may establish that Glushko Crater, Ohm Crater, and Orientale Basin each have two disjoint active, same-camera plan windows containing a combined 262 complete actions, 786 exposures, 2,358 products, and 145.162317082 GB. It may select Glushko for a pixel-blind registration and protocol gate because the plan explicitly designed its two windows as photometric repeat observations under changing viewing conditions. It cannot establish that every image contains the named target, that paired windows show equivalent scenes, that the camera is calibrated, that windows are independent events, that sparse or blank tags are negative evidence, that any split is valid before registration, or any model-performance, scientific-discovery, novelty, or priority claim.

## Hard negatives

- `call_plan_membership_image_content`: REJECTED
- `call_same_name_scene_equivalence`: REJECTED
- `call_same_camera_calibrated_photometry`: REJECTED
- `call_windows_independent_events`: REJECTED
- `call_sparse_tags_negative_evidence`: REJECTED
- `assign_model_partition_before_registration`: REJECTED
- `claim_model_performance_effect`: REJECTED
- `call_candidate_scientific_result`: REJECTED
- `claim_novelty_or_priority`: REJECTED
- `open_pixels_during_admission`: REJECTED
