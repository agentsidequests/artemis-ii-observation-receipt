# Stage 8C — Camera-Native Ordinal Canary

- Verification: `PASS`
- Evidence state: `NO_CAMERA_NATIVE_ORDINAL_CONCORDANCE`
- Disposition: `CLOSE_CAMERA_NATIVE_GLUSHKO_OHM_LANE`
- Verification network bytes: `0`

## Joint Same Frame

- Complete view pass: `False`
- Primary cell pass: `False`
- Passing robustness cells: `0 / 3`

| Cell | Glushko AUC | Ohm AUC | Similarity | Direction | Pass |
| --- | ---: | ---: | ---: | --- | --- |
| `inner_1p25_2p75_outer_2p75_3p75` | 0.515901 | 0.469209 | undefined | Glushko > Ohm | `False` |
| `inner_1p50_3p00_outer_3p00_4p00` | 0.537977 | 0.497915 | undefined | Glushko > Ohm | `False` |
| `inner_1p75_3p25_outer_3p25_4p25` | 0.556599 | 0.525383 | 0.448467 | Glushko > Ohm | `False` |

## Matched 400 mm Pair

- Complete view pass: `False`
- Primary cell pass: `False`
- Passing robustness cells: `0 / 3`

| Cell | Glushko AUC | Ohm AUC | Similarity | Direction | Pass |
| --- | ---: | ---: | ---: | --- | --- |
| `inner_1p25_2p75_outer_2p75_3p75` | 0.505873 | 0.469682 | undefined | Glushko > Ohm | `False` |
| `inner_1p50_3p00_outer_3p00_4p00` | 0.529397 | 0.500062 | 0.002094 | Glushko > Ohm | `False` |
| `inner_1p75_3p25_outer_3p25_4p25` | 0.551675 | 0.528916 | 0.559571 | Glushko > Ohm | `False` |

## Result

All six frozen cells preserve the Glushko-greater-than-Ohm direction, but none passes the complete two-target signal and similarity oracle. Direction alone does not reproduce Hansen's compound comparison, so the exact camera-native lane closes without retuning.

## Interpretation boundary

A strong pass would establish bounded ordinal concordance in the exact official processed browse images: both coordinate-derived ray fields are locally brighter by the frozen rank metric, their effects are similar, and Glushko is slightly stronger in both the joint frame and matched pair. It would not establish physical albedo, calibrated photometry, Hansen's retinal or perceived stimulus, the camera as the carrier of his judgment, a causal explanation of the Stage 8A mismatch, independent replication, novelty, or a public scientific finding.

## Next-step logic

- Strong: Retain the result as a private camera-native concordance and pressure-test whether known processing, lighting, window, or geometry confounds can explain it before any specialist-facing analysis. Do not upgrade it to perception or physical albedo.
- Joint only: Retain a same-frame photographic signal but do not call it robust across views. Prefer a future geometry/processing falsifier over more image selection.
- Pair only: Treat the matched-pair signal as insufficient because the stronger same-frame control failed. Close the lane without selecting alternate frames.
- Discordant: Close the camera-native Glushko/Ohm concordance lane and retain Hansen's statement as qualitative mission evidence only.
- Indeterminate: Repair only the named source, coordinate, or decoder defect and rerun the frozen contract. Do not change products, regions, endpoint, or thresholds.
- Cross-lanes: Reiner Gamma remains a separate lower-priority candidate. Official SPICE can re-attest geometry but cannot turn camera code values into Hansen's perception.
