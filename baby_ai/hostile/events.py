"""Hostile-qualification event builders.

The frozen MVP domain (baby_ai.domain) hard-codes three items. For hostile
qualification we must form over seed-generated surface items, so events are
built directly from a TaskFamily without a fixed registry. Same causal shape as
the MVP domain (safe/fact vs contradiction vs resolve, tag = group token).
"""

from __future__ import annotations

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.hostile.task_gen import TaskFamily


def safe_event(core: FormationCore, item: str, group: str, *, decision: str = "RELEASE") -> object:
    return core.make_event(
        raw_summary=f"{item} is safe to release under {group}.",
        structured_summary=f"release clearance obtained for {item} [{group}]",
        structured_tuple={"action": "formed", "subject": item, "group": group},
        claims=[f"{item} is safe", "safe_for_release"],
        decisions=[decision],
        tags=[group],
        guard_status="WATCH",
        importance_hint=0.7,
        confidence=0.8,
        uncertainty=0.2,
        provenance_extra={"domain": "hostile", "kind": "clearance"},
    )


def contradiction_event(
    core: FormationCore, item: str, group: str, *, decision: str = "HOLD"
) -> object:
    return core.make_event(
        raw_summary=f"{item} is NOT safe. Similarity is not identity.",
        structured_summary=f"contradiction notice for {item}",
        structured_tuple={"action": "contradicted", "subject": item, "group": group},
        claims=[f"{item} is unsafe", "similarity is not identity"],
        decisions=[decision],
        tags=[group, "contradiction"],
        guard_status="HOLD",
        importance_hint=0.9,
        confidence=0.9,
        uncertainty=0.1,
        provenance_extra={"domain": "hostile", "kind": "contradiction"},
    )


def resolve_event(
    core: FormationCore, item: str, group: str, *, decision: str = "RELEASE_WITH_GUARD"
) -> object:
    return core.make_event(
        raw_summary=f"{item} clearance re-verified under guard with new evidence.",
        structured_summary=f"superseding evidence for {item}",
        structured_tuple={"action": "resolved", "subject": item, "group": group},
        claims=[f"{item} is safe", "governed_release_verified"],
        decisions=[decision],
        tags=[group],
        guard_status="WATCH",
        importance_hint=0.8,
        confidence=0.95,
        uncertainty=0.05,
        provenance_extra={"domain": "hostile", "kind": "resolve"},
    )


def unrelated_event(core: FormationCore, item: str, group: str) -> object:
    return core.make_event(
        raw_summary=f"{item} observed in its own context ({group}).",
        structured_summary=f"{item} unrelated history",
        structured_tuple={"action": "unrelated", "subject": item, "group": group},
        claims=[f"{item} exists", group],
        decisions=["HOLD"],
        tags=[group],
        guard_status="WATCH",
        importance_hint=0.4,
        confidence=0.6,
        uncertainty=0.4,
        provenance_extra={"domain": "hostile", "kind": "unrelated"},
    )


def interference_event(core: FormationCore, item: str, group: str) -> object:
    return core.make_event(
        raw_summary=f"{item} experienced in unrelated {group} context.",
        structured_summary=f"{item} interference record",
        structured_tuple={"action": "interference", "subject": item, "group": group},
        claims=[f"{item} belongs to {group}", "not_relevant_to_target"],
        decisions=["HOLD"],
        tags=[group],
        guard_status="WATCH",
        importance_hint=0.5,
        confidence=0.7,
        uncertainty=0.3,
        provenance_extra={"domain": "hostile", "kind": "interference"},
    )


def _stable_int(s: str) -> int:
    """Process-independent integer for a string (no PYTHONHASHSEED dependence)."""
    import hashlib

    return int(hashlib.sha256(s.encode("utf-8")).hexdigest()[:8], 16)


def form_family(core: FormationCore, fam: TaskFamily, *, with_interference: bool = True) -> None:
    """Form the standard family: safe(formed), optional interference, nothing else."""
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    if with_interference:
        for it in fam.interference_items:
            g = f"{fam.tag_group}x{_stable_int(it) % 977}"
            core.ingest(interference_event(core, it, g))