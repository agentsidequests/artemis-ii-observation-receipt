# Stage 10C — Generalized Camera-Action Facet Integrity

- Verification: `PASS`
- Evidence state: `VERIFIED_RECURRENT_POSITION_STRUCTURED_FRAGMENTATION`
- Complete Flight Day 6 raw records: `8423`
- Complete three- or five-frame bracket actions: `1721`
- Activity-fractured actions: `21` (`1.2202%`)
- Longest repeated position-specific fracture run: `13` actions
- Pixel payload bytes opened: `0`

## Result

Activity-facet fragmentation recurs across 21 of 1,721 complete camera actions. Thirteen consecutive three-frame actions repeat the same split by exposure position: the middle exposure is tagged `14_Crew Choice #2` with no target, while the paired exposures are tagged `15_Discussion #4: Terminator` with target `Terminator`. This repeated within-action structure is not well explained as a single temporal activity boundary.

The result establishes a retrieval-unit mismatch, not wrong labels. Activity facets retain coarse value, and the evidence does not identify the correct activity, image content, or authoring cause.

## Pattern census

- `0,-1,+1`: `57` complete actions
- `0,-2,+2`: `1117` complete actions
- `0,-2,-1,+1,+2`: `221` complete actions
- `0,-6,-3,+3,+6`: `326` complete actions

## Claim ceiling

Stage 10C may establish recurrence and repeated within-action structure for complete Flight Day 6 raw crew-camera exposure brackets. It cannot identify which label is correct, call every fracture an error, infer image content or scientific meaning, assign one authoring cause, estimate rates for non-bracket products or other flight days, or conclude that activity facets lack coarse retrieval value.

## Hard negatives

- `count_partial_brackets`: REJECTED
- `infer_correct_activity_from_majority`: REJECTED
- `call_every_fracture_a_metadata_error`: REJECTED
- `treat_target_absence_as_image_content`: REJECTED
- `claim_one_cause_for_all_fractures`: REJECTED
- `generalize_fd6_rate_to_other_days`: REJECTED
- `claim_activity_facets_are_useless`: REJECTED
- `open_pixels_to_resolve_labels`: REJECTED
