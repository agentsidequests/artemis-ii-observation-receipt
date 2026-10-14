# Stage 10W target-tag readiness screen — 10 October 2026

## Decision this screen can change

Whether the Artemis II target tags can be treated as an evaluation-ready supervised-learning label set, and whether the Stage 10U camera-target association should be attributed to acquisition alone. The screen can qualify the label population and nominate an audit; it cannot recover missing targets or classify the missingness mechanism.

## Sources inspected

- NASA, “NASA Releases Artemis II Lunar Science Data, Images,” 7 October 2026: <https://www.nasa.gov/blogs/artemis/2026/10/07/nasa-releases-artemis-ii-lunar-science-data-images/>
- WIRED, “NASA Just Made Nearly 1 TB of Artemis II Data Available to the Public,” 9 October 2026: <https://www.wired.com/story/nasa-just-made-nearly-1-tb-of-artemis-ii-data-available-to-the-public/>
- NASA PDS, *Artemis II Lunar Science Data User Guide*, preserved locally at `evidence/stage10d/source/artemis2_data_user_guide.txt`, especially Table 17.
- Sportisse et al., “Are labels informative in semi-supervised learning?”, ICML 2023: <https://proceedings.mlr.press/v202/sportisse23a.html>
- Dervovic and Cashmore, “Model Evaluation in the Dark: Robust Classifier Metrics with Missing Labels,” AISTATS 2025: <https://proceedings.mlr.press/v258/dervovic25a.html>

## Findings

The public release is correctly described as ripe for exploration and direct analysis, but that does not make every metadata field an exhaustive supervised-learning target. The Data User Guide says primary targets were assigned through visual inspection and manual tagging for only a subset of images, were not thoroughly verified post-mission, and may contain errors.

The complete-action cohort makes the selection visible. Only 3,413 of 7,606 source exposures have nonblank target tags. Coverage is not approximately uniform by scheduled activity: 17 of 45 activity values have zero coverage, eight have complete coverage, and 20 are partial. `24_Sunset` is 1,294/1,294 tagged, while `12_Orientale Basin (2/2)` is 0/399 and `07_Whole Moon` is 3/456. Camera coverage also ranges from 30.078% to 67.900%.

The external methods literature establishes why missing-label evaluation needs explicit treatment and why label availability can itself be informative. It does not classify the Artemis II mechanism. Stage 10W therefore uses the narrower language “observably nonuniform, mechanism unresolved” and does not call the pattern missing-not-at-random.

## Decision impact

A target model trained and tested only on nonblank rows would estimate performance for a curated subset unless a task-native audit justifies a broader population claim. Blank tags must not be converted to negative examples. Activity or camera metadata must not be used to impute targets merely because they predict whether a tag is present.

Stage 10W also qualifies Stage 10U. The camera-target association remains a valid prospective shortcut canary within the tagged subset, but its mechanism can include both acquisition and curation structure. A future supervised task therefore needs a label-presence audit before a camera-only target baseline.

The plan-bounded Sunset result survives this pressure test because its 00:36–00:44 boundary comes from the targeting plan and includes all admitted rows in the time window without filtering on `target_id`. The unanimous Sunset tags are corroboration, not the selection rule.

## Recheck trigger

Reopen after a task-specific relabeling sample, a formal target-tag audit, revised PDS labels, or a public supervised Artemis II target model.
