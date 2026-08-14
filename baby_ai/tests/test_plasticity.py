"""Plasticity / corrigibility tests (Gap A)."""

import pytest

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.core.receipts import ReceiptLedger


def _core_with_belief(belief_id="blf:flux"):
    receipts = ReceiptLedger()
    core = FormationCore(activation_id="t-plast", receipts=receipts)
    plast = PlasticityExecutor(receipts=receipts)
    v1 = plast.assert_belief(
        belief_id=belief_id,
        claim="flux_alpha is safe",
        decision="RELEASE",
        strength=0.8,
        evidence=["A"],
        reason="A supports X",
    )
    return core, plast, v1


def test_hierarchy_no_deletion():
    core, plast, v1 = _core_with_belief()
    v2 = plast.weaken(belief_id="blf:flux", evidence=["doubt"], reason="C weakens", amount=0.2)
    lineage = plast.lineage("blf:flux")
    assert len(lineage) == 2
    assert lineage[0]["identity"] == v1["identity"]
    assert lineage[1]["identity"] == v2["identity"]
    assert v1 not in lineage[0].values()  # v1 immutable record remains
    assert lineage[0]["status"] == "active"
    assert lineage[1]["status"] == "weak"


def test_supersession_preserves_reconstructibility():
    core, plast, v1 = _core_with_belief()
    v2 = plast.supersede(
        belief_id="blf:flux",
        new_claim="flux re-verified under guard",
        new_decision="RELEASE_WITH_GUARD",
        evidence=["D"],
        reason="D supersedes scrap",
        scar_id="scar-0001",
    )
    chain_ok, _ = plast.receipts.verify_chain()
    assert chain_ok
    assert plast.get_scar_status("scar-0001") == "superseded"
    reconstructed = plast.reconstruct_lineage("blf:flux")
    # reverse walk: v2 then v1
    assert reconstructed[0]["identity"] == v2["identity"]
    assert reconstructed[-1]["identity"] == v1["identity"]
    assert reconstructed[-1]["supersedes"] is None


def test_hold_release_cycle():
    core, plast, v1 = _core_with_belief()
    # release on a non-held belief is refused (invariant: HOLD is the only path in)
    with pytest.raises(ValueError):
        plast.release(belief_id="blf:flux", evidence=[], reason="release of non-held")
    held = plast.hold(belief_id="blf:flux", evidence=["C-contradicts"], reason="insufficient to replace")
    assert held["status"] == "held"
    assert held["decision"] == "HOLD"
    # while held, the belief is NOT actionable (latest version controls)
    assert plast.active("blf:flux") is None
    assert plast.current("blf:flux")["decision"] == "HOLD"
    # sufficient evidence releases it back to active
    released = plast.release(belief_id="blf:flux", evidence=["D-sufficient"], reason="evidence sufficient")
    assert released["status"] == "active"
    assert plast.active("blf:flux")["identity"] == released["identity"]
    # full provenance retained: nothing was erased, all versions present
    assert len(plast.lineage("blf:flux")) == 3


def test_quarantine_invalidate_reactivate():
    core, plast, v1 = _core_with_belief()
    q = plast.quarantine(belief_id="blf:flux", evidence=["suspicious"], reason="quarantine")
    assert q["status"] == "quarantined"
    i = plast.invalidate(belief_id="blf:flux", evidence=["broken"], reason="invalid")
    assert i["status"] == "invalidated" and i["decision"] == "INVALID"
    r = plast.reactivate(belief_id="blf:flux", claim="flux again safe", decision="RELEASE", evidence=["new"], reason="reactivate")
    assert r["status"] == "active"
    reconstruct = plast.reconstruct_lineage("blf:flux")
    assert len(reconstruct) == len(plast.lineage("blf:flux"))


def test_old_active_version_does_not_resurrect_under_hold():
    """Regression guard: latest-version-controlled active() must not fall back.

    old state = ACTIVE / RELEASE ; new version = HOLD (and separately weak).
    A query on the belief must NOT see the old ACTIVE/RELEASE version resurrect.
    Only an explicit lifecycle step (resolve/supersede/release) may restore action.
    """
    core, plast, v1 = _core_with_belief()
    assert plast.active("blf:flux")["decision"] == "RELEASE"

    # HOLD on top of an ACTIVE/RELEASE version: nothing resurrects
    plast.hold(belief_id="blf:flux", evidence=["C-contradicts"], reason="C hold")
    assert plast.active("blf:flux") is None, "old ACTIVE/RELEASE must not resurrect under HOLD"
    assert plast.current("blf:flux")["decision"] == "HOLD"

    # weak also suspends (weak != actionable)
    v = plast.release(belief_id="blf:flux", evidence=["D-sufficient"], reason="release with evidence")
    assert plast.active("blf:flux")["identity"] == v["identity"]
    plast.weaken(belief_id="blf:flux", evidence=["doubt"], reason="weak", amount=0.2)
    assert plast.active("blf:flux") is None, "weakened current version must suspend action"

    # routing changes ONLY through the explicit lifecycle
    v3 = plast.supersede(
        belief_id="blf:flux",
        new_claim="flux re-verified",
        new_decision="RELEASE_WITH_GUARD",
        evidence=["E-reverified"],
        reason="supersede over weakened state",
    )
    assert plast.active("blf:flux")["identity"] == v3["identity"]
    assert plast.active("blf:flux")["decision"] == "RELEASE_WITH_GUARD"


def test_scar_status_write_through_adapter(seed_item):
    """The exact gap-A guarantee: no organ deletion; scar status change recorded."""
    from baby_ai import domain as D

    core = FormationCore(activation_id="t-scar")
    receipts = core.receipts
    plast = PlasticityExecutor(receipts=receipts, provenance=core.provenance)
    # a formed RELEASE decision the scar can block and unblock
    core.ingest(D.experience_safe(core, seed_item))
    assert core.route_decision(seed_item, plasticity=plast)["decision"] == "RELEASE"
    # contradictory event with contradiction tag + 2 claims -> qualified detector scar
    res = core.ingest(core.make_event(
        raw_summary=f"{seed_item} is NOT safe. Similarity is not identity.",
        structured_summary="contradiction",
        claims=[f"{seed_item} is unsafe", "similarity is not identity"],
        decisions=["HOLD"],
        tags=[f"contradiction"],
        guard_status="HOLD",
    ))
    assert res["scar_ids"], "qualified detector should have produced a scar given contradiction tag + 2 claims"
    scar_id = res["scar_ids"][0]
    # executor sees the scar and the routing layer obeys it as an unresolved block
    assert plast.get_scar_status(scar_id) == "unresolved"
    assert core.route_decision(seed_item, plasticity=plast)["decision"] == "HOLD"
    # supersede clears the block: status writes through the adapter, routing flips
    plast.assert_belief(
        belief_id=f"route:{seed_item}",
        claim=f"{seed_item} is safe to release",
        decision="RELEASE",
        strength=0.8,
        evidence=["A"],
        reason="clearance",
    )
    plast.supersede(
        belief_id=f"route:{seed_item}",
        new_claim=f"{seed_item} re-verified",
        new_decision="RELEASE_WITH_GUARD",
        evidence=["D"],
        reason="D resolves",
        scar_id=scar_id,
    )
    assert plast.get_scar_status(scar_id) == "superseded"
    assert core.route_decision(seed_item, plasticity=plast)["decision"] == "RELEASE"
    # the underlying memory records still exist (nothing erased)
    assert len(core.memories) >= 2