"""Conventional baseline comparison across seeds (section 10).

Feeds the SAME frozen task families to ConventionalMemory and compares against
the formed core on every demonstrated advantage:
    withheld-inheritance RELEASE, unrelated HOLD, contradiction switch to HOLD,
    resolve restore to RELEASE, ablate -> HOLD, restore -> RELEASE (transfer),
    and per-query work.

If the conventional baseline reproduces all of it with equal-or-less work, the
host must report that the formed core has NO measured advantage over an ordinary
store (this would be a hostile FAILURE of the innovation claim).
"""

from __future__ import annotations

from typing import Any

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.hostile.conventional import ConventionalMemory
from baby_ai.hostile.events import contradiction_event, resolve_event, safe_event
from baby_ai.hostile.task_gen import TaskFamily, generate_seed_set


def conventional_scenario(fam: TaskFamily) -> dict[str, Any]:
    m = ConventionalMemory()
    m.record(item=fam.formed_item, verdict="RELEASE", group=fam.tag_group, kind="fact")
    roles = {
        "formation": m.route(fam.formed_item),
        "withheld": m.route(fam.withheld_item),
        "unrelated": m.route(fam.unrelated_item),
    }
    m.record(item=fam.formed_item, verdict="HOLD", group=fam.tag_group, kind="contradiction")
    contradicted = m.route(fam.withheld_item)
    m.record(item=fam.formed_item, verdict="RELEASE", group=fam.tag_group, kind="resolve")
    restored = m.route(fam.withheld_item)

    # transfer: ablate the formed item from the conventional store, then restore
    snapshot = m.to_dict()
    m.ablate(fam.formed_item)
    post_ablate = m.route(fam.withheld_item)
    m.restore_from(snapshot)
    post_restore = m.route(fam.withheld_item)

    return {
        "seed": fam.seed,
        "formation": roles["formation"]["decision"],
        "withheld": roles["withheld"]["decision"],
        "unrelated": roles["unrelated"]["decision"],
        "contradicted": contradicted["decision"],
        "restored": restored["decision"],
        "post_ablate": post_ablate["decision"],
        "post_restore": post_restore["decision"],
        "max_work": max(
            roles["formation"]["work"],
            roles["withheld"]["work"],
            roles["unrelated"]["work"],
            contradicted["work"],
            restored["work"],
            post_ablate["work"],
            post_restore["work"],
        ),
        "max_ms": max(
            roles["formation"]["ms"],
            roles["withheld"]["ms"],
            roles["unrelated"]["ms"],
            contradicted["ms"],
            restored["ms"],
            post_ablate["ms"],
            post_restore["ms"],
        ),
        "estimates": m.estimates(),
    }


def run_conventional_all(count: int | None = None) -> dict[str, Any]:
    families = generate_seed_set(count)
    rows = [conventional_scenario(f) for f in families.values()]
    n = len(rows)
    withheld_release = sum(1 for r in rows if r["withheld"] == "RELEASE")
    unrelated_hold = sum(1 for r in rows if r["unrelated"] == "HOLD")
    contradicted_hold = sum(1 for r in rows if r["contradicted"] == "HOLD")
    restored_release = sum(1 for r in rows if r["restored"] == "RELEASE")
    ablate_hold = sum(1 for r in rows if r["post_ablate"] == "HOLD")
    restore_release = sum(1 for r in rows if r["post_restore"] == "RELEASE")
    return {
        "n": n,
        "seed_range": [min(families), max(families)] if families else [],
        "withheld_release": withheld_release,
        "unrelated_hold": unrelated_hold,
        "contradicted_hold": contradicted_hold,
        "restored_release": restored_release,
        "post_ablate_hold": ablate_hold,
        "post_restore_release": restore_release,
        "reproduces_all_advantages": (
            withheld_release == n
            and unrelated_hold == n
            and contradicted_hold == n
            and restored_release == n
            and ablate_hold == n
            and restore_release == n
        ),
        "max_work_seen": max(r["max_work"] for r in rows) if rows else 0,
        "max_ms_seen": max(r["max_ms"] for r in rows) if rows else 0,
        "rows": rows,
    }


def formed_work_baseline(fam: TaskFamily) -> dict[str, Any]:
    """Same scenario on the formed core for a work comparison. The contradiction
    scar blocks routing; superseding it (via PlasticityExecutor, exactly the demo
    restore path) releases the block again."""
    from baby_ai.core.plasticity import PlasticityExecutor

    core = FormationCore(activation_id=f"fw-{fam.seed}")
    plast = PlasticityExecutor(receipts=core.receipts, provenance=core.provenance)
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    plast.assert_belief(
        belief_id=f"route:{fam.formed_item}",
        claim=f"{fam.formed_item} safe",
        decision="RELEASE",
        strength=0.8,
        evidence=["formation"],
        reason="formed clearance",
    )
    d_withheld = core.route_decision(fam.withheld_item, plasticity=plast)
    d_unrelated = core.route_decision(fam.unrelated_item)
    core.ingest(contradiction_event(core, fam.formed_item, fam.tag_group, decision="HOLD"))
    d_contra = core.route_decision(fam.withheld_item, plasticity=plast)
    scar_id = core.scars[-1].scar_id if core.scars else None
    plast.supersede(
        belief_id=f"route:{fam.formed_item}",
        new_claim=f"{fam.formed_item} re-verified under guard",
        new_decision="RELEASE_WITH_GUARD",
        evidence=["hostile resolve"],
        reason="supersede contradiction hold",
        scar_id=scar_id,
    )
    core.ingest(resolve_event(core, fam.formed_item, fam.tag_group))
    d_restore = core.route_decision(fam.withheld_item, plasticity=plast)
    return {
        "withheld": d_withheld["decision"],
        "unrelated": d_unrelated["decision"],
        "contradicted": d_contra["decision"],
        "restored": d_restore["decision"],
        "query_work": len(core.memories) + len(core.attractors) + len(core.fog),
        "state_bytes": core.to_dict().__sizeof__(),
    }


def run_work_comparison(count: int | None = None) -> dict[str, Any]:
    families = generate_seed_set(count)
    conv = [conventional_scenario(f) for f in families.values()]
    formed = [formed_work_baseline(f) for f in families.values()]
    return {
        "n": len(conv),
        "conventional_max_work": max(r["max_work"] for r in conv),
        "conventional_mean_work": round(sum(r["max_work"] for r in conv) / len(conv), 3),
        "conventional_max_ms": max(r["max_ms"] for r in conv),
        "conventional_mean_ms": round(sum(r["max_ms"] for r in conv) / len(conv), 3),
        "formed_mean_query_work": round(sum(r["query_work"] for r in formed) / len(formed), 3),
        "formed_route_decisions": {
            k: sum(1 for r in formed if r[k] == "RELEASE")
            for k in ("withheld", "unrelated", "contradicted", "restored")
        },
        "conventional_route_decisions": {
            k: sum(1 for r in conv if r[k] == "RELEASE")
            for k in ("withheld", "unrelated", "contradicted", "restored")
        },
    }