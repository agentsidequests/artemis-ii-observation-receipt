# Stage 10D — Archive Unit Normalization

- Verification: `PASS`
- Evidence state: `VERIFIED_MULTI_UNIT_ARCHIVE_WITH_HEADLINE_CONSISTENT_SUBTOTAL`
- Atlas mission data products: `32,133`
- Atlas mission product footprint: `2.526790 TB`
- Footprint excluding processed crew-camera products: `833.887936 GB`
- Forward Look activity products / internal IDs: `6` / `2`
- Two complete Forward Look actions products / internal IDs: `30` / `10`
- Pixel payload bytes opened: `0`

## Verified

The Atlas snapshot contains three equally sized crew-camera product collections and 2.526790075510 TB of data products. Excluding the processed crew-camera collection leaves 833.887936412 GB. In the bounded Forward Look case, two activity-tagged exposure IDs become six products across source, raw, and processed representations, and the ten exposures in their two complete actions become thirty products.

## Bounded inference

The 833.9 GB subtotal is arithmetically consistent with NASA's 'more than 800 gigabytes' statement, suggesting—but not proving—that the headline excludes the processed crew-camera representation. The official source does not document that accounting formula.

## Decision use

Normalize archive searches by NASA internal ID and reconstruct camera actions before counting evidence; retain collection identity when estimating download or processing burden.

## Claim ceiling

Stage 10D may establish the exact Atlas product counts and archive.size sums in the preserved snapshot, official product-type semantics, and the bounded Forward Look representation multiplication. It may say the 833.9 GB subtotal is consistent with NASA's 'more than 800 gigabytes' statement. It cannot call NASA's statement false, claim NASA documented or intentionally used that subtotal, treat every representation as an independent observation, prove perfect representation parity for every crew exposure, generalize a live Atlas snapshot indefinitely, or infer scientific content.

## Hard negatives

- `call_nasa_800gb_statement_false`: REJECTED
- `claim_nasa_documented_the_accounting_formula`: REJECTED
- `count_each_representation_as_an_independent_observation`: REJECTED
- `collapse_three_products_into_one_downloadable_file`: REJECTED
- `claim_processed_products_were_intentionally_omitted`: REJECTED
- `generalize_two_action_identity_to_every_product`: REJECTED
- `claim_atlas_snapshot_is_permanent`: REJECTED
- `open_pixels_to_reconcile_archive_units`: REJECTED
