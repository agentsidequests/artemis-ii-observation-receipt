# Stage 10S — Plan-Bounded Sunset Window

- Verification: `PASS`
- Evidence state: `VERIFIED_PLAN_BOUNDED_SUNSET_CONCENTRATION`
- Planned block: `2026-04-07T00:36:00Z` to `2026-04-07T00:44:00Z` (`8` minutes)
- Products / exposures / actions: `2,535` / `845` / `169`
- Retrieval footprint: `200.901668231 GB`
- Source / raw / processed: `17.257373901` / `46.133066720` / `137.511227610 GB`
- Retrieval footprint / source-byte ratio: `11.641497x`
- Cohort product / action / byte share: `11.110%` / `7.802%` / `12.361%`
- Plan-window rank (products / actions / bytes): `1` / `1` / `1` of `36`
- Scheduled Sunset entries in plan: `1`
- Pixel payload bytes opened: `0`

## Verified

The independently scheduled eight-minute Sunset block contains 2,535 current Atlas products representing 845 exposures and 169 complete five-exposure actions across two cameras, two activity facets, and 24 conditional temporal clusters. Its 200.901668231-GB retrieval footprint decomposes into 17.257373901 GB of source NEFs, 46.133066720 GB of raw TIFFs, and 137.511227610 GB of processed TIFFs: an 11.641497-fold retrieval-footprint-to-source-byte ratio. It ranks first by products, actions, and bytes among all 36 plan windows containing admitted actions; every admitted row in the fixed block carries the Sunset target label.

## Decision use

For a model meant to generalize to a new Sunset event, treat the effective event-level sample count here as one, not 2,535 products, 845 exposures, or 169 actions. An episode-safe Artemis-II-only split cannot put different Sunset events in train and test because the plan contains only one Sunset entry. A within-event task needs a narrower, explicitly named estimand.

## Claim ceiling

Stage 10S may establish that the independently scheduled 00:36-00:44 Sunset block contains 2,535 current Atlas products representing 845 exposures and 169 complete five-exposure actions across two cameras, two activity facets, and 24 conditional five-second clusters. The products total 200.901668231 GB, decomposed into 17.257373901 GB of source NEFs, 46.133066720 GB of raw TIFFs, and 137.511227610 GB of processed TIFFs: an 11.641497-fold retrieval-footprint-to-source-byte ratio, with processed TIFFs contributing 68.447% of the footprint. This is 11.110% of products and exposures, 7.802% of actions, and 12.361% of bytes in the verified complete-action cohort. Sunset ranks first by products, actions, and bytes among all 36 plan windows containing admitted actions; every admitted row in the fixed block carries the Sunset target label, while the user guide warns that target labels were not thoroughly verified. The plan contains one scheduled Sunset entry, so this mission cannot supply separate Sunset events to both sides of an event-level evaluation. It cannot establish image similarity, semantic-scene identity, target-label correctness, independent plan-window samples, actual leakage, model performance, a named serial-to-operator mapping, archive-wide prevalence, cross-mission generalization, scientific discovery, novelty, or priority.

## Hard negatives

- `call_archive_footprint_source_volume`: REJECTED
- `call_plan_windows_disjoint_samples`: REJECTED
- `call_target_label_pixel_truth`: REJECTED
- `call_products_independent_samples`: REJECTED
- `attribute_serial_to_named_operator`: REJECTED
- `call_hypothetical_crossing_observed_leakage`: REJECTED
- `infer_model_performance_effect`: REJECTED
- `claim_cross_event_generalization_estimated`: REJECTED
- `generalize_sunset_concentration_to_archive`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_plan_window_canary`: REJECTED
