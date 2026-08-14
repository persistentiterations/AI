"""Independent conventional reimplementation baseline (section 10).

Deliberately ordinary. NO Operational Self, NO fractal formation. Just:

    event store (append-only)
    keyed retrieval by item + group-inheritance fallback
    explicit current conclusion
    contradiction flag (recent contradictory evidence suspends)
    simple supersession (newer resolving evidence replaces)
    JSON persistence

It is given access to EQUIVALENT information as the formed condition: the same
events (item, shared tag group, verdict, contradiction evidence, resolving
evidence). It is NOT crippled — it uses the shared-tag inheritance rule that is
exactly the mechanism withheld-item inheritance relies on in the formed core.

If this baseline reproduces every demonstrated advantage with less complexity,
the host runs MUST report that plainly.
"""

from __future__ import annotations

import json
import time
from typing import Any


class ConventionalMemory:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []          # append-only store
        self.by_item: dict[str, list[dict[str, Any]]] = {}  # keyed retrieval
        self.groups: dict[str, str] = {}                # item -> group tag
        self.conclusion: dict[str, str] = {}            # item -> verdict
        self.contradicted: dict[str, bool] = {}         # unresolved contradiction flag
        self.superset: dict[str, dict[str, Any]] = {}   # superseding record snapshot
        self.seq = 0

    # -------------------------------------------------------- recording
    def record(
        self,
        *,
        item: str,
        verdict: str,
        group: str | None = None,
        kind: str = "fact",
        evidence: str = "",
    ) -> int:
        """kind: fact | contradiction | resolve
        fact         -> stores verdict
        contradiction -> marks item contradicted (HOLD until resolve)
        resolve      -> supersedes: clears contradiction, stores new verdict
        """
        self.seq += 1
        rec = {
            "seq": self.seq,
            "kind": kind,
            "item": item,
            "group": group,
            "verdict": verdict,
            "evidence": evidence,
        }
        self.events.append(rec)
        self.by_item.setdefault(item, []).append(rec)
        if group:
            self.groups[item] = group

        if kind == "fact":
            self.conclusion[item] = verdict
            self.contradicted[item] = False
        elif kind == "contradiction":
            self.contradicted[item] = True
            # keep the pre-contradiction conclusion for restore-after-resolve
            self.superset.setdefault(item, {"pre": self.conclusion.get(item), "group": self.groups.get(item)})
            self.conclusion[item] = "HOLD"
        elif kind == "resolve":
            self.contradicted[item] = False
            self.conclusion[item] = verdict
        return self.seq

    # -------------------------------------------------------- retrieval
    def known_groups(self) -> list[str]:
        return sorted({g for g in self.groups.values() if g})

    def resolve_group_from_related(self, item: str) -> str | None:
        """Keyed retrieval: if item unknown but shares a known group, inherit."""
        g = self.groups.get(item)
        if g is None:
            for i, ig in self.groups.items():
                if ig == g or (item not in self.groups and self._same_family(i, item)):
                    pass
        return self._lookup_by_group(item)

    def _same_family(self, a: str, b: str) -> bool:
        # conventional proxy for the shared-tag inheritance: same prefix word
        return a.split("_")[0] == b.split("_")[0]

    def _lookup_by_group(self, item: str) -> str | None:
        g = self.groups.get(item)
        if g is None:
            for i, ig in self.groups.items():
                if self._same_family(i, item):
                    g = ig
                    break
        if g is None:
            return None
        # first item carrying that group that has a non-HOLD conclusion
        for i, ig in self.groups.items():
            if ig == g and self.conclusion.get(i) not in (None, "HOLD"):
                return self.conclusion[i]
        return None

    def route(self, query: str) -> dict[str, Any]:
        t0 = time.perf_counter()
        conf = self.conclusion.get(query)
        contradicted = self.contradicted.get(query, False)
        if contradicted:
            return {
                "decision": "HOLD",
                "reason": "contradiction_flag",
                "work": len(self.by_item.get(query, [])),
                "ms": round((time.perf_counter() - t0) * 1000, 3),
            }
        if conf and conf != "HOLD":
            return {
                "decision": conf,
                "reason": "explicit_conclusion",
                "work": len(self.by_item.get(query, [])),
                "ms": round((time.perf_counter() - t0) * 1000, 3),
            }
        inherited = self.resolve_group_from_related(query)
        if inherited:
            return {
                "decision": inherited,
                "reason": "group_inheritance",
                "work": len(self.by_item.get(query, [])) + len(self.group_events(query)),
                "ms": round((time.perf_counter() - t0) * 1000, 3),
            }
        return {
            "decision": "HOLD",
            "reason": "no_memory",
            "work": len(self.by_item.get(query, [])),
            "ms": round((time.perf_counter() - t0) * 1000, 3),
        }

    def group_events(self, item: str) -> list[dict[str, Any]]:
        g = self.groups.get(item)
        if g is None:
            g = next((ig for i, ig in self.groups.items() if self._same_family(i, item)), None)
        if g is None:
            return []
        return [e for e in self.events if e.get("group") == g]

    def estimates(self) -> dict[str, Any]:
        return {
            "events": len(self.events),
            "group_count": len(self.known_groups()),
            "conclusions": sum(1 for v in self.conclusion.values() if v and v != "HOLD"),
            "contradicted": sum(1 for v in self.contradicted.values() if v),
        }

    # ------------------------------------------------------- persistence
    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps({
            "seq": self.seq,
            "events": self.events,
            "by_item": self.by_item,
            "groups": self.groups,
            "conclusion": self.conclusion,
            "contradicted": self.contradicted,
            "superset": self.superset,
        }))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConventionalMemory":
        m = cls()
        m.seq = data.get("seq", 0)
        m.events = list(data.get("events", []))
        m.by_item = {k: list(v) for k, v in data.get("by_item", {}).items()}
        m.groups = dict(data.get("groups", {}))
        m.conclusion = dict(data.get("conclusion", {}))
        m.contradicted = dict(data.get("contradicted", {}))
        m.superset = dict(data.get("superset", {}))
        return m

    def export_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    # ------------------------------------------------------ transfer
    def ablate(self, item: str) -> bool:
        if item not in self.by_item:
            return False
        # remove the event records; route then falls to group inheritance or HOLD
        removed = [e for e in self.events if e["item"] == item]
        self.events = [e for e in self.events if e["item"] != item]
        del self.by_item[item]
        self.conclusion.pop(item, None)
        self.contradicted.pop(item, None)
        self.groups.pop(item, None)
        return bool(removed)

    def restore_from(self, snapshot: dict[str, Any]) -> None:
        clone = ConventionalMemory.from_dict(snapshot)
        item = next(iter(snapshot["by_item"]), None)
        if item:
            self.by_item[item] = clone.by_item.get(item, [])
            if item in snapshot["groups"]:
                self.groups[item] = snapshot["groups"][item]
            if item in snapshot["conclusion"]:
                self.conclusion[item] = snapshot["conclusion"][item]
            self.contradicted[item] = clone.contradicted.get(item, False)