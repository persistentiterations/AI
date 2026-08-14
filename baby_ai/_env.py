"""Environment bootstrap + organ provenance for baby_ai.

Imports the qualified organ trees read-only (Windows paths with spaces are fine
via sys.path). Records cryptographic provenance of the reused organs at import
time so every artifact produced by this workspace is traceable to exact sources.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]  # baby-ai-assembly-v0.1
PACKAGE = Path(__file__).resolve().parents[1] / "baby_ai"

# Qualified / frozen sources (read-only). Do NOT write here.
OLD_FRACTALISH_AI_TREE = Path(
    r"C:\Users\moop\Downloads\Articles on X.com\F R A C T A L I S H - - - A I - - - FRACTALISH-AI"
    r"\fractalish-ai\fractalish ai"
)
LIVE_FRACTALISHBUILD_TREE = Path(r"C:\Users\moop\FractalishBuild\fractalish-ai")
CONFIGURATOR_V1_2 = Path(
    r"C:\Users\moop\Downloads\Articles on X.com\Machine Consciousness as Persistent Statehood"
    r"\Configurator\configurator_v1_2_SYMLAN_BRIDGE.py"
)
CONFIGURATOR_V1_2_ALT = Path(
    r"C:\Users\moop\Downloads\Articles on X.com\Cognitive_Basin and Coherence\Configurator"
    r"\configurator_v1_2_SYMLAN_BRIDGE.py"
)

# Observational metadata keys: excluded from SEMANTIC state digest (see core/semantics.py).
SEMANTIC_OBSERVATIONAL_KEYS = {
    "timestamp",
    "created_at",
    "last_updated",
    "first_seen",
    "last_seen",
    "state_hash",
    "snapshot_id",
    "wall_clock_ms",
}

_ORGANS: dict[str, dict] = {}

# Public alias, matches the historical import surface used by baby_ai/__init__.py.
ORGANS = _ORGANS


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _dir_sha256(root: Path, suffix: str = ".py") -> str:
    """Rolling sha256 over package files (sorted by relpath, excludes __pycache__)."""
    h = hashlib.sha256()
    for rel in sorted(p.relative_to(root).as_posix() for p in root.rglob(f"*{suffix}") if "__pycache__" not in str(p)):
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(_sha256_file(root / rel).encode("ascii"))
        h.update(b"\x00")
    return h.hexdigest()


def _bootstrap_ids() -> dict:
    """Deterministic per-loader seeds for id generators + wall clock (bounded nondeterminism)."""
    return {
        "loader_start_unix": float(time.time()),
        "loader_start_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def bootstrap() -> None:
    """Insert reuse trees onto sys.path and snapshot organ hashes. Idempotent."""
    if _ORGANS:
        return

    roots = [
        OLD_FRACTALISH_AI_TREE,
        LIVE_FRACTALISHBUILD_TREE,
        PACKAGE.parent,  # workspace root (for `import baby_ai`)
    ]
    for root in roots:
        rp = str(root)
        if rp not in sys.path:
            sys.path.insert(0, rp)

    _organs: dict[str, dict] = {
        "OLD_FRACTALISH_AI_PACKAGE": {
            "tree": str(OLD_FRACTALISH_AI_TREE),
            "package_sha256": _dir_sha256(OLD_FRACTALISH_AI_TREE / "fractalish_ai")
            if (OLD_FRACTALISH_AI_TREE / "fractalish_ai").exists()
            else None,
            "shared_file_identity_with_live": _dir_sha256(OLD_FRACTALISH_AI_TREE / "fractalish_ai")
            == _dir_sha256(LIVE_FRACTALISHBUILD_TREE / "fractalish_ai"),
            "usage": "FORMATION CORE (import, read-only). Do not modify.",
            "claim": "qualified 113/113 in qualified tree",
        },
        "LIVE_FRACTALISHBUILD_SUPERSET": {
            "tree": str(LIVE_FRACTALISHBUILD_TREE),
            "package_sha256": _dir_sha256(LIVE_FRACTALISHBUILD_TREE / "fractalish_ai"),
            "usage": "CNTM organelles (cnt_morphology, evolution_prize_validation) + operational_self twin (byte-identical)",
            "claim": "227 passed / 1 suite-external failure (CNTM unreachable threshold, not qualified regression)",
        },
        "CONFIGURATOR_V1_2": {
            "file": str(CONFIGURATOR_V1_2),
            "sha256": _sha256_file(CONFIGURATOR_V1_2) if CONFIGURATOR_V1_2.exists() else None,
            "alt_copy_sha256": _sha256_file(CONFIGURATOR_V1_2_ALT) if CONFIGURATOR_V1_2_ALT.exists() else None,
            "generated_sha256_canonical": "8ec454a528fe00bc55f1c67d483a47f0640bdc622754beefa8e1023024514f79",
            "usage": "RECEIPT-CHAIN PATTERN (ChainedMatchLog/verify_chain/checkpoint) — reimplemented small in baby_ai.core.receipts",
        },
    }
    _ORGANS.update(_organs)


def organ_provenance() -> dict:
    bootstrap()
    return dict(_ORGANS)


def write_provenance_manifest(path: Path | None = None) -> Path:
    """Write organ provenance manifest next to artifacts."""
    import json as _json

    bootstrap()
    out = path or PACKAGE / "artifacts" / "organ_provenance.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_json.dumps(_ORGANS, indent=2), encoding="utf-8")
    return out


def _setup() -> None:
    bootstrap()


_setup()