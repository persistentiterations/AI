# Reproducing FPG-EXP-002

Read `FPG_EXP_002_PHYSARUM_FINAL_BOUNDED_REPORT_2026-08-23.md` first.

## Inputs

Download the 12 videos from Zenodo record `10.5281/zenodo.21908143` and verify them against `SOURCE_VIDEO_MD5.txt`.

The primary event tables and frozen predictions are included, so the published primary scores can be inspected without rebuilding image masks.

## Primary single-reveal command

The exact primary code is `physarum_history_test_primary_reveal.py`, whose SHA-256 is recorded in the final report and scoring receipt.

```bash
python physarum_history_test_primary_reveal.py \
  --config physarum_test_config.json \
  test physarum_events.npz reproduced_primary_result.json
```

This reruns the frozen leave-one-organism-out scoring from the included event table. It will also write `physarum_predictions.npz` in the working directory.

## Rebuilding segmentation and events

The source videos must be placed in a local directory. For each video, run the `segment` command to create its grid-mask archive. Then place the archives in one directory using names such as `Id2_segmented.npz` and run:

```bash
python physarum_history_test_primary_reveal.py \
  --config physarum_test_config.json \
  events SEGMENT_DIRECTORY rebuilt_events.npz
```

`Id1` is development-only and must not be added to the evaluation event table.

## Files

- `physarum_test_result.json`: primary 15-minute result.
- `physarum_test_result_h1.json`: 5-minute horizon sensitivity.
- `physarum_test_result_h6.json`: 30-minute horizon sensitivity.
- `physarum_test_result_t2.json`: thin occupancy sensitivity.
- `physarum_test_result_t8.json`: thick occupancy sensitivity.
- `qa/`: frozen Id1 QA measurements and visual overlay sheet.
- `FROZEN_PRE_EVALUATION_RECEIPT.json`: measurement freeze.
- `FROZEN_SCORING_RECEIPT.json`: single-reveal scoring freeze.

The later `physarum_history_test.py` adds the prespecified occupancy-threshold reconstruction command. It does not replace the exact primary-reveal file.
