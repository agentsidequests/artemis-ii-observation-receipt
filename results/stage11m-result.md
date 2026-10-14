# Stage 11M: Implementation-Diverse Split-Receipt Audit

- Verification: `PASS`
- Evidence state: `VERIFIED_IMPLEMENTATION_DIVERSE_SPLIT_RECEIPT_AUDIT`
- Oracle independence: `partial_implementation_diverse`
- Verifier source SHA-256: `3f1b77a24be09752bf8737e9122fda10417a88687bda26e3c858c20368a4ebb2`
- Assignment SHA-256: `2a372b95bc2897ee2d27400f7467d9d8ceb7c7410ed6fee7dab7aad0b1ed20d1`
- Receipt SHA-256: `9fb6f1d180e66cffb83b19924b3c25650b7c144712eff97053bfdf0043a97b2a`
- Pixel payload bytes opened: `0`

## Verified

A standalone consumer implementation reproduced the serialized source and assignment bindings, every assignment, and every policy metric without importing Stage 11L code.

## Separately recomputed key metrics

- Product-key crossing actions: `1,937`
- Action-key crossing actions: `0`
- Action-key crossing conditional five-second groups: `157`
- Actions inside those crossed outer groups: `1,216`
- Five-second-key crossing actions / groups: `0` / `0`

## Mutation results

- `tamper_source_hash_in_receipt`: REJECTED AT REQUIRED CHECKS
- `tamper_assignment_hash_in_receipt`: REJECTED AT REQUIRED CHECKS
- `tamper_algorithm_seed_in_receipt`: REJECTED AT REQUIRED CHECKS
- `duplicate_assignment_row`: REJECTED AT REQUIRED CHECKS
- `drop_assignment_row`: REJECTED AT REQUIRED CHECKS
- `change_relationship_key`: REJECTED AT REQUIRED CHECKS
- `tamper_partition_assignment`: REJECTED AT REQUIRED CHECKS
- `tamper_reported_metric`: REJECTED AT REQUIRED CHECKS
- `call_temporal_groups_semantic_scenes`: REJECTED AT REQUIRED CHECKS
- `call_crossing_observed_model_leakage`: REJECTED AT REQUIRED CHECKS
- `open_pixels_for_receipt_audit`: REJECTED AT REQUIRED CHECKS

## Claim ceiling

Stage 11M may establish that a second local implementation, sharing no Stage 11L code, reproduces the frozen serialized receipt and detects the named artifact and claim mutations. Its independence remains partial because it shares the declared algorithm, source manifest, relationship semantics, repository, and authoring episode. It cannot establish independent human replication, scientific task validity, semantic scenes, observed leakage, statistical independence, model-performance effects, operational sufficiency for NASA or PDS, or global novelty.
