# FormationCore DEPENDENCY REPAIR — v0.1

Repair ID: BABY_AI_FORMATIONCORE_DEPENDENCY_REPAIR_v0_1
Baselines: BABY_AI_COMPLEXITY_LADDER_v0_1 + BABY_AI_FORMATIONCORE_CONTEXT_REPAIR_v0_1 (both READ ONLY)

## Governing rule

> A dependent's proceeding is contingent on its prerequisite's state — evaluated
> where the query lands, not where the dependency was declared.

## The defect (traced)

24 R7 `b_scoped_ctx` residuals: DEPEND was recorded as **unmodeled** at the E layer
(gate OFF == historical traversal), so `b`'s proceeding never became contingent on `a`'s
state. The router still emitted HOLD — but by **token overlap** with `a`'s scoped
contradiction record, so the cause was borrowed: `active_contradiction, evidence_missing`
as though `b` itself were contradicted and ungrounded.
The oracle requires `prerequisite_missing:<a-surface>`.

Diagnostic seed 0: `DEPEND(a=<b>, b=<a>)`; query `b_scoped_ctx` retrieves only `a`'s
records (formed in `ctx_base`, contradicted in `ctx_scoped`); `b` has no own record.
First wrong transition: op index 1 (DEPEND ingestion).

## The repair (structural, keyed, direct)

- `FormationCore.dependencies`: dependent surface -> ordered prerequisite surfaces
  (`record_dependency`), persisted in `to_dict/from_dict`.
- `mem_tuples` attribution registry: surfaces that compression drops survive, so the
  representation can tell OWN-state (subject == query surface) from token-overlap
  records.
- `HistoricalFractalish.route`: for a dependent with a clean own-state (not
  superseded-HOLD, not contradicted in the query context), every prerequisite must
  satisfy the SAME formed-state gate the query itself goes through (retrieval,
  exact applicability tag, context grounding in the query's ctx or global, scar
  blocking, RELEASE). Any missing prereq -> `HOLD [prerequisite_missing:<full
  surface>]` (never truncated).
- **Direct primitive only:** no recursion into a prerequisite's own dependencies, no
  graph, no cycle walk, no RELIEVE semantics. Cycles (R8) and temporal validity (R9)
  remain explicitly deferred.

## Non-negotiable constraints honored

- Direct, boring, keyed representation (dependent->prerequisite surface list), no graph machinery.
- No RECURSION in satisfaction; no cycle claim; RELIEVE and temporal windows untouched.
- Cause fidelity: dependency-class HOLDs cite only `prerequisite_missing:<surface>`.
- Causal ablation (OFF == historical), frozen-ladder regression, adversarial specificity battery.

## Results (frozen, 24 seeds [0..23] inclusive)

| metric | E after context repair | E after dependency repair |
|--------|----------------------|--------------------------|
| route_correct | 1200/1272 | 1200/1272 |
| cause_fidelity | 1068/1272 | 1200/1272 |
| false_proceed | 72 | 72 (R8/R9 deferred) |
| false_hold | 0 | 0 |

Cause-fidelity gain = 132:
- R7 `b_scoped_ctx` x24 — the targeted residual.
- R3 `child_after_supersede` x24 and R4 `chainN_post` x84 — emergent dependency-class
  repairs, oracle-exact (only roots are FORMed; satisfiability of each immediate
  prereq fails and the cause names the true blocker).

Ablation: gate OFF reproduces the context-repaired historical numbers byte-for-byte
(route 1200, cause 1068); gate ON
adds exactly the 132 dependency-class repairs with ZERO
route changes and ZERO new false holds; RESTORE == gate ON.

Adversarial dependency battery: 15/15 correct across context splits,
global/local grounding, scoped supersede, resolve, missing prereq, cross-surface, and
cross-group ensembles.

A/B/C/D remain bit-identical to the original freeze (frozen-ladder regression).

## Claim boundary

The dependency-class cause defect is traced to DEPEND ingestion and fixed by the direct
keyed-prerequisite primitive, frozen under this package. All 132 cause repairs are
oracle-exact; no route changed; no new false hold. No claim about dependency cycles
(R8), RELIEVE semantics, or temporal validity (R9) — those remain honest deferred
failures in repaired E.
