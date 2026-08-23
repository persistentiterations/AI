# FPG-EXP-002 Physarum — Stage 2 access mirror

This directory exists solely to make the FPG-EXP-002 reproducibility materials individually browsable for independent Stage 2 reviewers that cannot ingest ZIP archives.

## Authority and claim boundary

- Original experiment date: 2026-08-23.
- Original verdict: `PHYSARUM_HISTORY_INCREMENT`.
- Claim level: empirical, predictive, substrate-specific, observational.
- This access mirror does **not** modify the experiment, scoring freeze, preregistration, result, or any Natural Math morphology artifact.
- The original ZIP remains the canonical packaged bundle.
- Files under `original_text/` are copied from original text members of that bundle where published here.
- `derived_access/` contains non-authoritative convenience material generated only to improve accessibility. Derived material must never be substituted for an original artifact in a claim of independent reproduction.

## Start here

1. `original_text/FPG_EXP_002_PHYSARUM_SOURCE_QUALIFICATION_AND_PREREGISTRATION_2026-08-23.md`
2. `original_text/FROZEN_PRE_EVALUATION_RECEIPT.json`
3. `original_text/FROZEN_SCORING_RECEIPT.json`
4. `original_text/physarum_test_config.json`
5. `derived_access/source_parts/README.md` and the four ordered primary-reveal source parts
6. `original_text/physarum_test_result.json`
7. `original_text/FPG_EXP_002_PHYSARUM_FINAL_BOUNDED_REPORT_2026-08-23.md`
8. `original_text/MANIFEST_SHA256.txt`
9. `original_text/REPRODUCE.md`
10. `derived_access/MODEL_READABLE_BINARY_INDEX.md`

Also available under `original_text/` are the environment receipt, source-video MD5 list, and Id1 QA CSV/JSON.

## Primary source accessibility

The exact frozen primary-reveal source has SHA-256:

`13943bcde1b27327cecfb96b4e8a9fa7d3b19fb57182d23eb8e5b87e6884e1c8`

For compatibility with reviewers that struggle to ingest larger source files through GitHub, its 638 lines are exposed in four ordered, line-preserving text parts under `derived_access/source_parts/`. The accompanying source-parts README records the order and the original source hash.

The later `physarum_history_test.py` sensitivity extension is represented by `derived_access/physarum_history_test_vs_primary.diff`, with its original SHA-256 recorded in the source-parts README and bundle manifest.

## Binary evidence

The original bundle also contains `.npz` event/prediction arrays and `qa/ID1_SEGMENTATION_QA_CONTACT.jpg`. Those binary members cannot be faithfully uploaded through the current ChatGPT GitHub text-file write interface. Their original SHA-256 values remain in `original_text/MANIFEST_SHA256.txt`.

`derived_access/MODEL_READABLE_BINARY_INDEX.md` exposes each binary member's SHA-256, byte size, and—where applicable—array names, shapes and dtypes, together with frozen result summaries derived from the exact uploaded ZIP. It is an access aid, **not** a substitute for the original binary bytes and must not be treated as independent reproduction.

A reviewer unable to inspect the original binary members should mark binary-level hash verification/recomputation `NOT VERIFIED` rather than infer it.

## Stage 2 review rule

Review the experiment on its own terms. Do not use Baby AI, Natural Math, Stage 20, CRR, DEC, FFC, or other cross-domain interpretations during Stage 2.
