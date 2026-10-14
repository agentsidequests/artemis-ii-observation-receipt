# Stage 10Q — Sunset Transcript Alignment

- Verification: `PASS`
- Evidence state: `VERIFIED_TRANSCRIPT_ALIGNED_OBSERVATION_EPISODE`
- Transcript utterances inside cluster: `35`
- Speakers inside cluster: `{'Hansen': 34, 'Wiseman': 1}`
- Nearest related boundary offsets: `2.084 seconds before` / `0.013 seconds after`
- Pixel payload bytes opened: `0`

## Verified

The exact 143.61-second Stage 10P Sunset interval contains 35 timestamped transcript utterances (34 Hansen, one Wiseman) about the Sun, Moon, glow, plume, and streamer. Related utterances bracket the interval by 2.084 seconds before and 0.013 seconds after.

## Decision use

This independent execution record supports calling the concentration microcase one time-bounded observation episode. It makes the grouping hazard concrete without establishing semantic scene identity or visual redundancy.

## Claim ceiling

Stage 10Q may establish that the exact Stage 10P interval is independently time-aligned with a dense, topically coherent crew observation record: 35 timestamped utterances occur inside the 143.61-second cluster, bracketed by related utterances 2.084 seconds before and 0.013 seconds after. This supports calling it a time-bounded observation episode. It cannot establish one semantic scene, visual similarity or redundancy among images, transcript-to-camera operator identity, activity-label correctness, observed leakage, a model-performance effect, archive-wide representativeness, scientific discovery, novelty, or priority.

## Hard negatives

- `call_episode_a_semantic_scene`: REJECTED
- `call_every_image_visually_redundant`: REJECTED
- `call_transcript_pixel_ground_truth`: REJECTED
- `attribute_camera_to_named_speaker`: REJECTED
- `call_expected_crossing_observed_leakage`: REJECTED
- `generalize_episode_to_archive`: REJECTED
- `infer_model_performance_effect`: REJECTED
- `claim_scientific_discovery_or_priority`: REJECTED
- `open_pixels_for_alignment_canary`: REJECTED
