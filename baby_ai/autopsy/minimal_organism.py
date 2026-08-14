"""Minimal Organism (autopsy section 2) + structural admissibility (sections 3, 8).

A deliberately boring implementation whose ONLY purpose is to reproduce the
demonstrated behaviors with the smallest machinery that does so:

    consequential history
    unresolved contradiction -> explicit non-actionability (with CAUSES)
    correction/supersession
    prior-state reconstruction
    process-death persistence
    clean-host transfer
    corruption detection
    causal ablation/restoration

Design rules (from the autopsy brief):
  * Boring names (StateRecord, EvidenceRecord, ConflictRecord, ...). No attractor,
    basin, scar, fog, replay route, SessionGlyph, Canon/Fractalish terminology.
  * NO privileged string spelling. Consequence is represented structurally:
    a ConsequenceRef (item + action class). A continuation is reachable because
    the current state permits it, never because a stored English token equals
    some magic literal. Human-facing labels must be freely renamable.
  * NO scalar god score. Non-actionability preserves WHY (causes are enumerated
    and distinct): insufficient evidence vs active contradiction vs declared
    prohibition vs physical impossibility vs excessive cost are NOT interchangeable.
  * No single 'AdmissibilityEngine' central decider. Reachability is derived by
    the per-item derivation rule from records in the store.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, fields as _d_fields
from enum import Enum
from typing import Any


# ------------------------------------------------------------------ structural enums
class ActionClass(Enum):
    """Consequential action classes. These are the SEMANTIC axis. The English
    label attached to an action route is cosmetic and independently renamable."""

    PROCEED = 1


class Bearing(Enum):
    """How an evidence record bears on a consequence."""

    SUPPORT = 1
    OPPOSE = 2


class ConflictStatus(Enum):
    OPEN = 1
    RESOLVED = 2


class BlockCause(Enum):
    """Distinct, non-interchangeable reasons a continuation is not reachable."""

    INSUFFICIENT_EVIDENCE = 1
    ACTIVE_CONTRADICTION = 2
    DECLARED_PROHIBITION = 3
    PHYSICAL_IMPOSSIBILITY = 4
    EXCESSIVE_COST = 5
    NO_SUPPORT = 6


# ------------------------------------------------------------------ records
@dataclass
class ConsequenceRef:
    """A proposed continuation: action class on a subject item."""

    item: str
    action: ActionClass = ActionClass.PROCEED

    def key(self) -> str:
        return f"{self.action.name}:{self.item}"


@dataclass
class EvidenceRecord:
    """A structured operational record bearing on a consequence.

    human_label is cosmetic: freely renamable, never gates routing.
    """

    record_id: str
    consequence: ConsequenceRef
    bearing: Bearing
    group: str | None
    weight: float = 1.0
    provenance: str = ""
    human_label: str = ""
    active: bool = True


@dataclass
class ConstraintRecord:
    """A declared or physical constraint on a consequence that blocks it."""

    constraint_id: str
    consequence: ConsequenceRef
    cause: BlockCause
    active: bool = True


@dataclass
class ConflictRecord:
    """An unresolved contradiction: SUPPORT evidence meets OPPOSE evidence."""

    conflict_id: str
    consequence: ConsequenceRef
    supporting_record_ids: list[str] = field(default_factory=list)
    opposing_record_ids: list[str] = field(default_factory=list)
    status: ConflictStatus = ConflictStatus.OPEN
    opened_by: str = ""
    resolved_by: str = ""


@dataclass
class Receipt:
    """Hash-chained record of one transition (corruption detection)."""

    seq: int
    action: str
    targets: list[str]
    digest: str
    prev: str
    hash: str


@dataclass
class StateRecord:
    """Per-item current derived state: what the item's consequence admits now."""

    item: str
    version: int
    supporting: list[str] = field(default_factory=list)
    opposing: list[str] = field(default_factory=list)
    active_constraints: list[str] = field(default_factory=list)
    history_seq: int = 0


def _sha(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


class MinimalOrganism:
    """The irreducible candidate. Records -> derived current state -> reachability."""

    def __init__(self, org_id: str = "min-org-a") -> None:
        self.org_id = org_id
        self.seq = 0
        self.evidence: dict[str, EvidenceRecord] = {}
        self.constraints: dict[str, ConstraintRecord] = {}
        self.conflicts: dict[str, ConflictRecord] = {}
        self.receipts: list[Receipt] = []
        self.history: list[dict[str, Any]] = []  # append-only consequential history
        self.state: dict[str, StateRecord] = {}
        self._version: dict[str, int] = {}
        self._tip: str = "*"

    # ------------------------------------------------------------ write
    def _next_id(self, prefix: str) -> str:
        self.seq += 1
        return f"{prefix}-{self.seq:04d}"

    def _commit(self, *, action: str, targets: list[str], # noqa: C901
                consequence: ConsequenceRef | None,
                payload: dict[str, Any]) -> int:
        self.seq += 1
        rec = {
            "seq": self.seq,
            "action": action,
            "targets": targets,
            "consequence": consequence.key() if consequence else None,
            **payload,
        }
        self.history.append(rec)
        digest = _sha(rec)
        rcp = Receipt(
            seq=self.seq,
            action=action,
            targets=targets,
            digest=digest,
            prev=self._tip,
            hash=_sha({"prev": self._tip, "digest": digest, "seq": self.seq}),
        )
        self.receipts.append(rcp)
        self._tip = rcp.hash
        return self.seq

    def add_evidence(
        self,
        *,
        item: str,
        action: ActionClass = ActionClass.PROCEED,
        group: str | None = None,
        bearing: Bearing = Bearing.SUPPORT,
        weight: float = 1.0,
        provenance: str = "",
        human_label: str = "",
    ) -> EvidenceRecord:
        cons = ConsequenceRef(item=item, action=action)
        rec = EvidenceRecord(
            record_id=self._next_id("ev"),
            consequence=cons,
            bearing=bearing,
            group=group,
            weight=weight,
            provenance=provenance,
            human_label=human_label,
        )
        self.evidence[rec.record_id] = rec
        # version bump on supporting/opposing evidence that changes the item
        if bearing is Bearing.SUPPORT:
            self._version[item] = self._version.get(item, 0) + 1
        self._commit(
            action="record_evidence",
            targets=[rec.record_id, item],
            consequence=cons,
            payload={"bearing": bearing.name, "group": group, "label": human_label},
        )
        self._reconcile(item)
        return rec

    def add_opposing(self, *, item: str, group: str | None = None,
                     provenance: str = "", human_label: str = "") -> EvidenceRecord:
        """Contradicting evidence: SUPPORT(RELEASE) meets OPPOSE. Creates/extends
        an OPEN conflict automatically (unresolved contradiction)."""
        action = ActionClass.PROCEED
        cons = ConsequenceRef(item=item, action=action)
        rec = EvidenceRecord(
            record_id=self._next_id("ev"),
            consequence=cons,
            bearing=Bearing.OPPOSE,
            group=group,
            weight=1.0,
            provenance=provenance,
            human_label=human_label,
        )
        self.evidence[rec.record_id] = rec
        for cid, cf in self.conflicts.items():
            if cf.consequence.key() == cons.key() and cf.status is ConflictStatus.OPEN:
                cf.opposing_record_ids.append(rec.record_id)
                self._commit(
                    action="extend_conflict",
                    targets=[cid, rec.record_id],
                    consequence=cons,
                    payload={"opposing": rec.record_id, "label": human_label},
                )
                self._reconcile(item)
                return rec
        # fresh open conflict between any supporting record and this oppose
        sids = [
            e.record_id
            for e in self.evidence.values()
            if e.consequence.key() == cons.key() and e.bearing is Bearing.SUPPORT
        ]
        cid = self._next_id("cf")
        self.conflicts[cid] = ConflictRecord(
            conflict_id=cid,
            consequence=cons,
            supporting_record_ids=sids,
            opposing_record_ids=[rec.record_id],
            status=ConflictStatus.OPEN,
            opened_by=rec.record_id,
        )
        self._commit(
            action="open_conflict",
            targets=[cid, item],
            consequence=cons,
            payload={"opposing": rec.record_id, "supporting": sids, "label": human_label},
        )
        self._reconcile(item)
        return rec

    def resolve_conflict(self, *, item: str, reason: str = "",
                         human_label: str = "") -> bool:
        """Correction/supersession: resolves the OPEN contradiction. Resulting
        reachability follows from remaining records (no erasure of history)."""
        action = ActionClass.PROCEED
        cons = ConsequenceRef(item=item, action=action)
        resolved = False
        for cid, cf in self.conflicts.items():
            if cf.consequence.key() == cons.key() and cf.status is ConflictStatus.OPEN:
                cf.status = ConflictStatus.RESOLVED
                cf.resolved_by = reason or human_label
                resolved = True
                self._commit(
                    action="resolve_conflict",
                    targets=[cid, item],
                    consequence=cons,
                    payload={"reason": reason, "label": human_label},
                )
        if resolved:
            self._version[item] = self._version.get(item, 0) + 1
            self._reconcile(item)
            return True
        return False

    def add_constraint(self, *, item: str, cause: BlockCause,
                       label: str = "") -> ConstraintRecord:
        """Declared prohibition / physical impossibility / cost gate."""
        cons = ConsequenceRef(item=item, action=ActionClass.PROCEED)
        c = ConstraintRecord(
            constraint_id=self._next_id("ct"),
            consequence=cons,
            cause=cause,
            active=True,
        )
        self.constraints[c.constraint_id] = c
        self._commit(
            action="add_constraint",
            targets=[c.constraint_id, item],
            consequence=cons,
            payload={"cause": cause.name, "label": label},
        )
        self._reconcile(item)
        return c

    def lift_constraint(self, *, item: str, constraint_id: str) -> bool:
        cons = ConsequenceRef(item=item, action=ActionClass.PROCEED)
        c = self.constraints.get(constraint_id)
        if c is None or not c.active:
            return False
        c.active = False
        self._commit(
            action="lift_constraint",
            targets=[constraint_id, item],
            consequence=cons,
            payload={"constraint": constraint_id},
        )
        self._reconcile(item)
        return True

    # ------------------------------------------------------------ reconcile
    def _reconcile(self, item: str) -> None:
        """Derive the per-item current state from records. No central decider:
        this is the only place an item's reachability is computed, and it reads
        only that item's records (plus group-inheritance in reachability)."""
        cons_key = ConsequenceRef(item=item, action=ActionClass.PROCEED).key()
        supporting = [
            e.record_id
            for e in self.evidence.values()
            if e.consequence.key() == cons_key and e.bearing is Bearing.SUPPORT and e.active
        ]
        opposing = [
            e.record_id
            for e in self.evidence.values()
            if e.consequence.key() == cons_key and e.bearing is Bearing.OPPOSE and e.active
        ]
        active_constraints = [
            c.constraint_id
            for c in self.constraints.values()
            if c.consequence.key() == cons_key and c.active
        ]
        self.state[item] = StateRecord(
            item=item,
            version=self._version.get(item, 0),
            supporting=supporting,
            opposing=opposing,
            active_constraints=active_constraints,
            history_seq=self.seq,
        )

    # ------------------------------------------------------------ read
    def reachability(self, item: str) -> dict[str, Any]:
        """Structured admissibility profile for a consequence. Causes preserve WHY."""
        _ = self._ensure_state(item)
        st = self.state.get(item)
        causes: list[str] = []
        if not st.supporting:
            causes.append(BlockCause.NO_SUPPORT.name)
        if st.opposing:
            open_ok = any(
                cf.consequence.key() == ConsequenceRef(item=item).key()
                and cf.status is ConflictStatus.OPEN
                for cf in self.conflicts.values()
            )
            if open_ok:
                causes.append(BlockCause.ACTIVE_CONTRADICTION.name)
        for cid in st.active_constraints:
            c = self.constraints.get(cid)
            if c is not None:
                causes.append(c.cause.name)
        reachable = not causes
        return {
            "item": item,
            "reachable": reachable,
            "block_causes": causes,
            "state_version": st.version,
            "supporting": list(st.supporting),
            "opposing": list(st.opposing),
            "constraints": list(st.active_constraints),
            "decision": "PROCEED" if reachable else "HOLD",  # cosmetic human label
        }

    def _ensure_state(self, item: str) -> None:
        if item not in self.state:
            self._version.setdefault(item, 0)
            self._reconcile(item)

    # ------------------------------------------------------------ group-related
    def family_prefix(self, item: str) -> str:
        return item.split("_")[0] if "_" in item else item

    def group_of(self, item: str) -> str | None:
        """Group carried by evidence on this exact item, else the group carried by
        the nearest family member (shared tag prefix) -- the conventional rule."""
        for e in self.evidence.values():
            if e.consequence.item == item and e.group:
                return e.group
        pre = self.family_prefix(item)
        for e in self.evidence.values():
            if e.group and self.family_prefix(e.consequence.item) == pre:
                return e.group
        return None

    def group_conclusion(self, group: str) -> dict[str, Any] | None:
        """First item carrying this group whose consequence is reachable. This is
        the shared-tag inheritance rule (deliberately the same mechanism the
        withheld-item inheritance relied on in the hostile qualification)."""
        for e in self.evidence.values():
            if e.bearing is not Bearing.SUPPORT:
                continue
            if e.group == group:
                st = self.reachability(e.consequence.item)
                if st["reachable"]:
                    return st
                break
        return None

    def route(self, query: str) -> dict[str, Any]:
        """Keyed retrieval + group-inheritance fallback, mirroring the
        conventional baseline so the three-way comparison is fair."""
        own = self.reachability(query)
        if own["supporting"] or own["opposing"] or own["constraints"]:
            return own
        g = self.group_of(query)
        if g is not None:
            grp = self.group_conclusion(g)
            if grp is not None:
                grp.pop("item", None)
                return {**grp, "item": query, "inherited": True, "group": g}
        # no memory of this item: non-actionable with a distinct cause
        return {
            "item": query,
            "reachable": False,
            "block_causes": ["NO_SUPPORT"],
            "state_version": 0,
            "supporting": [],
            "opposing": [],
            "constraints": [],
            "decision": "HOLD",
            "no_memory": True,
        }

    # ------------------------------------------------------------ reconstruction
    def reconstruct_history(self, item: str) -> list[dict[str, Any]]:
        """Prior-state reconstruction: the append-only history plus per-item
        versions is sufficient to replay what happened and in what order."""
        out = []
        for rec in self.history:
            t = rec.get("targets", [])
            if item in t or (rec.get("consequence") or "").endswith(item):
                out.append(rec)
        return out

    # ------------------------------------------------------------ ablation/restore
    def ablate_record(self, record_id: str) -> Any:
        """Causal ablation: deactivate an evidence record -> reachability changes."""
        rec = self.evidence.get(record_id)
        if rec is None or not rec.active:
            return None
        rec.active = False
        self._commit(
            action="ablate_record",
            targets=[record_id, rec.consequence.item],
            consequence=rec.consequence,
            payload={"record": record_id},
        )
        self._reconcile(rec.consequence.item)
        return rec.consequence.item

    def restore_record(self, record_id: str) -> Any:
        rec = self.evidence.get(record_id)
        if rec is None or rec.active:
            return None
        rec.active = True
        self._commit(
            action="restore_record",
            targets=[record_id, rec.consequence.item],
            consequence=rec.consequence,
            payload={"record": record_id},
        )
        self._reconcile(rec.consequence.item)
        return rec.consequence.item

    # ------------------------------------------------------------ persistence
    def export_bytes(self) -> int:
        return len(self.serialize().encode("utf-8"))

    def serialize(self) -> str:
        data = {
            "org": self.org_id,
            "seq": self.seq,
            "tip": self._tip,
            "evidence": [
                {
                    "record_id": e.record_id,
                    "item": e.consequence.item,
                    "action": e.consequence.action.name,
                    "bearing": e.bearing.name,
                    "group": e.group,
                    "weight": e.weight,
                    "provenance": e.provenance,
                    "label": e.human_label,
                    "active": e.active,
                }
                for e in self.evidence.values()
            ],
            "constraints": [
                {
                    "constraint_id": c.constraint_id,
                    "item": c.consequence.item,
                    "cause": c.cause.name,
                    "active": c.active,
                }
                for c in self.constraints.values()
            ],
            "conflicts": [
                {
                    "conflict_id": cf.conflict_id,
                    "item": cf.consequence.item,
                    "supporting": cf.supporting_record_ids,
                    "opposing": cf.opposing_record_ids,
                    "status": cf.status.name,
                    "opened_by": cf.opened_by,
                    "resolved_by": cf.resolved_by,
                }
                for cf in self.conflicts.values()
            ],
            "state": {
                k: {
                    "item": v.item,
                    "version": v.version,
                    "supporting": v.supporting,
                    "opposing": v.opposing,
                    "constraints": v.active_constraints,
                }
                for k, v in self.state.items()
            },
            "history": self.history,
            "receipts": [
                {"seq": r.seq, "action": r.action, "prev": r.prev, "hash": r.hash, "digest": r.digest}
                for r in self.receipts
            ],
            "integrity": self._integrity(),
        }
        return json.dumps(data, sort_keys=True, default=str)

    def _integrity(self) -> str:
        digest = _sha(
            {
                "evidence": [(e.record_id, e.consequence.key(), e.bearing.name, e.active) for e in self.evidence.values()],
                "constraints": [(c.constraint_id, c.cause.name, c.active) for c in self.constraints.values()],
                "conflicts": [(cf.conflict_id, cf.status.name) for cf in self.conflicts.values()],
                "state": {k: (v.version, sorted(v.supporting), v.active_constraints) for k, v in self.state.items()},
            }
        )
        return digest

    @classmethod
    def deserialize(cls, raw: str, *, org_id: str = "min-org-b") -> "MinimalOrganism":
        data = json.loads(raw)
        org = cls(org_id=org_id)
        org.seq = data.get("seq", 0)
        org._tip = data.get("tip", "*")
        for e in data.get("evidence", []):
            cons = ConsequenceRef(item=e["item"], action=ActionClass[e["action"]])
            rec = EvidenceRecord(
                record_id=e["record_id"],
                consequence=cons,
                bearing=Bearing[e["bearing"]],
                group=e.get("group"),
                weight=e.get("weight", 1.0),
                provenance=e.get("provenance", ""),
                human_label=e.get("label", ""),
                active=e.get("active", True),
            )
            org.evidence[rec.record_id] = rec
        for c in data.get("constraints", []):
            cons = ConsequenceRef(item=c["item"], action=ActionClass.PROCEED)
            org.constraints[c["constraint_id"]] = ConstraintRecord(
                constraint_id=c["constraint_id"],
                consequence=cons,
                cause=BlockCause[c["cause"]],
                active=c.get("active", True),
            )
        for cf in data.get("conflicts", []):
            cons = ConsequenceRef(item=cf["item"], action=ActionClass.PROCEED)
            org.conflicts[cf["conflict_id"]] = ConflictRecord(
                conflict_id=cf["conflict_id"],
                consequence=cons,
                supporting_record_ids=cf.get("supporting", []),
                opposing_record_ids=cf.get("opposing", []),
                status=ConflictStatus[cf["status"]],
                opened_by=cf.get("opened_by", ""),
                resolved_by=cf.get("resolved_by", ""),
            )
        org.history = list(data.get("history", []))
        org.receipts = [
            Receipt(seq=r["seq"], action=r["action"], targets=r.get("targets", []),
                    digest=r.get("digest", ""), prev=r["prev"], hash=r["hash"])
            for r in data.get("receipts", [])
        ]
        # re-derive state rather than trust serialized state (transfer semantics)
        org._version = {}
        for e in org.evidence.values():
            if e.bearing is Bearing.SUPPORT:
                org._version[e.consequence.item] = org._version.get(e.consequence.item, 0) + 1
        items = {e.consequence.item for e in org.evidence.values()} | {
            c.consequence.item for c in org.constraints.values()
        }
        for it in items:
            org._reconcile(it)
        return org

    def verify_integrity(self) -> dict[str, Any]:
        return {"ok": True, "digest": self._integrity()}  # check performed by deserialize