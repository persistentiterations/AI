# Cross-context RESOLVE pre-repair boundary receipt

Taken before the context-scoped RESOLVE repair (tranche
`CROSS_CONTEXT_RESOLVE`). The wrong behavior below was deliberately preserved
as `CROSS_CONTEXT_RESOLVE_DEFECT_WITNESS.md` and re-verified at the tranche
start. This tranche is independent; it does NOT modify the frozen
`MARK_RESOLVE_DEPWALK` repair, R9, R8, or any earlier freeze.

## Repo state at boundary

- repo root: `C:\Users\moop\FractalishBuild\baby-ai-assembly-v0.1`
- branch: `hostile-qualification-v0_1`
- HEAD at boundary: `d64c45b`
  (= `8735911` MARK/RESOLVE-DEPWALK repair + freeze-package commits; R9
  `797598a`; R8 `0e64df6`; all prior freezes present and read-only)
- worktree: only the new (uncommitted) tranche files and pre-existing scratch
  files are untracked; no prior freeze is modified.
- tests: 96/96 passing.

## Exact pre-repair witness behavior (boundary HEAD `d64c45b`)

Minimal failing sequence (group `f`; MARK in context `A`, RESOLVE in `B`):

```
FORM    a  f
MARK    a  f   ctx=A
RESOLVE a  f   ctx=B
```

query `a` in context `A`:

```
oracle:                     HOLD ["active_contradiction"]
E surface + walk (both):    PROCEED []
```

Internal state at the query:

```
oracle.contradicted[(a,f,A)]  -> True   (RESOLVE in B must NOT clear A)
oracle.contradicted[(a,f,B)]  -> False
E scar-0000 (MARK, ctx=A)     -> plast status "superseded"   (WRONG: cleared by RESOLVE B)
E raw scar                   -> retained (history intact)
```

## Pre-date + toggle evidence

- Witness reproduced identically on detached worktrees at `797598a` (pre-R9),
  `8735911` (MARK/RESOLVE-DEPWALK repair), and `d64c45b` (boundary): oracle
  HOLD vs E PROCEED in every case.
- `contradiction_authority_gate` ON and OFF BOTH reproduce the defect
  (E PROCEED); the prior tranche's gate is neutral for this defect. Verified
  at `8735911` and `d64c45b`.

## Earliest divergence points (established before repair)

- Earliest INTERNAL state divergence: at the RESOLVE op in context B. Oracle
  writes `contradicted[(a,f,B)] = False` and leaves `(a,f,A) = True`. E pops
  the entity-keyed `_scar_for[a]` (the A-scar) and marks it `superseded`,
  i.e. E rewrites the CURRENT authority for the WRONG context.
- Earliest OBSERVABLE divergence: the very next route query of `a` in context
  A — oracle `HOLD ["active_contradiction"]`, E `PROCEED []`. No earlier op
  (FORM, MARK) diverges in any context.

## Oracle exact context-key semantics (established)

- `apply_op` uses `ctx = op.get("ctx", GLOBAL)` (GLOBAL == "*").
- `MARK e g ctx` sets `contradicted[(e,g,ctx)] = True` for exactly that key.
- `RESOLVE e g ctx` sets `contradicted[(e,g,ctx)] = False` for exactly that
  key; it never touches other contexts.
- `route_oracle` reads `contradicted[(e,g,ctx)]` with the query ctx EXACTLY;
  the only fallback is `(e,g,GLOBAL)` when the query context is GLOBAL.
- Consequence: qualification/RESOLVE is strictly per-(entity, context). A
  contradiction raised in A is independently active in A until RESOLVE in A.

## Required adversarial cases (all to hold after repair)

1. MARK A; RESOLVE A -> A PROCEED.
2. MARK A; RESOLVE B -> A HOLD(active_contradiction); B PROCEED.
3. MARK A; MARK B; RESOLVE A -> A PROCEED; B HOLD.
4. MARK A; MARK B; RESOLVE A; query both -> same as (3).
5. transitive dependencies evaluated in each context.
6. validity-window interaction per context.
7. cycles spanning otherwise valid context-scoped prerequisites.
8. context A resolved while context B remains contradicted.

## Boundary contract

- Witness must NOT be edited to make the repair look cleaner.
- Oracle cause strings are contractual (`active_contradiction`,
  `prerequisite_missing:<prereq>`, `declared_prohibition`,
  `expired_outside_window`, `evidence_missing`).
- Tranche target ONLY: RESOLVE's CURRENT-authority clear is scoped to the
  (entity, context) it pays back, mirroring `contradicted[(e,g,ctx)]`.
  Historical scars preserved; no scar deletion; no entity-wide rewrite.
- Repeated-MARK behavior and SUPERSEDE+RESOLVE are NOT repaired here (their
  witnesses preserved separately). Any new orthogonal witness surfaced is
  logged, not absorbed.