"""Runner + metrics for the complexity ladder.

For each task we evaluate the Oracle and every representation at identical
query points (honoring `at` prefixes), then record per-query correctness,
cause fidelity, state bytes and op counts, and the relational complexity
measures (§7) for the task itself.
"""

from __future__ import annotations

import json
import time
from typing import Any

from baby_ai.ladder.generator import TaskProgram
from baby_ai.ladder.oracle import GLOBAL, OracleState, apply_op, route_oracle
from baby_ai.ladder.representations import FACTORIES, build


def oracle_prefix(ops: list[dict[str, Any]], at: int | None) -> OracleState:
    o = OracleState()
    stop = len(ops) if at is None else min(at, len(ops))
    for op in ops[:stop]:
        apply_op(o, op)
    return o


def oracle_answers(program: TaskProgram) -> dict[str, dict[str, Any]]:
    """Ground-truth answers for every query label."""
    out: dict[str, dict[str, Any]] = {}
    for q in program.queries:
        o = oracle_prefix(program.ops, q.get("at"))
        r = route_oracle(o, q["e"], q["g"], ctx=q.get("ctx", GLOBAL), t=q.get("t"))
        qname = str(q["label"])
        if qname not in out:
            out[qname] = {"decision": r["decision"], "causes": r["causes"],
                          "ctx": q.get("ctx", GLOBAL), "t": q.get("t")}
    return out


def replay_rep(rep, ops: list[dict[str, Any]], at: int | None):
    """Fresh representation replaying ops up to at (honors prefix queries)."""
    r = build(rep)
    stop = len(ops) if at is None else min(at, len(ops))
    for op in ops[:stop]:
        r.apply(op)
    return r


def run_representation(rep: str, program: TaskProgram) -> dict[str, Any]:
    """Run one representation on the full program; report per-query correctness
    vs oracle, plus aggregate."""
    oracle = oracle_answers(program)
    rows: list[dict[str, Any]] = []
    correct = 0
    total = len(program.queries)
    final_rep = build(rep)
    for op in program.ops:
        final_rep.apply(op)
    for q in program.queries:
        r = replay_rep(rep, program.ops, q.get("at"))
        qname = str(q["label"])
        got = r.route(q["e"], q["g"], ctx=q.get("ctx", GLOBAL), t=q.get("t"))
        exp = oracle[qname]
        match = got["decision"] == exp["decision"]
        cause_match = sorted(got.get("causes", [])) == sorted(exp["causes"])
        correct += int(match)
        rows.append({
            "label": qname,
            "e": q["e"],
            "ctx": q.get("ctx", GLOBAL),
            "t": q.get("t"),
            "expected": exp["decision"],
            "expected_causes": exp["causes"],
            "got": got["decision"],
            "got_causes": got.get("causes", []),
            "decision_ok": match,
            "causes_ok": cause_match,
            "state_bytes_after_prefix": r.state_bytes(),
        })
    w = final_rep.work()
    agg = {
        "representation": rep,
        "correct": correct,
        "total": total,
        "accuracy": round(correct / total, 4) if total else 1.0,
        "all_correct": correct == total,
        "cause_fidelity": round(
            sum(1 for row in rows if row["causes_ok"]) / total, 4) if total else 1.0,
        "final_state_bytes": final_rep.state_bytes(),
        "applies": w["applies"],
        "routes": w["routes"],
        "rows": rows,
        "unmodeled_ops": getattr(final_rep, "unmodeled", None),
    }
    return agg


def relational_complexity(program: TaskProgram) -> dict[str, Any]:
    """§7 measures: entities, consequential relations, depth, branching,
    contradiction count, correction depth, contextual states, reconstruction."""
    o = OracleState()
    for op in program.ops:
        apply_op(o, op)
    entities = sorted({op.get("e") for op in program.ops if op.get("e")} |
                      {op.get("a") for op in program.ops if op.get("a")} |
                      {op.get("b") for op in program.ops if op.get("b")})
    deps = o.deps
    # dependency depth = longest path in deps graph
    depth = 0
    memo: dict[str, int] = {}

    def dep_depth(e: str, _seen: set[str] | None = None) -> int:
        _seen = _seen or set()
        if e in _seen:
            return 0
        _seen = _seen | {e}
        parents = sorted(k for k, kids in deps.items() if e in kids)
        if not parents:
            return 0
        return 1 + max(dep_depth(p, _seen) for p in parents)

    for e in entities:
        depth = max(depth, dep_depth(e))
    branching = max((len(kids) for kids in deps.values()), default=0)
    contradictions = sum(1 for op in program.ops if op["op"] == "MARK")
    corrections = sum(1 for op in program.ops if op["op"] == "RESOLVE")
    contexts = sorted({op.get("ctx", GLOBAL) for op in program.ops})
    supersedes = sum(1 for op in program.ops if op["op"] == "SUPERSEDE")
    consequential_relations = sum(1 for kids in deps.values() for _ in kids)
    return {
        "level": program.level,
        "entities": len(entities),
        "consequential_relations": consequential_relations,
        "dependency_depth": depth,
        "branching_factor": branching,
        "contradiction_count": contradictions,
        "correction_depth": corrections,
        "contextual_states": len(contexts),
        "supersede_count": supersedes,
        "op_count": len(program.ops),
        "entities_list": entities,
    }


def run_level_all(levels: list[str], seeds: list[int], reps: list[str]) -> dict[str, Any]:
    from baby_ai.ladder.generator import make_task

    out: dict[str, Any] = {}
    for level in levels:
        for seed in seeds:
            prog = make_task(level, seed)
            key = f"{level}:{seed}"
            res: dict[str, Any] = {"task": {"level": level, "seed": seed, "name": prog.name,
                                            "notes": prog.notes},
                                   "complexity": relational_complexity(prog),
                                   "representations": {}}
            for rep in reps:
                t0 = time.perf_counter()
                agg = run_representation(rep, prog)
                agg["ms"] = round((time.perf_counter() - t0) * 1000, 4)
                res["representations"][rep] = agg
            out[key] = res
    return out