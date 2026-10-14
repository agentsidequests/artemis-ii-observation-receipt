# Adversarial flash claim audit

Date: 10 October 2026

Purpose: pressure-test the public flash brief and recommendations against the strongest plausible objections. This is an internal claim audit, not specialist acceptance.

## Claim-by-claim pressure test

| Public claim | Strongest objection | Evidence and correction | Disposition |
|---|---|---|---|
| Five accepted impact-flash observations are scientifically credible | Crew reports do not independently prove that every flash was an impact | NASA's report classifies the five as impact flashes after the crew distinguished them from cosmic-ray eye flashes and spacecraft glint. The Testbed can report NASA's accepted classification and cross-witness structure, but cannot independently establish physical cause for each event | Keep, attributed to NASA; do not call this independent confirmation |
| Eight witness marks and two multi-witness events strengthen the ledger | Witnesses shared environment, attention, training, and viewing geometry, so marks are not independent trials | The brief explicitly rejects capture-recapture use and names the dependencies | Keep as credibility structure, not calibrated sensitivity |
| Five events yield a conservative whole-Moon one-hour floor of about `1.31e-7 km^-2 h^-1` | The crew did not monitor the whole surface or a complete hour, so this is not a standard flux denominator | That is why the calculation is labeled an all-lunar detected-count floor. Using the full surface and one-hour ceiling deliberately enlarges the denominator. It is not an effective area-time or brightness-threshold flux | Keep only with the full-surface, one-hour, and non-comparability language adjacent |
| Missed events can only raise the realized count density | False positives or misclassification could lower the true impact count | Correct. The statement is conditional on NASA's five accepted events being impacts. It must not be presented as an unconditional physical truth | Keep the accepted-ledger assumption explicit; avoid broader wording |
| The numerical proximity to ground rates is illustrative only | Readers can still mistake side-by-side values for validation | The brief explicitly states that thresholds, monitored areas, confirmation rules, and completeness differ | Keep in technical brief; omit from the main article unless the warning is visually inseparable |
| The later 30 fps null did not test a ledger event | Annotation time is not necessarily a precise event time | It does not need to be. The five-event annotation already exists at 01:04:00 and the assessed window begins at 01:19:13, so that later window cannot contain any of those five preexisting events | Keep; limit the refutation to the five ledger events |
| The 59.94 fps clip overlaps a shared crew report | Speech can lag perception, and the report cannot be mapped to a numbered event | The clip is described as contextual overlap around a voice report, not event capture. The exact reaction delay and event mapping remain unknown | Keep only as context |
| The Moon is 10 pixels across in the report frame | Threshold choice changes the apparent footprint, and image sampling is not optical resolution | The brief and figure label the footprint as threshold-defined and explicitly reject an optical-resolution interpretation | Keep with threshold and representation attached |
| A ten-pixel Moon explains the camera null | A sufficiently bright unresolved point source can still change one or more pixels | The footprint shows poor sampling and localization, not a brightness limit. Detectability requires point-spread behavior, response, background, and injection recovery | Reject pixel count as a standalone detectability argument |
| No screened pulse appears | The detector may be insensitive | Stage 11Q directly confirms this objection. The original screen reaches only 5.6% recovery at the maximum requested pulse and never reaches 50% | Keep only as an insensitive contextual null; never as event evidence |
| The Stage 11Q curve shows plausible flashes were missed | The injected Gaussian, digital-count scale, and screen are not physically calibrated | Correct. The curve tests the frozen screen in transcoded clip-native units only. It does not define plausible physical flashes or a sensor threshold | Reject any physical-detectability interpretation |
| Orion had about a 27-fold point-source received-flux advantage | Human detectability also depends on window transmission, pupil, background, duration, spectrum, and geometry | The calculation is inverse-square geometry only and the brief says so. It does not transfer to luminous energy or impactor size | Keep as a plausibility explanation, not photometry |
| Five events imply an unexpectedly high lunar-impact rate | A modern NELIOTA analysis extrapolates about 7.4 validated sporadic events per hour over the full Moon for its sampled regime | The broad order makes five plausible, but different thresholds and selection functions prohibit a formal rate or Poisson comparison | Use only as contextual evidence against sensationalism |
| NASA should add a dedicated high-frame-rate, high-dynamic-range sensor | NASA already recommends this | The brief credits NASA first. The Testbed contribution is the explicit acceptance layer: target-conditioned plate scale, point-spread behavior, continuous coverage, injection recovery, effective area-time, and candidate receipts | Keep NASA's recommendation and our extension separate |
| A human exposure ledger would improve the impact rate | Human detection is too dependent and poorly controlled for a simple live-time correction | Correct. The ledger is necessary but not sufficient. It enables modeling; it does not guarantee a valid human-survey flux | Change any wording that implies the ledger alone calibrates observers |
| Effective area-time should be published | A human-and-camera hybrid may not have one simple scalar denominator | The recommendation is brightness-dependent and can be a multidimensional function or surface, not necessarily one scalar | Keep as a versioned machine-readable measurement function |
| A ground candidate is not a confirmed match | A match could exist in unpublished or newly released data | The brief says no public event-level match was found in the sources checked and includes a recheck trigger | Keep with dated public-source scope |

## Changed-case corrections

1. The screen null is weaker than the initial screen alone suggested. Stage 11Q supplies direct evidence of poor recovery and should be visible anywhere the null is mentioned.
2. The phrase "missed events can only raise" must remain conditional on NASA's accepted-impact classification. A false-positive model is outside the public data available here.
3. The numerical comparison with ground rates is educational but carries a high anchoring risk. It belongs in the technical brief or appendix, not the article's main narrative unless the non-comparability is part of the graphic itself.
4. The novel recommendation is not high frame rate, calibration, window characterization, passive audio, or time synchronization. NASA already owns those. The extension is a target-shaped acceptance and release contract.
5. The app prototype can represent `SUPPORTED`, `REFUTED_NONOVERLAP`, and two distinct blocked states. It still needs a second domain before any generality claim.

## Surviving public claim

The strongest defensible flash conclusion is:

> NASA's five-event ledger is credible and supports a deliberately conservative detected-count floor under explicit assumptions. The available camera records do not calibrate that count or exclude a crew report. The overlapping clip puts the Moon in only a ten-pixel footprint, and the frozen null screen fails its own clip-native injection-recovery gate. Future nulls need a task-shaped measurement function, not frame rate alone.

## Publication ceiling

Do not claim any of the following:

- independent physical confirmation of all five impacts;
- a calibrated impact flux or long-run rate;
- a brightness or energy limit from the overlap clip;
- event exclusion from either camera null;
- a measured several-centimeter impactor size;
- a confirmed citizen-science match;
- novelty for recommendations NASA already made; or
- generality of Observation Receipt beyond the Artemis fixture.
