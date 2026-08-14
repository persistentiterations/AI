"""TransferAssay (Gap C) — formed-state vs biography/flat/fresh comparison.

Question: does CONSEQUENTIAL ORGANIZATION of state beat merely supplying the
same words?

Conditions on identical question set:
  FRESH       - no history at all
  BIOGRAPHY   - same facts supplied as plain text (raw summary only, NO structured
                decisions/tags recovered — NO parsing)
  FLAT        - a single stored conclusion string, retrieved by exactness
  STRUCTURED  - full formed state via FormationCore (compressed memory +
                attractor + tags + linked decisions through qualified retrieval)

The biography condition must NOT secretly reconstruct structured state: it only
writes raw prose; the router sees no formed RELEASE decision. Any advantage of
STRUCTURED over BIOGRAPHY/FLAT is therefore attributable to the formed state,
not to the underlying words.
"""

from __future__ import annotations

from typing import Any

from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.provenance import ProvenanceLedger
from baby_ai.core.receipts import ReceiptLedger
from baby_ai import domain as D

QUERIES = ["flux_alpha", "flux_beta", "dura_gamma"]


class TransferAssay:
    def __init__(self) -> None:
        self.receipts = ReceiptLedger()
        self.provenance = ProvenanceLedger(self.receipts)

    def _fresh(self) -> dict[str, Any]:
        core = FormationCore(activation_id="transfer-FRESH")
        return {q: core.route_decision(q) for q in QUERIES}

    def _biography(self, item: str) -> dict[str, Any]:
        core = FormationCore(activation_id="transfer-BIO")
        # plain prose ONLY. No claims/decisions/tags -> no formed routing decision.
        core.ingest(core.make_event(raw_summary=D.biography_text(item)))
        return {q: core.route_decision(q) for q in QUERIES}

    def _flat(self, item: str) -> dict[str, Any]:
        core = FormationCore(activation_id="transfer-FLAT")
        # single stored conclusion, exact-string matched by prose retrieval only.
        core.ingest(core.make_event(raw_summary=D.flat_conclusion(item), tags=["conclusion"]))
        return {q: core.route_decision(q) for q in QUERIES}

    def _structured(self, item: str) -> dict[str, Any]:
        core = FormationCore(activation_id="transfer-STRUCTURED")
        core.ingest(D.experience_safe(core, item))
        return {q: core.route_decision(q) for q in QUERIES}

    @staticmethod
    def decision_map(results: dict[str, dict]) -> dict[str, str]:
        return {q: r["decision"] for q, r in results.items()}

    def run(self, item: str = "flux_alpha") -> dict[str, Any]:
        conditions = {
            "FRESH": self._fresh(),
            "BIOGRAPHY": self._biography(item),
            "FLAT": self._flat(item),
            "STRUCTURED": self._structured(item),
        }
        decoded = {name: self.decision_map(cond) for name, cond in conditions.items()}
        # advantage = conditions where a formed RELEASE actually routes beyond FRESH
        formed_releases = {
            q: decoded["STRUCTURED"][q] for q in QUERIES if decoded["STRUCTURED"][q] == "RELEASE"
        }
        biography_releases = {
            q: decoded["BIOGRAPHY"][q] for q in QUERIES if decoded["BIOGRAPHY"][q] == "RELEASE"
        }
        structured_advantage = set(formed_releases) - set(biography_releases) - set(formed_releases.keys() & biography_releases.keys())
        advantage_items = sorted(set(formed_releases) - set(biography_releases))

        report = {
            "conditions": decoded,
            "formed_release_items": sorted(formed_releases),
            "biography_release_items": sorted(biography_releases),
            "structured_advantage_over_biography_items": advantage_items,
            "structured_advantage": bool(advantage_items),
            "null_result": len(formed_releases) == 0,
            "note": (
                "STRUCTURED carries an explicit formed RELEASE decision + tags through "
                "qualified retrieval. BIOGRAPHY/FLAT supply the same words/verdict but "
                "no formed decision, so routing does not consequentially change. "
                "A clean null (no advantage) is an acceptable result."
            ),
        }
        self.receipts.append(
            action="transfer.assay",
            targets=[item],
            evidence=[f"advantage={report['structured_advantage']}"],
            payload=report,
        )
        return report