# Stage 10Y — Schedule/Tag Non-Equivalence Canary

- Verification: `PASS`
- Evidence state: `VERIFIED_SCHEDULE_TAG_NON_EQUIVALENCE`
- Plan target names / tag values / exact-name overlap: `19` / `23` / `14`
- Tagged exposures inside / outside exact-same-name plan windows: `1,313` / `2,100`
- Exact-same-name membership share: `38.471%`
- Sunset tagged inside / outside scheduled Sunset window: `845` / `708`
- Pixel payload bytes opened: `0`

## Verified

The mission plan and target-tag layer are not interchangeable ontologies or grouping systems. They share 14 exact names, while nine tag values are absent from the plan vocabulary and five plan names are absent from the tag vocabulary. Only 1,313 of 3,413 tagged source exposures have complete actions inside an exact-same-name scheduled window.

## Decision use

Use an independent schedule or task-native episode oracle for event grouping, and treat target tags as curated navigation metadata unless their population is separately audited. The fixed Sunset plan window remains primary; its tag concordance is corroborative.

## Claim ceiling

Stage 10Y may establish that the plan target-name vocabulary and target-tag vocabulary are non-equivalent and that exact-name temporal correspondence is incomplete: 14 names overlap, nine appear only as tags, five appear only in the plan, and 1,313 of 3,413 tagged source exposures have complete actions inside an exact-same-name scheduled window. It may establish that target tags cannot be silently substituted for scheduled event identifiers or grouping keys. It cannot determine whether either vocabulary is more correct, call an outside-window tag erroneous, infer a missed planned observation, treat an exact match as an independent event, merge ontologies, infer new Sunset events from the 708 outside-window rows, inspect pixels, or claim scientific discovery, novelty, or priority.

## Hard negatives

- `call_target_tags_event_ids`: REJECTED
- `call_plan_names_exhaustive_labels`: REJECTED
- `call_outside_window_tags_wrong`: REJECTED
- `call_zero_match_planned_observation_missed`: REJECTED
- `call_exact_name_match_independent_event`: REJECTED
- `merge_plan_and_tag_ontologies`: REJECTED
- `group_model_by_target_tag_as_event`: REJECTED
- `call_sunset_outside_rows_new_events`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_schedule_tag_canary`: REJECTED
