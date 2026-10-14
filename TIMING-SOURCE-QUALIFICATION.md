# An image time is not a ledger-creation time

12 October 2026. Public-candidate qualification, based on preserved primary sources. This narrows an earlier interpretation without changing the measured camera timestamps, accepted-event counts, transcript anchors, or injection results.

## What the sources support

The annotated graphic identifies its background image as `art002e016252` and displays **7 April 2026 01:04:00.000**. The PDS annotation product is a `Product_Document`; its label identifies publication on 7 October, not an assembly time during the flyby. NASA's preliminary report, pages 34-35, describes an annotated image prepared by the crew and downlinked to the Lunar Science Team after the flyby. Its text does not certify that the five-event ledger was complete at the background-photo epoch. [NASA report](https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/).

Preserved evidence: [annotation label](evidence/stage11n/source/art002e016252_pcd_ann_v01.xml), [annotated graphic](evidence/stage11n/source/art002e016252-impactflash-annotation-cropped.jpg), [report extract](evidence/stage11n/source/artemis-ii-preliminary-report-flash-pages.txt).

## Correct disposition

| Item | Supported use | Unsupported promotion |
| --- | --- | --- |
| 01:04 background-photo/context epoch | Identify the displayed scene and compare metadata times. | Treat it as certified ledger creation or an upper bound for all five event times. |
| Video start 01:19:13 | It is 913 seconds after the background-photo epoch and follows the retained clear report anchors. | Certify that it missed every numbered accepted event without an event-to-report mapping or event-level bounds. |
| Later video null | Retain NASA's limited-interval no-flash assessment. | Use an unverified all-event chronology as a proof of coverage or noncoverage. |
| Overlapping 15-second clip and weak injection recovery | Contextual overlap with one report; the frozen screen has poor clip-native sensitivity. | Event confirmation, exclusion, physical brightness, or calibrated impact flux. |

The corrected public app's negative timing proposition concerns the **background-photo epoch**, not all accepted events. Its old claim identifier is retained for source comparison, but the displayed proposition, fact name, and ceiling state the narrower meaning. A 913-second arithmetic check is not a scientific event-coverage certificate.

Historical Stage 11N receipts preserve the earlier `annotation_ledger_utc` terminology and assumptions. Their saved pass flags do not settle this clock-semantic issue. The current prototype fixture and saved outputs now use the narrower background-photo proposition, matching the app. The old flash timeline graphic is withheld from the current public candidate, as is the previously withdrawn distance-advantage graphic. The legacy renderer's CLI and imported main/timeline/distance entry points are disabled before output writes.

Required discriminators for a stronger claim: the annotation assembly history, numbered-event UTC intervals or uncertainty bounds, and a qualified mapping to transcript reports. Until then, coverage of every accepted event is **UNESTABLISHED**, not inferred from the photograph's time.

This does not assert that a confirmed flash occurred during the later video, that NASA's null assessment is wrong, or that the five-event classification is false. It rejects our stronger timing inference. No specialist or NASA acceptance is claimed, and no contact was made.
