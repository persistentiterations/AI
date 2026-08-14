"""Provenance ledger — records organ reuse and artifact lineage for every run.

Every adaptation/reuse/salvage is recorded with original path, sha256, and the
exact nature of the reuse (import-only vs new code). This satisfies the
assembly rule: 'copy only with explicit provenance and record original path,
original SHA-256, exact modifications.'
"""

from __future__ import annotations

import json
from typing import Any

from baby_ai.core.receipts import ReceiptLedger


class ProvenanceLedger:
    def __init__(self, receipts: ReceiptLedger | None = None) -> None:
        self.receipts = receipts or ReceiptLedger()
        self.records: list[dict[str, Any]] = []

    def record(
        self,
        *,
        component: str,
        organ: str,
        reuse_kind: str,  # "import", "adapter_over", "pattern_reimplement", "new_code"
        path: str,
        sha256: str | None,
        modifications: str,
    ) -> None:
        rec = {
            "component": component,
            "organ": organ,
            "reuse_kind": reuse_kind,
            "path": path,
            "sha256": sha256,
            "modifications": modifications,
        }
        self.records.append(rec)
        self.receipts.append(
            action="provenance.record",
            targets=[component, organ],
            evidence=[reuse_kind, path],
            payload={"share": 1},
        )

    def to_dict(self) -> dict[str, Any]:
        return {"records": self.records}

    @classmethod
    def from_dict(cls, data: dict[str, Any], receipts: ReceiptLedger) -> "ProvenanceLedger":
        obj = cls(receipts)
        obj.records = list(data.get("records", []))
        return obj