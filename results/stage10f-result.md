# Stage 10F — Plan / Execution / Curation Triangulation

- Verification: `PASS`
- Evidence state: `SUPPORTED_PARTIAL_PER_FRAME_CURATION_SIGNATURE`
- Repeated actions / frames: `13` / `39`
- Discussion + Terminator frames: `26`
- Crew Choice + missing-target frames: `13`
- Signature lies inside archived Crew Choice request window: `True`
- Pixel payload bytes opened: `0`

## Verified

A timestamp-to-plan pathway and a human-override pathway are both officially documented; target tags are manual and subset-only. The repeated metadata signature and contemporaneous context reproduce exactly.

## Strongest supported explanation

A partial per-frame curation pass is the strongest current explanation: selected 0 and +2 exposures jointly received Discussion #4 plus Terminator, while every intervening -2 exposure retained Crew Choice and no target. This is an inference from alignment, not a recovered edit log.

## Live alternatives

- An undocumented automated rule produced the same exposure-position pattern.
- The final LTP timing differed materially from the archived request timing.
- One or more source-label defects coincidentally mimic a partial override pass.

## Decision use

Treat activity_id as a mixed provenance field—planned-by-time unless selectively reinterpreted—not as a uniform ground-truth class. Reconstruct actions and preserve target-presence state at plan/execution transitions.

## Claim ceiling

Stage 10F may establish the official two-path activity-label procedure, the exact repeated activity/target/exposure-position association, and contemporaneous plan/execution context. It may rank partial per-frame curation as the strongest supported explanation. It cannot prove which records were human-overridden, identify correct labels, infer image content, assert that missing target always means default labeling, assign causality to scalar schema, or generalize one mechanism to every fracture without edit logs.

## Hard negatives

- `declare_human_override_proven`: REJECTED
- `declare_crew_choice_labels_wrong`: REJECTED
- `declare_discussion_labels_correct`: REJECTED
- `treat_every_missing_target_as_an_unoverridden_default`: REJECTED
- `infer_image_content_from_transcript`: REJECTED
- `claim_scalar_schema_caused_partial_curation`: REJECTED
- `generalize_mechanism_to_every_archive_fracture`: REJECTED
- `open_pixels_to_reconstruct_edit_history`: REJECTED
