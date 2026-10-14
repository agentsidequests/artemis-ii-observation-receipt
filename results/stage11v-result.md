# Stage 11V - Target-Field Completion Bounds

- Verification: `PASS`
- Evidence state: `VERIFIED_TARGET_FIELD_COMPLETION_BOUNDS`
- Source exposures: `7,606`
- Nonblank / blank target fields: `3,413` / `4,193`
- Observed target-field values: `23`
- Sunset observed share among nonblank fields: `45.502%`
- Sunset full-cohort completion bound: `20.418%` to `75.546%`
- Bound width: `55.128%`
- Pixel payload bytes opened: `0`
- Row-level completion witnesses: `7,606`

## Finding

With observed nonblank fields fixed and blanks unconstrained one target-field value at a time, Sunset spans 20.418% to 75.546% of the frozen cohort. The 55.128 percentage-point interval is the blank-field share, not an estimate of physical prevalence.

## Decision use

Report tagged-subset balance together with full-cohort completion bounds. Narrow the interval only with a declared label audit or another independently justified constraint on blank fields.

## Majority tipping point and audit job

A strict Sunset field majority requires 2,251 of the 4,193 blank fields (53.685%) to be completed as Sunset. One fewer produces exactly 50%, not a majority. Neither side is established by the current fields.

If no additional structural assumptions are made, resolving individual blank fields reduces the worst-case completion width by one divided by 7,606 per field. A width no greater than 10, 5 or 1 percentage points requires resolving at least 3,433, 3,813 or 4,117 blank fields respectively. These are deterministic completion budgets, not recommended statistical sample sizes.

A sample-based estimate is a different job. Declare the sampling frame, inclusion probabilities, task-native label oracle, dependence handling and uncertainty model before using it to estimate composition. An estimated proportion or confidence interval is not a guarantee about all unreviewed fields. The observed tag values are themselves not validated image-content labels.

## Claim ceiling

Stage 11V may establish that, if the 3,413 observed nonblank target fields are held fixed and the 4,193 blank fields are unconstrained for one target-field value at a time, Sunset's completed full-cohort field share can range from 1,553 of 7,606 (20.418%) to 5,746 of 7,606 (75.546%). The 55.128 percentage-point width equals the blank-field share, and the same marginal width applies to every observed target-field value. These are sharp bounds for completing the current metadata field under the stated assumptions. Direct arithmetic also supports the strict field-majority tipping point and minimum individual-field resolutions for declared worst-case width guarantees. They are marginal constraints, not a joint multiclass distribution; all intervals hold for a completed single-valued field but their upper endpoints cannot all be attained together. They are not validated labels, physical target prevalence, image-content inference, model behavior, statistical sample-size requirements, confidence intervals, physical-truth guarantees, or evidence of NASA acceptance, novelty, or priority.

## Hard negatives

- `call_blank_fields_negative`: REJECTED
- `call_nonblank_tags_validated`: REJECTED
- `narrow_sunset_bound_without_assumption`: REJECTED
- `call_lower_bound_prevalence`: REJECTED
- `call_upper_bound_prevalence`: REJECTED
- `call_marginal_bounds_simultaneous_distribution`: REJECTED
- `call_bounds_physical_prevalence`: REJECTED
- `generalize_beyond_frozen_cohort`: REJECTED
- `claim_nasa_acceptance_novelty_or_priority`: REJECTED
- `open_pixels_for_completion_bounds`: REJECTED
