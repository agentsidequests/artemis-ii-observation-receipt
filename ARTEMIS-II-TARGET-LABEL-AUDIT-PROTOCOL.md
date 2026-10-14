# Artemis II: a task-specific target-label audit

Private review candidate, 11 October 2026. Version 1.1.

## Recommendation and present status

Before training a target-recognition model, establish whether a declared target concept can be identified from the images, then audit both existing tags and blanks with a probability sample. Do not backfill the archive by guessing from the schedule. Do not mistake agreement between two reviewers for ground truth.

This document designs that audit. No probability audit has been drawn or executed, no images have been labeled, no new pixels have been acquired for this protocol, and no audit accuracy, content prevalence or model performance has been measured. A separate metadata-only feasibility packet now proposes candidate capture IDs; that is not an executed content audit. The source-frame census and planning arithmetic are locally checked. The concept definitions, image-level reference evidence and qualified acceptance are still pending. This is not a NASA requirement or an accepted benchmark.

The first practical output should be a small reviewer-calibration packet, not hundreds of inferred labels. Proceed to statistical estimation only if that packet demonstrates a usable response protocol.

## 1. What decision this audit answers

**Practical objective:** decide whether a bounded, explicitly defined crew-camera target-recognition task can support defensible evaluation, and which label work is actually needed.

Keep four jobs separate:

| Job | Observable output | What it does not establish |
| --- | --- | --- |
| Task feasibility | Which concepts can be judged at the declared image and context level | Accuracy of all archive tags |
| Label-quality estimation | Design-weighted support, contradiction, unresolved and out-of-scope rates for recorded tags; labelability of blanks | Individual certification of unreviewed records |
| Record completion | A versioned decision for each actually reviewed field | Statistical precision by itself, or the mission team's intended primary target |
| Model evaluation | Performance on a separately frozen, qualified reference set and task-native split | New-event generalization from repeated views of one event |

NASA's Data User Guide Table 17 defines a primary target as the main science target captured in the image, distinguishes other targets, and warns that only a subset was tagged and that errors may remain. Consequently, visible-target recognition is not identical to recreating the mission team's primary-target choice. [NASA PDS Data User Guide](https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf).

## 2. Freeze the task before looking for results

Use a **visible-content recognition task**, with one or more independently scorable concepts, rather than forcing every image into one of the 23 observed metadata strings. Multiple concepts can be present. An empty visible-target set is permissible only after adequate inspection under the accepted rubric. An unresolved concept is not absent.

Start the feasibility pilot with **one concept**. `Sunset` is a candidate because it connects to the existing denominator analysis, not because its image-level meaning has already been validated. A qualified lunar-imaging reviewer must first determine whether that archive term admits a reliable single-image recognition rule. A dark Moon, a lunar terminator, or a scheduled Sunset interval must not become an automatic positive. If the concept needs temporal or geometric evidence, freeze a separate context-assisted task; do not silently call it image-only recognition. If this candidate fails, preserve that result and define a different concept prospectively before its pilot.

The native target-plan entry for `Sunset` (`target_name=Sunset`, `order=24`) asks for solar-corona structure, possible horizon glow and lunar-limb appearance. This source-backed planning meaning is broader than one automatically scorable visible object. Define the desired image-level concept explicitly; do not treat the observing objective, an exact sunset boundary or any requested phenomenon as verified image content. The plan's observation request does not establish that dust or glow was detected.

For each admitted concept, the task owner and qualified reviewer must sign off a rubric containing:

- exact concept ID, archive vocabulary correspondence and operational definition;
- inclusion, exclusion and borderline rules, including multiple visible targets;
- minimum evidence for `PRESENT` and for `ABSENT`;
- image eligibility, resolution/viewing requirements and representation choice;
- permitted independent reference material, coordinate/registration requirements and temporal context;
- the difference between visible support, semantic correctness of a primary tag and crew intent;
- allowed abstentions and the cost of false positives, false negatives and unscorable cases;
- the intended prediction environment and whether the task is image-only or context-assisted.

**Stop gate:** without this rubric, produce a feasibility or semantic-ambiguity report only. Do not calculate a target-label error rate. A metadata value, plan name or transcript mention is not an image-level oracle.

## 3. Population, unit and source custody

The initial audit frame is the frozen **complete-action cohort**, not the whole Artemis II archive:

- 7,606 source-exposure identities in 2,166 reconstructed complete camera actions;
- 3,413 exposures with a nonblank primary target field;
- 4,193 exposures with a blank field;
- three archive representations per exposure, totaling 22,818 products.

One exposure is one audit unit. A source, raw and processed product of the same capture must never become three independently sampled observations. Keep action, camera, activity and many-to-many planned-window relationships for diagnostics and later split design. None supplies a validated physical-event identity.

Frame owner: `results/stage10o-product-relationship-manifest.csv`, 10,072,026 bytes, SHA-256 `8edd58437cc609229edb5abb41c4e00048bb420354f1ac17a269da92c17e4729`. Select exactly `collection_id == data_source`; use `capture_identity` as the deduplication key. For this snapshot, nonblank means a nonempty stripped field. Preserve original field bytes separately. Recompute counts and unique keys before a draw; a changed snapshot requires a new frame and version, not replacement of old evidence.

The steward must retain a private unit crosswalk with exposure ID, source product ID, action, camera, activity, original target field, tag-presence stratum, representation product IDs, image hashes and source URLs. Secondary targets must be recovered from the native PDS labels if needed; the flattened primary-target manifest does not contain a complete secondary-target oracle. Preserve spelling aliases through an explicit vocabulary map, not an undocumented cleanup.

Eligibility is assessed from content under the rubric. Do not drop untagged, difficult, non-lunar, inaccessible or ambiguous images to make the audit look cleaner. Record their status. A curated subpopulation can be formed later under an explicit rule, but its counts and scope must be reported separately.

## 4. Two distinct stages, with a real stop between them

### A. Response-protocol calibration: at most 48 exposures

Prepare at most **24 deliberate calibration exposures**, targeting 12 tagged and 12 blank units, spread across cameras and zero/partial/complete tag-coverage activities where feasible. Include difficult views, possible multiple targets and apparently non-lunar views. Use metadata only to seek coverage and difficulty, not to supply the label. This is a purposeful diagnostic panel and **cannot estimate population rates**.

Two role-qualified reviewers independently annotate the accepted concept on opaque-ID images using the form below. After their first decisions are locked, compare their reasoning, revise the rubric if necessary and record every revision. Then test the frozen rubric on up to **24 distinct confirmation exposures**, again aiming for 12 in each tag-presence group and using actions not used in calibration where feasible. Never cherry-pick confirmation images after seeing their outcomes. If the frame cannot supply the declared panel, document the shortfall before labeling.

The 24 + 24 cap is an operational scope choice, not a statistical sample size or reliability guarantee. These exposures are development material, not a held-out model test set. Keep them outside any proposed sealed test set at the chosen grouping layer.

Advance only when:

1. Every displayed image is source-bound, and both reviewers' initial decisions were made without the original tags or each other's answers.
2. The rubric version, permitted reference evidence and unscorable rules are frozen.
3. Every disagreement or unknown in confirmation has a recorded disposition, not necessarily a forced consensus.
4. A qualified reviewer accepts what the protocol can distinguish, and an independent reference basis exists for any claim of semantic label correctness. If only same-image judgments are available, narrow the result to reproducibility and visual support.
5. Measured review time, unresolved frequency and reference-access burden make the main audit worthwhile. If not, stop or narrow the task prospectively.

This stage does not claim all 23 metadata concepts are recognizable. Adding a concept requires a new rubric and feasibility check.

### B. Probability audit: only after Stage A is accepted

Use two exhaustive, disjoint strata: recorded-tag and blank-tag. Within each, draw a simple random sample of exposure identities without replacement. Freeze sample sizes, primary outcomes, precision criteria, exclusions, reference protocol and analysis before opening the selected images. Every frame exposure must have a known nonzero inclusion probability in its stratum.

Implementation specification for a later sampler:

- Sort each stratum by exact capture ID; freeze its hash and counts.
- Draw and record a random seed after the plan is frozen; record the generator, runtime/version and algorithm. Use unbiased random selection without replacement, not the first files or nearest timestamps.
- Save the complete selected-ID list, stratum sizes, inclusion probability `n_h/N_h` and weight `N_h/n_h` before annotation. Do not reroll because the images look inconvenient.
- Permit selected units from the same action. A one-per-action cap, action-first sampling or camera quota changes the design and requires new inclusion probabilities and variance rules.
- Preserve selected inaccessible units and unknowns. Do not substitute an easy neighbor. Additional difficulty or rare-target panels must be marked supplemental and must not enter population estimates as though randomly selected.
- Do not merge purposeful pilot outcomes into this audit without a separately specified design. The simpler default is to draw from the full frozen frame and re-review any pilot overlaps under the locked protocol; report the overlap and familiarity risk. Assign fresh reviewers who have not seen those units' labels for overlap cases, or mark the blinding/reference gate unverified. Do not replace a randomly drawn overlap with an easier new unit.

For illustration only, a conventional finite-population, normal-approximation planning formula is:

`n_h = ceil[N_h z^2 p(1-p) / {e^2(N_h-1) + z^2 p(1-p)}]`.

With `z=1.96`, `p=0.5`, and `e=0.05`, it gives **346 tagged and 352 blank exposures**, or 698 unique exposures before considering overlap with development material. This plans approximately 95% marginal precision for one binary outcome in each stratum under a complete-response, adequate-reference design. It is not a guaranteed interval width, a simultaneous multiclass guarantee, a rare-class guarantee, a measured label error rate or an approved sample allocation. It would require 1,396 initial image reviews for one concept, plus references and adjudication. More concepts multiply judgment burden. Final sizes and interval methods require statistical review and an accepted cost/precision target. Do not use the Stage 11V budgets of 3,433/3,813/4,117 as sample sizes: they answer deterministic completion-width questions instead.

Do not repeatedly inspect results and extend or stop the sample until a preferred confidence interval appears. A sequential design requires its own predeclared stopping and inference rule.

## 5. Viewing and independent annotation procedure

The steward creates opaque review IDs and hides metadata labels, activity names, planned windows, camera identifiers, descriptive filenames, embedded comments and prior model predictions. Keep a separate restricted crosswalk. Visual camera cues may remain in pixels; blinding cannot promise their elimination.

For visual recognition, a frozen processed-image rendering can be a practical viewing carrier, but it is an uncalibrated interpretation, not a color or photometric measurement. Record native product/hash, decoder, resize/crop policy, color/display settings and actual displayed dimensions. Both reviewers see the same version. If a downsample prevents identification, escalate under a predeclared full-resolution rule and log that change. Do not call an undersized preview a negative.

1. **Image-only pass:** each reviewer independently records `PRESENT`, `ABSENT`, `UNRESOLVED` or `OUT_OF_SCOPE` for each accepted concept, with a region or evidence locator and a reason. Record access failures as `UNRESOLVED` with an access-failure code.
2. **Context-assisted pass, if part of the frozen task:** retain the first vote and add a separate vote using approved, source-bound independent reference evidence. Register features against an atlas or geometry where the rubric requires it. Record any sibling frames, transcript or timing context. The original target tag stays hidden. A schedule can aid navigation but cannot verify presence.
3. **Lock both reviewers' votes:** no copying, model-assisted suggestion or exposure to the other's vote before locking. Agents may handle bookkeeping, not substitute unqualified semantic acceptance.
4. **Adjudication:** a qualified adjudicator reviews disagreement, inadequate evidence and ambiguous cases. Retain all original votes, added evidence, reasoning and `UNRESOLVED` decisions. Review a predeclared random portion of agreements too; unanimous reviewers can share an error. No fixed recheck percentage is claimed optimal here; freeze its selection and cost at the Stage A gate.
5. **Unblind the archive fields only after reference decisions are locked.** Compare the primary and, when available, secondary tags with the accepted visible-content judgment and archive semantics.

Tag-comparison categories are `SUPPORTED_VISIBLE`, `CONTRADICTED_BY_REFERENCE`, `UNRESOLVED`, `OUT_OF_SCOPE` and `NOT_APPLICABLE_BLANK`. Use contradiction only with adequate negative evidence and accepted archive-term semantics. A different visually dominant target, a visible secondary target or a mismatch to a newly invented single-label rule is not proof that the original primary tag is wrong. Image-supported content alone cannot recover crew intent. Archive terminology disputes remain semantic questions, not automatically annotation errors.

A one-concept pilot cannot evaluate tags naming other concepts. Mark those tag comparisons `OUT_OF_SCOPE`; do not call them wrong or claim an overall archive-tag accuracy. A later support/error estimate for tags mapped to an accepted concept is a domain estimate with its own denominator and uncertainty. The 346/352 example targets a binary stratum-wide outcome such as accepted-concept labelability, not precision inside a sparse target-specific domain. Broader tag-quality claims require broader qualified reference coverage.

Agreement, repeatability and confidence are diagnostics, not independent measures of truth. Report raw agreement, disagreements by concept and stratum, unresolved status, adjudication changes and reference limitations. Do not use one high agreement score to certify all labels.

## 6. Estimation, ambiguity and dependence

For a fully observed binary audit outcome `Y`, report the stratified estimator:

`P_hat = sum_h (N_h/N) mean_h(Y)`.

Under independent simple random draws without replacement in the two strata, the design variance estimator is:

`V_hat = sum_h (N_h/N)^2 (1-n_h/N_h) s_h^2/n_h`.

Use at least two sampled units in each non-census stratum for this variance estimator. A census stratum has zero sampling variance, but can still have annotation error. The estimator covers the frozen exposure population and that specific audit outcome, not an unseen-event population. Approximate intervals require explicit adequacy checks; sparse outcomes or extreme rates need an appropriate finite-population or other justified interval method. Freeze the method before estimation. Zero observed contradictions is not proof of zero errors.

**Synthetic weight check:** if two equally sampled strata contain 1 and 9 frame units, and their sampled binary outcomes are 1 and 0, the population estimate is 10%, not the unweighted sample's 50%. This is a toy accounting example, not Artemis data.

For content uncertainty, use two observable indicators for each concept: definite support `L=1` only for an accepted `PRESENT`; possible support `U=1` for every status except an accepted `ABSENT`. Thus both `UNRESOLVED` and `OUT_OF_SCOPE` remain possible positives in a full-frame content estimate. A benchmark-ineligible view is not automatically a content negative. Report those statuses separately. These indicators yield separate weighted estimates of lower and upper adjudication-support endpoints. They are **not deterministic bounds on all unreviewed images**. Sampling uncertainty must be attached to both endpoints before making a population interval, with familywise control if joint coverage is claimed. Annotation/reference error is a further uncertainty layer and is not removed by those sampling intervals.

Do not drop unknown cases and report only the easiest labels. For a fraction among eligible views, declare the eligibility denominator and use a design-consistent ratio estimator and variance method. If eligibility itself remains unresolved, report that uncertainty; do not manufacture a precise conditional prevalence.

Related action exposures do not automatically invalidate a design-based estimate for a fixed finite exposure frame: the randomness here is the declared sample draw, not independent lunar events. However, an action-cluster sample needs cluster-aware probabilities and variance, and an unseen-action or unseen-event model claim needs a separate sampling/split and dependence contract. A generic design-effect multiplier does not resolve these distinctions. [Census D1](https://www.census.gov/about/policies/quality/standards/standardd1.html).

## 7. Acceptance and the model-evaluation handoff

There is no universal acceptable annotation-error rate. Set the allowed error, ambiguity and coverage budgets from the proposed model's use and failure costs before the main audit. A feasibility pass is not benchmark certification.

| Gate | Required evidence | Failure disposition |
| --- | --- | --- |
| Source and frame | Exact snapshot, unique captures, correct strata, source-bound displayed images | Stop draw or quarantine affected units; preserve old frame |
| Semantics | Qualified rubric and primary/secondary distinction | Report semantic uncertainty; no label-error claim |
| Reference validity | Task-native independent evidence adequate for the accepted correctness claim | Narrow to visual support or repeatability |
| Reviewer operation | Locked independent votes, disagreement custody and agreement rechecks | Repair procedure prospectively; retain affected decisions |
| Estimation | Known inclusion probabilities, justified weights and variance, unknowns retained | Report descriptive panel only |
| Decision fitness | Predeclared use-specific tolerances and accepted uncertainty | Do not call labels evaluation-ready |
| Generalization | Exact deployment horizon, admissible group/event IDs and enough distinct units on both sides | Narrow evaluation or obtain genuinely new evidence |

An accepted audit still does not license random product splits. Group exact captures and representations; retain complete-action relationships. Stronger camera, time and event isolation depends on the deployment question. Activity tags and planned windows are not automatic realized-event truth.

The current Sunset opportunity has one scheduled event. Auditing or relabeling more views cannot create a second Sunset event. Within-event recognition can be a bounded task, but must not be described as new-Sunset-event validation. Report a camera-only baseline and a label-availability baseline on the same qualified evaluation population, alongside a simple majority or other task-appropriate baseline. If those metadata would not be available at deployment, label the corresponding baseline diagnostic rather than deployable. Do not reuse the old selected-tag canary scores as scores on new reference labels. If multi-label concepts are admitted, use concept-specific metrics and abstention/coverage reporting rather than forcing a multiclass accuracy score.

Keep calibration, rubric development, model tuning and sealed evaluation distinct. Freeze and hash the reference labels, group assignments and evaluation protocol before model comparison. Independence from training data, reference adequacy and population representation are separate gates.

## 8. Forms, evidence receipt and burden

Two empty UTF-8 CSV forms accompany this protocol:

- `target-label-audit/reviewer-form.csv`: one row per exposure, concept, reviewer and pass. Use `IMAGE_ONLY` or `CONTEXT_ASSISTED`; append the latter rather than replacing the former. Status and fields are defined in `target-label-audit/contract.json`.
- `target-label-audit/adjudication-form.csv`: one row per exposure/concept and task pass after vote locking. Preserve both reviewers' votes from that pass, the final decision, reference locator and unblinded tag-comparison category. Multiple disagreements or passes do not create new exposure units.

Populate opaque audit IDs through the steward crosswalk, not by typing original IDs into a blinded form. Reviewer confidence uses `HIGH`, `MEDIUM` or `LOW`, is subjective, and never fills a missing decision. Region/evidence locators must make the judgment reviewable. The forms are templates with **zero observations**; their existence does not mean an audit occurred.

The later audit receipt must bind frame and rubric hashes, source/render hashes, vocabulary mappings, random selection algorithm/seed, selected IDs and probabilities, exclusions/access failures, pilot overlaps, reviewer qualification and masking, original and final votes, reference evidence, unblinding order, analysis code/version, all denominators, uncertainty and acceptance disposition. Store new labels in a derived versioned layer. Never overwrite NASA/PDS source labels.

Measure review time during calibration, including viewing, reference registration, reconciliation and recovery. Estimate total burden using per-concept review time, two initial reviewers, planned agreement rechecks and adjudication, plus byte and display costs. Do not promise a 698-image audit is cheap merely because its count is lower than a completion census. Pause before new acquisition if representation sizes exceed the authorized byte budget. Qualified reviewer availability is a dependency, not an assumed resource.

## 9. Hard negatives and recovery

Reject these apparent shortcuts:

- blank field becomes negative; scheduled name becomes content truth; camera predicts presence so fills target;
- source/raw/processed triples become three observations; a one-per-action quota is analyzed as exposure SRS;
- primary/secondary differences become tag errors; uncertain or inaccessible views disappear;
- same-frame reviewer consensus becomes independent truth; a model supplies its own reference labels;
- a purposeful pilot produces a population rate; a balanced sample is summarized without design weights;
- zero observed errors becomes perfect accuracy; optional stopping uses fixed-sample intervals;
- field-completion bounds become physical prevalence; more views become more physical events;
- a protocol/template or passing software checks are reported as an executed, expert-accepted audit.

After a hash mismatch, ambiguity or failed review gate, preserve the prior artifact and the failure disposition. Change the task, rubric or frame only through a new version. Do not retroactively adjust the accepted definition to make observed tags correct or incorrect. No outreach, publication, remote creation, push, bulk download, model training or new timed tranche is authorized by this design.

## 10. What the source check changed

This is a project-local method proposal, not a new general standard.

- NASA's guide controls archive meanings and motivates auditing existing tags as well as blanks. Its secondary-target distinction rules out a naive forced single-class correctness audit.
- [Census A3](https://www.census.gov/about/policies/quality/standards/standarda3.html), last revised 8 October 2021 and checked 11 October 2026 local time, connects population, frame, design, precision and verification. It informs the separation of a purposeful feasibility panel from probability-based estimation; it is not a NASA rule.
- [Census D1](https://www.census.gov/about/policies/quality/standards/standardd1.html), same revision/access dates, motivates matching weights and variance to the actual design, keeping inference separate from code validation.
- [Stehman and Wickham, 2020](https://link.springer.com/article/10.1007/s10980-020-01029-1), version of record 28 May 2020, supplies a remote-sensing precedent for connecting sampling, response and analysis and reporting class-specific uncertainty. Its [author manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC7970508/) recommends blinded reference assignment and interpreter consistency checks. This informs locked independent votes and the feasibility pilot, not lunar competence or an area-weighted lunar estimator. Publisher metadata was accessible; the manuscript was available through indexed primary text, while direct access presented a browser challenge. Correction/supersession status was not independently certified.
- [NIST sample-size guidance](https://itl.nist.gov/div898/handbook/ppc/section3/ppc333.htm) motivates declaring proportion, confidence and precision assumptions. The finite-population adjustment and 346/352 values above are this protocol's checked planning derivation, not a NIST-prescribed Artemis sample.

The central limit is still reference validity: reproducible sampling and agreement cannot turn an ambiguous target definition into truth. The next useful action is to prepare the metadata-only feasibility packet and explicit concept-definition questions, without acquiring or labeling images or contacting anyone.

## Delivered copies

The working paths above identify canonical private sources. The directly usable copies are [this protocol](ARTEMIS-II-TARGET-LABEL-AUDIT-PROTOCOL.md), [the empty reviewer form](target-label-audit/reviewer-form.csv) and [the empty adjudication form](target-label-audit/adjudication-form.csv). The JSON contract and automated checks are internal source material; the protocol defines the form's permitted decisions, passes and confidence values. No filled observations accompany these templates.
