# Artemis II: what the target fields leave undetermined

Private analysis checkpoint, 11 October 2026. No publication or NASA acceptance is implied.

## The result

In the verified complete-action cohort, 4,193 of 7,606 source exposures have blank target fields. That is 55.128% of this particular cohort, not a claim about every file in the public archive. The remaining 3,413 fields contain 1,553 recorded Sunset values.

Holding those recorded values fixed and allowing each blank either Sunset or non-Sunset membership gives an exact mathematical range for the completed field share:

`1,553 / 7,606 <= possible Sunset field share <= (1,553 + 4,193) / 7,606`

The endpoints are 20.418% and 75.546%. Both are constructively attainable under this deliberately unconstrained model. A 7,606-row witness file retains every source capture and original field while supplying the two binary membership assignments. It is not a relabeled dataset or a training set.

The 45.502% Sunset share among nonblank fields is therefore a description of the selected subset, not an identified full-cohort composition. A strict completed-field majority requires at least 2,251 of the blank fields to be Sunset. With 2,250, the count is exactly half the cohort. Current metadata establish neither side.

All 23 observed field values have the same marginal interval width. The intervals are valid constraints together, but their upper endpoints cannot all be realized at once. They are not a joint class distribution.

## What this changes in the advice

“Audit the labels” hides two different jobs. Specify which one is wanted before choosing a budget.

| Desired result | Evidence needed under the stated model |
| --- | --- |
| A deterministic completion range no wider than 10 percentage points | Resolve at least 3,433 actual blank fields, leaving at most 760 unresolved. |
| The same guarantee at 5 percentage points | Resolve at least 3,813, leaving at most 380. |
| The same guarantee at 1 percentage point | Resolve at least 4,117, leaving at most 76. |
| A statistical estimate of a task-specific target population | Use a declared sampling design, inclusion probabilities, label oracle, dependence treatment and uncertainty model. The budgets above are not statistical sample sizes. |

Every individually resolved field removes one over 7,606 from the worst-case completion width. A probabilistic estimate can serve a different purpose without resolving thousands of fields, but its confidence interval cannot be presented as certification of every unreviewed record. No audit sample or population estimate was produced here.

There is also a second uncertainty: whether recorded tags are correct for the intended task. NASA's Data User Guide, Table 17, already says primary targets were manually assigned to a subset and were not thoroughly verified after the mission. These bounds hold the recorded strings fixed; they are not bounds on true image content or physical Sunset prevalence. A content-label audit must inspect already-tagged images as well as blanks.

## Conditional recommendation for a future benchmark

If NASA or another team chooses to build a target-recognition benchmark from this material:

1. Define the task, eligible observation population and target meaning first. An archive field is not automatically an exhaustive content label.
2. Separate missing-field resolution from validation of recorded labels. Preserve unknown, not-applicable, ambiguous and rejected states rather than forcing a class.
3. For an estimation audit, declare its frame and selection probabilities. Inspect blank and nonblank strata and the observed camera/activity structure; retain capture and action identifiers so related exposures are not mistaken for independent sampled events.
4. Report the cohort identity, audit outcome, remaining unknowns, label disagreements, assumptions and uncertainty type. Keep logical completion bounds separate from statistical estimates and model-performance claims.

This is a proposed task-conditioned audit contract, not a requirement that NASA backfill its mixed-purpose archive. NASA already discloses the limitation. The contribution here is quantifying its consequence and distinguishing the evidence needed for different claims.

## Verification, scope and custody

Stage 11V uses only the existing hash-pinned metadata manifest and adds no source acquisition or new pixel analysis. A separate PowerShell implementation recounts all source captures and all 23 field values, and matches the Python result. Exhaustive small binary-completion cases, a joint-endpoint countercase, per-row witness checks, duplicate-capture refusal, source-change refusal and output-path protections test the named mathematical and software seams. The ten declaration mutations are not a general semantic detector.

The source cohort and bound are assumption-specific. Labels remain unvalidated, the missingness mechanism remains unresolved, and no actual sampler, model bias, performance effect, calibrated flash flux, archive defect, scientific discovery or global novelty is established. The native recount reuses the same source, so it is implementation-diverse verification rather than independent science replication.

The internal evidence brief now includes this result. The public essay and specialist packet received only a factual correction to the nonblank query; full narrative integration remains the next unit. The source, witness CSV and native receipt are owned by the private local Testbed. Its existing lack of a remote is unchanged.

Reproduce with the Stage 11V commands in the Testbed README. Exact manifest SHA256: 8edd58437cc609229edb5abb41c4e00048bb420354f1ac17a269da92c17e4729. Witness SHA256: ad21d266cea32f783c81b766a72021d228b345d7119e200db3dbb33f0dd653e3.

All 584 Testbed tests passed, including the 19 Stage 11V checks. The earlier essay and reviewer files in Documents are preserved delivery snapshots; this new brief carries the latest analysis, pending the next narrative integration and delivery refresh.

The earlier draft, corrected wording, source identities and verification limits are preserved in evidence/stage11v/recovery-and-review.md. Reopen this calculation only for a changed cohort, justified constraint, audited/revised labels or a real target-modeling task.
