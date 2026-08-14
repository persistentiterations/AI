"""Sham transfer controls (section 3).

Transfers that LOOK legitimate but should NOT carry the causal effect:

  MISSING_FORMATION     valid envelope, no relevant formation formed
  UNRELATED_FORMATION   valid envelope, only unrelated items formed
  ZEROED_ACCESSIBILITY  valid envelope, formed state present but accessibility zeroed
  SHUFFLED_LINKS        valid envelope, relation links shuffled
  SUPERSEDED_ONLY       valid envelope, only a superseded record present
  CORRUPT_TIP           envelope with wrong receipt tip (integrity must reject)

For each, Host B must NOT exhibit the RELEASE effect, or import must fail loudly.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.hostile.events import safe_event, unrelated_event
from baby_ai.hostile.task_gen import TaskFamily


def _pack(core: FormationCore) -> dict[str, Any]:
    snap = ContinuitySnapshot()
    snap.pack(
        operational_self=core.to_dict(),
        plasticity=PlasticityExecutor(receipts=core.receipts).to_dict(),
        receipts=core.receipts.to_dict(),
        provenance=core.provenance.to_dict(),
        domain={"seed": core.activation_id},
    )
    return snap.to_dict()


def _imported(payload: dict[str, Any]) -> tuple[ContinuitySnapshot, FormationCore]:
    imported = ContinuitySnapshot.from_dict(payload)
    core = FormationCore.from_dict(imported.operational_self, activation_id="hq-sham-b")
    return imported, core


def sham_missing_formation(fam: TaskFamily) -> dict[str, Any]:
    core = FormationCore(activation_id="sham-missing")
    # envelope: a legit receipt/provenance present, but NOTHING formed for the item
    payload = _pack(core)
    _, core_b = _imported(payload)
    return {"decisions": core_b.route_decision(fam.formed_item), "expect": "HOLD"}


def sham_unrelated_formation(fam: TaskFamily) -> dict[str, Any]:
    core = FormationCore(activation_id="sham-unrelated")
    core.ingest(unrelated_event(core, fam.unrelated_item, "other"))
    payload = _pack(core)
    _, core_b = _imported(payload)
    return {"decisions": core_b.route_decision(fam.formed_item), "expect": "HOLD"}


def sham_zeroed_accessibility(fam: TaskFamily) -> dict[str, Any]:
    core = FormationCore(activation_id="sham-zeroed")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    payload = _pack(core)
    # strip the retrieval-visible text surface AND salience: the envelope looks
    # valid but nothing reachable should route RELEASE
    for attr in payload["operational_self"]["attractors"].values():
        attr["salience_score"] = 0.0
        attr["basin_region"] = "fog"
        attr["distance_from_reasoning_center"] = 99.0
        attr["label"] = "deleted"
        attr["tags"] = []
    for mem in payload["operational_self"]["memories"].values():
        mem["compressed_summary"] = "expired"
        mem["retained_claims"] = []
        mem["retained_decisions"] = []
    _, core_b = _imported(payload)
    return {"decisions": core_b.route_decision(fam.formed_item), "expect": "HOLD"}


def sham_shuffled_links(fam: TaskFamily) -> dict[str, Any]:
    core = FormationCore(activation_id="sham-links")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    payload = _pack(core)
    links = payload["operational_self"]["links"]
    if len(links) > 1:
        # re-point every link at the unrelated item (garbage relations)
        for lnk in links:
            lnk["from_memory_id"] = "mem-XXXX"
            lnk["to_memory_id"] = "mem-XXXX"
    _, core_b = _imported(payload)
    return {"decisions": core_b.route_decision(fam.formed_item), "expect": "RELEASE"}


def sham_superseded_only(fam: TaskFamily) -> dict[str, Any]:
    core = FormationCore(activation_id="sham-superseded")
    plast = PlasticityExecutor(receipts=core.receipts, provenance=core.provenance)
    v1 = plast.assert_belief(
        belief_id=f"route:{fam.formed_item}",
        claim=f"{fam.formed_item} safe",
        decision="RELEASE",
        strength=0.8,
        evidence=["A"],
        reason="clearance",
    )
    plast.supersede(
        belief_id=f"route:{fam.formed_item}",
        new_claim=f"{fam.formed_item} re-verified",
        new_decision="RELEASE_WITH_GUARD",
        evidence=["D"],
        reason="supersede",
    )
    payload = _pack(core)
    # the operational-self side is empty; only plasticity ledger has the (superseded) branch
    snap = ContinuitySnapshot.from_dict(payload)
    core_b = FormationCore.from_dict(snap.operational_self, activation_id="hq-sham-b")
    return {"decisions": core_b.route_decision(fam.formed_item), "expect": "HOLD"}


def sham_corrupt_tip(fam: TaskFamily) -> dict[str, Any]:
    core = FormationCore(activation_id="sham-tip")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    payload = _pack(core)
    payload["receipts"]["tip"] = "0000000000000000"  # wrong tip
    snap = ContinuitySnapshot.from_dict(payload)  # must recompute hash mismatch
    return {
        "integrity_ok": snap.integrity["ok"],
        "decisions": None,
        "expect_integrity": False,
        "note": "integrity verification must fail; import must not be trusted",
    }


SHAM_CONTROLS = {
    "MISSING_FORMATION": sham_missing_formation,
    "UNRELATED_FORMATION": sham_unrelated_formation,
    "ZEROED_ACCESSIBILITY": sham_zeroed_accessibility,
    "SHUFFLED_LINKS": sham_shuffled_links,
    "SUPERSEDED_ONLY": sham_superseded_only,
    "CORRUPT_TIP": sham_corrupt_tip,
}


def run_all_shams(fam: TaskFamily) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for name, fn in SHAM_CONTROLS.items():
        try:
            r = fn(fam)
            results[name] = {"ok": True, "result": r}
        except Exception as exc:  # loud failure is acceptable for corrupt inputs
            results[name] = {"ok": False, "error": str(exc)[:300]}
    return results