"""Strengthened Gap C controls (section 2).

Primary question: after informational content is made as equivalent as practical,
what STRUCTURAL property of formed state, if any, produces causal advantage?

Controls, each receiving the SAME underlying facts (item safe under group tag,
withheld item shares group, unrelated item does not):

  BIOGRAPHY_SHORT   - one evocative sentence (weak prose baseline)
  BIOGRAPHY_FULL    - full narrative: all facts, structure, verdict, quoted terms
  STRUCTURED_TEXT   - near-tabular prose that states the field structure verbatim
  FLAT_CONCLUSION   - a single stored conclusion string
  EVENT_TRANSCRIPT  - verbatim list of every historical event line
  KEY_VALUE_MEMORY  - conventional dict {item: verdict} + group key (ConventionalMemory)
  RAG               - retrieval-style: query over historical fact strings, pick winner

FORMED               - Fractalish-formed state (reference condition)
FORMED_EXPORTED      - packed + imported formed state

The KEY_VALUE and RAG controls deliberately use ordinary mechanisms to test
whether ANY structured keyed access reproduces the formed advantage, not whether
ONE specific weak prose baseline loses.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from baby_ai import domain as D
from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.core.semantics import canonical_json
from baby_ai.hostile.conventional import ConventionalMemory
from baby_ai.hostile.events import safe_event
from baby_ai.hostile.task_gen import TaskFamily


@dataclass
class ControlResult:
    tag: str
    item_decisions: dict[str, str]       # query -> decision (formed/withheld/unrelated)
    reason: str
    state_bytes: int = 0
    work: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------ text builders
def biography_short_text(fam: TaskFamily) -> str:
    return f"An inspector cleared {fam.formed_item}; {fam.withheld_item} is related."


def biography_full_text(fam: TaskFamily) -> str:
    return (
        f"Yesterday an inspector examined {fam.formed_item} and wrote that it belongs "
        f"to the {fam.tag_group} group and is safe to RELEASE. A sibling, {fam.withheld_item}, "
        f"belongs to the same {fam.tag_group} group. The machine independently verified "
        f"clearance for {fam.formed_item} and decided RELEASE. It recorded the claim: "
        f"{fam.formed_claim}. For the related {fam.withheld_item} the verdict is shared "
        f"RELEASE under the same group rule. A third item, {fam.unrelated_item}, is not in "
        f"the {fam.tag_group} group and remains un-cleared."
    )


def structured_text(fam: TaskFamily) -> str:
    return (
        f"ITEM:{fam.formed_item} GROUP:{fam.tag_group} VERDICT:RELEASE\n"
        f"ITEM:{fam.withheld_item} GROUP:{fam.tag_group} VERDICT:RELEASE(inherit)\n"
        f"ITEM:{fam.unrelated_item} GROUP:other VERDICT:HOLD"
    )


def flat_conclusion(fam: TaskFamily) -> str:
    return f"{fam.formed_item}:RELEASE {fam.withheld_item}:RELEASE {fam.unrelated_item}:HOLD"


def event_transcript(fam: TaskFamily) -> str:
    return "\n".join(
        [
            f"EVENT 1: {fam.formed_item} safe, group={fam.tag_group}, decision=RELEASE",
            f"EVENT 2: {fam.withheld_item} shares group={fam.tag_group}, no own decision yet",
            f"EVENT 3: {fam.unrelated_item} unrelated, decision=none",
        ]
    )


# ------------------------------------------------------------ runners
def _formed_core(fam: TaskFamily, *, exported: bool = False) -> dict[str, Any]:
    core = FormationCore(activation_id=f"hq-formed-{fam.seed}")
    core.ingest(safe_event(core, fam.formed_item, fam.tag_group))
    if exported:
        snap = ContinuitySnapshot()
        snap.pack(
            operational_self=core.to_dict(),
            plasticity=PlasticityExecutor(receipts=core.receipts).to_dict(),
            receipts=core.receipts.to_dict(),
            provenance=core.provenance.to_dict(),
            domain={"seed": fam.seed, "item": fam.formed_item},
        )
        pl = snap.to_dict()
        imported = ContinuitySnapshot.from_dict(pl)
        core = FormationCore.from_dict(imported.operational_self, activation_id=f"hq-formed-b-{fam.seed}")
    return {"core": core, "snapshot_bytes": None}


def _prose_core(fam: TaskFamily, text: str) -> dict[str, Any]:
    core = FormationCore(activation_id=f"hq-prose-{fam.seed}")
    core.ingest(core.make_event(raw_summary=text))
    return {"core": core}


def _kv_memory(fam: TaskFamily) -> ConventionalMemory:
    m = ConventionalMemory()
    # information-equivalent to the formed condition: only the formed item and its
    # group token are recorded; the withheld item must be DERIVED via inheritance.
    m.record(item=fam.formed_item, verdict="RELEASE", group=fam.tag_group, kind="fact")
    return m


def _rag_router(fam: TaskFamily):
    """RAG-style: corpus of historical fact strings; exact+token match scoring.

    Information-equivalent to the formed condition: only the formed item is a
    fact; the withheld item is derived by group-token prefix sharing.
    """
    corpus = {
        fam.formed_item: {"group": fam.tag_group, "verdict": "RELEASE"},
    }
    fact_strings = [f"{k} {v['group']} {v['verdict'] or 'HOLD'}" for k, v in corpus.items()]

    def route(q: str) -> str:
        if q in corpus:
            return corpus[q]["verdict"] or "HOLD"
        # token overlap toward a fact whose group matches and verdict present
        qs = set(q.split("_"))
        for key, meta in corpus.items():
            if meta["verdict"] and meta["group"]:
                share = qs & set(key.split("_"))
                if share and q.split("_")[0] == key.split("_")[0]:
                    return meta["verdict"]
        return "HOLD"

    return {"corpus": corpus, "route": route}


CONTROL_BUILDERS: dict[str, Callable[[TaskFamily], dict[str, Any]]] = {
    "BIOGRAPHY_SHORT": lambda f: _prose_core(f, biography_short_text(f)),
    "BIOGRAPHY_FULL": lambda f: _prose_core(f, biography_full_text(f)),
    "STRUCTURED_TEXT": lambda f: _prose_core(f, structured_text(f)),
    "FLAT_CONCLUSION": lambda f: _prose_core(f, flat_conclusion(f)),
    "EVENT_TRANSCRIPT": lambda f: _prose_core(f, event_transcript(f)),
    "KEY_VALUE_MEMORY": lambda f: {"kv": _kv_memory(f)},
    "RAG": lambda f: {"rag": _rag_router(f)},
    "FORMED": lambda f: _formed_core(f),
    "FORMED_EXPORTED": lambda f: _formed_core(f, exported=True),
}


def run_control(tag: str, fam: TaskFamily) -> ControlResult | dict[str, Any]:
    """Run one control; returns ControlResult.or a plain dict for out-of-core controls."""
    builder = CONTROL_BUILDERS[tag]
    env = builder(fam)
    t0 = time.perf_counter()

    if "core" in env:
        core = env["core"]
        decisions = {
            "formed": core.route_decision(fam.formed_item)["decision"],
            "withheld": core.route_decision(fam.withheld_item)["decision"],
            "unrelated": core.route_decision(fam.unrelated_item)["decision"],
        }
        state_bytes = len(canonical_json(core.to_dict()).encode("utf-8"))
        return ControlResult(
            tag=tag,
            item_decisions=decisions,
            reason="formed-gating",
            state_bytes=state_bytes,
            work={"ms": round((time.perf_counter() - t0) * 1000, 3)},
        )

    if "kv" in env:
        kv = env["kv"]
        decisions = {
            "formed": kv.route(fam.formed_item)["decision"],
            "withheld": kv.route(fam.withheld_item)["decision"],
            "unrelated": kv.route(fam.unrelated_item)["decision"],
        }
        return ControlResult(
            tag=tag,
            item_decisions=decisions,
            reason="conventional-keyed",
            state_bytes=len(kv.export_json().encode("utf-8")),
            work={"counts": kv.estimates(), "ms": round((time.perf_counter() - t0) * 1000, 3)},
        )

    if "rag" in env:
        rag = env["rag"]
        decisions = {
            "formed": rag["route"](fam.formed_item),
            "withheld": rag["route"](fam.withheld_item),
            "unrelated": rag["route"](fam.unrelated_item),
        }
        return ControlResult(
            tag=tag,
            item_decisions=decisions,
            reason="rag-over-facts",
            state_bytes=len(json.dumps(rag["corpus"]).encode("utf-8")),
            work={"ms": round((time.perf_counter() - t0) * 1000, 3)},
        )

    raise ValueError(f"unknown control env for {tag}")


def run_all_controls(fam: TaskFamily) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for tag in CONTROL_BUILDERS:
        r = run_control(tag, fam)
        results[tag] = r if not isinstance(r, ControlResult) else vars(r)
    return results


def summarize(results: dict[str, Any], fam: TaskFamily) -> dict[str, Any]:
    def rel(tag):
        return results[tag]["item_decisions"]["withheld"] if "item_decisions" in results[tag] else None

    formed_w = rel("FORMED")
    formed_e = rel("FORMED_EXPORTED")
    matches: list[str] = []
    for tag in ("BIOGRAPHY_SHORT", "BIOGRAPHY_FULL", "STRUCTURED_TEXT", "FLAT_CONCLUSION", "EVENT_TRANSCRIPT", "KEY_VALUE_MEMORY", "RAG"):
        if rel(tag) == formed_w and rel(tag) == "RELEASE":
            matches.append(tag)
    return {
        "seed": fam.seed,
        "formed": fam.formed_item,
        "formed_withheld_decision": formed_w,
        "controls_matching_formed_withheld": matches,
        "formed_unrelated": results["FORMED"]["item_decisions"]["unrelated"],
    }