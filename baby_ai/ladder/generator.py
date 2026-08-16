"""Deterministic complexity-ladder task generator.

Every rung is a TaskProgram: an op list under one semantic (the Oracle) plus a
query set. The rungs increase ONE causal demand at a time, in the smallest
natural progression the mechanisms will support:

    R0  independent single proposition           FORM + transfer + unrelated
    R1  proposition + direct correction          FORM -> MARK -> RESOLVE
    R2  multiple independent propositions        scaled FORM family
    R3  direct dependency / one-hop supersess    DEPEND, one level
    R4  transitive supersession cascade          DEPEND chain, scaled depth
    R5  branching dependencies                   fan-out + fan-in conjunction
    R6  shared evidence -> many conclusions      single FORM gates many
    R7  ctx-scoped contradiction                 same DEPEND, different ctx
    R8  cyclic / mutually constraining deps      cycle blocks until RELIEVE
    R9  temporal validity                        VALID windows by time
    R10 competing contexts                       ctx-scoped supersede revives old

Naming and sizes are seeded by splitmix64 so any rung is reproducible across
hosts and runs. The Oracle (independent) defines ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from baby_ai.ladder.oracle import splitmix64


@dataclass
class TaskProgram:
    level: str
    name: str
    seed: int
    ops: list[dict[str, Any]]
    queries: list[dict[str, Any]]   # {"label", "e", "g", "at": int|None, "ctx": str}
    notes: list[str] = field(default_factory=list)


PREFIXES = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta")


def _mix(*parts: int) -> int:
    x = 0x9E3779B97F4A7C15
    for p in parts:
        x ^= p
        x = splitmix64(x)
    return x


def _item(ns: str, seed: int, i: int) -> str:
    """Deterministic surface item; family token is the word before '_'."""
    return f"flux_{ns}_{i}_{_mix(seed * 7919, i * 104729, sum(ord(c) for c in ns)) % 10**6}"


def _tag(root: str) -> str:
    return f"{root}_family"


def _unrelated(ns: str, seed: int) -> str:
    return _item(f"zz_{ns}", seed, 0)


def _tag_unrelated(ns: str) -> str:
    return _tag(f"zz_{ns}")


# ------------------------------------------------------------------- rungs
def make_R0(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    formed = _item(ns, seed, 0)
    tag = _tag(ns)
    ops = [{"op": "FORM", "e": formed, "g": tag}]
    queries = [
        {"label": "formed", "e": formed, "g": tag},
        {"label": "withheld", "e": _item(ns, seed, 1), "g": tag},
        {"label": "unrelated", "e": _unrelated(ns, seed), "g": _tag_unrelated(ns)},
    ]
    return TaskProgram("R0", "independent_single_proposition", seed, ops, queries,
                       ["single FORM; transfer + unrelated are the baseline trio"])


def make_R1(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    formed = _item(ns, seed, 0)
    tag = _tag(ns)
    ops = [
        {"op": "FORM", "e": formed, "g": tag},
        {"op": "MARK", "e": formed, "g": tag},
        {"op": "RESOLVE", "e": formed, "g": tag},
    ]
    queries = [
        {"label": "after_form", "e": formed, "g": tag, "at": 1},
        {"label": "after_mark", "e": formed, "g": tag, "at": 2},
        {"label": "after_resolve", "e": formed, "g": tag, "at": 3},
        {"label": "withheld", "e": _item(ns, seed, 1), "g": tag},
        {"label": "unrelated", "e": _unrelated(ns, seed), "g": _tag_unrelated(ns)},
    ]
    return TaskProgram("R1", "proposition_plus_direct_correction", seed, ops, queries,
                       ["MARK then RESOLVE exercises the correction cycle"])


def make_R2(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    tag = _tag(ns)
    n = 3 + (seed % 3)
    ops = [{"op": "FORM", "e": _item(ns, seed, i), "g": tag} for i in range(n)]
    queries = [{"label": "indep", "e": _item(ns, seed, i), "g": tag} for i in range(n)]
    queries += [
        {"label": "withheld", "e": _item(ns, seed, n), "g": tag},
        {"label": "unrelated", "e": _unrelated(ns, seed), "g": _tag_unrelated(ns)},
    ]
    return TaskProgram("R2", "multiple_independent_propositions", seed, ops, queries,
                       [f"{n} independent FORMs share one family token"])


def make_R3(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    tag = _tag(ns)
    a = _item(ns, seed, 0)
    b = _item(ns, seed, 1)
    ops = [
        {"op": "FORM", "e": a, "g": tag},
        {"op": "DEPEND", "a": b, "b": a},
        {"op": "SUPERSEDE", "e": a, "g": tag, "decision": "HOLD"},
    ]
    queries = [
        {"label": "child_before_supersede", "e": b, "g": tag, "at": 2},
        {"label": "parent_after_supersede", "e": a, "g": tag, "at": 3},
        {"label": "child_after_supersede", "e": b, "g": tag, "at": 3},
        {"label": "unrelated", "e": _unrelated(ns, seed), "g": _tag_unrelated(ns)},
    ]
    return TaskProgram("R3", "direct_dependency_one_hop_supersession", seed, ops, queries,
                       ["b depends on a; before supersede b PROCEED, after a->HOLD b HOLD"])


def make_R4(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    tag = _tag(ns)
    depth = 2 + (seed % 4)
    items = [_item(ns, seed, i) for i in range(depth + 1)]
    ops = [{"op": "FORM", "e": items[0], "g": tag}]
    for i in range(1, depth + 1):
        ops.append({"op": "DEPEND", "a": items[i], "b": items[i - 1]})
    pre_at = 1 + depth
    post_at = pre_at + 1
    ops.append({"op": "SUPERSEDE", "e": items[0], "g": tag, "decision": "HOLD"})
    queries = [{"label": f"chain{i}_pre", "e": items[i], "g": tag, "at": pre_at} for i in range(depth + 1)]
    queries += [{"label": f"chain{i}_post", "e": items[i], "g": tag, "at": post_at} for i in range(depth + 1)]
    queries.append({"label": "unrelated", "e": _unrelated(ns, seed), "g": _tag_unrelated(ns)})
    return TaskProgram("R4", "transitive_supersession_cascade", seed, ops, queries,
                       [f"chain depth {depth}: pre-cascade all dependents PROCEED; root->HOLD cascades to all"])


def make_R5(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    tag = _tag(ns)
    parent = _item(ns, seed, 0)
    kids = [_item(ns, seed, 1 + i) for i in range(2 + (seed % 3))]
    operators = [{"op": "FORM", "e": parent, "g": tag}]
    for k in kids:
        operators.append({"op": "DEPEND", "a": k, "b": parent})   # fan-out: many kids on parent
    conj = _item(ns, seed, 30)
    p2 = _item(ns, seed, 31)
    operators.append({"op": "FORM", "e": p2, "g": tag})
    operators.append({"op": "DEPEND", "a": conj, "b": parent})
    operators.append({"op": "DEPEND", "a": conj, "b": p2})        # fan-in: conj needs both
    ops = operators
    queries = [{"label": f"kid{i}", "e": k, "g": tag} for i, k in enumerate(kids)]
    queries += [
        {"label": "conj", "e": conj, "g": tag},
        {"label": "unrelated", "e": _unrelated(ns, seed), "g": _tag_unrelated(ns)},
    ]
    return TaskProgram("R5", "branching_dependencies", seed, ops, queries,
                       [f"{len(kids)} fan-out kids + one fan-in conjunction (needs both parents)"])


def make_R6(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    tag = _tag(ns)
    shared = _item(ns, seed, 0)
    conclusions = [_item(ns, seed, 1 + i) for i in range(2 + (seed % 3))]
    ops = [{"op": "FORM", "e": shared, "g": tag}]
    for c in conclusions:
        ops.append({"op": "DEPEND", "a": c, "b": shared})
    queries = [{"label": f"concl{i}", "e": c, "g": tag} for i, c in enumerate(conclusions)]
    queries += [
        {"label": "shared", "e": shared, "g": tag},
        {"label": "unrelated", "e": _unrelated(ns, seed), "g": _tag_unrelated(ns)},
    ]
    return TaskProgram("R6", "shared_evidence_many_conclusions", seed, ops, queries,
                       [f"single FORM gates {len(conclusions)} conclusions via shared evidence"])


def make_R7(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    tag = _tag(ns)
    a = _item(ns, seed, 0)
    b = _item(ns, seed, 1)
    ctx1 = "ctx_scoped"
    ops = [
        {"op": "FORM", "e": a, "g": tag, "ctx": "ctx_base"},
        {"op": "DEPEND", "a": b, "b": a},
        {"op": "MARK", "e": a, "g": tag, "ctx": ctx1},
    ]
    queries = [
        {"label": "a_other_ctx", "e": a, "g": tag, "ctx": "ctx_base"},
        {"label": "a_scoped_ctx", "e": a, "g": tag, "ctx": ctx1},
        {"label": "b_scoped_ctx", "e": b, "g": tag, "ctx": ctx1},
        {"label": "b_other_ctx", "e": b, "g": tag, "ctx": "ctx_base"},
    ]
    return TaskProgram("R7", "context_scoped_contradiction", seed, ops, queries,
                       ["contradiction is scoped to ctx1; other contexts unaffected"])


def make_R8(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    tag = _tag(ns)
    a = _item(ns, seed, 0)
    b = _item(ns, seed, 1)
    ops = [
        {"op": "DEPEND", "a": a, "b": b},
        {"op": "DEPEND", "a": b, "b": a},
        {"op": "FORM", "e": a, "g": tag},
    ]
    queries = [
        {"label": "a_in_cycle", "e": a, "g": tag, "at": 3},
        {"label": "b_in_cycle", "e": b, "g": tag, "at": 3},
    ]
    ops += [{"op": "SYNC"}]
    ops += [{"op": "RELIEVE", "a": b, "b": a}]
    queries += [
        {"label": "b_after_relieve", "e": b, "g": tag},
        {"label": "unrelated", "e": _unrelated(ns, seed), "g": _tag_unrelated(ns)},
    ]
    return TaskProgram("R8", "cyclic_mutually_constraining", seed, ops, queries,
                       ["a<->b cycle; both blocked until the edge is relieved"])


def make_R9(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    tag = _tag(ns)
    a = _item(ns, seed, 0)
    ops = [
        {"op": "FORM", "e": a, "g": tag},
        {"op": "VALID", "e": a, "g": tag, "from": 2, "to": 4},
        {"op": "FORM", "e": _item(ns, seed, 5), "g": tag},
    ]
    queries = [
        {"label": "a_at_t2", "e": a, "g": tag, "t": 2},
        {"label": "a_at_t3", "e": a, "g": tag, "t": 3},
        {"label": "a_at_t6", "e": a, "g": tag, "t": 6},
        {"label": "unrelated", "e": _unrelated(ns, seed), "g": _tag_unrelated(ns), "t": 3},
    ]
    return TaskProgram("R9", "temporal_validity", seed, ops, queries,
                       ["a valid only in window [2..4]; queries at various times"])


def make_R10(seed: int) -> TaskProgram:
    ns = PREFIXES[seed % len(PREFIXES)]
    tag = _tag(ns)
    a = _item(ns, seed, 0)
    ops = [
        {"op": "FORM", "e": a, "g": tag},                       # global old state: valid
        {"op": "SUPERSEDE", "e": a, "g": tag, "decision": "HOLD", "ctx": "ctx_new"},
    ]
    queries = [
        {"label": "a_base_ctx", "e": a, "g": tag, "ctx": "ctx_base"},
        {"label": "a_new_ctx", "e": a, "g": tag, "ctx": "ctx_new"},
        {"label": "a_other_ctx", "e": a, "g": tag, "ctx": "ctx_other"},
    ]
    return TaskProgram("R10", "competing_contexts_revive_old", seed, ops, queries,
                       ["global old state stays valid in base/other ctx; superseded only in ctx_new"])


MAKERS = {
    "R0": make_R0, "R1": make_R1, "R2": make_R2, "R3": make_R3, "R4": make_R4,
    "R5": make_R5, "R6": make_R6, "R7": make_R7, "R8": make_R8, "R9": make_R9,
    "R10": make_R10,
}


def make_task(level: str, seed: int) -> TaskProgram:
    return MAKERS[level](seed)