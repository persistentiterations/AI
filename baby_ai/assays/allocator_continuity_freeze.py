"""Deterministic-regeneratable freeze for the R-001 allocator-continuity tranche.

Writes BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1 under baby_ai/artifacts/repair/.
The WITNESS_ALLOCATOR_CONTINUITY.json is byte-deterministic (no wall-clock or
random inputs); FREEZE_MANIFEST.json carries a creation timestamp and is not
byte-deterministic by convention (matching the other freeze tranches).
"""
import hashlib
import json
import os
import sys
import datetime
import platform

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from baby_ai import domain as D
from baby_ai.adapters.operational_self import FormationCore

PACK = "BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1"
OUT = os.path.join(REPO, "baby_ai", "artifacts", "repair", PACK)
os.makedirs(OUT, exist_ok=True)

ALLOCATOR_PREFIXES = ("mem", "attr", "fog", "scar", "lnk", "replay", "evt")

# Observed device evidence (from the G7 device investigation; NOT fixture output).
DEVICE_OBSERVATION = {
    "handset": "ZY22HFN93K (moto g stylus 2023, XT2317-2, Android 14)",
    "deployed_package": "llc.bonacqui.aptd 0.1.0-aptd",
    "deployed_bytecode": "pre-R-001 (operational_self.pyc lacks id_continuation)",
    "memories_observed": 90073,
    "fog_objects_observed": 100395,
    "duplicate_fog_id_suffixes_observed": 10322,
    "provenance_ledger_bytes_observed": 18,
}


def _sha8(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]


def _suffix(family, raw):
    for sep in ("-", "_"):
        m = family + sep
        if raw.startswith(m):
            return int(raw[len(m):])
    raise ValueError(raw)


def build_witness():
    # 1. Build inherited state with allocated ids across families.
    src = FormationCore(activation_id="witness-src")
    for item in ("flux_alpha", "flux_beta", "dura_gamma"):
        src.ingest(D.experience_safe(src, item))
        src.ingest(D.experience_contradiction(src, item))
    payload = src.to_dict()
    inherited_mem = sorted(src.memories.keys())
    inherited_fog = [f.fog_id for f in src.fog]

    # 2. OLD / pre-R-001 reload: collections restored, id stream left empty.
    old = FormationCore(activation_id="witness-old")
    old.memories.update(src.memories)
    old.attractors.update(src.attractors)
    old.fog.extend(src.fog)
    old.links.extend(src.links)
    old.scars.extend(src.scars)
    old.routes.extend(src.routes)
    old_mem_collision = old.ingest(D.experience_safe(old, "flux_alpha"))["memory_id"] in set(inherited_mem)
    old_fog_ids = [f.fog_id for f in old.fog]
    old_fog_duplicates = len(old_fog_ids) - len(set(old_fog_ids))

    # 3. R-001 reload via from_dict: continuation established, no collision.
    loaded = FormationCore.from_dict(payload, activation_id="witness-r001")
    new_id = loaded.ingest(D.experience_safe(loaded, "flux_alpha"))["memory_id"]
    new_fog_ids = [f.fog_id for f in loaded.fog]
    max_inherited_suffix = max(_suffix("mem", m) for m in inherited_mem)

    return {
        "tranche": "R001_ALLOCATOR_CONTINUITY",
        "invariant": (
            "After serialized state is reloaded, newly allocated identifiers "
            "continue from authoritative persisted allocator state and cannot "
            "collide with identifiers already present in retained state."
        ),
        "governed_families": list(ALLOCATOR_PREFIXES),
        "device_observation": DEVICE_OBSERVATION,
        "fixture": {
            "source_events": [
                "experience_safe(flux_alpha)", "experience_contradiction(flux_alpha)",
                "experience_safe(flux_beta)", "experience_contradiction(flux_beta)",
                "experience_safe(dura_gamma)", "experience_contradiction(dura_gamma)",
            ],
            "inherited_mem_count": len(inherited_mem),
            "inherited_fog_count": len(inherited_fog),
        },
        "pre_R001_reload": {
            "counters_empty": True,
            "memory_id_collision": old_mem_collision,
            "fog_duplicate_suffixes": old_fog_duplicates,
        },
        "r001_reload": {
            "allocator_status_kind": loaded.allocator_status["kind"],
            "formation_ready": loaded.formation_ready(),
            "memory_id_collision": new_id in set(inherited_mem),
            "next_memory_id": new_id,
            "max_inherited_suffix": max_inherited_suffix,
            "continues_beyond_retained": _suffix("mem", new_id) > max_inherited_suffix,
            "fog_duplicate_suffixes": len(new_fog_ids) - len(set(new_fog_ids)),
        },
    }


def build_manifest(git_head):
    src = [
        "baby_ai/adapters/operational_self.py",
        "baby_ai/core/migration_receipts.py",
        "baby_ai/tests/test_formation.py",
        "baby_ai/qualifications/r001_closure.py",
        "baby_ai/assays/allocator_continuity_freeze.py",
    ]
    return {
        "repair_id": PACK,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "philosophy": (
            "Formation survived on-device; allocator identity did not. R-001 repairs "
            "the reset-on-load id allocator by carrying an explicit, versioned "
            "id_continuation block and reconciling it at the load boundary."
        ),
        "scope": "ALLOCATOR CONTINUITY ONLY. No route/cause/authority semantics changed.",
        "governed_families": list(ALLOCATOR_PREFIXES),
        "legacy_handling": (
            "No id_continuation -> derive next-index = max(existing suffix) + 1 per family."
        ),
        "malformed_handling": (
            "Malformed/partial/stale/negative/overflow continuation -> REJECT: the core "
            "enters formation_blocked and answers HOLD only; never silent id reuse."
        ),
        "migration_handling": (
            "Operator-supplied counter values require a permanent MigrationReceipt "
            "(pre/post state hash, family, observed floor, supplied value, reason, "
            "authorization, timestamp). See MIGRATION_POLICY.json."
        ),
        "constraints_satisfied": {
            "no_scar_deletion": True,
            "prior_authority_semantics_unchanged": True,
            "ladder_representations_untouched": True,
            "deterministic_witness": True,
            "host_only": True,
        },
        "source_hashes": {p: _sha8(os.path.join(REPO, p)) for p in src},
        "evidence_files": [
            "WITNESS_ALLOCATOR_CONTINUITY.json",
            "TEST_RECEIPT.json",
            "MIGRATION_POLICY.json",
            "DIRTY_TREE_PREFLIGHT.json",
            "BABY_AI_ALLOCATOR_CONTINUITY_R001_FREEZE_REPORT.md",
            "FREEZE_MANIFEST.json",
        ],
        "prior_authority": {
            "implementation_sha": "9d6317351f74032c77883db198d637777af4a33b",
            "freeze_package": "BABY_AI_FORMATIONCORE_CROSS_CONTEXT_RESOLVE_v0_1",
        },
        "git_head": git_head,
        "python": platform.python_version(),
        "platform": sys.platform,
    }


def main():
    witness = build_witness()
    with open(os.path.join(OUT, "WITNESS_ALLOCATOR_CONTINUITY.json"), "w", encoding="utf-8") as f:
        json.dump(witness, f, indent=2, sort_keys=True)
    manifest = build_manifest(None)
    with open(os.path.join(OUT, "FREEZE_MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print("wrote", PACK)
    for n in ("WITNESS_ALLOCATOR_CONTINUITY.json", "FREEZE_MANIFEST.json"):
        print("  -", n)


if __name__ == "__main__":
    main()
