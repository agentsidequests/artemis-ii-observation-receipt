# Stage 11F external cluster-size screen

**Question:** Does the 9-versus-15-products-per-action result have a precise statistical analogue, and what terminology is justified?

**Scope:** bounded primary-literature screen. This note does not adopt an estimator, establish an outcome association, or claim novelty.

## Primary sources

1. Williamson, Datta, and Satten, “Marginal analyses of clustered data when cluster size is informative,” *Biometrics* 59(1), 2003. PubMed: https://pubmed.ncbi.nlm.nih.gov/12762439/ ; DOI: https://doi.org/10.1111/1541-0420.00005
   - Defines an inferential problem in which cluster size is informative and proposes generalized estimating equations weighted inversely by cluster size.
   - Shows asymptotic equivalence to within-cluster resampling for the target marginal analysis.

2. Hoffman, Sen, and Weinberg, “Within-cluster resampling,” *Biometrika* 88(4), 2001. https://academic.oup.com/biomet/article-abstract/88/4/1121/226041
   - Proposes repeated selection of observations within clusters for marginal inference when outcome risk is related to cluster size.
   - Makes clear that the cluster-weighted target differs from ordinary observation-weighted analysis.

3. Lee, Kim, and Skinner, “Within-cluster resampling for multilevel models under informative cluster size,” *Biometrika* 106(4), 2019. https://academic.oup.com/biomet/article/106/4/965/5537460
   - Extends the approach to multilevel models by drawing a fixed number of observations from each cluster.
   - Explicitly frames informative cluster size as a model-specification and estimand problem, not a generic data-quality defect.

## What changes in this Testbed

- The precise external analogue is **cluster-size weighting**: a flat observation table gives larger clusters more influence than an equal-cluster estimand would.
- Stage 11F identifies a mechanism capable of producing unequal cluster sizes before image content is considered: three-exposure versus five-exposure action protocols, each multiplied into three archive representations.
- The current evidence does **not** establish “informative cluster size” in the formal outcome-dependent sense. No model outcome or cluster-level latent effect has been introduced, so an association between cluster size and outcome cannot be tested.
- “Protocol-induced cluster-size weighting hazard” is therefore the strongest justified phrase. “Informative cluster size” may be introduced only as the relevant literature and a future test, not as a verified Artemis II diagnosis.
- Inverse-cluster-size weighting, fixed-number within-cluster resampling, action balancing, and event balancing are not interchangeable repairs. Each defines a different target population or estimand. A later task must first decide whether it wants equal weight per product, exposure, camera action, realized segment, or planned event.

## Claim boundary

This screen supports a terminology and method bridge, not a model result. It does not show that an actual Artemis II analysis is biased, that cluster size is related to a prediction target, that equal-event weighting is always correct, that products are wasteful, or that the observation-graph framing is novel.

## Decision

Retain the public-facing insight that flattening the archive silently chooses a weighting policy. If a model task follows, freeze its estimand and unit weights before selecting a remedy. Do not apply inverse cluster-size weighting merely because cluster sizes differ.
