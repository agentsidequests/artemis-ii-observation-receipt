# Artemis II: Look closer

Open **Artemis-II-Interactive-Field-Guide-v9-2026-10-14.html**. It is a self-contained local website, not a hosted site. It needs no account or installation. The high-resolution NASA browse photograph makes the file about 12 MB.

## Start anywhere

1. **Unfold:** choose scheduled event, sequences, capture keys or files. One scheduled Sunset remains one while the archive count changes. Every mark is an arranged accounting item, not a lunar location.
2. **Recount:** all four accounting views stay visible together. Choose one to read the explanation and exact ratio. Save A, choose another rule for B, then restore A if you wish. This saves the technical counting view, not the photograph's zoom or the unfolding scene. The optional ranking experiment shows why 76 versus 60 sequences can become 684 versus 900 files, without changing either observing window.
3. **Look:** choose a closer view of a real NASA/PDS lunar browse image, then use the position controls. Whole image and Reset restore the complete frame. Enlarging stored pixels is not a new measurement.
4. **Ask JPL:** follow the actual question and bounded reply. The optional claim exercise explains why one confirmed pair does not confirm all candidates or reduce the original cohort.
5. **Question:** switch among attention, camera sensitivity and timestamp meanings. The page deliberately does not simulate catching real lunar flashes.

Keyboard users can tab to buttons, use Enter or Space, choose a zoom with the native selector and use arrow keys on the position sliders. There is no timed task or drag-only control. The page respects reduced motion and offers an additional reduction control. Native expandable explanations include data tables and a glossary. Full assistive-technology and all-age comprehension testing have not been performed.

Saved A is session-only: reloading clears it. The full comparison contains a read-only view receipt you can copy or request as a download. A generated view address describes the current technical controls, not a persistent saved A/B workspace. Browser downloads can be blocked; the text receipt is the fallback.

## Go deeper

The **technical notebook** is in this same page. It preserves the earlier workbench, every exact source locator, original/conditional population, sensitivity analysis, scientific limit and reviewer route. The two NASA-facing pilots remain separate, with concrete deliverables and acceptance gates.

The directly delivered companion links use these existing Documents files:

- Artemis-II-Illustrated-Essay-v6-2026-10-14.html
- Artemis-II-Specialist-Review-v7-2026-10-14.html
- Artemis-II-Identity-App-v7-2026-10-14.html
- Artemis-II-Assumption-Atlas-v7-2026-10-14.html
- Artemis-II-Flash-App-v7-2026-10-14.html

Keep companions beside the guide if you move the direct delivery. Inside the complete source ZIP, the same companions keep their older internal October 13 filenames. Both routes are deliberate; neither is a public URL. The complete source package includes all four applications, scientific receipts in its declared bounded scope, current essay/charts and editable website source. It is not the full mission archive or private research repository.

The ZIP is a delivery container, not a file to commit to GitHub. Any later authorized transfer should use the extracted source files and verified public-account route. This local build does not perform that transfer or change a repository's visibility.

## What the reading changed

**Artemis-II-Field-Guide-Reading-and-Design-v9-2026-10-14.md** explains the selected book chapters, excerpts and other sources, their access limits and the design choices they changed. It does not claim whole-book reading, educational validation or NASA acceptance.

## Rebuild the extracted source

Use a qualified Node.js runtime and the `marked` dependency already required by the presentation builder:

```text
node tools/build_observatory.mjs --root . --output . --marked /absolute/path/to/marked.esm.js
node tools/build_observatory.mjs --root . --output . --marked /absolute/path/to/marked.esm.js --check
node presentation/observatory/test.cjs .
python -B tools/verify_public_package.py
```

The builder first replays the unchanged v8 presentation, then creates v9 and its separate manifest. The full technical notebook is byte-conserved. The source ZIP supplies a bounded consumer replay, not every private scientific-stage dependency. `marked` is not needed to open the delivered HTML. The file makes no external requests for fonts, scripts, photographs or data.

This is a local publication candidate. No upload or publication is implied. Own code and analysis retain MIT; NASA/PDS imagery and third-party material retain their own terms. Passing checks cannot establish scientific truth, full accessibility, learning, universal appeal or institutional endorsement.
