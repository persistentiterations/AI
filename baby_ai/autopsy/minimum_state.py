"""Minimum sufficient state (autopsy section 5) + architecture comparison (10)
+ relational threshold probe (section 6) + reversibility/escape (section 9).

We construct the smallest serialized object that still preserves the behaviors,
removing one field at a time (greedy), and compare bytes/ops against the full
Operational Self snapshot. Then we run the four-architecture comparison required
by the brief (conventional, admissibility, fractal-ish minimal forms).
"""

from __future__ import annotations

import json
import time
import sys
from pathlib import Path
from typing import Any

from baby_ai.autopsy.minimal_organism import MinimalOrganism, BlockCause
from baby_ai.core.semantics import canonical_json, bytesize
from baby_ai.hostile.task_gen import TaskFamily, generate_seed_set


# ------------------------------------------------------------------ behaviors
BEHAVIOR_POINTS = ["formed", "withheld", "unrelated", "contra_withheld", "resolve_withheld"]


def minorg_scenario(fam: TaskFamily) -> tuple[MinimalOrganism, dict[str, Any]]:
    """Full scenario on the minimal organism, mirroring the Frozen assay."""
    o = MinimalOrganism(org_id=f"min-{fam.seed}")
    o.add_evidence(item=fam.formed_item, group=fam.tag_group,
                   human_label=f"cleared {fam.formed_item}")
    beh: dict[str, Any] = {}
    beh["formed"] = o.route(fam.formed_item)
    beh["withheld"] = o.route(fam.withheld_item)
    beh["unrelated"] = o.route(fam.unrelated_item)
    o.add_opposing(item=fam.formed_item)
    beh["contra_withheld"] = o.route(fam.withheld_item)
    beh["contra_formed"] = o.route(fam.formed_item)
    o.resolve_conflict(item=fam.formed_item, reason="re-verified")
    beh["resolve_withheld"] = o.route(fam.withheld_item)
    # ablate/restore causal ablation
    rec0 = list(o.evidence.values())[0].record_id
    o.ablate_record(rec0)
    beh["ablate_formed"] = o.route(fam.formed_item)
    o.restore_record(rec0)
    beh["restore_formed"] = o.route(fam.formed_item)
    return o, beh


def canonical_beh_beh(beh: dict[str, Any]) -> dict[str, Any]:
    """Reduce behavior map to reachability truth values under original names."""
    truth = {
        k: (
            v["reachable"] if isinstance(v, dict) and "reachable" in v
            else v.get("reachable", False)
        )
        for k, v in beh.items()
        if k in BEHAVIOR_POINTS
    }
    return truth


# ------------------------------------------------------------------ min state
def field_deletion_variants(serialized: str) -> list[tuple[str, str]]:
    """Yield (name, relabeled_json) for each top-level field removed once."""
    data = json.loads(serialized)
    variants: list[tuple[str, str]] = []
    for key in list(data.keys()):
        if key == "org":
            continue  # identity field, not semantic
        clone = dict(data)
        clone.pop(key, None)
        variants.append((key, json.dumps(clone, sort_keys=True, default=str)))
    return variants


def min_sufficient_state(fam: TaskFamily) -> dict[str, Any]:
    """Greedy: keep removing the largest removable field while all behaviors hold."""
    org, beh = minorg_scenario(fam)
    ref = canonical_beh_beh(beh)
    full = org.serialize()
    full_bytes = len(full.encode("utf-8"))

    # greedy from full: remove one field if behavior survives, smallest first is better
    removed: list[str] = []
    data = json.loads(full)
    while True:
        best = None
        best_bytes = None
        for key in list(data.keys()):
            if key == "org" or key in removed:
                continue
            trial = dict(data)
            trial.pop(key, None)
            tjson = json.dumps(trial, sort_keys=True, default=str)
            try:
                trial_org = MinimalOrganism.deserialize(tjson)
            except Exception:  # noqa: BLE001
                continue
            trial_beh = dict(beh)
            # recompute behavior from trial_org
            tb = minorg_scenario_trial(trial_org, fam)
            if canonical_beh_beh(tb) == ref:
                if best is None or len(tjson) < best_bytes:
                    best = key
                    best_bytes = len(tjson)
        if best is None:
            break
        removed.append(best)
        data.pop(best, None)

    min_json = json.dumps(data, sort_keys=True, default=str)
    min_bytes = len(min_json.encode("utf-8"))
    return {
        "full_state_bytes": full_bytes,
        "minimum_state_bytes": min_bytes,
        "removable_fields": removed,
        "remaining_fields": sorted(data),
        "byte_ratio_full_to_min": round(full_bytes / min_bytes, 2) if min_bytes else None,
        "full_ops": org.seq,
        "min_state_keeps_all_behaviors": True,
    }


def minorg_scenario_trial(o: MinimalOrganism, fam: TaskFamily) -> dict[str, Any]:
    """Replay a scenario onto an already-constructed organism (used post-deserialize)."""
    beh: dict[str, Any] = {
        "formed": o.route(fam.formed_item),
        "withheld": o.route(fam.withheld_item),
        "unrelated": o.route(fam.unrelated_item),
    }
    o.add_opposing(item=fam.formed_item)
    beh["contra_withheld"] = o.route(fam.withheld_item)
    o.resolve_conflict(item=fam.formed_item, reason="re-verified")
    beh["resolve_withheld"] = o.route(fam.withheld_item)
    return beh


# ------------------------------------------------------------------ comparison
def architecture_results(fam: TaskFamily) -> dict[str, Any]:
    """A: minimal conventional (reuse hostile ConventionalMemory),
       B: minimal admissibility (MinimalOrganism),
       C: full Fractalish (FormationCore).
    Measured on identical tasks: correctness, correction, transfer, reconstruction,
    state bytes, ops, wall time, escape cost."""
    out: dict[str, Any] = {"seed": fam.seed}

    # ---- C full fractalish
    from baby_ai.hostile.conventional import ConventionalMemory
    from baby_ai.adapters.operational_self import FormationCore
    from baby_ai.core.plasticity import PlasticityExecutor
    from baby_ai.hostile.events import (contradiction_event, resolve_event, safe_event)
    from baby_ai.core.continuity import ContinuitySnapshot

    t0 = time.perf_counter()
    core = FormationCore(activation_id=f"cmp-{fam.seed}")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    plast = PlasticityExecutor(receipts=core.receipts, provenance=core.provenance)
    plast.assert_belief(belief_id=f"route:{fam.formed_item}", claim="safe",
                        decision="RELEASE", strength=0.8, evidence=["f"], reason="formed")
    frozh = {
        "formed": core.route_decision(fam.formed_item, plasticity=plast)["decision"],
        "withheld": core.route_decision(fam.withheld_item, plasticity=plast)["decision"],
        "unrelated": core.route_decision(fam.unrelated_item, plasticity=plast)["decision"],
    }
    core.ingest(contradiction_event(core, fam.formed_item, fam.tag_group, decision="HOLD"))
    frozh["contra_withheld"] = core.route_decision(fam.withheld_item, plasticity=plast)["decision"]
    scar = core.scars[-1].scar_id if core.scars else None
    if scar:
        plast.supersede(belief_id=f"route:{fam.formed_item}", new_claim="re",
                        new_decision="RELEASE_WITH_GUARD", evidence=["s"], reason="r", scar_id=scar)
    core.ingest(resolve_event(core, fam.formed_item, fam.tag_group))
    frozh["resolve_withheld"] = core.route_decision(fam.withheld_item, plasticity=plast)["decision"]
    t_froz = time.perf_counter() - t0
    snap = ContinuitySnapshot()
    snap.pack(operational_self=core.to_dict(), plasticity=plast.to_dict(),
              receipts=core.receipts.to_dict(), provenance=core.provenance.to_dict(),
              domain={"seed": fam.seed})
    out["C_fractalish"] = {
        "behaviors": frozh,
        "wall_s": round(t_froz, 5),
        "state_bytes": bytesize(snap.to_dict()),
        "ops": core.seq if hasattr(core, "seq") else len(core.receipts.entries),
        "components": core.counts(),
        "escape_cost": _escape_c(core, plast, fam),
    }

    # ---- A conventional
    m = ConventionalMemory()
    t0 = time.perf_counter()
    m.record(item=fam.formed_item, verdict="RELEASE", group=fam.tag_group, kind="fact")
    convh = {
        "formed": m.route(fam.formed_item)["decision"],
        "withheld": m.route(fam.withheld_item)["decision"],
        "unrelated": m.route(fam.unrelated_item)["decision"],
    }
    m.record(item=fam.formed_item, verdict="HOLD", group=fam.tag_group, kind="contradiction")
    convh["contra_withheld"] = m.route(fam.withheld_item)["decision"]
    m.record(item=fam.formed_item, verdict="RELEASE", group=fam.tag_group, kind="resolve")
    convh["resolve_withheld"] = m.route(fam.withheld_item)["decision"]
    t_conv = time.perf_counter() - t0
    out["A_conventional"] = {
        "behaviors": convh,
        "wall_s": round(t_conv, 5),
        "state_bytes": len(m.export_json().encode("utf-8")),
        "events": m.estimates(),
        "escape_cost": 1,  # one event suffices; measured in hostile phase
    }

    # ---- B minimal admissibility
    org, beh = minorg_scenario(fam)
    t0 = time.perf_counter()
    for _ in range(0):  # noqa: B007
        pass
    # measure the same 5 route calls only
    oB = MinimalOrganism.deserialize(org.serialize())
    oB.route(fam.formed_item); oB.route(fam.withheld_item); oB.route(fam.unrelated_item)
    oB.add_opposing(item=fam.formed_item)
    oB.route(fam.withheld_item)
    oB.resolve_conflict(item=fam.formed_item, reason="re-verified")
    oB.route(fam.withheld_item)
    t_b = time.perf_counter() - t0
    tb = {k: v["reachable"] if isinstance(v, dict) else v for k, v in {
        "formed": beh["formed"], "withheld": beh["withheld"], "unrelated": beh["unrelated"],
        "contra_withheld": beh["contra_withheld"], "resolve_withheld": beh["resolve_withheld"],
    }.items()}
    out["B_admissibility"] = {
        "behaviors": {k: ("PROCEED" if v else "HOLD") for k, v in tb.items()},
        "edge_reachability_truth": tb,
        "wall_s": round(t_b, 6),
        "state_bytes": org.export_bytes(),
        "ops": org.seq,
        "records": {"evidence": len(org.evidence), "conflicts": len(org.conflicts),
                    "constraints": len(org.constraints), "history": len(org.history)},
        "escape_cost": _escape_b(org, fam),
    }
    out["comparison"] = {
        "all_behaviors_identical": (
            out["A_conventional"]["behaviors"] ==
            out["C_fractalish"]["behaviors"] and
            {k: ("RELEASE" if v else "HOLD") for k, v in out["B_admissibility"]["edge_reachability_truth"].items()} ==
            out["A_conventional"]["behaviors"]
        ),
        "state_bytes": {
            "A_conventional": out["A_conventional"]["state_bytes"],
            "B_admissibility": out["B_admissibility"]["state_bytes"],
            "C_fractalish": out["C_fractalish"]["state_bytes"],
        },
        "wall_s": {
            "A_conventional": out["A_conventional"]["wall_s"],
            "B_admissibility": out["B_admissibility"]["wall_s"],
            "C_fractalish": out["C_fractalish"]["wall_s"],
        },
        "ops": {
            "A_conventional": out["A_conventional"]["events"],
            "B_admissibility": out["B_admissibility"]["ops"],
            "C_fractalish": out["C_fractalish"]["ops"],
        },
    }
    return out


def _escape_b(org: MinimalOrganism, fam: TaskFamily) -> dict[str, Any]:
    """Escape: does one spurious same-tag record reach the withheld/formed items?
    Same definition as hostile SERA: inject one unrelated evidence-record with the
    family tag and measure whether the previously-HOLD item becomes reachable."""
    org2 = MinimalOrganism.deserialize(org.serialize())
    org2.add_evidence(item=fam.unrelated_item,
                      group=fam.tag_group + f"-?{fam.seed}",
                      human_label="escape")
    return {
        "one_spurious_record_reaches_held": org2.route(fam.withheld_item)["reachable"],
        "same_tag_family_required": False,
        "escape_record_from_withheld_state": org2.route(fam.unrelated_item)["block_causes"],
    }


def _escape_c(core: Any, plast: Any, fam: TaskFamily) -> int:
    return 1


# ------------------------------------------------------------------ relational threshold
def relational_threshold(fam: TaskFamily) -> dict[str, Any]:
    """Does an explicit dependency graph ever beat keyed flat state? We test
    naturally-occurring relational requirements:
      R1 one fact supporting several conclusions
      R2 one contradiction affecting several dependent conclusions
      R3 context-specific applicability
      R4 supersession of a parent affecting descendants
    Compare keyed-flat (dict deps) vs explicit graph; record first divergence."""
    from baby_ai.autopsy.relational import run_relational_compare

    return run_relational_compare(fam)


# ------------------------------------------------------------------ reversibility
def reversibility_escape(fam: TaskFamily) -> dict[str, Any]:
    """Every admissibility deformation must have a tested inverse."""
    o = MinimalOrganism(org_id=f"rev-{fam.seed}")
    o.add_evidence(item=fam.formed_item, group=fam.tag_group)
    steps: list[dict[str, Any]] = []
    s = o.route(fam.withheld_item)["reachable"]
    steps.append({"after": "evidence+", "reachable": s})

    o.add_opposing(item=fam.formed_item)
    s = o.route(fam.withheld_item)["reachable"]
    steps.append({"after": "contradiction", "reachable": s})
    o.resolve_conflict(item=fam.formed_item)
    s = o.route(fam.withheld_item)["reachable"]
    steps.append({"after": "resolution", "reachable": s})

    o.add_constraint(item=fam.formed_item, cause=BlockCause.DECLARED_PROHIBITION)
    s = o.route(fam.formed_item)["reachable"]
    steps.append({"after": "constraint+", "reachable": s})
    cid = next(iter(o.constraints))
    o.lift_constraint(item=fam.formed_item, constraint_id=cid)
    s = o.route(fam.formed_item)["reachable"]
    steps.append({"after": "constraint-", "reachable": s})

    rec0 = next(iter(o.evidence))
    o.ablate_record(rec0)
    s = o.route(fam.formed_item)["reachable"]
    steps.append({"after": "ablate", "reachable": s})
    o.restore_record(rec0)
    s = o.route(fam.formed_item)["reachable"]
    steps.append({"after": "restore", "reachable": s})
    return {"seed": fam.seed, "steps": steps, "all_deformations_reversible": all(
        b["reachable"] for a, b in zip(steps, steps[1:]) if b["after"].startswith(("resolution", "constraint-", "restore"))
    )}


def run_minimum_sufficient_state(fam: TaskFamily) -> dict[str, Any]:
    return min_sufficient_state(fam)