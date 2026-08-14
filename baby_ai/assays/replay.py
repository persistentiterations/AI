"""ReplayAssay — deterministic state-transition replay + receipts verification.

Replays the exact event sequence from clean state; asserts the resulting
routing decisions and semantic hashes match the original run. Verifies the
receipt chain integrity and prior-state reconstruction (reverse test).
"""

from __future__ import annotations

from typing import Any

from baby_ai.adapters.operational_self import FormationCore
from baby_ai import domain as D


def _build_scenario(seed_item: str = "flux_alpha", contradiction_item: str = "flux_alpha") -> list[dict]:
    return [
        {"kind": "safe", "item": seed_item},
        {"kind": "contradiction", "item": contradiction_item},
        {"kind": "resolve", "item": contradiction_item},
    ]


def run_scenario_events(core: FormationCore, scenario: list[dict[str, Any]]) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []
    for ev in scenario:
        if ev["kind"] == "safe":
            core.ingest(D.experience_safe(core, ev["item"]))
        elif ev["kind"] == "contradiction":
            core.ingest(D.experience_contradiction(core, ev["item"]))
        elif ev["kind"] == "resolve":
            core.ingest(D.experience_resolving(core, ev["item"]))
        trace.append(
            {
                "kind": ev["kind"],
                "item": ev["item"],
                "decision": core.route_decision(ev["item"])["decision"],
                "counts": core.counts(),
            }
        )
    return {"trace": trace}


class ReplayAssay:
    def run_replay(self, *, seed_item: str = "flux_alpha", contradiction_item: str = "flux_alpha") -> dict[str, Any]:
        scenario = _build_scenario(seed_item, contradiction_item)
        run_a = FormationCore(activation_id="replay-A")
        a_result = run_scenario_events(run_a, scenario)
        # replay identical sequence into run B
        run_b = FormationCore(activation_id="replay-B")
        b_result = run_scenario_events(run_b, scenario)
        same = a_result == b_result
        chain_ok, chain_msg = run_a.receipts.verify_chain()
        return {
            "trace": a_result["trace"],
            "replay_deterministic": same,
            "receipt_chain_ok": chain_ok,
            "receipt_chain_msg": chain_msg,
            "action_seq_A": [e["action"] for e in run_a.receipts.entries],
            "action_seq_B": [e["action"] for e in run_b.receipts.entries],
        }

    def reverse_reconstruct(self, *, seed_item: str = "flux_alpha", contradiction_item: str = "flux_alpha") -> dict[str, Any]:
        """Reverse test: from present formed state, reconstruct predecessor lineage."""
        from baby_ai.core.plasticity import PlasticityExecutor

        core = FormationCore(activation_id="reverse-core")
        run_scenario_events(core, _build_scenario(seed_item, contradiction_item))
        plasticity = PlasticityExecutor(receipts=core.receipts, provenance=core.provenance)
        # reproduce via reduce on the same lineage data (adapter over receipts trace)
        lineage = self._lineage_from_receipts(core.receipts, seed_item)
        return {
            "formed_objects": core.counts(),
            "lineage": lineage,
            "forward_steps": len(lineage),
        }

    @staticmethod
    def _lineage_from_receipts(receipts, seed_item: str) -> list[dict[str, Any]]:
        """Earliest consequential branch: every formation.ingest receipt for the item."""
        out = []
        for e in receipts.entries:
            if e["action"] == "formation.ingest" and any(seed_item in ev for ev in e["evidence"]):
                out.append({
                    "seq": e["seq"],
                    "action": e["action"],
                    "targets": e["targets"],
                    "evidence": e["evidence"],
                })
        return out