# Stage 10U external method screen — 10 October 2026

## Decision this screen can change

Whether the observed Artemis II camera/target association should be treated as a prospective image-model confounding canary, or merely as an inert metadata curiosity. The screen can nominate a control and evaluation requirement; it cannot establish that Artemis II pixels encode camera identity or that any model would use it.

## Sources inspected

- NASA PDS, *Artemis II Lunar Science Data User Guide*, preserved locally at `evidence/stage10d/source/artemis2_data_user_guide.txt`, especially the camera roles, image-sequence design, and target-tag limitations.
- Jackson et al., “Camera Bias in a Fine Grained Classification Task,” arXiv:2007.08574: <https://arxiv.org/abs/2007.08574>
- DeGrave et al., “AI for radiographic COVID-19 detection selects shortcuts over signal,” *Nature Machine Intelligence* 3 (2021): <https://www.nature.com/articles/s42256-021-00338-7>
- Hill, Koback, and Schilling, “The risk of shortcutting in deep learning algorithms for medical imaging research,” *Scientific Reports* 14 (2024): <https://www.nature.com/articles/s41598-024-79838-6>

## Findings

The Artemis II guide independently states that the Z9 was the primary eclipse camera and that image sequences were deliberately varied. It also says target tags were manually assigned for only a subset and were not thoroughly verified. The local contingency is therefore operationally plausible but not a label-ground-truth result.

The external studies establish the mechanism class, not an Artemis II outcome. Jackson et al. directly demonstrate that camera/class correlations can be exploited by image classifiers and can fail when the correlation or camera changes. DeGrave et al. and Hill et al. show the broader acquisition-source shortcut problem and why strong internal scores do not by themselves identify the intended visual signal. None inspected Artemis II data.

## Decision impact

Treat camera serial as a mandatory diagnostic variable if a future Artemis II target classifier is proposed. Report a camera-only baseline before a pixel model, expose unsupported camera/target cells, and test camera-held-out or balanced conditions separately where the task permits. Do not claim mitigation from a random split, preprocessing, or camera balancing alone; the Stage 10T single-event limit remains controlling for new-Sunset-event generalization.

Do not train a pixel model merely to dramatize this risk. The current result already changes the evaluation design at negligible additional burden. Pixel access becomes decision-relevant only after a real target-classification estimand and an admissible test population exist.

## Recheck trigger

Reopen when a public Artemis II image model, benchmark, or split manifest exists; when target labels are independently validated; or when comparable target events create a camera/event-stratified test population.
