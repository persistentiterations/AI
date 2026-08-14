"""Orchestrator: run the full autopsy and emit evidence JSON.

Sections:
    1.  load-bearing ablation            (load_bearing)      -> 01_load_bearing.json
    2.  label invariance                 (label_invariance)  -> 02_label_invariance.json
    3.  minimum sufficient state         (minimum_state)     -> 03_minimum_sufficient_state.json
    4.  relational threshold             (relational)        -> 04_relational_threshold.json
    5.  architecture comparison          (minimum_state)     -> 05_architecture_comparison.json
    6.  reversibility / escape           (minimum_state)     -> 06_reversibility.json
    7.  verdict                          (verdict)           -> 07_verdict.json

All outputs land in baby_ai/artifacts/freeze/BABY_AI_AUTOPSY_v0_1/
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from baby_ai._env import PACKAGE
from baby_ai.autopsy import label_invariance, load_bearing, minimum_state, relational
from baby_ai.autopsy.verdict import SCIENTIFIC_VERDICT
from baby_ai.hostile.task_gen import SEEDS, generate_seed_set


OUT = PACKAGE / "artifacts" / "freeze" / "BABY_AI_AUTOPSY_v0_1"


def write_json(name: str, obj: Any) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return p


def run_all(*, max_seeds: int = 24) -> dict[str, Any]:
    t0 = time.time()
    report: dict[str, Any] = {
        "package": "baby_ai_autopsy_v0_1",
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "baseline": "BABY_AI_HOSTILE_QUALIFICATION_v0_1",
        "started_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seeds": SEEDS[: max_seeds],
    }

    n = min(max_seeds, len(SEEDS))
    families = generate_seed_set(n)

    # --- 1. load-bearing ablation
    lb = load_bearing.run_load_bearing_all(n, with_fields=True)
    write_json("01_load_bearing.json", lb)
    req = [k for k, v in lb["classification_matrix"].items()
           if v.get("REQUIRED") == n]
    redundant = [k for k, v in lb["classification_matrix"].items()
                 if v.get("REDUNDANT IN CURRENT ASSAY") == n]
    report["load_bearing"] = {
        "n": n,
        "always_required": req,
        "always_redundant": redundant,
        "field_count_total": len(lb["classification_matrix"]),
    }

    # --- 2. label invariance
    li = label_invariance.run_label_invariance_all(n)
    write_json("02_label_invariance.json", li)
    report["label_invariance"] = {
        "n": li["n"],
        "semantic_invariant_seeds": li["semantic_invariant_seeds"],
        "cycle_invariant_seeds": li["cycle_invariant_seeds"],
        "failures": li["n"] - li["semantic_invariant_seeds"],
        "finding": li["finding"],
    }

    # --- 3. minimum sufficient state (per-seed greedy removal)
    mss = {str(s): minimum_state.run_minimum_sufficient_state(f) for s, f in families.items()}
    write_json("03_minimum_sufficient_state.json", mss)
    ratios = [r["byte_ratio_full_to_min"] for r in mss.values() if r.get("byte_ratio_full_to_min")]
    remaining = sorted(list({tuple(sorted(r["remaining_fields"])) for r in mss.values()}))
    report["minimum_sufficient_state"] = {
        "n": n,
        "median_byte_ratio_full_to_min": round(sorted(ratios)[n // 2], 2) if ratios else None,
        "min_ratio": round(min(ratios), 2) if ratios else None,
        "max_ratio": round(max(ratios), 2) if ratios else None,
        "same_remaining_fields_across_seeds": len(remaining) == 1,
        "remaining_fields": list(remaining[0]) if remaining else [],
        "median_bytes": {
            "full": round(sorted(r["full_state_bytes"] for r in mss.values())[n // 2], 1),
            "minimum": round(sorted(r["minimum_state_bytes"] for r in mss.values())[n // 2], 1),
        },
    }

    # --- 4. relational threshold
    rel = {str(s): relational.run_relational_compare(f) for s, f in families.items()}
    write_json("04_relational_threshold.json", rel)
    first_lb = {v["first_load_bearing"] for v in rel.values() if v.get("first_load_bearing")}
    report["relational_threshold"] = {
        "n": n,
        "first_load_bearing_agreed_across_seeds": len(first_lb) == 1,
        "first_load_bearing": first_lb.pop() if first_lb else None,
        "finding": next(iter(rel.values()))["finding"],
    }

    # --- 5. architecture comparison (A/B/C on identical tasks)
    arch = {str(s): minimum_state.architecture_results(f) for s, f in families.items()}
    write_json("05_architecture_comparison.json", arch)
    identical = sum(1 for r in arch.values() if r["comparison"]["all_behaviors_identical"])
    mean_s = {k: round(sum(r["comparison"]["state_bytes"][k] for r in arch.values()) / n, 1)
              for k in ("A_conventional", "B_admissibility", "C_fractalish")}
    mean_w = {k: round(sum(r["comparison"]["wall_s"][k] for r in arch.values()) / n, 6)
              for k in ("A_conventional", "B_admissibility", "C_fractalish")} if any(
              r["comparison"]["wall_s"]["A_conventional"] is not None for r in arch.values()) else {}
    report["architecture_comparison"] = {
        "n": n,
        "seeds_with_identical_behaviors": identical,
        "mean_state_bytes": mean_s,
        "mean_wall_s": mean_w,
    }

    # --- 6. reversibility / escape
    rev = {str(s): minimum_state.reversibility_escape(f) for s, f in families.items()}
    write_json("06_reversibility.json", rev)
    report["reversibility_escape"] = {
        "n": n,
        "all_deformations_reversible": sum(1 for r in rev.values() if r["all_deformations_reversible"]),
    }

    # --- 7. verdict
    write_json("07_verdict.json", SCIENTIFIC_VERDICT)
    report["verdict"] = {
        "phase": SCIENTIFIC_VERDICT["phase"],
        "current_surviving_transfer_observation": SCIENTIFIC_VERDICT["current_surviving_transfer_observation"],
        "gaps": {k: SC["verdict"] for k, SC in SCIENTIFIC_VERDICT["gaps"].items()},
    }

    report["finished_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report["elapsed_s"] = round(time.time() - t0, 3)

    write_json("REPORT.json", report)
    return report


if __name__ == "__main__":
    import pprint

    pprint.pprint(run_all())