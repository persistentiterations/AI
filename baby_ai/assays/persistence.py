"""PersistenceAssay (Gap B) — Host A forms state, exports snapshot, process dies,
Host B (fresh subprocess) imports the file and must exhibit consequential behavior.

Simulates process death genuinely: Host B runs in a brand-new interpreter as a
subprocess (no shared globals, no in-memory handoff). Only the exported file,
code, and schema travel.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.core.provenance import ProvenanceLedger
from baby_ai.core.receipts import ReceiptLedger
from baby_ai import domain as D


class PersistenceAssay:
    def __init__(self) -> None:
        self.receipts = ReceiptLedger()
        self.provenance = ProvenanceLedger(self.receipts)
        self._record_provenance()

    def _record_provenance(self) -> None:
        self.provenance.record(
            component="PersistenceAssay",
            organ="baby_ai.core.continuity + baby_ai.hosts.host_b",
            reuse_kind="new_code",
            path=__file__,
            sha256=None,
            modifications="continuity snapshot pack/restore; Host B is a fresh subprocess",
        )

    # ------------------------------------------------------------ Host A
    def host_a_form_and_export(
        self,
        *,
        item: str = "flux_alpha",
        snapshot_path: str | Path,
        extra_contradiction: bool = False,
    ) -> tuple[FormationCore, ContinuitySnapshot, dict[str, Any]]:
        core = FormationCore(activation_id="baby-mvp-A")
        core.ingest(D.experience_safe(core, item))
        before = core.route_decision(item)

        plasticity = PlasticityExecutor(receipts=core.receipts, provenance=core.provenance)
        snap = ContinuitySnapshot()
        snap.pack(
            operational_self=core.to_dict(),
            plasticity=plasticity.to_dict(),
            receipts=core.receipts.to_dict(),
            provenance=core.provenance.to_dict(),
            domain={"item": item, "domain": "warehouse-routing"},
        )
        path = snap.write(snapshot_path)
        return core, snap, {"before_decision": before, "snapshot_path": str(path)}

    # ------------------------------------------------------------ Host B
    def host_b_subprocess(
        self,
        snapshot_path: str | Path,
        query: str,
        *,
        interpreter: str | None = None,
    ) -> dict[str, Any]:
        exe = interpreter or sys.executable
        env = {"PYTHONPATH": ";".join(sys.path), "PYTHONIOENCODING": "utf-8"}
        cmd = [exe, "-m", "baby_ai.hosts.host_b", "--snapshot", str(snapshot_path), "--query", query]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
        if proc.returncode != 0:
            raise RuntimeError(f"Host B failed rc={proc.returncode}: {proc.stderr[-2000:]}")
        result = json.loads(proc.stdout.strip())
        return result

    # ------------------------------------------------ strict clean-host
    def host_b_strict_subprocess(
        self,
        snapshot_path: str | Path,
        query: str,
        related: str,
        *,
        interpreter: str | None = None,
    ) -> dict[str, Any]:
        """Full consequential cycle in a FRESH interpreter on imported state only.

        The child is a brand-new python process: it holds no Host A globals, no
        prior runtime state, no original event transcript. Only the exported
        snapshot file plus code/schema travel. Host A is presumed terminated.
        """
        exe = interpreter or sys.executable
        env = {"PYTHONPATH": ";".join(sys.path), "PYTHONIOENCODING": "utf-8"}
        cmd = [
            exe,
            "-m",
            "baby_ai.hosts.host_b",
            "--snapshot",
            str(snapshot_path),
            "--query",
            query,
            "--related",
            related,
            "--strict",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
        if proc.returncode != 0:
            raise RuntimeError(f"Host B strict failed rc={proc.returncode}: {proc.stderr[-2000:]}")
        return json.loads(proc.stdout.strip())

    def strict_clean_host_run(
        self,
        *,
        item: str = "flux_alpha",
        related: str = "flux_beta",
        snapshot_path: str | Path,
    ) -> dict[str, Any]:
        """Host A forms+exports (in a terminating subprocess), then strict Host B cycle.

        Host A runs in its own interpreter, writes the snapshot file, and EXITS
        before Host B starts — genuine process death is simulated.
        """
        from baby_ai._env import PACKAGE

        p = Path(snapshot_path)
        if not p.is_absolute():
            p = PACKAGE / "artifacts" / p
        exe = sys.executable
        env = {"PYTHONPATH": ";".join(sys.path), "PYTHONIOENCODING": "utf-8"}
        host_a_cmd = [
            exe,
            "-c",
            (
                "import sys; sys.path.insert(0, %r)\n"
                "from baby_ai.assays.persistence import PersistenceAssay\n"
                "PersistenceAssay().host_a_form_and_export(item=%r, snapshot_path=%r)"
            )
            % (str(PACKAGE.parent), item, str(p)),
        ]
        proc_a = subprocess.run(host_a_cmd, capture_output=True, text=True, env=env, timeout=120)
        if proc_a.returncode != 0:
            raise RuntimeError(f"Host A (export) failed rc={proc_a.returncode}: {proc_a.stderr[-2000:]}")
        host_b = self.host_b_strict_subprocess(p, query=item, related=related, interpreter=exe)
        return host_b

    # ------------------------------------------------------------ run
    def run(self, *, item: str = "flux_alpha", snapshot_path: str | Path) -> dict[str, Any]:
        from baby_ai._env import PACKAGE

        p = Path(snapshot_path)
        if not p.is_absolute():
            p = PACKAGE / "artifacts" / p
        core_a, snap, meta_a = self.host_a_form_and_export(item=item, snapshot_path=p)
        host_b = self.host_b_subprocess(p, query=item)

        self.receipts.append(
            action="persistence.hostB",
            targets=[item],
            evidence=[f"integrity_ok={host_b['integrity_ok']}"],
            payload={"host_b": host_b},
        )
        return {
            "host_a_decision_before_export": meta_a["before_decision"],
            "host_b_decision": host_b["decision"],
            "host_b_reason": host_b["reason"],
            "host_b_integrity_ok": host_b["integrity_ok"],
            "survived": host_b["decision"] == meta_a["before_decision"],
            "snapshot_path": meta_a["snapshot_path"],
        }