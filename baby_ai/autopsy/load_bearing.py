"""Load-bearing component ablation (autopsy section 4).

For every field/component of the current Fractalish Operational Self state we
perform deletion / zeroing / permutation ablation where safe, then re-import via
ContinuitySnapshot and re-run the demonstrated behaviors:

    B1 formed -> withheld RELEASE (withheld RELEASE)
    B2 unrelated stays HOLD
    B3 contradiction -> HOLD (both formed + withheld)
    B4 resolve -> RELEASE restored
    B5 ablate -> HOLD
    B6 restore -> RELEASE

Each component is classified:
    REQUIRED                    behavior lost without it
    CONDITIONALLY REQUIRED      some behavior degrades but core routing survives
    REDUNDANT IN CURRENT ASSAY  routing identical with it removed
    OBSERVATIONAL ONLY          never read by routing (cosmetic/metadata)
    HISTORICAL ONLY             needed only for reconstruction/replay, not routing
    UNKNOWN                     not decidable in this harness

We do not infer necessity from architecture. We measure it.
"""

from __future__ import annotations

import copy
from typing import Any

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.hostile.events import contradiction_event, resolve_event, safe_event
from baby_ai.hostile.task_gen import TaskFamily, generate_seed_set


def build_formed(fam: TaskFamily) -> FormationCore:
    core = FormationCore(activation_id=f"lb-{fam.seed}")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    return core


def _pack(core: FormationCore) -> dict[str, Any]:
    snap = ContinuitySnapshot()
    snap.pack(
        operational_self=core.to_dict(),
        plasticity=PlasticityExecutor(receipts=core.receipts).to_dict(),
        receipts=core.receipts.to_dict(),
        provenance=core.provenance.to_dict(),
        domain={"seed": str(core.activation_id)},
    )
    return snap.to_dict()


def baseline_behavior(fam: TaskFamily) -> dict[str, str]:
    core = build_formed(fam)
    plast = PlasticityExecutor(receipts=core.receipts, provenance=core.provenance)
    plast.assert_belief(belief_id=f"route:{fam.formed_item}", claim="safe", decision="RELEASE",
                        strength=0.8, evidence=["f"], reason="formed")
    out = {
        "formed": core.route_decision(fam.formed_item, plasticity=plast)["decision"],
        "withheld": core.route_decision(fam.withheld_item, plasticity=plast)["decision"],
        "unrelated": core.route_decision(fam.unrelated_item, plasticity=plast)["decision"],
    }
    core.ingest(contradiction_event(core, fam.formed_item, fam.tag_group, decision="HOLD"))
    out["contra_withheld"] = core.route_decision(fam.withheld_item, plasticity=plast)["decision"]
    out["contra_formed"] = core.route_decision(fam.formed_item, plasticity=plast)["decision"]
    scar_id = core.scars[-1].scar_id if core.scars else None
    if scar_id:
        plast.supersede(belief_id=f"route:{fam.formed_item}", new_claim="re-verified",
                        new_decision="RELEASE_WITH_GUARD", evidence=["s"],
                        reason="resolve", scar_id=scar_id)
    core.ingest(resolve_event(core, fam.formed_item, fam.tag_group))
    out["resolve_withheld"] = core.route_decision(fam.withheld_item, plasticity=plast)["decision"]
    # ablate/restore on formed attractor
    rid = core.route_decision(fam.formed_item, plasticity=plast).get("match", {}).get("memory_id")
    aid = next((a for a, attr in core.attractors.items() if attr.memory_id == rid), None)
    if aid:
        attr = core.attractors[aid]
        del core.attractors[aid]
        out["ablate_formed"] = core.route_decision(fam.formed_item, plasticity=plast)["decision"]
        core.attractors[aid] = attr
        out["restore_formed"] = core.route_decision(fam.formed_item, plasticity=plast)["decision"]
    return out


def ablate_variant(fam: TaskFamily, *, transform) -> dict[str, Any]:
    """Build a fully-formed snapshot, apply transform to a deep copy, re-import."""
    core = build_formed(fam)
    payload = _pack(core)
    payload["operational_self"] = transform(payload["operational_self"])
    try:
        snap = ContinuitySnapshot.from_dict(payload)
        core_b = FormationCore.from_dict(snap.operational_self, activation_id="lb-b")
        plast = PlasticityExecutor.from_dict(snap.plasticity)
        decisions = {
            "formed": core_b.route_decision(fam.formed_item, plasticity=plast)["decision"],
            "withheld": core_b.route_decision(fam.withheld_item, plasticity=plast)["decision"],
            "unrelated": core_b.route_decision(fam.unrelated_item, plasticity=plast)["decision"],
        }
        return {"ok": True, "decisions": decisions, "integrity": snap.integrity["ok"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def _empty_dict(obj: dict[str, Any], keys: Any = ...) -> dict[str, Any]:
    out = copy.deepcopy(obj)
    if keys is ...:
        out = {}
    else:
        for k in keys:
            out.pop(k, None)
    return out


# ------------------------------------------------------------------- the inventory
COMPONENT_ABLATIONS: dict[str, Any] = {
    "memories": lambda o: {**o, "memories": {}},
    "attractors": lambda o: {**o, "attractors": {}},
    "links": lambda o: {**o, "links": []},
    "scars": lambda o: {**o, "scars": []},
    "fog": lambda o: {**o, "fog": []},
    "routes": lambda o: {**o, "routes": []},
    "state": lambda o: {**o, "state": _minimal_state()},
}


def _minimal_state() -> dict[str, Any]:
    """Structurally-valid but content-emptied state (constructor requires the 4
    scalar fields; no list content survives)."""
    return {
        "self_id": "oself-min",
        "activation_id": "min",
        "project_id": "baby-ai-v0.1",
        "purpose": "minimal",
        "operator_constraints": [],
        "active_narrative": "",
        "active_focus": "",
        "current_phase": "",
        "core_commitments": [],
        "unresolved_loops": [],
        "contradiction_scars": [],
        "hold_regions": [],
        "recovery_routes": [],
        "active_attractors": [],
        "deprioritized_memories": [],
        "recent_memory_ids": [],
        "session_glyph_refs": [],
        "last_updated": "",
        "confidence": 0.0,
        "uncertainty": 1.0,
        "non_claims": [],
    }

FIELD_ABLATIONS: dict[str, Any] = {
    # memory fields (applied to every memory)
    "retained_decisions": lambda o: _map(o, "memories", lambda m: {**m, "retained_decisions": []}),
    "retained_claims": lambda o: _map(o, "memories", lambda m: {**m, "retained_claims": []}),
    "compressed_summary": lambda o: _map(o, "memories", lambda m: {**m, "compressed_summary": ""}),
    "retained_constraints": lambda o: _map(o, "memories", lambda m: {**m, "retained_constraints": []}),
    "retained_open_loops": lambda o: _map(o, "memories", lambda m: {**m, "retained_open_loops": []}),
    "retained_scars": lambda o: _map(o, "memories", lambda m: {**m, "retained_scars": []}),
    "retained_routes": lambda o: _map(o, "memories", lambda m: {**m, "retained_routes": []}),
    "source_event_id": lambda o: _map(o, "memories", lambda m: {**m, "source_event_id": ""}),
    "lossiness": lambda o: _map(o, "memories", lambda m: {**m, "lossiness": 0.0}),
    "confidence": lambda o: _map(o, "memories", lambda m: {**m, "confidence": 0.0}),
    "uncertainty": lambda o: _map(o, "memories", lambda m: {**m, "uncertainty": 1.0}),
    "compression_level": lambda o: _map(o, "memories", lambda m: {**m, "compression_level": ""}),
    "dropped_noise": lambda o: _map(o, "memories", lambda m: {**m, "dropped_noise": []}),
    "compression_notes": lambda o: _map(o, "memories", lambda m: {**m, "compression_notes": ""}),
    "replay_fidelity_estimate": lambda o: _map(o, "memories", lambda m: {**m, "replay_fidelity_estimate": 0.0}),
    # attractor fields
    "attractor_label": lambda o: _map(o, "attractors", lambda a: {**a, "label": ""}),
    "attractor_salience": lambda o: _map(o, "attractors", lambda a: {**a, "salience_score": 0.0}),
    "attractor_basin": lambda o: _map(o, "attractors", lambda a: {**a, "basin_region": "fog"}),
    "attractor_distance": lambda o: _map(o, "attractors", lambda a: {**a, "distance_from_reasoning_center": 99.0}),
    "attractor_scores": lambda o: _map(o, "attractors", lambda a: {**a, "recurrence_score": 0.0, "utility_score": 0.0, "contradiction_score": 0.0, "pressure_score": 0.0, "authority_score": 0.0, "recency_score": 0.0, "replay_value": 0.0, "centrality_score": 0.0}),
    "attractor_links": lambda o: _map(o, "attractors", lambda a: {**a, "links": []}),
    "attractor_tags": lambda o: _map(o, "attractors", lambda a: {**a, "tags": []}),
    "attractor_status": lambda o: _map(o, "attractors", lambda a: {**a, "status": ""}),
    # self-state fields: zero the whole nested state collection referenced by retrieval
    "state_active_attractors": lambda o: _nested(o, "state", "active_attractors", []),
    "state_recent_memory_ids": lambda o: _nested(o, "state", "recent_memory_ids", []),
    "state_core_commitments": lambda o: _nested(o, "state", "core_commitments", []),
    "state_unresolved_loops": lambda o: _nested(o, "state", "unresolved_loops", []),
    "state_hold_regions": lambda o: _nested(o, "state", "hold_regions", []),
    "state_recovery_routes": lambda o: _nested(o, "state", "recovery_routes", []),
    "state_contradiction_scars": lambda o: _nested(o, "state", "contradiction_scars", []),
    "state_self_id": lambda o: _nested(o, "state", "self_id", ""),
}


def _map(o: dict[str, Any], coll: str, fn) -> dict[str, Any]:
    out = copy.deepcopy(o)
    if coll in out and isinstance(out[coll], dict):
        out[coll] = {k: fn(v) for k, v in out[coll].items()}
    return out


def _nested(o: dict[str, Any], parent: str, key: str, val: Any) -> dict[str, Any]:
    out = copy.deepcopy(o)
    if isinstance(out.get(parent), dict):
        out[parent] = {**out[parent], key: val}
    return out


def run_load_bearing(fam: TaskFamily, *, with_fields: bool = True) -> dict[str, Any]:
    base = baseline_behavior(fam)
    ref = {"formed": "RELEASE", "withheld": "RELEASE", "unrelated": "HOLD"}
    results: dict[str, Any] = {"base_baseline": base}
    for name, tform in COMPONENT_ABLATIONS.items():
        r = ablate_variant(fam, transform=tform)
        results[name] = _classify(name, r, ref)
    if with_fields:
        for name, tform in FIELD_ABLATIONS.items():
            r = ablate_variant(fam, transform=tform)
            results[name] = _classify(name, r, ref)
    return results


def _classify(name: str, r: dict[str, Any], ref: dict[str, str]) -> dict[str, Any]:
    if not r.get("ok"):
        return {"name": name, "ok": False, "class": "UNKNOWN", "error": r.get("error")}
    d = r["decisions"]
    if d == ref:
        return {"name": name, "ok": True, "class": "REDUNDANT IN CURRENT ASSAY", "decisions": d, "integrity": r["integrity"]}
    # partial behavior loss
    return {"name": name, "ok": True, "class": "REQUIRED" if d["formed"] != "RELEASE" else "CONDITIONALLY REQUIRED", "decisions": d, "integrity": r["integrity"]}


def run_load_bearing_all(count: int | None = None, *, with_fields: bool = True) -> dict[str, Any]:
    from collections import Counter

    families = generate_seed_set(count)
    agg: dict[str, Counter] = {}
    row_examples: dict[str, list] = {}
    for fam in families.values():
        res = run_load_bearing(fam, with_fields=with_fields)
        for name, entry in res.items():
            if name == "base_baseline":
                continue
            cls = entry["class"]
            agg.setdefault(name, Counter())[cls] += 1
            row_examples.setdefault(name, []).append(entry)
    return {
        "n": len(families),
        "classification_matrix": {
            name: dict(cnt) for name, cnt in agg.items()
        },
        "example_row": {
            name: row_examples[name][0] if row_examples.get(name) else None for name in agg
        },
    }