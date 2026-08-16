# FormationCore R8 — Post-Hoc Formative Interpretation

> This interpretation was written after the R8 cycle/relieve machinery had already
> been implemented, tested, frozen, and committed. It did not guide the R8
> implementation and therefore cannot be treated as prospective evidence for the
> broader theoretical interpretation.

This document maps the frozen R8 repair (_BABY_AI_FORMATIONCORE_CYCLE_RELIEVE_REPAIR_v0_1_,
commit `0e64df6`) onto a fixed observation vocabulary. It writes nothing back into the
code: no API renames, no new modules (`recursive_admissibility.py`, `morphology.py`, ...),
no behavioral modification. The vocabulary is applied to observe the frozen machine;
it is not a coding specification. Where the vocabulary would overstate what the assay
shows, this document says so explicitly.

Evidence snapshots referenced (all frozen, read-only):
- `baby_ai/artifacts/repair/BABY_AI_FORMATIONCORE_CYCLE_RELIEVE_REPAIR_v0_1/` (9 files)
- `baby_ai/artifacts/repair/BABY_AI_FORMATIONCORE_DEPENDENCY_REPAIR_v0_1/`
- `baby_ai/artifacts/freeze/BABY_AI_COMPLEXITY_LADDER_v0_1/`

---

## 1. Morphology

**Observation-layer definition used here:** the realized FormationCore instance state
that a fixed evaluator would inspect — the set of formed/proposition records, the
current directed dependency topology, and (derivatively) the current routing /
admissibility outcome for each query point.

Within this assay the realized state is precisely:
- per-instance formed/proposition records (`FormationCore` state serialized by
  `to_dict`/`from_dict`, including `dependency_ledger`);
- the current dependency topology: `dependencies[a]` ordered prerequisite lists, as
  mutated by `record_dependency` and `relieve_dependency`;
- the momentary routing admissibility outcome (PROCEED / HOLD) produced by
  `_dep_ok` + the routed walk for a given query.

Note that morphology *as observed here is time-indexed by the operation stream*, not
by an externally supplied wall-clock. The `state_bytes_after_prefix` signature in the
frozen regression captures this realized state actually, not just the final answer.

## 2. Build specification

**Observation-layer definition used here:** the fixed FormationCore evaluation rules —
declaration/contradiction semantics, grounding semantics (own formed record OR
has-dependencies OR family transfer), dependency semantics (ordered prerequisites,
cycle-blocked revisit), and route/admissibility semantics — as they exist in the frozen
sources.

In the R8 freeze these rules are the ones traced in
`REPAIR_MECHANISM.json`:
- `DEPEND`: `record_dependency(a, b)` appends `b` to `a`'s ordered prerequisites and
  records the event in the ledger.
- `RELIEVE`: `relieve_dependency(a, b)` discards the *current directional edge* only and
  records the event; nothing else changes.
- Route walk: recursive, cycle-safe, mirroring `oracle._route_internal` (own
  declared/contradicted state first, then grounding, then every dependency
  recursively). A seen-set revisit is `CYCLE_BLOCKED` → unsatisfied.
- `dependency_gate` toggle: OFF restores the historical non-recursive traversal for
  ablation; ON is the repaired rule set.

This is the fixed part: the evaluation does not change per instance; only instance state
feeds it.

## 3. Residual build specification → CANDIDATE_RESIDUAL_BUILD_SPECIFICATION

**Observation-layer definition used here:** the minimum per-instance state that, given a
*fixed* Build specification, must be carried along so that the correct admissibility
result can be regenerated.

For the current R8 freeze this is named (deliberately) the
`CANDIDATE_RESIDUAL_BUILD_SPECIFICATION`: current local formed/proposition state plus
the current dependency ledger (every DEPEND and RELIEVE event), which jointly let the
fixed evaluator reconstruct the recursive admissibility outcome — including the
cycle-blocked HOLD and the relieved-edge state — without external interpreter state.

**The word "minimal" is NOT claimed here.** Establishingsumed minimality requires the
bounded measurement experiment (compare exhaustive admissibility snapshot vs. local
state + full ledger + fixed evaluator vs. a smaller defensible representation,
measuring serialization size, explicit fact count, reconstruction/replay fidelity,
behavior under RELIEVE and under redeclared DEPEND, cycle-HOLD reconstruction,
cause-string reproduction, and hidden interpreter/configuration burden). Until that
experiment runs, the ledger is a candidate residual build specification, not the proven
minimum. If no defensible compression emerges the honest outcome is recorded separately
as `NO_MEANINGFUL_RESIDUAL_COMPRESSION`.

## 4. Recursive admissibility

**Observation-layer definition used here:** admissible evaluator semantics where
`admissible(x) -> admissible(prerequisites(x))`, evaluated transitively, with a
seen-set so that a revisit is treated as `CYCLE_BLOCKED` and a cycle cannot bootstrap
grounding from itself.

This is exactly the relation frozen in R8:
- `_dep_ok(e, g, ctx, _seen)` recurses over prerequisites; revisiting a node already in
  the current seen-set yields unsatisfied → HOLD.
- Consequence, demonstrated by the adversarial battery (17/17) and the frozen R8 rows:
  a two-node cycle holds from either node with `prerequisite_missing:<direct prereq>`;
  no member may borrow admissibility from the cycle itself.

The syntax is native (`_dep_ok`, `CYCLE_BLOCKED`, `prerequisite_missing`); no new
vocabulary module was introduced — this bullet only observes that the native mechanism
is a recursive-admissibility evaluator.

## 5. Scale invariance of grammar

**Status: `NOT TESTED`.**

This observation-layer property (the claim that the grammar-evaluation relation is
invariant across scale — different node counts, different topology sizes, cross-domain
acceptance such as K562 / processor transients / Natural Math) is **explicitly NOT
established** by any frozen assay. R8's fixtures are single small programs with a
two-node cycle and a small residue of R9 temporal queries. Nothing here scales the
grammar or matches it across domains. Marking this `NOT TESTED` is required honesty, not
an omission; it must never be read as demonstrated.

---

## 6. Why R8 is scientifically interesting (no code changed for this section)

1. **Circular self-support failure, observed before the repair.** The v0.1 dependency
   gate was one-level: "a prerequisite is satisfied iff IT alone passes the formed-state
   gate." Inside a cycle every node read its partner as RELEASE-by-transfer, so mutual
   constraints could borrow admissibility from each other and both PROCEED (48/48 rows
   wrong, `PROCEED` vs oracle `HOLD`). This is a concrete, frozen example of a closed
   loop certifying itself through a one-level check.

2. **Recursive repair closes the bootstrap hole.** Making the gate transitive
   (`_dep_ok` over the full prerequisite closure, with revisit detection) turns the
   cycle into two `prerequisite_missing:<direct prereq>` HOLDs — exactly the oracle's
   result — with **zero** collateral route changes and **zero** new false holds.

3. **Directional RELIEVE semantics.** `RELIEVE(a,b)` removes only the current
   directional edge; it does NOT erase the proposition/formed state, does NOT alter
   scars/history/time, does NOT remove the inverse edge, does NOT resurrect a
   previously-relieved binding; a later `DEPEND` re-binds. The frozen
   `RELIEVE_SEMANTICS.json` captures that only the current edge changes. This is
   asymmetric-unbind semantics, distinct from state erasure.

4. **Causal ablation scoping.** The OFF/ON/RESTORE ablation identifies the recursive
   gate as the responsible change: OFF reproduces the dependency-repaired historical
   numbers byte-for-byte; ON adds the 48 R8 repairs; RESTORE == ON. The evidence this
   supplies is scoped explicitly as
   `CAUSAL_IMPLEMENTATION_EVIDENCE_WITHIN_THE_SOFTWARE_ASSAY` — it attributes the change
   to the gate within this assay, and is NOT claimed as a universal or general proof of
   any broader theory.

## 7. Boundary of this document

Nothing in this document rewrites, renames, or extends the frozen R8 code or any earlier
freeze (CONTEXT / APPLICABILITY / FREEZE / DEPENDENCY remain read-only). The five
vocabulary items above are observation descriptors only. Established claims:

- E (R8) recursively evaluates dependency admissibility; a cycle cannot self-certify
  under R8; RELIEVE changes future admissibility by removing a directional edge; the
  ledger permits a transitive admissibility recompute by a fixed evaluator; the R8
  causal ablation identifies the recursive gate as responsible; the 24 R9 residuals
  expose unrepresented cases (see the R9 census, which is the next artifact).