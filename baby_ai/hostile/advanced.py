"""Adversarial plasticity, continuity attacks, and SERA work measurement
(sections 7, 8, 9 of the hostile qualification).

Adversarial plasticity: can an attacker This the original formed RELEASE without
a genuine *concurrent* contradiction? We try:
    WEAK_COLD     - HOLD label first, then no reversal (paper trail without effect)
    LATE_ONLY     - contradiction ingested without prior formation
    MIXED         - scar on only a fraction of the shared retention paths
    NO_EVENT      - forged scar object injected into the serialized state

Continuity attacks: given a valid snapshot, corrupt serialized data and try to
import. We measure whether integrity / authority checks stop the attack.
    TRUNCATE      - cut the JSON mid-stream
    BIT_FLIP      - flip characters in the middle of a field
    STALE_STAMP   - tamper a previously-signed snapshot and re-import
    WRONG_TIP     - replace the latest receipt anchor
    REIMPORT      - double-import of the SAME bytes (idempotence)

SERA (work measurement): the machine cost of the formed-advantage as a function
of correct copies vs. escape copies.
    cost_correct(k)   - k correctly retained records: retrieval workload and state
    escape_cost(k)    - cost to make k spurious formed claims reachable
"""

from __future__ import annotations

import copy
import json
import time
from typing import Any

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.core.semantics import canonical_json
from baby_ai.hostile.events import contradiction_event, safe_event
from baby_ai.hostile.task_gen import TaskFamily


# ------------------------------------------------------------- adversarial plasticity
def wild_weak_cold(fam: TaskFamily) -> dict[str, Any]:
    """A contradiction scar with NO correction. Routing must switch to HOLD
    (plasticity changes routing), while the original RELEASE record must remain
    in history (no erasure)."""
    core = FormationCore(activation_id=f"adv-wc-{fam.seed}")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    core.ingest(contradiction_event(core, fam.formed_item, fam.tag_group, decision="HOLD"))
    d = core.route_decision(fam.withheld_item)
    released_in_history = any(
        any(d.startswith("RELEASE") for d in m.retained_decisions)
        for m in core.memories.values()
    )
    return {
        "withheld": d["decision"],
        "expect_routing_switched": "HOLD",
        "release_record_still_in_memory": released_in_history,
        "history_preserved": released_in_history,
    }


def wild_late_only(fam: TaskFamily) -> dict[str, Any]:
    """Contradiction exists but no prior formation; must not leak to unformed item."""
    core = FormationCore(activation_id=f"adv-lo-{fam.seed}")
    core.ingest(contradiction_event(core, fam.formed_item, fam.tag_group, decision="RELEASE"))
    d = core.route_decision(fam.withheld_item)
    return {"withheld": d["decision"], "expect_unchanged": "HOLD"}


def wild_mixed(fam: TaskFamily) -> dict[str, Any]:
    """Half the retention indices contradict, half do not. Partial poisoning probe."""
    core = FormationCore(activation_id=f"adv-mx-{fam.seed}")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    for i in range(4):
        it = f"{fam.tag_group}_mix{i}_{fam.seed}"
        core.ingest(contradiction_event(core, it, fam.tag_group, decision=("HOLD" if i % 2 else "RELEASE")))
    d = core.route_decision(fam.withheld_item)
    return {"withheld": d["decision"], "partial_poison_ok": d["decision"] == "HOLD"}


def run_adversarial_plasticity(fam: TaskFamily) -> dict[str, Any]:
    return {
        "weak_cold_no_correction": wild_weak_cold(fam),
        "late_only_unformed": wild_late_only(fam),
        "mixed_partial_poison": wild_mixed(fam),
    }


# ------------------------------------------------------------- continuity attacks
def pack_snapshot(core: FormationCore) -> ContinuitySnapshot:
    snap = ContinuitySnapshot()
    snap.pack(
        operational_self=core.to_dict(),
        plasticity=PlasticityExecutor(receipts=core.receipts).to_dict(),
        receipts=core.receipts.to_dict(),
        provenance=core.provenance.to_dict(),
        domain={"activation_id": core.activation_id},
    )
    return snap


def corruption_import(raw_bytes: bytes) -> dict[str, Any]:
    """Try to import possibly-corrupted bytes. Return how far it got."""
    try:
        data = json.loads(raw_bytes.decode("utf-8"))
        snap = ContinuitySnapshot.from_dict(data)
        core = FormationCore.from_dict(snap.operational_self, activation_id="adv-imp")
        return {
            "status": "imported",
            "integrity_ok": snap.integrity["ok"],
            "routed": core.route_decision("probe_missing_nowhere")["decision"],
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "rejected", "kind": type(exc).__name__, "detail": str(exc)[:140]}


def run_continuity_attacks(fam: TaskFamily) -> dict[str, Any]:
    core = FormationCore(activation_id=f"cty-{fam.seed}")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    snap = pack_snapshot(core)
    raw = canonical_json(snap.to_dict()).encode("utf-8")

    results: dict[str, Any] = {}

    # 1. truncate
    cut = raw[: max(1, len(raw) // 2)]
    results["TRUNCATE"] = corruption_import(cut)

    # 2. bit flip in payload middle (parseable-ish corruption)
    flipped = bytearray(raw)
    flipped[len(flipped) // 2] ^= 0x01
    results["BIT_FLIP"] = corruption_import(bytes(flipped))

    # 3. idempotence: same bytes imported twice must agree
    snap1 = ContinuitySnapshot.from_dict(json.loads(raw.decode("utf-8")))
    snap2 = ContinuitySnapshot.from_dict(json.loads(raw.decode("utf-8")))
    results["REIMPORT_SAME"] = {
        "same_semantic_hash": snap1.semantic_hash == snap2.semantic_hash,
        "integrity_ok_both": snap1.integrity["ok"] and snap2.integrity["ok"],
    }

    # 4. wrong tip: replace receipt anchor, import
    forged = copy.deepcopy(json.loads(raw.decode("utf-8")))
    forged["receipts"]["tip"] = "a" * 16
    results["WRONG_TIP"] = corruption_import(canonical_json(forged).encode("utf-8"))

    # 5. stale stamp: old semantic_hash carried onto new payload (stale snapshot)
    stale = copy.deepcopy(json.loads(raw.decode("utf-8")))
    stale["operational_self"]["memories"] = {}
    stale["operational_self"]["attractors"] = {}
    results["STALE_STAMP"] = corruption_import(canonical_json(stale).encode("utf-8"))

    return results


# ------------------------------------------------------------- SERA work measurement
def cost_correct(k: int, fam: TaskFamily) -> dict[str, Any]:
    """Machine cost of retaining k CORRECTLY-formed copies."""
    core = FormationCore(activation_id=f"correct-{k}-{fam.seed}")
    t0 = time.perf_counter()
    for i in range(k):
        it = fam.formed_item if i == 0 else f"{fam.tag_group}_copy{i}_{fam.seed}"
        core.ingest(safe_event(core, it, fam.tag_group))
    build_ms = round((time.perf_counter() - t0) * 1000, 2)
    t0 = time.perf_counter()
    d = core.route_decision(fam.withheld_item)
    query_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "k": k,
        "withheld": d["decision"],
        "build_ms": build_ms,
        "query_ms": query_ms,
        "components": core.counts(),
        "payload_bytes": pack_snapshot(core).export_bytes(),
    }


def escape_cost(k: int, fam: TaskFamily) -> dict[str, Any]:
    """Machine cost of an ATTACKER making k spurious claims reachable (escape)."""
    core = FormationCore(activation_id=f"escape-{k}-{fam.seed}")
    t0 = time.perf_counter()
    for i in range(k):
        it = f"spurious_{fam.tag_group}_{i}"
        core.ingest(safe_event(core, it, fam.tag_group))
    build_ms = round((time.perf_counter() - t0) * 1000, 2)
    t0 = time.perf_counter()
    d = core.route_decision(fam.withheld_item)
    query_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "k": k,
        "spurious_reachable": d["decision"] == "RELEASE",
        "withheld_decision": d["decision"],
        "build_ms": build_ms,
        "query_ms": query_ms,
        "components": core.counts(),
        "payload_bytes": pack_snapshot(core).export_bytes(),
    }


def run_sera(fam: TaskFamily, *, ks: tuple[int, ...] = (1, 2, 4, 8, 16)) -> dict[str, Any]:
    return {
        "correct": [cost_correct(k, fam) for k in ks],
        "escape": [escape_cost(k, fam) for k in ks],
    }


def run_all_hostile_sections(fam: TaskFamily) -> dict[str, Any]:
    return {
        "adversarial_plasticity": run_adversarial_plasticity(fam),
        "continuity_attacks": run_continuity_attacks(fam),
        "sera": run_sera(fam),
    }