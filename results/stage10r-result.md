# Stage 10R — Cross-Camera Sunset Observation Episode

- Verification: `PASS`
- Evidence state: `VERIFIED_CROSS_CAMERA_CROSS_FACET_OBSERVATION_EPISODE`
- Combined products / captures / actions: `2,010` / `670` / `134`
- Combined archive footprint: `177.543697399 GB`
- Cohort product / action / byte share: `8.809%` / `6.187%` / `10.924%`
- Cameras / activity facets: `2` / `2`
- Transcript utterances inside second-camera interval: `24`
- Pixel payload bytes opened: `0`

## Verified

The transcript-aligned Sunset episode contains four overlapping same-camera capture runs from two cameras and two activity facets. Together they produce 2,010 products representing 670 exposures and 134 actions, totaling 177.543697399 GB—8.809% of products and exposures, 6.187% of actions, and 10.924% of bytes in the verified complete-action cohort; 24 transcript utterances fall inside the three nested second-camera runs.

## Decision use

Use this as the concrete reason that file, exposure, action, camera, activity facet, and observation episode are different possible evaluation units. The task's dependence oracle must choose among them.

## Claim ceiling

Stage 10R may establish that one independently transcript-aligned Sunset observation episode contains four overlapping capture runs from two cameras and two different activity facets: 2,010 products representing 670 exposures and 134 reconstructed actions, totaling 177.543697399 GB—8.809% of products and exposures, 6.187% of actions, and 10.924% of bytes in the verified complete-action cohort. It may show that action IDs, one camera's temporal clusters, or one activity facet are not sufficient universal episode keys. It cannot establish one semantic scene, image duplication or visual redundancy, activity-label error, camera-operator identity, observed leakage, a model-performance effect, archive-wide representativeness, scientific discovery, novelty, or priority.

## Hard negatives

- `call_episode_a_semantic_scene`: REJECTED
- `call_images_duplicates_or_visually_redundant`: REJECTED
- `call_activity_labels_incorrect`: REJECTED
- `attribute_cameras_to_named_speakers`: REJECTED
- `call_cross_camera_relation_observed_leakage`: REJECTED
- `generalize_episode_to_archive`: REJECTED
- `infer_model_performance_effect`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_cross_camera_canary`: REJECTED
