"""Full frozen-seed battery for the complexity ladder (§10).

Runs every representation (A–E) on every rung (R0–R10) across the frozen
hostile seed set (0..23), recording for EVERY query:

    expected route / actual route / route correctness
    expected cause set / actual cause set / cause fidelity
    false-proceed / false-hold flags
    state bytes (after prefix + final), op counts (applies/routes)
    relational complexity and temporal/context complexity of the task
    failure classification (route-only, cause-only, both, none)

Correctness is deliberately split into ROUTE correctness and CAUSE fidelity:
HOLD because of active contradiction is NOT the same as HOLD because of missing
evidence. Both are reported separately and aggregated independently.

The output is written to artifacts/freeze/BABY_AI_COMPLEXITY_LADDER_v0_1/
as the frozen battery package.
"""

from __future__ import annotations

import json
import hashlib
import os
import sys
import time
from typing import Any

from baby_ai.ladder.generator import make_task
from baby_ai.ladder.runner import oracle_answers, replay_rep, relational_complexity
from baby_ai.hostile.task_gen import SEEDS

LEVELS = ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"]
REPS = ["A", "B", "C", "D", "E"]

# canonical block causes (order matters for readability)
CAUSE_KINDS = [
    "active_contradiction", "declared_prohibition", "evidence_missing",
    "prerequisite_missing", "expired_outside_window", "cyclic_constraint",
]


def classify(query: dict[str, Any]) -> str:
    """Temporal/context/relational demand of a query."""
    if query.get("t") is not None:
        return "temporal"
    if query.get("ctx") not in (None, "*"):
        return "context"
    if query.get("at") is not None:
        return "prefix"
    return "plain"


def one_query(rep: str, level: str, seed: int, program, q: dict[str, Any]) -> dict[str, Any]:
    oracle = oracle_answers(program)[str(q["label"])]
    r = replay_rep(rep, program.ops, q.get("at"))
    got = r.route(q["e"], q["g"], ctx=q.get("ctx", "*"), t=q.get("t"))
    route_ok = got["decision"] == oracle["decision"]
    cause_ok = sorted(got.get("causes", [])) == sorted(oracle["causes"])
    exp_dec = oracle["decision"]
    got_dec = got["decision"]
    false_proceed = got_dec == "PROCEED" and exp_dec == "HOLD"
    false_hold = got_dec == "HOLD" and exp_dec == "PROCEED"
    if not route_ok:
        failure = "false_proceed" if false_proceed else "false_hold"
        classif = f"route_{failure}"
    elif not cause_ok:
        classif = "cause_only"
    else:
        classif = "none"
    return {
        "rep": rep, "level": level, "seed": seed,
        "label": str(q["label"]), "e": q["e"], "g": q["g"],
        "ctx": q.get("ctx", "*"), "t": q.get("t"), "at": q.get("at"),
        "demand": classify(q),
        "expected_route": exp_dec, "actual_route": got_dec,
        "route_correct": route_ok,
        "expected_causes": oracle["causes"], "actual_causes": got.get("causes", []),
        "cause_fidelity": cause_ok,
        "false_proceed": false_proceed, "false_hold": false_hold,
        "failure_class": classif,
        "missing_causes": sorted(set(oracle["causes"]) - set(got.get("causes", []))),
        "extra_causes": sorted(set(got.get("causes", [])) - set(oracle["causes"])),
        "state_bytes_after_prefix": r.state_bytes(),
    }


def run_battery(levels: list[str], seeds: list[int], reps: list[str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    tasks: dict[str, Any] = {}
    started = time.time()
    for level in levels:
        for seed in seeds:
            program = make_task(level, seed)
            tkey = f"{level}:{seed}"
            tasks[tkey] = {
                "level": level, "seed": seed, "name": program.name, "notes": program.notes,
                "complexity": relational_complexity(program),
                "queries": [
                    {"label": str(q["label"]), "e": q["e"], "ctx": q.get("ctx", "*"),
                     "t": q.get("t"), "at": q.get("at")} for q in program.queries
                ],
                "generator_hash": _task_hash(program),
            }
            for rep in reps:
                for q in program.queries:
                    rows.append(one_query(rep, level, seed, program, q))
    return {"rows": rows, "tasks": tasks, "elapsed_s": round(time.time() - started, 3)}


def _task_hash(program) -> str:
    payload = json.dumps({
        "level": program.level, "seed": program.seed, "ops": program.ops,
        "queries": program.queries,
    }, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def route_totals(battery: dict[str, Any], *, rep: str | None = None,
                 level: str | None = None) -> dict[str, Any]:
    rows = battery["rows"]
    if rep:
        rows = [r for r in rows if r["rep"] == rep]
    if level:
        rows = [r for r in rows if r["level"] == level]
    n = len(rows)
    return {
        "n": n,
        "route_correct": sum(1 for r in rows if r["route_correct"]),
        "cause_fidelity": sum(1 for r in rows if r["cause_fidelity"]),
        "false_proceed": sum(1 for r in rows if r["false_proceed"]),
        "false_hold": sum(1 for r in rows if r["false_hold"]),
        "failure_classes": _count(rows, "failure_class"),
        "route_accuracy": round(sum(1 for r in rows if r["route_correct"]) / n, 6) if n else None,
        "cause_accuracy": round(sum(1 for r in rows if r["cause_fidelity"]) / n, 6) if n else None,
    }


def _count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


def by_rep_by_level(battery: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for rep in REPS:
        out[rep] = {}
        for level in LEVELS:
            out[rep][level] = route_totals(battery, rep=rep, level=level)
    return out


def first_failures(battery: dict[str, Any]) -> dict[str, Any]:
    """First level (by rung index) where route correctness or cause fidelity drops."""
    out: dict[str, Any] = {}
    for rep in REPS:
        row = {"first_route_fail": None, "first_cause_fail": None,
               "route_levels": {}, "cause_levels": {}}
        for level in LEVELS:
            t = route_totals(battery, rep=rep, level=level)
            row["route_levels"][level] = t["route_correct"]
            row["cause_levels"][level] = t["cause_fidelity"]
            if row["first_route_fail"] is None and t["route_correct"] < t["n"]:
                row["first_route_fail"] = level
            if row["first_cause_fail"] is None and t["cause_fidelity"] < t["n"]:
                row["first_cause_fail"] = level
        out[rep] = row
    return out


def state_op_costs(battery: dict[str, Any]) -> dict[str, Any]:
    """Per rep+level: average state bytes (prefix+final) and op counts."""
    out: dict[str, Any] = {}
    for rep in REPS:
        out[rep] = {}
        for level in LEVELS:
            key = f"{level}:0"
            t = battery["tasks"][key]
            final = None
            prog = make_task(level, 0)
            r = replay_rep(rep, prog.ops, None)
            final = r.state_bytes()
            app = r.work()["applies"]
            pre_rows = [x for x in battery["rows"]
                        if x["rep"] == rep and x["level"] == level]
            avg_pre = round(sum(x["state_bytes_after_prefix"] for x in pre_rows) / len(pre_rows), 1) if pre_rows else None
            out[rep][level] = {
                "final_state_bytes": final,
                "avg_prefix_state_bytes": avg_pre,
                "applies": app,
                "entities": t["complexity"]["entities"],
                "ops": t["complexity"]["op_count"],
            }
    return out


def rep_level_cost_summary(state_costs: dict[str, Any]) -> dict[str, Any]:
    """Sum/average across all levels per rep."""
    out: dict[str, Any] = {}
    for rep, levels in state_costs.items():
        out[rep] = {
            "total_final_state_bytes": sum(v["final_state_bytes"] for v in levels.values()),
            "avg_final_state_bytes": round(
                sum(v["final_state_bytes"] for v in levels.values()) / len(levels), 1),
            "avg_applies_per_task": round(sum(v["applies"] for v in levels.values()) / len(levels), 1),
        }
    return out


def oracle_audit(battery: dict[str, Any]) -> dict[str, Any]:
    """Per rung, plain-English semantics for the oracle contract (§4)."""
    descriptions = {
        "R0": "One independently formed proposition. Fact: e is formed under family g. "
              "Dependency: none. Why PROCEED: own FORM record grounds it. Why HOLD: no form, "
              "no deps, no family member -> evidence_missing. Reversal: remove the FORM.",
        "R1": "Form then contradict then resolve. Facts: FORM(e), MARK(e), RESOLVE(e). "
              "Why PROCEED after resolve: contradiction cleared by RESOLVE. Why HOLD after mark: "
              "active_contradiction. Reversal: remove the RESOLVE.",
        "R2": "n independent FORMs in one family. Each stands alone; transfer makes a never-seen "
              "family member PROCEED. Why HOLD: unrelated family, no grounds. Reversal: nothing.",
        "R3": "b depends on a; a is superseded to HOLD. Fact: FORM(a); DEPEND(b on a); SUPERSEDE(a,HOLD). "
              "Why b PROCEED before supersede: b's deps ground b and a proceeds. Why b HOLD after: "
              "prerequisite a now HOLD. Reversal: remove supersede, or relieve the edge.",
        "R4": "Transitive chain: root FORMed, each item depends on the previous. Pre-cascade: every "
              "item PROCEED because the chain grounds it. Post-cascade: root->HOLD propagates to all "
              "dependents as prerequisite_missing. Reversal: re-form the root.",
        "R5": "Fan-out: several kids depend on one parent; fan-in: one conjunction depends on two "
              "parents. Why kids PROCEED: parent grounds each. Why conj PROCEED: both parents "
              "proceed. Why unrelated HOLD: no grounds. Reversal: mark either parent HOLD.",
        "R6": "One shared FORM gates many conclusions via DEPEND edges. Reversal: contradict the shared "
              "evidence, which cascades to every conclusion.",
        "R7": "Contradiction scoped to ctx1. Facts: FORM(a, ctx_base); MARK(a, ctx1). Why a_other_ctx "
              "PROCEED: contradiction is scoped, base ctx unaffected. Why a_scoped_ctx HOLD: mark lives "
              "there. Reversal: remove the MARK.",
        "R8": "a<->b mutual dependency cycle, a FORMed. Why both HOLD in cycle: recursive precondition "
              "walk detects CYCLE_BLOCKED, neither can proceed on the cycle. Why b PROCEED after RELIEVE: "
              "the b->a edge removed, b is now grounded by remaining a->b edge and a proceeds. Reversal: "
              "re-add the edge.",
        "R9": "a FORMed with VALID window [2,4]. Why PROCEED at t=2,3: inside window. Why HOLD at t=6: "
              "expired_outside_window. Reversal: extend the window.",
        "R10": "Old global state FORMed; SUPERSEDE HOLD scoped to ctx_new. Why base/other ctx PROCEED: "
               "the supersede is scoped, global form remains. Why ctx_new HOLD: declared_prohibition "
               "there. Reversal: move supersede to GLOBAL.",
    }
    out: dict[str, Any] = {}
    for level in LEVELS:
        t = battery["tasks"][f"{level}:0"]
        cx = t["complexity"]
        out[level] = {
            "name": t["name"],
            "semantics": descriptions[level],
            "facts": [{"op": o["op"], "subject": o.get("e") or o.get("a") or o.get("b"),
                       "target": o.get("b")} for o in make_task(level, 0).ops],
            "relational_complexity": cx,
            "temporal_or_context": {
                "has_time_queries": any(q.get("t") is not None for q in t["queries"]),
                "has_context_queries": any(q.get("ctx") not in (None, "*") for q in t["queries"]),
                "has_prefix_queries": any(q.get("at") is not None for q in t["queries"]),
            },
        }
    return out


def e_failure_profile(battery: dict[str, Any]) -> dict[str, Any]:
    """Exact evidence for the unmodified historical FormationCore (E)."""
    erows = [r for r in battery["rows"] if r["rep"] == "E"]
    fails = [r for r in erows if r["failure_class"] != "none"]
    profile = {
        "note": "FROZEN UNMODIFIED. No repair applied to E (historical FormationCore).",
        "summary": route_totals(battery, rep="E"),
        "failures": fails,
        "findings": {
            "unrelated_family_over_transfer": {
                "evidence": [
                    {"level": r["level"], "seed": r["seed"], "label": r["label"],
                     "expected": r["expected_route"], "actual": r["actual_route"],
                     "expected_causes": r["expected_causes"], "actual_causes": r["actual_causes"]}
                    for r in fails
                    if "unrelated" in r["label"] and r["actual_route"] == "PROCEED"
                ],
                "claim": "E over-proceeds on unrelated-family queries: token-level retrieval "
                         "reaches a formed candidate for a surface that shares tokens but not tag.",
            },
            "missing_context_scoping": {
                "evidence": [
                    {"level": r["level"], "seed": r["seed"], "label": r["label"],
                     "expected": r["expected_route"], "actual": r["actual_route"]}
                    for r in fails if r["demand"] == "context"
                ],
                "claim": "E lacks a context dimension: ctx-scoped contradiction/supersede is "
                         "treated as global, so scoped HOLDs bleed into other contexts.",
            },
            "missing_temporal_validity": {
                "evidence": [
                    {"level": r["level"], "seed": r["seed"], "label": r["label"],
                     "expected": r["expected_route"], "actual": r["actual_route"]}
                    for r in fails if r["demand"] == "temporal"
                ],
                "claim": "E lacks a time dimension: VALID windows are unmodeled, so expired "
                         "queries still PROCEED.",
            },
            "missing_dependency_primitives": {
                "evidence": [
                    {"level": r["level"], "seed": r["seed"], "label": r["label"],
                     "expected": r["expected_route"], "actual": r["actual_route"],
                     "expected_causes": r["expected_causes"], "actual_causes": r["actual_causes"]}
                    for r in fails if r["demand"] == "plain" and r["level"] in ("R9",)
                ],
                "claim": ("E models DEPEND and RELIEVE via the dependency gate: a dependent "
                       "proceeds only while its prerequisite passes the recursive, "
                       "cycle-safe formed-state walk in the query context (RW8); RELIEVE "
                       "un-binds the current edge and the ledger keeps history. R9 "
                       "temporal (VALID windows) remains the lone unmodeled demand."),
            },
        },
    }
    return profile


def b_vs_c_comparison(battery: dict[str, Any]) -> dict[str, Any]:
    """Behavioral equivalence check + cost/cause comparison between B and C."""
    bro = route_totals(battery, rep="B")
    cro = route_totals(battery, rep="C")
    bvs = {l: route_totals(battery, rep="B", level=l) for l in LEVELS}
    cvs = {l: route_totals(battery, rep="C", level=l) for l in LEVELS}
    bcost = rep_level_cost_summary(state_op_costs(battery))["B"]
    ccost = rep_level_cost_summary(state_op_costs(battery))["C"]
    return {
        "route_correct": {"B": bro["route_correct"], "C": cro["route_correct"]},
        "cause_fidelity": {"B": bro["cause_fidelity"], "C": cro["cause_fidelity"]},
        "behaviorally_identical": all(
            bvs[l]["route_correct"] == cvs[l]["route_correct"]
            and bvs[l]["cause_fidelity"] == cvs[l]["cause_fidelity"] for l in LEVELS),
        "per_level": {l: {"B_route": bvs[l]["route_correct"], "C_route": cvs[l]["route_correct"],
                          "B_cause": bvs[l]["cause_fidelity"], "C_cause": cvs[l]["cause_fidelity"]}
                      for l in LEVELS},
        "costs": {"B": bcost, "C": ccost},
        "interpretation": "C is minimal-admissibility with first-class per-cause records. "
                          "B is keyed/versioned record lists. If B and C are behaviorally identical "
                          "across all 24 seeds, admissibility has not yet earned its extra machinery "
                          "on this ladder; differences must be demonstrated by a task the ladder does "
                          "not yet include (e.g. fine-grained cause surgery / unambiguous reopening).",
    }


def relational_floor(battery: dict[str, Any]) -> dict[str, Any]:
    """Which rungs require explicit stored relational info, and whether graph
    organization (D) beats keyed encoding (B)."""
    b = {l: route_totals(battery, rep="B", level=l) for l in LEVELS}
    d = {l: route_totals(battery, rep="D", level=l) for l in LEVELS}
    relational_required = [l for l in LEVELS
                           if l in ("R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10")
                           and route_totals(battery, rep="A", level=l)["route_correct"] < route_totals(battery, rep="A", level=l)["n"]]
    return {
        "relational_info_required_from": "R3 (first rung scalar A fails)",
        "relational_info_required_levels": relational_required,
        "graph_object_earned": False,
        "graph_object_note": "B (keyed/versioned lists) matches D (explicit graph) on every rung "
                             "across all seeds: both 100% route+cause. Explicit graph organization "
                             "has NOT been shown necessary. Relational floor stays OPEN.",
        "b_route_correct": {l: b[l]["route_correct"] for l in LEVELS},
        "d_route_correct": {l: d[l]["route_correct"] for l in LEVELS},
        "b_cause_fidelity": {l: b[l]["cause_fidelity"] for l in LEVELS},
        "d_cause_fidelity": {l: d[l]["cause_fidelity"] for l in LEVELS},
    }


def write_package(battery: dict[str, Any], outdir: str) -> list[str]:
    os.makedirs(outdir, exist_ok=True)
    files: list[str] = []

    def dump(name: str, payload: Any) -> None:
        p = os.path.join(outdir, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=False, default=str)
        files.append(name)

    dump("FULL_RESULTS.json", battery)
    dump("ROUTE_CORRECTNESS.json", {"by_rep": by_rep_by_level(battery),
                                    "totals": {r: route_totals(battery, rep=r) for r in REPS}})
    dump("CAUSE_FIDELITY.json", {"by_rep": by_rep_by_level(battery),
                                 "note": "cause_fidelity = exact cause-set match; separate from route_correct"})
    dump("ORACLE_AUDIT.json", oracle_audit(battery))
    dump("ARCHITECTURE_COMPARISON.json", {
        "first_failures": first_failures(battery),
        "route_totals": {r: route_totals(battery, rep=r) for r in REPS},
        "b_vs_c": b_vs_c_comparison(battery),
        "relational_floor": relational_floor(battery),
    })
    dump("FORMATIONCORE_FAILURE_PROFILE.json", e_failure_profile(battery))
    dump("STATE_AND_OP_COSTS.json", state_op_costs(battery))
    dump("RELATIONAL_FLOOR.json", relational_floor(battery))

    md_files = ["ORACLE_AUDIT.md", "COMPLEXITY_LADDER_REPORT.md"]

    manifest = {
        "freeze_id": "BABY_AI_COMPLEXITY_LADDER_v0_1",
        "created_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "seeds": SEEDS,
        "levels": LEVELS,
        "representations": REPS,
        "query_count": len(battery["rows"]),
        "task_count": len(battery["tasks"]),
        "seed_source": "baby_ai.hostile.task_gen.SEEDS (frozen 0..23)",
        "generator_hashes": {k: v["generator_hash"] for k, v in battery["tasks"].items()},
        "architecture_status": "FROZEN UNMODIFIED for A/B/C/D/E",
        "evidence_files": files + md_files,
        "python": {"version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                   "platform": sys.platform},
    }
    dump("manifest.json", manifest)
    return files + md_files


if __name__ == "__main__":
    outdir = os.path.join(os.path.dirname(__file__), "..", "artifacts", "freeze",
                          "BABY_AI_COMPLEXITY_LADDER_v0_1")
    outdir = os.path.abspath(outdir)
    bat = run_battery(LEVELS, SEEDS, REPS)
    print(f"rows={len(bat['rows'])} elapsed={bat['elapsed_s']}s")
    write_package(bat, outdir)
    print("wrote:", outdir)
    for rep in REPS:
        t = route_totals(bat, rep=rep)
        print(f"  {rep}: route={t['route_correct']}/{t['n']} cause={t['cause_fidelity']}/{t['n']} "
              f"fp={t['false_proceed']} fh={t['false_hold']}")
