"""Orchestrator: run the full hostile qualification and emit evidence JSON.

Sections:
    1.  task generator sanity            (task_gen, seeds 0..23)
    2.  gap C controls                    (controls_gap_c)
    3.  sham transfer controls            (sham_transfer)
    4.  surface randomization            (surface_rnd)
    5.  multi-task family across seeds   (multi_task)
    6.  memory interference              (multi_task)
    7.  adversarial plasticity           (advanced)
    8.  continuity attacks               (advanced)
    9.  SERA work measurement            (advanced)
    10. conventional baseline comparison (baseline_cmp)

All outputs land in baby_ai/artifacts/freeze/BABY_AI_HOSTILE_QUALIFICATION_v0_1/
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from baby_ai._env import PACKAGE
from baby_ai.hostile import baseline_cmp, controls_gap_c, multi_task, sham_transfer, surface_rnd, task_gen
from baby_ai.hostile.advanced import run_all_hostile_sections
from baby_ai.hostile.task_gen import SEEDS, generate_family, generate_seed_set


OUT = PACKAGE / "artifacts" / "freeze" / "BABY_AI_HOSTILE_QUALIFICATION_v0_1"


def write_json(name: str, obj: Any) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return p


def run_all(*, max_seeds: int = 24) -> dict[str, Any]:
    t0 = time.time()
    report: dict[str, Any] = {
        "package": "baby_ai_hostile_qualification_v0_1",
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "started_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seeds": SEEDS[:max_seeds],
    }

    n = min(max_seeds, len(SEEDS))
    families = generate_seed_set(n)

    # --- 1. generator determinism + item generation sanity
    first_seed = int(next(iter(families)))
    fam0 = families[first_seed]
    ref_role_items = fam0.role_items()
    determinism = {"ok": True, "duplicate_surfaces": 0, "checks": {}}
    seen: set[str] = set()
    for s, f in families.items():
        ri = f.role_items()
        dup = len(ri) != len(set(ri.values()))
        if dup:
            determinism["ok"] = False
        for k in ("formed_item", "withheld_item", "unrelated_item"):
            v = getattr(f, k)
            if v in seen and v != ref_role_items.get(k):
                determinism["duplicate_surfaces"] += 1
            seen.add(v)
        determinism["checks"][str(s)] = {
            "valid": len(f.role_items()) == 3,
            "duplicate_roles": dup,
            "roles": ri,
        }
    gen = {
        "families_ok": {str(s): len(f.role_items()) == 3 for s, f in families.items()},
        "generator_deterministic": determinism,
    }
    write_json("01_generator.json", gen)
    report["generator"] = {
        "all_families_valid": all(gen["families_ok"].values()),
        "deterministic": determinism["ok"],
        "duplicate_surfaces": determinism["duplicate_surfaces"],
    }

    # --- 2. gap C controls across seeds
    ctl = {str(s): controls_gap_c.run_all_controls(f) for s, f in families.items()}
    write_json("02_gap_c_controls.json", ctl)
    PROSE = ("BIOGRAPHY_SHORT", "BIOGRAPHY_FULL", "STRUCTURED_TEXT", "FLAT_CONCLUSION", "EVENT_TRANSCRIPT")
    formed_tx = sum(1 for r in ctl.values() if r["FORMED"]["item_decisions"]["withheld"] == "RELEASE")
    formed_exp_tx = sum(1 for r in ctl.values() if r["FORMED_EXPORTED"]["item_decisions"]["withheld"] == "RELEASE")
    prose_hold = all(
        r[c]["item_decisions"]["withheld"] == "HOLD" for r in ctl.values() for c in PROSE
    )
    kv_reproduce = sum(1 for r in ctl.values() if r["KEY_VALUE_MEMORY"]["item_decisions"]["withheld"] == "RELEASE")
    rag_reproduce = sum(1 for r in ctl.values() if r["RAG"]["item_decisions"]["withheld"] == "RELEASE")
    report["gap_c_controls"] = {
        "n": n,
        "formed_transfer_count": formed_tx,
        "formed_exported_transfer_count": formed_exp_tx,
        "prose_controls_all_hold": bool(prose_hold),
        "key_value_memory_reproduces": kv_reproduce,
        "rag_reproduces": rag_reproduce,
    }

    # --- 3. sham transfer controls on 3 representative seeds
    sham_rows = {}
    for s in list(families)[:3]:
        sham_rows[str(s)] = sham_transfer.run_all_shams(families[s])
    write_json("03_sham_transfer.json", sham_rows)
    report["sham_transfer"] = {
        "seeds_run": list(sham_rows),
        "all_controls_ok": all(v["ok"] for rows in sham_rows.values() for v in rows.values()),
    }

    # --- 4. surface randomization
    surf = {str(s): surface_rnd.run_all_surface_probes(f) for s, f in families.items()}
    write_json("04_surface_randomization.json", surf)
    label_coupled = sum(1 for r in surf.values() if r["decision_label_rename"]["label_coupled"])
    id_rerouted_release = sum(1 for r in surf.values() if r["memory_id_refresh"]["rerouted"] == "RELEASE")
    report["surface_randomization"] = {
        "n": n,
        "label_coupled_count": label_coupled,
        "memory_id_refresh_rerouted_release": id_rerouted_release,
        "memory_id_refresh_integrity_ok": sum(1 for r in surf.values() if r["memory_id_refresh"]["integrity_ok"]),
    }

    # --- 5. multi-task family across seeds
    mtsk = multi_task.run_multi_task_all(n)
    write_json("05_multi_task_family.json", mtsk)
    report["multi_task_family"] = {
        "n": mtsk["n"],
        "release_counts_by_role": mtsk["release_counts_by_role"],
        "withheld_inherits": mtsk["finding"]["withheld_inherits"],
        "unrelated_stays_hold": mtsk["finding"]["unrelated_stays_hold"],
    }

    # --- 6. interference
    intr = multi_task.run_interference_all(n)
    write_json("06_interference.json", intr)
    report["interference"] = {
        "n": intr["n"],
        "selective_ok": intr["selective_ok"],
        "per_kind_ok": intr["per_kind_ok"],
    }

    # --- 7+8+9. adversarial plasticity, continuity, SERA
    adv = {str(s): run_all_hostile_sections(f) for s, f in families.items()}
    write_json("07_advanced_hostile.json", adv)
    report["advanced"] = _advanced_summary(adv)

    # --- 10. conventional baseline comparison
    conv = baseline_cmp.run_conventional_all(n)
    write_json("08_conventional_baseline.json", conv)
    work = baseline_cmp.run_work_comparison(n)
    write_json("09_work_comparison.json", work)
    report["conventional_baseline"] = {
        "reproduces_all_advantages": conv["reproduces_all_advantages"],
        "n": conv["n"],
        "conventional_max_work": conv["max_work_seen"],
        "formed_mean_query_work": work["formed_mean_query_work"],
        "conventional_mean_work": work["conventional_mean_work"],
    }

    report["finished_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report["elapsed_s"] = round(time.time() - t0, 3)

    write_json("REPORT.json", report)
    return report


def _advanced_summary(adv: dict[str, Any]) -> dict[str, Any]:
    n = len(adv)
    weak_holds = sum(
        1 for s, sec in adv.items()
        if sec["adversarial_plasticity"]["weak_cold_no_correction"]["expect_routing_switched"] == "HOLD"
        and sec["adversarial_plasticity"]["weak_cold_no_correction"]["withheld"] == "HOLD"
    )
    late_holds = sum(
        1 for s, sec in adv.items()
        if sec["adversarial_plasticity"]["late_only_unformed"]["expect_unchanged"] == "HOLD"
        and sec["adversarial_plasticity"]["late_only_unformed"]["withheld"] == "HOLD"
    )
    mixed_ok = sum(
        1 for s, sec in adv.items()
        if sec["adversarial_plasticity"]["mixed_partial_poison"]["partial_poison_ok"]
    )

    integrity_fails = {k: 0 for k in ("BIT_FLIP", "STALE_STAMP", "WRONG_TIP")}
    rejected = {k: 0 for k in ("BIT_FLIP", "STALE_STAMP", "WRONG_TIP")}
    truncate_rejected = 0
    for s, sec in adv.items():
        cy = sec["continuity_attacks"]
        truncate_rejected += 1 if cy["TRUNCATE"]["status"] == "rejected" else 0
        for k in integrity_fails:
            if cy[k].get("integrity_ok") is False:
                integrity_fails[k] += 1
            elif cy[k].get("status") == "rejected":
                rejected[k] += 1

    sera_escape_reachable = 0
    sera_escape_total = 0
    correct_payload: list[int] = []
    escape_payload: list[int] = []
    for sec in adv.values():
        for e in sec["sera"]["escape"]:
            sera_escape_total += 1
            if e["spurious_reachable"]:
                sera_escape_reachable += 1
            escape_payload.append(e["payload_bytes"])
        for e in sec["sera"]["correct"]:
            correct_payload.append(e["payload_bytes"])

    return {
        "adversarial_plasticity": {
            "n": n,
            "weak_cold_blocks_routing": weak_holds,
            "late_only_no_leak": late_holds,
            "mixed_partial_poison_ok": mixed_ok,
        },
        "continuity_attacks": {
            "n": n,
            "truncate_rejected": truncate_rejected,
            "integrity_failed_loudly": integrity_fails,
            "json_rejected_loudly": rejected,
        },
        "sera": {
            "escape_reachable_rows": sera_escape_reachable,
            "escape_rows_total": sera_escape_total,
            "correct_payload_mean_bytes": round(sum(correct_payload) / len(correct_payload), 1) if correct_payload else 0,
            "escape_payload_mean_bytes": round(sum(escape_payload) / len(escape_payload), 1) if escape_payload else 0,
        },
    }


if __name__ == "__main__":
    import pprint

    pprint.pprint(run_all())