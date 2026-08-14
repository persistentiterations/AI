"""Tests package."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import baby_ai  # noqa: F401  (bootstraps organ paths + provenance)