# Bounded research note for a public Artemis II analysis

**Decision question:** Can the verified Earthrise/Earthset timing contrast support a forceful public analysis without implying that NASA missed the event, that an availability window is a physical-contact clock, or that the trajectory-offset hypothesis is already proven?

**Disposition:** Yes. The strongest public thesis is about resilient execution across metadata layers, not a planning failure. One additional matched-view comparison materially strengthens the trajectory-offset candidate, while the direct crew transcript removes the fixed external camera as the sole evidence that Earthrise occurred before the archived availability interval.

## Decision-bearing evidence

### Earthrise: the event preceded the four-second availability interval

- The archived Outgoing Target Request gives Earthrise an observation availability interval of `2026-04-06T23:25:30Z` to `2026-04-06T23:25:34.147844Z`, a width of 4.147844 seconds.
- The same record assigns a requested observation time of `23:18:00Z` and a requested duration of 12 minutes. The broader activity slot therefore covers the event even though the narrow availability interval does not.
- In the PDS crew transcript, Glover says “The first corner of Earth” at `23:21:18.957Z` and “It is completely risen” at `23:23:27.170Z`.
- The independent SAW Cam 3 sequence brackets first visibility in `(23:21:14Z, 23:21:44Z]` and full clearance in `(23:22:44Z, 23:23:14Z]`.
- The fixed-camera full-clearance bracket ends 136 to 166 seconds before the availability interval begins. The crew account independently establishes that the observation itself was underway and complete before the interval.

### Earthset: the wider availability interval overlaps the event

- The Earthset availability interval runs from `22:42:19.730197Z` to `22:45:36.380230Z`, a width of 196.650033 seconds.
- The Earthset request time is `22:38:00Z` with an eight-minute requested duration.
- In the crew transcript, Glover says Earthset is beginning at `22:40:43.102Z` and that Earth has set at `22:43:34.220Z`.
- The independent SAW Cam 3 result also verifies overlap, including at least 54.269803 seconds of guaranteed overlap under its 30-second sampling brackets.
- The Earthset availability interval is 47.410180566 times wider than the Earthrise interval. The contrast is event-specific: it rejects a uniform claim that all such intervals either contain or miss the named optical transition.

### Planning lineage and two matched-view comparisons

NASA's Lunar Science Operations Report documents this sequence:

1. the Crew Lunar Observations team received post-TLI trajectory data;
2. that ephemeris fed the Live Encounters Guide;
3. selected targets and timing data were packaged in the Outgoing Target Request;
4. the request database populated the Lunar Targeting Plan; and
5. the final crew-facing plan featured the post-TLI ephemeris.

The report includes two expected-versus-actual image comparisons:

- Figure 6.3 compares a crew image at `22:33:56Z` with a post-TLI visualization at `22:36:30Z`, a 154-second difference. The report explicitly says the actual trajectory moved the flyby earlier by roughly two minutes.
- Figure 6.4 compares a 400 mm crew image at `20:12:20Z` with a simulated LTP view expected at `20:15:00Z`, a 160-second difference. The paired images show the same lunar region at the same stated scale; the report uses the figure to demonstrate similarity between expected and actual views.

Both 154 and 160 seconds fall inside the independently frozen 136-to-166-second Earthrise full-clearance-to-availability-start bracket. The second comparison makes a one-example coincidence less likely, but it still does not establish a uniform correction, event-specific causality, or exact inheritance of the Earthrise field.

## Strongest countercase

The availability interval is not documented as a first-contact-to-full-clearance clock. NASA's Data User Guide calls it an observation availability window, while the targeting package and operations report keep visibility, requested observation time, duration, and operational prompts distinct. Treating the four-second interval as a failed prediction would repeat the semantic error the source material rules out.

The correct claim is narrower and more interesting: one timing layer was brittle to a roughly two-and-a-half-minute trajectory difference, while the wider requested activity slot, crew setup, direct observation, and capture system still succeeded. The archive shows resilience through layered planning and human execution, not perfection in every metadata field.

The remaining falsifier is event-specific geometry. NASA PDS still lists the Artemis II SPICE bundle as delayed. When it is released, the hypothesis fails if the Earthrise actual-versus-planned shift falls outside the frozen 136-to-166-second bracket or if the event's availability timing did not inherit the documented post-TLI planning basis.

## Prior-art boundary

A bounded current search for the exact timestamps, availability widths, and Earthrise/Earthset placement comparison found no public analysis of this precise contrast as of 9 October 2026. That supports publication value but not a global novelty or priority claim.

## Public thesis

**A four-second Artemis II availability window fell after Earthrise, yet the crew captured the event because the mission's broader activity slot and human workflow were more resilient than that one metadata field. NASA's own matched-view comparisons nominate a trajectory-offset/window-tolerance explanation, but only the delayed event-specific geometry can confirm it.**

## Primary sources

- NASA, *Artemis II Lunar Science Operations Report*, especially pp. 31 and 37-40: <https://assets.science.nasa.gov/content/dam/science/missions/artemis/artemis-ii-prelimsci-report-/Artemis%20II_Lunar%20Science%20Operations%20Report_2Oct2026.pdf>
- NASA PDS, *Artemis II Lunar Science Data User Guide*, especially §5.6.2: <https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf>
- NASA PDS, Outgoing Target Request: <https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_outgoing_target_request.json>
- NASA PDS, Flight Day 6 Earthset transcript: <https://pds-imaging.jpl.nasa.gov/archive/archive/artemis/artemis2/artemis2_mission_audio/data_transcripts_pcd/fd06/art002a000045_pcd2_trn-csv_v01.csv>
- NASA PDS, Flight Day 6 Earthrise transcript: <https://pds-imaging.jpl.nasa.gov/archive/archive/artemis/artemis2/artemis2_mission_audio/data_transcripts_pcd/fd06/art002a000049_pcd2_trn-csv_v01.csv>
- NASA PDS Artemis II mission page and SPICE status: <https://pds-geosciences.wustl.edu/missions/artemis2/index.htm>
