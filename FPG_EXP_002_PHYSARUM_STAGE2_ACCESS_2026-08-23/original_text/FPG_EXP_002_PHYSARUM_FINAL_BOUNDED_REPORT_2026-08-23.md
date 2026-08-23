# FPG-EXP-002 — Final Bounded Physarum History Test

**Date:** 2026-08-23  
**Final verdict:** `PHYSARUM_HISTORY_INCREMENT`  
**Claim level:** Empirical, predictive, substrate-specific, and observational  
**Natural Math morphology status:** Frozen and untouched. G1, G1B, and G1C were not rerun or repaired. No morphology simulation was started.

## 1. Result in one sentence

Across 11 completely held-out *Physarum polycephalum* organisms, past local occupancy improved prediction of stable local expansion beyond the currently visible network, arena position, organism size, and nominal time: mean held-out log loss fell from **0.15983** to **0.14776**, a **7.55% relative improvement**.

This satisfies the preregistered `PHYSARUM_HISTORY_INCREMENT` criteria. It does not establish that history is the sole cause, identify the physical carrier, or validate the entire frozen Stage 20 mechanism.

## 2. Source and independent-data basis

The experiment used the public data accompanying:

- Chen, Tan, Mundewadi, Riedel-Kruse, and Cira (2026), *A traveling network model predicts emergent dynamics and search behavior from local remodeling in Physarum polycephalum*, bioRxiv, https://doi.org/10.64898/2026.08.13.744445
- Public videos: https://doi.org/10.5281/zenodo.21908143
- Authors' model code: https://github.com/CiraLab/AvoidantTravelingNetworks

The study recorded 12 separate organisms on nutrientless agar without additional food or water during imaging. The deposit supplies one MP4 sequence per organism. All 12 downloaded files matched their published Zenodo MD5 checksums.

The authors did not publish their Ilastik project, masks, event annotations, or original still-image timeline. Therefore a new adapter was developed on `Id1` only; `Id1` was then permanently excluded from the scientific effect estimate.

## 3. Frozen test

For currently unoccupied spatial cells immediately adjacent to the visible organism boundary, the test predicted stable new occupancy three acquisition frames later, nominally 15 minutes.

Two otherwise identical regularized logistic models were compared:

\[
M_S: P(Y_{i,t+3}=1\mid S_{i,t})
\]

\[
M_H: P(Y_{i,t+3}=1\mid S_{i,t},H_{i,t})
\]

`M_S` contained the current 3×3 occupancy patch, wider local occupancy summaries, local boundary gradients, current color/contrast score, arena coordinates, distance from the plate boundary, current organism area, and deposited-frame index.

`M_H` added only past-derived quantities: previous occupancy, time since previous occupancy, cumulative occupation, departure count, and local previous/recent occupancy summaries. No feature used a frame after the prediction timestamp.

Evaluation used leave-one-whole-organism-out folds over `Id2`–`Id12`. Candidate locations from each frame received equal total weight.

## 4. Measurement gate

The single-frame segmentation adapter was frozen after `Id1` development and before processing `Id2`–`Id12`.

| QA measure | Frozen gate | Observed | Result |
|---|---:|---:|---|
| Median IoU between uniform- and Gaussian-background methods | ≥ 0.85 | 0.9184 | Pass |
| Minimum sampled IoU | ≥ 0.70 | 0.9012 | Pass |
| Mean thin-tube recall | ≥ 0.80 | 0.9050 | Pass |
| Minimum thin-tube recall | ≥ 0.60 | 0.8343 | Pass |
| One-frame flash fraction | ≤ 0.05 | 0.0152 | Pass |
| Registration pass fraction | ≥ 0.99 | 1.0000 | Pass |

Thirteen evenly spaced visual overlays also passed manual review inside the frozen eligible arena. Regions near the plate rim and the stationary center glare were excluded rather than repaired.

## 5. Primary held-out result

- Eligible candidate decisions: **425,814**
- Stable positive expansion events: **14,679**
- Held-out organisms: **11**
- Mean snapshot log loss: **0.1598307**
- Mean history log loss: **0.1477628**
- Mean absolute improvement: **0.0120678**
- Relative log-loss improvement: **7.5504%**
- Organism-cluster bootstrap 95% interval for the absolute improvement: **[0.0070211, 0.0169465]**
- Organisms with positive improvement: **9 of 11**

All three primary gates passed: improvement exceeded 1%, the bootstrap lower bound was above zero, and at least 8 of 11 organisms improved.

### Per-organism results

| Held-out organism | Snapshot loss | History loss | Relative improvement |
|---|---:|---:|---:|
| Id2 | 0.20309 | 0.17516 | +13.75% |
| Id3 | 0.12437 | 0.11007 | +11.50% |
| Id4 | 0.12079 | 0.12258 | **−1.48%** |
| Id5 | 0.14476 | 0.12514 | +13.55% |
| Id6 | 0.17453 | 0.17690 | **−1.36%** |
| Id7 | 0.18930 | 0.17524 | +7.43% |
| Id8 | 0.14294 | 0.12995 | +9.09% |
| Id9 | 0.10520 | 0.09740 | +7.42% |
| Id10 | 0.15927 | 0.14782 | +7.19% |
| Id11 | 0.19686 | 0.18683 | +5.10% |
| Id12 | 0.19704 | 0.17831 | +9.50% |

The two negative organisms are retained. The result is a reproducible average tendency, not an invariant rule for every organism.

## 6. Frozen controls

| Control | Result | Gate |
|---|---|---|
| Matched shuffled history | Ordered history beat shuffled history in 11/11 organisms; mean loss advantage 0.05443 | Pass |
| Visible-residue exclusion | Mean relative improvement 8.59%; positive in 10/11 organisms | Pass |
| Coarse time strata | Mean improvement positive in all four quartiles | Pass |
| Organism-area strata | Mean improvement positive in all four quartiles | Pass |
| Coordinate-only nuisance model | Mean loss 0.16319, worse than both snapshot and history models | Diagnostic pass |

The visible-residue control excluded the top decile of current color/contrast scores among candidate cells. The retained effect therefore cannot be explained solely by obvious currently visible residue at previously occupied locations.

## 7. Prespecified sensitivity analyses

| Variant | Relative improvement | Positive organisms | All gates |
|---|---:|---:|---|
| 5-minute horizon | 6.41% | 10/11 | Pass |
| **15-minute primary horizon** | **7.55%** | **9/11** | **Pass** |
| 30-minute horizon | 6.13% | 10/11 | Pass |
| Thin occupancy: ≥2 pixels per 8×8 cell | 7.58% | 9/11 | Pass |
| Thick occupancy: ≥8 pixels per 8×8 cell | 8.63% | 10/11 | Pass |

The direction and decision-level verdict are stable across all five timing and measurement variants.

## 8. What the result means for the frozen work

The data support one bounded part of the causal organization under examination:

> Realized local history changes what is predictively likely next, even after a substantial representation of present visible structure is included.

This is relevant to Stage 20's event-dependent change in future admissibility. It supplies independent empirical evidence that a snapshot-only description is incomplete in this living remodeling system.

It does **not** test or validate:

- Stage 20's delayed acquisition of capability;
- actual transport or flow through the visible tubes;
- use-dependent persistence as a distinct causal variable;
- the exact Stage 20 state variables or update equations;
- Natural Math as a universal morphogenetic theory;
- Jim's broader Formative Field Computing or Conditional Reconstructive Recruitment claims.

## 9. Scientific limitations

1. **Observational prediction is not intervention.** A history increment does not identify the physical cause. Extracellular slime, unmeasured chemistry, mechanical state, or another persistent trace could carry the information.
2. **The source is a 2026 preprint.** It had not completed peer review when this test was run.
3. **The adapter is independent.** It was not the authors' unpublished Ilastik segmentation and may encode different measurement errors.
4. **The deposit is trimmed or incomplete relative to the acquisition description.** Eleven MP4s have fewer than the paper's stated minimum of 999 images. Frame order and nominal cadence are usable, but absolute time since inoculation is not.
5. **The present-state representation is substantial, not exhaustive.** It includes current visible morphology, image contrast, position, size, and time, but not tube flow, chemical concentrations, or local forces.
6. **Two organisms did not benefit.** The effect should not be described as universal at the individual level.

## 10. Final bounded conclusion

`PHYSARUM_HISTORY_INCREMENT` is supported under the frozen protocol.

The strongest honest statement is:

> In this public *P. polycephalum* dataset, past local occupancy adds robust organism-held-out predictive information about subsequent local expansion beyond the currently visible network and measured nuisance state. The increment survives matched history shuffling, visible-residue exclusion, time and size stratification, three prediction horizons, and three occupancy thresholds.

This increases the empirical plausibility of event-dependent future admissibility as a transferable organizational principle. It does not prove the complete Natural Math mechanism or the biological carrier of the history effect.

## 11. Frozen receipts and principal hashes

- Primary-reveal code SHA-256: `13943bcde1b27327cecfb96b4e8a9fa7d3b19fb57182d23eb8e5b87e6884e1c8`
- Primary scoring configuration SHA-256: `fdcbf8e8efef938b172927c3a1ac464cec21738be6394971ae77211e3b06799f`
- Primary event table SHA-256: `a129b47aa9c1b07222036b6597cecfec541106cb64490da3fb46d848403299b0`
- Primary result SHA-256: `a3484cfea71cfde74eb8004edd0728896a6579b1cff8cf2641668de2b197fd6d`
- Frozen predictions SHA-256: `68f8e3299deb6c29d1998d0145af2b60c30d530e5ea7bb03da42bb4b020feab8`
- 5-minute sensitivity result SHA-256: `b794dd407ec0fef7c5a8e2301b2ef86fdb3b880a9b68ecb6bb38737a3f11ee8c`
- 30-minute sensitivity result SHA-256: `aad4d366a4aed45daf18cf5bf41912f84d25244615375af0ba05c2a4b6c8cf8d`
- Two-pixel sensitivity result SHA-256: `b4d2ca48b1b578c6c650f08d6175379ef247212b8840969c7da7c134736cbbaa`
- Eight-pixel sensitivity result SHA-256: `d525e3f768e942b3a9d8b112143f28149e515377177c2b7d4c48013e47c8b94f`

The morphology archive and all G-series artifacts remain separate and unchanged.
