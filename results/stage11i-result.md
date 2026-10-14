# Stage 11I — Implicit-Weight Factorization

- Verification: `PASS`
- Evidence state: `VERIFIED_IMPLICIT_WEIGHT_FACTORIZATION`
- Actions / captures / products: `2166` / `7606` / `22818`
- Representation multiplier: `3×` for every admitted capture
- Three- / five-exposure products per action: `9` / `15`
- Five / three relative weight before and after representation multiplication: `1.666667×` / `1.666667×`
- Five-exposure action / product shares: `25.577%` / `36.419%`
- Pixel payload bytes opened: `0`

## Verified

The representation layer uniformly triples admitted capture rows without changing the five-versus-three action-weight ratio. Variable bracket length, not constant representation parity, creates relative action reweighting in product counts.

## Decision use

Separate absolute row multiplication from relative sample weighting: preserve all representations and exposures, then choose the outer action, segment, or event estimand explicitly.

## Claim ceiling

Stage 11I may establish that every one of 7,606 admitted capture identities has three archive representations, uniformly tripling the cohort from 7,606 captures to 22,818 products. It may establish that this constant multiplier preserves the five-versus-three exposure action-weight ratio at 1.666667, while variable bracket length raises five-exposure actions from 25.577% of actions to 36.419% of captures and products. It cannot call the representations duplicates, recommend deletion, rank their scientific value, assert an actual sampler or observed model bias, nominate a universal correction, extend beyond the admitted complete-action cohort, or make a novelty, priority, or physical-science claim.

## Hard negatives

- `claim_representation_multiplier_causes_relative_protocol_weight`: REJECTED
- `call_archive_representations_duplicates`: REJECTED
- `recommend_discarding_representations_or_brackets`: REJECTED
- `rank_representation_scientific_value`: REJECTED
- `claim_actual_sampler_is_uniform_products`: REJECTED
- `claim_observed_model_bias`: REJECTED
- `claim_one_universal_correct_weighting`: REJECTED
- `generalize_to_unadmitted_archive_records`: REJECTED
- `claim_novelty_or_priority`: REJECTED
- `open_pixels_during_factorization`: REJECTED
