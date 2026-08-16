# FormationCore CYCLE / RELIEVE REPAIR - v0.2

Repair ID: BABY_AI_FORMATIONCORE_CYCLE_RELIEVE_REPAIR_v0_1
Baselines: BABY_AI_COMPLEXITY_LADDER_v0_1 + CONTEXT_REPAIR_v0_1 + DEPENDENCY_REPAIR_v0_1 (READ ONLY)

## Governing rules

> 1. A dependency cycle blocks every member of it.
> 2. RELIEVE un-binds the *current directional edge* only; history is retained and never resurrected.

## The defect (traced)

R8 (`cyclic_mutually_constraining`): `DEPEND(a->b); DEPEND(b->a); FORM(a)`.
E's v0.1 dependency gate is **direct**: a prerequisite is satisfied iff IT alone
passes the formed-state gate. Inside the cycle every prerequisite reads the other
node as RELEASE-by-transfer, so `a_in_cycle` and `b_in_cycle` both PROCEED (48 rows
across the 24 frozen seeds). RELIEVE is unmodeled, so `b_after_relieve` is answered
from the still-bound `b->a` edge (its route happens to match, but the edge is not
actually un-bound).

Oracle ground truth (read-only, oracle.py `route_oracle` / `_route_internal`):
- the recursive precondition walk flags a revisit as CYCLE_BLOCKED and the surface
  HOLDs with `prerequisite_missing:<direct prereq>`;
- `apply_op` RELIEVE = `deps[X].discard(Y)` on the current binding only.

## The repair

- `HistoricalFractalish._dep_ok(e, g, ctx, _seen)`: recursive, cycle-safe walk
  mirroring `oracle._route_internal`. Order per node: own declared-HOLD, own
  contradicted, grounding (own formed record OR has-dependencies OR family
  transfer), then every dependency recursively. A revisit is CYCLE_BLOCKED ->
  unsatisfied. Fresh seen-set per direct prereq, exactly as the oracle re-seeds
  `_seen` per direct prereq.
- `FormationCore.relieve_dependency(x, y)` + `dependency_ledger`: RELIEVE:
  dependencies[x] discards y (current binding); the ledger keeps every DEPEND and
  RELIEVE event so the old edge is reconstructible but is NOT resurrected. A later
  DEPEND re-binds the edge. RELIEVE touches no formed/proposition state, no scars.
- Toggle `dependency_gate=False` restores the historical traversal (DEPEND/RELIEVE
  unmodeled, flat check) for the ablation.

## Results (frozen, 24 seeds [0..23] inclusive)

| metric | E after dependency repair | E after cycle/relieve repair |
|--------|--------------------------|------------------------------|
| route_correct | 1200/1272 | 1248/1272 |
| cause_fidelity | 1200/1272 | 1248/1272 |
| false_proceed | 72 | 24 (R9 residual only) |
| false_hold | 0 | 0 |

Gain = +48 route AND
+48 cause, all in R8: the two cycle
rows x 24 seeds now HOLD with `prerequisite_missing:<direct prereq>` exactly as the
oracle does; `b_after_relieve` still PROCEEDs via transfer with cause [] after the
edge is actually un-bound.

Ablation: gate OFF reproduces the dependency-repaired numbers byte-for-byte
(route 1200, cause 1068);
gate ON adds the 48 R8 repairs with ZERO route changes and ZERO
new false holds; RESTORE == gate ON.

Adversarial cycle/relieve battery: 17/17 queries correct vs route_oracle
(direct chains, two-node cycles from either node, self-loops formed/unformed, RELIEVE
breaking a cycle, RELIEVE keeping the inverse edge, redeclaration, cycles with external
grounding, empty RELIEVE no-ops, cross-context transfer).

A/B/C/D remain bit-identical to the original freeze.

## Claim boundary

The R8 cyclic-constraint and RELIEVE semantics are the scope of this package. No claim
about temporal validity (R9), which remains an honest deferred ask per the frozen
failure profile. Mathematically, mutual constraint + asymmetric relieve are exactly the
two relations the oracle defines for these ops; E now implements both.
