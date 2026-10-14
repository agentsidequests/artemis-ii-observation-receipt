# Stage 10S current framing screen — 10 October 2026

## Decision this screen can change

Whether the plan-bounded Sunset result is merely another generic warning about grouped splitting, or a differentiated Artemis II insight worth promoting above the earlier 144-second microcase. The screen can change framing and the next test; it cannot establish global novelty or priority.

## Sources inspected

- NASA, “NASA Releases Artemis II Lunar Science Data, Images,” 7 October 2026: <https://www.nasa.gov/blogs/artemis/2026/10/07/nasa-releases-artemis-ii-lunar-science-data-images/>
- NASA Science, “Artemis II Preliminary Lunar Science Report,” accessed 10 October 2026: <https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/>
- NASA PDS, “Artemis II Mission,” accessed 10 October 2026: <https://pds-geosciences.wustl.edu/missions/artemis2/index.htm>
- NASA PDS, *Artemis II Lunar Science Data User Guide*, preserved locally at `evidence/stage10d/source/artemis2_data_user_guide.txt`, especially §§3.1.1, 5, 5.2.2–5.2.4, 5.2.6, and 5.6.2.
- scikit-learn, `GroupShuffleSplit` documentation: <https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html>
- Baygin, Dogan, and Tuncer, “Model validation in machine learning: A scenario-based guide from hold-out splits to nested group cross-validation in biomedical and applied research,” arXiv:2610.01284, 1 October 2026: <https://arxiv.org/abs/2610.01284>
- Exact public searches for `"2,535" "Artemis II" Sunset data`, `"845" exposures "Artemis II" Sunset`, `"Artemis II" Sunset dataset machine learning split`, and `"artemis2_crew_camera" Sunset analysis`.

## Findings

NASA presents the release as more than 800 GB, more than 11,000 full-resolution images and video, 8.5 hours of audio, and annotations. The preliminary report specifically describes the eclipse as a rare opportunity to observe the evolving solar corona. The Data User Guide explains why repeated records are expected: image sequences were driven by the targeting plan; crews captured multiple images over one target for HDR and mosaics; settings changed within sequences; and the Z9 was the primary camera for eclipse observations. It separately defines source NEFs, PDS raw TIFFs, and processed TIFFs. The archive multiplication and local dependence are therefore part of the scientific acquisition and preservation design, not by themselves a duplication defect.

The Data User Guide also prevents overclaiming. Scheduled activity is assigned from the timeline with possible analyst overrides. Primary targets were manually tagged for only a subset and were not thoroughly verified post-mission. The fixed 00:36–00:44 plan boundary is therefore stronger than choosing a visually impressive interval from the data, while unanimous `Sunset` target labels inside that window remain corroboration rather than ground truth.

The external validation literature supports the general method but does not supply an Artemis II result: the independent unit must match the deployment target, and grouping should preserve domain-defined dependence. That principle is established prior art. The differentiated local contribution is the exact collapse for one planned event: `2,535 products → 845 exposures → 169 actions → 1 scheduled Sunset block`, with a `200.901668231 GB → 17.257373901 GB` retrieval-footprint-to-source decomposition. Exact searches did not locate those counts or an event-level Artemis II split analysis. Search absence is not proof of novelty.

## Decision impact

Promote the plan-bounded event-level sample-count collapse above the 144-second microcase. The stronger insight is not that the archive has derivatives or that grouped splitting exists. It is that the release can look enormous in both files and bytes while still supplying one independent event for a new-Sunset-event estimand. A correct episode-safe split exposes an insufficiency that a naïve random split conceals: Artemis II alone cannot place different Sunset events in training and test because the mission plan contains one Sunset entry.

Keep the claim conditional on the task. A within-event forecasting, reconstruction, denoising, or representation task could use a time-forward or action-aware split, but it must not be presented as new-event generalization. No current Artemis II camera-image ML pipeline was located, so the warning remains prospective rather than an accusation of observed leakage.

## Recheck trigger

Re-run the search when a public paper, benchmark, dataset card, split manifest, or repository uses the PDS crew-camera bundle; when a second comparable Sunset event becomes available; or immediately before publication.
