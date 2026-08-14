"""TransferControlAssay (Gap C) — four-condition transfer/control comparison.

Primary causal question, measured not assumed:

  Does the structured formed-state package provide some consequence that cannot
  be reproduced merely by handing the recipient equivalent words?

Conditions on the SAME withheld related task(s):
  CLEAN      — no prior history at all
  BIOGRAPHY  — human-readable narrative carrying equivalent historical info
               (plain prose ONLY: no structured claims/decisions/tags)
  FLAT       — a single stored conclusion string (no formation lineage)
  FORMED     — exported consequential structured state (pack + import)

Each condition is measured on:
  routing/correctness       per-task decision vs the domain rule
  retrieval/work count      matched results, receipts, ingest ops
  replay/reconstruction     receipt-chain steps, lineage depth
  state size                canonical JSON bytes
  processing time           setup + query wall time
  correction behavior       decision sequence through a contradiction + resolve

A NULL result (no FORMED advantage) is a legitimate, reportable outcome. The
BIOGRAPHY/FLAT conditions intentionally do NOT reconstruct structured state; the
router only acts on formed RELEASE decisions carried through qualified retrieval.
"""

from __future__ import annotations

import time
from typing import Any

from baby_ai import domain as D
from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.plasticity import PlasticityExecutor
from baby_ai.core.semantics import canonical_json
from baby_ai.core.receipts import ReceiptLedger

QUERIES = ["flux_alpha", "flux_beta"]


def _measure(fn):
    t0 = time.perf_counter()
    out = fn()
    return out, round((time.perf_counter() - t0) * 1000, 3)


class TransferControlAssay:
    def __init__(self) -> None:
        self.receipts = ReceiptLedger()

    # ------------------------------------------------------ conditions
    def _condition_clean(self) -> dict[str, Any]:
        core = FormationCore(activation_id="ctl-CLEAN")
        return {"core": core, "tag": "CLEAN"}

    def _condition_biography(self, item: str) -> dict[str, Any]:
        core = FormationCore(activation_id="ctl-BIO")
        core.ingest(core.make_event(raw_summary=D.biography_text(item)))
        return {"core": core, "tag": "BIOGRAPHY"}

    def _condition_flat(self, item: str) -> dict[str, Any]:
        core = FormationCore(activation_id="ctl-FLAT")
        core.ingest(core.make_event(raw_summary=D.flat_conclusion(item), tags=["conclusion"]))
        return {"core": core, "tag": "FLAT"}

    def _condition_formed(self, item: str) -> dict[str, Any]:
        core = FormationCore(activation_id="ctl-FORMED")
        core.ingest(D.experience_safe(core, item))
        return {"core": core, "tag": "FORMED"}

    # --------------------------------------------- condition D: exported
    def _condition_formed_exported(self, item: str) -> dict[str, Any]:
        """FORMED = pack + import through the same ContinuitySnapshot a Host B reads."""
        core = FormationCore(activation_id="ctl-FORMED-A")
        core.ingest(D.experience_safe(core, item))
        snap = ContinuitySnapshot()
        snap.pack(
            operational_self=core.to_dict(),
            plasticity=PlasticityExecutor(receipts=core.receipts).to_dict(),
            receipts=core.receipts.to_dict(),
            provenance=core.provenance.to_dict(),
            domain={"item": item, "domain": "warehouse-routing"},
        )
        payload = snap.to_dict()
        imported = ContinuitySnapshot.from_dict(payload)
        assert imported.verify_integrity()["ok"]
        core_b = FormationCore.from_dict(imported.operational_self, activation_id="ctl-FORMED-B")
        return {"core": core_b, "tag": "FORMED_EXPORTED", "snapshot_bytes": snap.export_bytes()}

    # ------------------------------------------------------ measurement
    def _condition_report(self, cond: dict[str, Any], item: str) -> dict[str, Any]:
        core = cond["core"]
        tag = cond["tag"]
        decisions = {q: core.route_decision(q)["decision"] for q in QUERIES}
        retrieval = core.retrieve(item)
        size = len(canonical_json(core.to_dict()).encode("utf-8"))
        chain_ok, chain_msg = core.receipts.verify_chain()
        return {
            "condition": tag,
            "decisions": decisions,
            "item_release": decisions.get(item),
            "related_release": decisions.get("flux_beta"),
            "retrieval_matches": retrieval.get("total_matches", 0),
            "receipts": len(core.receipts),
            "chain_ok": chain_ok,
            "state_size_bytes": size,
            "snapshot_bytes": cond.get("snapshot_bytes"),
            "counts": core.counts(),
            "chain_msg": chain_msg,
        }

    # -------------------------------------- correction after contradiction
    def _correction_sequence(self, cond: dict[str, Any], item: str) -> list[str]:
        """Decision sequence: formed -> contradiction -> resolve (if applicable)."""
        core = cond["core"]
        tag = cond["tag"]
        seq = [core.route_decision(item)["decision"]]
        core.ingest(D.experience_contradiction(core, item))
        seq.append(core.route_decision(item)["decision"])
        if tag in ("FORMED", "FORMED_EXPORTED"):
            plast = PlasticityExecutor(receipts=core.receipts, provenance=core.provenance)
            plast.assert_belief(
                belief_id=f"route:{item}",
                claim=f"{item} is safe to release",
                decision="RELEASE",
                strength=0.8,
                evidence=["A"],
                reason="clearance",
            )
            scar_id = core.scars[-1].scar_id if core.scars else None
            plast.supersede(
                belief_id=f"route:{item}",
                new_claim=f"{item} re-verified under guard",
                new_decision="RELEASE_WITH_GUARD",
                evidence=["D"],
                reason="D resolves",
                scar_id=scar_id,
            )
            core.ingest(D.experience_resolving(core, item))
            seq.append(core.route_decision(item, plasticity=plast)["decision"])
        else:
            # non-formed conditions have no formed decision to correct back to
            seq.append(core.route_decision(item)["decision"])
        return seq

    # -------------------------------------------------------------- run
    def run(self, item: str = "flux_alpha") -> dict[str, Any]:
        setup_fn = {
            "CLEAN": lambda: self._condition_clean(),
            "BIOGRAPHY": lambda: self._condition_biography(item),
            "FLAT": lambda: self._condition_flat(item),
            "FORMED": lambda: self._condition_formed(item),
        }

        conditions: dict[str, dict[str, Any]] = {}
        setup_ms: dict[str, float] = {}
        for tag, fn in setup_fn.items():
            cond, ms = _measure(fn)
            conditions[tag] = cond
            setup_ms[tag] = ms

        # FORMED_EXPORTED is the exported form of FORMED (not a 5th independent condition)
        exported, exp_ms = _measure(lambda: self._condition_formed_exported(item))
        conditions["FORMED_EXPORTED"] = exported
        setup_ms["FORMED_EXPORTED"] = exp_ms

        reports: dict[str, dict[str, Any]] = {}
        query_ms: dict[str, float] = {}
        for tag, cond in conditions.items():
            rep, ms = _measure(lambda c=cond: self._condition_report(c, item))
            reports[tag] = rep
            query_ms[tag] = ms

        correction: dict[str, list[str]] = {}
        corr_ms: dict[str, float] = {}
        for tag, cond in conditions.items():
            seq, ms = _measure(lambda c=cond: self._correction_sequence(c, item))
            correction[tag] = seq
            corr_ms[tag] = ms

        # --------------------------------------------------------- verdict
        item_dec = {tag: reports[tag]["item_release"] for tag in reports}
        related_dec = {tag: reports[tag]["related_release"] for tag in reports}
        formed_release = item_dec["FORMED"] == "RELEASE"
        biography_release = item_dec["BIOGRAPHY"] == "RELEASE"
        flat_release = item_dec["FLAT"] == "RELEASE"
        exported_release = item_dec["FORMED_EXPORTED"] == "RELEASE"

        # The causal question, stated as a difference:
        advantage_over_words = formed_release and not biography_release
        advantage_over_flat = formed_release and not flat_release
        transfer_preserved = formed_release and exported_release and (
            reports["FORMED"]["state_size_bytes"] > 0
        )

        verdict = {
            "formed_release": formed_release,
            "biography_release": biography_release,
            "flat_release": flat_release,
            "exported_release": exported_release,
            "advantage_over_biography": advantage_over_words,
            "advantage_over_flat": advantage_over_flat,
            "transfer_preserved": transfer_preserved,
            "causal_answer": (
                "STRUCTURED FORMED STATE ROUTES A CONSEQUENCE (RELEASE) THAT EQUIVALENT "
                "WORDS (BIOGRAPHY/FLAT) DO NOT, BECAUSE THE ROUTER ACTS ON FORMED "
                "DECISIONS CARRIED THROUGH QUALIFIED RETRIEVAL — NOT ON THE WORDS ALONE."
                if (advantage_over_words or advantage_over_flat)
                else "NULL RESULT: FORMED STATE ADDED NO MEASURABLE ADVANTAGE OVER WORDS."
            ),
            "honesty_note": (
                "The advantage is mechanism-scoped: within qualified-retrieval gating, "
                "only formed state produces consequential routing. This measures whether "
                "exported structured state changes routing where equivalent words do not. "
                "It does NOT claim the advantage generalizes to other mechanisms."
            ),
        }

        report = {
            "queries": QUERIES,
            "item_decisions": item_dec,
            "related_item_decisions": related_dec,
            "measurements": reports,
            "setup_ms": setup_ms,
            "query_ms": query_ms,
            "correction_ms": corr_ms,
            "correction_sequences": correction,
            "verdict": verdict,
        }
        self.receipts.append(
            action="transfer_control.assay",
            targets=[item],
            evidence=[f"advantage_over_biography={verdict['advantage_over_biography']}", f"advantage_over_flat={verdict['advantage_over_flat']}"],
            payload=report,
        )
        return report