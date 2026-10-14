# Stage 11J — Product-Rank Reversal Attribution

- Verification: `PASS`
- Evidence state: `VERIFIED_PROTOCOL_ATTRIBUTION_OF_PRODUCT_RANK_REVERSALS`
- Active windows / strictly comparable pairs: `36` / `621`
- Equal-rate comparable pairs / reversals: `222` / `0`
- Unequal-rate comparable pairs / reversals: `399` / `38`
- Constant representations per capture: `3`
- Pixel payload bytes opened: `0`

## Verified

All 38 action-to-product plan-window rank reversals occur across unequal products-per-action rates, and in every case the window with more actions has the lower rate. With exactly three representations per capture throughout the admitted cohort, exposure-protocol composition is the varying multiplicity behind these product-rank reversals.

## Decision use

The acquisition protocol becomes an implicit observation-weighting policy only when the hierarchy is flattened to products. This is an arithmetic property of the admitted archive structure, not evidence that an actual model used that sampler or suffered bias.

## Claim ceiling

Stage 11J may establish that all 38 action-to-product ordering reversals among the 621 strictly comparable active-window pairs occur across unequal products-per-action rates, that the higher-action window has the lower rate in every reversal, and that each window's product rate is exactly three times its exposure rate under the verified constant representation layer. It may therefore attribute these in-cohort product-rank reversals arithmetically to exposure-protocol composition rather than representation-count variation. It cannot interpret the rankings as scientific importance, assert an actual sampler or observed model bias, infer a causal outcome effect or formal informative cluster size, nominate a universal correction, recommend deleting intentional products, extend beyond the admitted active windows, or make a novelty, priority, or physical-science claim.

## Hard negatives

- `claim_scientific_importance_ranking`: REJECTED
- `claim_actual_sampler_is_uniform_products`: REJECTED
- `claim_observed_model_bias`: REJECTED
- `claim_causal_performance_effect`: REJECTED
- `call_formal_informative_cluster_size`: REJECTED
- `claim_one_universal_correct_weighting`: REJECTED
- `recommend_discarding_representations_or_brackets`: REJECTED
- `generalize_to_unadmitted_archive_records`: REJECTED
- `claim_novelty_or_priority`: REJECTED
- `open_pixels_during_attribution`: REJECTED
