# Artemis II: candidate corona-appearance rubric

Version 0.1, 11 October 2026. Private design proposal. **Unaccepted and not ready to score.**

This supplies a concrete response to the pilot's concept and reference questions. It does not assign labels to the 48 proposed captures, validate archive tags, or authorize image acquisition. Research text was reviewed; neither candidate pixels nor published reference figures were inspected for this proposal. Qualified solar/lunar-imaging review and a task-native image check remain necessary.

## The decision in one minute

The requested concept was visible solar-corona structure. The sources do not supply a validated image-only physical-origin oracle for these products. Accordingly, the proposed first task is narrower: **visible extended light adjacent to an apparent occulting limb, with its depicted morphology recorded separately from its physical interpretation.** Its provisional identifier is `A2-EL-APPEARANCE-01`.

This is an appearance diagnostic, not a solar-corona classifier. A reviewer may reject this proxy and require a context-assisted physical task instead. That would be a changed contract, not a quiet rename of the same labels.

| Decision | Proposed treatment |
| --- | --- |
| What can be recorded from the image? | Whether qualifying extended light is depicted, its region, and descriptive shape |
| What cannot follow from appearance alone? | Plasma origin, K/F-corona separation, lunar dust, dynamics, calibrated brightness, or a correct `Sunset` primary tag |
| What prevents a negative vote? | Missing field coverage, inadequate rendering or sensitivity, clipping, uncertain limb relationship, or unresolved artifact interference |
| What unlocks any scoring? | Qualified acceptance of the concept, viewing profile, references, and response rules, followed by authorized acquisition and a real image-use check |

The existing audit protocol remains controlling for sampling, blinding, estimation and acceptance. This candidate adds no probability sample, NASA requirement or executed scientific stage. Its delivered evidence and gates (local delivery copy not distributed; use the evidence map), empty supplementary form (local delivery copy not distributed; use the evidence map), and hypothetical decision cases (local delivery copy not distributed; use the evidence map) are review aids, not observations. Canonical counterparts remain in `target-label-audit/corona-rubric/`.

## 1. What the source check changed

1. **The plan is not a class label.** The native `Sunset` request asks for corona, possible horizon glow, and limb morphology. An observing objective does not prove that any requested feature appears in an individual image. [PDS target request](https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_outgoing_target_request.json), entry `target_name=Sunset`, order 24.
2. **The archive field is not the oracle.** The guide describes subset manual tagging and possible errors. It also describes window effects, absent color calibration, and interpreted processed TIFFs. Those limitations warrant carrier and artifact checks, not automatic rejection of every image. [Data User Guide](https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf), sections 3.1.2, 3.1.3, 5.2.4 and Table 17.
3. **A halo does not identify the planned plasma structures.** NASA's release, updated 8 April, explicitly retained uncertainty about halo origin. The later preliminary report separately discusses zodiacal light and observed coronal structures. These are different observations and levels of interpretation, not a universal halo-to-plasma conversion. [Release 26-029](https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/), eclipse captions; [preliminary report presentation](https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/), Chapter 4.
4. **One exposure does not establish completeness.** NASA's terrestrial eclipse guidance describes the corona's wide brightness range and exposure bracketing. This supports caution about nonvisibility; its numerical settings and Earth-view geometry are not Artemis-specific thresholds. [NASA/TP-2007-214149](https://eclipse.gsfc.nasa.gov/SEpubs/20080801/section3.html), section 3.3.
5. **Rendered RGB can support a bounded analysis when specifically qualified.** Tsumura and Arimatsu studied one Artemis II image using registration, stellar response checks, masking and restricted relative analysis. That is a counterexample to blanket image unusability, not a transferable calibration or reference label for our panel. Their F-corona terminology denotes inner zodiacal light, not automatically the plasma features in the plan. [Version 3, sections II.2, III and IV.3](https://arxiv.org/html/2604.13908v3); [journal DOI](https://doi.org/10.3847/2041-8213/ae71c8).

The exact local source identities, access dates and publication-status limits are in `contract.json`. The publisher's indexed record identifies ApJL 1004 L16 and publication on 9 June 2026. Direct publisher and Crossmark status access failed; correction/retraction status remains unknown. The inspected full text is arXiv v3, revised 21 May, not an attested byte-identical journal copy. No numerical result or calibration algorithm from that paper is adopted here.

## 2. Freeze the actual task before seeing candidates

Proposed unit: one `capture_identity` from the frozen 7,606-source-exposure complete-action cohort. Source, raw and processed products are representations of that capture, not independent observations. The first viewing carrier may be a qualified processed image or qualified preview. File existence, a TIFF extension and a large byte count do not establish adequacy.

The appearance question is: **Does this delivered view depict spatially extended light next to a locatable apparent occulting limb, with a describable shape distinguishable from an isolated point or merely a sharp bright edge?**

Proposed morphology descriptors are descriptive, not astrophysical identifications:

- diffuse halo or gradient;
- localized ray or fan;
- curved extension;
- multiple descriptors; or
- morphology unresolved.

A diffuse halo can qualify for this broad appearance task. It does not thereby qualify as a polar plume, helmet streamer, coronal loop, lofted dust or plasma corona. Those named physical subtypes are **not admitted** in version 0.1. A smooth appearance is not evidence that the corona is physically absent. Color may be described as displayed, never treated as calibrated or used alone to identify origin.

Do not use the original target, activity, camera, timestamp, plan window, filename or a crew description as the image-only vote. Other visible objects may coexist with the candidate appearance. A blank field is not a negative label; an Earth-, Moon- or other-tagged frame is not automatically out of scope.

## 3. Acceptance and viewing profile

All scoring is currently `NOT_READY_TO_SCORE`. An acceptance record must name the responsible qualified reviewer, version, date, conditions and evidence. the maintainer authorizes effects and continuation; neither the maintainer nor a local test substitutes for scientific qualification.

Before scoring, the reviewer must approve a versioned viewing profile specifying:

1. which carriers and renderers are usable, their lineage, dimensions, crop and display transforms;
2. allowed zoom and a retained full-frame view, so a cropped or off-frame region cannot disappear silently;
3. what counts as extended light at the approved scale, including borderline positive and artifact examples;
4. local adequacy for a positive vote, and separately the complete region and minimum feature class assessable for an absence vote;
5. how focus, motion blur, clipping, dark rendering, compression, demosaicing, window reflections and other artifacts are assessed;
6. whether any adjustment is allowed, its exact reproducible recipe and how the unadjusted view is retained; and
7. escalation, reference validity, independence and abstention rules.

No minimum pixel count, signal-to-noise threshold, intensity cut, solar-radius range or contrast adjustment is invented here. An adequate profile needs qualified examples and a real use check. For negative judgments, demonstrate that the specified minimum appearance can actually be recognized under that carrier/profile. A designed example or software injection can probe display recognition, but cannot establish physical coronal sensitivity unless its realism and end-to-end chain are separately qualified.

Keep artifact checks as questions until evidenced. Do not call a halo window scatter or a streak blooming merely because either explanation is plausible. Shared artifacts can persist across an exposure bracket, and raw/processed agreement is not independent instrumental corroboration.

## 4. Proposed response rules

These are **our candidate rules**, motivated by the sources, not a NASA-approved rubric. Apply them only after the release gates. Record a region and a reason; confidence is subjective and cannot override a failed gate.

| Judgment | Required premises | What it means |
| --- | --- | --- |
| `PRESENT` | Readable authorized view; locatable apparent limb and adjacent region; qualifying extended light; locally adequate depiction; no unresolved artifact that could explain the entire qualifying appearance | Appearance is depicted in that region. Physical origin remains a separate question. |
| `ABSENT` | No qualifying appearance; approved negative profile applied; the entire declared search region covered and adequately assessable; minimum appearance demonstrably recognizable; no unresolved artifact interference | The defined appearance is not depicted at the specified scale in this delivered view. Not physical absence, and not a whole-frame/whole-corona claim beyond the declared region. |
| `UNRESOLVED` | In-scope unit but a needed premise is missing, ambiguous or conflicting | Preserve the unit and the missing evidence. Do not discard it, substitute another image or count it as negative. |
| `OUT_OF_SCOPE` | Demonstrated failure of a declared unit/carrier eligibility rule, such as the wrong mission product | Not an image-content decision. Record the exclusion and keep it in the response inventory. Poor quality or an unexpected target is not itself an exclusion. |

Presence needs local adequacy; absence needs complete adequacy for the specified search. Thus a clear qualifying patch can support `PRESENT` even if another part is unreadable. An unreadable region prevents a full-region `ABSENT` vote. A tiny thumbnail with nothing obvious, a saturated limb, an off-frame expected region, or a caption without a usable image is `UNRESOLVED`, not absence.

Out-of-scope is available only under predeclared rules. If eligibility itself is uncertain, use `UNRESOLVED`. Do not use later context to edit a locked image-only decision. Keep the assisted result in a new row.

This draft is region-conditioned, not a complete all-frame label oracle. A frame without a locatable apparent limb remains `UNRESOLVED` under these rules. That is a conservative design choice, not evidence that clear off-target frames can never be labeled negative. A reviewer must decide whether this causes excessive abstention or whether a separately specified full-view structural-absence rule is justified. Do not silently switch between absence in a declared limb-adjacent region and absence of the pattern anywhere in an image.

## 5. Physical interpretation and references are a separate layer

Retain the appearance judgment and morphology, then record physical interpretation as `NOT_ASSESSED`, `UNRESOLVED`, or `REFERENCE_INTERPRETATION_RECORDED`. The last state must identify the named reference's claim and limitations; it is not a local certification of physical origin. There is no `VERIFIED_CORONA` state in this candidate.

| Evidence | Permitted contribution | Material limit |
| --- | --- | --- |
| Another reviewer of the same delivered view | Agreement, disagreement and interpretation consistency | Same-image consensus is not independent physical truth |
| Source/raw/processed alternatives of the same capture | Lineage or processing-artifact comparison, with a documented rendering | Shared detector, optics, window and scene remain |
| Adjacent captures or an exposure bracket | Assess persistence, settings and visibility under documented alignment | Not a second independent event; persistent artifacts are possible |
| Native labels, plan and exact crew report | Archive semantics, intended observation or reported human experience | Not an image-only content oracle; timing and report-to-image mapping may be unresolved |
| Same-image published analysis or NASA caption | Attributed scientific interpretation at its stated scope | Not an independent pixel source or a universal annotation oracle |
| A genuinely different instrument | Potential corroboration, if geometry, passband, time, resolution, masking and registration are commensurate | A different viewpoint can hide or change features; instrument independence alone is insufficient |

Do not place an Earth-view solar silhouette over an Artemis limb without validated registration. The Moon can occult a substantially different angular region from Orion. A general eclipse atlas teaches vocabulary but supplies no same-event location or detection threshold. A missing feature in a noncommensurate reference is not a refutation.

For artifact ambiguity, first ask for the smallest discriminating evidence already authorized and available. If it is unavailable, retain `UNRESOLVED`. Do not turn this rubric into a new geometry derivation, polarization study, pixel survey or acquisition request.

## 6. Blinding and record custody

This document is a **design/steward review packet**, not an already-blinded image-only reviewer kit. Public reference material may reveal mission context or studied images. Before giving training/reference examples to reviewers, screen exact captures and related actions against the proposed calibration and reserved confirmation units. One known public-image identifier was checked against the 48-unit crosswalk and was not present; that is a limited identity check, not comprehensive exposure-history or scene independence.

Freeze development examples and the accepted rubric before releasing reserved confirmation units. Do not retune on confirmation outcomes while still calling them confirmation. If they inform revision, retire that confirmation claim and explicitly designate a new, separately authorized set. Do not reroll convenient units or imply that 48 distinct actions create 48 independent physical events.

Use the existing reviewer form for the official audit fields. The supplementary empty form adds the viewing-profile identity, declared region, adequacy premises, artifact state, morphology and interpretation/dependence record. It contains no votes. Opaque IDs stay with reviewers; original fields and native URLs stay in the separate steward crosswalk. Record display hashes and transforms once an actual image bundle exists, not guessed source hashes as rendered-view identities.

After votes and reference interpretation lock, a steward may compare with original tags only under the existing protocol. Appearance `PRESENT` does not prove that `Sunset` should have been the primary target. Appearance `ABSENT` does not prove a `Sunset` tag wrong because that objective also includes limb and other observations. This proxy cannot backfill primary-target intent.

## 7. Hypothetical edge cases and what remains untested

`decision-cases.json` contains ten fully synthetic premise cases. They test the consistency of the proposed response rules, not astrophysics or image recognition:

1. unaccepted rubric remains not ready despite an apparently positive description;
2. a readable diffuse halo can be appearance-present while origin remains unresolved;
3. a local clear extension can be present without complete field coverage;
4. an unresolved plausible reflection blocks appearance acceptance;
5. a black thumbnail cannot support absence;
6. a cropped-away search region cannot support absence;
7. a completely assessable region with only a point-like glint can be appearance-absent under an accepted minimum-feature profile;
8. an original `Sunset` tag alone cannot support presence;
9. a demonstrably ineligible foreign product is out of scope; and
10. source/raw/processed agreement cannot turn appearance into verified physical origin.

Every example assumes its descriptive premises rather than establishing them from pixels. Passing local checks shows artifact consistency only. Reviewer competence, reference correctness, actual display recognition, artifact discrimination, agreement, time burden and use-specific error tolerance remain unmeasured.

## 8. Specific review request and stop rule

A qualified reviewer should return `ACCEPT WITH CONDITIONS`, `REVISE`, `NOT ASSESSABLE` or `OUT OF SCOPE` on each of these:

1. Is the appearance proxy useful, or must the task instead identify physical coronal features with context? State what decision the labels would serve.
2. Which depicted morphology and minimum assessable feature make the inclusion rule reproducible? Supply source-backed positives, exclusions and borderline cases, without relying on original archive fields.
3. What carrier, rendering, complete search region and recognition check can support negative judgments? Decide whether clear off-target frames need a separate structural-absence rule. If no negative profile is adequate, retain an unresolved-only negative channel or reject the task.
4. Which artifact and physical-origin distinctions can actually be resolved with available evidence? Name the independent evidence and its commensurability limits.
5. What reference/example overlap and reviewer training controls preserve the proposed two-phase diagnostic? Define acceptable disagreements and the abstention policy before confirmation.

If the task cannot be operationalized within qualified available evidence, retire the appearance candidate rather than manufacture specificity. Retain the metadata-completion findings and the archive-semantic review route. No physical insight, NASA acceptance or label-error rate is claimed by this candidate. The next live gate is qualified concept/reference review; independent narrative integration remains possible without it.
