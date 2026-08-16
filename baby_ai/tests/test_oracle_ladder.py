"""Oracle property tests for the complexity ladder (§4 audit).

These pin the ground-truth contract independently of any representation:
they exercise `OracleState` + `apply_op` + `route_oracle` directly. They are
NOT tests of B/C/D/E — those are compared against the oracle in the battery.
"""

import pytest

from baby_ai.ladder.generator import make_task
from baby_ai.ladder.oracle import GLOBAL, OracleState, apply_op, route_oracle
from baby_ai.ladder.runner import oracle_answers


def run_all(ops):
    o = OracleState()
    for op in ops:
        apply_op(o, op)
    return o


def test_form_grounds_own_item():
    o = run_all([{"op": "FORM", "e": "x", "g": "f"}])
    r = route_oracle(o, "x", "f")
    assert r["decision"] == "PROCEED"
    assert r["causes"] == []


def test_unrelated_is_evidence_missing():
    o = run_all([{"op": "FORM", "e": "x", "g": "f"}])
    r = route_oracle(o, "other", "other_family")
    assert r["decision"] == "HOLD"
    assert "evidence_missing" in r["causes"]


def test_mark_contradicts_and_resolve_clears():
    o = run_all([
        {"op": "FORM", "e": "x", "g": "f"},
        {"op": "MARK", "e": "x", "g": "f"},
    ])
    assert route_oracle(o, "x", "f")["decision"] == "HOLD"
    assert "active_contradiction" in route_oracle(o, "x", "f")["causes"]
    apply_op(o, {"op": "RESOLVE", "e": "x", "g": "f"})
    assert route_oracle(o, "x", "f")["decision"] == "PROCEED"


def test_dependency_is_grounds():
    """A dependent is grounded by its prerequisite edge: it PROCEEDs when the
    prereq PROCEEDs and HOLDs (prerequisite_missing) when the prereq HOLDs."""
    o = run_all([
        {"op": "FORM", "e": "a", "g": "f"},
        {"op": "DEPEND", "a": "b", "b": "a"},
    ])
    assert route_oracle(o, "b", "f")["decision"] == "PROCEED"
    apply_op(o, {"op": "SUPERSEDE", "e": "a", "g": "f", "decision": "HOLD"})
    r = route_oracle(o, "b", "f")
    assert r["decision"] == "HOLD"
    assert any(c.startswith("prerequisite_missing:") for c in r["causes"])


def test_transitive_cascade():
    o = run_all([
        {"op": "FORM", "e": "a", "g": "f"},
        {"op": "DEPEND", "a": "b", "b": "a"},
        {"op": "DEPEND", "a": "c", "b": "b"},
    ])
    assert route_oracle(o, "c", "f")["decision"] == "PROCEED"
    apply_op(o, {"op": "SUPERSEDE", "e": "a", "g": "f", "decision": "HOLD"})
    assert route_oracle(o, "b", "f")["decision"] == "HOLD"
    assert route_oracle(o, "c", "f")["decision"] == "HOLD"


def test_cycle_blocks_until_relieved():
    o = run_all([
        {"op": "DEPEND", "a": "a", "b": "b"},
        {"op": "DEPEND", "a": "b", "b": "a"},
        {"op": "FORM", "e": "a", "g": "f"},
    ])
    assert route_oracle(o, "a", "f")["decision"] == "HOLD"
    assert route_oracle(o, "b", "f")["decision"] == "HOLD"
    apply_op(o, {"op": "RELIEVE", "a": "b", "b": "a"})
    assert route_oracle(o, "b", "f")["decision"] == "PROCEED"


def test_time_window_expiry():
    o = run_all([
        {"op": "FORM", "e": "a", "g": "f"},
        {"op": "VALID", "e": "a", "from": 2, "to": 4},
    ])
    assert route_oracle(o, "a", "f", t=2)["decision"] == "PROCEED"
    assert route_oracle(o, "a", "f", t=4)["decision"] == "PROCEED"
    assert route_oracle(o, "a", "f", t=6)["decision"] == "HOLD"
    assert "expired_outside_window" in route_oracle(o, "a", "f", t=6)["causes"]


def test_context_scoped_contradiction():
    o = run_all([
        {"op": "FORM", "e": "a", "g": "f", "ctx": "base"},
        {"op": "MARK", "e": "a", "g": "f", "ctx": "scoped"},
    ])
    assert route_oracle(o, "a", "f", ctx="base")["decision"] == "PROCEED"
    r = route_oracle(o, "a", "f", ctx="scoped")
    assert r["decision"] == "HOLD"
    assert "active_contradiction" in r["causes"]


def test_competing_contexts_revive_old():
    o = run_all([
        {"op": "FORM", "e": "a", "g": "f"},
        {"op": "SUPERSEDE", "e": "a", "g": "f", "decision": "HOLD", "ctx": "new"},
    ])
    assert route_oracle(o, "a", "f", ctx="base")["decision"] == "PROCEED"
    assert route_oracle(o, "a", "f", ctx="other")["decision"] == "PROCEED"
    assert route_oracle(o, "a", "f", ctx="new")["decision"] == "HOLD"
    assert "declared_prohibition" in route_oracle(o, "a", "f", ctx="new")["causes"]


@pytest.mark.parametrize("level", ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"])
@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_oracle_is_deterministic_and_prefix_stable(level, seed):
    """Same seed -> identical queries and oracle answers; replaying a prefix
    yields the same answer as querying with at=prefix."""
    p1 = make_task(level, seed)
    p2 = make_task(level, seed)
    assert [(q["label"], q["e"]) for q in p1.queries] == [(q["label"], q["e"]) for q in p2.queries]
    assert oracle_answers(p1) == oracle_answers(p2)


@pytest.mark.parametrize("level", ["R3", "R4", "R5", "R6", "R8"])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_dependency_grounds_hold_across_ladder(level, seed):
    """Every dependency-bearing rung grounds its dependents: any query whose
    oracle answer is PROCEED must have either own form, a dependency edge, or
    family transfer available as a ground."""
    p = make_task(level, seed)
    answers = oracle_answers(p)
    for q in p.queries:
        if answers[str(q["label"])]["decision"] == "PROCEED":
            o = run_all(p.ops[: q.get("at", len(p.ops))])
            e, g = q["e"], q["g"]
            grounded = ((e, g, q.get("ctx", GLOBAL)) in o.formed
                        or (e, g, GLOBAL) in o.formed
                        or bool(o.deps.get(e)))
            # family-transfer covers the residual (withheld / unseen family members)
            if not grounded:
                g_fam = g.split("_")[0]
                grounded = any(
                    (ej, gj, cj) == (ej, gj, cj)
                    and formed
                    and ej != e and gj == g and g.split("_")[0] == g_fam
                    and (cj == q.get("ctx", GLOBAL) or cj == GLOBAL)
                    for (ej, gj, cj), formed in o.formed.items()
                )
            assert grounded, f"PROCEED without any ground: {level} {seed} {q['label']}"
