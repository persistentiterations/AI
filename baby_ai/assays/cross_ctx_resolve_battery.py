"""Cross-context RESOLVE battery (pre-implementation evidence).

Each case runs the same op stream through OracleState (apply_op + route_oracle)
and HistoricalFractalish E (replay_rep). Reports decision for each queried
context. Contexts used: 'A', 'B', and global ('*').
"""
import json, sys, os
from baby_ai.ladder.runner import replay_rep
from baby_ai.ladder.oracle import OracleState, apply_op, route_oracle
import baby_ai.ladder.representations as M

F = "f"
G = "*"


def _ops(seq):
    ops = []
    for kind, e, m1, m2, res, dep_pairs, val in seq:
        pass
    return ops


def run(ops, queries):
    o = OracleState()
    for op in ops:
        apply_op(o, op)
    r = replay_rep("E", ops, None)
    g = ops[0]["g"]
    row = {}
    for q in queries:
        row[q] = {
            "oracle": route_oracle(o, ops[0]["e"], g, ctx=q, t=None),
            "E": r.route(ops[0]["e"], g, ctx=q, t=None),
        }
    return row


def form(e="a", g=F):
    return {"op": "FORM", "e": e, "g": g}


def mark(e="a", g=F, ctx=G):
    return {"op": "MARK", "e": e, "g": g, "ctx": ctx}


def resolve(e="a", g=F, ctx=G):
    return {"op": "RESOLVE", "e": e, "g": g, "ctx": ctx}


def depend(a, b):
    return {"op": "DEPEND", "a": a, "b": b}


def valid(e, lo, hi, ctx=G):
    return {"op": "VALID", "e": e, "g": F, "from": lo, "to": hi, "ctx": ctx}


CASES = {}

# C1 MARK in A, RESOLVE in A -> A PROCEED (both agree)
CASES["C1_mark_A_resolve_A"] = {"ops": [form(), mark(ctx="A"), resolve(ctx="A")], "queries": ["A", "*"]}

# C2 MARK in A, RESOLVE in B -> A stays HOLD (oracle); E currently PROCEED (defect)
CASES["C2_mark_A_resolve_B"] = {"ops": [form(), mark(ctx="A"), resolve(ctx="B")], "queries": ["A", "B", "*"]}

# C3 MARK A, MARK B, RESOLVE A -> A cleared, B stays HOLD
CASES["C3_mark_AB_resolve_A"] = {"ops": [form(), mark(ctx="A"), mark(ctx="B"), resolve(ctx="A")], "queries": ["A", "B"]}

# C4 MARK A, MARK B, RESOLVE A, query BOTH (same as C3, kept per req)
CASES["C4_mark_AB_resolve_A_query_both"] = {"ops": [form(), mark(ctx="A"), mark(ctx="B"), resolve(ctx="A")], "queries": ["A", "B"]}

# C5 transitive dependencies evaluated in each context: c depends on a; a marked+resolved(A), a marked (B)
CASES["C5_transitive_dep_per_ctx"] = {
    "ops": [form(e="a"), form(e="c"), mark(e="a", ctx="A"), resolve(e="a", ctx="A"),
            mark(e="a", ctx="B"), depend("c", "a")],
    "queries": ["A", "B", "*"],
    "root": "c",
}

# C6 validity-window interaction per context: VALID a window t2..t4 in A only; marked+resolved in A
CASES["C6_validity_per_ctx"] = {
    "ops": [form(), valid("a", 2, 4, ctx="A"), mark(ctx="A"), resolve(ctx="A")],
    "queries": ["A", "B", "*"],
    "t": 6,
}

# C7 cycles spanning otherwise valid context-scoped prereqs: a<->b; a marked A resolved A; b marked B
CASES["C7_cycle_scoped"] = {
    "ops": [form(e="a"), form(e="b"), mark(e="a", ctx="A"), resolve(e="a", ctx="A"),
            mark(e="b", ctx="B"), depend("a", "b"), depend("b", "a")],
    "queries": ["A", "B", "*"],
    "root": "a",
}

# C8 context A resolved while B remains contradicted (mark only B after resolve A)
CASES["C8_A_resolved_B_remains"] = {
    "ops": [form(), mark(ctx="A"), resolve(ctx="A"), mark(ctx="B")],
    "queries": ["A", "B"],
}


def main():
    M.HistoricalFractalish.contradiction_authority_gate = True
    out = {}
    for name, spec in CASES.items():
        ops = spec["ops"]
        queries = spec["queries"]
        qroot = spec.get("root", ops[0]["e"])
        o = OracleState()
        for op in ops:
            apply_op(o, op)
        r = replay_rep("E", ops, None)
        row = {}
        g = "f"
        for q in queries:
            t = spec.get("t")
            row[q] = {
                "oracle": route_oracle(o, qroot, g, ctx=q, t=t),
                "E": r.route(qroot, g, ctx=q, t=t),
            }
        out[name] = row
        # gate OFF probe for the defect independence
        M.HistoricalFractalish.contradiction_authority_gate = False
        r2 = replay_rep("E", ops, None)
        off = {}
        for q in queries:
            t = spec.get("t")
            off[q] = r2.route(qroot, g, ctx=q, t=t)
        M.HistoricalFractalish.contradiction_authority_gate = True
        out[name + "__gateOFF"] = off
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()