# R9 Failure Classification — one cluster from 24 residuals

Derived from `R9_COUNTEREXAMPLE_CENSUS.md` + `R9_COUNTEREXAMPLE_CENSUS_MACHINE.json`.
No repair performed; this file is classification of frozen evidence only.

## 1. Clustering result

**A single causal failure class** covers all 24 residuals. Every residual row
(seed 0..23, label `a_at_t6`) is structurally identical: same op stream, same
divergence point, same oracle cause missing (`expired_outside_window`), same empty
FC dependency/contradiction/scar state. The reduction is 24 counterexamples → **1
failure class**, so the smallest justified causal repair target is one relation.

Rationale for one class (evidence, not guess):

- `divergence.earliest_state_divergence` is identical in all 24 records: op index 1,
  the `VALID(e, from=2, to=4)` op, at which the oracle stores a window in
  `o.valid` and FC merely marks the op `unmodeled`.
- The failing query is the same label (`a_at_t6`) in every seed; `a_at_t2`, `a_at_t3`,
  `unrelated` are correct in all 24 seeds.
- Every record's `missing_causes == ["expired_outside_window"]`; no other cause
  string appears.
- No record has dependencies, scars, contradictions, or ledger entries that differ
  from seeds 0..23's shared structure; the entities differ only by seeded surface name.

## 2. Questions asked of the evidence (Part 7 checklist)

| question | answer from evidence |
|---|---|
| is the valid-inference conditional? (a PROCEEDs only inside [2,4]) | yes — but FC has no primitive to evaluate the condition |
| does ordering matter? (VALID declared after FORM, before the t=6 query) | the declaration index matters only in that FC never stores it |
| does a dependency become invalid after a state transition? | N/A — R9 has no dependencies |
| is applicability inherited incorrectly? | N/A — family transfer is working (unrelated correct) |
| context path-local vs globally valid? | N/A — single global ctx, correct on all seeds |
| is a formation reused after its condition disappeared? | **yes — this is the observed signature**: `a` is formed and stays RELEASE, but its VALID window [2,4] has expired at t=6; FC keeps PROCEEDing |
| is contradiction tested at the wrong level? | N/A — no contradiction involved |
| does a prior dependency still exert influence after a later event? | N/A — no dependencies involved |
| does the oracle distinguish "not currently admissible" from "never formed"? | related — oracle separates `evidence_missing` (never formed) from `expired_outside_window` (formed but currently out of window); FC cannot represent the latter |
| is a missing relief/rebinding/history relation the cause? | N/A — no DEPEND/RELIEVE in R9 |
| reachable vs currently grounded? | related — FC's grounding check (`route_decision`) answers from stored formed records only; the oracle additionally gates by *currently* in window |
| another cycle-like structure? | no — R9 is acyclic |

## 3. Single smallest relation demanded by the oracle

The oracle compares against a richer validity notion that the R9 task posits as the
environmental contract: **current-in-window temporal validity** — an entity that is
formed is nevertheless HOLD while its applicable VALID window does not contain the
query time. In oracle terms this is `OracleState.valid` + `_in_window` (per
(e,ctx), falling back to global, checked at query time t, defaulting to the count of
applied ops).

FC currently has *no time dimension in routing*: `route(e, g, ctx, t)` accepts `t`
but ignores it, and `apply(VALID)` appends `unmodeled`. The relation that must be
represented for the oracle's `expired_outside_window` to be reproducible is:

> **per-entity atemporal-evaluator boundary**: a remembered formation can carry a
> declared validity window; FC route must HOLD (cause `expired_outside_window`) when
> no applicable window contains the query time, while preserving all `evidence_missing`
> / transfer / dependency behavior when no window is declared.

This is exactly**one minimal causal relation** (time-window gate on formed state). No
second class or additional relation is justified by the 24 residuals.

## 4. Scope statement

The classification intentionally does NOT claim: that a time dimension in the full
general sense is needed; that windows should interact with scars/history/dependencies;
or that any of `a_at_t2`/`a_at_t3` need changing. All 72 non-residual R9 rows already
agree. See `R9_MINIMUM_RELATION_HYPOTHESIS.md` (written before any implementation).