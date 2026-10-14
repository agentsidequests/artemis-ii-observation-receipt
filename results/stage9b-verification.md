# Stage 9B — Gray-Feature Source/Control Gate

- Verification: `PASS`
- Evidence state: `VERIFIED_SOURCE_CONTROL_STOP`
- Disposition: `SOURCE_CONTROL_INSUFFICIENT`
- Lane state: `CLOSE_GRAY_FEATURE_IMAGE_LANE_AT_CURRENT_ARCHIVE_BOUNDARY`
- New candidate-pixel bytes opened: `0`

## Result

The exact event source is PCD3 product `art002a000015`, not the overlapping PCD2 transcript previously present in the Stage 0 corpus. A bounded archive query found 40 Nikon D5 raw frames from `23:22:37.530` through `23:22:49.330 UTC`. Five exposure-bracket frames begin `0.020–0.390 s` after Koch's `23:22:39.010 UTC` report.

That unusually strong synchronization does not admit pixel inspection. The same recording documents persistent cabin reflections; the exact operator, eye/viewfinder state, and window path are not product-bound; the window stack lacks an event-specific optical model; the SPICE bundle is delayed; and the only near-time external frame is a different-viewpoint GoPro exposure at `+4.990 s`, ISO 100, about `0.000384 s`, and `-2 EV` with no faint-source sensitivity equivalence. NASA itself recommends a dedicated low-light limb camera for confident dust detection or non-detection.

Therefore the current archive cannot distinguish all four required causes. The gray-feature image lane closes as `SOURCE_CONTROL_INSUFFICIENT` without opening event pixels. This is not evidence that dust was or was not present.

## Control dimensions

- `A_exact_event_and_recorder_identity`: `PASS`
- `B_synchronous_internal_camera_coverage`: `PASS`
- `C_earth_emergence_temporal_progression`: `PASS`
- `D_rigid_terrain_control`: `PARTIAL`
- `E_observer_window_carrier_binding`: `PARTIAL`
- `F_cabin_window_optical_control`: `FAIL`
- `G_external_comparable_carrier`: `FAIL`
- `H_event_geometry`: `FAIL`
- `I_calibrated_faint_source_response`: `FAIL`

## Claim ceiling

Stage 9B establishes the exact PCD3 event transcript, a synchronized five-frame D5 exposure bracket inside a 40-frame cabin sequence, one near-time external SAW frame, and the missing controls that prevent four-way causal discrimination. It does not inspect event pixels, establish what any frame shows, detect or exclude lunar dust, refute Koch, validate an external anomaly, or make a public scientific finding.

## Hard negatives

- `substitute_overlapping_pcd2_for_exact_pcd3_event_source`: REJECTED
- `treat_time_alignment_as_operator_and_window_binding`: REJECTED
- `open_candidate_pixels_after_source_control_failure`: REJECTED
- `treat_external_camera_absence_as_refutation_without_sensitivity_equivalence`: REJECTED
- `treat_any_external_feature_as_lunar_dust`: REJECTED
- `ignore_documented_cabin_reflections`: REJECTED
- `promote_partial_terrain_control_to_exact_event_geometry`: REJECTED
- `let_spice_alone_repair_window_and_sensitivity_gaps`: REJECTED
- `treat_synchronized_d5_burst_as_calibrated_low_light_measurement`: REJECTED
- `claim_source_control_insufficiency_means_no_lunar_dust`: REJECTED

## Next-step logic

- Recommended: Return to a truthful synthesis centered on the measurement-design gap: Artemis II produced a precisely timed human anomaly report and a synchronized cabin image burst, but not the calibrated, geometry-bound independent carrier required to adjudicate it.
- Fail action: Keep every gray-feature candidate pixel closed and close this image lane at the current archive boundary.
- Secondary: The label-only activity-metadata integrity candidate remains eligible because it does not depend on this lane.
- Recheck trigger: Reopen only if a source changes the failed dimensions—for example an event-bound operator/window record plus optical characterization and a calibrated comparable external low-light carrier. SPICE alone can improve geometry but cannot satisfy the optical or sensitivity controls.
