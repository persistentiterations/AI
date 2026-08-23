# FPG-EXP-002 — Physarum Source Qualification and Frozen Test Contract

**Date:** 2026-08-23  
**Status:** `ADVANCE_TO_MEASUREMENT_FREEZE_ONLY`  
**Scientific result:** None yet. No predictive model has been fit and no hypothesis outcome has been revealed.  
**Natural Math morphology status:** Frozen and untouched. G1, G1B, and G1C were not rerun or repaired. No new morphology simulation was started.

## 1. Decision

The spider archive considered in FPG-EXP-001 cannot support the strong registered comparison because it did not directly record the evolving web structure. A newly released *Physarum polycephalum* source is materially better matched: it records the complete visible organism/network repeatedly through time in a stationary arena and publishes one video for each of 12 separate organisms.

The source passes authenticity, access, individual-identity, sequential-order, and gross visual-state gates. It does **not** yet pass the measurement gate because the authors did not publish their Ilastik project, binary masks, manual event annotations, original still images, or a mapping from deposited MP4 frames to the full acquisition timeline.

Therefore the allowed next action is to freeze and validate an image-to-state measurement adapter on a development organism. Statistical testing remains prohibited until that adapter meets the gates in section 8.

## 2. Primary sources and frozen receipts

### Scientific source

- Chen, Tan, Mundewadi, Riedel-Kruse, and Cira (2026), *A traveling network model predicts emergent dynamics and search behavior from local remodeling in Physarum polycephalum*, bioRxiv preprint, DOI: https://doi.org/10.64898/2026.08.13.744445
- The paper reports images every five minutes for 83.25–143 hours in 12 separate organisms on nutrientless agar, with no added food or water during free exploration.
- It reports that images were binarized in Ilastik and overlaid to create a full organism history; branching and retraction quantities were then measured from the sequences.

### Public data

- Zenodo record: https://doi.org/10.5281/zenodo.21908143
- Record title: *Videos of Physarum polycephalum*
- Publication date: 2026-08-12
- License: CC BY 4.0
- Record metadata SHA-256: `ae8ff6d9352be520afd36b315a7e7e51020666ec20a104d4b04ad87739ce399d`
- Deposit contents: 12 MP4 files, identifiers `Id1` through `Id12`, total local size approximately 77 MiB.
- All 12 downloaded MD5 values exactly matched the checksums supplied by Zenodo.

### Public code

- Repository: https://github.com/CiraLab/AvoidantTravelingNetworks
- Inspected commit: `062b34989ad7905643029d4adcb87715261cad50`
- Commit time: 2026-08-17T15:49:35-04:00
- Repository `README.md` SHA-256: `563eb6130b062d1ca0f90795e04551bd0abebd05ee415b1ba04b1d7c10cbb1da`
- The repository contains MATLAB implementations of the base, self-avoidant, and memory-avoidant traveling-network simulations.
- It does not contain the experimental image segmentation, registration, event extraction, or manual annotation pipeline. It is model code, not a complete empirical reproduction package.

## 3. Verified data inventory

All files are H.264, 1920 × 1080 pixels, and encoded at 10 display frames per second. The experimental cadence is taken from the paper as one acquisition image every five minutes; MP4 playback rate is not treated as experimental time.

| Organism | Frames | Video duration (s) | Zenodo MD5 |
|---|---:|---:|---|
| Id1 | 613 | 61.3 | `ccfc3a72c462289ec871b95eae8d2422` |
| Id2 | 749 | 74.9 | `68a4c741985feb8cefbfcf469fbe94fe` |
| Id3 | 636 | 63.6 | `4e8c24b911a950bd8423e10a8451242b` |
| Id4 | 1,716 | 171.6 | `555060f439906fcc38578a9fb74a7468` |
| Id5 | 657 | 65.7 | `bf91a4bfa961234b06777efd9a025bab` |
| Id6 | 567 | 56.7 | `f674fbc00b7870664bcda03c25fd8a53` |
| Id7 | 725 | 72.5 | `384f20e0d9196647d78e375a9c6ec7d7` |
| Id8 | 700 | 70.0 | `6424c8b7bd44e831a3f0a04795483736` |
| Id9 | 628 | 62.8 | `642e4699f246ad217c57f5a4ad50a4bd` |
| Id10 | 591 | 59.1 | `58424a3f94511ef3dcf07cbcc84871ad` |
| Id11 | 680 | 68.0 | `ab52114fa118d0d986f6f593df6f8e88` |
| Id12 | 650 | 65.0 | `f3a91f54017fb1db0dcbd7507aaf0eef` |

No exact decoded-frame duplicates were found in the inspected sequence. A low-resolution duplicate screen initially flagged 14 near-identical Id6 frames, but full-resolution decoded hashes showed that they were not exact duplicates.

## 4. Material caveat about “raw” status

The paper says that at least 999 images were acquired for each organism, except that some acquisitions extended to 143 hours. Eleven of the 12 deposited MP4s contain fewer than 999 frames; Id4 contains 1,716. The likely explanations include removal of the organism-specific transient or other trimming, but the deposit does not document the mapping.

Accordingly:

- frame order is usable;
- a five-minute nominal interval is supportable from the paper;
- absolute time since inoculation is not yet supportable;
- undocumented missing-frame or trimming assumptions must not be invented;
- analyses that require the excluded transient or exact absolute timestamps are prohibited.

## 5. Exact relation to the frozen Stage 20 causal organization

This is a focused transfer test, not a whole-model validation.

| Frozen causal element | What the Physarum source can test | Status |
|---|---|---|
| Local transport through an extant network | Visible tubes supply current network morphology, but flow is not measured in the deposit. | Partial only |
| Delayed acquisition of capability | No direct capability or maturation variable is recorded. | Not tested |
| Event-dependent change in future admissibility | Prior spatial occupancy can be reconstructed using past frames only and tested against subsequent local expansion. | **Primary target** |
| Bounded, use-dependent persistence | Local tube retention or retraction can be derived from successive visible masks if measurement reliability passes. | Secondary target |
| No supplied target morphology | Organisms explored nutrientless agar with no food or water added during imaging. | Good match |
| Strictly local decision context | Candidate future expansion can be evaluated from a frozen local neighborhood of the present boundary. | Good match |

A positive result would support only this bounded statement:

> Past local occupancy carries reproducible information about subsequent local remodeling after the currently visible network state is controlled.

It would not show that Physarum implements Stage 20, validate the full Formative Propagation Grammar, or establish a universal morphogenetic law.

## 6. Frozen scientific question

For spatial candidates immediately adjacent to the currently visible organism boundary, does past occupancy improve prediction of new occupancy at the next registered horizon after current morphology and arena position are included?

Define:

\[
M_S: P(Y_{i,t+h}=1\mid S_{i,t})
\]

\[
M_H: P(Y_{i,t+h}=1\mid S_{i,t},H_{i,t})
\]

where candidate location \(i\) is unoccupied at time \(t\), lies within the frozen boundary band, and \(Y_{i,t+h}=1\) means that it becomes newly occupied at the primary future horizon.

### Primary horizon

- Three acquisition frames, nominally 15 minutes.
- One-frame and six-frame horizons are sensitivity analyses only.

### Present state \(S_{i,t}\)

- current binary organism mask in a frozen local window;
- distance and orientation relative to the current boundary;
- local boundary curvature;
- local visible tube density and thickness summaries;
- current total visible organism area and skeleton length;
- fixed arena coordinates and distance to the plate boundary;
- deposited-frame index represented by a prespecified coarse time basis.

### Past-only history \(H_{i,t}\)

- whether the location was previously occupied;
- time since most recent prior occupancy, censored at a frozen maximum;
- cumulative number of prior occupied frames;
- cumulative occupancy in the frozen local window;
- most recent local departure direction, where determinable.

No feature may use frame \(t+1\) or later. The current mask must be derived from frame \(t\) alone; temporal smoothing that reaches into the future is prohibited.

## 7. Frozen evaluation structure

### Development and test separation

- `Id1` is the sole development organism for segmentation, registration, scale calibration, candidate construction, and quality thresholds.
- `Id1` is permanently excluded from the final scientific effect estimate.
- `Id2`–`Id12` are evaluation organisms.
- Once the adapter is frozen, measurement must run without organism-specific parameter tuning.

### Model comparison

- Paired regularized logistic classifiers with identical preprocessing, interaction policy, and nested regularization selection.
- `M_H` may differ from `M_S` only by addition of the frozen history block.
- Primary outer evaluation: leave one entire organism out across `Id2`–`Id12`.
- Spatial candidates from the same frame must receive equal total weight so that large boundaries do not dominate.
- Primary score: held-out log loss.
- Secondary scores: Brier score, area under the precision–recall curve, calibration slope/intercept, and per-organism event prevalence.

### Controls

1. Shuffle history within organism, coarse time bin, arena annulus, and present-state propensity stratum.
2. Repeat after excluding locations where the current image contains visible residue that may directly reveal prior occupancy.
3. Repeat within coarse organism-size/time strata.
4. Compare to a coordinate-only nuisance model to detect arena-position leakage.
5. Report results with and without the first 10% of deposited frames; do not call this the undocumented acquisition transient.

### Advance criterion

Call `PHYSARUM_HISTORY_INCREMENT` only if all are true:

1. `M_H` reduces mean held-out log loss by at least 1% relative to `M_S`.
2. The 95% organism-cluster bootstrap lower bound on improvement is above zero, using a frozen seed and 10,000 resamples.
3. At least 8 of the 11 evaluation organisms show positive log-loss improvement.
4. Ordered history beats the matched shuffled-history control.
5. The result survives coarse time/size stratification and the visible-residue exclusion.
6. Every measurement and feature passes the no-future-leakage audit.

### Other permitted outcomes

- `SNAPSHOT_CLOSURE`: present visible state absorbs the history increment.
- `HISTORY_PROXY_FOR_TIME_OR_LOCATION`: the increment fails time/size or arena-position controls.
- `MEASUREMENT_FRAGILITY`: the result changes materially across prespecified valid mask thresholds.
- `AMBIGUOUS`: uncertainty or usable organism count is insufficient.
- `DATA_NOT_QUALIFIED`: the measurement adapter fails the gates below.

## 8. Measurement gates before any model fit

The adapter must pass all of these on frozen samples before outcomes are computed:

1. **Registration:** plate-relative drift below one analysis-grid cell for at least 99% of adjacent frame pairs.
2. **Segmentation agreement:** blinded human review of a frozen set of development frames, plus a second independent threshold/segmentation method, must agree on organism occupancy above a frozen IoU threshold.
3. **Thin-tube recall:** a separately reviewed set of fine distal tubes must meet a frozen recall threshold; gross-area agreement alone is insufficient.
4. **Temporal consistency:** implausible one-frame births/deaths above a frozen area threshold must be below a frozen rate.
5. **Scale:** the visible 1 cm scale bar must yield a reproducible pixel calibration or the analysis must remain explicitly pixel-based.
6. **Candidate stability:** event prevalence and candidate counts must remain finite and nondegenerate across all 11 evaluation organisms.
7. **Provenance:** adapter code, configuration, sampled QA frames, split file, and feature schema must be hashed before evaluation labels are summarized.

Failure of any gate produces `DATA_NOT_QUALIFIED`; thresholds must not be relaxed after observing the history comparison.

## 9. Interpretation boundary

Prior work experimentally showed that *P. polycephalum* can avoid extracellular slime deposited in previously explored regions, supporting an externalized spatial-trace mechanism. The 2026 preprint also treats avoidance as probabilistic rather than strict and reports too few crossing events for strong organism-level conclusions about size dependence.

This experiment is observational. Even a robust history increment would not by itself prove that extracellular slime, internal biochemical memory, or a specific mechanical mechanism caused the effect. “History” is therefore used as an operational past-occupancy variable, not as a claim of neuronal-style memory or accurate stored representation.

## 10. Next authorized action

Build and freeze only the measurement adapter on `Id1`, including a small auditable QA packet. Do not fit `M_S` or `M_H`, inspect their coefficients, or compute any history increment until the adapter, split, and scoring contract are hashed.

This is the clean next test because it uses an empirical, independently generated, no-target remodeling system and can fail at the measurement gate without modifying the hypothesis or returning to morphology simulation.
