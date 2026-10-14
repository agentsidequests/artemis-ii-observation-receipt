# Artemis II evidence accounting brief

## Executive finding

The strongest combined insight is no longer merely that one Artemis II Sunset became 4,290 archive products.

It is this:

> **Data abundance can hide a shortage of evidential opportunities.**

The Artemis II archive exposes that problem in two opposite directions.

- **Positive evidence can look more independent than it is.** In the frozen product-key split canary, the test partition contains 4,511 files. Of those, 4,307 share their exact capture identity with at least one training product. The remaining 204 share their reconstructed complete camera action with training. Zero test products are isolated from training at the complete-action layer.
- **Negative evidence can look more capable than it is.** A 15-second camera interval overlapping one crew flash report contains 900 frames at about 59.94 frames per second. Yet the Moon occupies only a threshold-defined 10 by 9 pixel footprint, and the frozen screen recovers only 5.6 percent of synthetic trials at the highest requested clip-native signal level. That null cannot exclude the reported event.

The shared failure is not “bad data.” It is substituting a technical count for a claim-specific opportunity:

- files for independent evaluation opportunities;
- frames for sensitive detection opportunities;
- witness marks for independent witnesses; or
- accepted events for a calibrated impact rate.

The constructive recommendation is a linked four-function receipt package. It declares the relationships that must remain intact, the selection process that produced labels and omissions, the weights that turn records into influence, and the coverage and sensitivity required for an observation or null to bear on a physical claim.

This is narrower than asking NASA to invent provenance, grouped splitting, calibration, or injection-recovery. NASA and adjacent scientific communities already practice all four. The remaining seam is to bind them to one exact claim, source snapshot, observation interval, and executable acceptance test.

## Four functions hidden inside an analysis table

The two mathematical gates developed below, independence and detectability, remain distinct. The broader public and operational synthesis now separates four functions that can change a claim before a model or rate calculation begins.

1. **Relationship:** which products, captures, actions, windows, or realized episodes share a parent?
2. **Selection:** which source observations received a target tag or entered the analysis population, and why?
3. **Weighting:** how much influence does each opportunity receive when counted as an action, product, or byte?
4. **Detection:** which human or instrument channels had demonstrated capability at the claimed threshold?

The current verified results make each function concrete. The Stage 11R split canary has zero complete-action-isolated test products. Target tags cover 3,413 of 7,606 source exposures and are strongly structured by activity, so blanks cannot become negative labels. Stage 11U now verifies the interaction between selection and weighting: Sunset is 20.418 percent of all source-exposure target fields, 45.502 percent of nonblank target fields, 33.989 percent of selected actions, and 52.413 percent of selected bytes. Thirty-six active scheduled-window memberships yield concentration-equivalent counts of 19.000 under action weighting, 16.824 under product weighting, and 14.703 under byte weighting. The human flash transcript crosses explicit attention, glare, luminance, dark-adaptation, workflow, and prompt states after the first retained report, so raw eclipse clock time is not a homogeneous human-exposure denominator.

The concentration values are descriptive indices expressed in window units, not effective sample sizes or independent events. The attention timeline establishes changing observation conditions, not per-state detection probabilities, prompt causation, or physical event clustering.

## New interaction result: selection and weighting compound

Stage 10W established that target-tag coverage is incomplete and strongly activity-structured. Stage 11U asks what happens when a common nonblank-target selection predicate is followed by different weighting units.

The selection panel is exact:

| Declared population and unit | Sunset rows | Denominator | Sunset share |
| --- | ---: | ---: | ---: |
| All source-exposure target fields | 1,553 | 7,606 | 20.418% |
| Nonblank source-exposure target fields | 1,553 | 3,413 | 45.502% |

Conditioning on a recorded, nonempty target value therefore changes the descriptive Sunset share by 2.229 times. In SQL, excluding both nulls and empty strings requires `target_id IS NOT NULL AND target_id <> ''`. The blank fields remain unknown rather than negative examples.

The weighting panel holds the tagged population fixed while changing the unit:

| Declared unit | Sunset | Selected or tagged denominator | Sunset share |
| --- | ---: | ---: | ---: |
| Actions with any nonblank tag | 311 | 915 | 33.989% |
| Nonblank-tagged source exposures | 1,553 | 3,413 | 45.502% |
| Products derived from those exposures | 4,659 | 10,239 | 45.502% |
| Bytes attached to those products | 409,399,017,151 | 781,104,206,358 | 52.413% |

The action-to-byte change is 1.542 times. Exposure and product shares match because every admitted exposure has exactly three representations. Those products are related views, not three new independent observations.

Four counterchecks keep the result from depending on one convenient coding choice. First, carrying selected actions' nonblank tag membership across their blank exposures retains a 51.495 percent Sunset share of selected bytes. Second, the overall byte majority is representation-sensitive: Sunset is 49.188 percent of tagged source-representation bytes, 52.720 percent of tagged raw-representation bytes, and 52.734 percent of tagged processed-representation bytes. Third, the fully tagged `24_Sunset` activity supplies 1,294 of 1,553 Sunset-tagged exposures. Outside that activity, Sunset is 12.223 percent of tagged exposures and 21.554 percent of tagged bytes. This identifies the main activity-conditioned mechanism but does not define a better target population. Fourth, across all 23 nonblank target-tag values, the concentration equivalent contracts from 5.064 tag values under fractional action weighting to 3.823 under exposure or product weighting and 3.191 under byte weighting. Sunset ranks first under every declared unit.

This does not show that NASA or any researcher used this query or weighting scheme. It does not validate target tags, estimate physical prevalence, equate bytes with scientific value, claim a byte majority in every representation layer, claim invariance to activity composition, or establish model bias. It establishes a prior design fact: selection and weighting can jointly determine which observations dominate a table before pixel analysis begins.

## What the missing fields leave unidentified

Stage 11V now quantifies the selection limit rather than leaving it as a warning. In the frozen complete-action cohort, N = 7,606 source exposures, K = 1,553 recorded Sunset values, and M = 4,193 blank target fields. Hold every nonblank field fixed and leave every blank unconstrained for Sunset membership. The possible completed field share is exactly:

`K / N <= Sunset field share <= (K + M) / N`

That is 20.418% to 75.546%. The width is M / N, or 55.128 percentage points. This is an assumption-bound completion range, not a confidence interval or a physical class-prevalence estimate. All 23 observed target-field values have the same marginal width; their upper endpoints cannot all be realized together. A 7,606-row witness file constructs the two Sunset extremes while preserving each recorded value.

A strict field majority requires at least 2,251 of the blank fields to be completed as Sunset. Completing 2,250 produces exactly 50%. The current fields support neither side of that majority decision.

The advice must distinguish two jobs:

| Job | Needed evidence | What it does not establish |
| --- | --- | --- |
| Certify a narrower deterministic metadata-completion range | Resolve actual individual fields, or declare and justify another constraint. Under this unconstrained model, widths at most 10, 5 or 1 percentage points need at least 3,433, 3,813 or 4,117 blank fields resolved. | These budgets are not statistical sample-size requirements or physical-label guarantees. |
| Estimate a task-specific target population using an audit sample | Declare the sampling frame, inclusion probabilities, dependence groups, label oracle and uncertainty model. Include already-tagged as well as blank observations when label validity is the question. | A sample estimate is not certification of every unreviewed field. |

NASA's Data User Guide already says primary targets were manually assigned for only a subset and were not thoroughly verified after the mission. The bounds therefore do not establish an archive defect or ask NASA to treat its archive as a supervised benchmark. They provide a conditional rule for anyone building such a benchmark: specify the intended population and annotation meaning, audit missingness and label validity separately, and label any estimation assumptions explicitly. Do not fill blanks from activity, camera or schedule proxies merely because those variables predict tag presence.

The native source recount matches the Python result. Exhaustive small binary-completion cases, row-level witness checks and ten declaration hard negatives support only these accounting and mathematical seams. They are not independent scientific validation or a proof that every semantic overclaim will be detected.

## New quantitative result: 4,511 test products, zero action-isolated tests

Stage 11L created one deliberately simple 80/20 canary by hashing each archive product identifier independently. The assignment is not an observed NASA or research pipeline. Its purpose is to test whether a superficially clean, filename-disjoint split preserves the known hierarchy.

Stage 11R now resolves every test product into three mutually exclusive bins:

| Relationship between a test product and training | Test products | Share |
| --- | ---: | ---: |
| Exact capture identity also appears in training | 4,307 | 95.478% |
| Exact capture absent, complete camera action appears in training | 204 | 4.522% |
| Complete camera action absent from training | 0 | 0.000% |

The accounting identity is exact:

> **4,511 test products = 4,307 capture-linked + 204 action-only-linked + 0 action-isolated**

The hierarchy becomes even clearer at the group level. The test partition contains 3,679 capture identities. Only 68 of those captures are absent from training, and all 68 belong to actions that are represented in training. The result is a precise funnel:

`4,511 test files -> 3,679 test-visible captures -> 68 capture-isolated groups -> 1,937 test-visible actions -> 0 action-isolated groups`

Across the complete assignment, those 1,937 crossing actions contain 20,601 of the 22,818 product rows, or 90.284 percent of the cohort.

This is more informative than saying that “some groups cross.” It shows what the test partition actually contains. Nearly every test row has a tighter relationship to training through the same underlying exposure, and every remaining test row still shares the same bracket action.

The result is structural, not causal. It does not establish that pixels are similar enough for a model to exploit, that an actual evaluation leaked, that performance would be inflated, or that product-level splitting is wrong for every task. A compression or representation-conversion task may intentionally compare alternate products from one capture. A model claiming new-action or new-event generalization has a different burden.

The exact question must come first:

> What unit must be unseen for this score to mean what the author says it means?

## The opposite error: 900 frames do not make a calibrated null

The flash record creates the mirror image of the split problem.

NASA's public record contains five accepted impact-flash sightings and eight witness marks from three crew members. One continuous SAW3 stream overlaps the shared 00:51:15.947 crew report. A bounded extraction recovered 15 seconds and 900 frames at about 59.94 frames per second.

A raw frame count makes that sound like dense negative evidence. The measurement chain says otherwise:

- the threshold-defined lunar footprint is only 10 by 9 pixels;
- the clip was reconstructed and transcoded rather than preserved as a calibrated source-pixel scientific product;
- the point-spread function, radiometric response, limiting signal, and window effects are not known for this use;
- the exact flash-to-speech delay and numbered-event mapping are unresolved; and
- a frozen 1,458-trial injection grid recovers no trial through 12,000 requested integrated digital counts per frame and only 9 of 162 trials, or 5.6 percent, at 16,000.

That injection result is itself narrow. The synthetic pulse is not a validated physical flash, the units are not astronomical brightness, and the screen is only one detector. It proves neither that the flight camera was incapable nor that a flash occurred in the clip. It establishes something sufficient for the claim decision: the available no-pulse screen lacks demonstrated sensitivity, so its null cannot exclude the crew report.

The count of frames therefore fails for the same reason the count of files fails. It does not name the opportunity relevant to the claim.

## Two gates, not one generic warning

The synthesis earns its keep only if it preserves two different mechanisms.

### Gate 1: independence

An evaluation claim needs a task-native relation that identifies which records must not straddle training and testing.

For the frozen camera cohort, the recoverable hierarchy is:

`archive product -> capture identity -> bracket action -> conditional temporal run -> action-to-plan membership`

The broader layers are not interchangeable. A five-second same-camera group is a useful stress relation, not a discovered semantic scene. A plan window is a navigation prior, not a guaranteed content boundary. Target tags and activity facets are annotations, not event identifiers.

A split receipt can prove that the declared relation was preserved. It cannot prove that the declared relation is scientifically sufficient.

### Gate 2: detectability

A null, count, or rate claim needs a measurement function showing when and where the phenomenon could have been detected.

For a brightness-conditioned flash flux, the relevant denominator has the form:

`effective area-time(L) = integral over area and time of p_detect(L, x, t, channel, state)`

The corresponding rate is not merely `count / clock time`. It is the accepted event count divided by that brightness-conditioned effective exposure, with confirmation and dependence rules stated.

Under a simple Poisson illustration, the probability of zero detections is `exp(-lambda * effective area-time)`. If effective area-time is unknown, a zero count does not produce a defensible finite upper bound on the physical rate. This is an explanatory identity, not a fitted Artemis II Poisson model.

A detectability receipt can prove that a declared injection-recovery and coverage gate was passed. It cannot prove that the injected family spans every real event or that the physical model is complete.

## One discipline, two mathematical objects

The two gates can be stated compactly without pretending they have the same units.

For an evaluation claim, define:

`N_unseen(r) = number of test groups under relation r that have no member in training`

The relation `r` must come from the task. It might be capture identity for a representation-conversion task, complete camera action for a new-action claim, or a reviewed observation episode for a new-event claim. In the frozen product-key canary:

`N_unseen(complete action) = 0`

All 1,937 test-visible action groups also appear in training. That fact defeats a new-action interpretation of this canary, but it says nothing about a task that intentionally works within captures or actions.

For a detection or rate claim, define the brightness-conditioned opportunity:

`E_detect(L) = sum over channels of the integral over area and time of p_detect(L, x, t, channel, state)`

Here the raw frame count is not the denominator. A frame contributes only through its coverage, live state, and demonstrated recovery for the signal family. The Stage 11Q injection grid does not estimate physical `E_detect(L)` because `L` is not calibrated. It does establish that 900 overlapping frames cannot be promoted to a capable null merely from cadence.

These quantities should never be added or compared numerically. Their connection is procedural: both remove records that do not supply the opportunity required by the claim.

| Proposed claim | Tempting raw count | Claim-relevant accounting | Current result |
| --- | ---: | --- | --- |
| Generalization to unseen camera actions | 4,511 test products | Test action groups absent from training | Zero in the frozen canary |
| Camera exclusion of a reported flash | 900 overlapping frames | Effective area-time above a calibrated signal threshold | Unavailable; clip-native recovery is poor |
| Independent human corroboration | 8 witness marks | Dependency-aware observer opportunities and accepted events | Five accepted events; independence not modeled |
| Physical impact flux | 5 accepted events | Accepted events divided by brightness-conditioned effective area-time | Blocked; only a conservative detected-count floor is supported |

This table is the practical core of evidence accounting. It makes the numerator, denominator, relation, and capability gate visible before a headline count is interpreted.

## Why witness counts belong in the same analysis

The five accepted events contain eight witness marks. That cross-witness structure strengthens credibility, but it does not create eight independent events and it is not capture-recapture evidence.

The observers shared a spacecraft, viewing conditions, science plan, conversation, and changing attention. Some confirmations followed another person's report. The required distinction is therefore not only observer identity. It is first-mark timing, prompt state, eyes-on-target opportunity, dependency group, and the model used to treat marks as independent or dependent.

This produces a consistent rule across files, frames, and people:

> **A record becomes evidence for a claim only after its relationship to other records and its opportunity to observe the target are declared.**

## What NASA and the field already do

The recommendation must begin by crediting the existing practice.

- [PDS4](https://pds.nasa.gov/datastandards/documents/) provides stable product identity, collections and inventories, relationships, source lineage, Local Data Dictionaries, and conformance validation.
- The [PDS Machine Learning Analysis dictionary](https://pds-data-dictionaries.github.io/ldd-ml/user/user-guide.html) records dataset roles, versions, preprocessing, models, and evaluation information.
- [OGC TrainingDML-AI](https://docs.ogc.org/is/23-008r5/23-008r5.html) provides concepts for individual samples, split roles, data sources, labels, quality, provenance, and extensibility.
- NASA and IBM's [SomBench](https://ntrs.nasa.gov/citations/20260008699) keeps spatial parent zones intact across splits and materializes each tile's split role. This is strong evidence that leakage-aware grouping is already practiced in NASA lunar machine learning.
- NASA's lunar-impact monitoring program reports monitored area, live time, calibration, and detection thresholds. The [NELIOTA detection study](https://www.aanda.org/articles/aa/pdf/2018/11/aa33499-18.pdf) injects synthetic flashes into real lunar imagery and measures recovery as a function of magnitude.
- NASA's [Artemis II preliminary report](https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/) already recommends high-frame-rate, high-dynamic-range monitoring, camera and window characterization, passive timestamped audio, and synchronized clocks.

Those facts rule out several overstatements. NASA does not need to be told that provenance, grouped splitting, calibration, synchronized timing, or injection-recovery exist. The PDS archive is not defective because it does not decide every downstream estimand. An extensible standard is not deficient merely because one task-specific relation is not mandatory.

The narrow seam is end-to-end and claim-linked:

1. Which exact archived products and observation records bear on this claim?
2. Which of those records share a parent or dependence relation that the task must protect?
3. Which observers or sensors had overlapping exposure to the target?
4. Which of those channels had demonstrated capability at the stated signal threshold?
5. Which machine-readable result proves that the declared relations and measurement gates were actually preserved?

## Explicit recommendation: a linked four-function receipt package

NASA and the relevant PDS nodes should pilot one linked package for one frozen crew-camera task and one frozen transient-observation interval. The pilot should be anchored to exact PDS LIDVIDs and archive versions. It should remain experimental until mission and archive specialists accept the semantics.

### Receipt A: dependence and split integrity

Required fields:

- claim and task identifier;
- prediction unit, estimand, and target population;
- exact source snapshot and included PDS LIDVIDs;
- product-to-capture, capture-to-action, and any task-required episode relations;
- witness and prompt dependency groups when human marks are used;
- authority for each relation: mission-authoritative, reviewed-derived, unreviewed-derived, or unknown;
- complete assignment table, including excluded and unresolved states;
- protected relation or relations;
- split algorithm, version, seed, and hashes; and
- every crossing violation and every unknown membership.

Minimum acceptance:

- every in-scope record resolves to a declared state;
- no unknown or unreviewed relation is silently treated as independent;
- every protected group has zero partition crossings;
- many-to-many memberships are retained rather than forced to one owner;
- a separate consumer reproduces the assignments and metrics; and
- the receipt states that group preservation is necessary for the declared task, not proof of statistical independence or model validity.

### Receipt B: opportunity to detect

Required fields:

- exact claim, candidate set, and observation interval;
- observer and sensor coverage, field of view, and live time;
- source-equivalent frame identity and any transcode or processing state;
- plate scale, point-spread behavior, response, saturation, dynamic range, and window effects where relevant;
- observer eyes-on-target state, cabin light, dark-adaptation interruption, prompt state, and timing uncertainty;
- confirmation and rejection rules for cosmic rays, glints, reflections, and detector artifacts;
- injection family, parameter range, backgrounds, detector version, and recovery surface;
- effective area-time by signal threshold and channel; and
- candidate-level dispositions with accepted, ambiguous, rejected, retracted, uncovered, and capability-unknown states kept distinct.

Minimum acceptance:

- every event marker is covered or explicitly marked uncovered;
- a null is not called exclusionary unless the predeclared recovery gate passes for the relevant signal family;
- a rate or flux is blocked until effective area-time and threshold are available;
- human and instrument channels remain separate until their dependence is modeled;
- an independent user can recompute the headline count and denominator; and
- the receipt states which physical conclusions remain unsupported.

### Receipt C: selection and label production

Required fields:

- source population and inclusion rule;
- exact query or selection predicate and an attrition table showing what it removes;
- label source, authority, method version, and adjudication state;
- coverage by activity, camera, target, and relevant operational state;
- explicit blank, unknown, not-applicable, rejected, and unavailable states; and
- metadata-only baselines capable of exposing label-production shortcuts.

Minimum acceptance blocks blanks from becoming negatives, tagged prevalence from becoming archive prevalence, unreviewed labels from silently becoming physical truth, and a selection query from hiding its excluded population.

### Receipt D: weighting and influence

Required fields:

- prediction unit, estimand, and target population;
- action, exposure, product, and byte weights over explicitly matched populations;
- representation and exposure multiplicity;
- overlap allocation rule and conservation check;
- concentration table with declared units; and
- per-group influence or sampling probability.
- a sensitivity that carries partial action membership without promoting it to ground truth.

Minimum acceptance requires the analysis to show how results change under action, exposure, product, and byte weighting, keep the population fixed across columns or name every population change, preserve many-to-many totals under fractional allocation, and reject any interpretation of a concentration index as an effective sample size or physical-class count without a justified dependence model.

### Shared binding

The four receipts should share:

- one claim identifier;
- exact source identities and versions;
- clock-domain and uncertainty declarations;
- provenance and method versions;
- authority and review status;
- hashes for the canonical inputs and outputs;
- a compact human-readable explanation; and
- an explicit reopen trigger.

The production carrier may be a PDS supplemental product, mission product, Local Data Dictionary extension, OGC-aligned artifact, RO-Crate package, or linked Planetary Data Ecosystem resource. The pilot should discover the correct home through use. The analysis does not decide that institutional question.

## What this changes in the public argument

The original article lead remains valid but is now only the relationship case.

“4,290 products, one Sunset” shows how archival scale can exceed independent event scale. Stage 11R supplies a more direct evaluation result:

> **4,511 test files. Zero action-isolated tests.**

The selection and weighting results widen the argument. Target-tag coverage is 44.872 percent and strongly structured by activity. Once nonblank tags are selected, Sunset moves from 33.989 percent of selected actions to 52.413 percent of selected bytes, with a 51.495 percent action-carried sensitivity. Separately, 36 scheduled memberships contract to 19.000 action-weighted or 14.703 byte-weighted concentration-equivalent windows.

The flash case then prevents the essay from becoming only a familiar leakage warning:

> **900 overlapping frames. No calibrated null.**

Together the four functions support a stronger opening and a more consequential ending:

> NASA released an extraordinary amount of data. The next frontier is to publish the evidence accounting that says which records are related, selected, weighted, and detectable for each claim.

The article should not claim a new lunar-science discovery. Its value is a reproducible methodological finding, a clean structural canary, a measured capability failure in clip-native units, and a concrete pilot that respects what NASA already does.

## Claim ceiling

This brief supports a task-conditioned evidence-accounting argument. It may report the exact structural split decomposition, the exact frozen selection-weighting cascade and sensitivities, the exact frozen injection-recovery result, the distinction between a detected-count floor and calibrated flux, and the bounded linked-receipt recommendation.

It does not establish:

- observed leakage in an Artemis II model or benchmark;
- pixel similarity or exploitable shortcut information;
- a model-performance effect;
- target truth, physical target prevalence, or use of the tested selection-weighting cascade by an actual pipeline;
- statistical independence from a group key alone;
- a physical camera detection threshold;
- a camera non-detection of a numbered accepted flash;
- a calibrated impact rate or impactor-size distribution;
- a defect in NASA's archive or standards;
- global novelty or priority; or
- NASA, PDS, OGC, or specialist acceptance.

## Recheck triggers

Reopen this analysis if any of the following appears:

- a public Artemis II model, benchmark, dataset card, or split manifest;
- an authoritative exposure, action, episode, or event identifier;
- source-native overlapping flash frames or camera calibration;
- a crew eyes-on-target and prompt-state ledger;
- a brightness-conditioned effective area-time release;
- an event-level ground match;
- a revised PDS or OGC construct that directly carries the proposed relation and receipt semantics; or
- qualified specialist review that changes the independence, detectability, or standards interpretation.
