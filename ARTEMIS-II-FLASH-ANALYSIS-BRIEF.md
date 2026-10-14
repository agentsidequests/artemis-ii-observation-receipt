# Artemis II flash analysis brief

> 12 October 2026 source correction: the earlier distance/visibility illustration below is historical conditional arithmetic, not an established Artemis observing advantage. Its physical interpretation is withdrawn. See the [matched-epoch range audit](paper-review/range-geometry/RANGE-RECONCILIATION.md). Do not publish the older distance-advantage chart as a verified result. The accepted-count and no-calibrated-flux boundaries are unchanged.

> 12 October timing correction: 01:04 UTC is the annotation's background-photo/context epoch, not a verified ledger-creation time or an upper bound on all five events. Coverage of every accepted event by the later video remains UNESTABLISHED. See [the timing qualification](TIMING-SOURCE-QUALIFICATION.md). Both the old timeline and distance-advantage graphics are withdrawn from current use.

## Executive finding

The five Artemis II lunar flashes are scientifically credible, but the strongest public conclusion is more precise than the headline versions.

NASA has a conservatively curated ledger of five accepted impact-flash observations, supported by eight witness marks from three crew members. Conditional on NASA's impact classification, that ledger can support a deliberately conservative all-lunar detected-count floor of about `1.31 x 10^-7 km^-2 h^-1` for the eclipse interval. It cannot yet support a completeness-corrected, brightness-threshold impact flux comparable to established ground surveys.

Five is not, by itself, evidence of a lunar-impact surge. A 2024 NELIOTA analysis extrapolated its validated sporadic sample to about 7.4 meteoroids per hour over the full Moon for its sampled physical regime. That puts five in the same broad order, while the incompatible thresholds prevent a formal comparison. The useful opportunity is to understand human detection during the dark eclipse and why the uncalibrated camera record cannot quantify it. The earlier source-reported 46,000-mile visibility interpretation is withdrawn by the matched-epoch audit linked above.

The archive also contains two camera facts that should not be collapsed into one:

1. The 30 fps video NASA assessed for flashes begins at 01:19:13 UTC, 15 minutes 13 seconds after the annotation's background-photo/context epoch. This does not certify when the ledger was assembled or bound all five accepted event times. The video follows the retained clear report anchors, but coverage of every numbered event remains unestablished.
2. A different SAW3 stream does overlap the shared 00:51:15.947 crew report. A bounded extraction recovered the exact 15-second interval at about 59.94 fps. At the report frame, however, the Moon occupies a threshold-defined footprint only ten pixels across. A frozen screen found no qualifying brightness pulse in the transcoded clip. A 1,458-trial injection test then showed that this screen had very poor clip-native recovery, so the null cannot exclude the crew event or supply source-pixel photometry.

This creates a stronger and more useful conclusion than either "five mysterious flashes" or "the cameras saw nothing": Artemis II produced a credible event ledger and a compelling instrument-design case, but not yet a calibrated flash survey.

The headline word "mysterious" is not NASA's scientific state. NASA treats the five accepted events as impacts after the crew and science team distinguished them from cosmic-ray eye flashes and spacecraft glint. This Testbed does not independently confirm that physical classification. The unresolved scientific problem is narrower and more consequential: how many flashes were detectable, at what brightness, over what area and live time, and with what false-positive rule.

## What NASA has already established

NASA's preliminary report says five distinct flashes were reported during the eclipse, several additional possible flashes were not formally reported, and some accepted events were observed simultaneously by multiple crew members. The crew described the events as distinct from cosmic-ray eye flashes and spacecraft glint. All definitive flashes were on the non-illuminated Moon, with none reported in earthshine or sunlight.

NASA treats the observations as impact flashes and says they likely include the faintest events ever seen with unaided human vision. It estimates impactors on the order of several centimeters and says the observations place a lower bound on lunar impact flux. The crew's conservative exclusion of ambiguous sightings strengthens the accepted ledger.

NASA also already recommends:

- a dedicated high-frame-rate, high-dynamic-range impact-flash sensor;
- quantitative brightness, timing, and location capability;
- camera calibration and characterization, including window effects;
- passive continuous crew audio; and
- synchronized timestamps across cameras, crew systems, voice loops, payloads, and spacecraft time.

Those are NASA's recommendations. The analysis below extends them into acceptance criteria and release requirements rather than presenting them as new proposals.

## The event record

The official annotation contains five accepted events and eight witness marks:

| Event | Reid Wiseman | Jeremy Hansen | Victor Glover | Witness count |
|---|---:|---:|---:|---:|
| 1 | Yes | No | No | 1 |
| 2 | Yes | Yes | No | 2 |
| 3 | No | Yes | No | 1 |
| 4 | Yes | Yes | Yes | 3 |
| 5 | Yes | No | No | 1 |

This gives three single-witness events, two multi-witness events, and one three-witness event. The cross-witness structure supports credibility, but it is not capture-recapture data. Attention, viewing position, dark adaptation, reflections, and eyes-on-target time were dependent and changed during the interval.

The real-time transcript contains clear or possible anchors at 00:41:00.680, 00:51:15.947, 00:52:52.411, 00:59:18.291, and 01:03:04.906 UTC. The post-flyby conference says the timing of the first four accepted events was unclear and the crew did not announce every event. Therefore, those voice anchors cannot be assigned one-to-one to the five numbered annotation marks.

## What "lower bound" can mean

NASA's lower-bound language is defensible in a narrow count-based sense.

Using NASA's approximate lunar radius of 1,740 km:

`full lunar surface = 4 pi R^2 = about 38.0 million km^2`

The five accepted events occurred within the nearly hour-long eclipse. Rounding the interval up to one hour and using the Moon's entire surface as the spatial denominator gives:

`5 / (38.0 million km^2 x 1 hour) = about 1.31 x 10^-7 km^-2 h^-1`

This is a conservative detected-count floor for that interval. The whole lunar surface is larger than the observed region, and one hour is longer than the 22-minute span between the first and last clear transcript reports. Conditional on NASA's accepted-impact classification, additional missed events would raise the realized all-lunar count density.

This is not a calibrated flux estimate. It has no limiting magnitude, no brightness-dependent detection probability, no observer live-time ledger, no completeness correction, and no long-run sampling model.

Established surveys publish those missing terms. NASA's ground program and the Suggs analysis couple counts to photometric-quality live time, monitored area, a magnitude threshold, and simultaneous detections in independent telescopes. NELIOTA uses synchronized dual-band 30 fps cameras, GPS timing, and synthetic-flash injection and recovery. Its published completeness changes from about 98 percent at magnitude 10.4 to 50 percent at 11.4 and roughly 2 percent at 12.4.

The general measurement is:

`F(L) = N(L) / integral integral p_detect(L, x, t) dA dt`

Artemis II publicly supplies a credible `N`, plus enough geometry to state a conservative count floor. It does not yet supply the calibrated detection function and effective area-time needed for a survey-quality `F(L)`.

The count floor happens to be numerically near published ground-survey rates of roughly `1.03 x 10^-7` and `1.96 x 10^-7 km^-2 h^-1`. That numerical resemblance is not a scientific comparison because the brightness thresholds, monitored areas, confirmation rules, and completeness functions differ. It is an illustration of why a number without its measurement function can mislead.

## Camera evidence

### The later 30 fps null

NASA's report says Marshall assessed a roughly two-minute SAW3 clip at 30 fps and found no flashes. The exact PDS label dates that clip from 01:19:13 through 01:21:23 UTC. The five-event crew annotation is timestamped 01:04:00 UTC.

The camera window therefore begins 913 seconds after the displayed background-photo/context epoch, not a verified ledger-creation time. NASA describes the annotated image as downlinked after the flyby. It can establish that no flash was detected in that later two-minute interval under that camera configuration. It cannot establish that a confirmed crew event failed to appear on camera, and the photo time cannot certify non-overlap with every accepted event. See [the timing qualification](TIMING-SOURCE-QUALIFICATION.md).

### The overlapping 60 fps context clip

A separate, continuous SAW3 product spans the 00:51:15.947 shared crew report. The first bounded extraction attempt exhausted a 64 MiB budget because the MP4's index sits at the end of a 2.96 GB object and the proxy allowed 32 MiB range responses. Reducing the range gate to one MiB recovered the exact 15-second interval with 37,761,060 accepted media bytes, leaving 29,347,804 bytes unused.

The verified subset contains 900 frames at about 59.94 fps. In the report-time frame:

- the threshold-defined lunar footprint is 10 by 9 pixels;
- the apparent diameter is 10 pixels;
- the lunar diameter divided by that footprint is roughly 347 km per apparent pixel; and
- a frozen region-of-interest screen found no frame meeting both the six robust-scale and 20 percent increase thresholds.

The screen is deliberately limited. The clip was decoded and re-encoded during bounded extraction, the camera was not radiometrically calibrated for this use, the lunar image is tiny, the exact flash-to-speech reaction delay is unknown, and the shared transcript report cannot be assigned to a numbered annotation event. "No screened pulse" is therefore contextual evidence, not an event exclusion.

The ten-pixel footprint does not by itself prove that a flash was invisible. An unresolved point source can still raise one or more pixel values if it is bright enough. The footprint instead exposes the missing terms: point-spread behavior, response and saturation, local background, source-pixel preservation, and an injection-recovery curve tied to physical brightness.

The next check quantified that limitation instead of merely disclaiming it. A frozen injection grid added normalized Gaussian pulses at nine locations, six start times, three durations, and nine requested per-frame signal levels. Across 1,458 trials, the region-sum screen recovered no trial through 12,000 requested integrated digital counts per frame. At 16,000, it recovered only 9 of 162 trials, or 5.6 percent. Fifty percent recovery was not reached.

At the median frame, the 20 percent relative-rise condition required about 599 added digital counts, but the robust-z condition required about 4,817. Frame-to-frame variation therefore controlled the screen. Pixel saturation limited the realized addition at the maximum requested level to 2,896 through 4,046 digital counts per frame, depending on time and location.

These are transcoded clip-native units, not physical brightness. The synthetic Gaussian is not a validated flash model, and the curve does not characterize source pixels or flight-sensor performance. Its proper use is narrower and still important: it shows empirically that the frozen null screen was too insensitive to constrain the event.

The result does establish an important design point: high frame rate by itself is insufficient. A useful future sensor must combine frame rate with narrow enough field of view, adequate angular sampling, point-spread characterization, sensitivity, dynamic range, calibration, and continuous coverage.

## Why five flashes need not imply a rate spike

A 2024 NELIOTA analysis extrapolated 192 validated flashes to about 7.4 sporadic meteoroids per hour over the Moon's full surface for the campaign's sampled physical regime. More than 75 percent of its inferred impactors had radii of 0.5 to 3 centimeters under the paper's adopted luminous-efficiency assumptions, broadly overlapping NASA's indirect several-centimeter description. Artemis II's five accepted events during a nearly hour-long eclipse are therefore not, by count alone, an obvious anomaly. The comparison is only a plausibility check. NELIOTA used calibrated dual-band detections and a defined survey selection, while Artemis lacks a limiting magnitude and human detection function. A Poisson significance calculation that treats the two thresholds as identical would manufacture precision the data do not contain.

A 2026 NELIOTA analysis adds a different design implication. Across 124 multi-frame flashes, highland and mare events had similar peak-magnitude distributions but different decay behavior: the reported highland decay timescale was about 0.11 seconds, compared with about 0.038 seconds for mare flashes. A future injection grid and completeness surface should therefore preserve terrain class and test terrain-conditioned light-curve families, not only peak brightness. The Artemis annotation provides rough locations, not the event localization and calibrated light curves needed to classify these five events by that result.

### Historical distance illustration, physical interpretation withdrawn

The earlier calculation assumed the NASA feature's 46,000-mile description and NASA's separately stated 238,855-mile average Earth-Moon comparison distance. The nominal flash-report epochs instead reproduce much closer ranges in the published navigation data. Retain the arithmetic below for history, not as an established observing advantage:

`(238,855 / 46,000)^2 = about 27 times more received flux`

Conditional on those historical inputs, that arithmetic corresponds to about 3.58 astronomical magnitudes. It does not qualify the distance input or establish a physical visibility advantage for these reports.

Do not replace this with a larger physical ratio calculated from the closer nominal ranges. Event geometry, visibility, passband, threshold and measurement response remain unqualified for that comparison. The count alone still does not establish an impact-rate anomaly, independently of this retired illustration.

## Ground-observer state

NASA organized a genuine citizen-science campaign and thanked volunteers for submitted videos. Its April update called the bright dot submitted by Joerg Tomczak an "impact flash candidate." It did not identify that candidate as a confirmed match to a crew event.

The crew conference says the accepted flashes were outside the Earth-glow region and were not expected to be correlatable from Earth. NASA's report also says coordinated ground observation was not always possible because Earth did not always have a view of shadowed lunar terrain.

The defensible state is:

- a real coordinated ground campaign;
- at least one publicly highlighted candidate; and
- no public event-level ground match established in the sources checked here.

A future match should require compatible time, lunar location, visibility geometry, bandpass, and independent-detection evidence.

## Explicit recommendations to NASA

### Priority 0: make the event measurable

1. **Continuous event-window coverage**
   - Requirement: operate the dedicated sensor across the complete dark-lunar interval with pre-roll and post-roll.
   - Acceptance: every crew bookmark is covered by calibrated frames or explicitly marked uncovered with a reason.

2. **Target-scale sampling requirement**
   - Requirement: derive field of view and plate scale from predeclared localization and photometry objectives, not from frame rate alone.
   - Acceptance: flightlike injection tests recover synthetic flashes across the lunar disk and report brightness and location errors at the required threshold.

3. **Independent optical confirmation**
   - Requirement: use two synchronized channels, separate detectors, or an equivalent independent discriminator.
   - Acceptance: every candidate records channel-level hits and the rule used to reject cosmic rays, glints, and detector artifacts.

4. **Master-clock bookmarks and rolling buffers**
   - Requirement: give observers a voice or button marker tied to spacecraft time and a rolling pre-trigger and post-trigger frame buffer.
   - Acceptance: event, audio, camera, suit, tablet, and spacecraft times reconcile within a published maximum error.

### Priority 1: make the rate recomputable

5. **Human exposure ledger**
   - Requirement: record observer, window, eyes-on-target intervals, target region, cabin light, dark-adaptation interruptions, known reflections, first-mark time, and whether discussion or prompting preceded the mark.
   - Acceptance: the release provides enough information to model human live time and detection conditions, and preserves unprompted first marks separately from prompted confirmations.

6. **Injection-recovery completeness**
   - Requirement: inject synthetic flashes into representative flight backgrounds across brightness, duration, position, and background state.
   - Acceptance: a versioned completeness surface accompanies every rate or flux claim.

7. **Candidate-level evidence receipt**
   - Requirement: publish confirmed, ambiguous, and rejected candidates with observer marks, prompt state, camera coverage, detector results, timing uncertainty, location uncertainty, and final disposition.
   - Acceptance: a reader can reproduce the headline count and see why every excluded candidate was excluded.

8. **Effective area-time release**
   - Requirement: publish the brightness-dependent integral of detection probability over monitored area and live time, with human and instrument channels represented separately until their dependencies are modeled.
   - Acceptance: a third party can recompute flux from a machine-readable candidate table, channel-specific detection functions, terrain state where relevant, and an effective area-time curve or surface.

`ARTEMIS-II-FLASH-MEASUREMENT-ACCEPTANCE-SPEC.md` expands these recommendations into a compact requirements, failure-rule, release, and independent-replay contract for specialist review.

## Editorial consequence

The flash analysis should strengthen the existing article rather than replace it.

The best unifying argument is that the release contains two opposite counting traps:

- A large product count can exaggerate independent information when many files are derivatives, views, or fragments of the same observation.
- A small event count can understate the underlying phenomenon while still being insufficient for a calibrated rate.

Both problems have the same remedy: publish the relationships, coverage, and measurement function that connect files to observations and observations to claims.

Recommended article structure:

1. Keep the existing archive/product-count opening.
2. Introduce the five flashes as the higher-stakes scientific case.
3. Keep transcript anchors, the annotation's background-photo epoch and camera windows distinct; explain the limited-interval 30 fps null without certifying all-event coverage.
4. Show the conservative count-floor calculation and its limit.
5. Reveal the overlapping 60 fps clip and ten-pixel lunar footprint.
6. End with the explicit eight-part measurement and release design.

For the main Substack version, the strongest visual sequence is:

1. witness structure without inferred all-event times;
2. count floor versus calibrated flux; and
3. ten-pixel overlap limit.

The witness matrix and injection-recovery chart can support the current bounded argument. The old timeline and distance-advantage charts are withdrawn and must not be reused, including in an appendix. The injection chart is useful when explaining why a null needs a published completeness test.

## Claim ledger

| Claim | State |
|---|---|
| Five accepted flashes exist in NASA's public record | Supported |
| Eight witness marks from three crew members support the ledger | Supported |
| The observations can set a conservative one-hour all-lunar detected-count floor | Supported with explicit assumptions |
| The five events establish a calibrated impact flux | Not supported |
| The later 30 fps null tested a numbered accepted event | UNESTABLISHED; background-photo timing does not bound all accepted events |
| A 60 fps contextual clip overlaps the shared 00:51:15.947 report | Supported |
| The Moon occupies a threshold-defined ten-pixel footprint in the report frame | Supported for the transcoded clip |
| No screened pulse in that clip excludes the crew event | Not supported |
| The frozen region-sum screen had demonstrated sensitivity to plausible flashes | Refuted; 50 percent synthetic recovery was not reached in clip-native units |
| A volunteer ground candidate is a confirmed crew-event match | Not supported publicly |
| Orion had about a 27-fold geometric light advantage over an Earth observer | WITHDRAWN as an established Artemis observing advantage; historical conditional arithmetic only |
| Several-centimeter impactor sizes were directly measured | Not supported; NASA's estimate is indirect |

## Recheck triggers

Reopen the analysis if NASA publishes any of the following:

- event-level timing or photometry;
- a mapping between transcript reports and numbered annotation events;
- packet-preserving overlapping camera subsets;
- camera calibration or point-spread data;
- a human eyes-on-target exposure record;
- a ground observation matched by time and lunar location;
- a brightness-dependent effective area-time curve; or
- specialist review that changes the event, measurement, or camera interpretation.

## Primary and technical sources

- NASA, Artemis II Preliminary Lunar Science Report: https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/
- NASA, Volunteers Help NASA Astronauts Record Lunar Flashes: https://science.nasa.gov/get-involved/citizen-science/volunteers-help-nasa-astronauts-record-lunar-flashes/
- NASA, Impact Flash citizen-science project: https://science.nasa.gov/citizen-science/impact-flash/
- NASA Moon facts: https://science.nasa.gov/moon/facts/
- NASA Meteoroid Environment Office lunar monitoring summary: https://ntrs.nasa.gov/api/citations/20240011287/downloads/Lunar_impact_monitoring_2024Sep.pdf
- Suggs et al., The Flux of Kilogram-sized Meteoroids from Lunar Impact Monitoring: https://arxiv.org/abs/1404.6458
- NELIOTA, wide-field high-cadence lunar impact monitoring: https://arxiv.org/abs/1809.00495
- Liakos et al., NELIOTA results after 6.5 years: https://doi.org/10.1051/0004-6361/202449542
- Athanasopoulos et al., terrain-dependent lunar impact-flash light curves: https://doi.org/10.1051/0004-6361/202660978
- GEODES Impact Flash project: https://www.geodes.umd.edu/impactflash
- Lunar Impact Flashes portal: https://lif.mi.imati.cnr.it/home_page.php?status=start
