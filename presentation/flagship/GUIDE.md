# Artemis II: Explore / Play / Use / Inspect

A local flagship prototype, v10, 14 October 2026. Independent work by agentsidequests. Not published, NASA-endorsed or specialist-approved.

## Start here

Open **Artemis-II-Interactive-Science-v10-2026-10-14.html**. The four links at the top stay available as you move around:

1. **Explore:** the illustrated Artemis story, the archive unfolding, four counting views, a real lunar image, the JPL exchange and two separate proposed pilots.
2. **Play:** three small, untimed experiments. Change a train/test boundary, make an explicit assumption about missing target names, or alter an invented recorder. Plain explanations sit beside optional exact math and sources.
3. **Use:** the existing identity, historical identity, assumption-atlas and flash apps, reading copies, evidence download and portable source package.
4. **Inspect:** the complete preserved technical notebook. Jump directly to relationships, selection, weighting, detection, recommendations or source/replay evidence.

No accounts, telemetry or network calls are needed for the interactions. External source links require an internet connection. Use the keyboard or touch/mouse; native controls, text explanations and tables accompany the graphics. Reduced motion follows the device setting, with an additional page control. Full accessibility and assistive-technology testing remain unverified.

## What the experiments teach

**A fair test:** training fits a method to examples; testing evaluates held-out examples. The illustrated goal is a new camera sequence. Twelve invented files show why holding out a format, then a capture, then a whole sequence produce different relationship boundaries. The example runs no model and reports no accuracy. An actual Artemis structural canary is clearly separated from the miniature. Grouping at one layer does not establish physical independence or a new-event test.

**The missing names:** hold the 3,413 named fields fixed. Suppose `k` of the 4,193 blanks are assigned Sunset and the rest assigned other names. Then `(1,553 + k) / 7,606` is the hypothetical completed recorded-field share. Its possible range, 20.418% to 75.546%, is not a confidence interval, a probability distribution, an image-content result or a prediction. Recorded fields may also be wrong. Counting only named fields, `1,553 / 3,413 = 45.502%`, asks a different question.

**The invisible events:** twelve wholly invented signals stay fixed while a deterministic on-time and arbitrary signal rule change. An event outside coverage differs from an event inside coverage but below the rule. Neither null proves nothing happened. There is no noise, false-positive model, optical response, human-vision model or physical calibration. No toy setting maps to Artemis. The real transcoded-clip injection test and all its limitations remain separate in Inspect.

The wider habit: first say what is related, which records were selected, what gets weight and what could be detected. Those decisions can change what a dataset appears to say without changing the world it records.

## Save, switch and recover

Explore's **Save counting view as A** stores an optional source-bound evidence comparison. Switch sections and return without losing A. The Play settings are separate: **Reset all three experiments** does not clear A. Reloading resets session-only settings. The existing evidence workbench can create a source-matched view address and reject a different evidence edition. A local address is not a publicly reachable link.

Use can download the evidence excerpt or current teaching settings as JSON. If a browser blocks a download, expand the copyable JSON fallback. The source package also contains `presentation/data.json`. Teaching settings are not a scientific receipt and contain no personal notes or answers.

The direct Documents page links to the separately delivered companion apps and ZIP. For portability, extract **Artemis-II-Public-Candidate-v10-2026-10-14.zip** and open its v10 HTML. Keep the extracted files together. The ZIP is not nested inside itself: its download link appears only in the standalone Documents copy, where that file exists. The extracted site's Use section points to the source already supplied and its working replay guide. The package contains bounded replay material, not the full mission archive or private research history. Browser-operator checks used the loopback HTTP route; direct file-protocol opening was not observed.

## Reproduce and inspect

Inside the extracted package, existing `README.md`, `VALIDATION.md` and app instructions govern the declared replay. The new pure teaching model can be checked with Node.js:

```text
node presentation/flagship/test.cjs .
python -B -m unittest tests.test_flagship tests.test_observatory tests.test_reader_first tests.test_interactive_workbench tests.test_reader_flow tests.test_presentation -v
```

The buildless HTML works without Node or Python. Rebuilding uses the existing qualified Node/marked route, with explicit locations:

```text
node tools/build_flagship.mjs --root . --output . --marked /path/to/marked.esm.js --check
```

`--check` compares regenerated bytes. It does not establish scientific truth or human learning. Original scientific receipts, four apps, v9 and earlier reading versions remain intact. The v10 builder asserts that the full technical notebook is byte-identical to its v9 source. Public and private data pins remain deliberately separate.

## Design and evidence

The new layer uses a concrete mechanism before vocabulary, immediate consequences instead of scores, and optional exact detail rather than separate simplified and expert stories. The visual system retains the real lunar photographs, cream reading surfaces, editorial type and ink-blue experiment plates. Research already recorded for v9 informed these choices; it did not establish that this version teaches every age or education level.

The primary [scikit-learn cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data) informed the distinction between ordinary held-out files and a task-shaped group boundary. It is method context, not evidence that an Artemis model was trained. [NASA Eyes](https://science.nasa.gov/eyes/), [PhET](https://phet.colorado.edu/en/about) and [Explorable Explanations](https://explorabl.es/) remain relevant existing science-experience precedents, not proof of novelty or learning efficacy for this prototype.

Own code and authored analysis are MIT-licensed. NASA/PDS imagery and third-party material retain their own credits and terms. The JPL interaction is a narrow factual paraphrase, not a published email, a checksum comparison, a completed archive fix or broader endorsement. Both original catalogue IDs and all original denominators remain.

## Acceptance boundary

Build, model, source-conservation, extraction and bounded browser-operator checks are reported separately in the project verification record. They cannot certify enjoyment, uncoached comprehension, all-age usability, full accessibility, institutional acceptance or scientific validity. Paul retains design acceptance; qualified readers and specialists retain their respective judgments. This local revision authorizes no upload, hosting, contact or publication.
