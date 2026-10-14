# Artemis II flash range and epoch reconciliation

12 October 2026. Source-only audit of a reported distance and our earlier numerical illustration. Not flash photometry, an independent navigation solution or NASA acceptance.

## Decision

Retire the earlier **26.96-fold / 3.58-magnitude comparison as an established Artemis flash-observation advantage**. Its inverse-square arithmetic was correct conditional on NASA's feature-reported 46,000-mile value, but that input does not replay the navigation ranges at the retained clear flash-report epochs.

The current essay, evidence-accounting brief, specialist packet and outreach drafts already omit that numerical comparison. They need no numerical deletion. Historical Stage 11N inputs and results remain unchanged as reproducible records of the earlier conditional calculation; this audit supersedes that calculation's physical interpretation, not the five-event count or the no-calibrated-flux boundary.

A delivery check found that the older flash brief and its Documents index still promoted the comparison. Both now carry explicit supersession notices; the brief's range paragraphs are qualified, and the older distance-advantage chart is marked historical and not for publication. The chart file and original scientific receipts are retained. See the [updated legacy index](../../EVIDENCE-MAP.md) and [qualified flash brief](../../ARTEMIS-II-FLASH-ANALYSIS-BRIEF.md).

This is a reproducible **source discrepancy at matched report epochs**, not proof of how the discrepancy arose. Do not silently replace 46,000 with 4,600, use closest-approach altitude as flash distance, or manufacture a larger received-flux claim.

## 1. Sources and the time contract

NASA's [preliminary-report feature](https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/) still attributes the flash observations to a distance of about 46,000 miles in Chapter 1 and the annotation caption. This audit checked that live wording on 12 October. The prior preserved feature hash remains in Stage 11N; today's whole-page bytes were not reacquired or asserted identical.

The strongest geometry source found was the [NASA/JPL Horizons Artemis II identity record](https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND=%27Artemis%20II%27&MAKE_EPHEM=%27NO%27). It identifies spacecraft **-1024**, gives an object revision of 20 April 2026, and describes post-launch trajectory data from NASA/JSC navigation. The listed `Orion_OEM_20260408_0223.V0.1` segment covers the queried flyby epochs. The native query headers identify `Artemis_II_merged` and lunar ephemeris `DE441`.

Eight discrete times were frozen before acquisition: a near-closest-approach context time, four clear transcript report anchors, one ambiguous report, the annotation scene/ledger time, and the published photograph's metadata time. The four clear anchors are reproduced directly in the original PCD3 transcript. They are not a one-to-one mapping of all five annotated events or exact photon-emission times.

The explicit Horizons `TIME_TYPE=UT` is UTC for these modern dates, as documented in its [time specification](https://ssd.jpl.nasa.gov/horizons/manual.html#time) and the native output footer. The API's printed fractional seconds are replay precision, not certified spacecraft-clock or navigation uncertainty.

## 2. Observed ranges

Distances below are rounded from the preserved native output. Altitude uses the output's spherical lunar radius of 1,737.4 km. It is not a topographic height measurement or an event-to-spacecraft distance.

| Recorded UTC | Role | Distance to Moon's center, km | Spherical altitude, km | Center distance, miles |
| --- | --- | ---: | ---: | ---: |
| 6 Apr 23:00:00 | Context near closest approach | 8,282 | 6,545 | 5,146 |
| 7 Apr 00:41:00.680 | First clear report | 10,731 | 8,994 | 6,668 |
| 7 Apr 00:51:15.947 | Shared report | 11,178 | 9,441 | 6,946 |
| 7 Apr 00:59:18.291 | Later clear report | 11,543 | 9,806 | 7,173 |
| 7 Apr 01:03:04.906 | Last clear report | 11,719 | 9,981 | 7,282 |
| 7 Apr 01:06:19.780 | Published photograph, not a flash time | 11,872 | 10,134 | 7,377 |

Thus the nominal center ranges at the four retained clear report epochs are about **10,700 to 11,700 km**, or **6,700 to 7,300 miles**. This is a discrete-epoch result, not a continuous interval bound or four newly confirmed impacts.

The eight-row companion retains the ambiguous anchor and annotation context separately rather than converting them into additional events.

## 3. Why a distance convention does not explain the discrepancy

46,000 statute miles is about 74,030 km. For any point on the adopted spherical surface at a queried epoch, triangle inequality gives

\[
d-R\leq \lVert\mathbf{s}-\mathbf{p}\rVert\leq d+R,
\]

where \(d\) is the spacecraft-to-center range, \(R=1,737.4\) km, and \(\mathbf{p}\) is a spherical surface point. This is a deliberately broad geometric envelope, not an assigned flash location.

The largest upper endpoint among the four clear report anchors is **13,456 km**, far below 74,030 km. Interpreting the feature's number as altitude rather than center range would make its center range larger, not reconcile it. Converting statute miles to kilometres, changing center to surface, or retaining light-time corrections does not account for this gap at these nominal epochs.

The review does not identify the feature's intended replacement number, its editorial mechanism, the exact range of each annotated impact or a formal navigation uncertainty. A qualified source correction or additional event mapping remains welcome; the unsupported physical use of our old calculation need not wait for that correction.

## 4. The photograph and closest approach are different epochs

NASA's [flyby visualization description](https://svs.gsfc.nasa.gov/5633/) assigns the approximately 6,545-km altitude to closest approach. The sampled 23:00 UTC navigation context reproduces that rounded value. It does not locate the exact mathematical minimum of the trajectory.

At the public photograph's 01:06:19.780 UTC metadata epoch, the geometric center range is about 11,872 km and the spherical altitude about 10,134 km. The separate observer query gives an apparent lunar diameter of **16.831 degrees**, near the [F-corona manuscript's approximately 16.9 degrees](https://arxiv.org/html/2604.13908v3). We did not recover the authors' exact Horizons request or source version; that is not exact numerical reproduction of their value. Their approximate angular size and the much earlier closest-approach altitude must not be used as interchangeable image geometry.

This supports a caption/epoch clarification, not a demonstrated calibration, profile or dust-density error in the paper. No photograph or reference-figure pixels were inspected.

## 5. A related chronology caveat

The feature also places the impact-flash observations during a planned communications blackout. NASA's [live flyby update](https://www.nasa.gov/blogs/missions/2026/04/06/artemis-ii-flight-day-6-lunar-flyby-updates/) instead reports Earthrise and communications restoration shortly after 7:24 p.m. Eastern on 6 April, corresponding to approximately 23:24 UTC. Its eclipse entry is 8:35 p.m. Eastern, or 00:35 UTC on 7 April. The retained clear flash-report anchors begin at 00:41 UTC, later than that reported restoration.

Do not import the feature's blackout wording into our narrative as the chronology of these retained reports. This is a nominal source-chronology discrepancy, not a complete reconstruction of radio coverage or proof that no earlier sighting occurred. The preliminary report's eclipse description and exact transcript anchors remain the stronger entry for this analysis.

## 6. What this changes, and what it does not

- **Changed:** the earlier conditional 26.96 / 3.58 result is no longer eligible as an established Artemis observing advantage. The unresolved range gate is discharged by rejecting that physical use, not by assigning every flash a new distance.
- **Preserved:** five accepted annotated sightings, unresolved event-level timing and locations, the attention-conditioned observation analysis, the later camera interval, the clip sensitivity ceiling, metadata findings, and the absence of a calibrated impact-flux estimate.
- **Not substituted:** a new brightness, limiting magnitude, impactor size, physical detection probability or received-flux advantage. Range alone does not supply those quantities. Comparing a far-side flash with an actual Earth observation also requires visibility, not just an inverse-square ratio.
- **Not established:** NASA acceptance, an independent navigation reconstruction, a continuous range bound, the precise cause of the source discrepancy or a new lunar-science discovery.

For a later qualified source review, the explicit recommendation is to bind any quoted observing distance to a UTC epoch or bounded interval, source trajectory/revision, center-versus-surface convention and event/report distinction. Recheck the feature's 46,000-mile and blackout descriptions against the retained eclipse report epochs. Nothing has been sent.

## 7. Replay, evidence and acceptance

The [machine-readable receipt](../../paper-review/range-geometry/result.json) includes every queried epoch, computed range, claim limit, acquisition hash and request parameter. Canonical source responses, requests, helper and receipt are privately retained under `paper-review/range-geometry/` in the owning Testbed.

From that repository, the offline command is `python -B -m src.fcorona_range_reconciliation`, using the qualified Python 3.13 runtime. No network request, image decoder, installation or external effect is part of replay. Source acquisition is a separate bounded read-only helper that refuses to overwrite existing evidence; do not rerun it merely to verify the frozen result.

Verification recomputes range and range-rate from native Cartesian states, reverses target/center and checks state negation, compares geometric and apparent range, and replays the observer angular diameter from its stated radius and range. Native PowerShell separately reproduces the eight Cartesian norms, reciprocal states and clear-anchor range endpoints. These are implementation-diverse and configuration checks, not independent scientific solutions; all queries share the same navigation trajectory.

Sixteen focused tests cover exact bytes, prior anchor custody, wrong center, wrong units, TDB/UTC substitution, changed time, missing rows, incomplete tables, non-finite values, range/state disagreement, reciprocal queries, observer units, the surface-distance envelope and prohibited inference. The full Testbed regression result is recorded separately in `VERIFICATION.md` before the checkpoint is committed. Structural replay does not replace qualified navigation, lunar-impact or editorial acceptance.

The external-source disposition is a bounded source-consistency test in the existing Artemis owner. This is project-local preservation only, not a global operating-method or capability claim.
