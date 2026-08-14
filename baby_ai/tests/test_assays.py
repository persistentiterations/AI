"""Gap B (persistence/Host B) + Gap C (transfer) + replay integrity tests."""

from baby_ai import domain as D
from baby_ai.adapters.operational_self import FormationCore
from baby_ai.assays.persistence import PersistenceAssay
from baby_ai.assays.replay import ReplayAssay
from baby_ai.assays.transfer import TransferAssay


def test_host_b_restores_formed_decision(artifacts_dir, seed_item):
    pers = PersistenceAssay()
    path = artifacts_dir / "snapshot_host_A.json"
    core_a, snap, meta = pers.host_a_form_and_export(item=seed_item, snapshot_path=path)
    before = meta["before_decision"]["decision"]
    host_b = pers.host_b_subprocess(path, query=seed_item)
    assert host_b["integrity_ok"] is True
    assert host_b["decision"] == before == "RELEASE"
    assert host_b["decision"] != "HOLD"
    # Host B re-derived the decision from the file alone (fresh interpreter)
    assert host_b["reason"].startswith("formed_decision")


def test_transfer_structured_beats_biography(seed_item):
    assay = TransferAssay()
    rep = assay.run(item=seed_item)
    # STRUCTURED routed at least one RELEASE that plain-prose BIOGRAPHY did not
    assert rep["structured_advantage"] is True
    assert seed_item in rep["structured_advantage_over_biography_items"]
    # FLAT conclusion string alone cannot form a RELEASE decision
    assert rep["conditions"]["FLAT"][seed_item] == "HOLD"


def test_replay_deterministic_and_chain_intact(seed_item):
    rep = ReplayAssay().run_replay(seed_item=seed_item, contradiction_item=seed_item)
    assert rep["replay_deterministic"] is True
    assert rep["receipt_chain_ok"] is True
    assert rep["action_seq_A"] == rep["action_seq_B"]
    # final replay state is RELEASE (scar superseded nothing here, but resolve re-forms)
    assert rep["trace"][0]["decision"] == "RELEASE"
    assert rep["trace"][1]["decision"] == "HOLD"


def test_reverse_reconstruct_lineage(seed_item):
    rep = ReplayAssay().reverse_reconstruct(seed_item=seed_item, contradiction_item=seed_item)
    assert len(rep["lineage"]) == 3  # safe, contradiction, resolve
    assert rep["formed_objects"]["memories"] >= 3


def test_strict_clean_host_full_cycle(artifacts_dir, seed_item, related_item):
    """Strict Gap B: Host A terminates; fresh Host B does related-query/ablate/restore."""
    pers = PersistenceAssay()
    path = artifacts_dir / "strict_hostA.json"
    r = pers.strict_clean_host_run(item=seed_item, related=related_item, snapshot_path=path)
    assert r["integrity_ok"] is True
    assert r["related_decision"] == "RELEASE"
    assert r["effect_changed_on_ablate"] is True
    assert r["ablated_decision"] == "HOLD"
    assert r["effect_returned_on_restore"] is True
    assert r["restored_decision"] == "RELEASE"
    assert r["full_cycle_ok"] is True


def test_transfer_control_comparison(seed_item):
    """Gap C: FORMED vs equivalent words (BIOGRAPHY/FLAT) on the same related tasks."""
    from baby_ai.assays.transfer_control import TransferControlAssay

    rep = TransferControlAssay().run(item=seed_item)
    v = rep["verdict"]
    # formed state routes a consequence equivalent words do not
    assert v["formed_release"] is True
    assert v["biography_release"] is False
    assert v["flat_release"] is False
    assert v["advantage_over_biography"] is True
    assert v["advantage_over_flat"] is True
    # exported formed state preserves the effect on a fresh import
    assert v["exported_release"] is True
    assert v["transfer_preserved"] is True
    # the related (withheld) task inherits the formed consequence
    assert rep["related_item_decisions"]["FORMED"] == "RELEASE"
    # correction behavior exists only where there is a formed decision to correct
    assert rep["correction_sequences"]["FORMED"] == ["RELEASE", "HOLD", "RELEASE"]
    assert rep["correction_sequences"]["BIOGRAPHY"] == ["HOLD", "HOLD", "HOLD"]