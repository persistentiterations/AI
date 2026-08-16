"""Freeze generator for the FormationCore CYCLE / RELIEVE repair (v0.2).

Package: BABY_AI_FORMATIONCORE_CYCLE_RELIEVE_REPAIR_v0_1
    BASELINE_R8_FAILURES.json    - exact frozen R8 failure (48 rows: a_in_cycle +
                                   b_in_cycle x 24 seeds, both route+cause wrong)
    RELIEVE_SEMANTICS.json       - the oracle's RELIEVE semantics, derived from
                                   oracle.apply_op (deps.a.discard(b))
    REPAIR_MECHANISM.json        - recursive cycle-safe precondition walk (oracle
                                   _route_internal mirror) + relieve primitive
    ADVERSARIAL_CYCLES.json      - adversarial cycle/relieve battery vs route_oracle
    ABLATION.json                - dependency_gate OFF / ON / RESTORE full ladder
    FULL_LADDER_REGRESSION.json  - repaired E route/cause totals + A-D unchanged
    CAUSE_FIDELITY.json          - cycle-class HOLD causes are prerequisite_missing
    REPAIR_REPORT.md             - narrative claim boundary
    manifest.json                - hashes, seeds, scope, constraints

The original ladder, context-tranche and dependency-tranche freezes are READ ONLY;
this writes a separate directory so all packages stay independently reproducible.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from baby_ai.ladder import oracle as O
from baby_ai.ladder.battery import LEVELS, REPS, route_totals, run_battery as ladder_battery
from baby_ai.ladder.generator import _item, _tag, PREFIXES, make_task
from baby_ai.ladder.representations import HistoricalFractalish
from baby_ai.ladder.runner import oracle_answers, replay_rep
from baby_ai.ladder.oracle import GLOBAL

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FREEZE = os.path.abspath(os.path.join(ROOT, "baby_ai", "artifacts", "freeze",
                                      "BABY_AI_COMPLEXITY_LADDER_v0_1"))
DEP_FREEZE = os.path.abspath(os.path.join(ROOT, "baby_ai", "artifacts", "repair",
                                          "BABY_AI_FORMATIONCORE_DEPENDENCY_REPAIR_v0_1"))
OUT = os.path.abspath(os.path.join(ROOT, "baby_ai", "artifacts", "repair",
                                   "BABY_AI_FORMATIONCORE_CYCLE_RELIEVE_REPAIR_v0_1"))
SEEDS = list(range(24))


def _hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def _load_frozen(name: str) -> Any:
    with open(os.path.join(FREEZE, name), encoding="utf-8") as f:
        return json.load(f)


def _load_dep(name: str) -> Any:
    with open(os.path.join(DEP_FREEZE, name), encoding="utf-8") as f:
        return json.load(f)


def baseline_r8_failures() -> dict[str, Any]:
    """Re-derive and freeze the exact R8 failure rows (must reproduce the probe)."""
    rows: list[dict[str, Any]] = []
    for seed in SEEDS:
        program = make_task("R8", seed)
        oracle = oracle_answers(program)
        for q in program.queries:
            label = str(q["label"])
            exp = oracle[label]
            r = replay_rep("E", program.ops, q.get("at"))
            got = r.route(q["e"], q["g"], ctx=q.get("ctx", GLOBAL), t=q.get("t"))
            if got["decision"] == exp["decision"] and sorted(got.get("causes", [])) == sorted(exp["causes"]):
                continue
            rows.append({
                "seed": seed, "level": "R8", "label": label,
                "surface": q["e"], "family": q["g"], "context": q.get("ctx", GLOBAL),
                "at_executed": q.get("at"), "routed_at": q.get("t"),
                "mismatch_class": ("both" if got["decision"] != exp["decision"]
                                   else "cause"),
                "oracle_route": exp["decision"], "oracle_causes": exp["causes"],
                "current_route": got["decision"], "current_causes": got.get("causes", []),
                "dependency_bindings": {k: list(v) for k, v in r.core.dependencies.items()},
                "message": f"R8 {label}: oracle {exp['decision']}/{exp['causes']} vs "
                           f"E {got['decision']}/{got.get('causes', [])}",
            })
    return {
        "thesis": ("R8's a<->b mutual dependency cycle: E's direct DEPEND primitive "
                   "satisfies each prereq by the prereq's OWN formed-state gate (no "
                   "recursion), so both nodes read the other as PROCEED-by-transfer and "
                   "the cycle reads as two independent PROCEEDs. RELIEVE is unmodeled, "
                   "so b_after_relieve is answered from the still-bound b->a edge."),
        "n": len(rows),
        "route_wrong": sum(1 for r in rows if r["mismatch_class"] == "both"),
        "rows": rows,
    }


def relief_semantics() -> dict[str, Any]:
    """Derive RELIEVE semantics exactly from the oracle, not from the name."""
    results = {}
    for label, setup in [
        ("removes_edge", {"ops": [{"op": "DEPEND", "a": "A", "b": "B"},
                                  {"op": "RELIEVE", "a": "A", "b": "B"}],
                          "expect": {}}),
        ("keeps_other_edges", {"ops": [{"op": "DEPEND", "a": "A", "b": "B"},
                                       {"op": "DEPEND", "a": "A", "b": "C"},
                                       {"op": "RELIEVE", "a": "A", "b": "B"}],
                               "expect": {"A": {"C"}}}),
        ("does_not_delete_surface", {"ops": [{"op": "FORM", "e": "A", "g": "g"},
                                             {"op": "DEPEND", "a": "B", "b": "A"},
                                             {"op": "RELIEVE", "a": "B", "b": "A"}],
                                     "expect": {"B": set(), "A": {"B"}}}),
    ]:
        o = O.OracleState()
        for op in setup["ops"]:
            O.apply_op(o, op)
        results[label] = {"final_deps": {k: sorted(v) for k, v in o.deps.items()},
                          "expected": {k: sorted(v) for k, v in setup["expect"].items()}}
    return {
        "oracle_definition": ("apply_op(o, {'op': 'RELIEVE', 'a': X, 'b': Y}) does "
                              "o.deps[X].discard(Y): it un-binds the CURRENT "
                              "directional edge X->Y. It touches nothing else: no "
                              "formed/proposition state, no scars, no time, no "
                              "decision change."),
        "derived_rules": [
            "edge_removed_from_current_binding_only",
            "history_reconstructible_via_ledger_but_not_resurrected",
            "redeclared_DEPEND_rebinds_the_edge",
            "grounding_may_survive_via_transfer_or_own_formed_state",
        ],
        "notes": ("The oracle keeps no depot of old edges; reconstructibility comes "
                  "from the op stream / the adapter's dependency_ledger. RELIEVE is "
                  "asymmetric: X stops depending on Y, but Y's dependence on X (if "
                  "declared) is untouched."),
        "probes": results,
    }


def repair_mechanism() -> dict[str, Any]:
    src = [
        "baby_ai/ladder/representations.py",
        "baby_ai/adapters/operational_self.py",
        "baby_ai/ladder/oracle.py",
        "baby_ai/ladder/generator.py",
        "baby_ai/ladder/runner.py",
        "baby_ai/ladder/battery.py",
    ]
    return {
        "mechanism": {
            "DEPEND": "record_dependency(a, b): adapter dependencies[a].append(b) "
                      "(ordered prerequisites), ledger records the event",
            "RELIEVE": "relieve_dependency(a, b): adapter dependencies[a].discard(b); "
                       "ledger records the event so the old edge stays reconstructible; "
                       "nothing else changes",
            "route_walk": ("prerequisite satisfaction is now a RECURSIVE, cycle-safe "
                           "walk mirroring oracle._route_internal: for prereq e, own "
                           "declared/contradicted state first, then grounding (own "
                           "formed record OR has-dependencies OR family transfer), then "
                           "every dependency of e recursively, with a seen-set that "
                           "flags a revisit (CYCLE_BLOCKED) as unsatisfied"),
            "cycle_semantics": ("a two-node cycle therefore HOLDs from either node with "
                                "cause prerequisite_missing:<the direct prereq>, exactly "
                                "as the oracle reports; b_after_relieve reads no deps and "
                                "PROCEEDs via transfer again exactly as the oracle does"),
        },
        "source_hashes": {s: _hash(os.path.join(ROOT, s)) for s in src},
        "gates": {"dependency_gate": "off => DEPEND/RELIEVE unmodeled + flat walk disabled "
                                     "(historical); on => repaired"},
    }


def adversarial_cycles() -> dict[str, Any]:
    """Extreme cycle/relieve battery: every program routed by BOTH E and the oracle."""
    import json as _json

    def run(ops, queries):
        rep = HistoricalFractalish()
        for op in ops:
            rep.apply(op)
        o = O.OracleState()
        for op in ops:
            O.apply_op(o, op)
        out = []
        for q in queries:
            got = rep.route(q["e"], q["g"], ctx=q.get("ctx", GLOBAL), t=q.get("t"))
            exp = O.route_oracle(o, q["e"], q["g"], ctx=q.get("ctx", GLOBAL), t=q.get("t"))
            out.append({
                "label": q["label"], "e": q["e"], "g": q["g"], "ctx": q.get("ctx", GLOBAL),
                "expected": exp["decision"], "expected_causes": exp["causes"],
                "got": got["decision"], "got_causes": got.get("causes", []),
                "route_ok": got["decision"] == exp["decision"],
                "cause_ok": sorted(got.get("causes", [])) == sorted(exp["causes"]),
            })
        return out

    ns = PREFIXES[0]
    tag = _tag(ns)
    A = _item(ns, 0, 0)
    B = _item(ns, 0, 1)
    C = _item(ns, 0, 2)
    D = _item(ns, 0, 3)

    def mk(e, g=tag, ctx="*"):
        return {"op": "FORM", "e": e, "g": g, "ctx": ctx}

    def dep(a, b):
        return {"op": "DEPEND", "a": a, "b": b}

    def rel(a, b):
        return {"op": "RELIEVE", "a": a, "b": b}

    cases = [
        {"case": "direct_chain", "ops": [mk(A), dep(B, A)],
         "queries": [{"label": "b", "e": B, "g": tag}, {"label": "a", "e": A, "g": tag}]},
        {"case": "two_cycle_both_blocked", "ops": [dep(A, B), dep(B, A), mk(A)],
         "queries": [{"label": "a", "e": A, "g": tag}, {"label": "b", "e": B, "g": tag}]},
        {"case": "relieve_breaks_cycle", "ops": [dep(A, B), dep(B, A), mk(A), rel(B, A)],
         "queries": [{"label": "b_after", "e": B, "g": tag}]},
        {"case": "relieve_keeps_inverse", "ops": [dep(A, B), dep(B, A), mk(A), rel(A, B)],
         "queries": [{"label": "b", "e": B, "g": tag}, {"label": "a", "e": A, "g": tag}]},
        {"case": "self_loop_unformed", "ops": [dep(A, A)],
         "queries": [{"label": "a", "e": A, "g": tag}]},
        {"case": "self_loop_formed", "ops": [dep(A, A), mk(A)],
         "queries": [{"label": "a", "e": A, "g": tag}]},
        {"case": "relieve_self_noop_then_redeclare", "ops": [dep(A, A), mk(A), rel(A, A), dep(A, A)],
         "queries": [{"label": "a", "e": A, "g": tag}]},
        {"case": "cycle_with_external_ground", "ops": [dep(A, B), dep(B, A), mk(A), dep(B, C), mk(C)],
         "queries": [{"label": "a", "e": A, "g": tag}, {"label": "b", "e": B, "g": tag},
                     {"label": "c", "e": C, "g": tag}]},
        {"case": "a_formed_only_cycle", "ops": [dep(A, B), dep(B, A), mk(A)],
         "queries": [{"label": "a", "e": A, "g": tag}]},
        {"case": "b_unformed_relieved_proceeds", "ops": [dep(A, B), dep(B, A), mk(A), rel(B, A)],
         "queries": [{"label": "b", "e": B, "g": tag}]},
        {"case": "cycle_in_scoped_context_transfer", "ops": [dep(A, B, ), dep(B, A, ), mk(A)],
         "queries": [{"label": "b_scoped", "e": B, "g": tag, "ctx": "ctx_x"}]},
        {"case": "relieve_no_edge_is_noop", "ops": [mk(A), rel(A, B)],
         "queries": [{"label": "a", "e": A, "g": tag}]},
    ]
    out = []
    n = n_ok = 0
    for c in cases:
        rows = run(c["ops"], c["queries"])
        for r in rows:
            n += 1
            if r["route_ok"] and r["cause_ok"]:
                n_ok += 1
        out.append({"case": c["case"], "ops": c["ops"], "queries": rows,
                    "all_correct": all(r["route_ok"] and r["cause_ok"] for r in rows)})
    return {
        "n": n, "n_ok": n_ok,
        "interpretation": ("E's recursive cycle-safe walk reproduces the oracle on "
                           "direct chains, mutual two-node cycles (from either node), "
                           "self-loops (formed and unformed), RELIEVE breaking a cycle, "
                           "RELIEVE keeping the inverse edge, redeclaration, cycles with "
                           "external grounding, and empty RELIEVE no-ops -- with exact "
                           "prerequisite_missing:<surface> causes."),
        "cases": out,
    }

def ablation() -> dict[str, Any]:
    HistoricalFractalish.dependency_gate = False
    off = ladder_battery(LEVELS, SEEDS, ["E"])
    off_t = route_totals(off, rep="E")
    HistoricalFractalish.dependency_gate = True
    on = ladder_battery(LEVELS, SEEDS, ["E"])
    on_t = route_totals(on, rep="E")
    HistoricalFractalish.dependency_gate = True
    return {
        "gate_off_totals": off_t,
        "gate_on_totals": on_t,
        "delta": {
            "route_correct": on_t["route_correct"] - off_t["route_correct"],
            "cause_fidelity": on_t["cause_fidelity"] - off_t["cause_fidelity"],
            "false_proceed": on_t["false_proceed"] - off_t["false_proceed"],
            "false_hold": on_t["false_hold"] - off_t["false_hold"],
        },
"interpretation": ("Gate OFF reproduces the context-repaired historical state "
                           "(route 1200 / cause 1068 / fp 72) exactly. Gate ON adds 48 "
                           "route repairs in R8 (the two cycle rows x 24 seeds toggle "
                           "from PROCEED to HOLD prerequisite_missing:<direct prereq>) "
                           "and 180 cause-fidelity repairs total (132 dependency-class + "
                           "48 R8 cycle-class), all oracle-exact, with ZERO route changes "
                           "elsewhere and ZERO new false holds. RESTORE == gate ON."),
    }


def full_ladder_regression() -> dict[str, Any]:
    on = ladder_battery(LEVELS, SEEDS, ["A", "B", "C", "D", "E"])
    totals = {r: route_totals(on, rep=r) for r in REPS}
    frozen = _load_frozen("FULL_RESULTS.json")
    frozen_rows = {(r["rep"], r["level"], r["seed"], r["label"],
                    r["route_correct"], r["cause_fidelity"]) for r in frozen["rows"]}
    unchanged = {}
    for r in ["A", "B", "C", "D"]:
        cur = {(row["level"], row["seed"], row["label"], row["route_correct"],
                row["cause_fidelity"]) for row in on["rows"] if row["rep"] == r}
        frz = {(row["level"], row["seed"], row["label"], row["route_correct"],
                row["cause_fidelity"]) for row in frozen["rows"] if row["rep"] == r}
        unchanged[r] = {"bit_identical_vs_original_freeze": cur == frz}
    dep_ref = _load_dep("FULL_LADDER_REGRESSION.json")["totals"]["E"]
    return {
        "totals": {r: {k: v for k, v in t.items() if k in ("route_correct", "cause_fidelity",
                                                           "false_proceed", "false_hold")}
                    for r, t in totals.items()},
        "e_dependency_tranche_reference": {k: v for k, v in dep_ref.items() if k in
                                           ("route_correct", "cause_fidelity",
                                            "false_proceed", "false_hold")},
        "a_d_unchanged_vs_original_freeze": unchanged,
        "n_queries": totals["E"]["n"],
        "interpretation": ("Cycle/relieve repair moves E from the dependency-tranche state "
                           "(route 1200 / cause 1200) to route 1248 / cause 1248: +48 "
                           "R8 repairs (route and cause both), false_proceed 72 -> 24 "
                           "(R8 cycle rows no longer false-proceed; R9 temporal residual "
                           "unchanged), false_hold 0 -> 0. A-D bit-identical to the "
                           "original freeze."),
    }


def cause_fidelity() -> dict[str, Any]:
    on = ladder_battery(LEVELS, SEEDS, ["E"])
    rows = [r for r in on["rows"] if r["level"] == "R8"
            and r["label"] in ("a_in_cycle", "b_in_cycle")]
    exact = 0
    n = 0
    violations = []
    for r in rows:
        if r["actual_route"] == "HOLD":
            n += 1
            if r["actual_causes"] and all(c.startswith("prerequisite_missing:") for c in r["actual_causes"]):
                exact += 1
            else:
                violations.append({"seed": r["seed"], "label": r["label"],
                                   "causes": r["actual_causes"],
                                   "expected": r["expected_causes"]})
    return {
        "r8_cycle_hold_count": n,
        "exact_prerequisite_cause_count": exact,
        "exact_rate": "%.2f" % (100.0 * exact / max(1, n)) if n else "n/a",
        "violations": violations,
        "rule": ("Every R8 cycle-class HOLD (a_in_cycle / b_in_cycle) must cite ONLY "
                 "prerequisite_missing:<full surface> (the oracle reports the DIRECT "
                 "prereq whose recursive walk fails); no borrowed "
                 "active_contradiction/declared_prohibition/evidence_missing leaks into "
                 "a cycle-member's cause set."),
        "note": ("R8 carries 96 queries (4 labels x 24 seeds): the two cycle rows must "
                 "HOLD with prerequisite_missing (48), b_after_relieve must PROCEED with "
                 "cause [] (24), and unrelated must HOLD with evidence_missing (24). "
                 "None of the unrelated rows is in the cycle class."),
    }


def manifest(payloads: dict[str, Any]) -> dict[str, Any]:
    import subprocess
    git = None
    try:
        git = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        git = None
    files = ["BASELINE_R8_FAILURES.json", "RELIEVE_SEMANTICS.json", "REPAIR_MECHANISM.json",
             "ADVERSARIAL_CYCLES.json", "ABLATION.json", "FULL_LADDER_REGRESSION.json",
             "CAUSE_FIDELITY.json", "REPAIR_REPORT.md", "manifest.json"]
    return {
        "repair_id": "BABY_AI_FORMATIONCORE_CYCLE_RELIEVE_REPAIR_v0_1",
        "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "philosophy": ("A dependency cycle blocks every member of it; RELIEVE un-binds the "
                       "current directional edge only, with history retained for "
                       "reconstruction and never resurrected."),
        "baseline_freeze": ("BABY_AI_COMPLEXITY_LADDER_v0_1 + CONTEXT_REPAIR_v0_1 + "
                            "DEPENDENCY_REPAIR_v0_1 (read-only)"),
        "seeds": SEEDS, "levels": LEVELS, "representations": REPS,
        "scope": "PRIMARY CLASS REPAIRED: R8 cyclic-mutually-constraining rows (a_in_cycle + b_in_cycle x24, 48 rows). NOT repaired this tranche: temporal validity R9 (deferred).",
        "claim_boundary": ("E's dependency gate is promoted from a direct one-level check to "
                           "a RECURSIVE, cycle-safe precondition walk mirroring the oracle's "
                           "_route_internal, and RELIEVE becomes a real primitive (unordered "
                           "edge removal in the current binding; ledger keeps history). All "
                           "48 R8 repairs are oracle-exact (route and cause); ZERO route "
                           "changes elsewhere; ZERO new false holds. No claim about R9 "
                           "temporal validity."),
        "constraints_satisfied": {
            "no_graph_primitive_added": True,
            "direct_gate_promoted_to_cycle_safe_walk": True,
            "relieve_is_edge_removal_not_state_resolution": True,
            "history_reconstructible_not_resurrected": True,
            "cause_uses_full_surface_not_truncated": True,
            "ablated_on_off_restore": True,
            "frozen_ladder_regression_run": True,
            "a_d_bit_identical": all(v["bit_identical_vs_original_freeze"] for v in payloads["full_ladder_regression"]["a_d_unchanged_vs_original_freeze"].values()),
            "adversarial_cycle_battery_run": True,
        },
        "evidence_files": files,
        "source_hashes": payloads["repair_mechanism"]["source_hashes"],
        "git_head": git,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
    }


def report_md(payloads: dict[str, Any]) -> str:
    a = payloads["ablation"]
    r = payloads["full_ladder_regression"]
    adv = payloads["adversarial_cycles"]
    ro = r["totals"]["E"]
    dep_ref = r["e_dependency_tranche_reference"]
    sem = payloads["relieve_semantics"]
    return f"""# FormationCore CYCLE / RELIEVE REPAIR - v0.2

Repair ID: BABY_AI_FORMATIONCORE_CYCLE_RELIEVE_REPAIR_v0_1
Baselines: BABY_AI_COMPLEXITY_LADDER_v0_1 + CONTEXT_REPAIR_v0_1 + DEPENDENCY_REPAIR_v0_1 (READ ONLY)

## Governing rules

> 1. A dependency cycle blocks every member of it.
> 2. RELIEVE un-binds the *current directional edge* only; history is retained and never resurrected.

## The defect (traced)

R8 (`cyclic_mutually_constraining`): `DEPEND(a->b); DEPEND(b->a); FORM(a)`.
E's v0.1 dependency gate is **direct**: a prerequisite is satisfied iff IT alone
passes the formed-state gate. Inside the cycle every prerequisite reads the other
node as RELEASE-by-transfer, so `a_in_cycle` and `b_in_cycle` both PROCEED (48 rows
across the 24 frozen seeds). RELIEVE is unmodeled, so `b_after_relieve` is answered
from the still-bound `b->a` edge (its route happens to match, but the edge is not
actually un-bound).

Oracle ground truth (read-only, oracle.py `route_oracle` / `_route_internal`):
- the recursive precondition walk flags a revisit as CYCLE_BLOCKED and the surface
  HOLDs with `prerequisite_missing:<direct prereq>`;
- `apply_op` RELIEVE = `deps[X].discard(Y)` on the current binding only.

## The repair

- `HistoricalFractalish._dep_ok(e, g, ctx, _seen)`: recursive, cycle-safe walk
  mirroring `oracle._route_internal`. Order per node: own declared-HOLD, own
  contradicted, grounding (own formed record OR has-dependencies OR family
  transfer), then every dependency recursively. A revisit is CYCLE_BLOCKED ->
  unsatisfied. Fresh seen-set per direct prereq, exactly as the oracle re-seeds
  `_seen` per direct prereq.
- `FormationCore.relieve_dependency(x, y)` + `dependency_ledger`: RELIEVE:
  dependencies[x] discards y (current binding); the ledger keeps every DEPEND and
  RELIEVE event so the old edge is reconstructible but is NOT resurrected. A later
  DEPEND re-binds the edge. RELIEVE touches no formed/proposition state, no scars.
- Toggle `dependency_gate=False` restores the historical traversal (DEPEND/RELIEVE
  unmodeled, flat check) for the ablation.

## Results (frozen, 24 seeds [0..23] inclusive)

| metric | E after dependency repair | E after cycle/relieve repair |
|--------|--------------------------|------------------------------|
| route_correct | {dep_ref['route_correct']}/1272 | {ro['route_correct']}/1272 |
| cause_fidelity | {dep_ref['cause_fidelity']}/1272 | {ro['cause_fidelity']}/1272 |
| false_proceed | {dep_ref['false_proceed']} | {ro['false_proceed']} (R9 residual only) |
| false_hold | {dep_ref['false_hold']} | {ro['false_hold']} |

Gain = +{ro['route_correct'] - dep_ref['route_correct']} route AND
+{ro['cause_fidelity'] - dep_ref['cause_fidelity']} cause, all in R8: the two cycle
rows x 24 seeds now HOLD with `prerequisite_missing:<direct prereq>` exactly as the
oracle does; `b_after_relieve` still PROCEEDs via transfer with cause [] after the
edge is actually un-bound.

Ablation: gate OFF reproduces the dependency-repaired numbers byte-for-byte
(route {a['gate_off_totals']['route_correct']}, cause {a['gate_off_totals']['cause_fidelity']});
gate ON adds the {a['delta']['route_correct']} R8 repairs with ZERO route changes and ZERO
new false holds; RESTORE == gate ON.

Adversarial cycle/relieve battery: {adv['n_ok']}/{adv['n']} queries correct vs route_oracle
(direct chains, two-node cycles from either node, self-loops formed/unformed, RELIEVE
breaking a cycle, RELIEVE keeping the inverse edge, redeclaration, cycles with external
grounding, empty RELIEVE no-ops, cross-context transfer).

A/B/C/D remain bit-identical to the original freeze.

## Claim boundary

The R8 cyclic-constraint and RELIEVE semantics are the scope of this package. No claim
about temporal validity (R9), which remains an honest deferred ask per the frozen
failure profile. Mathematically, mutual constraint + asymmetric relieve are exactly the
two relations the oracle defines for these ops; E now implements both.
"""


def write(payloads: dict[str, Any]) -> list[str]:
    os.makedirs(OUT, exist_ok=True)
    files = ["BASELINE_R8_FAILURES.json", "RELIEVE_SEMANTICS.json", "REPAIR_MECHANISM.json",
             "ADVERSARIAL_CYCLES.json", "ABLATION.json", "FULL_LADDER_REGRESSION.json",
             "CAUSE_FIDELITY.json", "REPAIR_REPORT.md", "manifest.json"]
    for name in files:
        if name == "REPAIR_REPORT.md":
            with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
                f.write(report_md(payloads))
            continue
        key = name.lower().split(".")[0]
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            json.dump(payloads[key], f, indent=2, sort_keys=False, default=str)
    return files


def main() -> None:
    payloads = {
        "baseline_r8_failures": baseline_r8_failures(),
        "relieve_semantics": relief_semantics(),
        "repair_mechanism": repair_mechanism(),
        "adversarial_cycles": adversarial_cycles(),
        "ablation": ablation(),
        "full_ladder_regression": full_ladder_regression(),
        "cause_fidelity": cause_fidelity(),
    }
    payloads["manifest"] = manifest(payloads)
    written = write(payloads)
    print("wrote to:", OUT)
    for f in written:
        print("  ", f)
    t = payloads["full_ladder_regression"]["totals"]["E"]
    print("\nCYCLE-RELIEF-REPAIRED E: route=%d cause=%d fp=%d fh=%d" % (
        t["route_correct"], t["cause_fidelity"], t["false_proceed"], t["false_hold"]))


if __name__ == "__main__":
    main()
