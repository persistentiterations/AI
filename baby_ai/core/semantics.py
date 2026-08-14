"""Semantic state vs observational metadata separation.

The qualified Operational Self embeds wall-clock timestamps and self-referential
state_hash (manifest-recorded bounded nondeterminism). For continuity/integrity
comparisons we separate:

  SEMANTIC STATE   -> everything that must survive host transfer (memories,
                      attractors, links, scars, fog, routes, plasticity ledger)
  OBSERVATIONAL    -> wall clock, run ids, result ordering noise

We do NOT mutate the historical implementation. Normalization happens here, in
the integration layer, and is explicitly documented.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from baby_ai._env import SEMANTIC_OBSERVATIONAL_KEYS


def strip_observational(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of payload with observational metadata keys removed."""
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for k, v in payload.items():
            if k in SEMANTIC_OBSERVATIONAL_KEYS:
                continue
            out[k] = strip_observational(v) if isinstance(v, (dict, list)) else v
        return out
    if isinstance(payload, list):
        return [strip_observational(v) if isinstance(v, (dict, list)) else v for v in payload]
    return payload


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(strip_observational(payload), sort_keys=True, default=str)


def semantic_digest(payload: dict[str, Any]) -> str:
    """Stable digest over SEMANTIC content only. Deterministic across hosts/runs."""
    raw = canonical_json(payload)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def bytesize(payload: dict[str, Any]) -> int:
    return len(canonical_json(payload).encode("utf-8"))