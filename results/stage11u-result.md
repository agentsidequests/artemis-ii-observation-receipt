# Stage 11U: Selection and Weighting Cascade

- Verification: `PASS`
- Evidence state: `VERIFIED_SELECTION_WEIGHTING_CASCADE`
- Frozen cohort: `2,166` actions, `7,606` source exposures, `22,818` products
- Pixel payload bytes opened: `0`

## Panel A: selection conditioning

| Declared population and unit | Sunset rows | Denominator | Sunset share |
| --- | ---: | ---: | ---: |
| All source-exposure target fields | 1,553 | 7,606 | 20.418% |
| Nonblank source-exposure target fields | 1,553 | 3,413 | 45.502% |

Conditioning on a nonblank target field changes this descriptive share by `2.229x`. Blank fields remain unknown, not negative examples.

## Panel B: unit weighting inside the tagged subset

| Declared unit | Sunset | Selected/tagged denominator | Sunset share |
| --- | ---: | ---: | ---: |
| Actions with any nonblank tag | 311 | 915 | 33.989% |
| Nonblank-tagged source exposures | 1,553 | 3,413 | 45.502% |
| Products derived from those exposures | 4,659 | 10,239 | 45.502% |
| Bytes attached to those products | 409,399,017,151 | 781,104,206,358 | 52.413% |

The action-to-byte change is `1.542x`. The exposure and product shares are identical because every admitted exposure has exactly three representations; the extra products do not create new independent observations.

## Action-carried sensitivity

If each selected action's nonblank tag membership is conservatively carried across that action's blank exposures, Sunset remains `51.495%` of the selected byte mass. This sensitivity does not make carried tags ground truth.

The overall byte majority is representation-sensitive: Sunset is `49.188%` of tagged source-representation bytes, `52.720%` of tagged raw-representation bytes, and `52.734%` of tagged processed-representation bytes.

The cascade is also activity-conditioned. `24_Sunset` supplies `1,294` of the `1,553` Sunset-tagged exposures. Outside that activity, Sunset is `12.223%` of tagged exposures and `21.554%` of tagged bytes. This attribution check is not a substitute target population.

## All-tag countercheck

Across all `23` nonblank target-tag values, the concentration equivalent is `5.064` tag values under fractional action weighting, `3.823` under exposure or product weighting, and `3.191` under byte weighting. Sunset ranks first under every declared unit. The concentration equivalent is a descriptive index, not an effective number of physical classes.

## Finding

In the frozen cohort, conditioning source-exposure rows on nonblank target tags raises Sunset's descriptive tag share from 20.418% to 45.502%. Inside the selected tagged subset, Sunset is 33.989% of actions, 45.502% of exposures and products, and 52.413% of bytes. An action-carried sensitivity remains a 51.495% byte share.

## Claim ceiling

Stage 11U may establish that, in the frozen complete-action cohort, Sunset occupies 1,553 of 7,606 source-exposure tag fields (20.418%), 1,553 of 3,413 nonblank target-tag rows (45.502%), 311 of 915 actions with any nonblank tag (33.989%), and 409,399,017,151 of 781,104,206,358 bytes attached to nonblank-tagged exposures (52.413%). The same byte-majority result remains 51.495% in an action-carried sensitivity that includes blank exposures from selected actions. The byte result is representation-sensitive: Sunset is 49.188% of tagged source-representation bytes, 52.720% of tagged raw-representation bytes, and 52.734% of tagged processed-representation bytes. The result is also activity-conditioned: activity 24_Sunset supplies 1,294 of 1,553 Sunset-tagged exposures, and outside it Sunset is 12.223% of tagged exposures and 21.554% of tagged bytes. Across all 23 nonblank target-tag values, the concentration equivalent contracts from 5.064 tag values under fractional action weighting to 3.823 under exposure or product weighting and 3.191 under byte weighting. These are declared metadata-query and unit-weighting results. The stage cannot treat blanks as negatives, validate tags as ground truth, estimate physical prevalence, equate bytes with scientific value, claim that every representation layer has a Sunset byte majority, claim invariance to activity composition, call a concentration equivalent an effective class count, assert use by an actual pipeline, establish model bias or performance effects, treat products as independent examples, generalize beyond the frozen cohort, inspect pixels, or claim NASA acceptance, novelty, or priority.
