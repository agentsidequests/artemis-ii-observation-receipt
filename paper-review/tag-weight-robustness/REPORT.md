# Artemis II tag-weight robustness

13 October 2026. Private exploratory accounting follow-on, not a new physical or image-content result.

## The new bounded result

Sunset occupies 52.412855% of the bytes in the original nonblank-tag subset. Reassigning the 48 largest Sunset-tagged exposure fields to another nonblank target would reduce its byte share to 49.980167%; the best 47-field reassignment still leaves 50.030744%. The query, total bytes, capture keys and representations remain fixed.

These are hypothetical memberships, not detected tag errors. The source is not relabeled. This sensitivity concerns a narrow majority claim, not Sunset's ranking or physical presence.

## Missingness survives the weighting change

Nonblank values are held fixed here, with each blank unconstrained for one target value. These are sharp marginal metadata-completion ranges, not confidence intervals, content prevalence or jointly achievable multiclass endpoints.

| Unit | Lower share | Upper share | Width | Minimum blank-field resolutions for ≤5pp width |
| --- | ---: | ---: | ---: | ---: |
| exposure_fields | 20.418% | 75.546% | 55.128pp | 3,813 |
| products | 20.418% | 75.546% | 55.128pp | 3,813 |
| data_source_bytes | 22.856% | 76.388% | 53.532pp | 3,733 |
| data_raw_bytes | 25.420% | 77.203% | 51.783pp | 3,749 |
| data_processed_bytes | 25.431% | 77.206% | 51.776pp | 3,748 |
| all_representation_bytes | 25.189% | 77.130% | 51.940pp | 3,747 |

For combined archive bytes the possible full-cohort Sunset membership range remains 25.189%-77.130%. The 51.940pp width is unresolved accounting mass. Prioritizing the highest-weight blank fields minimizes the number of perfectly resolved fields under equal field cost, but still requires 3,747 resolutions for a worst-case width at most 5pp. The exposure-weighted baseline needs 3,813. Changing the unit or sorting the blanks does not make this a small deterministic completion task.

## Constructive witnesses and proof

For fixed positive weights, each completion endpoint is attained by setting every blank target membership to zero or one. For an at-most-r recorded-field reassignment budget, the lower endpoint removes the r largest known-positive weights; the upper endpoint adds the r largest known-negative weights. These are separate realizable witnesses. The sum of the r largest weights is an upper bound on every r-field subset, so the majority witness and equal-field-cost budget are cardinality-minimal. Integer predecessor checks avoid floating-point decisions at 50% or the requested width.

The saved JSON also contains 0, 1, 25, 47, 48, 50, 100 and 200-field sensitivity bounds for both populations and all six units. Budgets are assumptions, not estimates of the archive's error rate. The CSV witness identifies exact frozen capture keys, actions, activities and weights; the priority CSV is a hypothetical field-resolution order, not a reviewer queue or an executed audit.

## Explicit recommendations

1. If asserting a selected-byte majority, publish the smallest known-tag perturbation that changes it, alongside the query, weights and source version. In this frozen reconstruction, the diagnostic threshold is 48 fields out of 3,413 recorded fields (about 1.41%); that is not a measured error rate.
2. Distinguish completing blanks from validating recorded tags. A blank-only audit cannot establish the accuracy of the selected-byte majority.
3. Declare the audit job before prioritizing: worst-case individual-field completion, probability-based estimation, or majority robustness. Do not use the 3,747-field guarantee as a statistical sample size or demand NASA backfill an archive not designed for this target task.
4. Use weight-descending priority only for an accepted equal-field-cost completion objective. If retrieval, viewing or adjudication costs differ, freeze those costs and solve the appropriate constrained problem; weight sorting is not generally cost-optimal. Image-content judgments still require a qualified concept, reference and reviewer workflow.

NASA/PDS already supply substantial provenance and relevant scientific practice. These are task-specific receipt proposals for review, not NASA-accepted requirements or evidence of an archive defect.

## Limits and replay

Exact deterministic metadata-accounting sensitivity under the declared membership, fixed selection/weight and equal-field-cost assumptions. Reassignment budgets are hypothetical, not measured error rates. Completion bounds are marginal metadata-membership intervals, not a joint multiclass completion or physical truth. No actual audit, new pixels, physical capture merge, NASA pipeline finding, scientific discovery or acceptance.

Original filename/order-conditioned grouping and physical-identity uncertainty remain active. The one-action conditional sensitivity is not silently substituted. Flash timing, distance withdrawals, no-photometry and no-calibrated-flux ceilings are unchanged. No pixels, new source acquisitions, image labels, actual audits, outreach or publication were performed.

From the owning private Testbed, run `python -B -m src.tag_weight_robustness --check`. The contract, result, witness and source hash are under `paper-review/tag-weight-robustness/`; the exact source manifest remains unmodified. See `VERIFICATION.md` for measured checks and native-oracle scope. This report alone does not establish those checks passed.
