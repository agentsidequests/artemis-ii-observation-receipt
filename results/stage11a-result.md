# Stage 11A — Planned-Target Window Replication Census

- Verification: `PASS`
- Evidence state: `VERIFIED_PLANNED_TARGET_WINDOW_REPLICATION_CENSUS`
- Active plan windows / target names: `36` / `19`
- Singleton / repeated target names: `12` / `7`
- Singleton share: `63.158%`
- Pixel payload bytes opened: `0`

## Verified

Among 19 exact plan target-name values represented in the 36 active timed windows, 12 occur in one active window and seven occur in multiple active windows. Sunset is therefore an example of a broader scheduled-window replication constraint, not an isolated case.

## Decision use

A singleton plan name cannot support an internal two-sided evaluation on distinct same-name scheduled windows. Repeated plan names remain candidates only: window overlap, semantic comparability, camera coupling, and event identity still require task-native checks.

## Singleton plan target names

- `Aristarchus Plateau`
- `Crew Position Swap`
- `Earth`
- `Earthrise`
- `Earthset`
- `Hertzsprung Basin`
- `Impact Flashes`
- `Reiner Gamma`
- `Sunrise`
- `Sunset`
- `Vavilov Crater`
- `illum_limb`

## Repeated plan target names

- `Crew Team Swap`: `5` active windows
- `Glushko Crater`: `2` active windows
- `Guided Discussion`: `5` active windows
- `Moon`: `4` active windows
- `Ohm Crater`: `2` active windows
- `Orientale Basin`: `2` active windows
- `Whole Moon`: `4` active windows

## Claim ceiling

Stage 11A may establish that the 36 timed plan windows containing at least one verified complete action use 19 exact plan target-name values, of which 12 occur in one active window and seven occur in multiple active windows. For each singleton name, no internal split can place distinct same-name scheduled windows on both sides. It cannot establish that scheduled windows are independent semantic events, that repeated names are evaluation-ready, that a named observation occurred only once outside the plan, that target tags share the plan ontology, that singleton names are scientifically insufficient, that all archive target classes follow this distribution, or any model-performance, scientific-discovery, novelty, or priority claim.

## Hard negatives

- `call_active_windows_independent_events`: REJECTED
- `call_repeated_targets_evaluation_ready`: REJECTED
- `substitute_target_tags_for_plan_names`: REJECTED
- `claim_singleton_targets_observed_only_once`: REJECTED
- `claim_singleton_targets_scientifically_insufficient`: REJECTED
- `generalize_to_all_archive_target_classes`: REJECTED
- `assign_model_partition_from_plan_count`: REJECTED
- `infer_model_performance_effect`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_replication_census`: REJECTED
