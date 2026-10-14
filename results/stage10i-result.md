# Stage 10I — Source-to-Archive Provenance Crosswalk

- Verification: `PASS`
- Evidence state: `VERIFIED_NON_BIJECTIVE_PROVENANCE_CROSSWALK_WITH_RESIDUALS`
- Crew source files / current Nikon identities: `10,407` / `10,329`
- Documented pending iPhone / unexplained Nikon residual: `68` / `10`
- Orion source stills / current Orion still products: `1,040` / `1,012`
- Pixel payload bytes opened: `0`

## Verified

The source-to-current-archive mapping is non-bijective. The official crew source ledger has 10,407 files, while current Atlas has 10,329 Nikon identities represented three ways. Sixty-eight iPhone files are explicitly pending; ten Nikon-count differences remain unexplained. Orion's 28-still-image difference is entirely Cab Cam 2 in the current inventory. Audio source files are split, regrouped, transcribed, or embedded into image metadata rather than preserved as a one-product-per-source count.

## Bounded inference

The public release is a dated provenance graph with type-specific transformations and release coverage, not a single denominator. The remaining ten Nikon and twenty-eight Cab Cam 2 differences are inventory residuals, not evidence of lost or defective data.

## Decision use

Any archive coverage fraction must name its ledger and snapshot date. Use source files for acquisition scale, downloadable products and bytes for retrieval burden, stable capture identities for exposures, and reconstructed multi-frame actions for observation evidence.

## Claim ceiling

Stage 10I may establish exact crosswalk counts in the preserved source table and current Atlas snapshot, the documented pending iPhone release, and documented audio/product transformations. It may establish that the mapping is non-bijective. It cannot call any residual lost, defective, withheld, or erroneous; prove current release completeness; assume every source file yields three products; treat transcripts as independent source observations; or generalize the snapshot indefinitely.

## Hard negatives

- `equate_source_files_with_current_products`: REJECTED
- `declare_pending_iphone_files_lost`: REJECTED
- `declare_nikon_residuals_lost`: REJECTED
- `declare_cab2_residuals_lost`: REJECTED
- `equate_112_audio_products_with_115_source_files`: REJECTED
- `triple_every_mission_source_file`: REJECTED
- `declare_current_atlas_snapshot_complete`: REJECTED
- `open_pixels_to_explain_inventory_residuals`: REJECTED
