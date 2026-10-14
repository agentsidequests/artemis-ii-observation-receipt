# Stage 11H adversarial estimand screen — 10 October 2026

## Decision this screen can change

Whether the denominator-and-weighting result can carry a later public analysis without implying that one counting unit is universally correct, that NASA misdesigned the archive, or that an unobserved model is already biased. This is a private pressure test, not a public draft, novelty proof, or publication decision.

## Strongest surviving claim

The archive does not possess one unit-neutral sample count or prominence ranking. Its file and byte totals answer storage and retrieval questions. Exposure, action, realized-segment, and planned-event units answer progressively different scientific or evaluation questions. Acquisition policy changes the mapping among them, so flattening the observation graph selects an estimand even when the analyst never names one.

The local evidence is now stronger than a generic warning:

- the planned Sunset block collapses from `2,535 products → 845 exposures → 169 actions → 24 conditional bursts → 1 scheduled event`;
- a conservative connected context expands the file-side counts to `4,290 products → 1,430 exposures → 286 actions` while the planned-event count remains one;
- the context is 13.204% of cohort actions, 18.801% of products, and 22.785% of bytes;
- among active plan windows, 38 of 621 strictly comparable pairs reverse order from action count to product count and 59 reverse from action count to bytes; and
- in the deduplicated plan-associated action union, five-exposure actions are 35.455% of actions but 47.794% of flat products, with their occurrence aligned to camera and contiguous time regimes; camera `3920019` alone rises from 10.130% of actions to 13.655% of products.

Sunset remains first by total actions, products, and bytes. That makes it a stable illustration, not evidence that the units are interchangeable.

## Task-to-estimand contract

| Practical question | Natural unit or weight | What the current Testbed can support | Main boundary |
| --- | --- | --- | --- |
| How many downloadable records or how much transfer is involved? | Product or byte | Exact dated Atlas product and byte ledgers | Says nothing by itself about independent observations or calibration |
| What does a randomly selected camera exposure look like? | Exposure identity | Exact exposure identities in the admitted complete-action cohort | Exposure brackets remain nested inside actions |
| What is typical of a physical bracket action? | Equal action weight | 2,166 reconstructed complete actions and exact product→exposure→action mapping | Action oracle is admitted, not exhaustive; broader scene dependence remains |
| Can a method generalize within one observation episode? | Task-defined action/run/segment grouping | Conditional temporal groups and one transcript-supported Sunset context | Thresholds are not scene truth; a realized-segment oracle is incomplete |
| Can a method generalize to a new scheduled observation event? | Equal event weight with event-held-out evaluation | Plan-window census and one Sunset scheduled event | Sunset has no second same-name event; schedule is not realized content truth |
| Which representation minimizes burden or supports human viewing? | Representation- and byte-aware | Source/raw/processed identities and footprints | No calibrated crew-camera tier is supplied |

No row is the universal correction. The task chooses the estimand; the observation graph makes the choice executable and auditable.

## Hard counterarguments and dispositions

| Counterargument | Disposition |
| --- | --- |
| “Uniform product weighting is perfectly legitimate.” | Correct for a random-product or retrieval-level question. It is not a neutral substitute for a random action, segment, or event. The analysis must name which question it answers. |
| “Five-exposure sequences deserve more weight because NASA deliberately captured more information.” | Possibly, for an exposure- or protocol-level estimand. Deliberate acquisition makes deletion inappropriate, but it does not automatically set the weight for new-action or new-event generalization. |
| “Equal action weighting throws away HDR information.” | False choice. All exposures can be retained inside a hierarchical or action-aggregated analysis while each action receives equal outer weight. The representation and estimand decisions are separate. |
| “Inverse cluster-size weighting fixes the problem.” | Not universally. It changes the estimand and requires a defensible cluster boundary. Planned windows overlap, realized segments are not yet fully registered, and formal informative cluster size has not been established. |
| “Sunset is largest under every total, so the unit issue is cosmetic.” | Rejected. The lead rank is stable, but its cohort share changes from 13.204% of actions to 18.801% of products and 22.785% of bytes; 38 and 59 other pairwise window orderings reverse. Magnitudes and comparisons change even when rank one does not. |
| “Camera/time alignment proves a shortcut.” | Rejected. Stage 11H is an in-sample metadata description. No pixel model, sampler, held-out performance, or causal pathway was tested. It is a prospective control requirement. |
| “The schedule already supplies event IDs.” | Rejected as a realized-content claim. Stage 10Z shows many-to-many membership, and Stage 11C shows the second Glushko schedule both misses transcript-indicated activity and retains actions after an explicit transition. |
| “Adding more context creates more independent samples.” | Rejected for the new-event question. The Sunset context gains products, exposures, and actions while the independently planned event count remains one. It may support narrower within-event questions only. |
| “This is evidence that the archive is defective.” | Rejected. Multiple representations, bracketed exposures, and planned sequences are intentional scientific and preservation design. The analytical duty is to preserve their relationships and choose a task-specific unit. |

## What this changes in a later analysis

The sharpest framing is no longer merely “thousands of files can be one event.” It is:

> The archive's acquisition and representation policies become an implicit sampling policy when the observation graph is flattened. The resulting answer may be correct for a random product while being wrong for the unstated action or event question.

The article should make one exact reversal concrete—Earthset has 60 actions and 900 products, while plan-order-2 Guided Discussion has 76 actions and 684 products—then use Sunset as the stable high-volume example. It should show the observation graph as the constructive remedy and distinguish preserving intentional data from choosing its outer statistical weight.

## Claim ceiling

This screen does not establish an actual sampler, observed leakage, model bias, performance inflation, a causal association between bracket length and image outcome, formal informative cluster size, a universally correct weight, archive defect, global novelty, priority, or a new lunar-science result. Search absence remains `NOVELTY_UNESTABLISHED`. The maintainer retains framing and publication decisions; qualified reviewers retain scientific acceptance.

## Recheck trigger

Re-run when a real Artemis II analytical task names its outcome and target population; when a public model, benchmark, split, or sampler exists; when realized segments or event identities are independently validated; or when the archive or action oracle changes.
