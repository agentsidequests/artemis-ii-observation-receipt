# Artemis II F-corona: a source-only critical review

12 October 2026. Private research and verification proposal, not a replication or scientific acceptance.

## Verdict

There is a better deeper-analysis opportunity here: **verify the observation's identity, then test which conclusions survive the measurement pipeline.** It is not justified to dismiss the existing paper, infer new dust physics, or resume broad anomaly mining from this review.

Two bounded results strengthen our analysis now:

- A published-use image has a `Moon` primary-target field in our frozen raw metadata. Its public identifier also has a nine-field metadata match to a different identifier in our complete-action cohort. This provides a concrete selection and identity stress case, not proof of mislabeled content or identical image bytes.
- An independently derived mathematical example separates robust contour-family geometry from calibration-sensitive brightness slopes. It identifies a discriminating reprocessing test, not a demonstrated error in the real image.

The review also exposes an accuracy gate for our own earlier flash-visibility illustration: observation epochs and lunar ranges must be reconciled before the 26.96-fold / 3.58-magnitude comparison is used as an established observing advantage. The conditional arithmetic is preserved; the physical interpretation is on hold. No source error has been proved.

No image or reference-figure pixels were acquired or inspected. Existing metadata was read, primary-source text was examined, and hypothetical equations were evaluated. No model was fitted to Artemis pixels, no reviewer was assigned, and no contact or publication occurred.

## 1. Fair reading of the study

Tsumura and Arimatsu's inspected v3 studies rendered RGB image `art002e009301`, using registration, stellar response checks, a dark-lunar-region offset, masking and relative analysis. It reports flattened morphology and steeper profiles, relates the F-corona to inner zodiacal light, and acknowledges model degeneracy. Absolute surface brightness is not calibrated. Those are substantive precautions, not an unqualified interpretation of a pretty photograph. [Author manuscript, sections II-V](https://arxiv.org/html/2604.13908v3).

The manuscript is dated 21 May 2026; the publisher index identifies ApJL 1004 L16, published 9 June, [DOI 10.3847/2041-8213/ae71c8](https://doi.org/10.3847/2041-8213/ae71c8). Direct publisher access failed. Journal-byte parity and correction/retraction status remain unknown; no withdrawal notice was observed in the current arXiv history. This is a critical reading of the identified manuscript and available indexed journal passages, not a referee report on independently replayed results.

## 2. A real source-selection and identity witness

The preserved Flight Day 6 raw-metadata page contains these records:

| Public/archive stem | Camera file number | Shutter count | Recorded UTC | Primary target | In the complete-action manifest? |
| --- | --- | ---: | --- | --- | --- |
| `art002e009301` | `0860` | 3037 | 2026-04-07 01:06:19.780 | `Moon` | No exact stem match |
| `art002e015991` | `0860` | 3037 | 2026-04-07 01:06:19.780 | `Moon` | Yes, three representations |
| `art002e015990`, adjacent control | `0859` | 3036 | 2026-04-07 01:06:18.600 | `Moon` | Yes, three representations |

The first two additionally share serial `3920019`, ISO 1600, 35 mm focal length, continuous exposure-bracketing mode, bracket order `0,-,+` and bracket value `+2`. That is nine matching operational fields including the three in the table. Both carry activity `28_Eclipsed Moon (2/2)`. The control differs in shutter, camera file number, time and bracket value.

The second and third stems are positions five and four of the same reconstructed five-exposure action, `a2-action-1c22cc639e2f4792a76b8ca4`. These are frozen metadata and manifest observations, not pixel comparisons or independently calibrated exposure boundaries. Input paths, hashes, exact extracted records and checks are retained in the companion receipt.

### What follows, and what does not

**Selection:** a query restricted to the retained primary field, `target_id == Sunset`, rejects the paper's identifier in this metadata snapshot. The published use supplies the research-topic connection; we have not independently judged the depicted emission. Primary target, observing activity and a later scientific use are different concepts. This is not proof that NASA should replace `Moon` with `Sunset`, or that a tag is wrong. NASA's [Data User Guide, Table 17](https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf) already distinguishes primary and other targets and warns about incomplete, unverified tagging. Our frozen query did not request secondary targets. This countercase does not audit the PDS search interface, prove that a native primary-plus-secondary search misses the image, or establish a missing archive feature.

**Relationship:** the two identifiers are a strong **metadata alias candidate**. They are not yet a byte-identity or physical-exposure certificate. A copied label, duplicated metadata, identifier mapping or other provenance process could explain the agreement. Comparing like-for-like source hashes and original-file lineage would discriminate some of those possibilities. Different representation hashes would not, by themselves, refute a shared exposure.

**Scope correction:** the initial exact-ID miss must not be called a missing scientific observation. A corresponding candidate is already in the cohort under another stem. Conversely, we cannot silently merge the two identifiers or change a denominator on metadata agreement alone. Existing counts remain exact for their frozen filename-defined keys and contracts. No archive-wide alias prevalence or actual split leakage is established.

The three identifiers have no exact match in the proposed 48-unit pilot crosswalk. That limited check does not certify scene independence or complete exposure-history blinding.

### Remaining access boundary

The web reader could not retrieve the two exact source XML labels. A bounded direct fetch returned HTTP 403 for both, and one three-ID read-only Atlas search also returned 403. No image endpoint was fetched. Native source hashes, original-file lineage, current availability and the public JPEG-to-NEF derivation therefore remain unresolved. This is an access boundary, not evidence of absent or defective data.

## 3. A useful mathematical distinction: shape versus brightness law

The following is our own conditional analysis, not a reported Artemis measurement.

Let an intensity field be \(F(x)>0\), with a spatially uniform, strictly increasing transformation \(g\). Then

\[
\{x:F(x)\ge t\}=\{x:g(F(x))\ge g(t)\}.
\]

Thus the **family of level-set shapes** and rank ordering are invariant to such a transformation. Global positive gain, an unclipped global offset and a positive power-law tone curve satisfy this condition. It is not a new astrophysical discovery; it is an elementary property that helps choose a less fragile measurement.

Important limits:

- A fixed displayed or normalized intensity threshold need not select the same contour after a transformation. A single reported flattening value is not automatically invariant. Compare corresponding contours or ranks under a fixed mask.
- Clipping, quantization ties, local processing, changing masks, spatial gain or spatial background can break the required assumptions.
- Preserving an apparent shape does not establish its physical origin, absolute brightness or a dust-density law.

For a hypothetical radial law \(F(r)=A r^{-q}\) and encoded signal \(D=F^\Gamma\),

\[
-\frac{d\log D}{d\log r}=\Gamma q.
\]

The apparent slope changes while the contour family can remain unchanged. Inverting an appropriate known response can recover the original slope; assuming the response or using an inappropriate model cannot.

## 4. Background subtraction and tone inversion need not commute

Suppose a background \(B\) is added **before** a nonlinear encoding:

\[
D=(F+B)^\Gamma.
\]

If its encoded value \(B^\Gamma\) is subtracted and the remainder is then inverted, the result is

\[
\widetilde F=\left[(F+B)^\Gamma-B^\Gamma\right]^{1/\Gamma},
\]

which generally differs from \(F\). Inverting first and subtracting the actual pre-encoding background recovers \(F\) under this idealized model.

Take entirely hypothetical dimensionless values: \(F(r)=8r^{-3}\), radii 1 and 2, \(B=1\), and \(\Gamma=0.75\). The two true intensities are 8 and 1. Subtracting in the encoded domain before inversion gives approximately 6.7681 and 0.6001. The inferred two-point slope magnitude is **3.49555 instead of 3**.

| Hypothetical treatment of the same underlying two-point profile | Recovered slope magnitude |
| --- | ---: |
| Correct idealized inversion and subtraction | 3.00000 |
| Encoded-domain subtraction, then inversion | 3.49555 |
| An unremoved constant background of 0.5 in the linear domain | 2.50250 |
| Outer-point gain 0.8 relative to inner-point gain 1 | 3.32193 |

These are mathematical sensitivity witnesses, not fitted effects or proposed corrections for the published image. Hard negatives recover slope 3 when \(B=0\) or \(\Gamma=1\). If the offset is instead added **after** encoding, subtracting that offset before inversion can be correct. An empirical calibration may also absorb some processing effects. Section order in a manuscript does not prove execution order in its code.

The review question is therefore precise: **what forward response, offset location, fitted intercept and operation order were implemented, and does that transfer remain valid for faint diffuse signal?** No error by the authors is established. No two-dimensional brightness slope is converted here into a physical dust-density exponent.

## 5. Other tests worth asking for

### Epoch-specific geometry, including our earlier illustration

The [manuscript's Figure 1 and Table 1](https://arxiv.org/html/2604.13908v3) give an apparent lunar diameter of 16.9 degrees, while the caption invokes an altitude of about 6,545 km. The body places the image later than closest approach. Those descriptors should not be combined as one observing epoch without clarification.

Using [NASA's approximate lunar radius](https://science.nasa.gov/moon/facts/) of 1,740 km and a spherical Moon,

\[
d=\frac{R}{\sin(\theta/2)},\qquad h=d-R.
\]

The stated diameter conditionally implies center distance about **11,841 km** and altitude about **10,101 km**. An altitude of 6,545 km instead predicts diameter about **24.247 degrees**. The caption may be closest-approach context rather than an intended image-range measurement. This check does not validate an ephemeris, the stated angular size or a source error.

There is also an accuracy gate for our own analysis: [NASA's preliminary-report feature](https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/) still reports about 46,000 miles during the flash observations. Interpreted as center distance, that is about 74,030 km and predicts only 2.694 degrees under the same spherical model. The flash-range claim and the paper's later-image descriptors cannot simply be equated; exact epochs, range definitions and authoritative geometry need reconciliation. We do not infer the flash range from this photograph or decide which source is wrong.

Our earlier 26.96-fold / 3.58-magnitude visibility illustration remains arithmetic conditional on the source-reported 46,000-mile value. **Do not carry it into publication or outreach as an established epoch-specific observing advantage until this gate is resolved.** Historical inputs and calculations are preserved, not silently replaced. The detected-count ledger, metadata findings and absence of calibrated flux are unaffected.

### Stellar calibration versus diffuse-signal validity

A global stellar relation should be checked for residual dependence on position, color, aperture and signal level before being used as a spatially uniform diffuse response. As a toy mechanism, a residual gain \(G(r)\propto r^{-\delta}\) changes a linear-domain slope from \(q\) to \(q+\delta\). That is a possible nuisance mechanism, not evidence that this camera actually has it.

Cardiel et al. define a camera-independent RGB standard from median sensitivity curves and discuss conversion to particular camera systems. A standard-star catalog is a useful reference, not a supplied Nikon/window spectral calibration. [Native author text, sections 5.2-5.4](https://arxiv.org/html/2103.17009v1), [journal identity](https://doi.org/10.1093/mnras/stab997). The guide's sections 3.1.2, 3.1.3 and 5.2.4 independently document window and processing/calibration limits. This motivates residual checks; it does not negate empirical calibration.

### Model extrapolation versus model failure

The underlying ZodiSURF publication explicitly limits its calibrated reliability to Sun angles above 80 degrees. Its code can run outside that domain, which is not validation there. [SKYSURF-11 v2, section VI and Appendix B](https://arxiv.org/html/2510.18231v2). A successful low-angle fit would need its own validation and nuisance analysis, not borrowed large-angle uncertainty. A disagreement outside the supported domain is not, by itself, evidence of new dust physics. This limitation is already recognized in the F-corona study, so it is not our discovered flaw.

### Agreement versus independence

Three color channels share a capture, optics, scene and processing lineage. Their agreement can constrain a hypothesis, but does not make three independent observing events. Adjacent frames and bracket exposures are valuable for a consistency check without becoming independent physical replications. A different instrument requires a commensurate time, geometry, passband and mask before a missing feature can be treated as a refutation.

Pixel scatter, uncertainty in a profile mean, uncertainty in a fitted parameter and a systematic envelope are separate objects. Request the relevant covariance and nuisance treatment; do not automatically relabel a displayed scatter bar as an error or a parameter confidence interval.

## 6. The smallest warranted deeper-analysis route

This is a **bounded-test proposal**, not authorization to acquire or reprocess images.

1. **Reconcile epochs and ranges before public integration.** Resolve what each source's distance or altitude describes and tie any retained visibility illustration to the flash-observation interval. Prefer authoritative time-indexed geometry over combining descriptors from different epochs. If the range cannot be qualified, retain the illustration only as hypothetical arithmetic or omit it from the public argument. Do not infer flash geometry from the later photograph.
2. **Resolve identity and selection.** Use the existing all-day metadata to census matching camera-native identity candidates, retaining conflicts and an adjacent-shot hard negative. Do not deduplicate on a filename miss or metadata match alone. Seek like-for-like source checksums and original-file lineage only through an available authorized read route. Stop the byte-identity lane while access remains denied.
3. **Freeze the physical question and measurement contract.** Choose contour-family morphology, relative brightness slope or physical density inference separately. Name the representation, masks, region, coordinate registration, response model, negative controls, sensitivity endpoints and claim ceiling before looking at new pixels.
4. **Qualify a minimal paired-representation check.** A verified source exposure and its published/rendered counterpart would be the smallest useful unit. The identified five-exposure action is a possible later extension for response consistency, not five independent events. First establish availability, bytes, decoder support, provenance and explicit pixel authority; do not install software or imply a download budget here.
5. **Test transformations that predict different outcomes.** Hold registration and mask fixed when testing global tone/offset changes. Test spatial nuisance fields separately. Keep the contour-family/rank endpoint distinct from fixed-threshold flattening and brightness slopes. For any pixel result, report the parameter and mask sensitivity envelope, not just a favorable render.
6. **Escalate to physical inference only if warranted.** Require qualified imaging/statistical review and evidence that response, background, spectral and model assumptions are sufficiently constrained. If not, retain a bounded morphological result or retire the quantitative lane. A wider prior-art review may still be needed before any novelty or public contribution claim.

Before publication or outreach, the strongest accuracy gate is source-only epoch/range reconciliation, because it could change our own visibility illustration. The metadata-only identity census remains an independent useful edge that can change our graph, selection and future split design without acquiring images. Its oracle is candidate provenance and conflict detection, not physical duplicate certification. The source-only mathematical checks already justify a calibration-order question; they do not justify retuning the real data until a result looks different.

## What can be recommended now

For a later specialist discussion, propose a question-linked crosswalk between public photo IDs, native original-file/camera identities, source/raw/processed products and declared analysis roles. Keep aliases, transformation lineage, primary/secondary target semantics, selection rules and unresolved provenance visible. Accompany any relative-profile result with the exact response and background recipe, masks, registration and a systematic-sensitivity receipt.

These are reviewable proposals, not a claim that NASA lacks provenance infrastructure or that the paper is wrong. The existing four-function analysis gains a concrete natural-use example and a sharper measurement gate. It does not gain a new lunar impact, lofted-dust discovery, calibrated brightness, physical-density result, actual leakage finding or NASA acceptance.

## Companion and source custody

The delivered [source-only receipt](../paper-review/fcorona-source-only-receipt.json) preserves the metadata witness, hypothetical constants/results, limits and source identities. Canonical copies and deterministic checks remain in the private Testbed. The article, specialist packet, audit rubric and prior scientific receipts are not silently revised by this review.

Primary texts inspected: F-corona arXiv v3 and indexed publisher passages; Cardiel arXiv v1 sections relevant to RGB standards; SKYSURF-11 arXiv v2 sections relevant to domain and code limits; preserved NASA/PDS guide and metadata. Direct publisher/correction access is incomplete; version and correction status limits are retained rather than replaced by a search-result absence claim. These texts supply evidence and questions, not endorsement or qualified acceptance.
