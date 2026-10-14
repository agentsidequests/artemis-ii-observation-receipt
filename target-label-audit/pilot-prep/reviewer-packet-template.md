# Artemis II target-label pilot: concept review packet

Private preparation, 11 October 2026. Proposed candidates only. No images, content labels, probability sample or accepted benchmark accompany this packet.

## The decision to make first

Can a qualified reviewer define an image-level concept around the archive's `Sunset` term, or should this be a context-assisted task instead? Please review the six questions below before any image acquisition or scoring.

The native Lunar Targeting Plan's `Sunset` request asks for observations of solar-corona structure, possible glow beyond the horizon and lunar-limb appearance. It is an observing objective involving several possible phenomena, not an independently validated label for one visible object. That establishes the planning context, not what any candidate image shows or how the primary-target field was assigned. Predicting the recorded target field and recognizing visible content are different tasks. This is a protocol refinement, not a new lunar-science finding.

Source anchor: the preserved [NASA target-plan entry](https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_outgoing_target_request.json) with `target_name=Sunset`, `order=24`. Its parent file SHA-256 is `07dcfd09317764b4fb1436753eea42beafaad85fa0f307e43296553659e75754`. The [Data User Guide, Table 17](https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf) distinguishes primary from other targets and says only a subset was manually tagged, with possible errors. No image-level truth is inferred from those sources. These locators come from preserved source receipts, not a new live availability check.

## Six questions, with required dispositions

| Role | Question | A useful answer must specify |
| --- | --- | --- |
| Archive/metadata reviewer | 1. Does `Sunset` name a depicted phenomenon, an observing context, or a primary science objective? | The authoritative archive meaning, and whether predicting this field is a content-recognition task at all |
| Archive/metadata reviewer | 2. Can the cohort's primary-target fields be audited against native PDS labels, including other targets and representation lineage? | The controlling label fields, snapshot/version rule, and any differences across representations; no silent single-class conversion |
| Archive/metadata reviewer | 3. How should broad, unknown, discussion-related or overlapping target values be handled? | An accepted vocabulary map and out-of-scope/unknown rules, without treating unvalidated metadata as image truth |
| Lunar-imaging reviewer | 4. Which independently observable concept should this pilot test? | For example, a narrowly defined visible feature rather than the whole observing objective; precise inclusion and exclusion criteria, including multiple visible targets |
| Lunar-imaging reviewer | 5. What reference evidence can establish presence and, especially, absence? | Required image resolution, artifact discrimination, independent reference/registration evidence and any temporal context; same-image consensus alone is insufficient for correctness certification |
| Lunar-imaging reviewer | 6. Can a processed-image viewing carrier support that concept without a stronger physical measurement claim? | Acceptable rendering and escalation rules, an abstention policy, and whether image-only judgments must be distinguished from context-assisted judgments |

For each answer, record `ACCEPT WITH CONDITIONS`, `REVISE`, `NOT ASSESSABLE` or `OUT OF SCOPE`, with a source locator and the remaining dependency. A reply is not approval of population inference or of operational NASA guidance. Statistical design and use-specific error tolerances remain separate later gates.

## What is prepared, and what is not

There are {{PROPOSAL_COUNT}} proposed exposure identities from {{ACTION_COUNT}} distinct reconstructed complete camera actions. These are not established independent scenes or events. Only {{QUEUE_COUNT}} calibration IDs appear in the reviewer queue. A further {{RESERVED_COUNT}} confirmation proposal is reserved privately for use after the rubric is frozen. That reserve is an administrative hold, not an encrypted seal or a validated test set.

The panels were chosen purposefully from metadata. They cannot estimate archive-wide content prevalence, tag accuracy or model performance. No candidate is called positive, negative, difficult, non-lunar or otherwise content-verified. The selection policy seeks coverage; it does not supply answers.

The reviewer queue contains opaque IDs and pending states only. There is no ready-to-score blinded image bundle yet. Do not start scoring from the queue alone. No reviewer has been assigned or qualified by this preparation.

## Exact file-size accounting, not a download plan

{{COST_TABLE}}

Values are recorded native-product sizes in the frozen metadata snapshot, not observed transfer totals or current server checks. Decimal GB means 1,000,000,000 bytes. Source, raw and processed columns are alternative representations of the same captures, not independent observations. Downloading all three adds storage burden without adding capture identities. XML labels, independent reference material, rendered copies and caches are additional costs not included here.

The current authorized pixel budget is **zero**. A possible later preview-first pass could use a **64 MiB hard ceiling**, but that is only a proposal. The selected browse files' existence, sizes and suitability have not been checked. The source crosswalk supplies native-product paths; it does not claim that a small browse representation exists for each candidate.

Before a later download, accept the concept/rubric, choose the viewing representation, inventory selected labels or headers under a new explicit budget, and obtain authority for the bounded pixel pass. If preview size or resolution is inadequate, stop and request a specific escalation rather than downloading the full panel automatically. Do not call a small or inaccessible preview a content negative.

## Roles and blinding

The separate file named `Artemis-II-Target-Label-Pilot-Steward-Crosswalk-DO-NOT-SHARE-2026-10-11.csv` contains original tags, selection reasons, camera/activity information and native product links. It is for the steward, not for reviewers before their reference judgments are locked. Do not send the whole private source folder or repository as a blinded review package.

Opaque IDs and separate files provide workflow separation, not access-control enforcement or anonymity against someone who already knows the archive. The future steward must hide labels, metadata, original filenames and embedded comments from the actual displayed images. Rendering, masking, source hashing and reviewer independence are still unverified.

Use the previously delivered empty reviewer and adjudication forms only after the rubric, people and displayed-image versions are established. Preserve each initial vote and any later context-assisted vote. Unresolved and benchmark-ineligible cases remain visible; they must not become generic negative training labels.

## Human burden and stopping rule

Two initial image-only reviewers of all 48 proposed units would make **96 initial per-concept reviews**, before registration, reference lookup, agreement rechecks or adjudication. A separate context-assisted pass adds work. Review time has not been measured, so no hours-to-completion or low-cost claim is made. Measure it on a small accepted calibration subset before releasing the reserve or authorizing a main audit.

Stop if the term cannot support the chosen content task, the available viewing carrier cannot support the rubric, adequate reference evidence is absent, reviewers are unavailable, or the complete cost is disproportionate. Narrow the task or report the limit. More labels cannot create a second Sunset event or turn this mixed-purpose cohort into a universal benchmark.

No contact, publication, remote push, image acquisition or annotation has occurred. The next decision is the concept/reference gate, not a bulk-download decision.
