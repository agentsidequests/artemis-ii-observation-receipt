# Stage 10Z adversarial framing screen — 10 October 2026

## Decision this screen can change

Which internal lead is strong enough to carry a later public analysis without turning an intentional scientific archive into a defect story. This is a framing and counterargument screen, not a public draft, novelty proof, or publication decision.

## Current public frame

- NASA calls the release “more than 800 gigabytes,” “more than 11,000 full-resolution images and video,” and a powerful dataset “ripe for exploration and analysis”: <https://www.nasa.gov/blogs/artemis/2026/10/07/nasa-releases-artemis-ii-lunar-science-data-images/>
- WIRED describes “nearly 1 TB,” stresses that users can work directly with raw scientific files and metadata, and points to future research rather than a prebuilt machine-learning benchmark: <https://www.wired.com/story/nasa-just-made-nearly-1-tb-of-artemis-ii-data-available-to-the-public/>
- The NASA PDS Data User Guide explains why the release contains deliberate sequences and multiple representations, why target tags cover only a manually selected subset, and why no calibrated crew-camera products are supplied. The exact guide text is preserved locally at `evidence/stage10d/source/artemis2_data_user_guide.txt`.

The public sources do not claim that files are independent samples, target tags are exhaustive labels, plan windows partition the archive, processed TIFFs are calibrated, or the release is an evaluation-ready benchmark. Any later analysis must target the downstream analytical temptation created by a large, accessible archive—not accuse NASA or PDS of making those claims.

## Candidate framing tournament

### 1. “NASA released duplicates” — reject

This is inaccurate and needlessly adversarial. Source NEFs, raw Bayer TIFFs, and processed TIFFs are intentional preservation and access representations. Bracket siblings and rapid sequences are intentional acquisition. The contribution is to preserve those relationships, not erase them.

### 2. “The archive is not benchmark-ready” — reject as a global claim

Stage 10X shows that readiness is task-conditioned. Retrieval accounting is ready now, bounded representation work is supportable with a claim limit, and within-event tasks may become supportable under a frozen protocol. Other tasks need audited labels, another event, camera-aware controls, or calibration. A binary global verdict loses that distinction.

### 3. “Random splitting will leak” — retain only as a prospective mechanism

The 89.111% action-group crossing result is a useful quantified warning, but no Artemis II image model or actual split was inspected. Competent practitioners may already group related records. The stronger contribution is the executable relationship layer that makes correct grouping possible and exposes why action grouping alone is not a universal event oracle.

### 4. “A terabyte is not a sample count; the analytical object is an observation graph” — strongest surviving frame

This frame survives the main counterarguments because it is both corrective and constructive:

- the fixed Sunset example makes the denominator collision memorable: `2,535 products → 845 exposures → 169 actions → 24 conditional bursts → 1 scheduled event`;
- the same block separates `200.901668231 GB` of current retrieval footprint from `17.257373901 GB` of source NEFs;
- the full action ledger shows that schedule membership is many-to-many and incomplete, not a flat `event_id` column;
- the label audit shows that target tags are selected navigation metadata, not an exhaustive event or class oracle;
- the camera canary and representation gate show why acquisition context and measurement level must remain explicit;
- the product relationship manifest and action↔plan ledger provide the missing graph rather than merely criticizing its absence.
- those two deterministic CSVs total 10,470,310 bytes—0.000644% of the 1.625-TB verified cohort footprint, about 155,228 times smaller—so the decision-bearing structure can be recovered before image-pixel access.

The graph has distinct, non-substitutable layers:

`archive product → exposure identity → camera action → conditional temporal run → action↔scheduled-window membership`

Camera, activity, target tag, transcript alignment, and representation are attributes or evidence layers—not interchangeable group identifiers.

## Hard counterarguments and dispositions

| Counterargument | Disposition |
| --- | --- |
| “A large archive can still be valuable even if one target has one event.” | Correct. Keep retrieval, within-event, representation, and qualitative research routes open. The one-event result constrains only new-Sunset-event generalization. |
| “NASA never promised an IID benchmark.” | Correct. Aim the warning at downstream reuse and the gap between storage scale and task-specific evidence, not at NASA. |
| “Grouped splitting is standard.” | Correct in principle. The local contribution is the exact Artemis II hierarchy, quantified collapse, overlapping schedule structure, and executable grouping artifacts. |
| “Target tags were not meant as exhaustive labels.” | Correct and explicitly documented. That is why the public point is a reuse guard, not a metadata-quality accusation. |
| “Processed images remain scientifically useful without calibration.” | Correct. They support human viewing and bounded image tasks; they do not by themselves support instrument-independent color or photometry. |
| “Actions outside plan windows are probably irrelevant leftovers.” | Rejected by the current metadata. The 626 unmatched actions span all seven flight days and 1,894 source exposures, including 249 `Earth Photos`, 210 `Opportunistic Imaging`, and 683 Earth-tagged exposures. Dropping them would remove 25.316% of cohort bytes. This still does not establish their scientific value or target correctness. |
| “Overlapping plan memberships are data errors.” | Rejected. The 58 multiply assigned actions are concentrated in concurrent Eclipsed Moon / Deep Space windows and window-team position swaps, consistent with parallel scheduled structure. This does not make every plan overlap semantically independent. |

## Decision impact

The strongest lead is now broader and more constructive than “one event masquerading as thousands of samples.” The core insight is:

> Public scale describes storage and access. Scientific and model-evaluation scale emerges only after the archive is reconstructed as an observation graph whose units, annotations, schedule memberships, cameras, and representations remain separate.

The Sunset event is the opening proof, not the whole thesis. The action↔plan ledger is the constructive payoff. The target-selection, camera, and calibration findings are secondary consequences showing why no generic deduplication or split can make every task valid.

## Claim ceiling

This screen does not establish global novelty, priority, publication merit, observed model leakage, model-performance inflation, target-label error, archive defect, or a new lunar-science result. Search absence remains `NOVELTY_UNESTABLISHED`. the maintainer retains public framing and publication acceptance.

## Recheck trigger

Re-run immediately before publication or when a public Artemis II camera benchmark, dataset card, training repository, split manifest, revised archive, verified target audit, authoritative event identifier, or calibration chain appears.
