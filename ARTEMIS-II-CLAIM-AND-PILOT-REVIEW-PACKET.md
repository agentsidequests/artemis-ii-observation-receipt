# Artemis II article claim and pilot review packet

Date: October 10, 2026

Status: Detailed archive-design appendix. The current two-gate review entry is `ARTEMIS-II-TWO-GATE-SPECIALIST-REVIEW-PACKET.md`. Neither artifact is PDS-certified, OGC-conformant, or specialist-approved.

## Purpose

This packet lets a planetary-data, PDS4, or machine-learning evaluation specialist review the article without reconstructing its argument from scratch. It separates what the evidence establishes, what the article infers, what it expressly does not claim, and the exact NASA-facing pilot being recommended.

The requested review decision is narrow:

> Is the proposed companion relationship layer technically useful, compatible in principle with current PDS practice, and described without overstating either the Artemis II evidence or a gap in PDS?

## Evidence boundary

The quantitative analysis uses public Artemis II PDS metadata, the lunar targeting plan, and crew transcripts from a dated archive snapshot analyzed on October 10, 2026. The principal archive-structure results did not inspect image pixels. They did not train a model or inspect an existing model split.

The article does not claim:

- observed train/test leakage or a measured performance effect;
- image duplication, image similarity, or independent semantic scenes;
- a defect in NASA’s archive;
- correctness of manually assigned target tags;
- calibrated color or photometry;
- global novelty, scientific priority, or a lunar-science discovery; or
- that no mission, node, or research workflow has encoded equivalent relationships elsewhere.

It also does not claim that the proposed task profile implements or conforms to TrainingDML-AI. The current mapping is conceptual until a qualified reviewer selects an encoding and verifies it.

## Consequential claim map

| Public claim | Direct basis | Defensible ceiling |
| --- | --- | --- |
| NASA released more than 800 GB, more than 11,000 full-resolution images and videos, and 8.5 hours of audio | [NASA release announcement](https://www.nasa.gov/blogs/artemis/2026/10/07/nasa-releases-artemis-ii-lunar-science-data-images/) | Release-scale description only. It is not the denominator used for the cohort calculations. |
| The fixed Sunset plan block contains 2,535 products, 845 exposures, and 169 reconstructed five-exposure camera actions | Public PDS metadata joined to the independent eight-minute plan window; local receipt `results/stage10s-result.md` | Exact for the verified complete-action cohort and snapshot. It does not prove every product contains Sunset imagery. |
| A conservative connected Sunset context contains 4,290 products, 1,430 exposures, and 286 actions while the scheduled-event count remains one | Plan window plus transcript-bracketed adjacent context; `results/stage11d-result.md` | The interval is a connected-context canary, not a complete realized-event boundary or a content-verified image cohort. |
| The complete-action cohort contains 22,818 products, 7,606 exposure identities, and 2,166 reconstructed actions | Deterministic metadata reconstruction; `results/stage10l-result.md` | Exact within the six admitted bracket patterns and dated cohort, not the whole archive or every camera action. |
| The connected context is 13.204% of actions, 18.801% of products, and 22.785% of bytes | Same cohort and context; `results/stage11e-result.md` | Proves unit-dependent weight under hypothetical uniform weighting. It does not prove that an actual model used product or byte weighting. |
| Thirty-eight of 621 strict action/product window orderings reverse; 59 action/byte orderings reverse | Complete active-window comparison; `results/stage11g-result.md` and `results/stage11k-result.md` | Archive prominence changes with unit. Scientific importance is not ranked. |
| All 38 product reversals cross unequal products-per-action rates, while none of 222 equal-rate pairs reverses | Exact factorization; `results/stage11j-result.md` | Arithmetic attribution inside this cohort. It is not a causal model-performance result. |
| An independent 80/20 product split crosses an expected 89.111% of action groups; exposure splitting crosses 52.911% | Closed-form Bernoulli model over 1,612 nine-product and 554 fifteen-product action groups; `results/stage10m-result.md` | Expected hazard under a stated hypothetical split, not observed leakage. Action grouping protects only the measured siblings. |
| In one deterministic 80/20 canary, product-key hashing crosses 1,937 of 2,166 actions; action-key hashing crosses zero actions but 157 of 816 conditional five-second groups; five-second-group hashing crosses neither declared layer | Content-hashed relationship manifest, frozen algorithm and seed, complete assignment artifact, and two implementation paths; `results/stage11l-result.md` and `results/stage11m-result.md` | Executable validation of declared relationship preservation only. The second path remains partial implementation diversity, not independent human replication, a scientific task split, a semantic-scene rule, or evidence about a real pipeline. |
| Two local relationship ledgers total 10,470,310 bytes, 0.000644% of the 1.625-TB cohort | Exact uncompressed CSV sizes and cohort bytes; `results/stage10o-result.md` and `results/stage10z-result.md` | Illustrates storage leverage only. It excludes design, curation, review, migration, and maintenance cost. |
| The archive has six different task-readiness states across four blocker families | Integrated task map; `results/stage10x-result.md` | A task-specific decision aid, not a global readiness score. |

## Current PDS practice and the precise seam

The recommendation must begin from what PDS already does:

- PDS4 gives products stable LIDs and LIDVIDs, bundle and collection structure, validated labels, reference lists, and source-product relationships. See the [PDS4 Data Provider’s Handbook 1.26.0.0](https://pds.nasa.gov/data/pds4/documents/document_pds4_standards/1.26.0.0/PDS4_DPH_1.26.0.pdf).
- A PDS collection inventory enumerates member products by LID or LIDVID. See the current [Product_Collection](https://pds.nasa.gov/datastandards/documents/dd/v1/PDS4_PDS_DD_1O00/webhelp/all/ch02s04.html) and [Inventory](https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1J00/webhelp/all/ch03s70.html) definitions.
- `Product_Metadata_Supplemental` can provide added metadata for products in one collection, but its table fields must already be attributes in a PDS common, discipline, or mission dictionary. See [File_Area_Metadata](https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1J00/webhelp/all/ch03s52.html).
- `Table_Delimited_Source_Product_Internal` lists products used as inputs to create another product. Its source-product semantics are narrower than arbitrary analytical grouping. See the [current class definition](https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1J00/webhelp/all/ch03s111.html).
- The released Machine Learning Analysis LDD is designed to describe products generated by ML methods. The inspected `Data_Set` class records dataset version, count, augmentation, and preprocessing. The inspected class has no member list, task-native parent-group key, or split-integrity receipt. See the [PDS4 1.25 dictionary listing](https://pds.nasa.gov/datastandards/dictionaries/index-1.25.0.0.shtml), [released JSON](https://pds.nasa.gov/pds4/ml/v1/PDS4_ML_1P00_1211.JSON), and [user guide](https://pds-data-dictionaries.github.io/ldd-ml/user/user-guide.html).

The resulting claim is not “PDS lacks membership or provenance.” It is:

> The inspected ML dataset description does not itself expose the product-level membership, task-native parent groups, and split-integrity evidence needed to audit this evaluation boundary. Existing PDS mechanisms may supply parts of the solution, and mission-specific equivalents may exist outside the inspected sources.

## OGC and implemented-practice crosswalk

The [OGC TrainingDML-AI standard](https://www.ogc.org/standards/trainingdml-ai/) materially narrows the proposed seam. Its conceptual model includes individual sample identity, dataset membership, `trainingType` values for training, validation, test, and retraining, tasks, source citations, labels, labeling provenance, quality, and dataset changes. The revised conceptual model also discusses hashes and signatures as integrity strategies and provides an extension route. The proposal should reuse or align with those concepts rather than invent parallel names.

Two planetary implementations further constrain the recommendation:

- [SomBench](https://arxiv.org/abs/2609.13277), a current NASA and IBM lunar benchmark, assigns whole map zones to one split, keeps assignments consistent across its two resolution tracks, materializes each tile’s role in a `DATASET` catalog field, and drops zone-straddling tiles to preserve spatial separation.
- [MCTED](https://arxiv.org/abs/2509.08027) recursively clusters intersecting Mars stereo-footprint unions and assigns every patch in a cluster to the same split.

These are strong positive precedents. The surviving Artemis II seam is not a general failure to understand leakage or publish split membership. It is the need to declare task-native, sometimes non-spatial parent relations such as representations, exposures, bracket actions, temporal runs, and realized observing episodes, then bind a particular split to those declared relations with executable evidence.

No direct required field was identified in the inspected TrainingDML-AI conceptual model for an Artemis action or episode group, a protected group-key rule, zero-to-many observation membership, a crossing violation, or a content-hashed split receipt containing algorithm, seed, assignments, unresolved cases, and validator version. This is a bounded source finding, not a claim that no conformant extension or equivalent external practice exists. The detailed mapping is in `STANDARDS-AND-PRIOR-ART-CROSSWALK.md`.

## Recommended pilot

### Phase 0: freeze one task

Choose one deployment-shaped question before creating a split. Record:

- target population;
- prediction unit;
- estimand;
- label source and audited coverage;
- intended generalization boundary;
- representation and calibration requirements; and
- relationships that must remain intact.

Do not begin with a universal “AI-ready” label.

### Phase 1: publish three versioned artifacts

Use PDS LIDVIDs and collection versions as the source anchors. Map task, sample, split-role, label, provenance, quality, and change concepts onto TrainingDML-AI where the correspondence is accurate. Keep task-specific group semantics in an explicit companion relation until a PDS or OGC reviewer selects a formal encoding. Describe the result as OGC-aligned, not OGC-conformant.

#### 1. Product-to-group membership

One row per product and group association:

| Field | Requirement |
| --- | --- |
| `product_lidvid` | Exact PDS product identity and version |
| `source_snapshot` | Archive or collection version used to generate the row |
| `group_type` | Controlled value such as exposure, action, temporal segment, or reviewed episode |
| `group_id` | Identifier in a namespace that cannot be mistaken for a PDS LID |
| `group_authority` | `archive_authoritative`, `mission_authoritative`, or `derived` |
| `membership_basis` | Exact source or rule supporting the association |
| `method_id` and `method_version` | Reproducible derivation identity when the group is derived |
| `representation_role` | Source, raw, processed, or another defined role |
| `position_in_group` and `observed_group_size` | Bracket or sequence structure when applicable |
| `review_status` | Unreviewed, machine-checked, mission-reviewed, or another controlled state |
| `unknown_reason` | Required when a parent or membership cannot be resolved |

#### 2. Group-to-window or episode membership

One row per relationship, including zero-to-many cases:

- child group type and ID;
- parent window or episode type and ID;
- relationship type, such as planned-window containment or reviewed realized-segment membership;
- membership basis and source time coverage;
- authority and review status; and
- explicit unmatched state when no parent is assigned.

The format must not force one parent. In the verified cohort, 626 actions have no timed-plan membership and 58 have multiple memberships. Dropping the first group omits 25.316% of cohort bytes; naïvely summing overlapping windows inflates assigned bytes by 5.432%.

#### 3. Task-readiness profile

At minimum:

- task ID and version;
- a mapping to the relevant TrainingDML-AI task and individual-sample concepts;
- target population and eligibility rule;
- prediction unit and estimand;
- label source, production method, coverage, unknown state, and review status;
- required protected group keys;
- per-sample training, validation, test, excluded, or unknown role;
- split algorithm and version;
- representation and calibration status;
- camera, time, target, or event controls required by the task; and
- unsupported claims and external validation requirements.

### Phase 2: generate a split receipt

The reference splitter should emit a content-hashed receipt containing:

- source artifact identifiers and hashes;
- protected group key or keys;
- algorithm and version;
- random seed, if any;
- train, validation, test, excluded, and unknown counts at product and protected-group levels;
- every crossing violation;
- unresolved relationships;
- label coverage by relevant activity, camera, event, and split; and
- the exact validator version.

TrainingDML-AI metadata can describe several of these facts, and a published sample can carry its split role. The receipt has a different job: bind one canonical input snapshot, one algorithm execution, the complete assignments, and the validator result into a reproducible audit object. Descriptive metadata does not substitute for that execution record.

The local canary demonstrates the minimum executable behavior on this cohort. Its 4,216-byte receipt binds a 4,573,289-byte complete assignment artifact to the 10,072,026-byte relationship manifest by SHA-256, names the exact grouping key, algorithm, and validator version, records zero unresolved relationships, and reports crossings for every policy. The validator rejects a changed source hash, one altered assignment, one dropped row, a misdeclared grouping key, semantic-scene inflation, an observed-leakage claim, a performance-effect claim, a universal five-second rule, and pixel access. This is an implementation canary for reviewers to challenge, not a proposed production format or a valid scientific split.

A standalone consumer implementation now parses those serialized artifacts without importing Stage 11L code, recomputes every assignment and policy metric, and rejects 11 artifact-level mutations at their named checks. That reduces shared-code confidence risk. It is still only partial implementation diversity because both paths share the declared algorithm, manifest, relationship semantics, repository, and authoring episode.

### Phase 3: fail closed on six conditions

The validator rejects the split when:

1. a product cannot resolve to a declared parent and lacks an explicit unknown state;
2. a declared protected group spans partitions;
3. an unknown or unreviewed relationship is silently treated as independent;
4. many-to-many memberships are dropped, forced to one parent, or aggregated without identity-level deduplication;
5. curated-label coverage and a camera-only metadata baseline are omitted for a target-classification task; or
6. the readiness claim omits the task, estimand, population, representation, calibration boundary, or unsupported generalizations.

Passing proves only that declared relationships were preserved. It does not prove independence, correct labels, representative sampling, calibration, or external generalization.

### Phase 4: choose the formal home

Use the prototype to decide among:

- a PDS collection or supplemental metadata product using existing dictionary fields;
- a mission or discipline LDD addition;
- an ML or provenance LDD addition if the stewards judge the semantics in scope; or
- a linked Planetary Data Ecosystem artifact when archival standardization would be premature.

An OGC TrainingDML-AI JSON or XML encoding, or an extension of one, is also a candidate carrier for the task-facing layer. It should be selected only after the group semantics, canonicalization, conformance target, and PDS linkage have been reviewed. The pilot must not present conceptual alignment as conformance.

PDS’s published process assigns archive design to the data provider and coordinating discipline node. The node identifies needed LDD updates and shepherds them through the Data Design Working Group. The LDD steward validates and submits a release; the PDS Engineering Node performs basic release validation. Archive peer review evaluates validity and usability. See the current [PDS archiving guidelines](https://pds.nasa.gov/home/proposers/archiving/) and [dictionary release process](https://pds.nasa.gov/datastandards/dictionaries/index-1.25.0.0.shtml).

## Pilot acceptance criteria

The pilot passes only when:

- every in-scope product resolves to each required parent or has an explicit unknown reason;
- every declared protected key has zero train, validation, or test crossings;
- unmatched and overlapping relationships survive without silent loss or double-counting;
- a second operator reproduces the same artifact hashes and split receipt from versioned inputs;
- task claims remain within the readiness profile;
- curation time, specialist review time, update cost, and unresolved cases are reported; and
- the result is described as task-specific, not globally AI-ready.

The pilot fails or remains experimental if the group semantics cannot be reviewed, updates cannot be reproduced, unknowns are silently coerced, or the maintenance burden exceeds the decision value.

## Questions a specialist should answer

1. Is the proposed distinction among product identity, collection membership, source lineage, analytical grouping, and split integrity accurate in current PDS4 practice?
2. Would a collection, `Product_Metadata_Supplemental`, another existing product class, or a linked artifact be the least misleading first carrier?
3. Which proposed fields already exist in the common, imaging, provenance, processing, mission, or ML dictionaries?
4. Which fields should map directly to TrainingDML-AI, which require an extension, and which should remain PDS-linked external receipt fields?
5. Is extending the ML LDD appropriate given its stated focus on ML-generated products, or should the task profile and relationship semantics live elsewhere?
6. Which Artemis II grouping keys could be made mission-authoritative, and which should remain explicitly derived?
7. What review and versioning rule should apply when a later archive release changes group membership?
8. Which task-native dependence relations would remain missing even after the proposed pilot?

## Bottom line

The article’s strongest defensible conclusion is structural:

> Product count, observation count, event count, sampling weight, and storage burden are different quantities. A compact, versioned relationship layer can make one class of evaluation error auditable, but only a task-specific design and qualified review can decide the correct outer group.

The article is suitable for publication after owner acceptance of voice and presentation. It should not be represented as PDS endorsement, schema certification, specialist acceptance, or evidence that an actual Artemis II model evaluation failed.
