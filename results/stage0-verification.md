# Artemis II Observation-Execution Testbed — Stage 0 Result

- Overall: **PASS**
- Evidence state: `VERIFIED`
- Baseline run: `PASS`
- Hard negatives rejected: `YES`

## Recomputed event boundaries

| Event | Planned UTC | Transcript cue UTC | Delta | Result |
| --- | --- | --- | ---: | --- |
| Earthset first contact | 2026-04-06T22:42:19.730Z | 2026-04-06T22:40:43.102Z | 1m 36.6s early | PASS |
| Earthset complete | 2026-04-06T22:45:36.380Z | 2026-04-06T22:43:34.220Z | 2m 02.2s early | PASS |
| Earthrise first contact | 2026-04-06T23:25:30.000Z | 2026-04-06T23:21:18.957Z | 4m 11.0s early | PASS |
| Earthrise complete | 2026-04-06T23:25:34.147Z | 2026-04-06T23:23:27.170Z | 2m 07.0s early | PASS |
| Sunset first contact | 2026-04-07T00:35:08.308Z | 2026-04-07T00:32:44.177Z | 2m 24.1s early | PASS |
| Sunset complete | 2026-04-07T00:36:51.116Z | 2026-04-07T00:34:24.705Z | 2m 26.4s early | PASS |
| Sunrise first contact | 2026-04-07T01:31:02.595Z | 2026-04-07T01:29:47.301Z | 1m 15.3s early | PASS |

## Bounded finding

The archived transcript cues occur earlier than the paired OTR geometry-window fields for all seven frozen boundaries.

This verifies transcript-to-plan alignment mechanics only. It does not establish physical contact timing, cause, novelty, Artemis III generalization, or operational consequence.

## Hard negatives

- `shift_earthrise_plus_300`: REJECTED
- `cue_not_found`: REJECTED
- `swap_earthset_plan_field`: REJECTED
