# Artemis II Observation-Execution Testbed — Stage 5A Result

- Verification: **PASS**
- Evidence state: `VERIFIED_BUDGET_STOP`
- Acquisition stop: `BUDGET_EXHAUSTED`
- Range transport: **verified**
- 15-second clip: **not materialized**
- Accepted media-body bytes: **67,108,864 / 2,960,238,197**

The official delivery path returned exact HTTP 206 byte ranges and a source length that matches the PDS label. The MP4 stores a 30,289,940-byte `moov` index at the file tail. The direct FFmpeg-through-range-gate treatment consumed the full 64 MiB ceiling while seeking and stopped without creating a clip.

This is a verified budget stop, not a successful extraction and not proof that every bounded extraction strategy would fail. The terminal attempt accepted only 2.267% of the complete product.

## Container geometry

- `mdat`: offset 40, size 2,929,948,217 bytes
- `moov`: offset 2,929,948,257, size 30,289,940 bytes

Stage 5A can prove only its observed transport outcome. VERIFIED_BOUNDED_EXTRACTION would prove materialization within the frozen client-side byte budget; VERIFIED_BUDGET_STOP proves exact range support and budget enforcement but not clip materialization or the failure of every bounded extraction strategy. Neither state establishes what the pixels show, camera pointing, lunar geolocation, a physical flash, impact causation, or scientific novelty.

## Next-step logic

- Contract route after this stop: Complete Stage 3B and retain the flash as transcript-supported but physically unvalidated unless a cheaper official server-side subset route appears.
- A later alternative, if separately authorized: Repair only the local extraction representation if the receipt proves range support and material budget remains; otherwise use the transport-failure route.
- Stop boundary: Stop before any full-product download, second-channel inspection, still-image inspection, pixel interpretation, geolocation, or impact claim.

## Hard negatives

- `budget_not_exhausted`: REJECTED
- `source_total_changed`: REJECTED
- `clip_claim_without_artifact`: REJECTED
- `unrestricted_request_admitted`: REJECTED
- `moov_geometry_changed`: REJECTED
