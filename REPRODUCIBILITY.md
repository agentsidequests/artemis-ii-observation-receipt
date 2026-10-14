# Reproducibility and source availability

## Different claims, different checks

1. **Package identity:** `tools/verify_public_package.py` checks each shipped file against the release manifest. This attests bytes, not the truth of a proposition.
2. **Current app and qualification replay:** `tools/replay_public.py --quick` runs bounded current tests, the presentation and all four portable app cases. No network or image acquisition occurs.
3. **Retained scientific regression:** `tools/replay_public.py --suite` runs the retained root tests except the known full-text-dependent Stage 11N audit and a Git-only archive test when no Git checkout exists. The exact omissions are printed. No omitted check counts as a pass.
4. **Historical full-text audit:** `tools/replay_public.py --historical-full` first requires the exact withheld NELIOTA text extract. Without it, execution stops with a named source-availability boundary. Supplying arbitrary text or a newer version does not satisfy a hash pin.
5. **Pixel regeneration or new acquisition:** these are distinct workflows, not executed by the regression suite. The overlap pixel screen and synthetic injection helper need NumPy and external FFmpeg/FFprobe executables. PDF extraction needs pypdf. Current essay-chart regeneration needs Pillow and the original font context. The legacy flash-chart renderer's CLI and imported main/timeline/distance entry points are disabled because they would recreate withdrawn graphics; its historical calculation code is retained for inspection. The shipped qualified charts and recorded pixel receipts remain inspectable without those tools. No automatic installation or source download is performed.

Only the environment and checks reported in `VALIDATION.md` are qualified. A declared minimum Python version is not proof that every version or operating system was tested. A local preview inspection is not uncoached specialist acceptance or accessibility certification.

The public projection includes a factual summary of the scoped JPL reply, not its original correspondence. The app checks the summary's bytes and exact pair binding; it cannot authenticate or replay that unbundled parent. The original mail-intake preparer and private-delivery packagers are not exported. Seven named private-only checks carry explicit skips. Private predecessor-commit conservation is replaced at the export boundary by source/projection conservation and the public inventory, not represented as the original private Git test passing.

## Missing historical source

The following exact text is not redistributed:

```text
evidence/stage11n/source/neliota-wide-field-high-cadence.txt
bytes: 76776
sha256: c147cc0d0a28ba5e347a3bd6c6406dfb80272efaa8762d59a843d12ffc8936d4
```

The PDF's size and hash are recorded in `EXPORT-PROVENANCE.json`. Obtain the source only through an authorized route and reproduce the exact extract with the appropriate original version and extraction method if a full historical audit is needed. The [source paper](https://arxiv.org/abs/1809.00495) remains independently readable. No network fetch is hidden in the quick or broader test commands.

The historical Stage 11N result is a retained prior result, not a newly replayed full-text pass. It also includes the old conditional distance arithmetic and `annotation_ledger_utc` clock terminology. Its **physical observing-advantage interpretation is withdrawn** by the matched-epoch range review, and its promotion of the photo/context time to a completed-ledger/event bound is rejected by [TIMING-SOURCE-QUALIFICATION.md](TIMING-SOURCE-QUALIFICATION.md). A historical calculation or saved `pass` flag must not reverse either disposition. The current prototype fixture and saved outputs now use the qualified background-photo comparison, not independently certified event times. Run `python -B prototype/observation_receipt.py` to replay its three pinned inputs and five findings without modifying files.

## Exported versus original identities

Native NASA/PDS/JPL payloads and numerical figures remain unchanged. Some owned files contain a public projection: public credit, MIT licensing, removal of private runtime paths, public reading-copy locators, or dependent hash/byte-size rebinding. `EXPORT-PROVENANCE.json` records both source and exported identities for every copied file. These are two distinct byte identities, not a claim that a redacted receipt is the original receipt.

Dependent hashes are rebound to the actual exported bytes, rather than suppressed. Numerical findings, time anchors, source payloads, mutation tests, and claim ceilings are not intentionally changed. The candidate's retained checks must independently demonstrate that those boundaries still hold.

## Key read-only replay entry points

Run these from the repository root using Python 3.11 or newer:

```text
python -B -m src.camera_identity_alias_census
python -B -m src.order_robust_camera_reconstruction --check
python -B -m src.camera_sequence_downstream_sensitivity --check
python -B -m src.fcorona_range_reconciliation
```

These deterministic comparisons preserve unresolved physical identity. They do not adopt the order-robust candidate, merge aliases, validate image content, certify a flight sensor, establish a new impact rate, or grant permission to contact or publish on another party's behalf.
