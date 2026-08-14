"""ContinuitySnapshot (Gap B) — host-neutral full-state pack/restore.

Bridges:
  * Operational Self full state (memories/attractors/links/scars/fog/routes/self)
  * PlasticityExecutor lineage ledger
  * receipts tip + provenance
  * optional CNTM morphology substrate snapshot
  * domain/routing state (the consequential accessibility layer)

Separates SEMANTIC content from OBSERVATIONAL metadata. Semantic digest is
recomputed on restore for integrity. A second host may receive ONLY this file
plus code/schema — never Host A memory.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from baby_ai.core.semantics import canonical_json, semantic_digest, strip_observational

SCHEMA_VERSION = "baby_ai.snapshot.v0.1"


class ContinuitySnapshot:
    def __init__(self, *, schema_version: str = SCHEMA_VERSION) -> None:
        self.schema_version = schema_version
        self.operational_self: dict[str, Any] = {}
        self.plasticity: dict[str, Any] = {}
        self.receipts: dict[str, Any] = {}
        self.provenance: dict[str, Any] = {}
        self.domain: dict[str, Any] = {}
        self.substrate: dict[str, Any] = {}
        self.observational: dict[str, Any] = {}
        self.semantic_hash: str = ""
        self.integrity: dict[str, Any] = {}

    # ----------------------------------------------------------------- pack
    def pack(
        self,
        *,
        operational_self: dict[str, Any],
        plasticity: dict[str, Any],
        receipts: dict[str, Any],
        provenance: dict[str, Any],
        domain: dict[str, Any] | None = None,
        substrate: dict[str, Any] | None = None,
    ) -> "ContinuitySnapshot":
        self.operational_self = operational_self
        self.plasticity = plasticity
        self.receipts = receipts
        self.provenance = provenance
        self.domain = domain or {}
        self.substrate = substrate or {}
        self.semantic_hash = self._compute_semantic_hash()
        self.observational["created_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.observational["wall_clock_ms"] = round(time.time() * 1000)
        return self

    def _compute_semantic_hash(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "operational_self": self.operational_self,
            "plasticity": self.plasticity,
            "receipts": self.receipts,
            "provenance": self.provenance,
            "domain": self.domain,
            "substrate": self.substrate,
        }
        return semantic_digest(strip_observational(payload))

    def verify_integrity(self) -> dict[str, Any]:
        recomputed = self._compute_semantic_hash()
        ok = recomputed == self.semantic_hash
        self.integrity = {
            "ok": ok,
            "recorded": self.semantic_hash,
            "recomputed": recomputed,
        }
        return self.integrity

    # -------------------------------------------------------------- i/o
    def to_dict(self, *, include_observational: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema_version": self.schema_version,
            "semantic_hash": self.semantic_hash,
            "operational_self": self.operational_self,
            "plasticity": self.plasticity,
            "receipts": self.receipts,
            "provenance": self.provenance,
            "domain": self.domain,
            "substrate": self.substrate,
        }
        if include_observational:
            out["observational"] = self.observational
        return out

    def write(self, path: str | Path, *, include_observational: bool = True) -> Path:
        from baby_ai._env import PACKAGE

        p = Path(path)
        if not p.is_absolute() and not Path(path).exists():
            p = PACKAGE / "artifacts" / p
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(canonical_json(self.to_dict(include_observational=include_observational)), encoding="utf-8")
        return p

    def export_bytes(self) -> int:
        return len(canonical_json(self.to_dict()).encode("utf-8"))

    # ------------------------------------------------------------ restore
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContinuitySnapshot":
        obj = cls(schema_version=data.get("schema_version", SCHEMA_VERSION))
        obj.semantic_hash = data.get("semantic_hash", "")
        obj.operational_self = data.get("operational_self", {})
        obj.plasticity = data.get("plasticity", {})
        obj.receipts = data.get("receipts", {})
        obj.provenance = data.get("provenance", {})
        obj.domain = data.get("domain", {})
        obj.substrate = data.get("substrate", {})
        obj.observational = data.get("observational", {})
        obj.verify_integrity()
        return obj

    @classmethod
    def read(cls, path: str | Path) -> "ContinuitySnapshot":
        import json

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)