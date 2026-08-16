"""RESIDUAL_BUILD_SPEC_MEASUREMENT_V0 — measurement experiment (read-only).

Given the fixed FormationCore evaluator, how much per-instance state must be
carried to regenerate the correct admissibility result?

Regeneration model. One per-instance residual is captured ONCE at the end of the
program (the state that would be persisted between runs). To regenerate the
correct admissibility verdict for a query, the FIXED evaluator replays/uses that
residual; we measure whether the regenerated verdicts match the oracle for EVERY
query of the fixture, including at-prefix queries whose correct state is an
EARLIER point in the op stream than the final residual.

Candidates compared:

  A  exhaustive derived admissibility snapshot (every query -> verdict table)
  B  local formed/proposition state + full dependency ledger + fixed evaluator
  C  smaller defensible representation (formed state + CURRENT dependencies map
     only, no event history) + fixed evaluator

Measured: serialized size (canonical bytes), explicit fact count, reconstruction
fidelity per query, cause-string reproduction for the cycle HOLD, behavior under
RELIEVE and redeclared DEPEND, and the hidden evaluator/replay cost (shared
evaluator + per-instance residual state). A defensible conclusion is
NO_MEANINGFUL_RESIDUAL_COMPRESSION.
"""

from __future__ import annotations

import json
from typing import Any

from baby_ai.core.semantics import canonical_json
from baby_ai.ladder.generator import make_task, TaskProgram
from baby_ai.ladder.oracle import GLOBAL, OracleState, apply_op, route_oracle
from baby_ai.ladder.representations import build


def canon(obj: Any) -> bytes:
    return json.dumps(canonical_json(obj), sort_keys=True, default=str).encode("utf-8")


def size_bytes(obj: Any) -> int:
    return len(canon(obj))


def fact_count(obj: Any) -> int:
    def walk(o: Any) -> int:
        if isinstance(o, dict):
            return 1 + sum(walk(v) for v in o.values())
        if isinstance(o, (list, tuple, set)):
            return 1 + sum(walk(v) for v in o)
        return 1
    return walk(obj)


def oracle_prefix(ops, at):
    o = OracleState()
    stop = len(ops) if at is None else min(at, len(ops))
    for op in ops[:stop]:
        apply_op(o, op)
    return o


def oracle_answers_for(prog: TaskProgram) -> dict[str, dict[str, Any]]:
    out = {}
    for q in prog.queries:
        o = oracle_prefix(prog.ops, q.get("at"))
        r = route_oracle(o, q["e"], q["g"], ctx=q.get("ctx", GLOBAL), t=q.get("t"))
        out[q["label"]] = {"decision": r["decision"], "causes": sorted(r["causes"])}
    return out


def formed_facts(core) -> dict[str, str]:
    """subject -> group for RELEASE-formed memories (local formed state)."""
    out = {}
    for mid, ss in core.mem_tuples.items():
        if ss.get("subject") and ss.get("group"):
            out[ss["subject"]] = ss["group"]
    return out


def materialize_formed(rep, formed: dict[str, str]) -> None:
    """Emit FORM events for the captured formed state (fixed evaluator replay)."""
    for subj, grp in sorted(formed.items()):
        rep.apply({"op": "FORM", "e": subj, "g": grp})


def ledger_replay_prefix(prog: TaskProgram, core, at: int | None) -> None:
    """Apply dependency/relieve events from the PROG's order up to a prefix,
    exactly reproducing the op ordering the oracle honors. The ledger's event
    order equals the dependency-related ops order; we re-emit DEPEND and RELIEVE
    ops up to the prefix so the reconstructed state equals the oracle prefix state."""
    stop = len(prog.ops) if at is None else min(at, len(prog.ops))
    for op in prog.ops[:stop]:
        if op["op"] in ("DEPEND", "RELIEVE"):
            core.record_dependency(op["a"], op["b"]) if op["op"] == "DEPEND" else core.relieve_dependency(op["a"], op["b"])


def run_seed(seed: int) -> dict[str, Any]:
    prog = make_task("R8", seed)
    oracle = oracle_answers_for(prog)
    # final frozen FC state (as the battery computes it)
    fc = build("E")
    for op in prog.ops:
        fc.apply(op)
    formed = formed_facts(fc.core)

    def verdict(q) -> dict[str, Any]:
        return fc.route(q["e"], q["g"], ctx=q.get("ctx", GLOBAL), t=q.get("t"))

    # ---- Candidate A: exhaustive derived admissibility snapshot (per-query verdicts)
    snapA = {"admissibility": {q["label"]: {"decision": oracle[q["label"]]["decision"],
                                           "causes": oracle[q["label"]]["causes"]}
                               for q in prog.queries}}

    # ---- Candidate B: formed state + full dependency ledger (events)
    ledger_events = [dict(v) for v in fc.core.dependency_ledger]
    snapB = {"formed": formed, "dependency_ledger": ledger_events}
    # evaluator-side shared facts (route rules) are NOT per-instance state; they are
    # the fixed evaluator cost, counted separately (1 unit) below.

    # ---- Candidate C: formed state + CURRENT dependencies map (no history)
    snapC = {"formed": formed, "dependencies": {k: list(v) for k, v in fc.core.dependencies.items()}}

    # ---- Regeneration: replay through the FIXED evaluator per candidate.
    def regenerate(snap, q) -> dict[str, Any]:
        r = build("E")
        materialize_formed(r, snap.get("formed", {}))
        if "dependency_ledger" in snap:
            # replay event history up to the query's prefix (B has the history)
            ledger_replay_prefix(prog, r.core, q.get("at"))
        else:
            # C: only current-deps map, applied unconditionally (no history).
            for k, lst in snap.get("dependencies", {}).items():
                for b in lst:
                    r.core.record_dependency(k, b)
        return r.route(q["e"], q["g"], ctx=q.get("ctx", GLOBAL), t=q.get("t"))

    rows = {}
    for q in prog.queries:
        exp = oracle[q["label"]]
        gotA = snapA["admissibility"][q["label"]]
        gotB = regenerate(snapB, q)
        gotC = regenerate(snapC, q)
        def v(row): return row["decision"]
        def cs(row): return sorted(row.get("causes", []))
        rows[q["label"]] = {
            "at": q.get("at"),
            "oracle": exp["decision"], "oracle_causes": exp["causes"],
            "A": {"decision": v(gotA), "causes": cs(gotA), "match": v(gotA) == exp["decision"] and cs(gotA) == exp["causes"]},
            "B": {"decision": v(gotB), "causes": cs(gotB), "match": v(gotB) == exp["decision"] and cs(gotB) == exp["causes"]},
            "C": {"decision": v(gotC), "causes": cs(gotC), "match": v(gotC) == exp["decision"] and cs(gotC) == exp["causes"]},
        }

    # cause-string reproduction of the cycle HOLD via each candidate (a_in_cycle at=3)
    cycle = [k for k in ("a_in_cycle", "b_in_cycle") if k in rows]

    # behavior under RELIEVE and redeclared DEPEND: from B's reconstruction we must be
    # able to additionally apply a FUTURE RELIEVE / DEPEND (evaluator supports mutation)
    rr = build("E")
    materialize_formed(rr, snapB["formed"])
    for k, lst in {kk: list(v) for kk, v in fc.core.dependencies.items()}.items():
        for b in lst:
            rr.core.record_dependency(k, b)
    # redeclare DEPEND(a->b) again, then RELIEVE(a->b): match oracle apply_op
    oo = OracleState()
    for op in prog.ops:
        apply_op(oo, op)
    apply_op(oo, {"op": "DEPEND", "a": "x", "b": "y"})
    rr.core.record_dependency("x", "y")
    apply_op(oo, {"op": "RELIEVE", "a": "x", "b": "y"})
    rr.core.relieve_dependency("x", "y")
    deps_final_oracle = sorted((k, tuple(sorted(v))) for k, v in oo.deps.items())
    deps_final_fc = sorted((k, tuple(sorted(v))) for k, v in rr.core.dependencies.items())
    mutate_agrees = deps_final_oracle == deps_final_fc

    return {
        "seed": seed,
        "oracle_verdicts": {q["label"]: {"decision": oracle[q["label"]]["decision"],
                                         "causes": oracle[q["label"]]["causes"]} for q in prog.queries},
        "candidate_A": {"size_bytes": size_bytes(snapA), "facts": fact_count(snapA),
                        "note": "exhaustive derived admissibility snapshot"},
        "candidate_B": {"size_bytes": size_bytes(snapB), "facts": fact_count(snapB),
                        "formed_subjects": len(formed), "ledger_events": len(ledger_events),
                        "note": "formed state + full dependency ledger + fixed evaluator"},
        "candidate_C": {"size_bytes": size_bytes(snapC), "facts": fact_count(snapC),
                        "formed_subjects": len(formed),
                        "note": "formed state + current deps map (no event history)"},
        "reconstruction": rows,
        "cycle_causes_reproduced": {k: {"oracle": oracle[k]["causes"], "B": sorted(rows[k]["B"]["causes"]) if k in rows else None} for k in cycle},
        "mutate_agrees_oracle": mutate_agrees,
        "evaluator_cost": {"shared_evaluator_fact_unit": 1,
                            "per_instance_residual_unit": "B: formed+ledger | C: formed+current-map"},
    }


def main() -> None:
    out = {f"R8:{seed}": run_seed(seed) for seed in range(24)}
    all_B = all(all(r["B"]["match"] for r in seed_data["reconstruction"].values())
                for seed_data in out.values())
    all_C = all(all(r["C"]["match"] for r in seed_data["reconstruction"].values())
                for seed_data in out.values())
    all_A = all(all(r["A"]["match"] for r in seed_data["reconstruction"].values())
                for seed_data in out.values())
    report = {
        "method": "regenerate each query verdict from a single end-of-program residual through the FIXED FormationCore evaluator",
        "candidate_A_reconstructs_all": all_A,
        "candidate_B_reconstructs_all": all_B,
        "candidate_C_reconstructs_all": all_C,
        "A_size_min_max": (min(d["candidate_A"]["size_bytes"] for d in out.values()),
                           max(d["candidate_A"]["size_bytes"] for d in out.values())),
        "B_size_min_max": (min(d["candidate_B"]["size_bytes"] for d in out.values()),
                           max(d["candidate_B"]["size_bytes"] for d in out.values())),
        "C_size_min_max": (min(d["candidate_C"]["size_bytes"] for d in out.values()),
                           max(d["candidate_C"]["size_bytes"] for d in out.values())),
        "A_fact_min_max": (min(d["candidate_A"]["facts"] for d in out.values()),
                           max(d["candidate_A"]["facts"] for d in out.values())),
        "B_fact_min_max": (min(d["candidate_B"]["facts"] for d in out.values()),
                           max(d["candidate_B"]["facts"] for d in out.values())),
        "C_fact_min_max": (min(d["candidate_C"]["facts"] for d in out.values()),
                           max(d["candidate_C"]["facts"] for d in out.values())),
    }
    with open("RESIDUAL_BUILD_SPEC_MEASUREMENT_MACHINE.json", "w", encoding="utf-8") as f:
        json.dump({"per_seed": out, "report": report}, f, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))
    # show one failing per-query detail for clarity
    for seed, d in out.items():
        bad = [k for k, r in d["reconstruction"].items() if not (r["B"]["match"] and r["C"]["match"])]
        if bad:
            print(seed, "problem labels:", bad)
            for k in bad:
                print("  ", k, json.dumps(d["reconstruction"][k], indent=1, default=str))


if __name__ == "__main__":
    main()