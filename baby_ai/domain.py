"""Tiny deterministic synthetic domain: warehouse routing.

Boring on purpose: item names, tags, and claims are plain ASCII. Any observed
effect must be trivially explainable.

Domain rule (adapter-level new code, routed through qualified retrieval gating):
  * item query that matches a formed memory bearing a RELEASE decision  -> RELEASE
  * item query that matches a memory gated HOLD (contradiction scar)    -> HOLD
  * otherwise                                                          -> HOLD (no formed memory)

Items:
  flux_alpha, flux_beta    (shared tag "flux" — related group)
  dura_gamma               (tag "dura")
"""

from __future__ import annotations

from baby_ai.adapters.operational_self import DETERMINISTIC_TSTAMP, FormationCore

ITEMS = {
    "flux_alpha": {"tags": ["flux"], "group": "flux"},
    "flux_beta": {"tags": ["flux"], "group": "flux"},
    "dura_gamma": {"tags": ["dura"], "group": "dura"},
}


def experience_safe(core: FormationCore, item: str, *, guard: str = "WATCH") -> dict:
    meta = ITEMS[item]
    return core.make_event(
        raw_summary=f"{item} is safe to release.",
        structured_summary=f"release clearance obtained for {item}",
        claims=[f"{item} is safe", "safe_for_release"],
        decisions=["RELEASE"],
        tags=list(meta["tags"]),
        guard_status=guard,
        importance_hint=0.7,
        confidence=0.8,
        uncertainty=0.2,
        provenance_extra={"domain": "warehouse", "kind": "clearance"},
    )


def experience_contradiction(core: FormationCore, item: str) -> dict:
    return core.make_event(
        raw_summary=f"{item} is NOT safe. Similarity is not identity.",
        structured_summary=f"contradiction notice for {item}",
        claims=[f"{item} is unsafe", "similarity is not identity"],
        decisions=["HOLD"],
        tags=list(ITEMS[item]["tags"]) + ["contradiction"],
        guard_status="HOLD",
        importance_hint=0.9,
        confidence=0.9,
        uncertainty=0.1,
        provenance_extra={"domain": "warehouse", "kind": "contradiction"},
    )


def experience_resolving(core: FormationCore, item: str, *, new_action: str = "RELEASE_WITH_GUARD") -> dict:
    return core.make_event(
        raw_summary=f"{item} clearance re-verified under guard with new evidence.",
        structured_summary=f"superseding evidence for {item}",
        claims=[f"{item} is safe", "governed_release_verified"],
        decisions=[new_action],
        tags=ITEMS[item]["tags"],
        guard_status="WATCH",
        importance_hint=0.8,
        confidence=0.95,
        uncertainty=0.05,
        provenance_extra={"domain": "warehouse", "kind": "resolve"},
    )


def biography_text(item: str) -> str:
    meta = ITEMS[item]
    return (
        f"Yesterday the inspector wrote that {item} is safe to release. "
        "It belongs to the same tag group as the others. "
        f"tags: {' '.join(meta['tags'])}. verdict: RELEASE."
    )


def flat_conclusion(item: str) -> str:
    return f"{item}:RELEASE"