# Stage 11Q: transcoded injection recovery

State: `VERIFIED_TRANSCODED_INJECTION_RECOVERY`

## Question

How sensitive was the frozen Stage 11P region-sum screen to synthetic point-like pulses in the transcoded overlap clip?

## Frozen grid

- 9 locations inside the threshold-defined lunar footprint
- 6 start frames inside the report-time window
- 3 durations: 1, 2, and 3 frames
- 9 requested signal levels: 250 through 16,000 integrated digital counts per frame
- 1,458 total deterministic trials

The injected shape is a normalized two-dimensional Gaussian with sigma 0.85 pixels. Values are added to decoded grayscale pixels, rounded, and clipped to the unsigned 8-bit range before the exact Stage 11P screen is rerun.

## Result

| Requested integrated DN per frame | Trials recovered | Recovery |
|---:|---:|---:|
| 250 | 0 / 162 | 0.0% |
| 500 | 0 / 162 | 0.0% |
| 1,000 | 0 / 162 | 0.0% |
| 2,000 | 0 / 162 | 0.0% |
| 4,000 | 0 / 162 | 0.0% |
| 6,000 | 0 / 162 | 0.0% |
| 8,000 | 0 / 162 | 0.0% |
| 12,000 | 0 / 162 | 0.0% |
| 16,000 | 9 / 162 | 5.6% |

Fifty percent recovery was not reached.

At the median frame, the 20% relative-rise condition requires about 599 added digital counts. The robust-z 6 condition requires about 4,817 and therefore controls the screen. At the maximum requested signal, clipping limits the realized addition to 2,896 through 4,046 digital counts per frame.

## Interpretation

The Stage 11P no-pulse result does not have demonstrated sensitivity. This is a digital-domain result on the transcoded clip, not a physical brightness limit, a source-pixel test, a flight-sensor characterization, or an event exclusion.

The changed-case lesson is constructive: a future camera null should not be treated as constraining until the released measurement system includes task-shaped injection and recovery across position, background, signal level, and duration.

## Claim ceiling

No physical brightness, impact energy, impactor size, source-pixel equivalence, event exclusion, or NASA acceptance is established.
