"""M2 — authoritative-history continuity across process death (acceptance test).

Exercises the M2 runner in three genuine subprocess invocations (cold restart via
serialized state, never the same in-memory object) and asserts the continuity
invariants. Corruption controls are run by the runner and recorded; their outcomes
are asserted only where the frozen architecture already guarantees fail-closed.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "baby_ai" / "artifacts" / "repair" / "BABY_AI_AUTHORITATIVE_HISTORY_CONTINUITY_M2_v0_1"


def _run(*args):
    cp = subprocess.run(
        [sys.executable, "-m", "baby_ai.assays.authoritative_history_continuity", *args],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert cp.returncode == 0, f"{args} failed rc={cp.returncode}: {cp.stderr}"
    return cp


def _trace(phase):
    return json.loads((PKG / f"trace_{phase}.json").read_text(encoding="utf-8"))


def test_m2_authoritative_history_continuity_across_restart():
    _run("phase-a")
    _run("phase-b")
    _run("phase-c")

    a = _trace("A")
    b = _trace("B")
    c = _trace("C")

    # I7 / I8 — decision + cause continuity across each boundary
    assert a["route_before_persist"] == {"decision": "HOLD", "reason": "contradiction_scar_blocking"}
    assert b["route_after_reload_before_resolve"] == {"decision": "HOLD", "reason": "contradiction_scar_blocking"}
    assert b["route_after_resolve"] == {"decision": "RELEASE", "reason": "formed_decision:RELEASE"}
    assert c["route"] == {"decision": "RELEASE", "reason": "formed_decision:RELEASE"}

    # I1 — identity continuity
    assert a["facts"]["memory_ids"] == b["facts"]["memory_ids"] == c["facts"]["memory_ids"] == ["mem-0000", "mem-0001"]
    assert a["facts"]["scars"][0]["scar_id"] == b["facts"]["scars"][0]["scar_id"] == c["facts"]["scars"][0]["scar_id"] == "scar-0000"

    # I5 — archive continuity: the historical scar stays "hold" after resolution
    assert a["facts"]["scars"][0]["status"] == "hold"
    assert c["facts"]["scars"][0]["status"] == "hold"

    # I6 — authority continuity: resolved status survives cold restart
    assert a["facts"]["scar_statuses"] == {}
    assert b["facts"]["scar_statuses"] == {"scar-0000": "resolved"}
    assert c["facts"]["scar_statuses"] == {"scar-0000": "resolved"}

    # I4 — causal-link continuity: resolution lineage survives
    assert b["facts"]["lineage_statuses"]["flux_alpha"] == ["active", "resolved"]
    assert c["facts"]["lineage_statuses"]["flux_alpha"] == ["active", "resolved"]


def test_m2_corruption_fail_closed_where_guaranteed():
    _run("phase-a"); _run("phase-b")  # ensure fixture exists

    # C2 tampered content and C4 ordering corruption must fail closed (semantic hash)
    _run("corrupt", "C2_tampered_content")
    assert _trace("corrupt_C2_tampered_content")["outcome"] == "HOLD_CONTINUITY_FAILURE"
    _run("corrupt", "C4_ordering_corruption")
    assert _trace("corrupt_C4_ordering_corruption")["outcome"] == "HOLD_CONTINUITY_FAILURE"

    # C3 broken causal reference must revert to non-PROCEED (fails toward HOLD)
    _run("corrupt", "C3_broken_causal_ref")
    assert _trace("corrupt_C3_broken_causal_ref")["outcome"] == "PASS"
