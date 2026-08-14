"""SubstrateAdapter — reuse CNTM cnt_morphology (live FractalishBuild superset)
as a SUBSTRATE RECONSTRUCTION / ASSAY organ.

Reused read-only:
  * run_simulation            -> MorphologyGraph (full JSON serialization via to_dict)
  * _graph_from_dict           -> reconstruct exact MorphologyGraph from dict
  * load_run_artifacts         -> host-neutral multi-file run artifacts
  * save_final_state           -> natural math persistent attractor node-state export
  * replay_signature           -> perturbation gradient (causal sensitivity)
  * run_replay_probes          -> exact/noisy/perturbation/null/random/shuffled/cross-generator

new code in this module: rich wrappers for snapshot round-trip + digest.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from baby_ai._env import PACKAGE
from baby_ai.core.provenance import ProvenanceLedger
from baby_ai.core.receipts import ReceiptLedger

from fractalish_ai.cnt_morphology.simulator import CNTEdge, CNTNode, MorphologyGraph, run_simulation
from fractalish_ai.cnt_morphology.perturbation import (
    _graph_from_dict,
    load_run_artifacts,
    perturb_graph,
    replay_signature,
)
from fractalish_ai.cnt_morphology.features import extract_features
from fractalish_ai.cnt_morphology.conductance import compute_conductance
from fractalish_ai.cnt_morphology.glyphs import build_basin_signature
from fractalish_ai.cnt_morphology.growth_rules import GROWTH_PROFILES

MORPH_PROFILES = list(GROWTH_PROFILES.keys())


class SubstrateAdapter:
    def __init__(self, receipts: ReceiptLedger | None = None, provenance: ProvenanceLedger | None = None) -> None:
        self.receipts = receipts or ReceiptLedger()
        self.provenance = provenance or ProvenanceLedger(self.receipts)
        self._record_provenance()

    def _record_provenance(self) -> None:
        import baby_ai._env as env

        sha = env._ORGANS.get("LIVE_FRACTICALISHBUILD_SUPERSET", {}).get("package_sha256")
        self.provenance.record(
            component="SubstrateAdapter",
            organ="LIVE FRACTICALISH/CNTM SUPERSET (cnt_morphology)",
            reuse_kind="import",
            path=str(env.LIVE_FRACTICALISHBUILD_TREE),
            sha256=sha,
            modifications="adapter wrappers only; organ untouched",
        )

    # ------------------------------------------------------------ substrate
    def grow(self, *, profile: str = "aligned_forest", seed: int = 42, steps: int = 40, persistence: dict | None = None) -> dict[str, Any]:
        from fractalish_ai.cnt_morphology.schemas import PersistenceConfig

        cfg = PersistenceConfig(**persistence) if persistence else None
        result = run_simulation(profile, seed=seed, steps=steps, persistence=cfg)
        return self._snapshot_graph(result.graph)

    def _snapshot_graph(self, graph: MorphologyGraph) -> dict[str, Any]:
        return graph.to_dict()

    def graph_to_dict(self, graph: MorphologyGraph) -> dict[str, Any]:
        return graph.to_dict()

    # ------------------------------------------------------- reconstruction
    def reconstruct(self, data: dict[str, Any]) -> MorphologyGraph:
        """Host-neutral full MorphologyGraph reconstruction (Gap B substrate layer)."""
        nodes = [CNTNode(**n) for n in data["nodes"]]
        edges = [CNTEdge(**e) for e in data["edges"]]
        return MorphologyGraph(
            nodes=nodes,
            edges=edges,
            profile=data["profile"],
            seed=data["seed"],
            steps_run=data.get("steps_run", 0),
            operator_counts=data.get("operator_counts", {}),
        )

    def roundtrip_digest(self, data: dict[str, Any]) -> dict[str, Any]:
        g = self.reconstruct(data)
        rt = self._snapshot_graph(g)
        same = json.dumps(rt, sort_keys=True, default=str) == json.dumps(data, sort_keys=True, default=str)
        self.receipts.append(
            action="substrate.roundtrip",
            targets=[data.get("profile", ""), str(data.get("seed", ""))],
            evidence=[f"roundtrip_same={same}", f"nodes={len(data.get('nodes', []))}"],
            payload={"same": same},
        )
        return {"roundtrip_same": same, "profile": data.get("profile")}

    # -------------------------------------------------- causal sensitivity
    def replay_probe_gradient(
        self,
        *,
        profile: str = "aligned_forest",
        seed: int = 42,
        steps: int = 40,
        perturbations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Growing run then sequential replay_signature gradients (Gap C morph-layer assay)."""
        result = run_simulation(profile, seed=seed, steps=steps)
        graph = result.graph
        feats = extract_features(graph)
        cond = compute_conductance(graph, method="kirchhoff")
        g = build_basin_signature(feats, cond, GROWTH_PROFILES[profile], seed=seed)
        glyph = {"basin_signature": g["basin_signature"]}
        perturbations = perturbations or [
            {"type": "drop_random_edges", "magnitude": 0.1},
            {"type": "energy_noise", "magnitude": 5.0},
            {"type": "position_jitter", "magnitude": 0.05},
        ]
        result = replay_signature(graph, feats, cond, glyph, perturbations, seed=seed)
        # keep only the interpreted summary for artifacts (steps list can be huge)
        summary = {k: v for k, v in result.items() if k != "steps"}
        summary["warning"] = result.get("warning", "")
        return summary

    # ------------------------------------------------------------------ i/o
    def write_run_artifacts(self, graph: MorphologyGraph, dest_parent: str | Path) -> Path:
        d = Path(dest_parent)
        d.mkdir(parents=True, exist_ok=True)
        (d / "graph.json").write_text(json.dumps(self._snapshot_graph(graph), indent=2), encoding="utf-8")
        return d

    def load_run_artifacts(self, run_dir: str | Path):
        return load_run_artifacts(run_dir)