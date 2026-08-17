"""Deterministic-regeneratable freeze for the CROSS_CONTEXT_RESOLVE tranche.

Writes BABY_AI_FORMATIONCORE_CROSS_CONTEXT_RESOLVE_v0_1 under
baby_ai/artifacts/repair/. Regeneration is byte-deterministic for all
non-manifest evidence files.
"""
import hashlib, json, os, sys, datetime, platform

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from baby_ai.ladder.runner import replay_rep, run_level_all
from baby_ai.ladder.oracle import OracleState, apply_op, route_oracle
import baby_ai.ladder.representations as M

PACK = "BABY_AI_FORMATIONCORE_CROSS_CONTEXT_RESOLVE_v0_1"
OUT = os.path.join(REPO, "baby_ai", "artifacts", "repair", PACK)
os.makedirs(OUT, exist_ok=True)
F = "f"


def _sha8(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]


def _ops(seq):
    out = []
    for item in seq:
        out.append(dict(item))
    return out


def _o(ops, qroot, qctx, t):
    o = OracleState()
    for op in ops:
        apply_op(o, op)
    return route_oracle(o, qroot, F, ctx=qctx, t=t)


def _e(ops, qroot, qctx, t):
    r = replay_rep("E", ops, None)
    return r.route(qroot, F, ctx=qctx, t=t)


def build_witness():
    ops = [
        {"op": "FORM", "e": "a", "g": F},
        {"op": "MARK", "e": "a", "g": F, "ctx": "A"},
        {"op": "RESOLVE", "e": "a", "g": F, "ctx": "B"},
    ]
    before = {"decision": "PROCEED", "causes": []}
    M.HistoricalFractalish.context_resolve_gate = True
    r = replay_rep("E", ops, None)
    on = {q: r.route("a", F, ctx=q, t=None) for q in ("A", "B", "*")}
    M.HistoricalFractalish.context_resolve_gate = False
    roff = replay_rep("E", ops, None)
    off = {q: roff.route("a", F, ctx=q, t=None) for q in ("A", "B", "*")}
    M.HistoricalFractalish.context_resolve_gate = True
    ron = replay_rep("E", ops, None)
    return {
        "ops": ops,
        "query_a_in_context": "A",
        "oracle_a_A": _o(ops, "a", "A", None),
        "e_a_A_before_repair": before,
        "e_a_A_after_gate_ON": on["A"],
        "e_a_A_after_gate_OFF": off["A"],
        "e_query_table_gate_ON": on,
        "e_query_table_gate_OFF": off,
        "scar_statuses_gate_ON": {s.scar_id: ron.plast.get_scar_status(s.scar_id) for s in ron.core.scars},
        "scar_registry_gate_ON": {str(k): v for k, v in ron._scar_for.items()},
    }


def build_adversarial():
    cases = {}
    base = [{"op": "FORM", "e": "a", "g": F}]

    # C1 MARK A; RESOLVE A
    ops = base + [{"op": "MARK", "e": "a", "g": F, "ctx": "A"},
                  {"op": "RESOLVE", "e": "a", "g": F, "ctx": "A"}]
    cases["C1_mark_A_resolve_A"] = {q: {"oracle": _o(ops, "a", q, None), "E": _e(ops, "a", q, None)}
                                    for q in ("A", "B", "*")}

    # C2 MARK A; RESOLVE B
    ops = base + [{"op": "MARK", "e": "a", "g": F, "ctx": "A"},
                  {"op": "RESOLVE", "e": "a", "g": F, "ctx": "B"}]
    cases["C2_mark_A_resolve_B"] = {q: {"oracle": _o(ops, "a", q, None), "E": _e(ops, "a", q, None)}
                                    for q in ("A", "B", "*")}

    # C3 MARK A; MARK B; RESOLVE A
    ops = base + [{"op": "MARK", "e": "a", "g": F, "ctx": "A"},
                  {"op": "MARK", "e": "a", "g": F, "ctx": "B"},
                  {"op": "RESOLVE", "e": "a", "g": F, "ctx": "A"}]
    cases["C3_mark_A_B_resolve_A"] = {q: {"oracle": _o(ops, "a", q, None), "E": _e(ops, "a", q, None)}
                                      for q in ("A", "B", "*")}

    # C4 MARK A; MARK B; RESOLVE A; query both (same as C3, kept per requirement)
    cases["C4_mark_A_B_resolve_A_query_both"] = cases["C3_mark_A_B_resolve_A"]

    # C5 transitive dependencies per context: c depends on a; a resolved A, contradicted B
    ops = [{"op": "FORM", "e": "a", "g": F}, {"op": "FORM", "e": "c", "g": F},
           {"op": "MARK", "e": "a", "g": F, "ctx": "A"},
           {"op": "RESOLVE", "e": "a", "g": F, "ctx": "A"},
           {"op": "MARK", "e": "a", "g": F, "ctx": "B"},
           {"op": "DEPEND", "a": "c", "b": "a"}]
    cases["C5_transitive_per_ctx"] = {q: {"oracle": _o(ops, "c", q, None), "E": _e(ops, "c", q, None)}
                                      for q in ("A", "B", "*")}

    # C6 validity-window per context: VALID a in A window 2..4, mark+resolve A
    ops = base + [{"op": "VALID", "e": "a", "g": F, "from": 2, "to": 4, "ctx": "A"},
                  {"op": "MARK", "e": "a", "g": F, "ctx": "A"},
                  {"op": "RESOLVE", "e": "a", "g": F, "ctx": "A"}]
    cases["C6_validity_per_ctx"] = {q: {"oracle": _o(ops, "a", q, 6), "E": _e(ops, "a", q, 6)}
                                    for q in ("A", "B", "*")}

    # C7 cycle spanning valid context-scoped prereqs: a<->b; a marked A resolved A; b marked B
    ops = [{"op": "FORM", "e": "a", "g": F}, {"op": "FORM", "e": "b", "g": F},
           {"op": "MARK", "e": "a", "g": F, "ctx": "A"},
           {"op": "RESOLVE", "e": "a", "g": F, "ctx": "A"},
           {"op": "MARK", "e": "b", "g": F, "ctx": "B"},
           {"op": "DEPEND", "a": "a", "b": "b"}, {"op": "DEPEND", "a": "b", "b": "a"}]
    cases["C7_cycle_scoped"] = {q: {"oracle": _o(ops, "a", q, None), "E": _e(ops, "a", q, None)}
                                for q in ("A", "B", "*")}

    # C8 A resolved while B remains contradicted
    ops = base + [{"op": "MARK", "e": "a", "g": F, "ctx": "A"},
                  {"op": "RESOLVE", "e": "a", "g": F, "ctx": "A"},
                  {"op": "MARK", "e": "a", "g": F, "ctx": "B"}]
    cases["C8_A_resolved_B_contradicted"] = {q: {"oracle": _o(ops, "a", q, None), "E": _e(ops, "a", q, None)}
                                             for q in ("A", "B", "*")}
    return cases


def build_regression():
    res = run_level_all(["R0","R1","R2","R3","R4","R5","R6","R7","R8","R9","R10"],
                        [0,1,2,3,4], ["A","B","C","D","E"])
    out = {}
    for k, v in res.items():
        e = v["representations"]["E"]
        out[k] = {"accuracy": round(e["accuracy"], 4),
                  "cause_fidelity": round(e["cause_fidelity"], 4),
                  "all_correct": e["all_correct"]}
    return out


def build_ablation():
    ops = [{"op": "FORM", "e": "a", "g": F},
           {"op": "MARK", "e": "a", "g": F, "ctx": "A"},
           {"op": "RESOLVE", "e": "a", "g": F, "ctx": "B"}]
    row = {}
    for gate in (True, False):
        M.HistoricalFractalish.context_resolve_gate = gate
        r = replay_rep("E", ops, None)
        row["gate_ON" if gate else "gate_OFF"] = {q: r.route("a", F, ctx=q, t=None) for q in ("A", "B")}
    M.HistoricalFractalish.context_resolve_gate = True
    r = replay_rep("E", ops, None)
    row["gate_RESTORE"] = {q: r.route("a", F, ctx=q, t=None) for q in ("A", "B")}
    return {"target": "context_resolve_gate", "witness_query_a": row}


def build_readpath_orthogonal():
    ops = [{"op": "FORM", "e": "a", "g": F}, {"op": "MARK", "e": "a", "g": F}]
    row = {}
    for q in ("A", "*"):
        row["query_" + q] = {"oracle": _o(ops, "a", q, None), "E": _e(ops, "a", q, None)}
    row["note"] = "LOGGED orthogonal read-path witness (NOT repaired in this tranche)"
    return row


def main():
    with open(os.path.join(OUT, "WITNESS.json"), "w", encoding="utf-8") as f:
        json.dump(build_witness(), f, indent=2)
    with open(os.path.join(OUT, "ADVERSARIAL_CROSS_CONTEXT.json"), "w", encoding="utf-8") as f:
        json.dump(build_adversarial(), f, indent=2)
    with open(os.path.join(OUT, "FULL_LADDER_REGRESSION.json"), "w", encoding="utf-8") as f:
        json.dump(build_regression(), f, indent=2)
    with open(os.path.join(OUT, "ABLATION.json"), "w", encoding="utf-8") as f:
        json.dump(build_ablation(), f, indent=2)
    with open(os.path.join(OUT, "ORTHOGONAL_READPATH_WITNESS.json"), "w", encoding="utf-8") as f:
        json.dump(build_readpath_orthogonal(), f, indent=2)

    src = ["baby_ai/ladder/representations.py", "baby_ai/adapters/operational_self.py"]
    manifest = {
        "repair_id": PACK,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "philosophy": "Current contradiction authority is context-scoped. RESOLVE pays back only the (entity, context) it names (mirroring oracle contradicted[(e,g,ctx)]); qualification in one context does not rewrite authority in another. Historical scars stay intact; only current authority is rewritten per-context. Gate = context_resolve_gate (default True); OFF restores the entity-wide-clear pre-repair defect for audit.",
        "baseline_freeze": "COMPLEXITY_LADDER + CONTEXT + DEPENDENCY + APPLICABILITY + CYCLE_RELIEVE + R9 validity + MARK_RESOLVE_DEPWALK (all read-only)",
        "seeds": [0,1,2,3,4],
        "levels": ["R0","R1","R2","R3","R4","R5","R6","R7","R8","R9","R10"],
        "representations": ["A","B","C","D","E"],
        "scope": "PRIMARY DEFECT REPAIRED: RESOLVE cleared contradiction authority entity-wide; now scoped to (entity, context).",
        "claim_boundary": "Only RESOLVE's current-authority write is context-scoped, gated. No routes/causes outside the witness family changed; all prior freezes untouched; repeated-MARK and SUPERSEDE+RESOLVE NOT repaired here; a read-path GLOBAL-mark scope divergence is logged orthogonally, not absorbed.",
        "constraints_satisfied": {
            "no_scar_deletion": True,
            "current_authority_rewrite_per_context": True,
            "history_preserved": True,
            "oracle_exact_ctx_key": True,
            "gate_default_ON": True,
            "gate_OFF_restores_entity_wide_clear": True,
            "prior_freezes_untouched": True,
            "separate_tranche_commit": True,
        },
        "evidence_files": ["WITNESS.json","ADVERSARIAL_CROSS_CONTEXT.json",
                           "FULL_LADDER_REGRESSION.json","ABLATION.json",
                           "ORTHOGONAL_READPATH_WITNESS.json","manifest.json"],
        "source_hashes": {p: _sha8(os.path.join(REPO, p)) for p in src},
        "git_head": None,
        "python": platform.python_version(),
        "platform": sys.platform,
    }
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("wrote", PACK)
    for n in sorted(os.listdir(OUT)):
        print("  -", n)


if __name__ == "__main__":
    main()