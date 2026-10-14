# Observation Receipt

> Historical product proposal. The current application and two cases are in `observation-receipt/` and `preview/`. This concept is not a release-acceptance certificate. The uncoached-user and qualified-review gates remain open; the local publication candidate does not silently accept them.

## Recommendation

Build a narrow, local-first open-source application for reconstructing transient observations and testing whether the available evidence actually covers a claim.

Working name: **Observation Receipt**

One-line promise: **Turn timestamped observations, media windows, annotations, and detection limits into a receipt that shows what is supported, what was not observed, and what was never measurable.**

The Artemis II flash case is a strong public demonstration because it contains nearly every important failure mode:

- multiple human witnesses;
- ambiguous and rejected candidates;
- uncertain event-to-transcript mapping;
- camera windows that overlap or miss different intervals;
- a later null that can be mistaken for an event non-detection;
- a high-frame-rate clip whose target occupies only ten pixels;
- an event count that supports a floor but not a calibrated flux;
- a null screen that fails its own frozen injection-recovery gate; and
- evidence spread across CSV, XML, PDF, HTML, audio, images, and video.

## The product gap

Existing tools cover important parts of the problem:

- **VOEvent** represents and communicates astronomical transient events.
- **IVOA Provenance** models the entities, activities, and agents that produced astronomical data.
- **RO-Crate** packages research data and metadata.
- **Label Studio** supports synchronized multimodal annotation.
- **Timesketch** supports collaborative forensic timeline analysis.
- Claim and evidence graph tools support source tracing and, in some cases, complete-capture windows.

Observation Receipt should not replace any of them. Its narrower job is to connect four things that are usually separated:

1. the candidate event;
2. the witnesses and sensors that could have detected it;
3. the time, field of view, calibration, and completeness of their exposure; and
4. the exact claim someone wants to make from the result.

Its distinctive question is not merely "what happened when?" It is "did this evidence have the opportunity and capability to test this claim?"

That difference is what prevents a later camera null from being described as a failed event capture and prevents an uncalibrated count from being presented as a survey rate.

## First user and first use case

Start with researchers, citizen-science coordinators, data journalists, and technical reviewers reconstructing a small number of cross-modal transient events from public archives.

Do not start as a generic knowledge graph, fact-checker, media-forensics suite, or AI research agent. Those markets are crowded and would obscure the strongest demonstrated capability.

The first complete fixture should be Artemis II:

- ingest the official transcript, annotation, and camera labels;
- reproduce five events and eight witness marks;
- distinguish the later 30 fps null from the overlapping 60 fps context clip;
- show the ten-pixel lunar footprint;
- reproduce the clip-native injection-recovery curve;
- compute the conservative count floor;
- block promotion to a calibrated flux; and
- export a human-readable and machine-readable receipt.

## Core data model

### Artifact

- immutable identifier
- original path or URL
- byte length and hash
- media type
- producer and archive
- clock domain
- derivation and transcode state

### Observation window

- observer or sensor
- start and stop time
- clock uncertainty
- target and field of view
- live-time state
- calibration state
- detection threshold or completeness surface
- environmental context

### Candidate event

- candidate identifier
- reported time or interval
- location or region
- structured witness marks with observer, first-mark time, and unprompted, prompted, or unknown state
- confidence and disposition
- relationship to other candidates
- accepted, ambiguous, rejected, or retracted state

### Evidence relation

- supports
- contradicts
- overlaps
- does not overlap
- lacks capability
- derived from
- same-event unresolved

### Claim

- exact proposition
- required evidence conditions
- assumptions
- supporting and limiting relations
- status
- claim ceiling
- evidence that would reopen it

### Measurement function

- monitored area
- live time
- detection probability by signal strength, position, and background
- confirmation rule
- effective area-time
- units and threshold

## Minimum viable product

### 1. Deterministic ingestion

Support CSV, JSON, XML labels, images, and user-supplied media metadata. Preserve source hashes and never silently normalize times or identifiers.

### 2. Clock-aware timeline

Display events, voice reports, annotations, and sensor coverage on one timeline. Require explicit clock domains and uncertainty before treating two records as simultaneous.

### 3. Witness and detector matrix

Show which observers or channels marked each candidate. Keep "not marked" separate from "observed and rejected" and "not exposed."

### 4. Coverage solver

For every claim, answer:

- Did the observation window overlap the event interval?
- Was the target inside the field of view?
- Was the detector capable of seeing the claimed signal?
- Was capture complete enough for absence to count as evidence?

### 5. Measurement gate

Block rate or flux promotion until the units, live time, monitored area, threshold, confirmation rule, and completeness function are present.

### 6. Receipt export

Produce:

- a one-page Markdown or HTML docket;
- machine-readable JSON;
- candidate and relation CSV files;
- a timeline chart;
- a witness matrix;
- source hashes and replay commands; and
- optional RO-Crate packaging.

### 7. Standard interoperation

- Import or export VOEvent where a real astronomical transient packet is appropriate.
- Map artifact lineage to IVOA Provenance concepts.
- Package the final case as RO-Crate.
- Keep application-specific coverage, completeness, and claim rules in an explicit extension namespace.

## Acceptance tests for the Artemis fixture

The MVP is not complete unless it passes all of these:

1. It reproduces five annotated events, eight witness marks, and three observers.
2. It refuses a one-to-one mapping between transcript anchors and numbered events without added evidence.
3. The current qualified case shows that the assessed 30 fps clip starts 913 seconds after the annotation's background-photo/context epoch. The earlier inference that this certifies ledger creation or non-overlap with every accepted event is withdrawn. See `TIMING-SOURCE-QUALIFICATION.md`.
4. It identifies the 00:51:10 to 00:51:25 context clip as overlapping one transcript report.
5. It reports the ten-pixel threshold-defined lunar footprint without calling it optical resolution.
6. It treats the absence of a screened pulse as non-exclusionary.
7. It computes the `1.31 x 10^-7 km^-2 h^-1` conservative count floor with assumptions.
8. It blocks promotion of that floor to a completeness-corrected flux.
9. It preserves NASA's existing recommendations separately from the app's extensions.
10. It reproduces the frozen 1,458-trial injection grid and reports that 50 percent recovery was not reached.
11. It keeps the curve in clip-native digital units and blocks a physical brightness or sensor-performance interpretation.
12. Deleting derived outputs and rerunning produces equivalent receipts from the same frozen inputs.
13. It preserves an observer's unprompted first mark separately from a later prompted confirmation and never counts those records as independent without a declared dependency model.

## Technical route

The lowest-burden credible first release is:

- a Python library for the schema, validators, and deterministic calculations;
- a command-line interface for ingestion, validation, and export;
- a local read-only browser viewer generated from the receipt;
- SQLite or DuckDB for indexed local cases;
- no account, cloud service, database server, or required language model; and
- Apache-2.0 licensing to encourage scientific and institutional reuse.

Do not begin with a large React application, hosted collaboration, automatic event detection, or an AI chat interface. A small deterministic engine plus an excellent local viewer is enough to prove the category.

## Repository shape

```text
observation-receipt/
  src/observation_receipt/
    model.py
    ingest/
    clocks.py
    coverage.py
    measurement.py
    claims.py
    export.py
    viewer.py
  schemas/
  cases/artemis-ii-flashes/
  tests/
  docs/
  LICENSE
  README.md
```

## Public positioning

Lead with the demonstrated user problem:

> A timestamp match is not evidence coverage. A null is not an exclusion unless the sensor could see the event. A count is not a rate until the denominator is measurable.

Avoid positioning it as a NASA critique, an impact-flash detector, or a general truth machine. The strongest public posture is a reusable open-source method demonstrated on NASA's unusually rich public archive.

## Build sequence

### Milestone 1: reproducible case package

- Extract the current Stage 11N through 11Q schemas into a clean library.
- Ship the Artemis fixture and deterministic receipt.
- Generate the six polished charts from the receipt.

### Milestone 2: local viewer

- Timeline with coverage windows.
- Witness matrix.
- Claim detail with supporting, limiting, and missing evidence.
- Click-through to source hashes and exact rows or frames.

### Milestone 3: interoperability

- RO-Crate export.
- VOEvent import and export for applicable candidates.
- IVOA Provenance mapping.
- A second non-lunar fixture to test transfer.

## Go or no-go gate

Proceed if a clean external user can load the Artemis fixture, understand the later-null error in under five minutes, and reproduce the receipt without project-specific instructions.

Pause or pivot if the tool needs bespoke code for every case, if the coverage model cannot represent field of view and completeness without domain-specific patches, or if existing tools can reproduce the complete receipt with a thin configuration layer.

## Private Milestone 1 checkpoint

The clean `observation-receipt/` subtree now contains a local application candidate rather than only a prototype:

- `run.py demo` is the zero-install first-run path;
- `src/observation_receipt/` contains the validator, deterministic evaluator, exporters, CLI, and offline viewer generator;
- `schemas/observation-receipt-v0.2.schema.json` defines structured witness marks, observation capabilities, measurement functions, and bounded claim rules;
- `cases/artemis-ii-flashes/` binds the verified Artemis evidence into a portable fixture;
- `cases/synthetic-field-test/` supplies a clearly fictional non-lunar transfer check without making a real-world domain claim; and
- thirteen focused tests cover exact outputs, mutations, path containment, deterministic bundles, viewer structure, and the real first-run command.

The Artemis fixture now produces six distinct outcomes:

1. the five-event ledger is `SUPPORTED`;
2. the claim that the later camera window covered the annotation's background-photo epoch is `REFUTED_NONOVERLAP`, a metadata-time comparison only; coverage of every accepted event remains unestablished;
3. the overlapping camera null is `BLOCKED_INSUFFICIENT_CAPABILITY`;
4. the count floor is `SUPPORTED_WITH_ASSUMPTIONS`;
5. calibrated flux is `BLOCKED_MISSING_MEASUREMENT_FUNCTION`; and
6. independent-confirmation language is `BLOCKED_DEPENDENCE_MODEL_MISSING` when marks are socially connected and no dependence model is declared.

Version 0.2 closes the flat-witness gap. Each mark preserves observer, time state, exact time when available, elicitation state, independence state, dependency group, source artifact, and source locator. The engine never counts prompted or socially cued marks as independent without an explicit model.

This clears the local logic, packaging, and structural first-use gates. It does not establish uncoached comprehension, rendered visual acceptance, scientific acceptance, accessibility for disabled users, or maintained value. The available browser declined local-file navigation, so the exact generated viewer still needs actual-surface inspection through an allowed local route.

## Current recommendation

Keep the application local and private for one more gate. Inspect the generated viewer at its actual surface, then give a plausible first user only the README and ask them to explain why the later camera claim is refuted while the overlapping camera claim is blocked. Record the first wrong action or misunderstanding before offering help. Replace or supplement the synthetic transfer fixture with a small rights-cleared real case, and obtain qualified review of the Artemis terminology. If those checks preserve the product distinction without bespoke code, extract the clean subtree into its own public GitHub repository.

## Relevant standards and adjacent tools

- IVOA VOEvent: https://www.ivoa.net/documents/VOEvent/20110711/
- IVOA Provenance Data Model: https://www.ivoa.net/documents/ProvenanceDM/
- IVOA Data Origin: https://ivoa.net/documents/DataOrigin/20260331/EN-data-origin-1.2-20260331.html
- RO-Crate: https://www.researchobject.org/ro-crate/specification.html
- Label Studio multimodal template: https://labelstud.io/templates/timeseries_audio_video
- Timesketch: https://github.com/google/timesketch
- Evidencegraph: https://github.com/crashlabsai/evidencegraph
