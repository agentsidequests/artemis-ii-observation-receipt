# Stage 11F — Plan-Window Protocol Weighting

- Verification: `PASS`
- Evidence state: `VERIFIED_PLAN_WINDOW_PROTOCOL_WEIGHTING`
- Active windows: `36`
- Pure 3-exposure / pure 5-exposure / mixed: `19` / `11` / `6`
- Product range per action: `9` to `15`
- Pure-5 / pure-3 product weight: `1.666667×`
- Byte/action range: `546.814 MB` to `1.970 GB`
- Sunset: `15` products/action; byte-weight rank `4` of `36`
- Pixel payload bytes opened: `0`

## Verified

Acquisition-protocol weighting recurs across active plan windows: 19 contain only three-exposure actions, 11 contain only five-exposure actions, and six are mixed. With three archive representations per exposure, pure-five windows carry 15 products per action versus nine for pure-three windows.

## Decision use

A flat product table embeds protocol weights across the mission, not only in Sunset. Sampling and evaluation should declare whether actions, events, or products receive equal weight.

## Claim ceiling

Stage 11F may establish that 19 of 36 active plan windows contain only admitted three-exposure actions, 11 contain only admitted five-exposure actions, and six are mixed. Because each exposure has three representations in the verified cohort, the pure-five windows carry 15 products per action versus nine for pure-three windows, a 1.666667-fold product weight at equal action count. Per-window byte/action values span 546.814 MB to 1.970 GB, and Sunset is in the 15-product/action class. It cannot treat overlapping plan windows as a partition, turn product weight into image-content or scientific-value weight, assert an actual sampler or observed model bias, infer a causal performance effect, extend to unadmitted archive records, or make a physical-science, novelty, or priority claim.

## Hard negatives

- `call_plan_windows_a_partition`: REJECTED
- `call_product_weight_image_content_weight`: REJECTED
- `call_five_exposure_windows_more_valuable`: REJECTED
- `claim_actual_sampler_is_uniform_products`: REJECTED
- `claim_observed_model_bias`: REJECTED
- `claim_protocol_weighting_causal_performance_effect`: REJECTED
- `generalize_to_unadmitted_archive_records`: REJECTED
- `call_boundary_result_scientific_discovery`: REJECTED
- `claim_novelty_or_priority`: REJECTED
- `open_pixels_during_protocol_test`: REJECTED
