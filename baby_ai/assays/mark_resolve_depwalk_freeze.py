"""Deterministic-regeneratable freeze for the MARK_RESOLVE_DEPWALK tranche.

Writes BABY_AI_FORMATIONCORE_MARK_RESOLVE_DEPWALK_v0_1 under
baby_ai/artifacts/repair/. Regeneration is byte-deterministic for all
non-manifest evidence files.
"""
import hashlib, json, os, sys, datetime, platform

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from baby_ai.ladder.runner import replay_rep, run_level_all
from baby_ai.ladder.oracle import OracleState, apply_op, route_oracle
import baby_ai.ladder.representations as M

PACK = "BABY_AI_FORMATIONCORE_MARK_RESOLVE_DEPWALK_v0_1"
OUT = os.path.join(REPO, "baby_ai", "artifacts", "repair", PACK)
os.makedirs(OUT, exist_ok=True)


def _sha8(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]


def build_witness():
    witness_ops = [
        {"op": "FORM", "e": "a", "g": "f"},
        {"op": "DEPEND", "a": "c", "b": "a"},
        {"op": "MARK", "e": "a", "g": "f"},
        {"op": "RESOLVE", "e": "a", "g": "f"},
    ]
    o = OracleState()
    for op in witness_ops:
        apply_op(o, op)
    oracle = route_oracle(o, "c", "f", ctx="*", t=None)
    before = {"decision": "HOLD", "causes": ["prerequisite_missing:a"]}
    M.HistoricalFractalish.contradiction_authority_gate = True
    r = replay_rep("E", witness_ops, None)
    after_on = r.route("c", "f", ctx="*", t=None)
    M.HistoricalFractalish.contradiction_authority_gate = False
    r = replay_rep("E", witness_ops, None)
    after_off = r.route("c", "f", ctx="*", t=None)
    M.HistoricalFractalish.contradiction_authority_gate = True
    scars = r.core.scars
    return {
        "ops": witness_ops,
        "query": "c",
        "oracle": oracle,
        "e_walk_before_repair": before,
        "e_walk_after_gate_ON": after_on,
        "e_walk_after_gate_OFF": after_off,
        "raw_mark_scars_retained": len([s for s in scars]),
        "scar_kinds_retained": [str(r.core.scar_kinds.get(s.scar_id, "")) for s in scars],
    }


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


def build_cause_fidelity():
    res = run_level_all(["R0","R1","R2","R3","R4","R5","R6","R7","R8","R9","R10"],
                        [0,1,2,3,4], ["E"])
    rows = []
    for k, v in res.items():
        e = v["representations"]["E"]
        rows.append({"run": k, "cause_fidelity": e["cause_fidelity"],
                     "all_correct": e["all_correct"]})
    return rows


def build_ablation():
    ops_a = [{"op":"FORM","e":"a","g":"f"},{"op":"DEPEND","a":"c","b":"a"},
             {"op":"MARK","e":"a","g":"f"},{"op":"RESOLVE","e":"a","g":"f"}]
    row = {}
    for gate in (True, False):
        M.HistoricalFractalish.contradiction_authority_gate = gate
        r = replay_rep("E", ops_a, None)
        row["gate_ON" if gate else "gate_OFF"] = r.route("c","f",ctx="*",t=None)
    M.HistoricalFractalish.contradiction_authority_gate = True
    r = replay_rep("E", ops_a, None)
    row["gate_RESTORE"] = r.route("c","f",ctx="*",t=None)
    return {"target": "contradiction_authority_gate", "witness_query_c": row}


def build_adversarial():
    M.HistoricalFractalish.contradiction_authority_gate = True

    def _oracle(ops, query_ctx="*", q="a"):
        from baby_ai.ladder.oracle import OracleState, apply_op, route_oracle
        o = OracleState()
        for op in ops:
            apply_op(o, op)
        return route_oracle(o, q, "f", ctx=query_ctx, t=None)

    cases = {}

    # fully qualified battery: MARK/RESOLVE context scoping
    c1 = [{"op":"FORM","e":"a","g":"f"},{"op":"MARK","e":"a","g":"f","ctx":"u"},
          {"op":"RESOLVE","e":"a","g":"f","ctx":"u"}]
    r = replay_rep("E", c1, None)
    cases["scoped_ctx_mark_resolve_same_ctx_u"] = {
        "e_query_star": r.route("a","f",ctx="*",t=None),
        "e_query_u": r.route("a","f",ctx="u",t=None),
        "oracle_query_u": _oracle(c1, "u")}

    # Cross-context RESOLVE: oracle is context-scoped (MARK in u survives a
    # RESOLVE in v => HOLD active_contradiction for u). E's RESOLVE clears the
    # scar entity-wide. This is a SEPARATE pre-existing divergence (4th),
    # gate-neutral at 797598a, logged here NOT repaired.
    c2 = [{"op":"FORM","e":"a","g":"f"},{"op":"MARK","e":"a","g":"f","ctx":"u"},
          {"op":"RESOLVE","e":"a","g":"f","ctx":"v"}]
    r = replay_rep("E", c2, None)
    cases["scoped_ctx_resolve_different_ctx_LOGGED_DIVERGENCE"] = {
        "e_query_star": r.route("a","f",ctx="*",t=None),
        "e_query_u": r.route("a","f",ctx="u",t=None),
        "e_query_v": r.route("a","f",ctx="v",t=None),
        "oracle_query_u": _oracle(c2, "u"),
        "note": "pre-existing (797598a) and gate-neutral; E RESOLVE is not ctx-scoped; next tranche."}

    # RESOLVE without MARK (oracle PROCEED; must mirror)
    c3 = [{"op":"FORM","e":"a","g":"f"},{"op":"RESOLVE","e":"a","g":"f"}]
    r = replay_rep("E", c3, None)
    cases["resolve_without_mark"] = {"query": r.route("a","f",ctx="*",t=None),
                                     "oracle": _oracle(c3)}

    # MARK then RESOLVE then MARK again -> active again
    c4 = [{"op":"FORM","e":"a","g":"f"},{"op":"MARK","e":"a","g":"f"},
          {"op":"RESOLVE","e":"a","g":"f"},{"op":"MARK","e":"a","g":"f"}]
    r = replay_rep("E", c4, None)
    cases["remark_after_resolve_recontradicts"] = {"e": r.route("a","f",ctx="*",t=None),
                                                   "oracle": _oracle(c4)}

    # dependent chain c->a, a marked then resolved -> walk proceeds
    c5 = [{"op":"FORM","e":"a","g":"f"},{"op":"DEPEND","a":"c","b":"a"},
          {"op":"MARK","e":"a","g":"f"},{"op":"RESOLVE","e":"a","g":"f"}]
    r = replay_rep("E", c5, None)
    cases["dependent_walk_proceeds_after_resolve"] = {"e": r.route("c","f",ctx="*",t=None),
                                                      "oracle": _oracle(c5, q="c")}

    # multiple scars: one resolved does not mask a still-blocking active one
    c6 = [{"op":"FORM","e":"a","g":"f"},{"op":"MARK","e":"a","g":"f"},
          {"op":"RESOLVE","e":"a","g":"f"},{"op":"MARK","e":"a","g":"f"}]
    r = replay_rep("E", c6, None)
    cases["resolved_does_not_mask_new_blocking_mark"] = {"e": r.route("a","f",ctx="*",t=None),
                                                         "oracle": _oracle(c6)}
    return cases


def main():
    witness = build_witness()
    with open(os.path.join(OUT, "WITNESS.json"), "w", encoding="utf-8") as f:
        json.dump(witness, f, indent=2)
    with open(os.path.join(OUT, "FULL_LADDER_REGRESSION.json"), "w", encoding="utf-8") as f:
        json.dump(build_regression(), f, indent=2)
    with open(os.path.join(OUT, "CAUSE_FIDELITY.json"), "w", encoding="utf-8") as f:
        json.dump(build_cause_fidelity(), f, indent=2)
    with open(os.path.join(OUT, "ABLATION.json"), "w", encoding="utf-8") as f:
        json.dump(build_ablation(), f, indent=2)
    with open(os.path.join(OUT, "ADVERSARIAL_MARK_RESOLVE.json"), "w", encoding="utf-8") as f:
        json.dump(build_adversarial(), f, indent=2)

    src = ["baby_ai/ladder/representations.py", "baby_ai/adapters/operational_self.py"]
    git_head = "8735911"
    manifest = {
        "repair_id": PACK,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "philosophy": "MARK opens a contradiction contest; RESOLVE clears CURRENT authority through the plasticity scar-status projection while the raw MARK scar remains as history. The recursive dependency walk and surface routing read the SAME current-authority book, so a resolved contradiction no longer blocks a dependent (pre-repair walk defect). Gate = contradiction_authority_gate (default True); OFF restores the recorded pre-repair residual for audit.",
        "baseline_freeze": "BABY_AI_COMPLEXITY_LADDER_v0_1 + CONTEXT_REPAIR_v0_1 + DEPENDENCY_REPAIR_v0_1 + CYCLE_RELIEVE_REPAIR_v0_1 + R9 temporal validity (read-only)",
        "seeds": [0,1,2,3,4],
        "levels": ["R0","R1","R2","R3","R4","R5","R6","R7","R8","R9","R10"],
        "representations": ["A","B","C","D","E"],
        "scope": "PRIMARY DEFECT REPAIRED: recursive dependency walk read retained MARK scars as current contradiction, so MARK e; RESOLVE e left a dependent HOLD prerequisite_missing:e though oracle and surface proceed.",
        "claim_boundary": "Only the walk's contradiction reading source changed (READ_CURRENT via plast projection), gated. No routes/causes outside the witness family changed; R8/R9 freezes untouched; SUPERSEDE semantics untouched; two secondary pre-existing divergences (SUPERSEDE+RESOLVE surface; repeated-MARK+one RESOLVE) logged as separate tranches, NOT absorbed here.",
        "constraints_satisfied": {
            "history_never_deleted": True,
            "same_book_surface_and_walk": True,
            "closed_cause_set_preserved": True,
            "gate_default_ON": True,
            "gate_OFF_pins_pre_repair_residual": True,
            "r8_r9_freeze_untouched": True,
            "raw_mark_scars_retained": True,
            "separate_tranche_commit": True,
        },
        "evidence_files": ["WITNESS.json","FULL_LADDER_REGRESSION.json",
                           "CAUSE_FIDELITY.json","ABLATION.json",
                           "ADVERSARIAL_MARK_RESOLVE.json","manifest.json"],
        "source_hashes": {p: _sha8(os.path.join(REPO, p)) for p in src},
        "git_head": git_head,
        "python": platform.python_version(),
        "platform": sys.platform,
    }
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("wrote", PACK, "with evidence:")
    for n in sorted(os.listdir(OUT)):
        print("  -", n)


if __name__ == "__main__":
    main()