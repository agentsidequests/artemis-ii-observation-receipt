# Stage 11R: Hierarchical Test-Set Isolation Audit

- Verification: `PASS`
- Evidence state: `VERIFIED_HIERARCHICAL_TEST_ISOLATION_AUDIT`
- Pixel payload bytes opened: `0`

## Result

The frozen Stage 11L product-key canary contains 4,511 test products, but none is isolated from training at the verified complete-action layer.

| Test-product relationship to training | Products | Share of test partition |
| --- | ---: | ---: |
| Exact capture identity also in training | 4,307 | 95.478% |
| Capture absent, complete action in training | 204 | 4.522% |
| Complete action absent from training | 0 | 0.000% |

The accounting identity is exact:

`4,511 = 4,307 + 204 + 0`

At the group level, the test partition contains 3,679 capture identities. Only 68 captures are absent from training, and all of them belong to actions represented in training. The 1,937 test-visible action groups are therefore all crossing actions, with zero action groups isolated in test.

Across the full assignment artifact, those 1,937 crossing action groups contain 20,601 of 22,818 products (90.284%).

## Decision use

Use this result to show that a filename-disjoint test partition can still have zero action-isolated test products under one frozen product-key policy. Require a real task to name its prediction unit, estimand, and protected relation before treating structural isolation as sufficient.

## Claim ceiling

Stage 11R may establish that, in the frozen Stage 11L product-key canary, all 4,511 test products share either their exact capture identity or their reconstructed complete action with at least one training product, including 4,307 exact-capture-linked and 204 action-only-linked test products. It cannot establish pixel similarity, statistical dependence, observed leakage, model shortcut use, performance inflation, scientific-task invalidity, a complete event oracle, independent replication, NASA acceptance, or global novelty.
