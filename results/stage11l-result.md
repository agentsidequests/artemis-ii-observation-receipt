# Stage 11L: Deterministic Split-Receipt Canary

- Verification: `PASS`
- Evidence state: `VERIFIED_DETERMINISTIC_SPLIT_RECEIPT_CANARY`
- Source manifest SHA-256: `8edd58437cc609229edb5abb41c4e00048bb420354f1ac17a269da92c17e4729`
- Assignment artifact bytes / SHA-256: `4,573,289` / `2a372b95bc2897ee2d27400f7467d9d8ceb7c7410ed6fee7dab7aad0b1ed20d1`
- Receipt bytes / SHA-256: `4,216` / `9fb6f1d180e66cffb83b19924b3c25650b7c144712eff97053bfdf0043a97b2a`
- Pixel payload bytes opened: `0`

## Verified

The deterministic canary distinguishes three policy boundaries: product hashing fractures declared action groups; action hashing preserves actions but still fractures conditional five-second groups; hashing the five-second key preserves both declared layers.

## Policy comparison

| Policy key | Test product share | Crossing action groups | Crossing 5-second groups | Actions inside crossing 5-second groups |
| --- | ---: | ---: | ---: | ---: |
| `product_id` | 19.769% | 1,937 | 762 | 2,105 |
| `action_id` | 18.906% | 0 | 157 | 1,216 |
| `temporal_cluster_5s` | 19.419% | 0 | 0 | 0 |

## Decision use

Use the receipt as executable evidence that declared relationships can be checked and failed. Do not reuse the canary assignment as a scientific split; a real task must replace the conditional key with its own dependence oracle.

## Claim ceiling

Stage 11L may establish that one deterministic canary assignment and its validator preserve or fracture the declared action and conditional five-second relationship keys exactly as reported, and that the content-bound receipt rejects the tested source, assignment, completeness, policy, semantic, leakage, performance, universality, and pixel-access mutations. It cannot establish that five seconds defines a semantic scene, that the canary is a valid split for a scientific task, that any real pipeline leaked information, that preserving declared groups guarantees independence, that model performance changes, that the proposed fields are operationally sufficient for NASA or PDS, or that the mechanism is globally novel.

## Hard negatives

- `mismatch_source_hash`: REJECTED
- `tamper_partition_assignment`: REJECTED
- `drop_assignment_row`: REJECTED
- `misdeclare_product_policy_as_action_safe`: REJECTED
- `call_temporal_groups_semantic_scenes`: REJECTED
- `call_crossing_observed_model_leakage`: REJECTED
- `infer_model_performance_effect`: REJECTED
- `claim_five_seconds_is_universal`: REJECTED
- `open_pixels_for_split_canary`: REJECTED
