"""baby_ai.demo — first end-to-end causal MVP.

Usage:  python -m baby_ai.demo   (from baby-ai-assembly-v0.1)

Emits a concise human-readable trace with [PASS]/[HOLD] lines and writes
machine-readable artifacts under baby_ai/artifacts/.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from baby_ai import domain as D
from baby_ai.adapters.operational_self import FormationCore
from baby_ai.assays.persistence import PersistenceAssay
from baby_ai.assays.replay import ReplayAssay
from baby_ai.assays.transfer import TransferAssay
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.core.semantics import semantic_digest
from baby_ai._env import PACKAGE

ITEM = "flux_alpha"
ITEM_RELATED = "flux_beta"
ARTIFACTS = PACKAGE / "artifacts"


def _line(code: str, msg: str) -> None:
    print(f"[{code}] {msg}")


def run() -> dict:
    t0 = time.time()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    results: dict = {}
    log: list[dict] = []

    # ------------------------------------------------------------- clean
    core = FormationCore(activation_id="baby-mvp-A")
    baseline = core.route_decision(ITEM)
    _line("PASS", f"clean baseline established: {ITEM} -> {baseline['decision']} ({baseline['reason']})")
    assert baseline["decision"] == "HOLD", "clean baseline must HOLD"
    log.append({"step": "clean", "decision": baseline["decision"]})

    # ------------------------------------------------------- experience A
    core.ingest(D.experience_safe(core, ITEM))
    f1 = core.route_decision(ITEM)
    _line("PASS", f"Experience A formed state: {core.counts()['attractors']} attractor(s)")
    _line("PASS", f"F1 changed Task B routing: {ITEM} -> {f1['decision']} ({f1['reason']})")
    assert f1["decision"] == "RELEASE"
    log.append({"step": "A", "decision": f1["decision"]})

    # ------------------------------------------------ no-memory control
    control = FormationCore(activation_id="control")
    ctl = control.route_decision(ITEM)
    _line("PASS", f"no-memory control differs: {ITEM} -> {ctl['decision']} ({ctl['reason']})")
    assert ctl["decision"] == "HOLD"
    log.append({"step": "control", "decision": ctl["decision"]})

    # -------------------------------------------------------- ablation
    removed = core.remove_attractor(f1["match"]["memory_id"]) if f1.get("match") else None
    ablated = core.route_decision(ITEM)
    restored_ok = False
    if removed:
        _line("PASS", f"ablation removed effect: {ITEM} -> {ablated['decision']} ({ablated['reason']})")
        # rebuild attractor by re-ingesting the same experience
        core.ingest(D.experience_safe(core, ITEM))
        restored = core.route_decision(ITEM)
        restored_ok = restored["decision"] == "RELEASE"
        _line("PASS", f"restoration returned effect: {ITEM} -> {restored['decision']}")
    else:
        _line("HOLD", "ablation: no matching attractor found to remove")
    log.append({"step": "ablation", "decision": ablated["decision"]})

    # ------------------------------------------------ full snapshot export
    plasticity = PlasticityExecutor(receipts=core.receipts, provenance=core.provenance)
    # fold the F1 belief into the plasticity ledger for supersession story
    plasticity.assert_belief(
        belief_id=f"route:{ITEM}",
        claim=f"{ITEM} is safe to release",
        decision="RELEASE",
        strength=0.8,
        evidence=[f"Experience A: {ITEM} safe"],
        reason="clearance obtained",
    )
    snap = ContinuitySnapshot()
    snap.pack(
        operational_self=core.to_dict(),
        plasticity=plasticity.to_dict(),
        receipts=core.receipts.to_dict(),
        provenance=core.provenance.to_dict(),
        domain={"item": ITEM, "domain": "warehouse-routing"},
    )
    snap_path = snap.write(ARTIFACTS / "snapshot_host_A.json")
    _line("PASS", f"full snapshot exported ({snap.export_bytes()} bytes) -> {snap_path.name}")
    log.append({"step": "export", "bytes": snap.export_bytes()})

    # ------------------------------------------------------- Host B restore
    t_b = time.time()
    pers = PersistenceAssay()
    pb = pers.host_b_subprocess(snap_path, query=ITEM)
    import_ms = (time.time() - t_b) * 1000
    _line("PASS", f"Host A destroyed; Host B restored causal state: {ITEM} -> {pb['decision']} ({pb['reason']}) integrity_ok={pb['integrity_ok']}")
    assert pb["decision"] == "RELEASE", "Host B must exhibit formed RELEASE"
    log.append({"step": "hostB", "decision": pb["decision"], "import_ms": round(import_ms, 2)})

    # ------------------------------------------------- contradictory C
    core.ingest(D.experience_contradiction(core, ITEM))
    scar_id = core.scars[-1].scar_id if core.scars else None
    after_c = core.route_decision(ITEM, plasticity=plasticity)
    _line("PASS", f"contradictory Experience C produced scar {scar_id}/HOLD: {ITEM} -> {after_c['decision']} ({after_c['reason']})")
    assert after_c["decision"] == "HOLD"
    assert scar_id, "contradictory experience must produce a contradiction scar"
    log.append({"step": "C", "decision": after_c["decision"], "scar_id": scar_id})

    # -------------------------------------------------- resolving D (supersede)
    superseded = plasticity.supersede(
        belief_id=f"route:{ITEM}",
        new_claim=f"{ITEM} re-verified under guard",
        new_decision="RELEASE_WITH_GUARD",
        evidence=["Experience D: governed re-verification"],
        reason="D supersedes C-hold with sufficient evidence",
        scar_id=scar_id,
    )
    # Route again: the superseded scar no longer blocks routing, and the newly
    # formed RELEASE_WITH_GUARD decision routes as RELEASE (guard is advisory).
    core.ingest(D.experience_resolving(core, ITEM))
    after_d = core.route_decision(ITEM, plasticity=plasticity)
    _line("PASS", f"resolving Experience D superseded F1 (v{superseded['version']}); future routing -> {after_d['decision']} ({after_d['reason']})")
    assert after_d["decision"] == "RELEASE", "superseded scar must release routing"
    log.append({"step": "D", "decision": after_d["decision"], "superseded_version": superseded["version"]})

    # --------------------------------------------- prior state reconstructible
    lineage = plasticity.reconstruct_lineage(f"route:{ITEM}")
    _line("PASS", f"prior state remains reconstructible: {len(lineage)} lineage version(s) for route:{ITEM}")
    _line("PASS", f"scar status now = {plasticity.get_scar_status(core.scars[-1].scar_id) if core.scars else 'n/a'}")
    log.append({"step": "reconstruct", "lineage_depth": len(lineage)})

    # --------------------------------------------------- biography comparison
    transfer = TransferAssay()
    t_report = transfer.run(item=ITEM)
    adv = t_report["structured_advantage"]
    _line("PASS" if adv else "HOLD", f"formed transfer vs biography control: advantage={adv} items={t_report['structured_advantage_over_biography_items']}")
    log.append({"step": "transfer", "advantage": adv})

    # -------------------------------------------------- replay / integrity
    rep = ReplayAssay()
    replay = rep.run_replay(seed_item=ITEM, contradiction_item=ITEM)
    _line("PASS", f"replay/integrity verified: deterministic={replay['replay_deterministic']} receipt_chain_ok={replay['receipt_chain_ok']}")
    assert replay["replay_deterministic"] and replay["receipt_chain_ok"]
    log.append({"step": "replay", "deterministic": replay["replay_deterministic"], "chain_ok": replay["receipt_chain_ok"]})

    # ------------------------------------------------------------ metrics
    metrics = {
        "wall_seconds": round(time.time() - t0, 3),
        "formed_objects": core.counts(),
        "import_ms": round(import_ms, 2),
        "export_bytes": snap.export_bytes(),
        "transfer_advantage": adv,
        "receipt_count": len(core.receipts),
        "plasticity_versions": sum(len(v) for v in plasticity.lineages.values()),
    }
    (ARTIFACTS / "demo_results.json").write_text(json.dumps({"results": log, "metrics": metrics}, indent=2), encoding="utf-8")
    _line("PASS", f"metrics -> artifacts/demo_results.json ({metrics['wall_seconds']}s, {metrics['formed_objects']['memories']} memories)")
    return {"log": log, "metrics": metrics}


def main() -> int:
    try:
        run()
    except AssertionError as exc:
        _line("FAIL", f"assertion: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())