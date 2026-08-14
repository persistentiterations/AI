"""PlasticityExecutor (Gap A) — the previously-missing DEFORMATION layer.

The qualified Operational Self detects contradiction/scars/HOLD but has NO code
path that writes ScarStatus 'resolved'/'superseded' (manifest TRUE_MISSING
gap A). This executor provides the explicit resolution lifecycle:

  strengthen, weaken, supersede, resolve, quarantine, invalidate, reactivate,
  HOLD (insufficient evidence), RELEASE.

Invariants:
  * never erases history — every transition appends an immutable version
  * prior evidence and scar provenance preserved in each version record
  * every transition receipts through ReceiptLedger
  * a superseded state remains reconstructible via reconstruct_lineage()
  * later evidence can reopen/revise (strengthen/weaken/reactivate on top)

Belief identity: each belief has a lineage list. The 'current' version is the
latest appended; 'active' is the latest version that a router may act on.
"""

from __future__ import annotations

from typing import Any

from baby_ai.core.provenance import ProvenanceLedger
from baby_ai.core.receipts import ReceiptLedger

DISCLOSURE = (
    "PlasticityExecutor is integration-layer new code. It does not mutate the "
    "qualified fractalish-ai tree; it operates on in-memory state and writes "
    "scar/attractor statuses through adapter methods only."
)


def _id(belief_id: str, version: int) -> str:
    return f"{belief_id}_v{version}"


class PlasticityExecutor:
    def __init__(self, receipts: ReceiptLedger | None = None, provenance: ProvenanceLedger | None = None) -> None:
        self.receipts = receipts or ReceiptLedger()
        self.provenance = provenance or ProvenanceLedger(self.receipts)
        self.lineages: dict[str, list[dict[str, Any]]] = {}
        self.scar_statuses: dict[str, str] = {}
        self.document('plasticity_executor', DISCLOSURE)

    # ------------------------------------------------------------------ docs
    def document(self, component: str, note: str) -> None:
        self.provenance.record(
            component=component,
            organ="baby_ai.core.plasticity",
            reuse_kind="new_code",
            path=__file__,
            sha256=None,
            modifications=note,
        )

    # ----------------------------------------------------------------- core
    def _append(
        self,
        *,
        belief_id: str,
        version: int,
        claim: str,
        decision: str,
        strength: float,
        status: str,
        evidence: list[str],
        reason: str,
        supersedes: str | None,
        superseded_by: str | None,
        action: str,
    ) -> dict[str, Any]:
        rec = {
            "identity": _id(belief_id, version),
            "belief_id": belief_id,
            "version": version,
            "claim": claim,
            "decision": decision,
            "strength": round(float(strength), 4),
            "status": status,
            "evidence": list(evidence),
            "reason": reason,
            "supersedes": supersedes,
            "superseded_by": superseded_by,
        }
        entry = self.receipts.append(
            action=action,
            targets=[belief_id, rec["identity"]],
            evidence=list(evidence),
            payload={"claim": claim, "decision": decision, "status": status, "strength": rec["strength"]},
        )
        rec["receipt"] = entry["hash"]
        self.lineages.setdefault(belief_id, []).append(rec)
        return dict(rec)

    def _mark_scar(self, scar_id: str, status: str) -> None:
        """Adapter write for ScarStatus fields the qualified organ never wrote."""
        prior = self.scar_statuses.get(scar_id)
        self.scar_statuses[scar_id] = status
        self.receipts.append(
            action="scar.status",
            targets=[scar_id],
            evidence=[f"prior={prior}", f"now={status}"],
            payload={"status": status},
        )

    def get_scar_status(self, scar_id: str) -> str:
        return self.scar_statuses.get(scar_id, "unresolved")

    # ------------------------------------------------------------ operations
    def assert_belief(
        self, *, belief_id: str, claim: str, decision: str, strength: float, evidence: list[str], reason: str
    ) -> dict[str, Any]:
        return self._append(
            belief_id=belief_id,
            version=1,
            claim=claim,
            decision=decision,
            strength=strength,
            status="active",
            evidence=evidence,
            reason=reason,
            supersedes=None,
            superseded_by=None,
            action="assert_belief",
        )

    def strengthen(self, *, belief_id: str, evidence: list[str], reason: str, amount: float = 0.1) -> dict[str, Any]:
        prev = self.lineages[belief_id][-1]
        return self._append(
            belief_id=belief_id,
            version=prev["version"] + 1,
            claim=prev["claim"],
            decision=prev["decision"],
            strength=min(1.0, prev["strength"] + amount),
            status="active",
            evidence=prev["evidence"] + list(evidence),
            reason=reason,
            supersedes=prev["identity"],
            superseded_by=None,
            action="strengthen",
        )

    def weaken(self, *, belief_id: str, evidence: list[str], reason: str, amount: float = 0.1) -> dict[str, Any]:
        prev = self.lineages[belief_id][-1]
        return self._append(
            belief_id=belief_id,
            version=prev["version"] + 1,
            claim=prev["claim"],
            decision=prev["decision"],
            strength=max(0.0, prev["strength"] - amount),
            status="weak",
            evidence=prev["evidence"] + list(evidence),
            reason=reason,
            supersedes=prev["identity"],
            superseded_by=None,
            action="weaken",
        )

    def hold(self, *, belief_id: str, evidence: list[str], reason: str) -> dict[str, Any]:
        prev = self.lineages[belief_id][-1]
        return self._append(
            belief_id=belief_id,
            version=prev["version"] + 1,
            claim=prev["claim"],
            decision="HOLD",
            strength=prev["strength"],
            status="held",
            evidence=prev["evidence"] + list(evidence),
            reason=reason,
            supersedes=prev["identity"],
            superseded_by=None,
            action="hold",
        )

    def release(self, *, belief_id: str, evidence: list[str], reason: str) -> dict[str, Any]:
        prev = self.lineages[belief_id][-1]
        if prev["status"] != "held":
            raise ValueError(f"release requires held state, got {prev['status']}")
        return self._append(
            belief_id=belief_id,
            version=prev["version"] + 1,
            claim=prev["claim"],
            decision=prev["decision"],
            strength=min(1.0, prev["strength"] + 0.05),
            status="active",
            evidence=prev["evidence"] + list(evidence),
            reason=reason,
            supersedes=prev["identity"],
            superseded_by=None,
            action="release",
        )

    def supersede(
        self,
        *,
        belief_id: str,
        new_claim: str,
        new_decision: str,
        evidence: list[str],
        reason: str,
        strength: float | None = None,
        scar_id: str | None = None,
    ) -> dict[str, Any]:
        prev = self.lineages[belief_id][-1]
        rec = self._append(
            belief_id=belief_id,
            version=prev["version"] + 1,
            claim=new_claim,
            decision=new_decision,
            strength=prev["strength"] if strength is None else strength,
            status="active",
            evidence=prev["evidence"] + list(evidence),
            reason=reason,
            supersedes=prev["identity"],
            superseded_by=None,
            action="supersede",
        )
        self._append_link_history(prev, rec)
        if scar_id:
            self._mark_scar(scar_id, "superseded")
        return rec

    def resolve(self, *, belief_id: str, evidence: list[str], reason: str, scar_id: str | None = None) -> dict[str, Any]:
        prev = self.lineages[belief_id][-1]
        rec = self._append(
            belief_id=belief_id,
            version=prev["version"] + 1,
            claim=prev["claim"],
            decision=prev["decision"],
            strength=prev["strength"],
            status="resolved",
            evidence=prev["evidence"] + list(evidence),
            reason=reason,
            supersedes=prev["identity"],
            superseded_by=None,
            action="resolve",
        )
        if scar_id:
            self._mark_scar(scar_id, "resolved")
        return rec

    def quarantine(self, *, belief_id: str, evidence: list[str], reason: str) -> dict[str, Any]:
        prev = self.lineages[belief_id][-1]
        return self._append(
            belief_id=belief_id,
            version=prev["version"] + 1,
            claim=prev["claim"],
            decision="QUARANTINE",
            strength=prev["strength"],
            status="quarantined",
            evidence=prev["evidence"] + list(evidence),
            reason=reason,
            supersedes=prev["identity"],
            superseded_by=None,
            action="quarantine",
        )

    def invalidate(self, *, belief_id: str, evidence: list[str], reason: str) -> dict[str, Any]:
        prev = self.lineages[belief_id][-1]
        return self._append(
            belief_id=belief_id,
            version=prev["version"] + 1,
            claim=prev["claim"],
            decision="INVALID",
            strength=0.0,
            status="invalidated",
            evidence=prev["evidence"] + list(evidence),
            reason=reason,
            supersedes=prev["identity"],
            superseded_by=None,
            action="invalidate",
        )

    def reactivate(self, *, belief_id: str, claim: str, decision: str, evidence: list[str], reason: str) -> dict[str, Any]:
        prev = self.lineages[belief_id][-1]
        return self._append(
            belief_id=belief_id,
            version=prev["version"] + 1,
            claim=claim,
            decision=decision,
            strength=max(0.3, prev["strength"]),
            status="active",
            evidence=prev["evidence"] + list(evidence),
            reason=reason,
            supersedes=prev["identity"],
            superseded_by=None,
            action="reactivate",
        )

    def _append_link_history(self, prev: dict[str, Any], rec: dict[str, Any]) -> None:
        """Write supersedes/superseded_by links on the versions (immutable read-mining)."""
        prev["superseded_by"] = rec["identity"]

    # ------------------------------------------------------------- queries
    def lineage(self, belief_id: str) -> list[dict[str, Any]]:
        return list(self.lineages.get(belief_id, []))

    def current(self, belief_id: str) -> dict[str, Any] | None:
        versions = self.lineages.get(belief_id)
        return versions[-1] if versions else None

    def active(self, belief_id: str) -> dict[str, Any] | None:
        """Latest version the router may act on, or None.

        The CURRENT version controls the belief state: only a latest version whose
        status is 'active'/'resolved' is actionable. A 'held'/'weak'/'quarantined'/
        'invalidated' current version suspends routing (returns None) rather than
        resurrecting a stale older active version.
        """
        versions = self.lineages.get(belief_id, [])
        if not versions:
            return None
        cur = versions[-1]
        if cur["status"] in ("active", "resolved"):
            return cur
        return None

    def reconstruct_lineage(self, belief_id: str) -> list[dict[str, Any]]:
        """Reverse walk from current back through supersedes chain to earliest consequential branch."""
        out: list[dict[str, Any]] = []
        versions = self.lineages.get(belief_id, [])
        if not versions:
            return out
        by_identity = {rec["identity"]: rec for rec in versions}
        cur: dict[str, Any] | None = versions[-1]
        seen: set[str] = set()
        while cur and cur["identity"] not in seen and cur["supersedes"] is not None:
            seen.add(cur["identity"])
            out.append(cur)
            cur = by_identity.get(cur["supersedes"])
        # append the final root (supersedes is None)
        if cur and cur["identity"] not in seen:
            out.append(cur)
        return out

    # ----------------------------------------------------------- persistence
    def to_dict(self) -> dict[str, Any]:
        return {
            "lineages": self.lineages,
            "scar_statuses": self.scar_statuses,
            "receipts": self.receipts.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlasticityExecutor":
        obj = cls()
        obj.lineages = {k: list(v) for k, v in data.get("lineages", {}).items()}
        obj.scar_statuses = dict(data.get("scar_statuses", {}))
        obj.receipts = ReceiptLedger.from_dict(data.get("receipts", {"entries": [], "tip": "*"}))
        return obj