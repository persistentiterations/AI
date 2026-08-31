"""M2 — authoritative-history continuity across process death (host-only).

Orchestrates the FROZEN FormationCore persistence components; creates NO new
authority semantics. Each phase is a separate process invocation (genuine cold
restart via serialized state, never the same in-memory object).

Phases:
  phase-a   build H1 -> HOLD -> persist -> trace -> exit
  phase-b   load H1 -> HOLD -> RESOLVE -> PROCEED -> persist -> trace -> exit
  phase-c   load H1' -> PROCEED -> verify retained scar + lineage -> trace -> exit
  corrupt   load snapshot, apply a corruption, reload, report pass/fail-closed

Invariants I1..I8 and corruption controls C1..C4 are checked and emitted in the
trace. This runner may only orchestrate; it must not alter authority semantics.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from baby_ai import domain as D
from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.core.provenance import ProvenanceLedger
from baby_ai.core.receipts import ReceiptLedger

ITEM = "flux_alpha"
PACK = "BABY_AI_AUTHORITATIVE_HISTORY_CONTINUITY_M2_v0_1"
OUT = Path(__file__).resolve().parents[1] / "artifacts" / "repair" / PACK


def _outdir() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    return OUT


def build_h1() -> tuple[FormationCore, PlasticityExecutor]:
    """Smallest legitimate history H1: a release + a contradiction scar."""
    core = FormationCore(activation_id="m2-h1")
    plast = PlasticityExecutor(receipts=core.receipts, provenance=core.provenance)
    core.ingest(D.experience_safe(core, ITEM))
    core.ingest(D.experience_contradiction(core, ITEM))
    return core, plast


def resolve_history(core: FormationCore, plast: PlasticityExecutor) -> dict[str, Any]:
    """Legitimate resolution: mark the contradiction scar resolved (authority, not erase)."""
    scar = core.scars[0]
    plast.assert_belief(
        belief_id=ITEM, claim=f"{ITEM} is safe", decision="RELEASE", strength=0.8,
        evidence=["governed_release_verified"], reason="reverified under guard",
    )
    rec = plast.resolve(
        belief_id=ITEM, evidence=["governed_release_verified"],
        reason="superseding evidence", scar_id=scar.scar_id,
    )
    return {"scar_id": scar.scar_id, "receipt": rec["receipt"]}


def route(core: FormationCore, plast: PlasticityExecutor) -> dict[str, Any]:
    return core.route_decision(ITEM, plasticity=plast)


def persist(core: FormationCore, plast: PlasticityExecutor, path: Path) -> str:
    snap = ContinuitySnapshot()
    snap.pack(
        operational_self=core.to_dict(),
        plasticity=plast.to_dict(),
        receipts=core.receipts.to_dict(),
        provenance=core.provenance.to_dict(),
        domain={"kind": "m2_fixture", "item": ITEM},
    )
    snap.write(path)
    return snap.semantic_hash


def load(path: Path) -> tuple[FormationCore, PlasticityExecutor, ContinuitySnapshot]:
    snap = ContinuitySnapshot.read(path)
    rcpts = ReceiptLedger.from_dict(snap.receipts)
    prov = ProvenanceLedger.from_dict(snap.provenance, rcpts)
    core = FormationCore.from_dict(snap.operational_self, activation_id="m2-reload",
                                   receipts=rcpts, provenance=prov)
    plast = PlasticityExecutor.from_dict(snap.plasticity)
    plast.receipts = core.receipts
    plast.provenance = core.provenance
    return core, plast, snap


def facts(core: FormationCore, plast: PlasticityExecutor, snap: ContinuitySnapshot | None) -> dict[str, Any]:
    return {
        "memory_ids": sorted(core.memories.keys()),
        "memory_count": len(core.memories),
        "scars": [{"scar_id": s.scar_id, "status": s.status, "memory_ids": list(s.memory_ids)} for s in core.scars],
        "scar_statuses": dict(plast.scar_statuses),
        "lineage_statuses": {k: [v["status"] for v in l] for k, l in plast.lineages.items()},
        "receipt_count": len(core.receipts.entries),
        "receipt_tip": core.receipts.tip,
        "provenance_count": len(core.provenance.records),
        "provenance_components": [r["component"] for r in core.provenance.records],
        "allocator_kind": core.allocator_status.get("kind"),
        "id_continuation": {p: core.ids.counters.get(p, 0) for p in
                            ("mem", "attr", "fog", "scar", "lnk", "replay", "evt")},
        "semantic_hash": snap.semantic_hash if snap else None,
        "integrity_ok": snap.verify_integrity()["ok"] if snap else None,
    }


def _write_trace(phase: str, trace: dict[str, Any]) -> Path:
    p = _outdir() / f"trace_{phase}.json"
    p.write_text(json.dumps(trace, indent=2, sort_keys=True), encoding="utf-8")
    return p


def _route_result(core: FormationCore, plast: PlasticityExecutor) -> dict[str, Any]:
    r = route(core, plast)
    return {"decision": r.get("decision"), "reason": r.get("reason")}


# ----------------------------------------------------------------- phases
def phase_a() -> int:
    core, plast = build_h1()
    r0 = _route_result(core, plast)
    before_path = _outdir() / "before.json"
    sha = persist(core, plast, before_path)
    trace = {
        "phase": "A", "step": "build H1", "route_before_persist": r0,
        "facts": facts(core, plast, None),
        "persisted_semantic_hash": sha,
        "persisted_file": str(before_path),
    }
    _write_trace("A", trace)
    assert r0["decision"] == "HOLD" and r0["reason"] == "contradiction_scar_blocking", r0
    return 0


def phase_b() -> int:
    before_path = _outdir() / "before.json"
    core, plast, snap = load(before_path)
    r_hold = _route_result(core, plast)
    resolve_history(core, plast)
    r_proceed = _route_result(core, plast)
    after_path = _outdir() / "after.json"
    sha = persist(core, plast, after_path)
    trace = {
        "phase": "B", "step": "reload H1 -> resolve",
        "route_after_reload_before_resolve": r_hold,
        "route_after_resolve": r_proceed,
        "scar_still_present": [s.scar_id for s in core.scars],
        "facts": facts(core, plast, snap),
        "persisted_semantic_hash": sha,
        "persisted_file": str(after_path),
    }
    _write_trace("B", trace)
    assert r_hold["decision"] == "HOLD", r_hold
    assert r_proceed["decision"] == "RELEASE", r_proceed
    return 0


def phase_c() -> int:
    after_path = _outdir() / "after.json"
    core, plast, snap = load(after_path)
    r = _route_result(core, plast)
    trace = {
        "phase": "C", "step": "reload H1' -> verify PROCEED + retained history",
        "route": r,
        "scar_still_present": [{"scar_id": s.scar_id, "status": s.status} for s in core.scars],
        "facts": facts(core, plast, snap),
    }
    _write_trace("C", trace)
    assert r["decision"] == "RELEASE", r
    assert core.scars, "original blocking history must survive resolution"
    return 0


# ------------------------------------------------------------ corruption
def _rehash(data: dict[str, Any]) -> dict[str, Any]:
    """Recompute semantic_hash over the (legitimately altered) payload so the
    snapshot is internally consistent — models a state that was *written* with a
    structural gap, not a post-hoc tamper."""
    tmp = ContinuitySnapshot.from_dict(data)
    data["semantic_hash"] = tmp._compute_semantic_hash()
    return data


def _apply_corruption(snap_data: dict[str, Any], case: str) -> tuple[dict[str, Any], bool]:
    """Return (corrupted_data, rehash_flag). rehash=True models a legitimate
    structural gap (hash consistent); rehash=False models post-hoc tampering."""
    data = json.loads(json.dumps(snap_data))
    if case == "C1_missing_provenance":
        data["provenance"] = {"records": []}
        return data, True  # a state genuinely written without provenance
    if case == "C2_tampered_content":
        data["operational_self"]["scars"][0]["status"] = "resolved"
        return data, False  # tamper without re-signing
    if case == "C3_broken_causal_ref":
        data["plasticity"]["scar_statuses"] = {}
        data["plasticity"]["lineages"] = {}
        return data, True  # resolution link legitimately absent
    if case == "C3b_scar_erased":
        data["operational_self"]["scars"] = []
        return data, True  # history erased but "resolved" flag may survive
    if case == "C4_ordering_corruption":
        data["receipts"]["entries"].reverse()
        return data, False  # tamper without re-signing
    raise ValueError(case)


def corrupt(case: str) -> int:
    after_path = _outdir() / "after.json"
    good = ContinuitySnapshot.read(after_path)
    data, rehash = _apply_corruption(good.to_dict(include_observational=False), case)
    if rehash:
        data = _rehash(data)
    else:
        data["semantic_hash"] = good.semantic_hash  # tamper without re-sign
    corrupt_path = _outdir() / f"corrupt_{case}.json"
    corrupt_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    result = {"case": case, "rehash": rehash, "corrupt_file": str(corrupt_path),
              "outcome": None, "detail": ""}
    try:
        snap = ContinuitySnapshot.read(corrupt_path)
        integrity = snap.verify_integrity()
        if not integrity["ok"]:
            result["outcome"] = "HOLD_CONTINUITY_FAILURE"
            result["detail"] = "integrity_mismatch (payload changed without hash re-sign)"
        else:
            core, plast, _snap = load(corrupt_path)
            r = _route_result(core, plast)
            chain_ok, chain_msg = core.receipts.verify_chain()
            if case == "C1_missing_provenance":
                # reconstruction did NOT fail closed: it loaded successfully from
                # operational_self + plasticity with an empty provenance ledger.
                # The ledger is then repopulated with LOAD-TIME bookkeeping only.
                comps = sorted({r["component"] for r in core.provenance.records})
                result["outcome"] = "HOLD_CONTINUITY_FAILURE"
                result["detail"] = (
                    "provenance_missing: reconstruction accepted empty provenance (no fail-closed); "
                    f"reloaded ledger components={comps} (load-time bookkeeping only, no event source binding)"
                )
            elif case == "C3_broken_causal_ref":
                # broken resolution link -> scar reverts to unresolved -> must not PROCEED
                result["outcome"] = "PASS" if r["decision"] != "RELEASE" else "HOLD_CONTINUITY_FAILURE"
                result["detail"] = (f"route={r['decision']} (broken link reverted to non-PROCEED)"
                                    if r["decision"] != "RELEASE"
                                    else f"route={r['decision']} (silently PROCEEDED despite broken link)")
            elif case == "C3b_scar_erased":
                result["outcome"] = "PASS" if r["decision"] != "RELEASE" else "HOLD_CONTINUITY_FAILURE"
                result["detail"] = (f"route={r['decision']} (erased history did NOT silently PROCEED)"
                                    if r["decision"] != "RELEASE"
                                    else f"route={r['decision']} (history erased -> silently PROCEEDED)")
            elif case == "C4_ordering_corruption":
                result["outcome"] = "HOLD_CONTINUITY_FAILURE" if not chain_ok else "PASS"
                result["detail"] = f"receipt_chain_ok={chain_ok} msg={chain_msg}"
            else:
                result["outcome"] = "HOLD_CONTINUITY_FAILURE"
                result["detail"] = "tampering accepted without failure"
    except Exception as e:  # noqa: BLE001
        result["outcome"] = "HOLD_CONTINUITY_FAILURE"
        result["detail"] = f"exception: {e}"
    _write_trace(corrupt_path.stem, result)
    print(json.dumps(result))
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        return 2
    cmd = argv[0]
    if cmd == "phase-a":
        return phase_a()
    if cmd == "phase-b":
        return phase_b()
    if cmd == "phase-c":
        return phase_c()
    if cmd == "corrupt":
        return corrupt(argv[1] if len(argv) > 1 else "C1_missing_provenance")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
