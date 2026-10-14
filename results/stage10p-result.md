# Stage 10P — Five-Second Capture-Run Concentration

- Verification: `PASS`
- Evidence state: `VERIFIED_FIVE_SECOND_CAPTURE_RUN_CONCENTRATION`
- Products / captures / actions: `1,230` / `410` / `82`
- Time span: `143.61 seconds`
- Archive footprint: `75.056509295 GB`
- Cohort product / byte share: `5.390%` / `4.618%`
- Hypothetical independent 80/20 action-split crossing probability: `99.999998869%`
- Pixel payload bytes opened: `0`

## Verified

The largest conditional five-second same-camera cluster contains 1,230 downloadable products representing 410 exposures and 82 complete five-exposure actions over 143.61 seconds. Its products total 75.056509295 GB. Every admitted row carries camera serial 3500015, activity 24_Sunset, and target Sunset.

## Decision use

Use this as the concrete microcase for why a flat file split can divide one structured capture run across evaluation partitions. The metadata establishes concentration and label concordance, not semantic scene identity or actual leakage.

## Claim ceiling

Stage 10P may establish the exact concentration of the largest conditional five-second same-camera cluster in the verified cohort and its expected crossing under hypothetical independent action assignment. It cannot call that cluster a semantic scene or independent sample, validate activity or target correctness, claim observed leakage or a performance effect, generalize the largest cluster to the archive, infer image content or similarity, or claim global novelty or priority.

## Hard negatives

- `call_cluster_a_semantic_scene`: REJECTED
- `call_activity_or_target_labels_correct`: REJECTED
- `call_cluster_an_independent_sample`: REJECTED
- `call_expected_crossing_observed_leakage`: REJECTED
- `generalize_largest_cluster_to_archive`: REJECTED
- `infer_model_performance_effect`: REJECTED
- `claim_global_priority`: REJECTED
- `open_pixels_for_concentration_canary`: REJECTED
