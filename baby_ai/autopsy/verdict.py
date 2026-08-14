"""Explicit scientific verdict of the hostile qualification, recorded without
attempting to rescue weakened claims. The autopsy proceeds from here."""

from __future__ import annotations

from typing import Any

SCIENTIFIC_VERDICT: dict[str, Any] = {
    "baseline": "BABY_AI_HOSTILE_QUALIFICATION_v0_1",
    "baseline_commit": "fe8d596",
    "date": "2026-08-14",
    "phase": "BABY_AI_AUTOPSY_v0_1",
    "gaps": {
        "GAP_A_plasticity_corrigibility": {
            "verdict": "SURVIVES",
            "detail": "mechanism survives hostile tests at 24 frozen seeds; weak-cold contradiction scar blocks routing with history preserved; late-only contradiction never leaks to unformed items; partial tag poisoning insufficient.",
        },
        "GAP_B_second_host_restore": {
            "verdict": "SURVIVES",
            "detail": "mechanism survives hostile tests at 24 frozen seeds; truncation rejected, bit-flip/stale-stamp/wrong-tip fail loudly (integrity or JSON rejection), re-import idempotent.",
        },
        "GAP_C_transfer_advantage": {
            "verdict": "STRONG CLAIM WEAKENED / NOT DEMONSTRATED",
            "detail": "a competent conventional keyed-memory implementation (ConventionalMemory) reproduced all six demonstrated advantages with LOWER measured work (mean 3 vs 8 components). The Fractalish formed-state topology is not shown to be required.",
        },
    },
    "current_surviving_transfer_observation": (
        "unstructured prose does not reproduce the effect; structured operational "
        "records do. This does NOT establish that Fractalish formed-state topology "
        "is required."
    ),
    "additional_recorded_findings": {
        "relations_not_load_bearing": (
            "relation/link structure is not presently load-bearing in the assay; "
            "shuffling links leaves routing unchanged."
        ),
        "literal_semantic_coupling": (
            "literal RELEASE-family semantic coupling remains load-bearing and was "
            "exposed by surface randomization (24/24 label coupling)."
        ),
    },
    "research_question": (
        "What is the minimum machinery actually required for every demonstrated "
        "behavior? We seek subtraction, not a harder test engineered to make "
        "Fractalish win."
    ),
    "claim_discipline": (
        "A result that says 'the whole thing reduces to a small conventional state "
        "machine' is a SUCCESSFUL result. Protect only the phenomenon demonstrated "
        "by experiment."
    ),
}


def emit_verdict() -> dict[str, Any]:
    return SCIENTIFIC_VERDICT


if __name__ == "__main__":
    import json

    print(json.dumps(emit_verdict(), indent=2, default=str))