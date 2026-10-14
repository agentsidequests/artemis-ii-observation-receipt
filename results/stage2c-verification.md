# Artemis II Observation-Execution Testbed — Stage 2C Result

- Verification: **PASS**
- Evidence state: `VERIFIED_SOURCE_NOMINATED_HYPOTHESIS`
- Disposition: `HYPOTHESIS_NOMINATED_STOP_SOURCE_ONLY`
- Admitted explanatory candidates: **1**

## Bounded result

NASA documents one matched-view example in which the realized flyby was 154 seconds earlier than the post-TLI visualization used in the planning lineage. That 154-second example falls inside Earthrise's independently measured 136-to-166-second full-clearance-to-availability-start lag.

Earthset's availability window is 196.650033 seconds wide, while Earthrise's is only 4.147844 seconds. The width difference can therefore make the two events respond differently to an offset of the documented scale: Earthset can remain overlapping while Earthrise misses completely.

This is a source-nominated, quantitatively consistent hypothesis—not a confirmed cause or a uniform timing correction.
The matched-view comparison comes from an earlier scene, not either limb crossing; event-specific transfer remains the unresolved test.

## Quantitative oracle

| Quantity | Value | Frozen relation |
| --- | ---: | --- |
| NASA matched-view actual-vs-visualization delta | 154s earlier | Inside Earthrise lag bracket |
| Earthrise full-clearance-to-window-start lag | [136s, 166s) | Contains 154s |
| Earthset availability width | 196.650033s | Wider than 154s |
| Earthrise availability width | 4.147844s | Narrower than 154s |

## Fields that do not explain the placement

- Requested activity duration differs (8 vs. 12 minutes), but NASA documents it as the LTP observation slot rather than an availability boundary.
- Earthrise requires a Science Situation Report and Earthset does not, but the source supplies no mapping from that reporting flag to visibility-window placement.
- Time-sensitive status, STM links, camera actions, science impact, and location placeholders are shared and cannot discriminate the opposite results.

## Falsifier and stop

When NASA publishes the actual Artemis II SPICE bundle, derive the Earthrise event-specific geometry. Reject the hypothesis if the actual-vs-planned shift falls outside the frozen 136-to-166-second lag bracket or if the OTR timing did not inherit the documented post-TLI planning basis.

Stop the source-only lane after one candidate meets the frozen nomination oracle or after every candidate fails it. Do not obtain more pixels, generalize a constant shift, or convert quantitative consistency into cause.

## Next-step logic

**Recommended:** Stop active timing acquisition with the trajectory-offset/window-tolerance hypothesis recorded. Re-attest the delayed Artemis II SPICE bundle only when NASA publishes an actual release, then run one event-specific geometry falsifier.

Why: The source-only pass found a decision-changing, quantitatively aligned hypothesis, but current public sources cannot adjudicate event-specific geometry or causality.

Blocked: Do not widen image acquisition, claim a planning failure, or present the 154-second example as a uniform correction.

## Hard negatives

- `remove_trajectory_source`: REJECTED
- `move_reported_delta_outside_earthrise_lag`: REJECTED
- `promote_sitrep_without_timing_mapping`: REJECTED
- `equate_request_duration_with_availability`: REJECTED
- `promote_hypothesis_to_confirmed_cause`: REJECTED
