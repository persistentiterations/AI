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


def test_id_continuation_explicit_round_trip(seed_item):
    core = FormationCore(activation_id="t-ice")
    core.ingest(D.experience_safe(core, seed_item))
    payload = core.to_dict()
    assert "id_continuation" in payload
    assert payload["id_continuation"]["version"] == "v0.1"
    # all allocator families travel in the block (touched or not)
    assert set(payload["id_continuation"]["counters"]) == {
        "mem", "attr", "fog", "scar", "lnk", "replay", "evt"}

    loaded = FormationCore.from_dict(payload, activation_id="t-ice-B")
    assert loaded.formation_ready()
    assert loaded.allocator_status["kind"] == "persisted"
    # explicit continuation wins: id sequence resumes exactly
    for p, n in core.ids.counters.items():
        assert loaded.ids.counters[p] == n
    r = loaded.route_decision(seed_item)
    assert r["decision"] == "RELEASE"
    assert "allocator" not in r


def test_id_continuation_legacy_derivation(seed_item):
    core = FormationCore(activation_id="t-icd")
    core.ingest(D.experience_safe(core, seed_item))
    legacy = dict(core.to_dict())
    legacy.pop("id_continuation")  # a pre-continuation serialization

    loaded = FormationCore.from_dict(legacy, activation_id="t-icd-B")
    assert loaded.formation_ready()
    assert loaded.allocator_status["kind"] == "derived_legacy"
    # deterministic: max existing id + 1 per family
    assert loaded.ids.counters["mem"] >= 1
    assert loaded.route_decision(seed_item)["decision"] == "RELEASE"
    # a new formation resumes strictly after every existing id
    mem_id = loaded.ingest(D.experience_safe(core, seed_item))["memory_id"]
    assert all(mid < mem_id for mid in loaded.memories if mid != mem_id)


def test_id_continuation_malformed_rejects_formation(seed_item):
    core = FormationCore(activation_id="t-icm")
    core.ingest(D.experience_safe(core, seed_item))
    payload = core.to_dict()
    # stale counters (below what the collections already require)
    payload["id_continuation"]["counters"]["mem"] = 0

    loaded = FormationCore.from_dict(payload, activation_id="t-icm-B")
    assert not loaded.formation_ready()
    assert loaded.allocator_status["kind"] == "FAIL"
    # read path surfaces what would have happened (EVIDENCE)...
    r = loaded.route_decision(seed_item)
    assert r["decision"] == "HOLD"
    assert r["reason"] == "EVIDENCE"
    assert "loader_rejected_allocator_continuation" in r["evidence"][-1]
    assert "allocator" in r
    # ... and the write path is blocked, never silently self-repaired
    res = loaded.ingest(D.experience_resolving(core, seed_item))
    assert res["error"] == "formation_blocked"
    assert res["decision"] == "HOLD"


def _suffix(family, raw):
    for sep in ("-", "_"):
        m = family + sep
        if raw.startswith(m):
            return int(raw[len(m):])
    raise ValueError(raw)


def test_allocator_continuity_reset_on_load_regression():
    """Motorola-shaped witness: formation survived, allocator identity did not.

    Reproduces the class of defect observed on the handset (~90,073 memories,
    ~100,395 fog objects, 10,322 duplicate fog-id suffixes; deployed bytecode was
    pre-R-001). Under the historical (pre-R-001) load behavior, restored
    collections with an empty id stream re-issue suffix 0 and collide with /
    overwrite inherited ids. Under R-001, allocation continues beyond retained
    authority without collision.
    """
    core = FormationCore(activation_id="witness-src")
    for item in ("flux_alpha", "flux_beta", "dura_gamma"):
        core.ingest(D.experience_safe(core, item))
        core.ingest(D.experience_contradiction(core, item))
    payload = core.to_dict()
    inherited_mem = set(core.memories.keys())
    assert inherited_mem

    # ---- OLD / pre-R-001 reload: collections restored, counters left empty ----
    old = FormationCore(activation_id="witness-old")
    old.memories.update(core.memories)
    old.attractors.update(core.attractors)
    old.fog.extend(core.fog)
    old.links.extend(core.links)
    old.scars.extend(core.scars)
    old.routes.extend(core.routes)
    # ids.counters is still {} -> the reset-on-load defect
    old_fog_before = len(old.fog)
    new_id_old = old.ingest(D.experience_safe(old, "flux_alpha"))["memory_id"]
    assert new_id_old in inherited_mem, "pre-R-001 re-issued an inherited id (collision)"
    # append-only fog list witnesses the reset: duplicate suffix accumulated
    old_fog_suffixes = [f.fog_id for f in old.fog]
    assert len(set(old_fog_suffixes)) < len(old_fog_suffixes), (
        "pre-R-001 produced duplicate fog-id suffixes (append-only witness)")
    assert len(old.fog) > old_fog_before

    # ---- R-001 reload via from_dict: continuation established, no collision ----
    loaded = FormationCore.from_dict(payload, activation_id="witness-r001")
    assert loaded.formation_ready()
    assert loaded.allocator_status["kind"] == "persisted"
    new_id = loaded.ingest(D.experience_safe(loaded, "flux_alpha"))["memory_id"]
    assert new_id not in inherited_mem, "R-001 must not collide with inherited ids"
    max_suffix = max(_suffix("mem", mid) for mid in inherited_mem)
    assert _suffix("mem", new_id) > max_suffix, (
        "R-001 must continue strictly beyond retained authority")
    # no duplicate fog suffixes after R-001 continuation
    loaded_fog = [f.fog_id for f in loaded.fog]
    assert len(set(loaded_fog)) == len(loaded_fog), "R-001 must not duplicate fog ids"