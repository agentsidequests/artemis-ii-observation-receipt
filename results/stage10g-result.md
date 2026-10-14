# Stage 10G — Retrieval Distortion Amplification

- Verification: `PASS`
- Evidence state: `VERIFIED_RETRIEVAL_DISTORTION_AMPLIFICATION`
- Fractured actions / exposure IDs / products: `21` / `69` / `207`
- Total footprint of those products: `15.833953 GB`
- Activity/target partition coupled actions: `20` / `21`
- Pixel payload bytes opened: `0`

## Verified

The 21 fractured camera actions contain 69 exposure identities but 207 downloadable data products and 15.833953276 GB across three representations. Activity and target partitions are exactly coupled in 20 of the 21 actions.

## Discussion #4 stress case

Inside the fourteen Discussion #4 / Crew Choice fractures, the Discussion facet contributes 84 products representing 28 exposures, yet reconstructs zero complete actions. Fourteen companion exposures—42 more products—are required.

## Decision use

Use three explicit keys: collection identity for bytes and processing, NASA internal ID for exposure identity, and camera-native grouping for physical action. Activity and target remain useful annotations, never the join key or independent-evidence count.

## Claim ceiling

Stage 10G may quantify representation multiplication and action under-recovery for the 21 verified fractured raw crew-camera brackets. It cannot count products as independent observations, call useful representations waste, infer correct activities or targets, estimate anomaly rates for non-bracket products, or claim the three-unit normalization exhausts every archive product class.

## Hard negatives

- `count_207_products_as_independent_observations`: REJECTED
- `claim_three_representations_triple_scientific_evidence`: REJECTED
- `claim_69_exposures_are_all_archive_anomalies`: REJECTED
- `infer_target_correctness_from_partition_coupling`: REJECTED
- `declare_discussion_facet_action_complete`: REJECTED
- `call_representations_wasteful_duplicates`: REJECTED
- `generalize_bracket_result_to_every_product_class`: REJECTED
- `open_pixels_to_normalize_archive_units`: REJECTED
