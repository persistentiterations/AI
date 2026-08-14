"""Formation + formation-causality + ablation tests."""

from baby_ai import domain as D
from baby_ai.adapters.operational_self import FormationCore


def test_clean_baseline_is_hold(seed_item):
    core = FormationCore(activation_id="t-clean")
    r = core.route_decision(seed_item)
    assert r["decision"] == "HOLD"
    assert r["reason"] == "no_formed_memory"


def test_experience_a_changes_routing(seed_item):
    core = FormationCore(activation_id="t-A")
    core.ingest(D.experience_safe(core, seed_item))
    r = core.route_decision(seed_item)
    assert r["decision"] == "RELEASE"
    assert r["reason"].startswith("formed_decision")


def test_no_memory_control_differs(seed_item):
    formed = FormationCore(activation_id="t-A2")
    formed.ingest(D.experience_safe(formed, seed_item))
    blank = FormationCore(activation_id="t-B2")
    f_dec = formed.route_decision(seed_item)["decision"]
    b_dec = blank.route_decision(seed_item)["decision"]
    assert f_dec == "RELEASE" and b_dec == "HOLD"
    assert f_dec != b_dec


def test_formation_ablation_restoration(seed_item):
    core = FormationCore(activation_id="t-abl")
    core.ingest(D.experience_safe(core, seed_item))
    before = core.route_decision(seed_item)
    assert before["decision"] == "RELEASE"
    mem_id = before["match"]["memory_id"]
    removed = core.remove_attractor(mem_id)
    assert removed is not None
    ablated = core.route_decision(seed_item)
    assert ablated["decision"] == "HOLD"
    # restore by forming the same experience again
    core.ingest(D.experience_safe(core, seed_item))
    restored = core.route_decision(seed_item)
    assert restored["decision"] == "RELEASE"


def test_deterministic_state_transition_repeat(seed_item):
    a = FormationCore(activation_id="t-det")
    b = FormationCore(activation_id="t-det")
    for core in (a, b):
        core.ingest(D.experience_safe(core, seed_item))
        core.ingest(D.experience_contradiction(core, seed_item))
        core.ingest(D.experience_resolving(core, seed_item))
    # full semantic equality across two independently-run cores
    assert a.to_dict() == b.to_dict()
    assert a.route_decision(seed_item)["decision"] == b.route_decision(seed_item)["decision"]