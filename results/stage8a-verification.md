# Stage 8A — Glushko/Ohm Reflectance Canary

- Verification: `PASS`
- Evidence state: `NO_REFLECTANCE_CONCORDANCE`
- Disposition: `STOP_GLUSHKO_OHM_REFLECTANCE_LANE`
- Scored verification network bytes: `0`

## Result

The frozen 566 nm proxy does not satisfy the complete contrast, similarity, direction, and robustness oracle. The reflectance lane stops.

| Target | Ray median | Background median | Local contrast | Ray pixels | Background pixels |
| --- | ---: | ---: | ---: | ---: | ---: |
| Glushko | 0.093939 | 0.095870 | -2.014% | 2557 | 5100 |
| Ohm | 0.110668 | 0.110785 | -0.106% | 6314 | 12631 |

Primary similarity ratio: `UNDEFINED (one or both local contrasts are non-positive)`. Glushko greater than Ohm: `NO`.
Robustness: `0/9` cells meet contrast plus similarity; `0/9` retain the Glushko-greater-than-Ohm direction.

## Source and burden

Accepted science-source network bytes: `21847168`. Complete network burden including the rejected browse representation: `66162790`. Verification replays locally.

## Scientific ceiling

A pass would establish only bounded cross-axis concordance between one astronaut's same-session ordinal comparison and one frozen 566 nm local-contrast proxy for two named ray sectors. It would not reconstruct the crew's viewing geometry or spectral stimulus, establish causal perception, control geology or substrate completely, establish observer generality, make raster pixels independent samples, show statistical significance, demonstrate scientific novelty, validate ray boundaries beyond the named-axis proxy, or create a publishable scientific result.

## Next-step logic

- If passed: Retain the result as a stronger private canary. Before any public or scientific claim, require one independent observation or endpoint that was not used to choose the geometry, plus specialist review of the photometric and geologic controls.
- If partial: Retain the exact split between similarity, local contrast, and direction. Do not rewrite the astronaut claim or thresholds; decide whether a second independently frozen band or observation could discriminate the mismatch.
- If failed: Stop the Glushko-Ohm reflectance lane and preserve the transcript observation as qualitative only.
- If indeterminate: Repair only a named source identity, label, or projection defect without changing the semantic claim, regions, band, or oracle; otherwise stop.
