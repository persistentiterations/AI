"""FormationCore — adapter over the QUALIFIED OLD FRACTALISH-AI Operational Self.

Reuses the qualified package READ-ONLY via import (byte-identical twin lives in
the FractalishBuild superset; verified 0 diffs across 68 shared py files in the
operational_self + session_glyph layers). All formation work (compress ->
attractor -> scar -> fog -> retrieval gating) is performed by the qualified
functions; ids/timestamps are normalized here so the integration is deterministic.

Imported ALLOWED modules (no mutation):
  operational_self.light_compress, .create_attractor, .detect_scars_from_event,
  .detect_fog_from_event, .retrieve, .update_self_from_consolidation,
  .create_initial_self, .build_replay_route
  session_glyph building helpers are NOT needed for full-graph continuity.

In-process deterministic id stream (adapter layer, NOT organ mutation) plus
fixed timestamps make repeated runs byte-consistent; the continuity test then
only relies on SEMANTIC state (see core.semantics).
"""

from __future__ import annotations

import re
from dataclasses import fields as _fields
from typing import Any

from baby_ai._env import PACKAGE
from baby_ai.core.provenance import ProvenanceLedger
from baby_ai.core.receipts import ReceiptLedger

# ---------------------------------------------------------------- qualified
from fractalish_ai import operational_self as _os
from fractalish_ai.operational_self import (
    compression as _comp,
    attractors as _attr,
    scars as _scars,
    fog as _fog,
    retrieval as _retr,
    self_state as _ss,
    replay as _rp,
)
from fractalish_ai.operational_self.models import (
    CompressedMemory,
    ContradictionScar,
    FogRegion,
    MemoryAttractor,
    MemoryEvent,
    MemoryLink,
    OperationalSelfState,
    ReplayRoute,
)

DETERMINISTIC_TSTAMP = "2026-08-14T12:00:00+00:00"
GLOBAL_CTX = "*"  # ladder global-context marker (matches baby_ai.ladder.oracle.GLOBAL)

# ------------------------------------------------------------------ allocator
# The in-process DeterministicIdStream is a DELIVERY mechanism only; it is not
# itself the persisted continuity contract. Continuity lives in the serialized
# "id_continuation" block (explicit, versioned counters). Every load path MUST
# either present that block or accept a DETERMINISTIC derivation from the
# collections actually present (max index in each collection + 1); anything
# else is rejected at the boundary and the core enters formation_blocked
# (HOLD, no write into the formed-state). See FormationCore.reconcile_allocator.
ALLOCATOR_CONTRACT_VERSION = "v0.1"
ALLOCATOR_PREFIXES = ("mem", "attr", "fog", "scar", "lnk", "replay", "evt")
# (prefix, separator) per persistent id family. "evt" has no persistent
# collection (its records are transient) so it carries no id format and
# derives to 0 in legacy mode.
ALLOCATOR_ID_FORMATS = {
    "mem": ("mem", "-"),
    "attr": ("attr", "_"),
    "fog": ("fog", "-"),
    "scar": ("scar", "-"),
    "lnk": ("lnk", "-"),
    "replay": ("replay", "-"),
}

# Deterministic sanity cap: an explicit counter more than this many indices
# ABOVE the derived floor is treated as nonsensical/overflow and rejected
# (formation_blocked). Absolute bounds are banned because they would break
# legitimate batches; the cap tracks the floor so it scales with the store.
ALLOCATOR_INDEX_HEADROOM = 10_000_000


def _family_ids(core: "FormationCore", family: str):
    """Live iterable of persistent ids currently present for a family."""
    if family == "mem":
        return list(core.memories.keys())
    if family == "attr":
        return list(core.attractors.keys())
    if family == "fog":
        return [f.fog_id for f in core.fog]
    if family == "scar":
        return [s.scar_id for s in core.scars]
    if family == "lnk":
        return [l.link_id for l in core.links]
    if family == "replay":
        return [r.route_id for r in core.routes]
    return []

_ID_TAIL = re.compile(r"-(\d+)$")


def _record_provenance_allocator_migration(core: "FormationCore", family: str,
                                          floor: int, operator_value: int,
                                          pre_hash: str, post_hash: str,
                                          reason: str) -> None:
    """Permanent provenance row for a manual operator allocator handoff."""
    if any(r["component"] == "FormationCore/allocator" and r["organ"] == "operator_override"
           and r.get("modifications", "").startswith(f"family={family} ") for r in core.provenance.records):
        return
    core.provenance.record(
        component="FormationCore/allocator",
        organ="operator_override",
        reuse_kind="operator",
        path="operator-supplied migration counter (see MigrationReceiptLedger)",
        sha256=post_hash,
        modifications=(f"family={family} floor={floor} value={operator_value} "
                       f"pre={pre_hash} post={post_hash} reason={reason}"),
    )


def _max_next_index(ids, prefix: str) -> int:
    """max(index among ids)+1, 0 when empty. For '_'-separated attr ids both
    separator variants are considered (legacy attrs used 'attr-<n>')."""
    best = -1
    for raw in ids:
        for sep in ("-", "_"):
            i = raw.rfind(prefix + sep)
            if i < 0:
                continue
            tail = raw[i + len(prefix) + 1:]
            if not tail.isdigit():
                continue
            best = max(best, int(tail))
    return best + 1


def _counters_from_state(core: "FormationCore") -> dict[str, int]:
    """Deterministic next-index derivation from the collections ONLY."""
    return {
        "mem": _max_next_index(core.memories, "mem"),
        "attr": _max_next_index(core.attractors, "attr"),
        "fog": _max_next_index((f.fog_id for f in core.fog), "fog"),
        "scar": _max_next_index((s.scar_id for s in core.scars), "scar"),
        "lnk": _max_next_index((l.link_id for l in core.links), "lnk"),
        "replay": _max_next_index((r.route_id for r in core.routes), "replay"),
        "evt": 0,
    }


def _mk(**kw: Any):
    return dict(kw)


class DeterministicIdStream:
    """Adapter-layer deterministic id generator (replaces organ uuid4 noise)."""

    def __init__(self) -> None:
        self.counters: dict[str, int] = {}

    def nid(self, prefix: str) -> str:
        n = self.counters.get(prefix, 0)
        self.counters[prefix] = n + 1
        return f"{prefix}-{n:04d}"


class FormationCore:
    def __init__(
        self,
        *,
        activation_id: str = "baby-mvp-a",
        project_id: str = "baby-ai-v0.1",
        receipts: ReceiptLedger | None = None,
        provenance: ProvenanceLedger | None = None,
    ) -> None:
        self.activation_id = activation_id
        self.ids = DeterministicIdStream()
        self.receipts = receipts or ReceiptLedger()
        self.provenance = provenance or ProvenanceLedger(self.receipts)
        self.state = _ss.create_initial_self(activation_id=activation_id, project_id=project_id)
        # normalize wall-clock + organ-random ids out of the organ-created state
        self.state.self_id = f"oself-{activation_id}"
        self.state.last_updated = DETERMINISTIC_TSTAMP
        self.memories: dict[str, CompressedMemory] = {}
        self.attractors: dict[str, MemoryAttractor] = {}
        self.links: list[MemoryLink] = []
        self.scars: list[ContradictionScar] = []
        self.fog: list[FogRegion] = []
        self.routes: list[ReplayRoute] = []
        # context dimension (repair v0.1): which context each memory/store was
        # grounded in, plus the origin op-kind of each contradiction scar.
        self.mem_contexts: dict[str, str] = {}
        self.scar_contexts: dict[str, str] = {}
        self.scar_kinds: dict[str, str] = {}
        # dependency dimension (repair v0.1): dependent surface -> ordered
        # prerequisite surfaces. Satisfaction is evaluated per-query-context by
        # the representation layer reusing the formed-state gate; the router's
        # raw path is untouched. Direct primitive only: no recursion, no graph.
        self.dependencies: dict[str, list[str]] = {}
        # dependency ledger (repair v0.2): append-only record of every DEPEND
        # and RELIEVE event. A RELIEVE un-binds only the CURRENT binding; the
        # old edge remains reconstructible from this ledger but never
        # resurrects. Redeclared DEPEND re-binds the edge.
        self.dependency_ledger: list[dict[str, str]] = []
        # surface attribution (repair v0.1): the event's structured_summary
        # {action, subject, group} survives compression nowhere, so it is kept
        # in a side registry mirroring mem_contexts/scar_contexts, letting the
        # representation distinguish OWN-state from token-overlap records.
        self.mem_tuples: dict[str, dict[str, str]] = {}
        # temporal validity (repair v0.3): (entity, context) -> list of
        # [from, to] VALID windows. At route time a formation is admissible
        # only while some applicable window contains the query time; when the
        # entity records no window the gate is inert (always in-window).
        self.valid_windows: dict[tuple[str, str], list[list[int]]] = {}
        # allocator continuity: whether this core MAY allocate persistent ids.
        # Fresh construction is always ready; a load that cannot establish
        # explicit-or-derived continuation sets _formation_blocked and the
        # router then only answers HOLD. See reconcile_allocator.
        self._formation_blocked = False
        self.allocator_status: dict[str, Any] = {
            "kind": "fresh",
            "reason": "new core: id_continuation established on first load/knowledge",
            "counters": dict(self.ids.counters),
            "version": ALLOCATOR_CONTRACT_VERSION,
        }
        self._record_provenance()

    def _record_provenance(self) -> None:
        import baby_ai._env as env

        opsha = env._ORGANS.get("OLD_FRACTALISH_AI_PACKAGE", {}).get("package_sha256")
        # idempotent: __init__ + from_dict share one ledger, so the record
        # (and its semantically-derived hash) must not be re-appended twice.
        uid = ("FormationCore", "OLD FRACTALISH-AI / OPERATIONAL SELF")
        if any(r["component"] == uid[0] and r["organ"] == uid[1]
               for r in self.provenance.records):
            return
        self.provenance.record(
            component="FormationCore",
            organ="OLD FRACTALISH-AI / OPERATIONAL SELF",
            reuse_kind="import",
            path=str(env.OLD_FRACTALISH_AI_TREE),
            sha256=opsha,
            modifications="adapter layer: deterministic id stream + fixed timestamps; no organ mutation",
        )

    # ------------------------------------------------------------ allocator
    def formation_ready(self) -> bool:
        """True when this core may allocate persistent ids (i.e. continuation
        was established explicitly or derived deterministically)."""
        return not self._formation_blocked

    def allocator_continuation(self) -> dict[str, Any]:
        """Human/audit evidence for the allocator-continuity decision."""
        return {
            "ready": self.formation_ready(),
            "status": dict(self.allocator_status),
        }

    def allocator_family_ids(self, family: str) -> list[str]:
        """Persistent ids currently present for a family (collections only;
        never the in-memory counter stream)."""
        if family not in ALLOCATOR_PREFIXES:
            raise ValueError(f"unknown allocator family {family!r}")
        return sorted(_family_ids(self, family))

    def allocator_state_hash(self) -> str:
        """Deterministic hash over the identity-bearing allocator surface:
        every family's present ids plus the continuation status/counters."""
        from baby_ai.core.semantics import canonical_json

        surface = {
            "status": {k: v for k, v in self.allocator_status.items()},
            "counters": dict(self.ids.counters),
            "ids": {f: self.allocator_family_ids(f) for f in ALLOCATOR_PREFIXES},
        }
        import hashlib

        return hashlib.sha256(canonical_json(surface).encode("utf-8")).hexdigest()

    def apply_operator_allocator_override(
        self,
        family: str,
        operator_value: int,
        *,
        reason: str,
        ledger_root: str | None = None,
    ) -> dict[str, Any]:
        """MANUAL allocator handoff with a permanent migration receipt.

        The derived floor is the default; an operator counter is an explicit
        exception and is ONLY permitted when it does not collide with (i.e. is
        strictly above) every id the collections already prove, and ONLY with a
        stated reason. The handoff is recorded in the MigrationReceiptLedger:
        pre-migration state hash, derived floor, operator value, reason the
        derived value was insufficient, post-migration hash. Manual counters
        are never silent history. Returns the written receipt + new status.
        """
        from baby_ai.core.migration_receipts import MigrationReceiptLedger

        if family not in ALLOCATOR_PREFIXES:
            raise ValueError(f"unknown allocator family {family!r}")
        if isinstance(operator_value, bool) or not isinstance(operator_value, int):
            raise ValueError(f"operator_value must be an int, got {operator_value!r}")
        if not reason or not reason.strip():
            raise ValueError("a stated reason is required: manual counters are never silent history")
        derived_floor = self._derive_counters().get(family, 0)
        if operator_value < derived_floor:
            raise ValueError(
                f"operator value {operator_value} is below derived floor {derived_floor} for {family!r} "
                "(an operator cannot lower the floor)"
            )
        if operator_value > derived_floor + ALLOCATOR_INDEX_HEADROOM:
            raise ValueError(
                f"operator value {operator_value} is absurdly above floor {derived_floor} "
                f"(headroom {ALLOCATOR_INDEX_HEADROOM}); refuse"
            )

        observed = self.allocator_family_ids(family)
        pre_hash = self.allocator_state_hash()
        self.ids.counters[family] = operator_value
        self.allocator_status = {
            "kind": "operator_override",
            "reason": f"operator handoff for {family}: {reason}",
            "counters": dict(self.ids.counters),
            "version": ALLOCATOR_CONTRACT_VERSION,
        }
        post_hash = self.allocator_state_hash()
        ledger = MigrationReceiptLedger(ledger_root) if ledger_root else MigrationReceiptLedger()
        receipt = ledger.record(
            activation_id=self.activation_id,
            family=family,
            derived_floor=derived_floor,
            operator_value=operator_value,
            reason_derived_insufficient=reason,
            pre_state_hash=pre_hash,
            post_state_hash=post_hash,
            observed_ids=observed,
        )
        self.receipts.append(
            action="allocator.operator_override",
            targets=[f"family={family}"],
            evidence=[f"floor={derived_floor}", f"value={operator_value}", reason],
            payload={"pre_hash": pre_hash, "post_hash": post_hash, "receipt_hash": receipt["receipt_hash"]},
        )
        _record_provenance_allocator_migration(self, family, derived_floor, operator_value,
                                                pre_hash, post_hash, reason)
        return {"receipt": receipt, "allocator": self.allocator_continuation()}

    def _derive_counters(self) -> dict[str, int]:
        return _counters_from_state(self)

    def _block_allocator(self, reason: str) -> None:
        self._formation_blocked = True
        self.allocator_status = {
            "kind": "FAIL",
            "reason": reason,
            "counters": None,
            "version": ALLOCATOR_CONTRACT_VERSION,
        }

    def reconcile_allocator(self, persisted: Any) -> dict[str, Any]:
        """Establish allocator continuation for a loaded core. Rules (single
        deterministic policy, enforced at the load boundary):

        1. NO id_continuation block -> DERIVE next-index from the collections
           actually present (max index in each + 1). This is what a legacy
           serialization (organ session glyph, device packet, prior MVP dump)
           must rely on: collapsed collections leave a unique max that any
           future allocator will exceed.
        2. Malformed/partial block (bad version, missing/invalid counter,
           unknown prefix, stale counter below what the collections already
           require) -> REJECT. The core enters formation_blocked and answers
           HOLD only; the run is never silently self-repaired by guessing.
        3. Explicit counters equal-or-beyond collections -> first-next-index
           = counter value (explicit continuation wins).

        Prepends provenance evidence to the shared ledger (idempotent on the
        (phase, policies) identity)."""
        import baby_ai._env as env

        derived = self._derive_counters()
        baseline = dict(self.ids.counters)
        if persisted is None:
            self.ids.counters.update(derived)
            self.allocator_status = {
                "kind": "derived_legacy",
                "reason": "no id_continuation in source; deterministic max(existing id)+1 per family",
                "counters": dict(self.ids.counters),
            }
            self._record_reconcile_evidence(env, "load_derived", baseline, {}, self.allocator_status["reason"])
            return self.allocator_continuation()

        # ------------------------------------------------------------------
        # note: a derived core already skipping strict structural checks below
        if not isinstance(persisted, dict) or persisted.get("version") != ALLOCATOR_CONTRACT_VERSION:
            self._block_allocator(
                "id_continuation malformed: missing/bad version "
                f"(want {ALLOCATOR_CONTRACT_VERSION}, got {persisted.get('version') if isinstance(persisted, dict) else persisted!r})"
            )
            self._record_reconcile_evidence(env, "load_reject", baseline, {}, self.allocator_status["reason"])
            return self.allocator_continuation()
        counters = persisted.get("counters")
        if not isinstance(counters, dict):
            self._block_allocator("id_continuation malformed: counters is not a dict")
            self._record_reconcile_evidence(env, "load_reject", baseline, {}, self.allocator_status["reason"])
            return self.allocator_continuation()
        unknown = set(counters) - set(ALLOCATOR_PREFIXES)
        if unknown:
            self._block_allocator(f"id_continuation malformed: unknown prefix(es) {sorted(unknown)}")
            self._record_reconcile_evidence(env, "load_reject", baseline, {}, self.allocator_status["reason"])
            return self.allocator_continuation()
        missing = [p for p in ALLOCATOR_PREFIXES if p not in counters]
        if missing:
            self._block_allocator(f"id_continuation malformed: missing prefix(es) {missing}")
            self._record_reconcile_evidence(env, "load_reject", baseline, {}, self.allocator_status["reason"])
            return self.allocator_continuation()

        errors: list[str] = []
        parsed: dict[str, int] = {}
        for prefix in ALLOCATOR_PREFIXES:
            val = counters.get(prefix)
            if isinstance(val, bool) or not isinstance(val, int):
                errors.append(f"{prefix}: non-integer {val!r}")
                continue
            if val < 0:
                errors.append(f"{prefix}: negative {val}")
                continue
            need = derived[prefix]
            if val < need:
                errors.append(f"{prefix}: stale counter {val} < required {need}")
                continue
            if val > need + ALLOCATOR_INDEX_HEADROOM:
                errors.append(
                    f"{prefix}: nonsensical/overflow counter {val} > floor {need} + headroom {ALLOCATOR_INDEX_HEADROOM}"
                )
                continue
            parsed[prefix] = val
        if errors:
            self._block_allocator("id_continuation REJECTED: " + " | ".join(errors))
            self._record_reconcile_evidence(env, "load_reject", baseline, parsed, self.allocator_status["reason"])
            return self.allocator_continuation()

        self.ids.counters.update(parsed)
        self.allocator_status = {
            "kind": "persisted",
            "reason": "explicit id_continuation accepted",
            "counters": dict(self.ids.counters),
            "version": ALLOCATOR_CONTRACT_VERSION,
        }
        self._record_reconcile_evidence(env, "load_accept", baseline, dict(parsed),
                                        self.allocator_status["reason"])
        return self.allocator_continuation()



    def _record_reconcile_evidence(self, env, phase: str, baseline: dict,
                                   explicit: dict, reason: str) -> None:
        """Append allocator reconciliation evidence to the provenance ledger,
        idempotent on (phase) identity: a core records at most one row per
        reconciliation phase (load_derived/load_accept/load_reject)."""
        if any(r["component"] == "FormationCore/allocator" and r["organ"] == phase
               for r in self.provenance.records):
            return
        self.provenance.record(
            component="FormationCore/allocator",
            organ=phase,
            reuse_kind="load",
            path="serialized id_continuation",
            sha256=("explicit" if explicit else "derived"),
            modifications=f"counters baseline={baseline} explicit={explicit}; {reason}",
        )

    def record_dependency(self, dependent: str, prerequisite: str) -> None:
        """Declare a keyed dependency edge: `dependent` may proceed only while
        `prerequisite` is in a formed, non-blocked state in the query context.
        Direct primitive: one record per (dependent, prerequisite); no graph,
        no recursion (the representation layer walks cycles at route time)."""
        lst = self.dependencies.setdefault(dependent, [])
        if prerequisite not in lst:
            lst.append(prerequisite)
        self.dependency_ledger.append({"kind": "DEPEND", "dependent": dependent,
                                       "prerequisite": prerequisite})

    def relieve_dependency(self, dependent: str, prerequisite: str) -> None:
        """Un-bind the directional edge (dependent -> prerequisite) from the
        CURRENT binding only. The edge remains in the ledger (reconstructible,
        never resurrected); a later DEPEND re-binds it. RELIEVE never touches
        formed/proposition state."""
        lst = self.dependencies.get(dependent)
        if lst and prerequisite in lst:
            lst.remove(prerequisite)
            if not lst:
                self.dependencies.pop(dependent, None)
        self.dependency_ledger.append({"kind": "RELIEVE", "dependent": dependent,
                                       "prerequisite": prerequisite})

    def record_valid_window(self, entity: str, from_t: int, to_t: int,
                            *, context: str = "*") -> None:
        """Declare a VALID [from..to] window for an entity in a context. An
        entity may accumulate multiple windows (the oracle appends). At route
        time admissible only while some applicable window contains the query
        time; no window recorded => always in-window."""
        self.valid_windows.setdefault((entity, context), []).append([from_t, to_t])

    # ------------------------------------------------------------ formation
    def make_event(
        self,
        *,
        raw_summary: str,
        structured_summary: str = "",
        structured_tuple: dict | None = None,
        claims: list[str] | None = None,
        decisions: list[str] | None = None,
        tags: list[str] | None = None,
        guard_status: str = "WATCH",
        importance_hint: float = 0.6,
        confidence: float = 0.7,
        uncertainty: float = 0.3,
        provenance_extra: dict[str, Any] | None = None,
        context: str = GLOBAL_CTX,
        op_kind: str | None = None,
    ) -> MemoryEvent:
        eid = self.ids.nid("evt")
        extra = dict(provenance_extra or {})
        extra.setdefault("context", context)
        if op_kind is not None:
            extra["op_kind"] = op_kind
        if structured_tuple:
            extra["structured_tuple"] = dict(structured_tuple)
        return MemoryEvent(
            event_id=eid,
            activation_id=self.activation_id,
            source_type="mock_event",
            source_id="mvp-domain",
            timestamp=DETERMINISTIC_TSTAMP,
            raw_summary=raw_summary,
            structured_summary=structured_summary,
            claims=claims or [],
            decisions=decisions or [],
            guard_status=guard_status,
            importance_hint=importance_hint,
            confidence=confidence,
            uncertainty=uncertainty,
            tags=tags or [],
            provenance={"domain": "mvp", **extra},
        )

    def ingest(self, event: MemoryEvent) -> dict[str, Any]:
        """Full qualified formation: compress -> attractor -> scars -> fog -> links -> replay -> self."""
        if self._formation_blocked:
            return {
                "error": "formation_blocked",
                "decision": "HOLD",
                "reason": "allocator_continuation_failed",
                "allocator": dict(self.allocator_status),
            }
        memory = _comp.light_compress(event)
        attractor = _attr.create_attractor(event, memory)
        memory_id = "mem-" + self.ids.nid("mem")[4:]
        # normalize organ-generated ids into deterministic mirror set
        memory.memory_id = memory_id
        attractor.memory_id = memory_id
        attractor.attractor_id = "attr_" + self.ids.nid("attr")[5:]

        ev_ctx = str(event.provenance.get("context", GLOBAL_CTX))
        ev_kind = event.provenance.get("op_kind")
        self.mem_contexts[memory_id] = ev_ctx
        _tup = event.provenance.get("structured_tuple") if isinstance(getattr(event, "provenance", None), dict) else None
        self.mem_tuples[memory_id] = dict(_tup) if isinstance(_tup, dict) else {}

        new_scars = _scars.detect_scars_from_event(event, memory)
        fog_region = _fog.detect_fog_from_event(event, memory)

        self.memories[memory_id] = memory
        self.attractors[attractor.attractor_id] = attractor

        for s in new_scars:
            s.scar_id = "scar-" + self.ids.nid("scar")[5:]
            s.first_seen = DETERMINISTIC_TSTAMP
            s.last_seen = DETERMINISTIC_TSTAMP
            s.memory_ids = [mid if mid == memory_id else mid for mid in s.memory_ids]
            s.memory_ids = [memory_id]
            # link the paired memories if we know both sides
            self.scar_contexts[s.scar_id] = ev_ctx
            self.scar_kinds[s.scar_id] = str(ev_kind or "contradiction")
            self.scars.append(s)
            self._link_contradiction_scar(s)

        if fog_region:
            fog_region.fog_id = "fog-" + self.ids.nid("fog")[4:]
            fog_region.created_at = DETERMINISTIC_TSTAMP
            fog_region.related_memory_ids = [m if m == memory_id else memory_id for m in fog_region.related_memory_ids]
            self.fog.append(fog_region)

        self._link_supporting(event, memory_id)
        self._update_replay_routes(event)
        self.state = _ss.update_self_from_consolidation(self.state, event, memory, attractor, self.scars, fog_region, self.routes)
        self.state.last_updated = DETERMINISTIC_TSTAMP

        self.receipts.append(
            action="formation.ingest",
            targets=[memory_id, attractor.attractor_id],
            evidence=[event.raw_summary],
            payload={"claims": event.claims, "decisions": event.decisions},
        )

        return {
            "event_id": event.event_id,
            "memory_id": memory_id,
            "attractor_id": attractor.attractor_id,
            "scar_ids": [s.scar_id for s in new_scars],
            "fog_id": fog_region.fog_id if fog_region else None,
        }

    def _link_supporting(self, event: MemoryEvent, memory_id: str) -> None:
        for mid, mem in self.memories.items():
            if mid == memory_id:
                continue
            shared_tags = set(event.tags) & set(mem.retained_claims)
            if shared_tags:
                self.links.append(
                    MemoryLink(
                        link_id="lnk-" + self.ids.nid("lnk")[4:],
                        from_memory_id=memory_id,
                        to_memory_id=mid,
                        link_type="supports",
                        strength=0.7,
                        reason="shared tag",
                        evidence=list(shared_tags),
                    )
                )

    def _link_contradiction_scar(self, scar: ContradictionScar) -> None:
        if len(scar.memory_ids) >= 2:
            self.links.append(
                MemoryLink(
                    link_id="lnk-" + self.ids.nid("lnk")[4:],
                    from_memory_id=scar.memory_ids[0],
                    to_memory_id=scar.memory_ids[1],
                    link_type="contradicts",
                    strength=0.9,
                    reason="contradiction scar",
                    evidence=[scar.claim_a, scar.claim_b],
                )
            )

    def _update_replay_routes(self, event: MemoryEvent) -> None:
        label = event.structured_summary or event.raw_summary
        route = _rp.build_replay_route(label, self.memories, self.attractors, self.scars, self.fog)
        if route:
            route.route_id = "replay-" + self.ids.nid("replay")[7:]
            self.routes.append(route)

    def add_link(self, *, from_memory_id: str, to_memory_id: str, link_type: str, strength: float = 0.5, reason: str = "") -> MemoryLink:
        lnk = MemoryLink(
            link_id="lnk-" + self.ids.nid("lnk")[4:],
            from_memory_id=from_memory_id,
            to_memory_id=to_memory_id,
            link_type=link_type,  # type: ignore[arg-type]
            strength=strength,
            reason=reason,
            evidence=[],
        )
        self.links.append(lnk)
        return lnk

    # --------------------------------------------------------------- route
    def retrieve(self, query: str, limit: int = 5) -> dict[str, Any]:
        return _retr.retrieve(
            query,
            memories=self.memories,
            attractors=self.attractors,
            links=self.links,
            scars=self.scars,
            limit=limit,
        )

    def route_decision(
        self,
        query: str,
        plasticity: "Any | None" = None,
        *,
        applicability: str | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Deterministic domain routing over formed state (formation core gating).

        If a PlasticityExecutor is supplied, its scar lifecycle status is
        authoritative: a contradiction scar in unresolved/hold state BLOCKS the
        routed RELEASE; once the scar is superseded/resolved, the formed RELEASE
        decision is allowed through again. This is the Gap A causal hook: the
        executor, not the router, decides when a scar stops blocking.

        APPLICABILITY GATE (adapter-local, repair v0.1): when `applicability` is
        given, it is the query's DECLARED SCOPE (a stable identity token, e.g.
        the family tag). A retrieved record is only admissible if one of its
        stored tags equals the declared scope EXACTLY. Retrieval may surface
        candidates (lexical overlap is allowed); retrieval does NOT make them
        consequential. With no declared scope, behavior is unchanged (legacy).

        CONTEXT GATE (adapter-local, repair v0.1): when `context` is given it is
        the query's DECLARED CONTEXT. A memory is admissible only if it was
        grounded in that context or in the global context ("*"), and a
        contradiction scar blocks only if it was raised in that context or
        globally. When a scoped scar blocks, the reason token names the scar
        origin (MARK -> active_contradiction, SUPERSEDE HOLD ->
        declared_prohibition) and, if nothing grounds a RELEASE decision inside
        the query's context, evidence_missing is added. With no declared
        context, behavior is unchanged (legacy: scar-blocking reason stays
        "contradiction_scar_blocking").

        ALLOCATOR CONTINUITY (repair): routing is a READ path (no ids are
        allocated) so it still surfaces whatever was formed. When this core is
        in formation_blocked (its id_continuation could not be established at
        load), every reply carries the allocator status and any would-be
        RELEASE is downgraded to HOLD with reason EVIDENCE — an operator can
        see "what would have happened had I not survived" alongside the reason
        the allocator rejected continuation.
        """
        out = self._evaluate_route(
            query, plasticity, applicability=applicability, context=context
        )
        if self._formation_blocked:
            status = dict(self.allocator_status)
            out["allocator"] = status
            if out.get("decision") == "RELEASE":
                out["decision"] = "HOLD"
                out["reason"] = "EVIDENCE"
                out["evidence"] = list(out.get("evidence", [])) + [
                    f"loader_rejected_allocator_continuation: {status.get('reason')}"
                ]
        return out

    def _evaluate_route(
        self,
        query: str,
        plasticity: "Any | None" = None,
        *,
        applicability: str | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        res = self.retrieve(query)
        results = res.get("results", [])
        if not results:
            return {"query": query, "decision": "HOLD", "reason": "no_formed_memory", "evidence": [], "match": None}

        ctx_query = context if context is not None else GLOBAL_CTX

        if applicability is not None:
            applicable = self._applicable_results(results, applicability, context)
            if not applicable:
                return {
                    "query": query,
                    "decision": "HOLD",
                    "reason": "no_applicable_evidence",
                    "evidence": [r.get("memory_id") for r in results],
                    "match": results[0],
                    "retrieved_but_inapplicable": [r.get("memory_id") for r in results],
                }
            results = applicable
        elif context is not None:
            keep: list[dict] = []
            for r in results:
                mid = r.get("memory_id")
                if self.mem_contexts.get(mid, GLOBAL_CTX) in (ctx_query, GLOBAL_CTX):
                    keep.append(r)
            results = keep

        # Gather all formed RELEASE-family decisions reachable for this query.
        release_matches: list[dict] = []
        for r in results:
            mem = self.memories.get(r.get("memory_id"))
            if not mem:
                continue
            decisions = [d.strip().upper() for d in mem.retained_decisions]
            if any(d.startswith("RELEASE") for d in decisions):
                release_matches.append(r)

        blocking_scars = self._blocking_scars_for(results, plasticity, context)
        if release_matches and not blocking_scars:
            best = results[0]
            decisions = [d.strip().upper() for d in (self.memories.get(best.get("memory_id")).retained_decisions or [])]
            action = next((d for d in decisions if d.startswith("RELEASE")), "RELEASE")
            return {"query": query, "decision": "RELEASE", "reason": f"formed_decision:{action}", "evidence": decisions, "match": best}

        if blocking_scars:
            out: dict[str, Any] = {
                "query": query,
                "decision": "HOLD",
                "reason": "contradiction_scar_blocking",
                "evidence": [b.replay_warning or f"scar {b.scar_id}" for b in blocking_scars],
                "match": results[0],
            }
            if context is not None:
                causes, reason = self._cause_for_block(blocking_scars, release_matches)
                out["reason"] = reason
                out["causes"] = causes
            return out
        return {"query": query, "decision": "HOLD", "reason": "no_release_decision", "evidence": [], "match": results[0]}

    def _cause_for_block(self, blocking_scars: list[ContradictionScar], release_matches: list[dict]) -> tuple[list[str], str]:
        kinds = [self.scar_kinds.get(s.scar_id, "contradiction") for s in blocking_scars]
        primary = "declared_prohibition" if any(str(k).upper() == "SUPERSEDE" for k in kinds) else "active_contradiction"
        causes = [primary]
        if not release_matches:
            causes.append("evidence_missing")
        return causes, primary

    def _applicable_results(self, results: list[dict], scope: str, context: str | None = None) -> list[dict]:
        """Keep only retrieved candidates whose stored tag identity matches the
        declared scope exactly and (when a context is declared) whose grounding
        context is the query context or global. Stable identity is the tag — NOT
        lexical overlap. Rejects token-sharing records that belong to a
        different family."""
        mem_tags: dict[str, list[str]] = {}
        for attr in self.attractors.values():
            mem_tags.setdefault(attr.memory_id, []).extend(list(attr.tags or []))
        permit_ctx = context if context is not None else GLOBAL_CTX
        out: list[dict] = []
        for r in results:
            mid = r.get("memory_id")
            tags = mem_tags.get(mid, [])
            if not any(t == scope for t in tags):
                continue
            if self.mem_contexts.get(mid, GLOBAL_CTX) not in (permit_ctx, GLOBAL_CTX):
                continue
            out.append(r)
        return out

    def _blocking_scars_for(self, results: list[dict], plasticity: "Any | None", context: str | None = None) -> list[ContradictionScar]:
        memory_ids = {r.get("memory_id") for r in results}
        permit_ctx = context if context is not None else GLOBAL_CTX
        out: list[ContradictionScar] = []
        for scar in self.scars:
            if not (set(scar.memory_ids) & memory_ids):
                continue
            if self.scar_contexts.get(scar.scar_id, GLOBAL_CTX) not in (permit_ctx, GLOBAL_CTX):
                continue
            if plasticity is not None:
                status = plasticity.get_scar_status(scar.scar_id)
                if status in ("superseded", "resolved"):
                    continue  # executor has cleared the block
            if scar.status in ("superseded", "resolved"):
                continue
            out.append(scar)
        return out

    # ------------------------------------------------------------- ablation
    def remove_attractor(self, memory_id: str) -> str | None:
        for aid, attr in list(self.attractors.items()):
            if attr.memory_id == memory_id:
                del self.attractors[aid]
                return aid
        return None

    def restore_attractor(self, attractor: MemoryAttractor) -> None:
        self.attractors[attractor.attractor_id] = attractor

    # ---------------------------------------------------------- persistence
    def to_dict(self) -> dict[str, Any]:
        def dd(obj):
            return obj.to_dict()

        return {
            "state": self.state.to_dict(),
            "memories": {k: dd(v) for k, v in self.memories.items()},
            "attractors": {k: dd(v) for k, v in self.attractors.items()},
            "links": [dd(v) for v in self.links],
            "scars": [dd(v) for v in self.scars],
            "fog": [dd(v) for v in self.fog],
            "routes": [dd(v) for v in self.routes],
            "mem_contexts": dict(self.mem_contexts),
            "scar_contexts": dict(self.scar_contexts),
            "scar_kinds": dict(self.scar_kinds),
            "mem_tuples": {k: dict(v) for k, v in self.mem_tuples.items()},
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "dependency_ledger": [dict(v) for v in self.dependency_ledger],
            "valid_windows": {f"{e}\x00{c}": [list(w) for w in wins]
                              for (e, c), wins in self.valid_windows.items()},
            # explicit allocator continuity: next-id counters, versioned. The
            # contract always carries ALL families (untouched = 0) so the block
            # round-trips as a complete, parseable continuation.
            "id_continuation": {
                "version": ALLOCATOR_CONTRACT_VERSION,
                "counters": {p: self.ids.counters.get(p, 0) for p in ALLOCATOR_PREFIXES},
            },
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        activation_id: str = "baby-mvp-a",
        receipts: Any = None,
        provenance: Any = None,
    ) -> "FormationCore":
        core = cls(activation_id=activation_id, receipts=receipts, provenance=provenance)

        def rebuilt(cls_, payload: dict[str, Any]):
            field_names = {f.name for f in _fields(cls_)}
            return cls_(**{k: v for k, v in payload.items() if k in field_names})

        core.state = rebuilt(OperationalSelfState, data["state"])
        core.memories = {k: rebuilt(CompressedMemory, v) for k, v in data.get("memories", {}).items()}
        core.attractors = {k: rebuilt(MemoryAttractor, v) for k, v in data.get("attractors", {}).items()}
        core.links = [rebuilt(MemoryLink, v) for v in data.get("links", [])]
        core.scars = [rebuilt(ContradictionScar, v) for v in data.get("scars", [])]
        core.fog = [rebuilt(FogRegion, v) for v in data.get("fog", [])]
        core.routes = [rebuilt(ReplayRoute, v) for v in data.get("routes", [])]
        core.mem_contexts = dict(data.get("mem_contexts", {}))
        core.scar_contexts = dict(data.get("scar_contexts", {}))
        core.scar_kinds = dict(data.get("scar_kinds", {}))
        core.mem_tuples = {k: dict(v) for k, v in data.get("mem_tuples", {}).items()}
        core.dependencies = {k: list(v) for k, v in data.get("dependencies", {}).items()}
        core.dependency_ledger = [dict(v) for v in data.get("dependency_ledger", [])]
        core.valid_windows = {}
        for key, wins in data.get("valid_windows", {}).items():
            e, _, c = key.partition("\x00")
            core.valid_windows[(e, c)] = [list(w) for w in wins]
        core.reconcile_allocator(data.get("id_continuation"))
        return core

    def counts(self) -> dict[str, int]:
        return {
            "memories": len(self.memories),
            "attractors": len(self.attractors),
            "links": len(self.links),
            "scars": len(self.scars),
            "fog": len(self.fog),
            "routes": len(self.routes),
        }