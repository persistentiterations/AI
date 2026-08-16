# FORMATIONCORE_FABULOUS_FIVE_CROSSWALK_V0

Status: observation-layer documentation only. This file does NOT rename APIs, does NOT
add `recursive_admissibility.py` / `morphology.py` modules, and does NOT modify R8 code.
The five vocabulary items below are applied to observe the frozen implementation
(`HistoricalFractalish` / `FormationCore`), not as a coding spec.

Companion docs: `FORMATIONCORE_R8_FORMATIVE_INTERPRETATION.md`,
`R9_COUNTEREXAMPLE_CENSUS.md`, `R9_FAILURE_CLASSIFICATION.md`,
`R9_MINIMUM_RELATION_HYPOTHESIS.md`, `RESIDUAL_BUILD_SPEC_MEASUREMENT_V0.md`.

## Crosswalk (native mechanism -> vocabulary term)

| term | native mechanism it describes | where |
|---|---|---|
| Morphology | realized FormationCore state: formed/proposition records, current directed dependency topology, current routing/admissibility outcome | `FormationCore.to_dict` (memories, scars, dependencies, ledger); `route()` result |
| Build specification | fixed evaluation rules: declaration/contradiction/grounding semantics, dependency semantics (ordered prereqs, cycle-blocked revisit), route/admissibility semantics | `representations.py` `_dep_ok` / `_dep_grounded` / `route`; `oracle.py` `_route_internal` |
| Residual build specification → `CANDIDATE_RESIDUAL_BUILD_SPECIFICATION` | local formed state + full dependency ledger, replayed by the fixed evaluator | `RESIDUAL_BUILD_SPEC_MEASUREMENT_V0.md` (candidate B); minimality NOT claimed |
| Recursive admissibility | `_dep_ok(e, g, ctx, _seen)`: `admissible(x) -> admissible(prerequisites(x))`; seen-set revisit → `CYCLE_BLOCKED` → unsatisfied; cycle cannot bootstrap grounding | `representations.py` `_dep_ok` (R8); `admissible(x)->admissible(prerequisites(x))` |
| Scale invariance of grammar | NOT TESTED — explicit, no frozen assay demonstrates it | `FORMATIONCORE_R8_FORMATIVE_INTERPRETATION.md` §5 |

## Terms NOT upgraded to code

No `recursive_admissibility.py`, no `morphology.py`, no renaming of
`dependency_ledger`, `_dep_ok`, or `relieve_dependency`. Native names are domain-native
and stay. The claim checked is whether the vocabulary *describes* the code, not whether
the code should be rewritten to match the vocabulary.

## Claim boundaries (Part 18), applied to this crosswalk

ALLOWED (demonstrated in this repo):
- FC recursively evaluates dependency admissibility; a cycle cannot self-certify under
  R8 (48 cycle rows → HOLD, adversarial 17/17).
- RELIEVE changes future admissibility by removing a directional edge only (directional
  RELIEVE semantics, ledger reconstructible but not resurrected).
- The R8 causal ablation identifies the recursive gate as responsible
  (OFF reproduces 1200/1068, ON 1248/1248, RESTORE==ON).
- The 24 R9 residuals expose unrepresented cases (census: single class,
  `expired_outside_window` missing).

NOT allowed:
- "Baby AI understands causality" / human-like reasoning / universal proof.
- "The ledger is the minimal residual build spec" — not claimed; C fails correctness,
  B reconstructs, no smaller defensible rep; NO_MEANINGFUL_RESIDUAL_COMPRESSION outcome.
- "Same grammar as genetics/K562/processor transients/Natural Math" — nothing tested.
- "Scale invariance demonstrated" — explicitly NOT TESTED.
- Consciousness / sentience / personhood claims.

## History-equivalence note (Part 11)

No existing R9 fixture is a natural history-equivalence pair: all 24 seeds share the
identical op history `(FORM, VALID, FORM)` with an empty dependency topology, so there
is no "same current topology reached by different paths" inside R9. The only
topology-similar pair in the whole ladder is R3 vs R7 (both end with `deps = {b->a}` on
all 24 seeds), but they differ in contradiction state (R3: global SUPERSEDE-HOLD; R7:
ctx-scoped MARK), so they are NOT a clean current-state-equivalence pair either. Per
Part 11 the finding is recorded as `NO_EXISTING_HISTORY_EQUIVALENCE_PAIR` (natural, not
manufactured); any future history-vs-morphology assay requires separate
pre-registration.