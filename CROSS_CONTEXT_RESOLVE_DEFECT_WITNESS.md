# Cross-context RESOLVE defect witness (BEFORE repair)

Defect: `RESOLVE` clears the current contradiction authority entity-wide. A
contradiction raised in one context is paid back by a RESOLVE issued in a
DIFFERENT context, so the wrong context's authority is rewritten. The oracle
keys contradiction strictly by `(entity, group, context)` and a RESOLVE only
touches its own context.

## Minimal repro (group f; MARK in A, RESOLVE in B)

ops:

```
FORM    a  f
MARK    a  f   ctx=A
RESOLVE a  f   ctx=B
```

query `a` in context A:

| source    | decision | causes                |
|-----------|----------|-----------------------|
| oracle    | HOLD     | [active_contradiction]|
| E surface | PROCEED  | []                    |
| E walk    | PROCEED  | []                    |

Query `a` in context B and `*`:

| source    | decision | causes |
|-----------|----------|--------|
| oracle    | PROCEED  | []     |
| E surface | PROCEED  | []     |

## Root cause (pre-repair)

In `HistoricalFractalish.apply`, RESOLVE popped `_scar_for[e]` — a registry
keyed by ENTITY ONLY. The scar recorded for `a` (from the MARK in context A)
was therefore paid back by a RESOLVE issued in context B, marking scar-0000
`superseded`. The oracle's `contradicted[(a,f,A)]` key was never touched.

## Boundary

- Reproduced at `797598a` (pre-R9), `8735911` (post MARK/RESOLVE-DEPWALK
  repair), and `d64c45b` (tranche start): oracle HOLD vs E PROCEED.
- `contradiction_authority_gate` ON/OFF both reproduce it (prior gate is
  neutral for this defect).
- Earliest internal divergence: the RESOLVE op itself (wrong context's scar
  marked superseded). Earliest observable divergence: first query of `a` in
  context A after RESOLVE B.

## Fix applied (tranche `CROSS_CONTEXT_RESOLVE`)

The scar registry is keyed by `(e, ctx)` when the new `context_resolve_gate`
(default True) is ON, mirroring the oracle's exact `(e,g,ctx)` keying.
RESOLVE pops `_scar_for[(e, ctx_of_resolve)]` — so it pays back only a MARK
issued in the SAME context. Raw MARK scars stay in `core.scars` (history);
only current authority is rewritten, per-context. With the gate OFF the
registry is keyed by `e` alone, restoring the historical entity-wide clear
(the pre-repair defect) for the ablation.

## Post-repair (re-run, gate ON)

| source    | decision | causes                |
|-----------|----------|-----------------------|
| oracle    | HOLD     | [active_contradiction]|
| E surface | HOLD     | [active_contradiction]|
| E walk    | HOLD     | [active_contradiction]|

With `context_resolve_gate=False` the historical defect is pinned
(E PROCEED; scar-0000 `superseded`).

## Required adversarial cases (all oracle-exact after repair)

1. MARK A; RESOLVE A -> A PROCEED.
2. MARK A; RESOLVE B -> A HOLD(active_contradiction); B PROCEED.
3. MARK A; MARK B; RESOLVE A -> A PROCEED; B HOLD.
4. MARK A; MARK B; RESOLVE A; query both -> same as (3).
5. transitive dependencies evaluated in each context (e.g. c depends on a;
   a resolved in A but contradicted in B -> c PROCEED in A, HOLD
   prerequisite_missing:a in B).
6. validity-window interaction per context (VALID window expired in A ->
   HOLD expired_outside_window in A only).
7. cycles spanning otherwise valid context-scoped prerequisites (cycle stays
   cycle-safe; HOLD prerequisite_missing on the revisiting member).
8. context A resolved while context B remains contradicted (A PROCEED, B
   HOLD active_contradiction).

## Not repaired here (preserved orthogonal witnesses)

1. repeated-MARK + one RESOLVE (unchanged from prior log): oracle collapses
   repeated MARKs to a single bool; E keeps two always-active scars so one
   RESOLVE cannot clear both. Surface AND walk agree (adapter-vs-oracle
   collision). Gate-neutral, predates tranche.
2. SUPERSEDE+RESOLVE surface divergence (unchanged from prior log): after
   SUPERSEDE-HOLD then RESOLVE, E's surface PROCEEDs while the oracle keeps
   `declared_prohibition`; the walk already matches the oracle.
3. NEW read-path divergence surfaced during this tranche's battery
   (LOGGED, NOT repaired): a MARK issued in GLOBAL context is read by E as
   active in ANY context (`_own_contradicted`/`_blocking_scars_for` accept
   scars whose context is `*` for a scoped query), while the oracle reads
   `contradicted[(e,g,ctx)]` EXACTLY (GLOBAL mark blocks only GLOBAL
   queries). E: query A HOLD after global MARK; oracle: query A PROCEED.
   Gate-neutral, predates tranche (verified at `797598a`). This is a READ
   path scope divergence, distinct from the WRITE path repaired here; needs
   its own tranche.