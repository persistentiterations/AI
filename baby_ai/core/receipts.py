"""ReceiptLedger — small receipt-chain (pattern reimplementation of CONFIGURATOR v1.2
ChainedMatchLog: append, verify_chain, checkpoint, tip). New stdlib-only code.

Every state transition in the MVP produces a receipt: seq, prev_hash, action,
targets, evidence, payload digest, entry hash. Chain integrity is verifiable and
the tip is carried in ContinuitySnapshot.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _entry_hash(seq: int, prev_hash: str, action: str, targets: list[str], evidence: list[str], payload_digest: str) -> str:
    raw = json.dumps({"seq": seq, "prev": prev_hash, "action": action, "targets": targets, "evidence": evidence, "payload": payload_digest}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class ReceiptLedger:
    """Append-only receipt chain. Settled entries are immutable."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []
        self.tip = "*"

    def append(self, *, action: str, targets: list[str], evidence: list[str], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload_digest = "—"
        if payload is not None:
            payload_digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
        seq = len(self.entries)
        entry = {
            "seq": seq,
            "prev": self.tip,
            "action": action,
            "targets": targets,
            "evidence": evidence,
            "payload_digest": payload_digest,
        }
        entry["hash"] = _entry_hash(seq, self.tip, action, targets, evidence, payload_digest)
        self.entries.append(entry)
        self.tip = entry["hash"]
        return dict(entry)

    def verify_chain(self) -> tuple[bool, str]:
        if not self.entries:
            return True, "empty chain"
        prev = "*"
        for e in self.entries:
            recomputed = _entry_hash(e["seq"], prev, e["action"], e["targets"], e["evidence"], e["payload_digest"])
            if recomputed != e["hash"]:
                return False, f"chain broken at seq {e['seq']}"
            prev = e["hash"]
        if prev != self.tip:
            return False, "tip does not match recomputed chain"
        return True, f"{len(self.entries)} receipts verified, tip={self.tip}"

    def to_dict(self) -> dict[str, Any]:
        return {"tip": self.tip, "entries": self.entries}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReceiptLedger":
        obj = cls()
        obj.entries = list(data.get("entries", []))
        obj.tip = data.get("tip", "*")
        return obj

    def __len__(self) -> int:
        return len(self.entries)