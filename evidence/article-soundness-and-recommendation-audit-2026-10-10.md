# Article soundness and recommendation audit

Date: 2026-10-10

## Decision changed by this pass

The public article should not frame NASA as lacking metadata, provenance, machine-learning vocabulary, or analysis-ready-data work. PDS4 already supplies stable product identity, source references, supplemental table mechanisms, and discipline dictionaries. The current Machine Learning Analysis Local Data Dictionary describes training, validation, and test sets, preprocessing, model architecture, and performance. NASA's 2021 Planetary Data Ecosystem review also explicitly called for analysis-ready products and deeper machine-actionable linkages, and NASA's fiscal-year 2023 response recorded active work on those recommendations.

The OGC TrainingDML-AI standard narrows the gap again. It already models individual samples, dataset membership, split role, tasks, source citations, labels, labeling provenance, quality, and dataset changes. SomBench and MCTED show that planetary ML implementations already materialize split membership and keep spatial parents together. The article therefore must not imply that the field lacks split discipline.

The surviving seam is task-native, sometimes non-spatial dependence: alternate representations, exposure brackets, camera actions, temporal runs, and observing episodes, plus executable evidence that one particular split preserved the declared relation. The constructive contribution is an OGC-aligned companion relationship layer keyed to PDS identifiers and bound to a content-hashed split receipt, not a replacement architecture, a new universal vocabulary, an OGC conformance claim, or a claim of global novelty.

## Primary sources inspected

- PDS4 Data Provider's Handbook, version 1.26.0.0, including `File_Area_Observational_Supplemental` and `Table_Delimited_Source_Product_Internal` support for source-product tables keyed by LIDVID: https://pds.nasa.gov/data/pds4/documents/document_pds4_standards/1.26.0.0/PDS4_DPH_1.26.0.pdf
- PDS4 compatible data dictionaries, version 1.25.0.0, including the Machine Learning Analysis and Provenance dictionaries: https://pds.nasa.gov/datastandards/dictionaries/index-1.25.0.0.shtml
- Current Machine Learning Analysis dictionary JSON, release 1.2.1.1: https://pds.nasa.gov/pds4/ml/v1/PDS4_ML_1P00_1211.JSON
- Machine Learning Analysis dictionary repository and user documentation: https://github.com/pds-data-dictionaries/ldd-ml
- Machine Learning Analysis user guide, including the Data_Set definition and field list: https://pds-data-dictionaries.github.io/ldd-ml/user/user-guide.html
- Current PDS `Product_Collection` and `Inventory` definitions, which establish existing member-product enumeration: https://pds.nasa.gov/datastandards/documents/dd/v1/PDS4_PDS_DD_1O00/webhelp/all/ch02s04.html and https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1J00/webhelp/all/ch03s70.html
- Current `Product_Metadata_Supplemental` carrier constraint, which requires all field names to be defined in a PDS common, discipline, or mission dictionary: https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1J00/webhelp/all/ch03s52.html
- Current PDS archiving roles and LDD-change path, including discipline-node ownership and Data Design Working Group review: https://pds.nasa.gov/home/proposers/archiving/
- Planetary Data Ecosystem Independent Review Board final report, especially its ML/AI linkage and analysis-ready-data findings: https://science.nasa.gov/wp-content/uploads/2023/05/PDEIRBFinalReport-1.pdf
- Fiscal Year 2023 Planetary Science Division response to the review, especially Recommendations 49 and 51 through 53: https://science.nasa.gov/wp-content/uploads/2024/03/psd-pde-irb-response-v1-20240228.pdf
- OGC TrainingDML-AI standards page and revised conceptual model, including individual sample `trainingType`, task, provenance, quality, changesets, extension, and integrity discussion: https://www.ogc.org/standards/trainingdml-ai/ and https://docs.ogc.org/is/23-008r5/23-008r5.html
- SomBench paper and released dataset card, including zone-wise split assignment, cross-track consistency, materialized `DATASET` roles, and boundary-tile exclusion: https://arxiv.org/abs/2609.13277 and https://huggingface.co/datasets/nasa-ibm-ai4science/Sombench-pretraining-data
- MCTED paper, including recursive clustering of intersecting stereo-footprint unions and cluster-wise split assignment: https://arxiv.org/abs/2509.08027

## Claim ceiling

- The schema inspection supports saying that the released ML dictionary names training, validation, and test sets and records model provenance, but the inspected definitions do not expose per-product membership, task-native parent groups, or split-integrity evidence.
- TrainingDML-AI can carry individual sample membership and split role, so the article may not imply that a new vocabulary is needed for those concepts.
- No direct required TrainingDML-AI field was identified for an Artemis action or episode group, a protected-group rule, zero-to-many observation membership, a crossing violation, or the complete executable receipt proposed here. This is a bounded inspection result, not proof that a conformant extension or equivalent practice is impossible.
- SomBench and MCTED are positive precedents for group-aware planetary splits. They do not establish an Artemis-specific non-spatial grouping carrier.
- It does not establish that no PDS mission or community product has ever encoded equivalent relationships elsewhere.
- It does not establish that PDS lacks set membership. `Product_Collection` inventories enumerate member products by LID or LIDVID.
- A `Product_Metadata_Supplemental` is only a candidate carrier. Its fields must already be defined in a PDS dictionary, and source-product tables are limited to product-creation lineage semantics.
- The proposed fields are an illustrative companion design. PDS dictionary and node stewards would decide whether they belong in an existing discipline dictionary, a mission dictionary, a supplemental product, or another Planetary Data Ecosystem artifact.
- The relationship layer demonstrated here uses private reconstructed action keys. They are not official PDS identifiers or semantic scene labels.
- The 80/20 crossing results are expectations under a hypothetical independent split, not observed leakage or model-performance effects.

## Recommendation shaped by the evidence

Pilot three interoperable artifacts on an Artemis-like crew-camera collection, beginning with a versioned PDS-anchored and OGC-aligned linked prototype rather than an immediate standards change:

1. A product-relationship table keyed by PDS LIDVID, with exposure identity, reconstructed or authoritative action identity, representation role, bracket position and size, and grouping-method version.
2. A many-to-many action-to-episode table with relationship type, membership basis, coverage, and review status, preserving unmatched and overlapping actions.
3. A task-readiness profile and validator that reuses TrainingDML-AI concepts where they fit, declares the estimand, minimum split key, label population and coverage, representation and calibration limits, unsupported generalizations, and fails when related groups cross partitions.

The splitter should emit a content-hashed receipt binding the canonical input manifest, algorithm and version, seed, complete assignments, unresolved relations, crossing violations, and validator version. TrainingDML-AI metadata can describe several of those facts, but descriptive metadata alone is not the execution record.

The mission data provider and coordinating PDS discipline node own prototype archive design. If the pilot warrants a dictionary change, the node shepherds it through the PDS Data Design Working Group, the relevant LDD steward validates and submits the release, and the PDS Engineering Node performs basic release validation. Peer review retains scientific usability acceptance.

For the verified cohort, the two reconstructed relationship ledgers total 10,470,310 bytes for 1,625,281,365,343 bytes of archive products, or 0.000644 percent. Under the article's hypothetical independent 80/20 product split, an expected 1,930.148 of 2,166 complete camera actions cross sides. This gives the recommendation a concrete burden and payoff without claiming that an actual pipeline failed.
