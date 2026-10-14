# Artemis II Observation-Execution Testbed — Stage 2A Earthrise Result

- Verification: **PASS**
- Evidence state: `VERIFIED_NO_OVERLAP`
- Coverage relation: `AFTER_EVENT_NO_OVERLAP`
- Minimum separation: **136 seconds**
- Disposition: `CONTINUE_BOUNDED_PATTERN_CHECK`

The fixed SAW Cam 3 sequence places Earthrise completely before the official observation availability window. The result is interval-censored at 30 seconds; it is not an exact contact-time claim.

## Independent image oracle

| PDS timestamp | Frozen state | Bright-component corroboration |
| --- | --- | ---: |
| 2026-04-06T23:21:14Z | NOT_VISIBLE | 0 pixels |
| 2026-04-06T23:21:44Z | PARTIAL | 98 pixels |
| 2026-04-06T23:22:14Z | PARTIAL | 477 pixels |
| 2026-04-06T23:22:44Z | PARTIAL | 2130 pixels |
| 2026-04-06T23:23:14Z | FULL_CLEAR | 4050 pixels |
| 2026-04-06T23:23:44Z | FULL_CLEAR | 4187 pixels |

## Derived brackets

- First visible contact: `(2026-04-06T23:21:14Z, 2026-04-06T23:21:44Z]`
- Full clearance: `(2026-04-06T23:22:44Z, 2026-04-06T23:23:14Z]`
- Stable full-clear check: `2026-04-06T23:23:44Z`

## Coverage test

The OTR availability window is `2026-04-06T23:25:30Z` to `2026-04-06T23:25:34.147844Z` (4.147844 seconds). Its start is 136 seconds after the latest possible full-clearance time, so overlap is impossible within the frozen image brackets.

This does **not** mean the OTR endpoints were intended as contact times, and it does not establish why the window was placed later.

## Independence and limits

The oracle is partially independent: transcript review nominated the small time neighborhood, but the scored states and timestamps come only from a fixed Orion camera and PDS4 labels. The human visual classification is hash-pinned and corroborated by a stable image footprint; the 30-second sampling prevents exact contact times.

SPICE status: `NOT_ADMISSIBLE_AT_RUN_TIME` — NASA PDS lists the Artemis II SPICE actual release as TBD; no archive bundle was available to pin.

## Next-step logic

**Recommended:** Run the same small, fixed-camera image-state coverage test for Earthset, Sunset, and Sunrise before any broad archive analysis.

Why: Earthrise now establishes a real non-overlap, but one event cannot distinguish an isolated planning choice from a repeated window-placement pattern.

Alternative: Re-attest Earthrise with the Artemis II SPICE bundle after NASA publishes an actual release.

Fallback: If the other event families do not reproduce the relation, pivot to Stage 3 target execution and attention allocation rather than widening the timing claim.

## Hard negatives

- `shift_image_timestamps_plus_300_seconds`: REJECTED
- `label_pre_event_frame_partial`: REJECTED
- `present_transcript_as_image_oracle`: REJECTED
- `widen_availability_window_to_event`: REJECTED
