# Artemis II Observation-Execution Testbed — Stage 2B Result

- Verification: **PASS**
- Evidence state: `VERIFIED_SINGLE_ADMISSIBLE_REPLICATION`
- Pattern classification: `SINGLE_ADMISSIBLE_REPLICATION`
- Admissible replications: **1 of 3**
- Disposition: `RETAIN_EARTHSET_COUNTEREXAMPLE_WITHOUT_PATTERN_CLAIM`

Only Earthset reaches the frozen physical-transition oracle. Its official observation availability window begins during the independently visible occultation, so Earthset is a bounded counterexample to the Earthrise non-overlap. Sunset and Sunrise stop independently; the result supports no repeated-pattern claim.

## Earthset — verified overlap

| PDS timestamp | Frozen state |
| --- | --- |
| 2026-04-06T22:40:14Z | FULL_VISIBLE |
| 2026-04-06T22:40:44Z | FULL_VISIBLE |
| 2026-04-06T22:41:14Z | FULL_VISIBLE |
| 2026-04-06T22:41:44Z | FULL_VISIBLE |
| 2026-04-06T22:42:14Z | PARTIAL |
| 2026-04-06T22:42:44Z | PARTIAL |
| 2026-04-06T22:43:14Z | PARTIAL |
| 2026-04-06T22:43:44Z | NOT_VISIBLE |

- Occultation onset: `(2026-04-06T22:41:44Z, 2026-04-06T22:42:14Z]`
- Complete disappearance: `(2026-04-06T22:43:14Z, 2026-04-06T22:43:44Z]`
- Availability window: `[2026-04-06T22:42:19.730197Z, 2026-04-06T22:45:36.380230Z]`
- Coverage relation: `OVERLAPS_EVENT`
- Minimum guaranteed overlap: **54.269803 seconds**

The overlap is established because two observed PARTIAL frames occur after the availability window begins. The 30-second cadence still yields interval brackets rather than exact contact times.

## Independent stops

- Sunset: `NOT_ADMISSIBLE_CAMERA_VIEW`. States: `SUN_VISIBLE -> SUN_VISIBLE -> PARTIAL -> PARTIAL`. The sequence ends before a fully occulted photosphere or following stability state.
- Sunrise: `NOT_ADMISSIBLE_CAMERA_VIEW`. The complete label sequence cannot structurally supply the required post-clearance stability frame, so no pixels were acquired.

## Burden

The bounded acquisition accepted 24 files totaling 29,181,381 bytes under a 62,914,560-byte ceiling. Verification is local and uses zero network bytes.

## Claim boundary

Earthset disproves a uniform tested-event non-overlap, but one admissible replication cannot establish a recurrent placement pattern or explain why Earthrise and Earthset differ. OTR endpoints remain availability-window values, not physical contact times.

## Next-step logic

Retain Earthset as a bounded counterexample to Earthrise non-overlap, make no recurrence claim, and compare only the smallest plan metadata or current primary documentation that could explain the placement contrast before acquiring more pixels.

## Hard negatives

- `shift_image_timestamps_plus_300_seconds`: REJECTED
- `substitute_transcript_times_for_image_states`: REJECTED
- `change_camera_inside_event`: REJECTED
- `invent_state_through_saturation_or_obstruction`: REJECTED
- `extend_frozen_sequence_after_pixel_inspection`: REJECTED
- `treat_availability_endpoint_as_physical_contact`: REJECTED
