# Stage 10A — Exposure-Bracket Metadata Integrity

- Verification: `PASS`
- Evidence state: `VERIFIED_ACTIVITY_FACET_FRAGMENTATION`
- Complete Flight Day 6 raw crew-camera records: `8423`
- Qualifying complete five-frame brackets: `221`
- Activity-fractured brackets: `2` (`0.9050%`)
- Target-presence-fractured brackets: `10`
- Target-value-fractured brackets: `0`
- Pixel payload bytes opened: `0`

## Result

At least one camera-native five-exposure bracket is divided across multiple `activity_id` values. The archive therefore preserves the files while fragmenting one physical camera action across search facets in this qualified cohort.

## Activity-fractured brackets

- `2026-04-07T00:50:46.820Z` — `3920019`
  - Files: `art002e015902_nkz9019_raw_v01.tif, art002e015903_nkz9019_raw_v01.tif, art002e015904_nkz9019_raw_v01.tif, art002e015905_nkz9019_raw_v01.tif, art002e015906_nkz9019_raw_v01.tif`
  - Activity IDs: `['25_Discussion #6: Forward Look', '24_Sunset', '24_Sunset', '24_Sunset', '24_Sunset']`
  - Target IDs: `[None, 'Sunset', 'Sunset', 'Sunset', 'Sunset']`
- `2026-04-07T00:51:51.830Z` — `3920019`
  - Files: `art002e015907_nkz9019_raw_v01.tif, art002e015908_nkz9019_raw_v01.tif, art002e015909_nkz9019_raw_v01.tif, art002e015910_nkz9019_raw_v01.tif, art002e015911_nkz9019_raw_v01.tif`
  - Activity IDs: `['24_Sunset', '25_Discussion #6: Forward Look', '24_Sunset', '24_Sunset', '24_Sunset']`
  - Target IDs: `['Sunset', None, 'Sunset', 'Sunset', 'Sunset']`

## Claim ceiling

Stage 10A may establish the complete Flight Day 6 five-exposure-bracket denominator and whether any one camera action is fragmented across activity_id facets. It cannot identify the correct tag, infer image content, estimate error across non-bracket products or other flight days, invalidate the pixel archive, or establish scientific findings.

## Hard negatives

- `infer_correct_activity_from_bracket_majority`: REJECTED
- `treat_target_id_absence_as_wrong_image_content`: REJECTED
- `use_otr_windows_as_execution_truth`: REJECTED
- `count_incomplete_or_nonconsecutive_brackets`: REJECTED
- `generalize_fd6_bracket_rate_to_all_archive_products`: REJECTED
- `claim_metadata_fragmentation_invalidates_pixel_data`: REJECTED
- `claim_pds_validation_guarantees_semantic_label_correctness`: REJECTED
- `open_pixels_to_resolve_activity_identity`: REJECTED
