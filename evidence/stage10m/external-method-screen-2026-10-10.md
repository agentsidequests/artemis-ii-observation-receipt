# Stage 10M external method screen — 10 October 2026

## Decision this screen can change

Whether action-level grouping is merely a locally convenient convention or a methodologically grounded minimum for a later Artemis II image-model evaluation. This screen does not transfer performance effects from other domains to Artemis II.

## Sources inspected

- scikit-learn `GroupShuffleSplit` documentation: <https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html>
- Wen et al., “Effect of data leakage in brain MRI classification using 2D convolutional neural networks,” *Scientific Reports* 11, 22544 (2021): <https://www.nature.com/articles/s41598-021-01681-w>
- Bussola et al., “Inflation of test accuracy due to data leakage in deep learning-based classification of OCT images,” *Scientific Data* 9, 580 (2022): <https://www.nature.com/articles/s41597-022-01618-6>
- Alkhatib, “Data Leakage in Patch-Based Hyperspectral Image Classification: Quantifying the Impact of Spatial Overlap,” arXiv:2610.08770 (preprint, 6 October 2026): <https://arxiv.org/abs/2610.08770>

## Mechanism evidence

The maintained scikit-learn interface explicitly supports domain-defined group labels and defines train/test sizes in groups rather than samples. That is the directly reusable method: the split unit must encode the dependence that the evaluation must keep together.

The two peer-reviewed medical-imaging studies supply changed-domain evidence for the failure mechanism. When correlated slices or images from the same subject or volume were split independently, reported evaluation performance was materially higher than under subject- or volume-level grouping. These studies do not predict the size or direction of an Artemis II model effect; they show why related records crossing partitions can invalidate the intended independence.

The current hyperspectral remote-sensing preprint is closer in representation but weaker in publication status. It finds that random overlapping patches can produce much higher apparent performance than spatially separated sampling across several model families. Treat it as current adjacent evidence, not settled authority or an Artemis effect estimate.

## Decision

Stage 10M's recommendation survives external pressure: reconstructed camera action is a justified minimum grouping key for the exact representation and bracket-sibling dependence in the verified cohort. It is not automatically the final grouping key. Scene, target, time, observer, or source episode can be the correct broader group for a particular task.

## Ceiling

No model was trained on Artemis II data, no performance inflation was observed, and no existing pipeline was inspected. The external studies cannot supply an Artemis II effect size. They support the mechanism and grouped-split design principle only.
