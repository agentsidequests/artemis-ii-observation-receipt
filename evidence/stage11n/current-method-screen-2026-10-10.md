# Stage 11N current-method screen

## Decision this reading can change

Whether the Artemis II flash story should be framed as an unexpectedly high lunar-impact rate, or as a credible but deliberately conservative event ledger that exposes a missing measurement denominator.

## NASA's own conclusion and recommendations

The preliminary report calls five flashes distinct, notes several additional possible flashes were not formally reported, and says multiple crew members saw some events simultaneously. The crew distinguished them from cosmic-ray eye flashes and spacecraft glint. NASA describes the observations as a lower bound and recommends a dedicated high-frame-rate, high-dynamic-range sensor, quantitative brightness and location, calibrated cameras, passive audio, and synchronized timestamps.

Those recommendations are the baseline. Stage 11N must not present them as ours.

## The two meanings of lower bound

NASA's statement that the observations place a lower bound on lunar impact flux is defensible in a deliberately conservative, count-based sense. Five accepted impacts occurred within the nearly hour-long eclipse. Dividing five by the Moon's entire roughly 38.0-million-square-kilometer surface and rounding the observation interval up to one hour gives an all-lunar detected-count floor of about `1.31e-7 km^-2 h^-1`. Using the whole surface and the longer time makes the denominator as large as the public facts allow. Conditional on NASA's accepted-impact classification, additional missed events would increase the realized count density for that interval.

That value is not a completeness-corrected, brightness-threshold flux estimate. It carries no limiting magnitude, human detection function, photometry, or long-run sampling model. It cannot be compared directly with survey fluxes that define those quantities. The earlier stronger wording that no flux quantity follows at all has therefore been retired.

## What established lunar-impact surveys add

NASA's ground program and the peer-reviewed Suggs analysis couple event counts to photometric-quality live time, monitored lunar area, a magnitude completeness limit, and independent simultaneous detections. NELIOTA adds synchronized dual-band 30 fps imaging, GPS timing, and synthetic-flash injection and recovery. Its published recovery curve changes from about 98 percent at magnitude 10.4 to 50 percent at 11.4 and about 2 percent at 12.4.

The decision-changing delta is not simply a better camera. It is a publishable measurement function:

`F(L) = N(L) / integral_over_time_and_area p_detect(L, position, time) dA dt`

Artemis II publicly supplies a conservative count floor, but not the human or instrumental detection probability, brightness threshold, effective area-time, or continuously overlapping calibrated frames needed to evaluate that expression as a survey-quality measurement.

## Archive-level timing result

The NASA report says Marshall assessed a roughly two-minute 30 fps SAW3 video and found no flashes. The exact PDS label dates that video from 01:19:13 to 01:21:23 UTC. The official five-event annotation is timestamped 01:04:00 UTC. The high-rate video therefore starts 15 minutes 13 seconds after the five-event ledger already existed. It is useful evidence for a later null interval, but it is not a simultaneous camera test of any confirmed event.

An earlier streamed SAW3 product has label-timed overlap with the 00:51:15.947 shared crew report. A revised bounded transport route has now materialized the exact 15-second interval from 00:51:10 through 00:51:25 using 37.8 MiB of the 64 MiB ceiling. The verified clip contains 900 frames at about 59.94 fps.

That success tightens the camera interpretation but does not validate an impact. In the report-time frame, the Moon occupies a threshold-defined footprint only 10 pixels across, or roughly 347 kilometers per apparent pixel as a sampling illustration. A frozen brightness screen found no qualifying pulse in the transcoded clip. Because the subset was decoded and re-encoded, lacks photometric calibration, has a tiny lunar footprint, and cannot be assigned one-to-one to the official five-event annotation, the screen is contextual evidence and not an event exclusion.

The footprint is not itself a detectability limit. A sufficiently bright unresolved point source can change one or more pixels. What the ten-pixel image cannot supply on its own is target-conditioned point-spread behavior, calibrated response, local-background sensitivity, or useful localization. Those terms, rather than pixel count alone, determine whether a null is informative.

Stage 11Q then tested the screen rather than treating that disclaimer as sufficient. A frozen 1,458-trial grid injected normalized Gaussian pulses across nine locations, six start frames, three durations, and nine requested clip-native signal levels. The screen recovered no trial through 12,000 requested integrated digital counts per frame and only 5.6% at 16,000. Fifty percent recovery was not reached. At the median frame, robust-z 6 required about 4,817 added digital counts, versus about 599 for the 20% relative-rise condition. Frame variability, not the relative-rise gate, controlled. Clipping held the maximum realized addition below the controlling median-frame threshold.

This is not a physical completeness curve. It uses transcoded grayscale values, an unvalidated synthetic pulse, and the original region-sum screen. It does establish that the no-pulse screen is empirically insensitive in its own digital domain. The camera null therefore remains non-exclusionary for a stronger reason than absent calibration alone.

The five Nikon Z9 raw images admitted by Stage 4A begin about 36 seconds after the 00:51:15 report and are not event frames by timing alone.

## What the crew record adds

The real-time and post-flyby transcripts show why a count-only analysis fails:

- The crew did not announce every event.
- The science team said the timing of the first four was unclear.
- The location annotation was explicitly rough.
- Visibility depended on staring at the dark center, avoiding solar glow, preserving dark adaptation, and suppressing cabin reflections.
- One crew member explicitly acknowledged possible priming bias.
- The official annotation still carries useful cross-witness structure: five events, eight witness marks, two multi-witness events, and one three-witness event.

This supports credibility and conservative curation. It does not supply calibrated sensitivity.

## Ground-observer boundary

NASA's April citizen-science update thanked volunteers for submitted video and labeled the bright dot in Joerg Tomczak's image an "impact flash candidate." It did not identify it as a confirmed match to any crew event. In the post-flyby conference, Wiseman said his flashes were not in the Earth-glow region and he did not expect them to be correlatable by an Earth-based team. The preliminary report likewise says coordinated ground observations were not always possible because Earth did not always have a view of shadowed lunar terrain.

The defensible state is therefore: a real coordinated campaign, at least one publicly highlighted ground candidate, and no public event-level match established in the sources checked here. Any later ground match must satisfy time, lunar location, viewing geometry, and independent-detection criteria before it changes the crew-event receipt.

## Strongest defensible insight

The surprising number five need not mean an anomalously high lunar-impact rate. A 2024 NELIOTA analysis extrapolated its 192 validated flashes to about 7.4 sporadic meteoroids per hour over the full Moon for the survey's sampled physical regime. More than 75 percent of the inferred impactors had radii of 0.5 to 3 centimeters under an adopted luminous efficiency, broadly overlapping NASA's indirect several-centimeter description. Five accepted Artemis events in a nearly hour-long eclipse are of the same broad order, but the two counts have different selection functions and cannot support a formal rate or Poisson comparison.

Orion was about 46,000 miles from the Moon, versus an average Earth-Moon range of 238,855 miles. Pure inverse-square point-source geometry gives roughly 27 times more received flux, or a 3.6-magnitude advantage, before accounting for the exceptional dark-eclipse background and the crew's active search. This is an observing-geometry explanation, not a photometric measurement of the flashes.

## Explicit extension beyond NASA's report

NASA has already named the sensor, calibration, audio, and synchronization needs. The testbed's extension is an operational and release specification:

1. Continuous calibrated coverage of the complete dark-lunar interval.
2. Independent optical channels or an equivalent artifact discriminator.
3. Spacecraft-clock event bookmarks with a rolling frame buffer.
4. A human exposure ledger for eyes-on-target time, window, target region, dark adaptation, cabin light, reflections, first-mark time, and prior prompting or discussion.
5. Synthetic-flash injection and recovery on real flight backgrounds.
6. A candidate-level receipt that includes confirmed, ambiguous, and rejected events plus whether each witness mark was unprompted or prompted.
7. Machine-readable, brightness-dependent human and instrument detection functions, kept separate until their dependencies are modeled, plus the resulting effective area-time curve.
8. A target-scale sampling requirement tied to localization and photometry objectives, verified through end-to-end synthetic-flash recovery across the lunar disk.

## Stop rule

The conservative all-lunar one-hour detected-count floor may be reported only with its assumptions and its non-comparability to brightness-threshold surveys. Do not publish a completeness-corrected impact-rate estimate from the five events unless a calibrated denominator is found. Do not interpret the later 30 fps null as a failed capture of the confirmed flashes. Reopen the inference only if event-level photometry, overlapping frames, a calibrated human-exposure record, or independently matched ground observations become available.
