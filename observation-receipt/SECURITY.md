# Security and data handling

Observation Receipt is a local, read-only evaluator. It does not require network access, execute case-supplied code, or upload evidence.

## Report a vulnerability

Before a public release, report security concerns privately to the repository owner. A public contact route will be added only when the project is published.

## Data boundaries

- Treat case files and generated viewers as potentially sensitive.
- Do not include credentials, private participant data, or restricted evidence.
- Local artifact paths are resolved beneath the root supplied by the operator, but the current alpha is not a sandbox for hostile case files.
- Generated HTML escapes case-supplied text and contains no active external scripts.
- Review fixture rights and redaction before sharing a bundle.
- Conditional metric values and identity alternatives come only from pinned local JSON artifacts; a mismatch blocks their display/evaluation. Case predicates and labels remain declarations requiring qualified semantic review.
- CSV exports prefix formula-leading text with an apostrophe; numeric deltas remain numeric. Review exports before using them in spreadsheets or publishing them.
- Viewer source-disclosure controls do not change evidence or resolve identity. Embedded downloads may behave differently across browser hosts; the bundle contains direct files as a fallback.

This alpha has not received an independent security audit.
