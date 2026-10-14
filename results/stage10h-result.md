# Stage 10H — Source Volume / Archive Footprint Reconciliation

- Verification: `PASS`
- Evidence state: `VERIFIED_SOURCE_VOLUME_VS_ARCHIVE_PRODUCT_FOOTPRINT`
- Official source ledger: `11,591` files / `814.51 GB`
- Preserved Atlas ledger: `32,133` products / `2.526790075510 TB`
- Source video / Atlas video: `598.20 GB` MXF / `26.268401779 GB` MP4
- Prior 833.9-GB hypothesis superseded: `True`
- Pixel payload bytes opened: `0`

## Verified

NASA's 814.51 GB is an explicit source-data volume for 11,591 files received and archived by the Lunar Science Team. The current Atlas snapshot instead sums 32,133 archive products across source and additional representations to 2.526790075510 TB. These are different ledgers, not competing measurements of one fixed payload.

## Successful falsification

The prior 833.887936412 GB subtotal happens to fit the release's rounded wording, but Table 4.1 supplies the documented basis: 814.51 GB of source files. The earlier processed-crew-omission explanation is superseded.

## Video bridge

Table 4.1 reports 598.20 GB of source MXF video, while Atlas exposes 22 MP4 video products totaling 26.268401779 GB. The User Guide documents a frame-rate-aware H.264 conversion with substantial file-size reduction, so the two figures must not be treated as missing bytes or equivalent-format totals.

## Decision use

Use 814.51 GB and 11,591 files for received source-data scale; use Atlas product counts and archive.size for current retrieval and compute burden; use stable exposure identities and reconstructed camera actions for evidentiary sampling. Never substitute one ledger for another.

## Claim ceiling

Stage 10H may establish NASA's documented 11,591-file, 814.51-GB source-data ledger; the preserved Atlas snapshot's 32,133-product, 2.526790075510-TB archive footprint; and the official MXF-to-MP4 conversion explanation. It may supersede the Stage 10D headline-accounting hypothesis. It cannot call 2.527 TB source data, call 814.51 GB the current all-product download burden, treat representations as independent observations or waste, infer loss of scientific content from byte reduction, or infer release completeness from source-versus-Atlas count differences.

## Hard negatives

- `claim_833gb_is_documented_headline_basis`: REJECTED
- `claim_2527tb_is_source_data_volume`: REJECTED
- `claim_815gb_is_current_download_footprint`: REJECTED
- `treat_archive_products_as_independent_observations`: REJECTED
- `call_video_size_difference_missing_data`: REJECTED
- `call_format_conversions_wasteful_duplicates`: REJECTED
- `infer_current_release_completeness_from_count_difference`: REJECTED
- `open_pixels_to_reconcile_ledger_units`: REJECTED
