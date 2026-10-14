# Stage 10O — Product-to-Action Relationship Manifest

- Verification: `PASS`
- Evidence state: `VERIFIED_PRODUCT_ACTION_RELATIONSHIP_MANIFEST`
- Products / captures / complete actions: `22,818` / `7,606` / `2,166`
- Manifest bytes: `10,072,026`
- Manifest SHA-256: `8edd58437cc609229edb5abb41c4e00048bb420354f1ac17a269da92c17e4729`
- Pixel payload bytes opened: `0`

## Verified

Every one of the 22,818 products in the verified cohort maps deterministically to one of 7,606 capture identities and one of 2,166 reconstructed complete actions. The manifest also carries separate private keys for each Stage 10N temporal threshold without assigning train, validation, or test membership.

## Decision use

Join a later task to this relationship layer before splitting. Keep action_id as the exact minimum group and choose a broader temporal or semantic key only after the task supplies its dependence oracle.

## Conditional temporal group counts

- `1s`: `2,051` groups
- `2s`: `1,377` groups
- `5s`: `816` groups
- `10s`: `538` groups
- `30s`: `254` groups

## Claim ceiling

Stage 10O may establish a deterministic private relationship manifest for the verified complete-action cohort and the conditional Stage 10N temporal groups. It cannot define a train/test partition before a task, treat products as independent observations, substitute activity facets for reconstructed actions, call private keys official PDS identifiers, call temporal clusters semantic scenes, include unadmitted records as complete actions, infer pixel similarity or image content, claim archive-wide exhaustiveness, observed leakage, model performance, or global novelty or priority.

## Hard negatives

- `assign_train_test_without_a_frozen_task`: REJECTED
- `use_activity_as_the_action_key`: REJECTED
- `count_products_as_independent_observations`: REJECTED
- `call_private_action_ids_official_pds_ids`: REJECTED
- `call_temporal_clusters_semantic_scenes`: REJECTED
- `include_unadmitted_records_as_complete_actions`: REJECTED
- `infer_pixel_similarity`: REJECTED
- `claim_archive_wide_exhaustiveness`: REJECTED
- `call_hypothetical_hazard_observed_leakage`: REJECTED
- `claim_global_priority`: REJECTED
- `open_pixels_for_manifest`: REJECTED
