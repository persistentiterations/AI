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
        # surface attribution (repair v0.1): the event's structured_summary
        # {action, subject, group} survives compression nowhere, so it is kept
        # in a side registry mirroring mem_contexts/scar_contexts, letting the
        # representation distinguish OWN-state from token-overlap records.
        self.mem_tuples: dict[str, dict[str, str]] = {}
        self._record_provenance()

    def _record_provenance(self) -> None:
        import baby_ai._env as env

        opsha = env._ORGANS.get("OLD_FRACTALISH_AI_PACKAGE", {}).get("package_sha256")
        self.provenance.record(
            component="FormationCore",
            organ="OLD FRACTALISH-AI / OPERATIONAL SELF",
            reuse_kind="import",
            path=str(env.OLD_FRACTALISH_AI_TREE),
            sha256=opsha,
            modifications="adapter layer: deterministic id stream + fixed timestamps; no organ mutation",
        )

    def record_dependency(self, dependent: str, prerequisite: str) -> None:
        """Declare a keyed dependency edge: `dependent` may proceed only while
        `prerequisite` is in a formed, non-blocked state in the query context.
        Direct primitive: one record per (dependent, prerequisite); no graph,
        no recursion, no cycle semantics (RELIEVE/cycles deferred)."""
        lst = self.dependencies.setdefault(dependent, [])
        if prerequisite not in lst:
            lst.append(prerequisite)

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
        """
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
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, activation_id: str = "baby-mvp-a") -> "FormationCore":
        core = cls(activation_id=activation_id)

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