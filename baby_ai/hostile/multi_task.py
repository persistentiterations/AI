"""Multi-task family run + irrelevant-memory interference (sections 5 & 6).

Section 5: a frozen family generator (task_gen) produces formation/calibration/
withheld/unrelated tasks per seed; results aggregated across many seeds.

Section 6: interference probes — form the target, then add
    NONE / MODEST / LARGE / CONFLICTING unrelated history
and measure whether selective reachability survives (withheld RELEASE intact,
unrelated stays HOLD) and how retrieval/work scales.
"""

from __future__ import annotations

import time
from typing import Any

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.semantics import canonical_json
from baby_ai.hostile.events import interference_event, safe_event
from baby_ai.hostile.task_gen import TaskFamily, generate_seed_set


def multi_task_summary(fam: TaskFamily) -> dict[str, Any]:
    """Full role probe on one family: formation, calibration, withheld, unrelated."""
    core = FormationCore(activation_id=f"multi-{fam.seed}")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    roles = {
        "formation": fam.formed_item,
        "calibration": fam.formed_item,      # same item, direct query
        "withheld": fam.withheld_item,
        "unrelated": fam.unrelated_item,
    }
    t0 = time.perf_counter()
    decisions = {role: core.route_decision(it)["decision"] for role, it in roles.items()}
    ms = round((time.perf_counter() - t0) * 1000, 3)
    retr = core.retrieve(fam.formed_item)
    return {
        "seed": fam.seed,
        "decisions": decisions,
        "retrieval_total_matches": retr["total_matches"],
        "state_bytes": len(canonical_json(core.to_dict()).encode("utf-8")),
        "route_ms": ms,
    }


def run_multi_task_all(count: int | None = None) -> dict[str, Any]:
    families = generate_seed_set(count)
    rows = [multi_task_summary(f) for f in families.values()]
    by_role = {role: sum(1 for r in rows if r["decisions"][role] == "RELEASE") for role in ("formation", "calibration", "withheld", "unrelated")}
    return {
        "seeds": sorted(families),
        "n": len(rows),
        "release_counts_by_role": by_role,
        "rows": rows,
        "finding": {
            "withheld_inherits": by_role["withheld"] == len(rows),
            "unrelated_stays_hold": by_role["unrelated"] == 0,
        },
    }


# -------------------------------------------------------------- interference
def interference_probe(fam: TaskFamily, *, interference_kind: str) -> dict[str, Any]:
    core = FormationCore(activation_id=f"intf-{fam.seed}-{interference_kind}")

    if interference_kind == "none":
        counts = 0
    elif interference_kind == "modest":
        counts = 3
    elif interference_kind == "large":
        counts = 30
    elif interference_kind == "conflicting":
        counts = 2
    else:
        raise ValueError(interference_kind)

    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    for i in range(counts):
        it = f"other_x_intr{i}_{fam.seed}"
        g = f"{fam.tag_group}x{i}"
        core.ingest(interference_event(core, it, g))

    if interference_kind == "conflicting":
        # conflicting-but-unrelated: items tagged with the SAME group but claiming HOLD
        for i in range(counts):
            it = f"{fam.tag_group}_c{i}_{fam.seed}"
            core.ingest(interference_event(core, it, fam.tag_group))

    t0 = time.perf_counter()
    withheld = core.route_decision(fam.withheld_item)
    unrelated = core.route_decision(fam.unrelated_item)
    ms = round((time.perf_counter() - t0) * 1000, 3)
    retr = core.retrieve(fam.withheld_item)
    return {
        "seed": fam.seed,
        "interference_kind": interference_kind,
        "interference_count": counts,
        "withheld_decision": withheld["decision"],
        "unrelated_decision": unrelated["decision"],
        "retrieval_total_matches": retr["total_matches"],
        "memories": core.counts()["memories"],
        "route_ms": ms,
        "selective_reachability_ok": withheld["decision"] == "RELEASE" and unrelated["decision"] == "HOLD",
    }


def run_interference_all(count: int | None = None) -> dict[str, Any]:
    families = generate_seed_set(count)
    kinds = ("none", "modest", "large", "conflicting")
    rows: list[dict[str, Any]] = []
    for fam in families.values():
        for kind in kinds:
            rows.append(interference_probe(fam, interference_kind=kind))
    ok = sum(1 for r in rows if r["selective_reachability_ok"])
    per_kind = {
        kind: sum(1 for r in rows if r["interference_kind"] == kind and r["selective_reachability_ok"])
        for kind in kinds
    }
    return {"n": len(rows), "selective_ok": ok, "per_kind_ok": per_kind, "rows": rows}