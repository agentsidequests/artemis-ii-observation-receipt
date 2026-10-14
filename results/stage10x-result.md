# Stage 10X — Task-Conditioned Readiness Map

- Verification: `PASS`
- Evidence state: `VERIFIED_TASK_READINESS_SEPARATION`
- Candidate tasks: `6`
- Independent blocker families: `4`
- Pixel payload bytes opened: `0`

## Verified

The current archive is ready for some bounded tasks, conditional for others, and insufficient for still others. Retrieval accounting is supported now; representation work is supportable with a claim limit; within-event modeling needs a frozen protocol; supervised target classification needs a label-population audit and camera/event controls; new-Sunset-event generalization needs another event; calibrated color or photometry needs an external calibration chain.

## Task map

| Task | Status | Admissible unit | Limiting boundary |
| --- | --- | --- | --- |
| archive_retrieval_and_footprint_audit | `SUPPORTED_NOW` | archive product, exposure identity, or byte count when explicitly named | not a scientific image-content or independent-sample claim |
| within_identity_representation_transformation | `SUPPORTED_NOW_WITH_CLAIM_LIMIT` | exposure identity with sibling representations kept together | processed is an uncalibrated vendor interpretation, not physical truth |
| within_event_temporal_or_hdr_modeling | `CONDITIONALLY_SUPPORTABLE` | time-blocked action or larger task-native temporal group | horizon, gap, camera coupling, target construction, and representation are not yet frozen |
| supervised_archive_target_classification | `NOT_YET_SUPPORTABLE` | event-safe groups from a task-specific audited label population | only 44.872% of cohort exposures are tagged; coverage is activity-structured and camera is predictive inside the curated subset |
| new_sunset_event_generalization | `NOT_INTERNALLY_IDENTIFIABLE` | whole scheduled Sunset event | the mission plan contains one Sunset event, yielding zero two-sided internal event allocations |
| calibrated_color_or_photometry | `NOT_SUPPORTED_BY_ARCHIVED_TIERS_ALONE` | externally calibrated measurement tied to a validated instrument response | the official guide provides no calibrated products and warns that processed color cannot be completely verified or quantified |

## Decision use

Replace the binary question 'is this dataset benchmark-ready?' with six task-specific readiness decisions. The four blocker families are independent: a better split cannot create labels, another event, camera balance, or calibration.

## Claim ceiling

Stage 10X may establish that current Artemis II crew-camera evidence has task-dependent readiness: retrieval accounting and bounded within-identity representation work are supportable now; within-event modeling is conditional on a task-native protocol; archive-wide target classification is not yet supportable from the curated tags; new-Sunset-event generalization is not internally identifiable from one event; and calibrated color or photometry is not supported by the archived tiers alone. These limitations arise from at least four distinct boundary families, so no single generic split repairs them. It cannot call the archive globally benchmark-ready, globally unusable, scientifically defective, or incapable of future task-specific use; it cannot establish pixel similarity, actual leakage, model performance, label correctness, calibration, scientific discovery, novelty, or priority.

## Hard negatives

- `call_archive_globally_benchmark_ready`: REJECTED
- `call_archive_globally_unusable`: REJECTED
- `call_retrieval_a_scientific_model`: REJECTED
- `call_within_event_new_event_generalization`: REJECTED
- `use_blank_tags_as_negative_labels`: REJECTED
- `omit_camera_only_baseline`: REJECTED
- `call_processed_tier_calibrated`: REJECTED
- `claim_one_split_repairs_all_boundaries`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_readiness_synthesis`: REJECTED
