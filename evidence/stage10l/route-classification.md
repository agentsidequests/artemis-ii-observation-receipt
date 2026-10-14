# Stage 10L access-route classification

- Goal: exact metadata-only representation parity for the 7,606-identity complete-action cohort.
- Exact target: the public PDS Imaging Atlas search endpoint already used by Stages 10D and 10G.
- Required state: current public structured JSON; no authentication and no pixels.
- Initial route: one POST containing every exact internal ID.
- Initial result: HTTP 403 before an Atlas response was returned.
- Failure classification: `SURFACE_PREREQUISITE_MISSING` for the large request envelope, not target, authentication, source, or API unavailability.
- Discriminating probe: the same endpoint accepted the preserved small Stage 10D query with HTTP 200.
- First fallback result: 100-ID batches reached Atlas, but an internal-ID aggregation was rejected because that field is text rather than an aggregatable keyword. Failure class: `REPRESENTATION_INSUFFICIENT` for that response shape, not missing source data.
- Selected fallback: the same semantic API and exact identity cohort in deterministic 100-ID batches, returning the three metadata records per identity and reconciling collection parity locally.
- Stop: any batch mismatch, missing identity bucket, response over 2,000,000 bytes, pixel access, or need for authentication.
