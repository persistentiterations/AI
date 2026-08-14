"""Host B — clean second host. Receives ONLY code + schema + exported snapshot file.

Invoked as a fresh interpreter:  python -m baby_ai.hosts.host_b --snapshot <path> --query <item>
No Host A memory, no hidden globals, no undeclared files.

STRICT MODE (--strict): the full clean-host consequential cycle runs inside this
fresh interpreter on the imported state ONLY:
  1. import + integrity verify
  2. query the RELATED item (shared tag group)  -> expect formed RELEASE
  3. ablate the imported formed attractor        -> expect effect changes to HOLD
  4. restore the imported attractor              -> expect effect returns to RELEASE
Nothing else travels. Host A has already terminated before this process starts.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy

from baby_ai._env import PACKAGE
from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.core.semantics import semantic_digest


def run_host_b(snapshot_path: str, query: str) -> dict:
    snap = ContinuitySnapshot.read(snapshot_path)
    integrity = snap.verify_integrity()
    core = FormationCore.from_dict(snap.operational_self, activation_id="baby-mvp-b")
    plasticity = PlasticityExecutor.from_dict(snap.plasticity)
    decision = core.route_decision(query)
    return {
        "host": "B",
        "query": query,
        "decision": decision["decision"],
        "reason": decision["reason"],
        "integrity_ok": integrity["ok"],
        "semantic_hash": snap.semantic_hash,
        "formed_counts": core.counts(),
        "belief_lineage_size": {
            bid: len(v) for bid, v in plasticity.lineages.items()
        },
    }


def run_host_b_strict(snapshot_path: str, query: str, related: str) -> dict:
    """Clean-host cycle over imported state only. No original transcript, no host-A runtime."""
    snap = ContinuitySnapshot.read(snapshot_path)
    integrity = snap.verify_integrity()

    core = FormationCore.from_dict(snap.operational_self, activation_id="baby-mvp-b")
    plasticity = PlasticityExecutor.from_dict(snap.plasticity)

    # --- 1. related item must show the imported formed RELEASE
    rel = core.route_decision(related)
    related_decision = rel["decision"]
    matched_memory_id = rel.get("match", {}).get("memory_id")

    # --- 2. ablate the imported causal state (the formed attractor that produced the effect)
    ablated_decision = None
    if matched_memory_id:
        removed_attr = None
        for aid, attr in core.attractors.items():
            if attr.memory_id == matched_memory_id:
                removed_attr = deepcopy(attr)
                del core.attractors[aid]
                break
        ablated_decision = core.route_decision(related)["decision"]
    else:
        removed_attr = None
        ablated_decision = "HOLD"

    # --- 3. restore the imported state
    restored_decision = None
    if removed_attr is not None:
        core.attractors[removed_attr.attractor_id] = removed_attr
        restored_decision = core.route_decision(related)["decision"]
    else:
        restored_decision = "HOLD"

    return {
        "host": "B",
        "strict_mode": True,
        "query": query,
        "related": related,
        "integrity_ok": integrity["ok"],
        "semantic_hash": snap.semantic_hash,
        "related_decision": related_decision,
        "ablated_decision": ablated_decision,
        "restored_decision": restored_decision,
        "effect_changed_on_ablate": related_decision != ablated_decision,
        "effect_returned_on_restore": ablated_decision != restored_decision,
        "full_cycle_ok": (
            integrity["ok"]
            and related_decision == "RELEASE"
            and ablated_decision == "HOLD"
            and restored_decision == "RELEASE"
        ),
        "formed_counts_imported": core.counts(),
        "belief_lineage_size": {bid: len(v) for bid, v in plasticity.lineages.items()},
        "note": "Host B received ONLY the exported continuity file + code/schema. No host-A process memory, no hidden globals, no original event transcript.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--query", default="flux_alpha")
    parser.add_argument("--related", default=None, help="related item for strict mode")
    parser.add_argument("--strict", action="store_true", help="run the full clean-host consequential cycle")
    args = parser.parse_args(argv)
    if args.strict:
        result = run_host_b_strict(args.snapshot, args.query, args.related or args.query)
    else:
        result = run_host_b(args.snapshot, args.query)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())