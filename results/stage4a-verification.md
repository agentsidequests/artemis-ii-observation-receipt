# Artemis II Observation-Execution Testbed — Stage 4A Result

- Verification: **PASS**
- Evidence state: `VERIFIED_CAPTURE_AVAILABLE`
- Admitted products: **7**
- Flash state: `UNVALIDATED_CAPTURE_CANDIDATE`
- Disposition: `NOMINATE_TINY_STAGE5_SUBSET`

The official PDS inventory contains label-timed coverage of the report interval: two SAW3 stream-channel products span the whole interval, and five Nikon Z9 raw exposures start inside it. The channel products are not two independent viewpoints, and coverage does not establish that the reported flash appears in any media.

## Admitted products

| Product | Kind | Acquisition time | Activity tag | Payload bytes |
| --- | --- | --- | --- | ---: |
| art002m1010962338_saw3_raw_v01.mp4 | continuous_video | 2026-04-06T23:38:11Z to 2026-04-07T01:37:57Z | Other | 2960238197 |
| art002m1020962338_saw3_raw_v01.mp4 | continuous_video | 2026-04-06T23:38:11Z to 2026-04-07T01:37:45Z | Other | 2921875198 |
| art002e015907_nkz9019_raw_v01.tif | raw_image | 2026-04-07T00:51:51.83Z (1s exposure) | 24_Sunset | 91412576 |
| art002e015908_nkz9019_raw_v01.tif | raw_image | 2026-04-07T00:51:53.02Z (0.25s exposure) | 25_Discussion #6: Forward Look | 91412576 |
| art002e015909_nkz9019_raw_v01.tif | raw_image | 2026-04-07T00:51:53.34Z (0.5s exposure) | 24_Sunset | 91412576 |
| art002e015910_nkz9019_raw_v01.tif | raw_image | 2026-04-07T00:51:53.92Z (2s exposure) | 24_Sunset | 91412576 |
| art002e015911_nkz9019_raw_v01.tif | raw_image | 2026-04-07T00:51:56.10Z (4s exposure) | 24_Sunset | 91412576 |

## Decision-relevant limits

The five still exposures begin about 36 seconds after the first report and before the later joint characterization. Their timing cannot establish that they captured the initially reported transient. Four are tagged `24_Sunset`; one is tagged `25_Discussion #6: Forward Look`. That split is a bounded metadata-friction finding, not pointing or impact validation.

Fetching all seven full payloads would require 6339176275 bytes (6.339 GB; 5.904 GiB). No media bytes were downloaded.

Official labels establish acquisition coverage and a bounded metadata inconsistency only. They do not show that a flash is visible, that the products point at the reported location, that the two observers saw a lunar impact, or that the 41.681-second report interval is an event duration.

## Next-step logic

**Recommended:** Run a Stage 5 transport canary for one SAW3 channel around 00:51:10Z-00:51:25Z, proving whether a tiny byte-range or server-side clip is feasible before accepting a 2.96 GB full-product download.

Why: The continuous stream is the only admitted product that spans the first report; the five still exposures begin about 36 seconds later and cannot by timing alone capture the initially reported transient. Both full video channels plus five raw frames total 6.34 GB.

Alternative: Inspect only lightweight browse/source derivatives of the five Z9 frames as camera-state and pointing controls, not as impact validation.

Fallback: If bounded video extraction is infeasible or the nominated segment lacks a usable lunar view, complete Stage 3B and retain the candidate as transcript-supported but physically unvalidated.

Stop: Do not download full media, interpret pixels, geolocate a flash, or make a public novelty claim in Stage 4A.

## Hard negatives

- `label_creation_time_is_acquisition`: REJECTED
- `derivatives_are_independent_acquisitions`: REJECTED
- `target_tag_validates_impact`: REJECTED
- `report_interval_is_flash_duration`: REJECTED
- `outside_interval_product_is_admitted`: REJECTED
