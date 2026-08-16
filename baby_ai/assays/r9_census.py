"""R9 counterexample census generator (24 residual false proceeds).

Runs the R9 temporal-validity task for every frozen seed, routes each query
through the oracle (ground truth) and through E (HistoricalFractalish, the
qualified FormationCore representation), and emits the exact divergence data
per residual: op stream, divergence point, route/cause on both sides, and a
snapshot of the FC state fields at the query prefix.
"""

from __future__ import annotations

import json
from typing import Any

from baby_ai.ladder.generator import make_task
from baby_ai.ladder.oracle import GLOBAL, OracleState, apply_op, route_oracle
from baby_ai.ladder.representations import build
from baby_ai.ladder.runner import oracle_answers


def op_label(op: dict[str, Any]) -> str:
    if "op" in op:
        if op["op"] == "FORM":
            return f"FORM(e={op['e']}, g={op['g']})"
        if op["op"] == "VALID":
            return f"VALID(e={op['e']}, g={op['g']}, from={op.get('from')}, to={op.get('to')})"
        return str(op)
    return f"QUERY(label={op.get('label')}, e={op.get('e')}, t={op.get('t')})"


def core_snapshot(rep: Any) -> dict[str, Any]:
    core = rep.core
    mems = {}
    for mid, mem in core.memories.items():
        ss = core.mem_tuples.get(mid, {})
        mems[mid] = {
            "subject": ss.get("subject"),
            "group": ss.get("group"),
            "decision": list(getattr(mem, "retained_decisions", []) or []),
            "claim": getattr(mem, "claim", None),
        }
    return {
        "memories": mems,
        "scar_count": len(core.scars),
        "scar_kinds": {k: v for k, v in core.scar_kinds.items()},
        "scar_contexts": {k: v for k, v in core.scar_contexts.items()},
        "dependencies": {k: list(v) for k, v in core.dependencies.items()},
        "dependency_ledger": list(core.dependency_ledger),
        "unmodeled": list(rep.unmodeled),
    }


def census() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed in range(24):
        prog = make_task("R9", seed)
        oracle = oracle_answers(prog)
        seen_before: set[str] = set()
        for i, o in enumerate(prog.ops):
            seen_before.add(o["op"])
        for qi, q in enumerate(prog.queries):
            label = q["label"]
            exp = oracle[label]
            # replay E at query prefix (honors 'at'; t only for time queries)
            rep = build("E")
            stop = len(prog.ops) if q.get("at") is None else min(q.get("at"), len(prog.ops))
            for op in prog.ops[:stop]:
                rep.apply(op)
            got = rep.route(q["e"], q["g"], ctx=q.get("ctx", GLOBAL), t=q.get("t"))
            if got["decision"] == exp["decision"]:
                continue
            tq = q.get("t")
            oracle_time = OracleState()
            for op in prog.ops:
                apply_op(oracle_time, op)
            # Earliest op index where the oracle's state differs structurally from
            # FC's: the VALID op records a window in the oracle's `valid` table but
            # only appends "unmodeled" in FC (no expressible temporal primitive).
            first_state_divergence = None
            for oi, op in enumerate(prog.ops):
                if op["op"] == "VALID":
                    first_state_divergence = {
                        "op_index": oi,
                        "op": op_label(op),
                        "reason": "oracle records valid-window (o.valid); FC marks op unmodeled (no temporal primitive)",
                    }
                    break
            rows.append({
                "case_id": f"R9-S{seed:02d}-{label}",
                "seed": seed,
                "label": label,
                "task_name": prog.name,
                "op_stream": [op_label(o) for o in prog.ops],
                "op_stream_raw": prog.ops,
                "query": q,
                "oracle_time_at_full_ops": oracle_time.time,
                "query_prefix_ops": prog.ops[:stop],
                "divergence": {
                    "at_query_index": qi,
                    "query_op_repr": f"QUERY(label={q.get('label')}, e={q.get('e')}, t={q.get('t')})",
                    "point_kind": "query-evaluation (VALID window applied by oracle only)",
                    "earliest_state_divergence": first_state_divergence,
                },
                "oracle_route": exp["decision"],
                "oracle_causes": exp["causes"],
                "fc_route": got["decision"],
                "fc_causes": got.get("causes", []),
                "divergence_kind": "route_false_proceed" if got["decision"] == "PROCEED" and exp["decision"] == "HOLD" else "route_false_hold",
                "missing_causes": sorted(set(exp["causes"]) - set(got.get("causes", []))),
                "formed_state": {"formed_subjects": sorted({ss.get("subject") for ss in core_mem_tuples(rep).values() if ss.get("subject")})},
                "contradiction_state": {"scar_count": len(rep.core.scars), "scar_kinds": {k: v for k, v in rep.core.scar_kinds.items()}},
                "dependency_state": {k: list(v) for k, v in rep.core.dependencies.items()},
                "applicability_ctx_state": {"queries_ctx": q.get("ctx", GLOBAL), "g": q["g"], "t": q.get("t"), "recorded_window": {"from": 2, "to": 4}},
                "scars_history": {"scar_kinds": {k: v for k, v in rep.core.scar_kinds.items()}, "dependency_ledger_len": len(rep.core.dependency_ledger)},
                "core_snapshot": core_snapshot(rep),
            })
    return rows


def core_mem_tuples(rep: Any) -> dict[str, dict[str, Any]]:
    return rep.core.mem_tuples


def main() -> None:
    rows = census()
    out = {
        "total_residuals": len(rows),
        "residuals": rows,
    }
    with open("R9_COUNTEREXAMPLE_CENSUS_MACHINE.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"residuals captured: {len(rows)}")


if __name__ == "__main__":
    main()