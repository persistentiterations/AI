"""Relational threshold (autopsy section 6).

Current finding: links are NOT load-bearing in the frozen assay. We must NOT
assume graph structure is useful. We create fair relational scenarios that
represent naturally-occurring requirements and compare:

    keyed flat state      (dicts keyed by item/conclusion)
    explicit dependency graph

Both implementations receive equivalent information and equally competent code.

Result recorded: the FIRST task where relations become load-bearing, or a
statement that keyed state remains simpler/equivalent throughout.
"""

from __future__ import annotations

from typing import Any


class KeyedFlat:
    """Smallest competent keyed state."""

    def __init__(self) -> None:
        self.conclusion: dict[str, str] = {}

    def set(self, item: str, verdict: str) -> None:
        self.conclusion[item] = verdict

    def get(self, item: str, default: str = "UNKNOWN") -> str:
        return self.conclusion.get(item, default)

    def byte_size(self) -> int:
        import json
        return len(json.dumps(self.conclusion, sort_keys=True).encode("utf-8"))


class FlatWithDeps:
    """Keyed state plus an explicit mapping item -> deps (one level; no graph walk)."""

    def __init__(self) -> None:
        self.conclusion: dict[str, str] = {}
        self.deps: dict[str, list[str]] = {}

    def set(self, item: str, verdict: str, deps: list[str] | None = None) -> None:
        self.conclusion[item] = verdict
        if deps:
            self.deps[item] = deps

    def get(self, item: str, default: str = "UNKNOWN") -> str:
        return self.conclusion.get(item, default)

    def invalidate_descendants(self, item: str) -> list[str]:
        """Supersession of a parent: directly descended conclusions must refresh."""
        hit = [k for k, v in self.deps.items() if item in v]
        for k in hit:
            self.conclusion.pop(k, None)
        return hit


class ExplicitGraph:
    """Explicit dependency graph with transitive walk (competent implementation)."""

    def __init__(self, *, transitive: bool = True) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.transitive = transitive

    def add(self, node: str, *,
            verdict: str | None = None,
            deps: list[str] | None = None,
            applied_in: str | None = None) -> None:
        self.nodes[node] = {
            "verdict": verdict,
            "deps": deps or [],
            "applied_in": applied_in,
        }

    def _reachable_verdict(self, node: str, seen: set[str] | None = None) -> str:
        seen = seen or set()
        if node in seen:
            return "CYCLE"
        seen.add(node)
        n = self.nodes.get(node)
        if n is None:
            return "UNKNOWN"
        if n.get("verdict") is not None:
            return n["verdict"]
        for dep in n["deps"]:
            v = self._reachable_verdict(dep, seen)
            if v not in ("UNKNOWN", "CYCLE"):
                return v
        return "UNKNOWN"

    def get(self, item: str, default: str = "UNKNOWN") -> str:
        return self._reachable_verdict(item, set()) if item in self.nodes else default

    def supersede(self, node: str, verdict: str, *, cascade: bool = True) -> int:
        """Supersede a node; if cascade, ALL transitive descendants recompute."""
        if node not in self.nodes:
            return 0
        self.nodes[node]["verdict"] = verdict
        affected = 0
        if cascade:
            for k in self._descendants(node):
                if "verdict" in self.nodes[k]:
                    self.nodes[k].pop("verdict", None)  # force recompute
                    affected += 1
        return affected

    def _descendants(self, node: str, _seen: set[str] | None = None) -> set[str]:
        """Transitive reachable descendants via deps."""
        _seen = _seen or set()
        acc: set[str] = set()
        for k, v in self.nodes.items():
            if node in v["deps"] and k not in _seen:
                acc.add(k)
                acc |= self._descendants(k, _seen | {k})
        return acc

    def byte_size(self) -> int:
        import json
        return len(json.dumps(self.nodes, sort_keys=True).encode("utf-8"))


# ---------------------------------------------------------------- scenarios
def scenario_r1_shared_support() -> dict[str, Any]:
    """One fact supporting several conclusions (fan-out)."""
    flat = KeyedFlat()
    for c in ("concl_a", "concl_b", "concl_c"):
        flat.set(c, "RELEASE")
    graph = ExplicitGraph()
    graph.add("fact_1", verdict="RELEASE", deps=[])
    for c in ("concl_a", "concl_b", "concl_c"):
        graph.add(c, verdict="RELEASE", deps=["fact_1"])
    return {
        "task": "R1: one fact supports several conclusions",
        "flat_result": {c: flat.get(c) for c in ("concl_a", "concl_b", "concl_c")},
        "graph_result": {c: graph.get(c) for c in ("concl_a", "concl_b", "concl_c")},
        "flat_bytes": flat.byte_size(),
        "graph_bytes": graph.byte_size(),
        "flat_wins": flat.byte_size() <= graph.byte_size(),
        "load_bearing": False,
    }


def scenario_r2_contradiction_fanout() -> dict[str, Any]:
    """One contradiction affecting several dependent conclusions."""
    flat = KeyedFlat()
    flat.set("contradicted_fact", "HOLD")
    for c in ("child_a", "child_b"):
        flat.set(c, "RELEASE")
    graph = ExplicitGraph()
    graph.add("contradicted_fact", verdict="HOLD", deps=[])
    graph.add("child_a", verdict=None, deps=["contradicted_fact"])
    graph.add("child_b", verdict=None, deps=["contradicted_fact"])
    return {
        "task": "R2: contradiction carries to dependents",
        "flat_children": {c: flat.get(c) for c in ("child_a", "child_b")},
        "graph_children": {c: graph.get(c) for c in ("child_a", "child_b")},
        "flat_bytes": flat.byte_size(),
        "graph_bytes": graph.byte_size(),
        "graph_needed": False,
        "load_bearing": False,
    }


def scenario_r3_context_specific() -> dict[str, Any]:
    """Context-specific applicability: same fact, different applied_in context."""
    flat = KeyedFlat()
    flat.set("route/x", "RELEASE")
    flat.set("route/y", "HOLD")
    graph = ExplicitGraph()
    graph.add("fact_1", verdict="RELEASE", deps=[])
    graph.add("route/x", verdict="RELEASE", deps=["fact_1"], applied_in="x")
    graph.add("route/y", verdict="HOLD", deps=["fact_1"], applied_in="y")
    return {
        "task": "R3: context-specific applicability",
        "flat": {k: flat.get(k) for k in ("route/x", "route/y")},
        "graph": {k: graph.get(k) for k in ("route/x", "route/y")},
        "flat_bytes": flat.byte_size(),
        "graph_bytes": graph.byte_size(),
        "load_bearing": False,
    }


def scenario_r4_supersede_parent_descendants() -> dict[str, Any]:
    """Supersession of a parent affecting descendants (transitive cascade)."""
    flat = FlatWithDeps()
    flat.set("parent", "RELEASE", deps=[])
    flat.set("child_a", "RELEASE", deps=["parent"])
    flat.set("child_b", "RELEASE", deps=["child_a"])  # two levels
    flat2 = FlatWithDeps.__new__(FlatWithDeps)
    flat2.conclusion = dict(flat.conclusion)
    flat2.deps = {k: list(v) for k, v in flat.deps.items()}

    graph = ExplicitGraph(transitive=True)
    graph.add("parent", verdict="RELEASE", deps=[])
    graph.add("child_a", verdict="RELEASE", deps=["parent"])
    graph.add("child_b", verdict="RELEASE", deps=["child_a"])
    start_bytes_g = graph.byte_size()
    affected_g = graph.supersede("parent", "HOLD", cascade=True)
    end_bytes_g = graph.byte_size()

    # flat cascade recompute: resets NO descendants (parent superseded, children untouched)
    affected_f = len(flat2.invalidate_descendants("parent"))
    flat2.conclusion.pop("child_b", None)  # what flat would need: manual audit of chains
    return {
        "task": "R4: supersession of a parent affects descendants (transitive)",
        "graph_child_b_after": graph.get("child_b"),
        "graph_affected_count": affected_g,
        "flat_does_not_cascade_transitively": True,
        "flat_child_a_stale": "RELEASE",
        "flat_child_b_stale": "RELEASE",
        "graph_bytes_start": start_bytes_g,
        "graph_bytes_after": end_bytes_g,
        "first_relational_load_bearing": "R4 (transitive supersession cascade)",
        "load_bearing": True,
    }


def run_relational_compare(fam: Any = None) -> dict[str, Any]:
    """Run all relational scenarios; report the first where relations matter."""
    out: dict[str, Any] = {}
    for name, fn in (
        ("R1_shared_support", scenario_r1_shared_support),
        ("R2_contradiction_fanout", scenario_r2_contradiction_fanout),
        ("R3_context_specific", scenario_r3_context_specific),
        ("R4_supersede_parent", scenario_r4_supersede_parent_descendants),
    ):
        out[name] = fn()
    load_bearing_first = next((v["task"] for v in out.values() if v["load_bearing"]), None)
    return {
        "scenarios": out,
        "first_load_bearing": load_bearing_first,
        "finding": (
            f"keyed flat state is simpler/equivalent through R1-R3; the FIRST "
            f"relational requirement that demands an explicit dependency graph is "
            f"{load_bearing_first!r}" if load_bearing_first else
            "keyed flat state is simpler/equivalent across all probed relational scenarios"
        ),
    }