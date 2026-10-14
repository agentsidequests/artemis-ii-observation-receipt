# Stage 9A source screen — archive-wide opportunity selection

**Access date:** 9 October 2026
**Decision question:** Can any untested archive relation beat a truthful synthesis or deliberate stop without reopening a closed lane?
**Disposition:** `ADMIT_NO_PIXEL_SOURCE_CONTROL_GATE`

## Selected signal

At `23:22:39 UTC`, immediately before/during Earthrise, Christina Koch asked whether a gray feature was lofted lunar dust. Reid Wiseman answered that he thought it was mountains; Koch said it might be an optical illusion. NASA's preliminary report preserves the disagreement, calls the episode a potential sighting, and concludes that no lofted dust or exospheric glow was definitively detected.

This is materially different from the exhausted reflectance lane:

- it is a transient edge-of-limb event, not a static surface-albedo judgment;
- it has an exact time and competing explanations stated at observation time;
- the repository already holds an external SAW Cam 3 sequence at `23:22:14`, `23:22:44`, and `23:23:14 UTC`, with the middle frame only five seconds after the utterance;
- the external camera is independent of the cabin window but is not assumed to have equivalent sensitivity or viewpoint; and
- the result is valuable in either direction if the oracle remains causal-discrimination rather than dust confirmation.

The direct baseline does **not** settle this event. NASA explicitly leaves it unresolved. A bounded current search located no public analysis of this exact `23:22:39 UTC` feature; that is `NOVELTY_UNESTABLISHED`, not proof of priority.

## Why it matters

The lunar horizon-glow record is scientifically unsettled. LADEE found a persistent impact-generated dust cloud but NASA summarizes its result as no evidence for an electrostatically lofted effect visible to the human eye. LRO/LAMP, Clementine, and broad LADEE searches place strong upper limits on a persistent high-altitude cloud. In tension with that baseline, Xie et al. (2020) reported five localized LADEE dust-enhancement events near twilight craters, argued that sporadic local dust fountains could reconcile some Apollo observations, and identified them as a potential exploration hazard.

That literature does not validate the Artemis II feature. It makes a correctly controlled classification of this exact observation decision-relevant.

## Candidate comparison

| Family | Direct-source state | Missing discriminator | Disposition |
| --- | --- | --- | --- |
| Pre-Earthrise gray feature | NASA leaves the event unresolved; exact external-camera coverage already exists | Exact cross-carrier inventory, sensitivity boundary, and terrain/illumination controls | **Admit source/control gate** |
| Activity-metadata integrity | One five-frame tag inconsistency is verified locally | Full label-only denominator and a content-independent truth rule | Hold second |
| Camera clocks | NASA reports opposite-sign `+14.2 s` and `-24.5 s` image/render offsets | Released event-specific geometry capable of separating camera clocks from ephemeris | Hold for SPICE or stronger clock oracle |
| Corona pulsation | NASA already pairs the crew view and annotation with SOHO one minute later | A distinct prospectively defined dynamics endpoint | Stop direct-baseline corroboration |
| Moonlit full-disk Earth | NASA already identifies the major natural and human features | Calibrated quantitative endpoint that one high-ISO image can support | Stop feature inventory |
| Reiner Gamma | NASA already publishes the description and an LROC comparison | A human-stimulus-equivalent representation and distinct scientific question | No admission |
| Limb/terminator morphology | NASA already frames the value for future polar imaging | Event-specific line of sight and human viewing path | Hold for SPICE |
| Operational adaptation | NASA already documents the broad mechanism | Matched causal counterfactual | Synthesis only |

## Source identities and limits

1. **NASA, Artemis II Preliminary Science Report.** NTRS `20260009221`; distribution date 7 October 2026; downloaded from the NTRS primary artifact on 9 October 2026. Local research copy: `143,769,154` bytes, SHA-256 `edf4a22f7451b404c7eb85210e357bd5809a34aff79b07ccf8d57a9ca53748fa`. Decision-bearing locations: §5.5.1 (pp. 62–64), §5.5.3 (pp. 65–66), §7.6 (pp. 104–105), §8.1–8.2 (pp. 106–109), and §9.9 (pp. 115–117). <https://ntrs.nasa.gov/citations/20260009221>
2. **NASA, Artemis II Lunar Science Operations Report.** NTRS `20260009223`; distribution date 7 October 2026; downloaded from the NTRS primary artifact on 9 October 2026. Local research copy: `38,473,199` bytes, SHA-256 `64339869c8a1c41dde273cf1b507a0827e93a881390e4af4c16a5f2f44b00cf5`. It establishes the direct operational baseline and recommendations; it does not resolve the gray feature. <https://ntrs.nasa.gov/citations/20260009223>
3. **Artemis II Lunar Science Data User Guide v1.0.** Released 7 October 2026; local research copy `8,320,046` bytes, SHA-256 `c4f5ab25363ca3f8fc17bb776e9fc90c19707c8a18c9255648aef34d6a7b0bd2`. It establishes archive carriers, processing, clock semantics, and current tooling. <https://assets.science.nasa.gov/content/dam/science/missions/artemis/artemis-ii-prelimsci-report-/artemis2_data_user_guide.pdf>
4. **NASA PDS Artemis II mission page.** Current on 9 October 2026. It establishes that crew-camera, Orion-camera, and mission-audio bundles are available while the SPICE bundle is delayed. <https://pds-geosciences.wustl.edu/missions/artemis2/index.htm>
5. **NASA LADEE retrospective.** Updated 3 August 2023. It states that LADEE detected impact-ejected lunar dust but no effect of the proposed electrostatically lofted kind that would be visible to the human eye. <https://www.nasa.gov/general/what-is-ladee-the-lunar-atmosphere-and-dust-environment-explorer/>
6. **Horányi et al. (2015), _A permanent, asymmetric dust cloud around the Moon_.** DOI `10.1038/nature14479`. Primary LADEE/LDEX paper establishing a persistent impact-generated cloud and no dense global Apollo-like cloud. <https://doi.org/10.1038/nature14479>
7. **Szalay and Horányi (2015), _The search for electrostatically lofted grains above the Moon with the Lunar Dust Experiment_.** DOI `10.1002/2015GL064324`. Reports upper limits roughly two to three orders below Apollo-based expectations under the studied conditions. <https://doi.org/10.1002/2015GL064324>
8. **Xie et al. (2020), _Lunar Dust Fountain Observed Near Twilight Craters_.** DOI `10.1029/2020GL089593`. Reports five localized LADEE enhancements and proposes a sporadic, crater-linked mechanism; this is the strongest countercase to treating global non-detection as a universal absence result. <https://doi.org/10.1029/2020GL089593>

## Claim ceiling and next proof

Stage 9A selects a question; it discovers no dust. The next proof must remain no-new-pixel until it binds exact products, viewpoints, exposure/sensitivity proxies, terrain and illumination controls, and a fail-closed outcome set. A later image can support only one of these archive-level states:

- `NO_EXTERNAL_ANOMALY_AT_AVAILABLE_SENSITIVITY`;
- `EXTERNAL_ANOMALY_INDETERMINATE`;
- `RIGID_TERRAIN_OR_EARTH_LINKED_OPTICAL_PATTERN`;
- `SOURCE_CONTROL_INSUFFICIENT`.

No state alone identifies lunar dust. A positive external anomaly would only justify qualified specialist review and event-specific geometry.
