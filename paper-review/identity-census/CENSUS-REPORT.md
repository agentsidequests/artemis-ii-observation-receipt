# Artemis II camera-identity census

Private metadata-only review, 12 October 2026. This is a frozen-source diagnostic, not a physical exposure census or a NASA-accepted conclusion.

## What changed

Three separate findings now matter:

1. In 10,329 distinct raw-product records, 24 pairs share all nine retained camera fields. These are candidate identity links, not confirmed duplicate photographs.
2. None of those pairs contributes both identifiers to our frozen counted cohort. However, 21 pairs differ in whether the recorded primary-target field contains `Moon` or is absent.
3. More importantly, our existing action finder is sensitive to input order. Reversing the same records changes its result from 2,166 to 2,134 reconstructed sequences. The original receipts still replay exactly, but their counts must not be presented as an order-invariant physical census.

The immediate robustness gate belongs to our reconstruction, not to NASA's processing pipeline. No original receipt, counted manifest, article, image, or scientific stage was revised by this census.

## Scope and identity rule

The inputs are the retained Stage 10A and Stage 10E raw crew-camera search responses acquired on 10 October 2026: 18 pages covering queries for flight days 1 through 10. They contain 10,329 records from the `artemis2_crew_camera/data_raw` collection. This is not a live archive census, a census of every mission photograph, or an analysis of the approximately 800-GB release's image content. Zero results for days 9 and 10 describe these frozen queries, not an absence of mission photography.

A strict candidate key requires exact lexical agreement in camera serial, camera file number, shutter count, recorded UTC, ISO, focal length, shooting mode, automatic bracket order, and exposure bracket value. All nine must be single nonblank strings. Leading zeros are preserved; nulls and multiple values cannot manufacture a match. A separate explicit-offset UTC normalization and a four-field core comparison produce the same 24 pairs in this snapshot. This agreement does not validate a physical-identity key.

All 10,329 records are key-eligible. The 24 pairs involve 48 distinct product IDs and leave 10,305 distinct nine-field metadata keys. That last number is not a corrected exposure denominator. All pairs are on serial `3920019`: 21 on flight day 4 and three on flight day 6. Other cameras having no strict pairs under this rule is not proof of physical uniqueness.

## Intersection with our counted cohort

The existing manifest contains 22,818 products, arranged as three archived representations for each of 7,606 capture keys, grouped into 2,166 reconstructed complete actions. These are declared ledger units, not independently accepted physical exposures or events.

| Strict candidate pairs | Number of pairs |
| --- | ---: |
| Neither identifier belongs to the counted cohort | 23 |
| Only one identifier belongs | 1 |
| Both identifiers belong | 0 |

The known study-image stem `art002e009301` matches cohort stem `art002e015991`; only the latter is counted. Both record `Moon`. Adjacent `art002e015990` fails the strict match and remains a hard negative. The other flight-day-6 pairs are `art002e012280` / `art002e015488` and `art002e009300` / `art002e015965`, neither with both identifiers counted.

This rejects direct double-counting of these particular strict pairs inside the frozen cohort. It does not exclude other identity relationships, validate all 7,606 physical exposures, establish independence, or repair grouping outside the cohort.

## Target-field disagreement survives identity matching

In the 21 flight-day-4 pairs, the smaller product ID records `Moon` and its matching counterpart has an absent primary-target field. The recorded activity is `Opportunistic Imaging` in both. This is a conflict in field coverage, not evidence that either label is wrong or that two photographs depict the same scene.

Consequently, even a future independently justified identity merge must preserve both native identifiers and their original fields. Choosing the first, smallest, or largest ID as the truth can silently choose which target field survives. Content truth and archive lineage require separate evidence.

## Conditional reconstruction diagnostic

The contract declared four local replays of the unchanged six-pattern action finder: original order, reversed order, and two hypothetical lists retaining one representative per strict pair. The latter choose the minimum or maximum product ID only as contrasting diagnostic policies. Neither is an accepted deduplication rule.

| Local input treatment | Reconstructed sequences | Admitted raw capture keys | Admitted keys with nonblank target fields |
| --- | ---: | ---: | ---: |
| Original retained order | 2,166 | 7,606 | 3,413 |
| Same records, reversed order | 2,134 | 7,502 | 3,344 |
| Hypothetical minimum-ID representative | 2,174 | 7,632 | 3,439 |
| Hypothetical maximum-ID representative | 2,174 | 7,632 | 3,418 |

The reversal changes 106 admitted identifiers by symmetric difference, not merely a subset of 104 lost identifiers. No records or scientific inputs were added. The two hypothetical representative policies remove 24 records each and admit eight additional sequence witnesses: seven three-frame sequences on flight day 4 and one five-frame Sunset sequence on flight day 6. These are eight algorithmic admissions, not eight newly discovered physical camera actions. The minimum-ID policy adds 27 keys and omits one original key; the maximum-ID policy adds 26 and retains every original key.

Despite identical sequence and key counts under the two hypothetical policies, their nonblank-target counts differ by 21. This separates reconstruction sensitivity from target-field selection. It does not choose which policy is physically correct.

## Mechanism and falsifiers

Within each serial, the incumbent finder sorts only on parsed shutter count. Stable sorting therefore inherits the original row order when counts tie. A follow-on profile, declared after the reversal exposed a difference, finds 101 tied sort keys involving 222 records. Of those ties, 77 contain different recorded times and file numbers; none spans flight days. Those 77 ties are not strict alias candidates. Merely partitioning by flight day would not eliminate this observed ambiguity.

A small synthetic case demonstrates the mechanism: moving a tied-count distraction changes whether one otherwise complete three-frame sequence is admitted. Giving that distraction a distinct counter makes both orders admit the sequence. A separate repeated-middle-record case shows how a matching key can interrupt reconstruction. These are counterexamples to order invariance, not demonstrations of physical duplication or a universal diagnosis of every changed action.

The candidate grouping itself is permutation-invariant. The action reconstruction is not. Reproducible frozen output and robust inference are different acceptance questions.

## Explicit recommendation

Before integrating these counts as physically meaningful action or exposure totals, develop and test a separate order-robust reconstruction candidate. Keep the existing route and receipts intact as the known-good frozen baseline. Preserve identity candidates as ambiguous links rather than automatically collapsing them.

The candidate must report differences against the baseline, pass the tied-count and repeated-middle-record counterexamples, preserve no-tie hard negatives, and make its identity and abstention policy explicit. A deterministic tie breaker alone can establish computational invariance, not correct physical grouping. Source lineage and qualified scientific acceptance remain separate gates. Any downstream result whose population changes would require explicit recomputation and renewed interpretation, not a silent denominator edit.

Until then, existing structural results remain exact for their frozen identifiers, source order, algorithm, and declared grouping contract. Do not generalize their populations to a physical, order-invariant census. The bounded source-backed finding can inform an unsent specialist question, but this work neither contacts a reviewer nor integrates a new public allegation.

## Replay, evidence and limits

The canonical exported evidence is `paper-review/identity-census/`: `contract.json`, `result.json`, all 48 witness rows in `candidate-crosswalk.csv`, `native-crosscheck.ps1`, and `native-crosscheck.json`. See the repository-root `REPRODUCIBILITY.md` and `VALIDATION.md` for current exported checks. Replay from the repository root with `python -B -m src.camera_identity_alias_census`; add `--csv` for the witness export. The PowerShell crosscheck independently recounts source metadata, candidate membership and sort ties, but does not independently reconstruct actions or establish source truth.

The exported companions are [the complete receipt](result.json) and [the candidate crosswalk](candidate-crosswalk.csv). The receipt embeds source hashes and the declared contract; the exported repository supplies the preserved source snapshot and code for this replay. Companion files alone are not the complete reproducibility bundle.

The census and its conditional diagnostics made zero network requests and opened zero image-payload bytes. Full repository regression replays previously admitted evidence; it is not new image acquisition. This work performed no outreach, publication or remote push. It establishes no source-byte identity, pixel similarity, tag correctness, actual ML leakage, calibrated impact flux, physical clustering, global novelty or NASA acceptance. Previously access-blocked lineage reads remain unresolved. The prior withdrawal of the flash distance-advantage interpretation remains in force.
