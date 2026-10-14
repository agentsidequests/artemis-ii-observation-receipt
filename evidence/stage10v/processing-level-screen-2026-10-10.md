# Stage 10V processing-level screen — 10 October 2026

## Decision this screen can change

Whether the representation-byte result should be framed as generic format multiplication or as a task-fitness constraint. The screen can determine which archived tier is admissible for a named task; it cannot calibrate the cameras, measure color, or rank one representation universally.

## Sources inspected

- NASA PDS, *Artemis II Lunar Science Data User Guide*, preserved locally at `evidence/stage10d/source/artemis2_data_user_guide.txt`, especially §§5, 5.2, and 5.2.1–5.2.4.
- NASA PDS, “Data Processing Levels (for PDS4),” version 2.0: <https://pds.nasa.gov/data/pds4/documents/policy/policy_on_data_processing_levels_v2.0.pdf>
- NASA PDS Common Data Dictionary, `processing_level`: <https://pds.nasa.gov/datastandards/documents/dd/v1/PDS4_PDS_DD_1O00/webhelp/all/ch05s732.html>

## Findings

PDS defines calibrated data as values converted to physical units so they are independent of the instrument. The Artemis II guide explicitly says no calibration has been applied and no calibrated products are provided. Its three crew-camera representations serve different purposes:

- source NEFs preserve original embedded metadata and native pixel values but use proprietary encoding;
- raw TIFFs expose the Bayer array in a non-proprietary archival form and remain uncalibrated;
- processed TIFFs are uncalibrated, interpreted, visually finished outputs produced with proprietary Nikon demosaicing, default camera settings, sRGB, and autoscaling.

The guide warns that processing may introduce artifacts or reduce fine detail and that output colors cannot be completely verified or quantified without further information, calibration, and testing. This is a representation boundary, not evidence that a particular image contains an artifact or that processed products lack scientific use.

## Decision impact

The byte ledger and the processing ladder move in different directions. Processed TIFFs occupy 67.932% of the verified complete-action cohort's 1.625-TB footprint and 68.447% of the fixed Sunset block's 200.902-GB footprint, but they do not constitute a calibrated tier. More storage and more interpretation do not imply more independent evidence or stronger measurement status.

Name the task first. Use source for native provenance, raw for open Bayer-level analysis, and processed for human-viewable vendor interpretation. Stop a quantitative physical-unit or fully verified color claim unless a separate calibration and validation design becomes available. Do not collapse these distinctions into “raw good, processed bad”: all three tiers retain a legitimate task.

## Recheck trigger

Reopen after a calibrated crew-camera collection, validated spectral response, revised processing documentation, or a specific analysis whose task requires a different representation contract.
