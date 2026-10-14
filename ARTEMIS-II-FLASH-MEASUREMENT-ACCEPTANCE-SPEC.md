# Artemis flash measurement acceptance specification

Status: review candidate, not NASA-accepted requirements

Purpose: convert the strongest lessons from the Artemis II public record into falsifiable requirements for a future crewed lunar impact-flash campaign.

## Baseline NASA already owns

NASA's preliminary report already recommends a dedicated high-frame-rate, high-dynamic-range sensor, quantitative brightness and location measurements, camera and window calibration, passive audio, and synchronized clocks. This specification does not claim those ideas as new.

NASA's ground-based Lunar Impact Monitoring Program also supplies important precedents: two telescopes, simultaneous detection in both, an approximately 4 million square kilometer field, and stated completeness to magnitude +9. NELIOTA adds synchronized dual-band validation and synthetic-flash injection and recovery. This specification does not claim those mechanisms as new either.

The added proposal is an integrated acceptance and release contract. It joins human exposure, target coverage, clock alignment, instrument response, artifact discrimination, injection versioning, candidate disposition, and effective area-time in one independently replayable evidence chain. It defines what evidence should exist before a future camera null excludes an event or a candidate count becomes a flux.

## Science claims the system should support

| Claim class | Minimum evidence | Block the claim when |
|---|---|---|
| A candidate occurred | Candidate record, target coverage, time uncertainty, and independent discriminator | Target was outside coverage, timing is unresolved, or the artifact rule is absent |
| A reported event was not detected | Overlapping calibrated frames and demonstrated recovery at the claimed signal | Coverage, calibration, or completeness is missing |
| A reported event is excluded above threshold | Declared physical threshold, recovery probability, false-positive rule, and source-equivalent frames | The threshold exists only in transcoded digital counts or recovery is untested |
| An impact flux is measured | Candidate ledger plus brightness-dependent effective area-time | Monitored area, live time, confirmation rule, or detection function is missing |
| Human and camera records confirm each other | Clock-aligned first marks, prompt state, camera coverage, and a dependency model | A later prompted confirmation is counted as independent evidence |

## Required observing system

### 1. Continuous target coverage

Requirement: cover the complete predeclared dark-lunar interval, including rolling pre-trigger and post-trigger storage.

Acceptance evidence:

- a machine-readable interval ledger for every sensor and observer;
- explicit gaps with reason codes;
- target-in-field status for each interval; and
- preserved source-equivalent frames for every retained event window.

Failure rule: a gap is not a null, and a later camera interval cannot test an earlier event.

### 2. Target-conditioned optical performance

Requirement: derive field of view, angular sampling, exposure, dynamic range, and point-spread requirements from the intended brightness and localization claims.

Acceptance evidence:

- plate scale and point-spread behavior across the lunar disk;
- radiometric response, saturation, dark, and flat characterization;
- installed-window transmission and distortion characterization;
- lunar terrain class and relevant surface context for localized events;
- flightlike background scenes spanning expected lunar illumination; and
- uncertainty budgets for brightness, time, and position.

Failure rule: frame rate, pixel count, or a visible lunar disk alone does not establish detectability.

### 3. Independent artifact discrimination

Requirement: use two synchronized optical channels, separate detectors, or another predeclared discriminator capable of rejecting detector artifacts, cosmic-ray hits, glint, and moving objects.

Acceptance evidence:

- channel-level candidate flags;
- the exact confirmation and rejection rule;
- false-positive challenge cases; and
- retained ambiguous and rejected candidates.

Failure rule: no candidate may be promoted solely because one uncalibrated channel changed.

### 4. Master-clock event marking

Requirement: provide each observer with a low-burden voice or button mark tied to spacecraft time and the rolling camera buffer.

Acceptance evidence:

- raw first-mark timestamp and uncertainty;
- audio, camera, tablet, suit, payload, and spacecraft clock offsets;
- a published maximum reconciliation error; and
- preserved links from each mark to the relevant buffered artifacts.

Failure rule: annotation creation time and remembered event time must remain distinct.

### 5. Human exposure and dependence ledger

Requirement: treat each human observer as a time-varying detection channel rather than an always-on independent sensor.

Required fields:

- observer and viewing window;
- eyes-on-target start and stop;
- target region and viewing aid;
- cabin illumination and dark-adaptation interruptions;
- known reflections or obstructions;
- first-mark time;
- whether another report or discussion occurred first; and
- accepted, ambiguous, rejected, or no-observation state.

Failure rule: unprompted first marks, prompted confirmations, silence while exposed, and not exposed are four different states.

### 6. End-to-end injection recovery

Requirement: inject physically defined synthetic flashes into source-equivalent, flightlike backgrounds before interpreting nulls or rates.

The frozen grid must span:

- calibrated brightness or magnitude;
- duration and light-curve shape, including terrain-conditioned families;
- position across the lunar disk;
- mare, highland, border, and uncertain terrain states where relevant;
- background and window state;
- channel and exposure mode; and
- artifact and saturation cases.

Acceptance evidence:

- recovery probability and uncertainty for every frozen cell;
- brightness and location error for recovered events;
- predeclared science threshold and required recovery probability;
- false-positive performance; and
- immutable test inputs, code version, and result hashes.

Failure rule: do not tune the pulse, threshold, locations, or timing after viewing the recovery curve without declaring a new test version.

### 7. Candidate-level evidence receipt

Every candidate, including rejected and ambiguous candidates, should carry:

- stable candidate identifier;
- event time or interval and clock domain;
- lunar location or region and uncertainty;
- lunar terrain class, source, and uncertainty when localization supports it;
- structured witness marks with prompt state;
- sensor coverage and channel results;
- calibration and injection-test versions;
- supporting and limiting artifact identifiers and hashes;
- disposition and reason code;
- claim ceiling; and
- evidence that would reopen the disposition.

Acceptance test: an independent reader can reproduce the headline count and determine why every excluded candidate was excluded.

### 8. Measurement-function release

Release human and instrument detection functions separately until their dependencies are modeled. A useful representation is:

`F(L) = N(L) / integral integral p_detect(L, x, t, channel, state) dA dt`

Required machine-readable outputs:

- candidate table by threshold;
- monitored-area and live-time ledger;
- channel-specific detection probability surface;
- terrain-conditioned detection terms when light-curve duration changes recovery;
- confirmation rule;
- effective area-time curve or multidimensional surface;
- uncertainty propagation; and
- the exact software and source identities used to compute the published value.

Failure rule: duration, full-disk area, event count, or file count is not a substitute for effective area-time.

## Minimum release package

1. Source and calibration artifact manifest with hashes.
2. Clock and coverage interval ledger.
3. Structured human witness-mark ledger.
4. Complete candidate table, including ambiguous and rejected cases.
5. Frozen injection inputs and recovery results.
6. Channel-specific detection functions.
7. Effective area-time product.
8. Human-readable and machine-readable claim receipt.

## Reproducibility gate

A release passes only if an independent implementation can:

1. reconstruct coverage for every candidate;
2. reproduce the accepted count;
3. reproduce the missing-capability state for each non-exclusionary null;
4. reproduce the completeness surface from frozen injections; and
5. recompute any published flux and uncertainty from the candidate table and effective area-time product.

## Artemis II changed-case example

The public Artemis II record illustrates why each gate is necessary:

- the five-event ledger is credible but the human detection function is absent;
- the assessed 30 fps camera interval begins after the annotation's background-photo epoch and the retained clear report anchors; that does not certify when the ledger was assembled or bound every accepted event time;
- a separate 59.94 fps clip overlaps one report, but its Moon is only a threshold-defined 10 by 9 pixel footprint;
- that footprint alone does not determine detectability;
- the frozen contextual screen recovers only 5.6 percent of trials at its maximum requested pulse and never reaches 50 percent; and
- the resulting null is contextual, not exclusionary.

## Authority and review boundary

NASA owns mission design, safety, science priorities, operational feasibility, and acceptance. Lunar-impact, instrumentation, human-factors, and planetary-data specialists should review the proposed fields, recovery design, timing tolerances, and carrier. This document supplies a concrete review target. It does not establish that every requirement is operationally optimal or that NASA has accepted it.

## Primary method anchors

- NASA, Artemis II Preliminary Lunar Science Report: https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/
- NASA, Lunar Impact Monitoring Program: https://ntrs.nasa.gov/citations/20240011287
- Xilouris et al., NELIOTA monitoring system and injection completeness: https://arxiv.org/abs/1809.00495
- Liakos et al., NELIOTA results after 6.5 years: https://doi.org/10.1051/0004-6361/202449542
- Athanasopoulos et al., mare versus highland lunar impact-flash light curves: https://doi.org/10.1051/0004-6361/202660978
