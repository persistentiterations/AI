"""Surface randomization (section 4).

The task generator already randomizes domain terms, item ids, group tags, and
interface tokens per seed. Here we additionally probe:

  DECISION_LABELS   - rename RELEASE/HOLD surface labels in the formed decision
                      field; does the router still route the consequence?
  MEMORY_IDS        - replace memory/attractor/relation ids with fresh ids; does
                      the constructed retrieval still hold?

If performance collapses because a specific surface token carries the test, the
deeper claim must be HOLD.
"""

from __future__ import annotations

from typing import Any

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.hostile.events import safe_event
from baby_ai.hostile.task_gen import TaskFamily


def decision_label_rename(fam: TaskFamily, *, new_label: str = "GREEN_LIGHT") -> dict[str, Any]:
    """Form a RELEASE under a RENAMED decision label and ask the router."""
    core = FormationCore(activation_id=f"rnd-label-{fam.seed}")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group, decision=new_label))
    before_dict = core.to_dict()
    decided = core.route_decision(fam.formed_item)
    # also verify the exact label used to be 'RELEASE' in the control case
    control = FormationCore(activation_id=f"rnd-ctl-{fam.seed}")
    control.ingest(safe_event(control, fam.formed_item, fam.tag_group, decision="RELEASE"))
    ctl = control.route_decision(fam.formed_item)
    return {
        "renamed_label": new_label,
        "renamed_decision": decided["decision"],
        "renamed_reason": decided["reason"],
        "control_decision_RELEASE": ctl["decision"],
        "label_coupled": decided["decision"] != ctl["decision"],
        "note": "if label_coupled=True the router keys on the literal RELEASE string, not on the semantics",
    }


def memory_id_refresh(fam: TaskFamily) -> dict[str, Any]:
    """Re-sign every id in the formed state, import, and re-route."""
    core = FormationCore(activation_id=f"rnd-ids-{fam.seed}")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))

    dct = core.to_dict()
    # re-sign all ids deterministically
    counters: dict[str, int] = {}

    def new_id(prefix: str) -> str:
        counters[prefix] = counters.get(prefix, 0) + 1
        return f"{prefix}-{counters[prefix]:04d}"

    id_map: dict[str, str] = {}
    for tag in ("mem", "attr", "lnk", "scar", "fog", "replay"):
        for objs in (dct["memories"], dct["attractors"], dct["links"], dct["scars"], dct["fog"], dct["routes"]):
            if isinstance(objs, dict):
                for k in list(objs):
                    if k.startswith(f"{tag}-"):
                        id_map[k] = new_id(tag)
            elif isinstance(objs, list):
                for o in objs:
                    for field, val in list(o.items()):
                        if isinstance(val, str) and val in id_map:
                            o[field] = id_map[val]
    # apply id map to dict keys
    dct["memories"] = {id_map.get(k, new_id("mem")): v for k, v in dct["memories"].items()}
    dct["attractors"] = {id_map.get(k, new_id("attr")): v for k, v in dct["attractors"].items()}
    for obj in dct["memories"].values():
        if obj.get("memory_id") and obj["memory_id"] in dct["memories"]:
            pass
    # rewrite foreign keys
    for field in ("memory_id", "attractor_id", "source_event_id", "related_memory_ids", "memory_ids", "from_memory_id", "to_memory_id", "route_id", "fog_id", "scar_id", "link_id"):
        for collection in (dct["memories"].values(), dct["attractors"].values(), dct["links"], dct["scars"], dct["fog"], dct["routes"]):
            if isinstance(collection, dict):
                items = list(collection.values())
            else:
                items = collection
            for o in items:
                if field in o and isinstance(o[field], list):
                    o[field] = [id_map.get(x, x) for x in o[field]]
                elif field in o and isinstance(o[field], str) and o[field].startswith(("mem-", "attr-", "lnk-", "scar-", "fog-", "replay-")):
                    o[field] = id_map.get(o[field], new_id(o[field].split("-")[0]))

    from baby_ai.core.continuity import ContinuitySnapshot
    from baby_ai.core.plasticity import PlasticityExecutor
    from baby_ai.adapters.operational_self import FormationCore as FC

    snap = ContinuitySnapshot()
    snap.pack(
        operational_self=dct,
        plasticity=PlasticityExecutor(receipts=core.receipts).to_dict(),
        receipts=core.receipts.to_dict(),
        provenance=core.provenance.to_dict(),
        domain={"seed": fam.seed},
    )
    imported = ContinuitySnapshot.from_dict(snap.to_dict())
    core_b = FC.from_dict(imported.operational_self, activation_id=f"rnd-ids-b-{fam.seed}")
    return {
        "rerouted": core_b.route_decision(fam.formed_item)["decision"],
        "ids_changed": len(id_map),
        "integrity_ok": imported.integrity["ok"],
    }


def run_all_surface_probes(fam: TaskFamily) -> dict[str, Any]:
    return {
        "decision_label_rename": decision_label_rename(fam),
        "memory_id_refresh": memory_id_refresh(fam),
    }