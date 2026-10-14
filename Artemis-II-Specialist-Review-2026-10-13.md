# Artemis II four-function specialist review packet

Updated: October 13, 2026

Status: Draft for qualified review. the maintainer's earlier archive inquiry received the scoped JPL response below. This packet has not been sent; no specialist has accepted its terminology, interpretation, carrier, or recommendations.

## Quick orientation

This packet asks two different specialists to correct four connected evidence-accounting functions before a public article or pilot proposal is treated as review-ready:

1. **Relationship:** which products, captures, camera actions, windows, or observations share a parent or dependence relation?
2. **Selection:** which source observations received labels or entered the analysis population, and what do blank or excluded states mean?
3. **Weighting:** how much influence does each opportunity receive when counted as an action, product, or byte?
4. **Detection:** which human or instrument channels had demonstrated opportunity and capability at the claimed threshold?

The governing claim is:

> Data abundance can hide a shortage of claim-relevant evidential opportunities.

The request is for correction and routing, not endorsement. The four functions are one accounting frame, but they do not share one technical oracle or institutional owner.

**Leading archive question:** Updated 13 October: JPL's science/archive teams confirmed the identical-image relationship between `art002e009301` and `art002e015991`, both original `019A0860.NEF`. What versioned source checksums and public-release processing evidence can qualify byte/transform lineage, and what independently qualifies the derived camera-action grouping? Only `art002e015991` was counted; no denominator is reduced. The team's cataloguing explanation is likely, and future documentation/mitigation is intended, not completed. This private correspondence does not confirm the other 23 candidate pairs, adopt our candidate or endorse the analysis. Public use remains subject to disclosure review. Our original finder remains source-order sensitive, and the results below remain frozen-order/algorithm-conditioned receipts. The separate candidate and historical withholding test follow the decision table.

| Review lane | Functions in scope | Best first reviewer | Decision the review must settle |
| --- | --- | --- | --- |
| Archive and ML | Relationship, selection, weighting | PDS archive or planetary ML metadata specialist | Whether the terms, derived relations, label-population treatment, weighting diagnostics, and proposed carrier are accurate and useful |
| Lunar-impact science | Detection, including human attention and camera capability | Lunar-impact monitoring or transient-detection specialist | Whether the observation-state, event, witness, camera, recovery, and effective area-time distinctions support the stated scientific ceiling |

## Decision summary

| Function | Frozen result | What it supports | What it does not support |
| --- | --- | --- | --- |
| Relationship | **4,511 test products = 4,307 capture-linked + 204 action-only-linked + 0 action-isolated** | One hypothetical product-level split has no test product isolated from training at the reconstructed complete-action layer | Observed leakage, exploitable pixel similarity, performance inflation, or a universal split rule |
| Selection | Target tags cover **3,413 of 7,606** source exposures, or **44.872%**; conditioning on nonblank tags changes Sunset's descriptive share from **20.418%** of all target fields to **45.502%** of nonblank fields | Blank tags cannot safely become negative labels, and the exact selection predicate must remain visible | Tag correctness, random-missingness classification, labeler intent, imputation, or physical target prevalence |
| Weighting | Inside the nonblank-tag subset, Sunset is **33.989%** of selected actions but **52.413%** of selected bytes; separately, **36** scheduled-window memberships yield **19.000** action- or **14.703** byte-weighted concentration-equivalent windows | Selection and unit choice can compound, and the apparent amount of opportunity changes materially with the declared unit of influence | Actual pipeline behavior, model bias, scientific value from bytes, effective sample size, independent events, or required mission reflight |
| Detection | The first retained flash report precedes explicit search intent by **138.865 s**; a separate overlapping 900-frame clip has no demonstrated calibrated sensitivity | Human exposure was nonstationary, and the clip-native null cannot exclude the report | Per-state detection probability, prompt causation, event photometry, physical clustering, or calibrated impact flux |

These quantities must not be added or treated as interchangeable. Their connection is procedural: each identifies a function that must be declared before a raw record count can bear on a claim.

## Reconstruction qualification and conditional comparison

The evidence chain has four distinct steps:

1. **Original baseline:** retained source order gives 2,166 reconstructed actions and 7,606 native capture keys. Reversing the same records through our unchanged finder gives 2,134 and 7,502. The 106-key symmetric difference is a local algorithm-admission result, not a NASA pipeline result or physical duplicate census.
2. **Identity census:** 24 exact nine-field candidate pairs occur among 10,329 raw IDs; 21 pairs disagree in target-field presence. Zero pairs have both IDs in the counted cohort. Matching metadata is not physical alias certification, and a field conflict is not a proven label error.
3. **Separate candidate:** complete-path enumeration gives 2,225 native-ID paths in 2,174 metadata-path families. Its output is identical across eight tested input orders. All 2,166 original paths are accounted for: 2,165 unambiguous metadata sequences and one original sequence in a withheld family. Nine identity-alternative families are withheld, including eight with no original path. They are not added physical actions. The candidate is not adopted; no native representative is selected.
4. **Conditional treatment:** remove the one affected original five-frame action, all 15 source/raw/processed products, their original assignment rows and two overlapping plan-membership rows. Preserve all surviving fields, original split bins, action and temporal keys, and schedule intervals. Do not rebuild clusters, resplit, add the alternative ID, or add the eight other withheld families.

The affected original action is `a2-action-1c22cc639e2f4792a76b8ca4`, captures `art002e015987` through `art002e015991`, camera `3920019`, 2026-04-07 01:06:17.480–01:06:19.780 UTC. Its last slot retains the `art002e009301` / `art002e015991` alternative; only `art002e015991` was counted. All five original fields are `Moon`, activity `28_Eclipsed Moon (2/2)`. Its two plan memberships are orders 28 and 29, both exact plan target `Moon`. The excluded products total 1,971,542,570 bytes: 13 original training rows and two capture-linked test rows.

The unchanged baseline reproduces all five canonical accounting blocks before any delta is interpreted.

| Quantity | Original frozen cohort | Conditional one-action withholding |
| --- | ---: | ---: |
| Products / native keys / original actions | 22,818 / 7,606 / 2,166 | 22,803 / 7,601 / 2,165 |
| Capture-linked / additional action-linked / isolated test products | 4,307 / 204 / 0 | 4,305 / 204 / 0 |
| Nonblank / blank target fields | 3,413 / 4,193 | 3,408 / 4,193 |
| Target-field coverage | 44.872% | 44.836% |
| Sunset selected-action share | 33.989% | 34.026% |
| Sunset combined selected-byte share | 52.413% | 52.545% |
| Sunset action-carried byte sensitivity | 51.495% | 51.623% |
| Source / raw / processed selected-byte shares | 49.188% / 52.720% / 52.734% | 49.294% / 52.855% / 52.870% |
| Raw action / product / byte concentration indices | 19.000 / 16.824 / 14.703 | 18.976 / 16.790 / 14.651 |
| Possible completed Sunset field share | 20.418–75.546% | 20.432–75.595% |

The selected Sunset numerators remain 311 actions, 1,553 keys and 409,399,017,151 bytes. Its combined-byte share increases by 0.132627 percentage points because a Moon-tagged denominator contribution is removed, not because a Sunset observation is added.

All eight named Boolean predicates survive: zero action-isolated test products; incomplete/activity-structured field selection; Sunset selected-action minority/combined-byte majority; source-tier minority/raw and processed majorities; most Sunset keys supplied by `24_Sunset`; outside-`24_Sunset` byte share below half; raw concentration ordered action > product > byte; and a completion range spanning 50%. This is one treatment, not eight independent replications or all-ambiguity robustness.

Thirty-six active windows and exact-name replication debt remain unchanged. Fractional and same-name-collapsed calculations replay, and unique-total conservation passes. Their conditional indices are respectively 18.024 / 15.794 / 13.561 and 17.328 / 15.311 / 13.168, not independent-event counts or effective sample sizes. Detection receipts are byte-preserved, not recomputed by this treatment.

Twenty focused checks and a separate native row/count/byte/split recount support the conditional calculation. Reconstruction independence is partial and physical identity remains unresolved across the full reconstruction; one steward-confirmed pair does not settle it. A green replay cannot accept archive semantics. Original receipts, counts and sources are unchanged; all remaining baseline tables refer to the original cohort.

### Conditional replay identity

- Result: `paper-review/downstream-sensitivity/result.json`, 152,230 bytes, SHA-256 `88c5451bed59ef2536c790459b3fffc92d566e93069349826f2a85e02adb79bf`
- Comparison: `paper-review/downstream-sensitivity/comparison.csv`, 392 scalar rows, SHA-256 `5a4dda40059c81087ddb687e890c8d6170efd038a300fa50e527d276f8beebf3`
- Withheld witnesses: `paper-review/downstream-sensitivity/withheld-products.csv`, 15 rows, SHA-256 `2abe4e773eb14ab7a9eaa6698b22b4850cdb1250fba327114c2db80c1667b0f1`
- Read-only replay from this repository root: `python -B -m src.camera_sequence_downstream_sensitivity --check`

The private Observation Receipt 0.4 `identity-confirmed` case displays the scoped steward statement separately from unverified local byte identity and unchanged historical sensitivity. Both native IDs remain; no representative or revised count is selected. The older 0.3 case remains a metadata-only control. The app is an inspectable consumer, not an archive-wide identity resolver, independent scientific replication, or substitute for reviewer acceptance. This candidate includes the exported replay inputs, code, app and evidence map. Qualified acceptance remains open.

## Function 1: relationship

### Frozen split canary

The frozen cohort contains 22,818 archive products. Stage 11L assigns products independently to an 80/20 train/test canary by hashing each product identifier. The assignment is deliberately simple and hypothetical. Stage 11R resolves every test product against the verified product-to-capture-to-reconstructed-complete-action hierarchy.

| Test-product relationship to training | Products | Share of test partition |
| --- | ---: | ---: |
| Exact capture identity also appears in training | 4,307 | 95.478% |
| Exact capture absent, reconstructed complete camera action appears in training | 204 | 4.522% |
| Reconstructed complete camera action absent from training | 0 | 0.000% |

The exact accounting identity is:

`4,511 test products = 4,307 capture-linked + 204 action-only-linked + 0 action-isolated`

At the group level:

`4,511 test files -> 3,679 test-visible captures -> 68 captures absent from training -> 1,937 test-visible actions -> 0 actions absent from training`

The 1,937 crossing actions contain 20,601 of all 22,818 product rows, or 90.284 percent of the cohort.

### Replay identity

- Assignment artifact: `results/stage11l-split-assignments.csv`
- Bytes: 4,573,289
- SHA-256: `2a372b95bc2897ee2d27400f7467d9d8ceb7c7410ed6fee7dab7aad0b1ed20d1`
- Receipt artifact: `results/stage11l-split-receipt.json`
- Bytes: 4,216
- SHA-256: `9fb6f1d180e66cffb83b19924b3c25650b7c144712eff97053bfdf0043a97b2a`

### Interpretation boundary

This is a structural fact about one frozen assignment. It does not establish that NASA or any researcher used this split, that pixels are similar enough for a model to exploit, that statistical dependence or leakage occurred, that performance would be inflated, that product-level splitting is always wrong, or that the archive is defective.

The task must define what must be unseen. A within-capture representation task may intentionally use related products. A claim about generalization to new camera actions has a different burden.

## Function 2: selection

### Frozen target-tag canary

Stage 10W audits tag presence, not image content or target correctness.

- Tagged source exposures: **3,413**
- Blank source exposures: **4,193**
- Total source exposures: **7,606**
- Coverage: **44.872%**
- Across 45 activity values: **17** have zero coverage, **8** have complete coverage, and **20** have partial coverage
- An in-sample activity-majority lookup classifies tag presence at **87.484%**, versus a **55.128%** global-majority baseline
- Activity association Cramér's V: **0.820465**

Examples show why a blank is not a stable negative class:

| Activity | Tagged | Total |
| --- | ---: | ---: |
| `24_Sunset` | 1,294 | 1,294 |
| `12_Orientale Basin (2/2)` | 0 | 399 |
| `07_Whole Moon` | 3 | 456 |
| `h_Observation Break` | 259 | 284 |

The result supports treating these tags as curated navigation metadata until a task-specific audit establishes a label population. It does not validate the nonblank tags, prove a formal missing-data mechanism, infer labeler intent, justify imputation, or estimate archive-wide target prevalence.

### Field completion is not content validation

With all recorded nonblank fields fixed and every blank unconstrained, the original Sunset field share can range from 1,553/7,606 to 5,746/7,606, or 20.418% to 75.546%. These sharp completion bounds are not confidence intervals, validated content labels or physical prevalence. A strict field majority needs 2,251 additional blank Sunset memberships. Worst-case widths of 10, 5 or 1 percentage points require resolving 3,433, 3,813 or 4,117 individual blank fields. These are deterministic completion budgets, not statistical sample-size recommendations. A quality-estimation audit needs a probability design and a valid concept/reference oracle; it must inspect recorded tags too.

The native plan's `Sunset` objective includes solar-corona structure, possible horizon glow and lunar-limb observations. The first review decision is whether a task predicts an archival field, recognizes depicted appearance, or makes a context-assisted physical judgment. These are not interchangeable. The unaccepted extended limb-adjacent light candidate records appearance separately from physical origin and requires stricter adequacy for an absence vote. Its ten synthetic cases are design checks, not image evidence. An image-specific published rendered-RGB analysis supplies no transferable camera calibration or valid reference labels for this panel.

A metadata-only feasibility proposal has 24 purposeful calibration IDs and 24 reserved confirmation IDs from 48 distinct reconstructed actions. Only calibration IDs appear in the opaque reviewer queue; native identifiers, original tags and selection reasons stay in the separate steward crosswalk. The proposed processed products total 8,480,681,056 bytes, not a measured download cost. Preview availability, viewing adequacy, real masking, concept/reference acceptance and reviewer performance remain unverified. No panel pixels or content labels were produced, no probability audit was executed, and the proposal does not certify independent scenes or events. Do not send the steward crosswalk as a blinded reviewer attachment.

## Function 3: weighting

### Frozen scheduled-opportunity concentration

Stage 11T starts with 36 active scheduled-window memberships across 19 exact plan names and computes:

`N_conc = 1 / sum(p_i^2)`

where `p_i` is a window's share of the declared weight.

| Sensitivity | Actions | Products | Bytes |
| --- | ---: | ---: | ---: |
| Raw active-window memberships | 19.000 | 16.824 | 14.703 |
| Fractionalized multiply assigned actions | 18.040 | 15.815 | 13.595 |
| Same-name overlap collapsed, fractionalized | 17.332 | 15.318 | 13.181 |

The two hard negatives preserve the conclusion while changing the exact value:

- fractional allocation conserves the unique totals instead of double-counting multiply assigned actions;
- collapsing four overlapping or touching same-name windows reduces representation multiplicity.

Descriptive replication debt is also unit-bound:

| Target | Exact-window debt | Same-name-collapsed debt |
| --- | ---: | ---: |
| At least 2 windows per exact plan name | 12 | 13 |
| At least 3 windows per exact plan name | 27 | 29 |

These are concentration indices expressed in window units. They are not effective sample sizes or independent-event counts. Exact-name equality is only a vocabulary match, not proof of comparable geometry, illumination, observer state, or scientific replication.

### Selection-weighting interaction

Stage 11U holds the frozen complete-action cohort and stored target fields fixed, then makes the selection predicate and unit explicit.

| Declared population or unit | Sunset | Denominator | Descriptive share |
| --- | ---: | ---: | ---: |
| All source-exposure target fields | 1,553 | 7,606 | 20.418% |
| Nonblank source-exposure target fields | 1,553 | 3,413 | 45.502% |
| Actions with any nonblank tag | 311 | 915 | 33.989% |
| Products derived from nonblank-tagged exposures | 4,659 | 10,239 | 45.502% |
| Bytes attached to those products | 409,399,017,151 | 781,104,206,358 | 52.413% |

Conditioning on recorded, nonempty target values (`target_id IS NOT NULL AND target_id <> ''` in SQL) changes the exposure-row share by 2.229 times. Changing from action to byte weighting inside the selected population changes the share by 1.542 times. An action-carried sensitivity that includes blank exposures from selected actions retains a 51.495 percent Sunset byte share.

The combined byte majority is representation-sensitive. Sunset is 49.188 percent of tagged source-representation bytes, 52.720 percent of tagged raw-representation bytes, and 52.734 percent of tagged processed-representation bytes. The claim is therefore about the combined selected byte mass, not every representation layer.

The main activity-conditioned mechanism is also visible. The fully tagged `24_Sunset` activity supplies 1,294 of 1,553 Sunset-tagged exposures. Outside that activity, Sunset is 12.223 percent of tagged exposures and 21.554 percent of tagged bytes. This is an attribution check, not a proposed replacement population.

The all-tag countercheck uses all 23 nonblank target-tag values. Its concentration equivalent contracts from 5.064 tag values under fractional action weighting to 3.823 under exposure or product weighting and 3.191 under byte weighting. Sunset ranks first under every declared unit.

The result is metadata accounting, not physical prevalence. It does not show that NASA or a researcher used this query or weighting scheme, that target tags are correct, that bytes measure scientific value, that every representation layer has a byte majority, that the result is invariant to activity composition, or that a model's behavior changed.

### Follow-on: weighted completion and majority robustness

The exploratory follow-on keeps the original nonblank selection, capture keys, representations and positive integer byte weights fixed. A recorded target-membership reassignment remains nonblank. It concerns one target, Sunset, and each lower/upper endpoint has its own constructive witness, not one joint multiclass completion.

For combined selected bytes, Sunset begins at 409,399,017,151 / 781,104,206,358 = 52.412855%. Removing the 48 largest recorded Sunset field weights subtracts 19,001,826,912 bytes of target membership, leaving 390,397,190,239 / 781,104,206,358 = 49.980167%. The best 47-field choice leaves 390,792,245,249 / 781,104,206,358 = 50.030744%. Exact integer crossings prove the 48-field minimum under the individual-field model. Those fields span 29 original actions, not 48 independent observations. They are hypothetical changes, not identified errors, random-error tolerance, a rank-reversal certificate or physical content judgments.

Raw and processed selected-byte majorities each require 54 analogous changes. Source-byte and exposure/product shares start below half, so their majority-loss minimum is zero. This is distinct from the one-action identity withholding above; surviving that treatment does not establish robustness to recorded-field reassignment.

At r = 0, weighted full-cohort Sunset completion remains 25.189424%–77.129794%. Equal individual-field-cost, perfect blank resolution requires 3,747 highest-weight resolutions to guarantee combined-byte width ≤5pp; exposure weighting requires 3,813. The gain is 66 fields. This is cardinality-minimal under the stated objective, not a statistical sample size, real audit, heterogeneous-cost optimum or recommendation that NASA backfill metadata. Recorded-tag validation and blank completion remain separate jobs.

Source: `results/stage10o-product-relationship-manifest.csv`, 10,072,026 bytes, SHA-256 `8edd58437cc609229edb5abb41c4e00048bb420354f1ac17a269da92c17e4729`. Result: `paper-review/tag-weight-robustness/result.json`, SHA-256 `afa22634e5bd5883d6bf5b22b76a708df3f7c976011786e94c045ef695a64c76`. The exact witness and priority CSVs, native recount, exhaustive-check scope and limits are in the same folder. Read-only replay: `python -B -m src.tag_weight_robustness --check`. The private app's separate `demo --case robustness` case exposes these assumptions and source rows; source matching and consumer recount do not add scientific acceptance.

## Function 4: detection

### Human observation state

Stage 11S binds exact transcript anchors into an ordered observation-state timeline:

| UTC | State transition | Decision relevance |
| --- | --- | --- |
| 00:41:00.680 | First retained report | Occurs before explicit search intent |
| 00:43:19.545 | Explicit search intent | 138.865 s after the first report |
| 00:43:39.492 | Glare identified | Viewing interference becomes explicit |
| 00:44:01.444 | Display dimmed | Cabin/display luminance changes |
| 00:44:59.421 | Dedicated watching begins | Attention becomes explicitly task-focused |
| 00:45:15.857 | Eyes continuing to adapt | Adaptation state remains in motion |
| 00:51:15.947 | Shared retained report | 376.526 s after dedicated watching begins |
| 00:52:52.411 | Explicitly ambiguous candidate | Confidence state remains distinct |
| 00:53:19.564 | Return to science timeline | Dedicated-watching interval closes after 500.143 s |
| 00:59:05.829 | Ground query ends | Observation becomes ground-prompted |
| 00:59:18.291 | Prompt-proximate report | 12.462 s after the query |
| 01:03:04.906 | Last clear retained report | 1,324.226 s after the first clear report |

The transcript therefore does not expose one homogeneous hour of human observation. Attention, glare, display luminance, dark adaptation, workflow, and prompting changed. This supports a state-segmented exposure ledger. It does not estimate how detection probability changed, show that prompting caused a report, establish witness independence, or show that physical events clustered.

### Camera capability

- NASA's public record contains five accepted crew-reported impact-flash events, eight witness marks, and three observers.
- The 30 frame-per-second SAW Cam 3 video assessed by NASA's Meteoroid Environment Office begins 15 minutes 13 seconds after the 01:04 UTC background-photo epoch used for the annotation. That is a metadata-time comparison, not proof of ledger creation or an upper bound on all five accepted events. NASA describes the annotated image as downlinked after the flyby. The video follows the retained clear report anchors, but their unresolved mapping does not establish non-overlap with every accepted event. Event-level intervals are still required. See `TIMING-SOURCE-QUALIFICATION.md`.
- A separate 15-second SAW3 clip overlaps the 00:51:15.947 crew report and contains 900 decoded frames at about 59.94 frames per second.
- In that transcoded clip, the threshold-defined lunar footprint at the report frame is only 10 by 9 pixels.
- A frozen grid injected 1,458 deterministic point-like synthetic trials into the decoded clip. The exact local screen recovered no trial through 12,000 requested integrated digital counts per frame and recovered 9 of 162 trials, or 5.6 percent, at 16,000. Fifty percent recovery was not reached.

The recovery grid uses uncalibrated clip-native units on a reconstructed, transcoded video. The synthetic pulse is not a validated physical lunar-impact flash. The result does not characterize the flight sensor, set a physical brightness limit, prove that a flash occurred in the clip, or overturn NASA's accepted classifications.

It supports one narrower statement: the local no-pulse result lacks demonstrated sensitivity and cannot exclude the overlapping crew report.

The five accepted events also support a conservative one-hour, whole-Moon detected-count floor of `1.31e-7 km^-2 h^-1` under explicit assumptions. That number is not a completeness-corrected or brightness-threshold flux. A calibrated rate requires a brightness-conditioned effective exposure, conceptually:

`effective area-time(L) = integral over area and time of p_detect(L, x, t, channel, state)`

Raw clock time, frame count, witness marks, and accepted-event count cannot substitute for that denominator.

The separate nominal-epoch range audit retired the earlier numerical flash-observation advantage's physical interpretation. That illustration is not reinstated here or replaced with photometry from the nearer navigation ranges. Exact flash locations, human thresholds, crater confirmation, capture-recapture inference and calibrated lunar impact flux remain unsupported.

## Existing practice the proposal must credit

This proposal does not ask NASA to discover provenance, grouped splitting, calibration, synchronized timing, or injection-recovery.

- [PDS4](https://pds.nasa.gov/datastandards/documents/) already provides product identity, collection inventories, relationships, source lineage, Local Data Dictionaries, and conformance validation.
- The [PDS Machine Learning Analysis dictionary](https://pds-data-dictionaries.github.io/ldd-ml/user/user-guide.html) records dataset roles, versions, preprocessing, models, and evaluation information.
- [OGC TrainingDML-AI](https://docs.ogc.org/is/23-008r5/23-008r5.html) covers individual samples, split roles, tasks, data sources, labels, quality, provenance, and extensibility.
- NASA and IBM's [SomBench](https://ntrs.nasa.gov/citations/20260008699) keeps spatial parent zones intact across splits and materializes each tile's split role.
- NASA lunar-impact monitoring reports monitored area, live time, calibration, and detection thresholds. The [NELIOTA detection study](https://www.aanda.org/articles/aa/pdf/2018/11/aa33499-18.pdf) measures recovery of synthetic flashes injected into lunar imagery.
- NASA's [Artemis II preliminary report](https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/) already recommends minimum camera calibration, a high-frame-rate and high-dynamic-range dedicated sensor, window characterization, continuous timestamped audio, and synchronized clocks.

The proposed addition is narrower: bind those practices to one exact claim, source snapshot, protected relation, selection rule, weighting rule, observation interval, capability test, and executable acceptance result.

## Proposed linked experimental receipts

These are pilot concepts, not a claim that PDS requires a new standard.

### Receipt A: relationship and split integrity

Record the claim, task, prediction unit, target population, exact source versions and PDS LIDVIDs, product-to-capture and capture-to-action relations, relation authority, complete assignment, protected relation, split method, hashes, crossings, and unknown memberships.

Minimum acceptance requires every in-scope record to resolve to a declared state, every protected group to have zero partition crossings, every unknown or unreviewed relation to remain explicit, and a separate consumer to reproduce the assignments and metrics. Test input-order perturbations and competing-path hard negatives; withhold unresolved native alternatives without choosing a convenient representative. If the admitted population changes, publish a distinct recomputation or conditional sensitivity with complete removed/added witnesses. The receipt must say that group preservation is necessary for the declared task, not proof of statistical independence or model validity.

### Receipt B: selection and label production

Record the source population, exact query or inclusion predicate, attrition by state, label source and authority, method version, adjudication state, coverage by activity and camera, explicit blank and unavailable states, and a metadata-only baseline for label-production shortcuts.

Minimum acceptance blocks blanks from becoming negatives, tagged prevalence from becoming archive prevalence, unreviewed labels from becoming physical truth, and a selection query from hiding the population it removed. Before annotation, accept the task's concept, viewing carrier, independent reference evidence and abstention rules. Keep feasibility, quality estimation and individual-field completion separate. A purposeful diagnostic panel cannot estimate population accuracy.

### Receipt C: weighting and influence

Record the prediction unit, estimand, explicitly matched populations, action/exposure/product/byte weights, representation and exposure multiplicity, overlap allocation rule, conservation check, declared concentration units, per-group influence or sampling probability, and an action-carried sensitivity when tag presence is partial within actions.

When reporting a selected-weight majority, also record the hypothetical membership budget, lower/upper witnesses, exact fixed denominator, smallest majority-changing perturbation and predecessor check. A blank-completion proposal must declare perfect-resolution assumptions, width objective, field unit and cost model separately from quality estimation. A blank-only audit cannot establish the correctness of the recorded-tag majority. Real unequal costs require a different accepted constrained objective before calling a priority optimal.

Minimum acceptance shows sensitivity to action, exposure, product, and byte weighting, names every population change, preserves totals under fractional allocation, and blocks any effective-sample-size or effective-physical-class interpretation without a justified dependence model.

### Receipt D: opportunity to detect

Record the claim, candidate set, interval, observer and sensor coverage, source-equivalent frame identity, processing state, optical response where relevant, human attention and adaptation state, prompt state, timing uncertainty, artifact-discrimination rules, injection family, detector version, recovery surface, effective area-time by signal threshold and channel, and candidate-level dispositions.

Minimum acceptance requires every event marker to be covered or marked uncovered, blocks exclusionary null language until a predeclared recovery gate passes, blocks rate or flux until effective area-time is available, keeps human and instrument channels separate until dependence is modeled, and lets an independent user recompute the count and denominator.

### Shared binding and carrier question

The four receipts should share one claim identifier, exact source identities and versions, clock-domain declarations, provenance and method versions, authority and review status, hashes, a compact human explanation, and an explicit reopen trigger.

Possible carriers include a PDS supplemental product, mission product, Local Data Dictionary extension, OGC-aligned artifact, RO-Crate package, or linked Planetary Data Ecosystem resource. The pilot should discover the correct carrier through use. This analysis does not decide the institutional home.

## Questions for the archive and ML reviewer

1. Given the steward-confirmed `art002e009301` / `art002e015991` pair, what versioned source checksums and release-processing records can qualify byte/transform lineage? What independent evidence qualifies the source-order-sensitive baseline or separate abstaining candidate? Are our product/capture/action terms accurate without a global physical identity certificate?
2. Which relationship, selection, and weighting fields already have suitable PDS4, Machine Learning Analysis dictionary, or OGC representations, and which should remain in a linked task artifact?
3. Do the selection/weighting comparison, one-action withholding and field-completion bounds have the stated limits? Which task definition and concept/reference gate would make the proposed label pilot meaningful, and what is the least burdensome carrier?
4. Is the 48-field individual-membership counterfactual a useful diagnostic of a selected-byte majority, and are its worst-case selection, fixed denominator and separate-extrema limits correctly stated? What recorded-tag validation and real retrieval/review costs would make either majority robustness or blank completion a worthwhile task? No audit, error rate or required statistical sample size is claimed.

## Questions for the lunar-impact reviewer

1. Is it accurate to treat the five accepted events, eight witness marks, changing human attention states, later 30 fps null, overlapping low-sampling clip, and effective area-time denominator as separate evidential objects?
2. Is “non-exclusionary because demonstrated sensitivity is absent” the right ceiling for the clip-native injection result, and is a state-segmented human-exposure ledger the right response to the transcript evidence?
3. Which minimum human-state, calibration, coverage, dependence, and injection-recovery fields would make a future camera null or brightness-conditioned rate scientifically interpretable?

## Low-burden response format

A reviewer need not assess the full repository. A useful response can label each questioned sentence or field:

- `ACCURATE`
- `NEEDS QUALIFICATION`, with the preferred wording
- `INCORRECT`, with the correct term or owner

The reviewer may also state whether the proposed pilot remains worth testing and identify the correct institutional owner. A correction or referral is sufficient.

## Evidence map

| Function or question | Local evidence |
| --- | --- |
| Native identity candidates and original input-order failure | `paper-review/identity-census/CENSUS-REPORT.md`, `paper-review/identity-census/result.json` |
| Separate, unadopted reconstruction candidate and full native-path accounting | `paper-review/order-robust-reconstruction/CANDIDATE-REPORT.md`, `paper-review/order-robust-reconstruction/result.json`, `paper-review/order-robust-reconstruction/membership.csv` |
| One-action conditional comparison, exact exclusions and native recount | `paper-review/downstream-sensitivity/contract.json`, `paper-review/downstream-sensitivity/result.json`, `paper-review/downstream-sensitivity/comparison.csv`, `paper-review/downstream-sensitivity/withheld-products.csv`, `paper-review/downstream-sensitivity/native-crosscheck.json`, `paper-review/downstream-sensitivity/SENSITIVITY-REPORT.md` |
| Relationship and split hierarchy | `results/stage11l-split-assignments.csv`, `results/stage11l-split-receipt.json`, `results/stage11r-hierarchical-isolation.json`, `results/stage11r-result.md` |
| Selection and target-tag coverage | `results/stage10w-result.md`, `spec/stage10w.json` |
| Field-completion mathematics and witnesses | `results/stage11v-result.json`, `results/stage11v-sunset-completion-witnesses.csv`, `evidence/stage11v/native-count-oracle.json` |
| Unexecuted task-specific audit and concept gates | `ARTEMIS-II-TARGET-LABEL-AUDIT-PROTOCOL.md`, `target-label-audit/pilot-prep/reviewer-packet.md`, `target-label-audit/corona-rubric/CANDIDATE-RUBRIC.md` |
| Weighting and concentration sensitivity | `results/stage11t-result.md`, `results/stage10z-action-plan-membership.csv`, `spec/stage11t.json` |
| Selection-weighting interaction and all-tag countercheck | `results/stage11u-result.md`, `results/stage11u-selection-weighting-cascade.json`, `spec/stage11u.json` |
| Weighted completion, hypothetical recorded-field sensitivity, minimum witness and equal-field-cost scope | `paper-review/tag-weight-robustness/contract.json`, `paper-review/tag-weight-robustness/result.json`, `paper-review/tag-weight-robustness/majority-reassignment-witness.csv`, `paper-review/tag-weight-robustness/blank-resolution-priority.csv`, `paper-review/tag-weight-robustness/native-crosscheck.json`, `paper-review/tag-weight-robustness/REPORT.md` |
| Human attention-state timeline | `results/stage11s-result.md`, `spec/stage11s.json` |
| Five-event witness structure and timing | `results/stage11n-result.md`, `evidence/stage11n/source/artemis-ii-preliminary-report-flash-pages.txt` |
| Overlapping video and footprint | `evidence/stage11o/acquisition-receipt.json`, `results/stage11p-overlap-pixel-screen.json` |
| Injection-recovery | `results/stage11q-injection-recovery.json`, `results/stage11q-result.md` |
| Nominal range audit and withdrawn observing-advantage interpretation | `paper-review/range-geometry/RANGE-RECONCILIATION.md`, `paper-review/range-geometry/result.json` |
| Four-function synthesis and field proposal | `ARTEMIS-II-EVIDENCE-ACCOUNTING-BRIEF.md`, `STANDARDS-AND-PRIOR-ART-CROSSWALK.md` |
| Detailed archive field crosswalk | `ARTEMIS-II-CLAIM-AND-PILOT-REVIEW-PACKET.md` |
| Detailed flash acceptance proposal | `ARTEMIS-II-FLASH-MEASUREMENT-ACCEPTANCE-SPEC.md` |

## Present acceptance state

This packet is structurally self-contained and the local quantities, hashes, and links are mechanically reviewable. The scientific interpretation, PDS terminology, institutional carrier, reviewer comprehension, and operational value have not been accepted by a qualified specialist. They remain `NOT VERIFIED` until the relevant reviewers respond.

The smallest unsupported claim is still decisive: this packet cannot establish that the proposed four-function carrier is semantically correct, scientifically sufficient, or institutionally useful without role-qualified review.
