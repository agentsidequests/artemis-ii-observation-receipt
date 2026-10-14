# Artemis II Observation-Execution Testbed — Stage 1 Result

- Verification: **PASS**
- Stage 1 gate: **STOPPED**
- Evidence state: `VERIFIED_STOP`
- Disposition: `STOP_UNVALIDATED_TIMING_LANE`
- Boundary verdicts: 0 PASS / 2 FAIL / 5 AMBIGUOUS

The verification passes because the Testbed correctly stops the original timing lane. It does not mean boundary equivalence passed.

## Boundary map

| Boundary | OTR meaning | Spoken meaning | Verdict |
| --- | --- | --- | --- |
| earthset_first_contact | availability_window_start | optical_first_contact | AMBIGUOUS |
| earthset_complete | availability_window_end | optical_completion | AMBIGUOUS |
| earthrise_first_contact | availability_window_start | optical_first_contact | FAIL |
| earthrise_complete | availability_window_end | optical_completion | FAIL |
| sunset_first_contact | availability_window_start | optical_first_contact | AMBIGUOUS |
| sunset_complete | availability_window_end | optical_completion | AMBIGUOUS |
| sunrise_first_contact | availability_window_start | optical_first_contact | AMBIGUOUS |

## Interval hard negative

| Event | OTR window | Crew progression | Ratio | Verdict |
| --- | ---: | ---: | ---: | --- |
| Earthset | 196.650033s | 171.118s | 1.149 | AMBIGUOUS |
| Earthrise | 4.147844s | 128.213s | 0.032 | FAIL |
| Sunset | 102.807100s | 100.528s | 1.023 | AMBIGUOUS |

Earthrise is decisive: a 4.147844-second availability window cannot be treated as the endpoints of a 128.213-second first-corner-to-completely-risen progression.

## Source-backed interpretation

NASA documents the OTR timing as an observation availability window and separately presents target visibility and request timing. None of the reviewed source locators defines `start_date_time` or `end_date_time` as first or last optical contact.

## Next-step logic

**Recommended:** Reframe Stage 2 as an independent geometry coverage test: compute physical event intervals from SPICE or image-state transitions, then test whether each OTR availability window contains or overlaps the event. Do not call the difference a boundary delay.

Why: It preserves the strongest candidate while removing the failed semantic assumption and is cheaper than expanding to the image archive.

Blocked: Do not advance the original plan-boundary-versus-crew-boundary timing claim.

## Hard negatives

- `promote_earthrise_duration_mismatch`: REJECTED
- `present_request_time_as_contact`: REJECTED
- `treat_beginning_as_completion`: REJECTED
- `promote_sunset_from_duration_only`: REJECTED
