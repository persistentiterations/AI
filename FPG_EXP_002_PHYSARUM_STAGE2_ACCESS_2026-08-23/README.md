# FPG-EXP-002 Physarum — Stage 2 access mirror

This directory exists solely to make the FPG-EXP-002 reproducibility materials individually browsable for independent Stage 2 reviewers that cannot ingest ZIP archives.

## Authority and claim boundary

- Original experiment date: 2026-08-23.
- Original verdict: `PHYSARUM_HISTORY_INCREMENT`.
- Claim level: empirical, predictive, substrate-specific, observational.
- This access mirror does **not** modify the experiment, scoring freeze, preregistration, result, or any Natural Math morphology artifact.
- The original ZIP remains the canonical packaged bundle. Files under `original_text/` are copied byte-for-byte from its text members where possible.
- `derived_access/` contains non-authoritative convenience material generated only to describe binary members for reviewers that cannot open `.npz` files.

## Start here

1. `original_text/FPG_EXP_002_PHYSARUM_SOURCE_QUALIFICATION_AND_PREREGISTRATION_2026-08-23.md`
2. `original_text/FROZEN_PRE_EVALUATION_RECEIPT.json`
3. `original_text/FROZEN_SCORING_RECEIPT.json`
4. `original_text/physarum_test_config.json`
5. `original_text/physarum_history_test_primary_reveal.py`
6. `original_text/physarum_test_result.json`
7. `original_text/FPG_EXP_002_PHYSARUM_FINAL_BOUNDED_REPORT_2026-08-23.md`
8. `original_text/MANIFEST_SHA256.txt`
9. `original_text/REPRODUCE.md`

## Binary evidence

The original bundle also contains `.npz` event/prediction arrays and `qa/ID1_SEGMENTATION_QA_CONTACT.jpg`. Those binary members cannot be faithfully uploaded through the current ChatGPT GitHub text-file write interface. Their original SHA-256 values remain in `MANIFEST_SHA256.txt`.

`derived_access/MODEL_READABLE_BINARY_INDEX.json` provides array names, shapes, dtypes, byte sizes and summary statistics from the exact uploaded ZIP. It is an access aid, **not** a substitute for the original binary bytes and must not be treated as independent evidence.

A reviewer unable to inspect the original binary members should mark binary-level recomputation `NOT VERIFIED` rather than infer it.

## Review rule

Review the experiment on its own terms. Do not use Baby AI, Natural Math, Stage 20, CRR, DEC, FFC, or other cross-domain interpretations during Stage 2.
