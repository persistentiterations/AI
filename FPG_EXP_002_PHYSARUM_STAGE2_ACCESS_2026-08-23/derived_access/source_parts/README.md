# Source access notes

The exact primary-reveal source in the frozen ZIP is `physarum_history_test_primary_reveal.py`, 638 lines, SHA-256 `13943bcde1b27327cecfb96b4e8a9fa7d3b19fb57182d23eb8e5b87e6884e1c8`.

For maximum model/browser compatibility it is exposed here in four ordered line-preserving parts:

1. `part01_lines_001-180`
2. `part02_lines_181-360`
3. `part03_lines_361-540`
4. `part04_lines_541-638`

Concatenating the text payloads in that order reconstructs the source content. Reviewers should use `original_text/MANIFEST_SHA256.txt` as the authoritative hash receipt.

The later `physarum_history_test.py` has SHA-256 `ba31480a7e8dfdc7a704b8f42482fd09185dd96933c4491a8e27c60f9b0f8fc7`. Its changes relative to the exact primary-reveal source are exposed as `physarum_history_test_vs_primary.diff`; they add occupancy-threshold sensitivity reconstruction and do not replace the primary reveal file.
