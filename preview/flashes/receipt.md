# Observation Receipt: Artemis II lunar flash evidence

State: `VERIFIED`

Five accepted marks form a credible event ledger. The available camera records do not yet provide a calibrated measurement function, so camera nulls and flux claims stop at different evidence boundaries.

## Decision summary

- Supported: **2**
- Refuted: **1**
- Blocked: **3**
- Local artifacts verified: **3 / 3**
- Reference-only URLs, not byte verified: **2**

## Findings

| Claim | Status | Claim ceiling |
|---|---|---|
| The public annotation contains five accepted events, eight witness marks, and three observers. | `SUPPORTED` | Credible event ledger, not calibrated sensitivity or independent detections. |
| The later 30 fps window covered the annotation's 01:04 background-photo epoch. | `REFUTED_NONOVERLAP` | Metadata-time non-overlap only. The photo epoch is not ledger creation or an upper bound for all five accepted events; their event-level video coverage remains unestablished. |
| The absence of a screened pulse in the overlap clip excludes the shared crew report. | `BLOCKED_INSUFFICIENT_CAPABILITY` | Contextual temporal overlap, not event exclusion. |
| Five accepted events support a conservative whole-Moon one-hour detected-count floor. | `SUPPORTED_WITH_ASSUMPTIONS` | Detected-count floor under explicit assumptions, not calibrated flux. |
| The five events establish a calibrated brightness-threshold lunar impact flux. | `BLOCKED_MISSING_MEASUREMENT_FUNCTION` | Blocked until a recomputable measurement function is public. |
| The two marks around the 00:51 report are independent confirmations suitable for capture-recapture inference. | `BLOCKED_DEPENDENCE_MODEL_MISSING` | Separate witness marks are preserved, but independence is not assumed without a declared dependence model. |

## Why each finding landed there

### The public annotation contains five accepted events, eight witness marks, and three observers.

**SUPPORTED**

- Observed: Event Count: 5, Witness Marks: 8, Unique Observers: 3, Observers: Jeremy Hansen, Reid Wiseman, Victor Glover
- Expected: Event Count: 5, Witness Marks: 8, Unique Observers: 3

Claim ceiling: Credible event ledger, not calibrated sensitivity or independent detections.

### The later 30 fps window covered the annotation's 01:04 background-photo epoch.

**REFUTED_NONOVERLAP**

- Window Id: later-saw3-30fps
- Gap Seconds: 913

Claim ceiling: Metadata-time non-overlap only. The photo epoch is not ledger creation or an upper bound for all five accepted events; their event-level video coverage remains unestablished.

### The absence of a screened pulse in the overlap clip excludes the shared crew report.

**BLOCKED_INSUFFICIENT_CAPABILITY**

- Window Id: overlap-saw3-59.94fps
- Overlaps: Yes
- Missing Capabilities: source_pixel_equivalent, radiometrically_calibrated, detection_completeness_at_50_percent, target_resolved_for_localization

Claim ceiling: Contextual temporal overlap, not event exclusion.

### Five accepted events support a conservative whole-Moon one-hour detected-count floor.

**SUPPORTED_WITH_ASSUMPTIONS**

- Accepted Event Count: 5
- Sphere Area Km2: 3.80459e+07
- Duration Hours: 1
- Value Km2 Hour: 1.3142e-07
- Expected Value Km2 Hour: 1.3142e-07
- Relative Error: 0

Claim ceiling: Detected-count floor under explicit assumptions, not calibrated flux.

### The five events establish a calibrated brightness-threshold lunar impact flux.

**BLOCKED_MISSING_MEASUREMENT_FUNCTION**

- Missing Fields: monitored_area_km2, live_time_hours, limiting_magnitude, detection_probability_surface, calibrated_brightness

Claim ceiling: Blocked until a recomputable measurement function is public.

### The two marks around the 00:51 report are independent confirmations suitable for capture-recapture inference.

**BLOCKED_DEPENDENCE_MODEL_MISSING**

- Candidate Id: shared-transcript-report
- Witness Marks: 2
- Independent Marks: 0
- Dependency Model: Not provided

Claim ceiling: Separate witness marks are preserved, but independence is not assumed without a declared dependence model.

## Observation windows

| Window | Start | Stop | Target |
|---|---|---|---|
| Later assessed SAW3 window | 2026-04-07T01:19:13Z | 2026-04-07T01:21:23Z | Moon |
| Context clip spanning the shared report | 2026-04-07T00:51:10Z | 2026-04-07T00:51:25Z | Moon |

## Witness marks

| Candidate | Observer | Time state | Mark time | Elicitation | Independence |
|---|---|---|---|---|---|
| Annotated event 1 | Reid Wiseman | unknown | Unknown | unknown | not_established |
| Annotated event 2 | Reid Wiseman | unknown | Unknown | unknown | not_established |
| Annotated event 2 | Jeremy Hansen | unknown | Unknown | unknown | not_established |
| Annotated event 3 | Jeremy Hansen | unknown | Unknown | unknown | not_established |
| Annotated event 4 | Reid Wiseman | unknown | Unknown | unknown | not_established |
| Annotated event 4 | Jeremy Hansen | unknown | Unknown | unknown | not_established |
| Annotated event 4 | Victor Glover | unknown | Unknown | unknown | not_established |
| Annotated event 5 | Reid Wiseman | unknown | Unknown | unknown | not_established |
| Shared transcript report at 00:51 | Reid Wiseman | exact | 2026-04-07T00:51:15.947Z | unprompted | not_established |
| Shared transcript report at 00:51 | Jeremy Hansen | exact | 2026-04-07T00:51:54.985Z | socially_cued | dependent |

## Artifact integrity

| Artifact | State |
|---|---|
| artemis-event-ledger | `MATCH` |
| shared-report-excerpt | `MATCH` |
| camera-coverage-summary | `MATCH` |
| nasa-preliminary-report | `REFERENCE_ONLY` |
| nasa-citizen-science-update | `REFERENCE_ONLY` |

## Claim ceiling

This case may establish the annotated witness pattern, selected transcript anchors, metadata-time non-overlap with the background-photo epoch, the poor clip-native recovery of one contextual screen, and a conservative detected-count floor. It does not certify ledger creation, bound all five event times, certify coverage or noncoverage of every accepted event, map reports one-to-one to numbered events, establish independent witnesses, exclude a reported flash, estimate calibrated physical flux, prove every candidate's cause, or accept an operational recommendation on NASA's behalf.

## What would change this receipt

- Publish event-level time intervals or uncertainty bounds before mapping transcript reports to numbered events.
- Publish verified live time, monitored area, radiometric response, limiting sensitivity, and task-shaped injection recovery before estimating flux.
- Declare a witness-dependence model before treating prompted or socially cued marks as independent detections.
- Bind every future camera null to event coverage, target-in-field evidence, and a passed capability gate.

## Reproduce

This bundle was generated deterministically from the case file and hash-pinned local artifacts. Rebuild it with the command documented in the project README.
