"""Five representations for the complexity ladder (§4).

Each representation receives the SAME op stream and must answer the SAME query
set with the same ground truth as the Oracle. They differ ONLY in what they
store and how they derive a verdict:

  A. scalar/current-state          one current verdict per (e,g,ctx), no history
  B. keyed/versioned state         per-key record lists + explicit derived map
  C. minimal admissibility         record-per-cause; block causes are first class
  D. explicit relational graph     nodes/edges with reachability walk + cycle guard
  E. historical Fractalish         FULL current architecture (FormationCore)

All are written to be competent, not crippled. Richer structure must earn its
keep through correctness/cost on the same task, or it is overhead.
"""

from __future__ import annotations

from typing import Any

from baby_ai.ladder.oracle import GLOBAL, family_of


class Representation:
    name = "?"

    def apply(self, op: dict[str, Any]) -> None:
        raise NotImplementedError

    def route(self, e: str, g: str, *, ctx: str = GLOBAL, t: int | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def state_bytes(self) -> int:
        raise NotImplementedError

    def work(self) -> dict[str, int]:
        return {"applies": 0, "routes": 0}


# ------------------------------------------------------------------ A
class ScalarCurrent(Representation):
    """One current verdict per (e, g, ctx). No history, no dependencies, no time.
    This is the least-structure baseline: it simply cannot answer relational,
    historical, or temporal demands beyond its current-value dict."""

    name = "A_scalar_current_state"

    def __init__(self) -> None:
        self.current: dict[tuple[str, str, str], str] = {}
        self._w = {"applies": 0, "routes": 0}

    def apply(self, op: dict[str, Any]) -> None:
        self._w["applies"] += 1
        k = (op.get("e"), op.get("g", ""), op.get("ctx", GLOBAL))
        if op["op"] == "FORM":
            self.current[k] = "PROCEED"
        elif op["op"] == "MARK":
            self.current[k] = "HOLD"
        elif op["op"] == "RESOLVE":
            self.current[k] = "PROCEED"
        elif op["op"] == "SUPERSEDE":
            self.current[k] = "PROCEED" if op.get("decision") == "PROCEED" else "HOLD"
        # DEPEND/RELIEVE/VALID: not representable in a scalar current-state.
        # We record their occurrence as work but cannot model them.

    def route(self, e: str, g: str, *, ctx: str = GLOBAL, t: int | None = None) -> dict[str, Any]:
        self._w["routes"] += 1
        v = self.current.get((e, g, ctx)) or self.current.get((e, g, GLOBAL))
        if v == "PROCEED":
            return {"decision": "PROCEED", "causes": []}
        return {"decision": "HOLD", "causes": ["evidence_missing"]}

    def state_bytes(self) -> int:
        import json
        return len(json.dumps(
            {f"{k[0]}||{k[1]}||{k[2]}": v for k, v in self.current.items()}, sort_keys=True))

    def work(self) -> dict[str, int]:
        return dict(self._w)


# ------------------------------------------------------------------ B
class KeyedVersioned(Representation):
    """Per-key record lists (history preserved) + a derived current map.
    Dependencies are tracked as plain keyed lists (parent -> children) and a
    query walks the dependency chain recursively with a cycle guard. Context is
    a key dimension; time is answered only if the record has an interval.
    Competent keyed/versioned state — NOT a graph object."""

    name = "B_keyed_versioned_state"

    def __init__(self) -> None:
        self.records: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        self.children: dict[str, set[str]] = {}        # parent -> {children}
        self._seq = 0
        self._w = {"applies": 0, "routes": 0}

    def apply(self, op: dict[str, Any]) -> None:
        self._w["applies"] += 1
        kind = op["op"]
        e = op.get("e")
        g = op.get("g", "")
        ctx = op.get("ctx", GLOBAL)
        k = (e, g, ctx) if e else None
        rec = dict(op)
        rec["_seq"] = self._seq
        self._seq += 1
        if kind in ("FORM", "MARK", "RESOLVE", "SUPERSEDE") and e:
            self.records.setdefault(k, []).append(rec)
        elif kind == "DEPEND":
            self.children.setdefault(op["b"], set()).add(op["a"])
        elif kind == "RELIEVE":
            self.children.setdefault(op["b"], set()).discard(op["a"])
        elif kind == "VALID" and e:
            self.records.setdefault(k, []).append(rec)

    def _res_records(self, e: str, g: str, ctx: str) -> list[dict[str, Any]]:
        """All records for (e,g) visible in this context, most recent last."""
        lists = []
        if ctx == GLOBAL:
            lists = [self.records.get((e, g, GLOBAL), [])]
        else:
            lists = [self.records.get((e, g, ctx), []), self.records.get((e, g, GLOBAL), [])]
        merged = [r for lst in lists for r in lst]
        return sorted(merged, key=lambda r: r["_seq"])

    def _latest(self, e: str, g: str, ctx: str) -> dict[str, Any] | None:
        recs = self._res_records(e, g, ctx)
        return recs[-1] if recs else None

    def _own_verdict(self, e: str, g: str, ctx: str) -> str | None:
        latest = self._latest(e, g, ctx)
        if latest is None:
            return None
        if latest["op"] == "FORM":
            return "PROCEED"
        if latest["op"] == "MARK":
            return "HOLD"
        if latest["op"] == "RESOLVE":
            return "PROCEED"
        if latest["op"] == "SUPERSEDE":
            return "PROCEED" if latest.get("decision") == "PROCEED" else "HOLD"
        return None

    def route(self, e: str, g: str, *, ctx: str = GLOBAL, t: int | None = None) -> dict[str, Any]:
        self._w["routes"] += 1
        causes: list[str] = []
        own = self._own_verdict(e, g, ctx)
        # temporal windows: a VALID record narrower than the query time blocks
        recs = self._res_records(e, g, ctx)
        in_window = True
        for r in recs:
            if r["op"] == "VALID" and t is not None:
                if not (r["from"] <= t <= r["to"]):
                    in_window = False
        if not in_window:
            causes.append("expired_outside_window")

        grounded = own is not None or bool(self._parents_of(e, ctx)) or self._transfer_possible(e, g, ctx)
        if own is None:
            if not grounded:
                causes.append("evidence_missing")
        elif own == "HOLD":
            causes.append("declared_prohibition" if any(
                r["op"] == "SUPERSEDE" for r in recs) else "active_contradiction")
        # prerequisites: walk dependency chain of e
        for parent in self._parents_of(e, ctx):
            if self._dep_route(parent, g, ctx, t, _seen=set()) != "PROCEED":
                causes.append(f"prerequisite_missing:{parent}")
        if causes:
            return {"decision": "HOLD", "causes": sorted(set(causes))}
        return {"decision": "PROCEED", "causes": []}

    def _parents_of(self, e: str, ctx: str) -> list[str]:
        # scan children index: any key whose children include e
        return sorted(k for k, kids in self.children.items() if e in kids)

    def _transfer_possible(self, e: str, g: str, ctx: str) -> bool:
        fam = family_of(g)
        for (ej, gj, cj), recs in self.records.items():
            if ej == e:
                continue
            if gj != g:
                continue
            if family_of(gj) != fam:
                continue
            if self._own_verdict(ej, gj, cj) == "PROCEED":
                return True
        return False

    def _dep_route(self, e: str, g: str, ctx: str, t: int | None, *, _seen: set[str]) -> str:
        if e in _seen:
            return "CYCLE_BLOCKED"
        _seen = _seen | {e}
        own = self._own_verdict(e, g, ctx)
        if own == "HOLD":
            return "HOLD"
        for parent in self._parents_of(e, ctx):
            if self._dep_route(parent, g, ctx, t, _seen=_seen) != "PROCEED":
                return "HOLD"
        parents = self._parents_of(e, ctx)
        if own == "PROCEED" or parents:
            return "PROCEED"
        return "HOLD"

    def state_bytes(self) -> int:
        import json
        return len(json.dumps({
            "records": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in self.records.items()},
            "children": {k: sorted(v) for k, v in self.children.items()},
        }, sort_keys=True))

    def work(self) -> dict[str, int]:
        return dict(self._w)


# ------------------------------------------------------------------ C
class MinimalAdmissibility(Representation):
    """Records per cause; verdict derives from record structure. Distinct causes
    (evidence_missing / active_contradiction / declared_prohibition /
    prerequisite_missing / expired) are FIRST-CLASS: each is a separate record
    kind, so removing one cause reopens exactly the right continuation."""

    name = "C_minimal_admissibility"

    def __init__(self) -> None:
        self.support: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.marks: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.supersedes: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.deps: dict[str, set[str]] = {}
        self.windows: dict[tuple[str, str], list[tuple[int, int]]] = {}
        self._w = {"applies": 0, "routes": 0}

    def apply(self, op: dict[str, Any]) -> None:
        self._w["applies"] += 1
        e = op.get("e")
        g = op.get("g", "")
        ctx = op.get("ctx", GLOBAL)
        if op["op"] == "FORM" and e:
            self.support[(e, g, ctx)] = op
            self.marks.pop((e, g, ctx), None)
            self.supersedes.pop((e, g, ctx), None)
        elif op["op"] == "MARK" and e:
            self.marks[(e, g, ctx)] = op
        elif op["op"] == "RESOLVE" and e:
            self.marks.pop((e, g, ctx), None)
        elif op["op"] == "SUPERSEDE" and e:
            self.supersedes[(e, g, ctx)] = op
            self.marks.pop((e, g, ctx), None)
        elif op["op"] == "DEPEND":
            self.deps.setdefault(op["b"], set()).add(op["a"])
        elif op["op"] == "RELIEVE":
            self.deps.setdefault(op["b"], set()).discard(op["a"])
        elif op["op"] == "VALID" and e:
            self.windows.setdefault((e, ctx), []).append((op["from"], op["to"]))

    def _supported(self, e: str, g: str, ctx: str) -> bool:
        return (e, g, ctx) in self.support or (e, g, GLOBAL) in self.support

    def _causes(self, e: str, g: str, ctx: str, t: int | None,
                *, _seen: set[str] | None = None) -> list[str]:
        _seen = _seen or set()
        if e in _seen:
            return ["cyclic_constraint"]
        _seen = _seen | {e}
        causes: list[str] = []
        if (e, g, ctx) in self.supersedes and self.supersedes[(e, g, ctx)].get("decision") == "HOLD":
            causes.append("declared_prohibition")
        if (e, g, ctx) in self.marks:
            causes.append("active_contradiction")
        if not self._supported(e, g, ctx):
            if not self._transfer_possible(e, g, ctx):
                causes.append("evidence_missing")
        for parent in self._parents_of(e):
            if self._causes(parent, g, ctx, t, _seen=_seen):
                causes.append(f"prerequisite_missing:{parent}")
        if t is not None and not self._in_window(e, ctx, t):
            causes.append("expired_outside_window")
        return causes

    def _parents_of(self, e: str) -> list[str]:
        return sorted(k for k, kids in self.deps.items() if e in kids)

    def _transfer_possible(self, e: str, g: str, ctx: str) -> bool:
        fam = family_of(g)
        return any(
            ej != e and gj == g and family_of(gj) == fam and self._supported(ej, gj, cj)
            and (ej, gj, cj) not in self.marks
            for (ej, gj, cj) in list(self.support)
        )

    def _in_window(self, e: str, ctx: str, t: int) -> bool:
        w = self.windows.get((e, ctx)) or self.windows.get((e, GLOBAL)) or []
        if not w:
            return True
        return any(a <= t <= b for a, b in w)

    def route(self, e: str, g: str, *, ctx: str = GLOBAL, t: int | None = None) -> dict[str, Any]:
        self._w["routes"] += 1
        causes = self._causes(e, g, ctx, t)
        if causes:
            return {"decision": "HOLD", "causes": sorted(set(causes))}
        return {"decision": "PROCEED", "causes": []}

    def state_bytes(self) -> int:
        import json
        return len(json.dumps({
            "support": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in self.support.items()},
            "marks": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in self.marks.items()},
            "supersedes": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in self.supersedes.items()},
            "deps": {k: sorted(v) for k, v in self.deps.items()},
            "windows": {f"{k[0]}|{k[1]}": v for k, v in self.windows.items()},
        }, sort_keys=True))

    def work(self) -> dict[str, int]:
        return dict(self._w)


# ------------------------------------------------------------------ D
class ExplicitGraph(Representation):
    """Explicit relational graph: node objects with edges. Reachability walk with
    cycle guard; per-node marks/supersedes/support. Competent graph."""

    name = "D_explicit_graph"

    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self._w = {"applies": 0, "routes": 0}

    def _node(self, e: str) -> dict[str, Any]:
        return self.nodes.setdefault(e, {
            "deps": set(), "marked": {}, "superseded": {}, "formed": {}, "windows": {},
        })

    def apply(self, op: dict[str, Any]) -> None:
        self._w["applies"] += 1
        kind = op["op"]
        e = op.get("e")
        g = op.get("g", "")
        ctx = op.get("ctx", GLOBAL)
        if kind in ("FORM", "MARK", "RESOLVE", "SUPERSEDE") and e:
            n = self._node(e)
            if kind == "FORM":
                n["formed"][(g, ctx)] = True
                n["marked"].pop((g, ctx), None)
                n["superseded"].pop((g, ctx), None)
            elif kind == "MARK":
                n["marked"][(g, ctx)] = True
            elif kind == "RESOLVE":
                n["marked"].pop((g, ctx), None)
            elif kind == "SUPERSEDE":
                n["superseded"][(g, ctx)] = op.get("decision", "HOLD")
                n["marked"].pop((g, ctx), None)
        elif kind == "DEPEND":
            self._node(op["b"])["deps"].add(op["a"])   # b is a prerequisite of a
        elif kind == "RELIEVE":
            self._node(op["b"])["deps"].discard(op["a"])
        elif kind == "VALID" and e:
            self._node(e)["windows"].setdefault((g, ctx), []).append((op["from"], op["to"]))

    def _parents_of(self, e: str) -> list[str]:
        """Parents of e = nodes that list e among their deps."""
        return sorted(k for k, n in self.nodes.items() if e in n["deps"])

    def _proceeds(self, e: str, g: str, ctx: str, t: int | None, *, _seen: set[str]) -> str:
        if e in _seen:
            return "CYCLE_BLOCKED"
        _seen = _seen | {e}
        n = self.nodes.get(e)
        formed = False
        if n is not None:
            formed = bool(n["formed"].get((g, ctx)) or n["formed"].get((g, GLOBAL)))
        grounds = formed or bool(self._parents_of(e)) or self._transfer_possible(e, g, ctx)
        if not grounds:
            return "HOLD"
        if n is not None:
            if n["superseded"].get((g, ctx)) == "HOLD" or n["superseded"].get((g, GLOBAL)) == "HOLD":
                return "HOLD"
            if n["marked"].get((g, ctx)) or n["marked"].get((g, GLOBAL)):
                return "HOLD"
        else:
            # a never-seen surface is only reachable via parents/transfer which
            # are already grounds; there are no local blocks to read.
            pass
        for parent in self._parents_of(e):
            if self._proceeds(parent, g, ctx, t, _seen=_seen) != "PROCEED":
                return "HOLD"
        if n is not None:
            w = n["windows"].get((g, ctx)) or n["windows"].get((g, GLOBAL)) or []
            if t is not None and w and not any(a <= t <= b for a, b in w):
                return "HOLD"
        return "PROCEED"

    def _transfer_possible(self, e: str, g: str, ctx: str) -> bool:
        fam = family_of(g)
        return any(
            ej != e
            and (n["formed"].get((g, ctx)) or n["formed"].get((g, GLOBAL)))
            and not (n["superseded"].get((g, ctx)) == "HOLD" or n["superseded"].get((g, GLOBAL)) == "HOLD")
            and not (n["marked"].get((g, ctx)) or n["marked"].get((g, GLOBAL)))
            for ej, n in self.nodes.items()
        )

    def route(self, e: str, g: str, *, ctx: str = GLOBAL, t: int | None = None) -> dict[str, Any]:
        self._w["routes"] += 1
        res = self._proceeds(e, g, ctx, t, _seen=set())
        if res == "PROCEED":
            return {"decision": "PROCEED", "causes": []}
        # derive causes for HOLD deterministically
        causes = self._causes(e, g, ctx, t, _seen=set())
        return {"decision": "HOLD", "causes": sorted(set(causes))}

    def _causes(self, e: str, g: str, ctx: str, t: int | None, *, _seen: set[str]) -> list[str]:
        if e in _seen:
            return ["cyclic_constraint"]
        _seen = _seen | {e}
        n = self.nodes.get(e)
        causes: list[str] = []
        formed = n is not None and bool(n["formed"].get((g, ctx)) or n["formed"].get((g, GLOBAL)))
        if not formed and not self._parents_of(e) and not self._transfer_possible(e, g, ctx):
            causes.append("evidence_missing")
        if n is not None:
            if n["superseded"].get((g, ctx)) == "HOLD" or n["superseded"].get((g, GLOBAL)) == "HOLD":
                causes.append("declared_prohibition")
            if n["marked"].get((g, ctx)) or n["marked"].get((g, GLOBAL)):
                causes.append("active_contradiction")
        for parent in self._parents_of(e):
            if self._proceeds(parent, g, ctx, t, _seen=set()) != "PROCEED":
                causes.append(f"prerequisite_missing:{parent}")
        if n is not None:
            w = n["windows"].get((g, ctx)) or n["windows"].get((g, GLOBAL)) or []
            if t is not None and w and not any(a <= t <= b for a, b in w):
                causes.append("expired_outside_window")
        return causes

    def state_bytes(self) -> int:
        import json
        return len(json.dumps({
            k: {
                "deps": sorted(v["deps"]),
                "formed": {f"{kk[0]}|{kk[1]}": True for kk in v["formed"]},
                "marked": {f"{kk[0]}|{kk[1]}": True for kk in v["marked"]},
                "superseded": {f"{kk[0]}|{kk[1]}": d for kk, d in v["superseded"].items()},
                "windows": {f"{kk[0]}|{kk[1]}": wl for kk, wl in v["windows"].items()},
            } for k, v in self.nodes.items()
        }, sort_keys=True))

    def work(self) -> dict[str, int]:
        return dict(self._w)


# ------------------------------------------------------------------ E
class HistoricalFractalish(Representation):
    """The CURRENT Fractalish architecture driven through the SAME op stream.

    FORM -> safe_event ingest; MARK -> contradiction_event; RESOLVE -> resolve
    event + plasticity supersede; DEPEND -> keyed dependency record (direct
    prerequisite primitive, evaluated per query context at route time);
    queries -> core.route_decision(plasticity).
    This is the actual qualified implementation (FormationCore via adapters),
    not a stub. RELIEVE and temporal windows (VALID) still have no expressible
    primitive in the current architecture's routing: links are stored but not
    route-load-bearing, and there is no time dimension. Those ops are recorded
    as unmodeled so the honest failure points raise.
    """

    name = "E_historical_fractalish"

    def __init__(self) -> None:
        from baby_ai.adapters.operational_self import FormationCore
        from baby_ai.core.plasticity import PlasticityExecutor
        from baby_ai.hostile.events import contradiction_event, resolve_event, safe_event

        self._fac = FormationCore
        self._plast_cls = PlasticityExecutor
        self._safe, self._contra, self._resolve = safe_event, contradiction_event, resolve_event
        self.core = FormationCore(activation_id="ladder-e")
        self.plast = PlasticityExecutor(receipts=self.core.receipts, provenance=self.core.provenance)
        self._seen_group: dict[str, str] = {}
        self._scar_for: dict[str, str] = {}
        self._w = {"applies": 0, "routes": 0}
        self.unmodeled: list[str] = []

    def _last_scar(self, e: str) -> str | None:
        return self.core.scars[-1].scar_id if self.core.scars else None

    def apply(self, op: dict[str, Any]) -> None:
        self._w["applies"] += 1
        kind = op["op"]
        e = op.get("e")
        g = op.get("g", "")
        ctx = op.get("ctx", GLOBAL)
        if kind == "FORM":
            self.plast.assert_belief(belief_id=f"route:{e}", claim="safe", decision="RELEASE",
                                     strength=0.8, evidence=["formed"], reason="formed")
            ev = self._safe(self.core, e, g)
            ev.provenance.update({"context": ctx, "op_kind": kind})
            self.core.ingest(ev)
            self._seen_group.setdefault(e, g)
        elif kind == "MARK":
            ev = self._contra(self.core, e, g, decision="HOLD")
            ev.provenance.update({"context": ctx, "op_kind": kind})
            self.core.ingest(ev)
            scar = self._last_scar(e)
            if scar:
                self._scar_for[e] = scar
        elif kind == "RESOLVE":
            scar = self._scar_for.pop(e, None)
            if scar:
                self.plast.supersede(belief_id=f"route:{e}", new_claim="re-verified",
                                     new_decision="RELEASE_WITH_GUARD", evidence=["r"],
                                     reason="resolve", scar_id=scar)
            ev = self._resolve(self.core, e, g, decision="RELEASE_WITH_GUARD")
            ev.provenance.update({"context": ctx, "op_kind": kind})
            self.core.ingest(ev)
        elif kind == "SUPERSEDE":
            decision = op.get("decision", "HOLD")
            if decision == "HOLD":
                ev = self._contra(self.core, e, g, decision="HOLD")
                ev.provenance.update({"context": ctx, "op_kind": kind})
                self.core.ingest(ev)
                scar = self._last_scar(e)
                if scar:
                    self._scar_for[e] = scar
            else:
                ev = self._resolve(self.core, e, g, decision="RELEASE_WITH_GUARD")
                ev.provenance.update({"context": ctx, "op_kind": kind})
                self.core.ingest(ev)
        elif kind == "DEPEND":
            if type(self).dependency_gate:
                self.core.record_dependency(op["a"], op["b"])
            elif getattr(self, "unmodeled", None) is not None:
                self.unmodeled.append(kind)
        elif kind == "RELIEVE":
            if type(self).dependency_gate:
                self.core.relieve_dependency(op["a"], op["b"])
            elif getattr(self, "unmodeled", None) is not None:
                self.unmodeled.append(kind)
        elif kind == "VALID":
            if type(self).validity_gate:
                self.core.record_valid_window(op["e"], op.get("from", 0), op.get("to", 0),
                                              context=op.get("ctx", GLOBAL))
            elif getattr(self, "unmodeled", None) is not None:
                self.unmodeled.append(kind)

    def _belief_id(self, e: str) -> str:
        return f"route:{e}"

    # Applicability repair gate (v0.1): route_decision is given the query's
    # DECLARED SCOPE token (g); only retrieved records whose stored tag equals it
    # are admissible. Toggle OFF restores the historical (unscoped) behavior for
    # the adversarial ablation.
    applicability_gate: bool = True

    # Context repair gate (v0.1): route_decision is given the query's DECLARED
    # CONTEXT; memories ground a decision only in their own context (or the
    # global context) and scoped scars block only in their own context. Toggle
    # OFF restores the historical behavior for the ablation.
    context_gate: bool = True

    # Dependency repair gate (v0.1): DEPEND records a keyed prerequisite edge
    # (dependent surface -> ordered prerequisite surfaces). At route time a
    # dependent surface whose OWN state is clean (not superseded-HOLD, not
    # contradicted) proceeds only while every prerequisite satisfies the
    # formed-state gate in the QUERY's context; otherwise the cause is
    # prerequisite_missing:<surface> (never truncated).
    # Cycle/relieve repair (v0.2): prerequisite satisfaction is a RECURSIVE,
    # cycle-safe walk mirroring the oracle's _route_internal: a prerequisite
    # is satisfied only if ITS OWN formed-state gate passes and every one of
    # ITS dependencies is in turn satisfied, with a seen-set that flags a
    # revisit (CYCLE_BLOCKED) as unsatisfied. RELIEVE un-binds the current
    # edge (adapter ledger keeps history); DEPEND after RELIEVE re-binds.
    # Temporal validity repair (v0.3): VALID records per-entity windows; a
    # formation is admissible only while some applicable window contains the
    # query time (expired_outside_window otherwise). The window check runs in
    # both the surface query AND the recursive walk, mirroring
    # route_oracle/_route_internal. Toggle OFF restores the historical
    # behavior (DEPEND/RELIEVE dropped to unmodeled) for the ablation.
    dependency_gate: bool = True

    # Temporal validity gate (v0.3): VALID windows bound admissibility by
    # time. OFF restores the historical behavior (VALID unmodeled) for the
    # ablation.
    validity_gate: bool = True

    # Contradiction-authority gate (MARK/RESOLVE tranche, v0.4): RESOLVE clears
    # the CURRENT contradiction authority through the plasticity executor's
    # scar-status projection (superseded/resolved), the same projection the
    # surface already consumes in operational_self._blocking_scars_for. The raw
    # MARK scar stays in core.scars as historical record — it is not deleted.
    # The recursive dependency walk derives "currently contradicted" from the
    # SAME projection so surface routing and walk agree after a legitimate
    # RESOLVE. OFF restores the historical defect: the walk reads raw retained
    # scars, so a resolved MARK scar still blocks a dependent as
    # prerequisite_missing (pre-repair behavior). SUPERSEDE semantics are
    # untouched by this gate.
    contradiction_authority_gate: bool = True

    def _dep_grounded(self, e: str, g: str, ctx: str) -> bool:
        """Oracle _grounded mirror: e is grounded if it has a formed-state
        gate pass (own record or family transfer) OR it has dependencies
        (its prerequisites are its grounds). A member of a dependency cycle
        is grounded by the cycle's own edges, so the recursive walk reaches
        the revisit instead of reporting evidence_missing."""
        if self.core.dependencies.get(e):
            return True
        kwargs = {"plasticity": self.plast}
        if type(self).applicability_gate:
            kwargs["applicability"] = g
        if type(self).context_gate:
            kwargs["context"] = ctx
        r = self.core.route_decision(e, **kwargs)
        return str(r.get("decision", "HOLD")).startswith("RELEASE")

    def _dep_ok(self, e: str, g: str, ctx: str, _seen: frozenset[str], t: int | None = None) -> bool:
        """Recursive precondition walk mirroring the oracle's _route_internal.
        e satisfies iff: its OWN formed-state gate passes (declared/contradicted
        first, then grounding) and every dependency of e is itself satisfied.
        A revisit of the walk (e already in _seen) is CYCLE_BLOCKED -> False.
        Temporal validity (v0.3): an entity with a recorded VALID window must be
        in-window at the query time, else it fails the walk --- exactly how
        _route_internal applies _in_window."""
        if e in _seen:
            return False
        _seen = _seen | {e}
        if self._own_superseded_hold(e, g, ctx):
            return False
        if self._own_contradicted(e, g, ctx):
            return False
        if not self._dep_grounded(e, g, ctx):
            return False
        if type(self).validity_gate and not self._in_valid_window(e, ctx, t):
            return False
        for b in self.core.dependencies.get(e, []):
            if not self._dep_ok(b, g, ctx, _seen, t):
                return False
        return True

    def _prereq_ok(self, prereq: str, g: str, ctx: str, t: int | None = None) -> bool:
        """Y satisfies the prerequisite iff Y passes the recursive dependency
        walk (its own formed-state gate and its transitive dependencies) in
        the same query context X is routed in. Fresh seen-set per prereq,
        exactly as the oracle re-seeds _seen per direct prereq."""
        return self._dep_ok(prereq, g, ctx, frozenset(), t)

    def _own_superseded_hold(self, e: str, g: str, ctx: str) -> bool:
        """Own-state: e is superseded-HOLD in this context (a SUPERSEDE-origin
        scar over e's own grounded record, scoped to ctx or global)."""
        for scar in self.core.scars:
            if str(self.core.scar_kinds.get(scar.scar_id, "")).upper() != "SUPERSEDE":
                continue
            if self.core.scar_contexts.get(scar.scar_id, "*") not in (ctx, "*"):
                continue
            for mid in scar.memory_ids:
                mem = self.core.memories.get(mid)
                if not mem:
                    continue
                ss = self.core.mem_tuples.get(mid, {})
                if ss.get("subject") == e and (ss.get("group") in (None, "", g)):
                    return True
        return False

    def _own_contradicted(self, e: str, g: str, ctx: str) -> bool:
        """Own-state: e is CURRENTLY contradicted in this context.

        A non-SUPERSEDE-origin contradiction scar over e's own grounded
        record (scoped to ctx or global) is treated as ACTIVE only while its
        current authority survives. With the contradiction_authority_gate ON,
        that authority comes from the plasticity executor's scar status
        (superseded/resolved => no longer active), the SAME projection the
        surface consumes in _blocking_scars_for — so the recursive dependency
        walk and surface routing agree after a legitimate RESOLVE while the raw
        MARK scar remains in core.scars as history. With the gate OFF the
        historical behavior is restored: any retained MARK scar reads as
        active (the pre-repair walk defect). SUPERSEDE-origin scars are never
        consulted here (they belong to _own_superseded_hold)."""
        for scar in self.core.scars:
            if str(self.core.scar_kinds.get(scar.scar_id, "")).upper() == "SUPERSEDE":
                continue
            if self.core.scar_contexts.get(scar.scar_id, "*") not in (ctx, "*"):
                continue
            if type(self).contradiction_authority_gate:
                status = self.plast.get_scar_status(scar.scar_id)
                if status in ("superseded", "resolved"):
                    continue
            for mid in scar.memory_ids:
                mem = self.core.memories.get(mid)
                if not mem:
                    continue
                ss = self.core.mem_tuples.get(mid, {})
                if ss.get("subject") == e and (ss.get("group") in (None, "", g)):
                    return True
        return False

    def route(self, e: str, g: str, *, ctx: str = "", t: int | None = None) -> dict[str, Any]:
        self._w["routes"] += 1
        kwargs = {"plasticity": self.plast}
        if type(self).applicability_gate:
            kwargs["applicability"] = g
        if type(self).context_gate and ctx not in ("", None):
            kwargs["context"] = ctx
        r = self.core.route_decision(e, **kwargs)
        decision = r.get("decision", "HOLD")
        # Dependency gate (v0.1): mirrors the oracle's straight-line order -
        # X's own superseded/contradicted state is checked FIRST; only a clean
        # dependent is gated by its prerequisites. Each missing prerequisite is
        # cited by full surface, never truncated (the oracle cause strings
        # carry the full surface).
        if type(self).dependency_gate:
            deps = self.core.dependencies.get(e, [])
            if deps:
                ctx_q = ctx if ctx not in ("", None) else GLOBAL
                if not self._own_superseded_hold(e, g, ctx_q) and not self._own_contradicted(e, g, ctx_q):
                    missing = [p for p in deps if not self._prereq_ok(p, g, ctx_q, t)]
                    if missing:
                        return {
                            "decision": "HOLD",
                            "causes": ["prerequisite_missing:" + p for p in missing],
                        }
        # Surface the ladder's canonical cause tokens: a retrieval that found
        # nothing admissible (or records outside the declared scope) is, per the
        # oracle contract, "evidence_missing" for that query.
        cause: list[str] = []
        if not str(decision).startswith("RELEASE"):
            reason = str(r.get("reason", "no_memory"))
            if reason in ("no_applicable_evidence", "no_formed_memory", "identity_mismatch"):
                reason = "evidence_missing"
            if (r.get("causes") and type(self).context_gate):
                cause = [c[:40] for c in r["causes"]]
            else:
                cause = [reason[:40]]
        # Temporal validity gate (v0.3): a formation with a recorded VALID window
        # is admissible only while the query time sits inside some applicable
        # window. Out-of-window forces HOLD with the oracle cause, exactly as
        # route_oracle appends expired_outside_window after the grounded check.
        # When the query time is absent the window check is anchored to the
        # applied-op count, mirroring the oracle's t_real = o.time.
        if type(self).validity_gate and not self._in_valid_window(e, ctx, t):
            decision = "HOLD"
            if "expired_outside_window" not in cause:
                cause.append("expired_outside_window")
        return {
            "decision": "PROCEED" if str(decision).startswith("RELEASE") else "HOLD",
            "causes": cause,
        }

    def _in_valid_window(self, e: str, ctx: str, t: int | None) -> bool:
        """Mirror of the oracle's _in_window: e is PROCEED-able at time t iff
        every recorded per-context window for e is empty of t, or no window is
        recorded at all (gate inert). Per-context windows fall back to GLOBAL,
        exactly as the oracle consults o.valid[(e, ctx)] or o.valid[(e, GLOBAL)].
        When t is None the oracle anchors to o.time (applied-op count); E
        mirrors it with the adapter's applied-op counter."""
        ctx_q = ctx if ctx not in ("", None) else GLOBAL
        windows = self.core.valid_windows.get((e, ctx_q)) or self.core.valid_windows.get((e, GLOBAL)) or []
        if not windows:
            return True
        t_real = self._w["applies"] if t is None else t
        return any(a <= t_real <= b for a, b in windows)

    def state_bytes(self) -> int:
        import json
        from baby_ai.core.semantics import canonical_json
        return len(json.dumps(canonical_json(self.core.to_dict()), sort_keys=True, default=str))

    def work(self) -> dict[str, int]:
        return dict(self._w)


FACTORIES = {
    "A": ScalarCurrent,
    "B": KeyedVersioned,
    "C": MinimalAdmissibility,
    "D": ExplicitGraph,
    "E": HistoricalFractalish,
}


def build(arch: str) -> Representation:
    return FACTORIES[arch]()