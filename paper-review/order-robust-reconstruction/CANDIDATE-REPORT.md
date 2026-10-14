# Order-robust camera reconstruction candidate

Private local engineering result, 12 October 2026. Computational support only; not a revised physical census, adopted reconstruction or NASA-accepted recommendation.

## Result

The new candidate removes input-order selection from complete-sequence reconstruction and makes unresolved identity visible. Its complete output is identical in eight tested orders of the frozen 10,329-record snapshot. Every original baseline sequence is accounted for. None is silently dropped, reassigned or corrected.

| Declared unit | Candidate result |
| --- | ---: |
| Input native raw-product IDs | 10,329 |
| Complete native-ID paths satisfying the declared rules | 2,225 |
| Lossless metadata-path families | 2,174 |
| One-ID-per-slot, noncompeting metadata sequences | 2,165 |
| Identity-alternative families, withheld from admission | 9 |
| Competing-path components in this snapshot | 0 |
| Native IDs participating in any complete candidate path | 7,655 |

These units are deliberately different. The table does not estimate physical exposures or actions.

## What changed in the algorithm

The old route sorts a camera's records by shutter count and greedily tries contiguous windows. At tied counts, source-row order changes which window is tried. Our census showed 2,166 reconstructed sequences in the retained order but 2,134 under reversal.

The candidate instead enumerates native-ID paths that satisfy explicit consecutive shutter and file counters, serial and recorded optical-setting equality, the six frozen bracket patterns, required shooting mode/order and the original ten-second span ceiling. A tied-count distraction cannot interrupt a qualifying path merely by occupying a neighboring list position. No path is chosen because it yields a preferred count.

It adds an explicit-offset, nondecreasing recorded-time gate across every slot. The original route checks endpoint span but not internal time monotonicity. A synthetic counterexample proves this is a stricter rule, not merely a refactoring. All original snapshot sequences satisfy it, so this snapshot has zero baseline exclusions. A future exclusion must carry its reason.

The output has three states:

- `UNAMBIGUOUS_METADATA_SEQUENCE`: exactly one native ID per slot and no native ID shared with another complete metadata path.
- `IDENTITY_ALTERNATIVES_ABSTAIN`: one or more slots have multiple IDs sharing the same nine-field metadata key. Every member identifier, shared key and original target/activity/flight-day field array remains visible. No representative is selected.
- `COMPETING_PATHS_ABSTAIN`: otherwise distinct complete metadata paths share native records. Their entire connected component is withheld, not just whichever path happens to be visited second.

A metadata-path family is a lossless way to expose alternatives, not a physical merge. The family ID hashes its declared metadata path for reproducibility; it is not an image-content hash or source-identity certificate. Target fields, activities and flight-day tags are retained but do not choose a path.

## Comparison with the frozen baseline

Of the original 2,166 sequences, 2,165 correspond to unambiguous metadata sequences and one belongs to an identity-alternative family. Every original native-ID path is present in the candidate. Its original manifest still has 7,606 keys and 22,818 product rows; nothing is replaced.

The withheld original sequence begins at `2026-04-07T01:06:17.480Z`, with pattern `0,-2,-1,+1,+2`. Its final slot retains both `art002e009301` and `art002e015991`. Its original action is `a2-action-1c22cc639e2f4792a76b8ca4`. The ambiguity concerns the native identifier relationship, not a proven target-label error.

Eight families have no original baseline path: seven three-slot families on flight day 4 and one five-slot Sunset family on flight day 6. All eight are identity-ambiguous and withheld. They are not eight newly accepted physical camera actions.

The nine withheld families contain 31 metadata slots and 54 native IDs. The unambiguous subset has 7,601 native keys. Across all families there are 7,632 metadata slots and 7,655 native IDs. None of these replaces the original denominator.

The seven flight-day-4 families have two native alternatives at each of three slots, hence eight native paths each. The two other families have one two-way slot each:

`7 × (2 × 2 × 2) + 2 + 2 = 60 ambiguous native-ID paths`

`2,165 unambiguous paths + 60 ambiguous paths = 2,225 native-ID paths`

This explains why 2,225 paths are not 2,225 independent actions, and why an arbitrary smallest-ID policy would hide uncertainty. The flight-day-4 `Moon` versus absent-target fields are preserved for both alternatives rather than averaged, voted on or imputed.

## What the tests establish

Eight full-snapshot orders include original, reversed, native-ID-sorted, a rotation and four independently seeded shuffles. Exact output parity covers family identities, membership, field alternatives, residual IDs and ambiguity components, not just summary counts.

An independently implemented exhaustive small-case oracle reads raw fields and checks counter arithmetic, settings, bracket patterns and time rules without using the production path builder or its leaf validator. It agrees for all six patterns, repeated records, competing times and 32 randomized alternative cases. All 720 input permutations of a six-record, three-slot alternative fixture retain the same eight native paths and withhold the family. Transitive competing paths produce one complete withheld component; omitted or invented components and false admission are rejected.

Settings/counter/bracket/order mutations, missing or multiple fields, naive or invalid times, internal time reversal, the ten-second boundary, duplicate native IDs and complexity ceilings have explicit checks. Label changes and native-ID renaming cannot choose a different metadata family. Invalid acceptance or external-effect flags are rejected.

This is engineering verification. The main code still reuses the frozen original compatibility predicate at path leaves, so full-snapshot independence is partial. The independent oracle is exhaustive only for its bounded small fixtures, not for every possible mission, label schema or physical camera behavior. Eight full-data orders are empirical tests, not a claim that every possible permutation was executed.

An implementation-diverse PowerShell consumer also checks the exported members directly against the frozen raw source and original manifest. It confirms every copied field, all matching-ID alternatives in each slot, counter/time/bracket constraints, coherent mapping of all 2,166 original actions and all 7,655 CSV rows. It does not independently discover every full-snapshot path or validate physical identity.

## Reproducibility and safe use

The owner is `paper-review/order-robust-reconstruction/`, with the prospective `contract.json`, canonical `result.json`, complete `membership.csv`, and this report. The exported check boundary is in the repository-root `REPRODUCIBILITY.md` and `VALIDATION.md`. The implementation is `src/order_robust_camera_reconstruction.py`. From this repository root, run:

```text
python -B -m src.order_robust_camera_reconstruction --check
```

`--write` builds absent or identical generated files and rejects unknown differing files. Development refresh requires both exact previous artifact hashes; the wrong hash causes no refresh writes. These are generated outputs, not replacements for immutable NASA/PDS evidence. A check detects interrupted or changed output bytes before any commit. Atomic multi-file crash recovery is not claimed.

The exported companions are [the complete candidate receipt](result.json) and [the native-membership CSV](membership.csv). Replay also needs the exact source snapshot and code supplied in this export. Treat CSV identifiers, timestamps and zero-padded file numbers as strings; spreadsheet inference may change their display.

## Decision and next gate

The computational order-sensitivity gate has a supported separate candidate. It has not been adopted, and no downstream population has been recomputed. Do not replace 2,166 with 2,174, 2,165 or 2,225 as a physical headline.

The strongest next analysis is a bounded downstream sensitivity receipt: determine which relationship, selection and weighting claims depend on the one withheld original sequence, while keeping canonical receipts intact. In parallel with any later owner-approved specialist review, ask what source lineage or identity evidence would resolve the native alternatives. A deterministic algorithm cannot answer that archive-semantic question by itself.

This work acquires no new source or image data and performs no outreach, publication or push. Full repository regression may read already-admitted local evidence from earlier stages. Source-byte identity, physical grouping, target truth, scientific acceptance, impact-flux calibration and NASA pipeline behavior remain unverified.
