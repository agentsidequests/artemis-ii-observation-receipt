# Stage 10N public-adoption screen — 10 October 2026

## Decision this screen can change

Whether the split-hazard lead can responsibly criticize an existing Artemis II camera-image machine-learning pipeline, or must remain a prospective evaluation-design warning.

## Release-age baseline

NASA's public release notice is dated 7 October 2026 and describes the PDS upload as newly available for public exploration and analysis:

- <https://www.nasa.gov/blogs/artemis/2026/10/07/nasa-releases-artemis-ii-lunar-science-data-images/>
- <https://pds-geosciences.wustl.edu/missions/artemis2/index.htm>

The archive had therefore been public for about three days when this screen ran.

## Bounded discovery routes

The screen searched the public web, GitHub repository metadata, arXiv, and Hugging Face for combinations of `Artemis II`, image or camera data, machine learning or computer vision, the PDS bundle identifier `artemis2_crew_camera`, collection names, and sample internal IDs.

Visible public results included:

- Artemis II trajectory, mission-summary, text, and synthetic-simulator datasets on Hugging Face, but no located PDS crew-camera image-model training pipeline: <https://huggingface.co/datasets/juliensimon/artemis-ii>
- Artemis II gallery, risk-modeling, trajectory, telemetry, and human-research repositories on GitHub, but no located repository whose training split uses the current PDS crew-camera products.
- one Artemis II F-corona analysis using a released rendered image, not the current PDS complete-action cohort or an image-model train/test split: <https://arxiv.org/abs/2604.13908>

Exact-string searches for the crew-camera bundle identifier, `data_source` / `data_raw` / `data_processed` collection structure, and representative `art002e` identifiers did not locate a public image-model pipeline to inspect. Search absence is not proof that none exists.

## Decision

No actual Artemis II camera-image ML split was identified in this bounded screen. The current lead must remain prospective: the archive structure creates a measurable risk for a naïve future pipeline, but this Testbed cannot say that current researchers, NASA, PDS, or a named model have leaked data or inflated performance.

The release age increases the practical value of an early split-design warning while decreasing the credibility of any adoption or priority claim. Recheck only when a public training repository, dataset card, paper, benchmark, or split manifest references the PDS crew-camera bundle or its stable identifiers.

## Ceiling

This screen is bounded, indexing can lag, private work is invisible, and terminology can differ. It supports `NO LOCATED PIPELINE TO AUDIT`, not `NO PIPELINE EXISTS`, `FIRST WARNING`, or any global novelty claim.
