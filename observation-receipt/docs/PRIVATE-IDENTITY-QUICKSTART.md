# Observation Receipt: private identity and sensitivity demo

## Read it now

Open `Artemis-II-Identity-Sensitivity-Viewer-2026-10-12.html` from Documents in your ordinary browser. The file is self-contained. No account, server or package installation is needed to read it. The separately delivered comparison CSV is a fallback if your browser does not save an embedded download.

The first screen distinguishes replay integrity from scientific acceptance. Scroll to the unresolved-identity panel and original/conditional table. Expand the provenance disclosures to inspect the source identifiers and JSON paths. On a narrow screen, scroll the table sideways; its focusable region can also be moved with arrow keys. All eight named predicates survive this one-action condition, but no physical representative is selected.

## Rebuild or edit

Extract the private source ZIP. From its `observation-receipt` folder, with Python 3.11 or newer:

```powershell
python -B .\run.py demo --case identity
```

Open `build/artemis-ii-identity/index.html`. The original flash demo remains `python -B .\run.py demo`. Run the standalone checks with `python -B -m unittest discover -s tests -v`.

The editable identity case is `cases/artemis-ii-identity/case.json`. The full pinned sensitivity source and exact derived metadata-family excerpt are beside it under `sources`. All runtime dependencies are standard library. No wheel/editable-install tooling is required.

## What this is not

This is a private application candidate, not a public release or a NASA-accepted method. It does not merge source identities, replace original scientific counts, validate content labels, discover impacts or establish calibrated flux. Its byte checks do not prove archive semantics. The excerpt's parent reconstruction is checked in the owning private Testbed, not independently rebuilt by this portable app.

Rendered desktop/narrow-screen inspection and targeted keyboard checks are live operator evidence, not an uncoached outside-user trial or accessibility certification. Qualified archive/science review, fixture rights/redaction and public-release approval remain open. The Codex in-app browser's CSV download event was not confirmed; use the delivered CSV or the bundle's actual export file as the reliable fallback.
