# MARK/RESOLVE dependency-walk tranche — initial hypothesis (R9-adjacent)

Status: REPAIRED AND FROZEN (separate tranche commit). R9 remains frozen; the repair was
committed as its own commit on top of `797598a`, never patched inside the R9 commit.

## The observed defect (witness)

See `MARK_RESOLVE_DEPWALK_DEFECT_WITNESS.md` for the minimal four-op sequence
(FORM a; DEPEND c a; MARK a; RESOLVE a) and the full divergence table.

In short: after a prerequisite is MARKed (contradicted) then RESOLVEd, the surface route
for that entity (and the oracle) PROCEEDs, but the recursive dependency walk still HOLDs
the dependent with `prerequisite_missing:<prereq>` because `_own_contradicted` reads the
retained MARK scar as a currently-active contradiction.

## The core question of this tranche

> What is the minimum state distinction needed so that a resolved contradiction remains
> historically recorded without continuing to invalidate recursive dependency
> admissibility?

## Initial hypothesis: two different semantics, one scar

The apparent defect is that RESOLVE clears the CURRENT contradiction for surface routing
while recursive dependency evaluation still interprets the retained MARK scar as an
ACTIVE contradiction. The hypothesis is that these are two distinguishable states:

1. **Historical contradiction scar** — the fact that `a` was once called into question.
   This is evidence; it should be preserved for audit/provenance and NOT be treated as
   present-tense blocking.
2. **Currently active contradiction** — the present-tense fact that `a` is blocked.

RESOLVE transitions `a` from (2) to not-(2), leaving (1) intact.

## Explicitly NOT assumed

**Do not assume the scar itself should be deleted.** Deleting the scar (or marking its
record as cleared in place) conflates the two semantics: it would destroy historical
evidence to achieve a routing outcome. The tranche should look for the minimal state
distinction — e.g. a scar-level "resolved/cleared" flag, a separate active-block registry,
or a route-time re-derivation that consults the RESOLVE ledger — whichever is
smallest in state, keeps history, and keeps `route_decision` and the dependency walk on
the same book.

## Acceptance criteria for this tranche

- The four-op witness and its variants (dropping each op) behave identically to the
  oracle.
- Cause fidelity for the surface AND the walk: `HOLD` after MARK stays
  `prerequisite_missing:<prereq>` (walk) / `active_contradiction` (surface); after RESOLVE
  both PROCEED.
- Historical evidence retained: the MARK scar (and its provenance) survives RESOLVE in
  state, and can be enumerated after the fact.
- Scoped-context variants (MARK in ctx1, RESOLVE in ctx1, query ctx2) hold.
- R9 census stays zero; frozen R0–R10 residuals and R8 cycle/relieve freeze stay bit-identical.
- The R9 validity gate and this tranche's repair co-exist: a marked->resolved prereq with
  an unexpired VALID window PROCEEDs through the walk; with an expired window it HOLDs on
  `expired_outside_window`.

## Protocol / prohibition

- Reproduce the witness first on the current tree and on HEAD (pre-R9) as a control.
- Keep state bytes growth minimal; compare `state_bytes()` and the `counts()` deltas.
- Do not modify Natural Math v5; no theoretical operators; no scope-expansion battery of
  unrelated adversarial families in this tranche.

## Outcome (applied)

- Minimal repair: the recursive walk's contradiction predicate
  (`_own_contradicted`, consulted via `_own_contradicted`/`_prereq_ok` in the
  walk) is bound to the same current contradiction authority the surface
  routing uses (plast scar-status projection), gated by the new
  `contradiction_authority_gate` (default True; OFF re-anchors the recorded
  pre-repair residual for audit).
- Raw MARK scars retained as ordered history; only current authority reads
  through plast.
- Witness + full battery + census + 96 tests green; R9 and R8 freezes
  untouched. Two further pre-existing divergences surfaced during the
  acceptance battery → logged, NOT absorbed (see witness doc "Not repaired
  here").