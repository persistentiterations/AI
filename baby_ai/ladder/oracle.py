"""Oracle: independent ground-truth semantics for ladder tasks.

The oracle is NOT any of the compared representations. It is a direct statement
of the environmental contract established by the hostile phase:

  * a structured record FORM(e, g, ctx) under a family token g makes e PROCEED
    under g within context ctx;
  * an unresolved MARK(e, g, ctx) contradicts it -> HOLD(active_contradiction)
    scoped to that context;
  * RESOLVE clears the contradiction (superseding the prior HOLD);
  * DEPEND(e -> b) makes e's proceeding require b's proceeding (prerequisite);
  * VALID(e, [from..to]) gates e's validity by time;
  * transfer: an unseen surface sharing the family token of a PROCEED member
    inherits that verdict (the group-token inheritance shown load-bearing).

Context is structured as a scoped name; time is a monotone integer advanced by
each applied operation (R9/R10 semantics run against these same clocks).

Every representation is measured against these same truths. No representation
is given privileged information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

GLOBAL = "*"


@dataclass
class OracleState:
    groups: dict[str, str] = field(default_factory=dict)                  # e -> family token
    formed: dict[tuple[str, str, str], bool] = field(default_factory=dict)  # (e,g,ctx)
    contradicted: dict[tuple[str, str, str], bool] = field(default_factory=dict)
    superseded: dict[tuple[str, str, str], str] = field(default_factory=dict)  # (e,g,ctx) -> decision
    valid: dict[tuple[str, str], list[tuple[int, int]]] = field(default_factory=dict)  # (e,ctx) -> windows
    deps: dict[str, set[str]] = field(default_factory=dict)               # e -> {prereqs b}
    time: int = 0


def splitmix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
    x = (x ^ (x >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
    return x ^ (x >> 31)


def rng(seed: int):
    state = seed
    while True:
        state = splitmix64(state)
        yield state


def family_of(token: str) -> str:
    return token.split("_")[0]


def apply_op(o: OracleState, op: dict[str, Any]) -> None:
    o.time += 1
    kind = op["op"]
    ctx = op.get("ctx", GLOBAL)
    if kind == "FORM":
        e, g = op["e"], op["g"]
        o.groups[e] = family_of(g)
        o.formed[(e, g, ctx)] = True
        o.contradicted[(e, g, ctx)] = False
    elif kind == "MARK":
        o.contradicted[(op["e"], op["g"], ctx)] = True
    elif kind == "RESOLVE":
        o.contradicted[(op["e"], op["g"], ctx)] = False
    elif kind == "SUPERSEDE":
        o.superseded[(op["e"], op["g"], ctx)] = op.get("decision", "HOLD")
        o.contradicted[(op["e"], op["g"], ctx)] = False
    elif kind == "DEPEND":
        o.deps.setdefault(op["a"], set()).add(op["b"])
    elif kind == "RELIEVE":
        o.deps.setdefault(op["a"], set()).discard(op["b"])
    elif kind == "VALID":
        o.valid.setdefault((op["e"], ctx), []).append((op["from"], op["to"]))


def _in_window(o: OracleState, e: str, ctx: str, t: int | None) -> bool:
    windows = o.valid.get((e, ctx)) or o.valid.get((e, GLOBAL)) or []
    if not windows:
        return True
    t_real = o.time if t is None else t
    return any(a <= t_real <= b for a, b in windows)


def _context_ok(o: OracleState, keyed: tuple[str, str, str], ctx: str) -> bool:
    """A record in GLOBAL context applies everywhere; a scoped record only there."""
    return keyed[2] == ctx or keyed[2] == GLOBAL


def _transfer_possible(o: OracleState, e: str, g: str, ctx: str) -> bool:
    """Unseen e shares family token with a PROCEED member in this context."""
    g_fam = family_of(g)
    for (ej, gj, cj), formed in o.formed.items():
        if not formed:
            continue
        if ej == e:
            continue
        if gj != g:
            continue
        if o.groups.get(ej) != g_fam:
            continue
        if not _context_ok(o, (ej, gj, cj), ctx):
            continue
        if o.contradicted.get((ej, gj, cj)):
            continue
        return True
    return False


def _grounded(o: OracleState, e: str, g: str, ctx: str) -> bool:
    """An entity is grounded if it has its own form record, OR it depends on
    other entities (its grounds are its prerequisites), OR it can inherit by
    family transfer. A member of a dependency cycle with no independent grounds
    is NOT grounded by the cycle itself."""
    if (e, g, ctx) in o.formed or (e, g, GLOBAL) in o.formed:
        return True
    if o.deps.get(e):
        return True
    return _transfer_possible(o, e, g, ctx)


def route_oracle(o: OracleState, e: str, g: str, *, ctx: str = GLOBAL, t: int | None = None) -> dict[str, Any]:
    """Return PROCEED/HOLD with the full cause set (block causes)."""
    causes: list[str] = []
    keyed = (e, g, ctx)

    # prerequisites: every dependency must itself proceed (in this context/time)
    for b in sorted(o.deps.get(e, set())):
        if _route_internal(o, b, g, ctx, t, _seen=set()) != "PROCEED":
            causes.append(f"prerequisite_missing:{b}")

    declared = o.superseded.get((e, g, ctx)) or o.superseded.get((e, g, GLOBAL))
    if declared == "HOLD":
        causes.append("declared_prohibition")
    if o.contradicted.get((e, g, ctx)):
        causes.append("active_contradiction")
    elif o.contradicted.get((e, g, GLOBAL)) and keyed[2] == GLOBAL:
        causes.append("active_contradiction")

    if not _grounded(o, e, g, ctx):
        causes.append("evidence_missing")
    if not _in_window(o, e, ctx, t):
        causes.append("expired_outside_window")

    if causes:
        return {"decision": "HOLD", "causes": sorted(set(causes))}
    return {"decision": "PROCEED", "causes": []}


def _route_internal(o: OracleState, e: str, g: str, ctx: str, t: int | None,
                    *, _seen: set[str] | None = None) -> str:
    """Recursive precondition walk used by route_oracle (cycle-safe)."""
    _seen = _seen or set()
    if e in _seen:
        return "CYCLE_BLOCKED"
    _seen = _seen | {e}
    keyed = (e, g, ctx)
    declared = o.superseded.get(keyed) or o.superseded.get((e, g, GLOBAL))
    if declared == "HOLD":
        return "HOLD"
    if o.contradicted.get(keyed) or (o.contradicted.get((e, g, GLOBAL)) and keyed[2] == GLOBAL):
        return "HOLD"
    if not _grounded(o, e, g, ctx):
        return "HOLD"
    for b in o.deps.get(e, set()):
        if _route_internal(o, b, g, ctx, t, _seen=_seen) != "PROCEED":
            return "HOLD"
    if not _in_window(o, e, ctx, t):
        return "HOLD"
    return "PROCEED"