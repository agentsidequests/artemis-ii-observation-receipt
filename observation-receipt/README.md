# Observation Receipt

Current identity case: `python -B run.py demo --case identity-confirmed`. It displays an authored factual summary of JPL's exact-pair confirmation separately from unverified NEF-byte equality and the unchanged historical withholding comparison. Both catalogue IDs and all original counts are retained. [Contract](docs/STEWARD-IDENTITY-CONTRACT.md) owns source and disclosure limits. The original `--case identity` stays available as a historical metadata-only control; do not present that older fixture as the current confirmation state.

**Turn timestamped observations, sensor windows, witness marks, and detection limits into a receipt that shows what is supported, what is refuted, and what was never measurable.**

A timestamp match is not evidence coverage. A null is not an exclusion unless the sensor could see the event. A count is not a rate until the denominator is measurable.

Observation Receipt is a small, local-first Python tool for researchers, citizen-science coordinators, data journalists, and technical reviewers reconstructing cross-modal transient events. It joins four things that are often separated:

1. the candidate event;
2. the humans and sensors that could have detected it;
3. their time, field of view, calibration, and completeness; and
4. the exact claim someone wants to make.

It then exports a self-contained browser viewer, a machine-readable JSON receipt, a Markdown docket, and CSV tables. It uses only the Python standard library. No account, database server, cloud service, JavaScript dependency, or language model is required.

## Separate case: target-weight robustness

Run `python -B run.py demo --case robustness`, then open `build/artemis-ii-robustness/index.html`. Its native controls choose six accounting units, two frozen populations and eight hypothetical budgets from the existing verified analysis. A 47/48-field comparison exposes the narrow combined-byte majority margin without identifying actual tag errors. Source-linked witnesses, exact denominators, r = 0 equal-field-cost completion priorities and direct CSV files are inspectable.

See [quickstart](docs/ROBUSTNESS-QUICKSTART.md) and [case contract](docs/ROBUSTNESS-CONTRACT.md). The case has its own `schemas/tag-weight-case-v1.schema.json`; existing 0.2/0.3 fixtures retain their scientific values. It verifies pinned bytes and consumer accounting before writing, not physical identities, content labels, scientific acceptance or uncoached usability. The standalone build needs only Python 3.11+ and its standard library. Original project code and documentation are credited to agentsidequests under MIT; third-party material retains its own terms. This candidate is not published.

## Unresolved identities and conditional comparisons

Private version 0.3 adds a separate source-bound accounting demo:

```powershell
python .\run.py demo --case identity
```

Open `build/artemis-ii-identity/index.html` in your browser. The viewer keeps the two native alternatives unresolved, labels frozen original and conditional populations separately, and compares 23 metrics read from the exact pinned local receipt. It computes the eight named predicates separately in both views. All eight survive this one-action withholding condition, while physical identity remains blocked. This is one treatment, not eight independent replications or a corrected physical census.

The original flash demo below remains the default. Its 0.2 case version and numerical results are retained, but the timing proposition now concerns the annotation's background-photo epoch, not all five event times. The new viewer does not mix archive-action identity with the accepted flash-event ledger.

The identity build also exports `comparison.csv` and `identity-groups.csv`. Its HTML embeds the receipt and comparison downloads, so the viewer can be copied alone. A browser download event was not confirmed in the Codex in-app browser; the actual CSV file is included in the bundle as a direct fallback. No server is needed to read the self-contained HTML in an ordinary browser.

### Add a source-bound comparison

Use schema `schemas/observation-receipt-v0.3.schema.json`, retaining the ordinary case fields. Add a pinned local JSON artifact, unresolved `identity_groups` if relevant, and `conditional_comparisons` with distinct original/conditional root pointers. Each metric has one relative pointer used on both sides, a declared unit, scale and display precision. Case-supplied literal values cannot substitute for sourced numbers. Predicates compare a metric with a numeric threshold or a second metric of the same unit.

The included identity case is the complete editable example. Runtime validation enforces source containment, unique references, finite numbers, count/byte types, distinct roots, condition operands and abstention. The schema is self-contained; its references/rule inventory receive structural checks. Full independent JSON Schema conformance is not claimed, because the qualified development runtimes do not include a JSON Schema validator.

The metadata-family artifact is a derived exact excerpt. Its parent is checked by the private Testbed preparation command, not reconstructed by this portable app. SHA-256 matching establishes byte identity of that excerpt, not physical identity of the alternatives, semantic correctness of labels, or independent scientific acceptance. Source changes require an explicit repin and review of expected findings; the app never silently follows a live archive.

## See the Artemis II demo

Requirements: Python 3.11 or newer.

```powershell
python .\run.py demo
```

Open `build/artemis-ii-flashes/index.html` in any modern browser.

The demo reproduces six deliberately different results:

| Question | Result |
|---|---|
| Does the public annotation contain five accepted events, eight witness marks, and three observers? | `SUPPORTED` |
| Did the later 30 fps window cover the annotation's 01:04 background-photo epoch? | `REFUTED_NONOVERLAP`, metadata-time comparison only |
| Does a null in the overlapping context clip exclude the shared report? | `BLOCKED_INSUFFICIENT_CAPABILITY` |
| Do five accepted events support a conservative count floor? | `SUPPORTED_WITH_ASSUMPTIONS` |
| Do they establish a calibrated impact flux? | `BLOCKED_MISSING_MEASUREMENT_FUNCTION` |
| Can two socially connected marks be counted as independent confirmations? | `BLOCKED_DEPENDENCE_MODEL_MISSING` |

The app does not accept a scientific or operational claim on NASA's behalf.

The photo epoch does not certify ledger creation or bound all five accepted event times. Their event-level video coverage remains unestablished. The 913-second gap and this narrower negative proposition cannot establish that the later window missed every accepted event.

## Why structured witness marks matter

Version 0.2 replaces flat witness-name lists with records that preserve:

- observer;
- exact, interval, or unknown time state;
- the mark time when known;
- unprompted, prompted, socially cued, or unknown elicitation state;
- independent, dependent, or not-established status;
- dependency group;
- source artifact and locator; and
- a case-level witness-dependence model when one is justified.

The engine never promotes two marks to independent confirmations merely because two names appear.

## Build another case

```powershell
python .\run.py validate .\cases\synthetic-field-test\case.json --root .

python .\run.py build .\cases\synthetic-field-test\case.json `
  --root . `
  --output .\build\synthetic-field-test
```

The second case is explicitly synthetic. It verifies that the core logic transfers beyond lunar flashes without presenting fictional data as a real incident.

## Bundle contents

Each build produces:

```text
index.html                 read-only local viewer
receipt.json               complete deterministic evaluation
receipt.md                 human-readable docket
candidates.csv             candidate ledger
witness-marks.csv          structured witness records
observation-windows.csv    sensor and observer windows
findings.csv               claim statuses and ceilings
manifest.json              byte lengths and SHA-256 identities
```

The viewer is self-contained. It uses no external fonts, scripts, trackers, or network requests.

## Case model

The portable JSON case contains:

- `artifacts`: paths or URLs, hashes, media type, producer, archive, clock domain, and derivation state;
- `candidates`: disposition, mapping state, structured witness marks, and any declared witness-dependence model;
- `observation_windows`: time interval, clock uncertainty, target, field of view, and explicit capability states;
- `measurement_function`: monitored area, live time, threshold, completeness, confirmation rule, and task-specific fields;
- `claims`: exact propositions, deterministic rules, and claim ceilings; and
- `expected_findings`: frozen outcomes that make fixture drift visible.

The original normative schema is `schemas/observation-receipt-v0.2.schema.json`; extended cases use the separate self-contained 0.3 schema. The runtime also performs cross-reference and semantic checks that JSON Schema alone cannot express, such as artifact references, identifier uniqueness, and claim-to-window resolution.

## Supported deterministic rules

| Rule | Question answered |
|---|---|
| `ledger_summary` | Does the selected ledger have the expected events, marks, and observers? |
| `window_after_boundary` | Did an observation begin only after the relevant evidence boundary? |
| `window_capability_gate` | Did a window overlap, and were all required capabilities demonstrated? |
| `count_floor_sphere` | Does a count reproduce a stated spherical area-time floor under explicit assumptions? |
| `required_measurement_fields` | Is the declared measurement function complete enough for the proposed claim? |
| `witness_independence_gate` | Is a declared dependence model sufficient for an independence claim? |
| `identity_resolution_gate` | Does an unresolved source-linked identity still block physical resolution? |
| `conditional_comparison_gate` | Does a named numeric predicate hold in both the frozen original and conditional views? |

These rules are intentionally narrow. Observation Receipt is not a generic truth engine, event detector, image-analysis suite, or knowledge graph.

## Design boundaries

- Local artifacts fail closed on byte-length or SHA-256 mismatch.
- Reference-only URLs are identified as references, not hash-verified evidence.
- Unknown times remain unknown.
- Temporal overlap does not imply target coverage or detector capability.
- A missing capability blocks an exclusion claim rather than converting it into a negative result.
- A detected-count floor remains separate from a calibrated rate or flux.
- Prompted or socially cued marks remain separate from independent detections.
- `SUPPORTED`, `REFUTED`, and `BLOCKED` are all valid outcomes.
- Generated outputs are deterministic for the same case and source bytes.

## Development

Run the standalone checks:

```powershell
python -B -m unittest discover -s .\tests -v
```

The source-checkout launcher is the primary first-use path and requires no packaging tools. Editable installation is optional when `setuptools` is already available in the selected Python environment:

```powershell
python -m pip install -e .
observation-receipt demo
```

The editable-install and wheel paths are not part of the current local acceptance receipt because the qualified Python runtime does not include `setuptools`. Do not install extra build tooling merely to run the demo.

## Current maturity

This is a local Milestone 1 candidate, not yet a public release.

Completed locally:

- deterministic case evaluation;
- structured witness marks;
- Artemis II fixture;
- synthetic second-domain fixture;
- portable receipt bundle;
- read-only browser viewer;
- mutation and failure-path tests; and
- MIT licensing.

Still required before a public GitHub release:

- an uncoached first-use test with a plausible external user;
- qualified review of the Artemis terminology and claim boundaries;
- a rights and attribution pass over every distributed fixture artifact;
- repository extraction from the private Artemis Testbed;
- public issue templates, release notes, and a support boundary; and
- a real, rights-cleared second-domain case if cross-domain value is claimed publicly.

## Relationship to adjacent standards and tools

Observation Receipt is intended to complement, not replace:

- [IVOA VOEvent](https://www.ivoa.net/documents/VOEvent/20110711/) for astronomical transient packets;
- [IVOA Provenance](https://www.ivoa.net/documents/ProvenanceDM/) for entities, activities, and agents;
- [RO-Crate](https://www.researchobject.org/ro-crate/specification.html) for research-object packaging;
- Label Studio for multimodal annotation; and
- Timesketch for collaborative forensic timelines.

Its narrower contribution is the claim gate connecting event candidates, observation opportunity, detector capability, witness dependence, and measurement completeness.

## License

MIT for original project code and documentation. See `LICENSE` and the repository's third-party notices for excluded source material.
