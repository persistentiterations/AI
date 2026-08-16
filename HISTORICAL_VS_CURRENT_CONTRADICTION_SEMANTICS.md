# Historical vs current contradiction semantics (HISTORICAL_VS_CURRENT)

## Problem

`MARK`/`RESOLVE` (and `SUPERSEDE`) write both a retained scar record
("history", never erased) and a plasticity mutation ("current", always the
source for routing decisions). The ladder's `E` representation tied its
recursive walk's contradiction predicate to the historical scar instead of
the current plasticity projection, causing a surface/walk disagreement.

## Model

- Retained construct (raw scar): append-only record of the event. Frozen.
- Plast state: the current bool/binding that routing and the walk consult.
- RESOLVE: supersedes current authority only; history is not erased, it is
  re-framed as "superseded".

## Oracle reading (route_oracle)

- `apply_op` writes `o.contradicted[(e,g,ctx)]` on MARK, clears on RESOLVE.
- Oracles do not carry scars; they are pure current-state. Malformed or
  contradictory current-state (e.g., RESOLVE before MARK) is routed as
  `PROCEED []` — the oracle does not falsify evidence.
- The oracle's `plast`-relevant key is the contradiction bool only; declared
  prohibitions and evidence remain structural.

## Divergence family (all log-before-fix)

| case | oracle | E surface | E recursive walk | repair |
|------|--------|-----------|------------------|--------|
| MARK;RESOLVE -> dependent | PROCEED | PROCEED | HOLD (stale) | THIS TRANCH |
| SUPERSEDE-HOLD;RESOLVE -> entity | HOLD declared_prohibition | PROCEED | HOLD (walk matches oracle) | separate tranche |
| MARK;MARK;RESOLVE -> entity | PROCEED | PROCEED | HOLD (2nd MARK scar never resolved) | separate tranche |

## Repair principle

The current contradiction authority must be read through the same plasticity
status projection that the surface uses. Raw retained marks stay ordered
history. The repair is gated (`contradiction_authority_gate` default True) so
the pinned pre-repair residual remains auditable offline by setting the gate
False — no regression, no erase.

## Result

`MARK_RESOLVE_DEPWALK_DEFECT_WITNESS.md` documents the pre/post states.
Boundary receipt: `MARK_RESOLVE_PRE_REPAIR_BOUNDARY.md`.