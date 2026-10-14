# Stage 11N: Artemis II flash exposure audit

**State:** VERIFIED_FLASH_EXPOSURE_RECEIPT

## Result

Five conservatively curated, cross-witnessed crew events support a conservative all-lunar detected-count floor, but not a completeness-corrected, brightness-threshold impact flux.

The assessed 30 fps null video begins 15 minutes 13 seconds after the official five-event ledger timestamp, so it is a later null window rather than a simultaneous test of any confirmed event.

## Reproduced event structure

- Annotated events: 5
- Witness marks: 8
- Multi-witness events: 2
- Three-witness events: 1
- Single-witness events: 3

## Camera timing

- Five-event annotation timestamp: 2026-04-07T01:04:00Z
- Assessed 30 fps video: 2026-04-07T01:19:13Z to 2026-04-07T01:21:23Z
- Start lag after the ledger: 913 seconds (00:15:13)
- Meaning: a later null interval, not a simultaneous non-detection of a confirmed event.

## Overlapping camera context

A separately materialized 60 fps SAW3 clip spans the 00:51:15.947 crew report, but the threshold-defined lunar image is only ten pixels across. A frozen screen found no qualifying pulse in the transcoded clip; that result is contextual and does not exclude the crew event.

The bounded extraction screened 900 frames at about 59.94 fps. At the report frame, the Moon occupied a threshold-defined 10-pixel footprint, equivalent to about 347 kilometers per apparent pixel as a sampling illustration. This is not source-pixel photometry or an optical-resolution measurement.

## What five can and cannot say about flux

NASA's lower-bound language is defensible in a narrow sense. If all five accepted events occurred within the nearly hour-long eclipse, rounding the interval up to one hour and dividing by the Moon's entire 38,045,944 square-kilometer surface gives a conservative detected-count floor of 1.31e-07 per square kilometer per hour. Missed events can only raise the realized all-lunar count density for that interval.

That floor is not a completeness-corrected or brightness-threshold flux and is not directly comparable to established surveys. Such a measurement needs brightness-dependent detection probability integrated over monitored area and live time. The public event record does not supply a calibrated human or instrument detection function, photometric threshold, observer live-time ledger, or continuously overlapping calibrated event frames.

The first-to-last clear transcript reports span 1324.226 seconds. Choosing that span instead of one hour changes a naive visible-hemisphere denominator by 2.72 times before any completeness correction. Those narrower-denominator values remain invalid as calibrated flux estimates.

## Observing-geometry illustration

At 46,000 miles versus the average Earth-Moon distance of 238,855 miles, inverse-square point-source geometry gives about 27.0 times more received flux, equivalent to 3.58 magnitudes. This helps explain why faint events were visible, but it is not flash photometry.

## Recommendations

### R1. Continuous event-window coverage

Run the dedicated impact sensor continuously across the complete dark-lunar observing interval, including pre-roll and post-roll, and publish verified live time.

Acceptance: Every crew event marker is either covered by calibrated frames or explicitly labeled uncovered with a reason.

### R2. Independent optical confirmation

Use two synchronized optical channels, separate detectors, or an equivalent independent discriminator so detector artifacts and spacecraft glints can be rejected.

Acceptance: The release records channel-level hits and the confirmation rule for every candidate.

### R3. Spacecraft-clock event bookmarks

Give each observer a voice or button event marker bound to the spacecraft master clock and a rolling pre-trigger and post-trigger buffer.

Acceptance: Event, audio, camera, suit, PCD, and spacecraft times reconcile within a published maximum error.

### R4. Human exposure ledger

Record observer, window, eyes-on-target intervals, target region, cabin illumination, dark-adaptation interruptions, and known reflections.

Acceptance: The release provides observer live time and the conditions needed to model human detection probability.

### R5. Injection-recovery completeness

Inject synthetic flashes into representative flight backgrounds and publish recovery probability by brightness, duration, position, background, and channel.

Acceptance: A versioned completeness surface accompanies any rate or flux claim.

### R6. Candidate-level evidence receipt

Publish confirmed, ambiguous, and rejected candidates with observer marks, coverage, detector results, timing uncertainty, location uncertainty, and final disposition.

Acceptance: A reader can trace every headline count to its evidence and see why excluded candidates were excluded.

### R7. Effective area-time release

Publish the brightness-dependent integral of detection probability over monitored lunar area and live time, not just duration or event count.

Acceptance: Flux can be recomputed from candidate count and a machine-readable effective area-time curve.

### R8. Target-scale sampling requirement

Set the sensor field of view and angular sampling from predeclared localization and photometry objectives, then publish plate scale, point-spread behavior, and window effects across the lunar disk.

Acceptance: An end-to-end flightlike test recovers injected flashes across the disk and reports brightness and location errors at the required detection threshold.

## Claim ceiling

Stage 11N may establish exact public-source identities, the annotated witness pattern, transcript anchor times, a later non-overlapping 30 fps null window, a contextual 60 fps clip spanning one transcript report, a threshold-defined ten-pixel lunar footprint in that transcoded clip, the absence of a screened pulse under the frozen rule, an approximate distance-based visibility advantage, a conservative all-lunar one-hour detected-count floor under explicit assumptions, the absence of a public calibrated exposure denominator, NASA's candidate-level description of a volunteer image, and a source-grounded measurement design. It cannot promote the pixel screen to source photometry or an event exclusion, promote the count floor to a completeness-corrected or brightness-threshold flux or an independently measured impact rate, establish a calibrated impactor-size distribution, assign exact one-to-one timing to all five annotated events, claim a simultaneous camera non-detection of any confirmed event, confirm a ground match to a crew event, independently prove the cause of every candidate, establish instrument flight readiness, claim NASA acceptance, or claim global novelty.
