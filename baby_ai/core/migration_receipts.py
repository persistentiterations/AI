"""MigrationReceiptLedger — permanent record of MANUAL allocator handoffs.

R-001 rule: the derived-allocator floor is the DEFAULT continuation. If an
operator supplies a manual counter to migrate an existing batch, the derived
value was measured INSUFFICIENT (e.g. the batch carries a non-contiguous /
hand-collapsed id history the collections can no longer prove). That manual
counter is an operator judgement, so it must never be a silent action: a
permanent receipt is written recording

  * pre-migration state hash
  * derived allocator floor
  * operator-supplied value
  * reason the derived value was insufficient
  * resulting post-migration hash

Receipts are append-only JSONL under an explicitly passed directory (defaults
to <PACKAGE>/artifacts/migration_receipts). Missing receipts ARE the invariant:
a batch that never needed a manual handoff has none, and any that did has one.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from baby_ai.core.semantics import canonical_json


def state_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class MigrationReceiptLedger:
    def __init__(self, root: str | Path | None = None) -> None:
        if root is None:
            from baby_ai._env import PACKAGE

            root = PACKAGE / "artifacts" / "migration_receipts"
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._path = self.root / "migration_receipts.jsonl"

    @property
    def path(self) -> Path:
        return self._path

    def record(
        self,
        *,
        activation_id: str,
        family: str,
        derived_floor: int,
        operator_value: int,
        reason_derived_insufficient: str,
        pre_state_hash: str,
        post_state_hash: str,
        observed_ids: list[str],
    ) -> dict[str, Any]:
        receipt = {
            "schema": "baby_ai.migration_receipt.v1",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "activation_id": activation_id,
            "family": family,
            "derived_allocator_floor": derived_floor,
            "operator_value": operator_value,
            "reason_derived_value_insufficient": reason_derived_insufficient,
            "pre_migration_state_hash": pre_state_hash,
            "post_migration_state_hash": post_state_hash,
            "observed_ids": observed_ids,
        }
        receipt["receipt_hash"] = state_hash(receipt)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(receipt, sort_keys=True) + "\n")
        return dict(receipt)

    def read_all(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def verify(self) -> tuple[bool, str]:
        receipts = self.read_all()
        if not receipts:
            return True, "empty migration receipt ledger"
        for r in receipts:
            body = {k: v for k, v in r.items() if k != "receipt_hash"}
            if state_hash(body) != r["receipt_hash"]:
                return False, f"migration receipt tampered: {r.get('activation_id')} {r.get('family')}"
        return True, f"{len(receipts)} migration receipt(s) verified"