# Stage 10V — Task-Conditioned Representation Fitness

- Verification: `PASS`
- Evidence state: `VERIFIED_STORAGE_WEIGHT_NOT_CALIBRATION_LEVEL`
- Complete-action cohort processed-byte share: `67.932%`
- Fixed Sunset block processed-byte share: `68.447%`
- Calibrated product tiers: `0`
- Pixel payload bytes opened: `0`

## Verified

Processed TIFFs account for 67.932% of bytes in the verified complete-action cohort and 68.447% in the fixed Sunset block, yet the Data User Guide says no crew-camera products are calibrated and processed colors cannot be completely verified or quantified.

## Decision use

Select the image representation after naming the task. Source preserves native pixels and metadata, raw exposes the Bayer array in an open archival format, processed provides a viewable vendor interpretation, and none supplies instrument-independent physical units or quantitatively verified color on its own.

## Task gate

- `preserve_original_native_pixels_and_metadata`: `source`
- `open_standardized_bayer_array_analysis`: `raw`
- `human_viewable_vendor_interpretation`: `processed`
- `instrument_independent_physical_measurement`: `none_available`
- `quantitatively_verified_color`: `none_available`

## Claim ceiling

Stage 10V may establish that processed TIFFs occupy 67.932% of bytes in the verified complete-action cohort and 68.447% in the fixed Sunset block while the Data User Guide defines all crew-camera products as uncalibrated and warns that processed colors cannot be completely verified or quantified. It may establish a task-conditioned representation gate: source preserves native pixels and metadata, raw exposes the Bayer array in an open archival format, processed provides a viewable vendor interpretation, and none is a calibrated physical-unit or quantitatively verified-color product. It cannot rank one representation universally, call any tier defective or wasteful, infer a specific pixel artifact, measure color or photometry, infer scientific-content loss, generalize byte shares beyond the frozen cohorts, or claim scientific discovery, novelty, or priority.

## Hard negatives

- `call_processed_products_calibrated`: REJECTED
- `call_raw_products_calibrated`: REJECTED
- `rank_largest_representation_as_best`: REJECTED
- `call_processed_products_scientifically_invalid`: REJECTED
- `call_representations_wasteful_duplicates`: REJECTED
- `infer_specific_pixel_artifact`: REJECTED
- `claim_quantitative_color_available`: REJECTED
- `generalize_byte_shares_to_all_archive_products`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_representation_gate`: REJECTED
