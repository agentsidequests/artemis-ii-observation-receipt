# Stage 8B — Actual-Stimulus Recoverability Gate

- Verification: `PASS`
- Evidence state: `CAMERA_NATIVE_STIMULUS_PROXY_AVAILABLE`
- Disposition: `ADMIT_SEPARATE_CAMERA_NATIVE_CANARY`

## Recoverability result

- **A — SATISFIED:** Hash-pinned official labels place Glushko at 2026-04-06T19:17:12.47Z, Ohm at 19:25:15.53Z, and the joint frame at 19:27:31.04Z, inside the frozen hash-pinned transcript intervals.
- **B — SATISFIED:** All three PNGs decoded. The selected target regions and ray structures are visible, and dense official label control points fall within 0.156 degrees of the official Glushko/Ohm coordinates.
- **C — SATISFIED:** The selected Glushko and Ohm labels both report Nikon D5, the same 80-400 mm lens, 400 mm, f/8, ISO 400, and 0.001 s.
- **D — SATISFIED:** The 19:27:31.04Z wider frame is officially tagged with Glushko and secondary target Ohm; both coordinate-localized ray-crater regions are visibly present in the same image.
- **E — NOT SATISFIED:** The labels provide strong 2-D fitted pixel-to-lunar-coordinate control and image footprints, but not spacecraft position, attitude, a physical camera pointing model, or incidence/emission/phase geometry. The official 2026-10-08 PDS calendar lists Artemis II SPICE with anticipated date 2026-10-10 and actual release date TBD. Therefore complete line-of-sight plus lighting reconstruction is not currently recoverable.
- **F — NOT SATISFIED:** The target request separates unaided-eye and camera actions, but the scored transcript comparison does not fix naked-eye versus optical viewfinder versus display mediation. The released records do not supply the operative window transmission/angle model, eye/display mapping, or Hansen's changing visual adaptation.

## Interpretation

The archive classification is an availability result. It does not by itself validate a reconstruction or explain the failed Stage 8A reflectance proxy.

## Claim ceiling

A full pass would establish source recoverability, not that the recovered reconstruction is scientifically correct or perceptually identical. A camera-proxy result would establish only that official, time-correlated, camera-state-matched photographic records can support a bounded same-session comparison. It would not reconstruct Hansen's retinal stimulus, establish the camera as the judgment carrier, recover complete spacecraft or window geometry, control visual adaptation, explain the Stage 8A mismatch causally, validate a photometric measurement, establish novelty, or support a public scientific claim.

## Next-step logic

- Full human stimulus: Form a separate reconstruction test with the recovered geometry and optical assumptions exposed; do not treat availability as validation.
- Camera proxy: Admit one separately frozen camera-native paired-and-joint-image canary. Keep its claim photographic and same-session; do not call it Hansen's actual stimulus.
- Metadata only: Stop image interpretation. Preserve the product/time mapping as metadata and close the stimulus lane unless a source defect can be repaired without changing selection.
- No reconstruction: Close the recoverability lane and retain the transcript as qualitative mission evidence only.
- Indeterminate: Repair only the named source identity, corrupted object, or missing inspection record; do not select a more favorable scene.
- Recheck trigger: When official Artemis II SPICE becomes actually available, re-attest dimensions E and F. New trajectory geometry may change E; it cannot by itself satisfy F.
