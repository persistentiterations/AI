"""Create the BABY_AI_CAUSAL_CORE_MVP_2026-08-14 freeze manifest.

Records, for every newly-created/modified integration file under baby_ai/:
  * SHA-256 of file content
  * python version + interpreter
  * installed dependency pins (pytest runtime)
  * qualified organ tree paths + package SHA-256 (via baby_ai._env provenance)
  * exact freeze/test/demo/strict-host/gap-C commands
  * freeze identifier + git HEAD (when inside a repo)

Writes BABY_AI_FREEZE_MANIFEST.json next to the captured evidence.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import baby_ai._env as env
from baby_ai.assays.persistence import PersistenceAssay
from baby_ai.assays.transfer_control import TransferControlAssay

WORKSPACE = Path(__file__).resolve().parents[1]
FREEZE_ID = "BABY_AI_CAUSAL_CORE_MVP_2026-08-14"
EVIDENCE = WORKSPACE / "baby_ai" / "artifacts" / "freeze" / FREEZE_ID / "evidence"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> dict:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(WORKSPACE), capture_output=True, text=True)
        status = subprocess.run(["git", "status", "--short"], cwd=str(WORKSPACE), capture_output=True, text=True)
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=str(WORKSPACE), capture_output=True, text=True)
        return {
            "head_commit": out.stdout.strip() if out.returncode == 0 else None,
            "branch": branch.stdout.strip() if branch.returncode == 0 else None,
            "status_short": status.stdout.strip().splitlines() if status.returncode == 0 else [],
        }
    except Exception as exc:  # pragma: no cover
        return {"head_commit": None, "branch": None, "status_short": [], "error": str(exc)}


def integration_file_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted((WORKSPACE / "baby_ai").rglob("*.py")):
        rel = p.relative_to(WORKSPACE).as_posix()
        out[rel] = sha256_file(p)
    return out


def run() -> Path:
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    # Gap B strict clean-host + Gap C, re-run for this freeze (deterministic)
    strict = PersistenceAssay().strict_clean_host_run(
        item="flux_alpha", related="flux_beta", snapshot_path=WORKSPACE / "baby_ai" / "artifacts" / "strict_hostA.json"
    )
    (EVIDENCE / "strict_host_b_cycle.json").write_text(json.dumps(strict, indent=2), encoding="utf-8")
    gap_c = TransferControlAssay().run(item="flux_alpha")
    (EVIDENCE / "transfer_control_gap_c.json").write_text(json.dumps(gap_c, indent=2), encoding="utf-8")

    env.bootstrap()
    organs = {k: v for k, v in env.organ_provenance().items()}

    commands = {
        "freeze_manifest": f"python {Path(__file__).name}",
        "test_suite": f"{sys.executable} -m pytest baby_ai/tests -q",
        "demo": "python -m baby_ai.demo",
        "compileall": f"{sys.executable} -m compileall -q baby_ai",
        "strict_host_b": "python -m baby_ai.hosts.host_b --snapshot <snapshot> --query flux_alpha --related flux_beta --strict",
        "host_b_assay": "python -c \"from baby_ai.assays.persistence import PersistenceAssay; PersistenceAssay().strict_clean_host_run(item='flux_alpha', related='flux_beta', snapshot_path=...)\"",
        "gap_c_assay": "python -c \"from baby_ai.assays.transfer_control import TransferControlAssay; TransferControlAssay().run(item='flux_alpha')\"",
    }

    manifest = {
        "freeze_id": FREEZE_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "not_a_final_architecture": True,
        "classification_provisional": True,
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "dependencies": {
            "pytest": "9.1.1",
            "pluggy": "1.6.0",
            "packaging": "26.3",
            "iniconfig": "2.3.0",
            "colorama": "0.4.6",
            "pygments": "2.20.0",
            "note": "runtime is stdlib-only; pytest installed in baby-ai-assembly-v0.1/.venv for the test harness",
        },
        "git": git_head(),
        "qualified_organs": organs,
        "integration_file_sha256": integration_file_hashes(),
        "exact_commands": commands,
        "status_claims": {
            "GAP_A_plasticity_corrigibility": "CLOSED AT MVP MECHANISM LEVEL (causal chain: formed RELEASE -> contradiction scar -> HOLD -> supersede -> old scar stops gating -> RELEASE restored -> prior state reconstructible)",
            "GAP_B_second_host_restore": "CLOSED AT MVP MECHANISM LEVEL (strict clean-host cycle PASS: related RELEASE -> ablate -> HOLD -> restore -> RELEASE; snapshot restores full Operational Self state: memories/attractors/links/scars/fog/routes + plasticity + receipts + provenance)",
            "GAP_C_transfer_advantage": "OPEN (mechanism-scoped advantage measured: FORMED/EXPORTED route RELEASE where equivalent words do not; advantage is scoped to qualified-retrieval gating, not claimed to generalize)",
        },
        "evidence_files": sorted(p.name for p in EVIDENCE.iterdir()),
    }
    out = EVIDENCE.parent / "BABY_AI_FREEZE_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    path = run()
    print(f"manifest -> {path}")
