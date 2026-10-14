# Stage 11E — Unit-Choice Reweighting Canary

- Verification: `PASS`
- Evidence state: `VERIFIED_UNIT_CHOICE_REWEIGHTING_CANARY`
- Disposition: `ADMIT_UNIT_CHOICE_REWEIGHTING_CANARY`
- Context share by actions: `13.204%`
- Context share by products: `18.801%`
- Context share by total bytes: `22.785%`
- Product weight / action weight: `1.423876×`
- Byte weight / action weight: `1.725630×`
- Pixel payload bytes opened: `0`

## Verified

The conservative Sunset context is 13.204% of verified complete camera actions but 18.801% of products and 22.785% of bytes. Product and byte denominators therefore assign it more weight than an action denominator even before any pixel analysis.

## Decision use

Treat sampling unit as an explicit model-design choice. A flat product table changes event weight as well as dependency structure; action or event balancing answers a different question.

## Claim ceiling

Stage 11E may establish that the conservative 758.576-second Sunset context accounts for 13.204% of actions, 18.801% of products, and 22.785% of bytes in the verified complete-action cohort. Under explicitly hypothetical uniform weighting, product units weight that context 1.423876 times and total bytes 1.725630 times its action-unit share. It cannot call the context a complete event, extend the shares to the whole archive, assert that an actual pipeline samples products or bytes this way, establish observed model bias or a performance effect, judge representation value, or make a physical-science, novelty, or priority claim.

## Hard negatives

- `call_context_complete_event`: REJECTED
- `generalize_to_entire_archive`: REJECTED
- `claim_actual_pipeline_samples_products_uniformly`: REJECTED
- `claim_actual_pipeline_samples_bytes_proportionally`: REJECTED
- `claim_observed_model_bias`: REJECTED
- `claim_reweighting_causal_performance_effect`: REJECTED
- `call_products_wasteful_duplicates`: REJECTED
- `call_boundary_result_scientific_discovery`: REJECTED
- `claim_novelty_or_priority`: REJECTED
- `open_pixels_during_reweighting_test`: REJECTED
