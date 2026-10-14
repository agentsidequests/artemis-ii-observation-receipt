# Artemis II v1.0.0

An independent, open-source research prototype by agentsidequests. Interactive Science for All is the ambition, not a measured all-age learning result. This project is not affiliated with or endorsed by NASA, PDS or JPL. It is not specialist-approved.

## What is in v1

- **Explore:** a photographic investigation of what the archive counts can and cannot tell us, including a bounded factual summary of the exchange with JPL.
- **Play:** three clearly labeled teaching experiments about grouped tests, missing fields and detection. They are not new mission measurements or trained ML results.
- **Use:** current identity, historical identity, weighting-sensitivity and flash-receipt applications, plus portable source downloads.
- **Inspect:** the full technical notebook, exact math, pinned evidence, uncertainty, rejected interpretations and two separate proposed pilots.

V1 publishes an existing tested analysis and adds a static hosting projection. The native evidence, scientific calculations, original populations and historical controls are unchanged. Hosted photographs retain their exact image bytes but load as separate cacheable assets. Older dated files are preserved as historical reading copies, not proof of current publication or acceptance state.

## Reproduce and deploy

The Python app and replay paths are documented in [README](README.md) and [reproducibility](REPRODUCIBILITY.md). To prepare the website with Node.js 24, without installing packages:

```text
node tools/build_site.mjs
node --test tests/site-release.test.mjs
```

The output is `site/`. Vercel reads `vercel.json`: framework Other, no install command, build command `node tools/build_site.mjs`, output directory `site`. Connect this repository, not a ZIP. The complete source ZIP belongs in GitHub Releases, not in Git history or the hosted website.

The website has no account system, database, paid API, analytics library, tracking cookie or runtime package. The hosting provider still processes normal request data under its own terms. On-page lesson settings remain in the page session. Downloads are deliberately user-triggered. External citations and GitHub source links require a network connection; the complete source package retains the offline previews.

## Verification and recovery

The release tests verify hosting inputs, publication labels, image-byte custody, local-link coverage, no invented source download and deterministic output. Verify the deployed entry, all four modes, four apps, JSON download, source release link, mobile layout and response headers after deployment. Passing local checks is not proof of deployment, human comprehension, accessibility certification or scientific acceptance.

Future updates should use a new version and tag. Keep `v1.0.0` fixed. Roll back a defective hosting change by redeploying the last verified commit in Vercel; GitHub retains the released source. Reverting a public repository to private does not recall downloaded copies. Report reproducible defects or bounded scientific corrections through this repository's issues; do not submit personal information, credentials or private correspondence.

## Research boundaries

These are metadata-accounting and methodological findings, not new lunar-science discoveries. JPL confirmed one image pair, not a global duplicate census. Hypothetical splits do not show a NASA model leaked or was harmed. Recorded fields are not validated image content. Concentration is not effective sample size. The flash analysis does not establish event photometry, physical brightness, human thresholds, precise locations, crater confirmation, calibrated impact flux or physical clustering. The full notebook retains exact qualifications and proposed, unaccepted recommendations.

Original work is MIT licensed. NASA/PDS/JPL material and third-party sources retain their own terms and credits. See [third-party notices](THIRD-PARTY-NOTICES.md). AI assistance is disclosed in the README.
