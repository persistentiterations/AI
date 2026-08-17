# BABY_AI_FUTURE_TEACHING_CONTRACT v0_1

Purpose: make the semantics taught to a future session transferable for both
repair (this `MARK_RESOLVE_DEPWALK` + `CROSS_CONTEXT_RESOLVE` tranches) and any
later tranche.

## Non-negotiables (never traded away)

1. Historical evidence is never erased. RESOLVE/SUPERSEDE re-frame current
   authority; scars keep provenance.
2. Surface routing and the recursive dependency walk MUST read the SAME
   current-authority book. No surface/walk disagreement, ever.
3. The closed cause set is contract. A HOLD must resolve to exactly one of:
   `prerequisite_missing:<x>`, `active_contradiction`, `declared_prohibition`,
   `expired_outside_window`, `evidence_missing`. No invented causes.
4. Every repair ships behind an OFF-able gate (default ON) so the pre-repair
   residual remains pinnable and auditable offline. OFF gates are ablation
   only; never shipped behavior.
5. Frozen packages (FREEZE/DEPENDENCY/CONTEXT/APPLICABILITY, R8, R9) are
   read-only; a repair is a SEPARATE tranche commit, never patched inside a
   freeze commit.
6. Reproduce the witness on both the current tree and an earlier HEAD control
   before touching state.

## Ledger of the repair semantics (what a future session must teach)

| concept            | canonical form |
|--------------------|----------------|
| contradiction contest | MARK opens, RESOLVE closes; repeated MARKs merge current authority (single bool) |
| declared prohibition  | SUPERSEDE decision=HOLD; survives RESOLVE unless proven contradiction-origin |
| temporal admissibility| VALID window; elapsed -> `expired_outside_window` in surface AND walk |
| prerequisite missing  | ordered walk, first unmet edge -> `prerequisite_missing:<prereq>`, cycle handled symmetrically |
| cause ground-truth    | `route_oracle` in `baby_ai/ladder/oracle.py` is the contract reference |
| context-scoped authority | MARK/RESOLVE are per-(entity, context): a RESOLVE pays back only the same-context MARK; qualification in one context never rewrites authority in another; GLOBAL ("*") keys block only GLOBAL queries (see CROSS_CONTEXT_RESOLVE tranche) |

## Repair boundary for the CROSS_CONTEXT_RESOLVE tranche

- Repair ONLY RESOLVE's current-authority write: keyed by (entity, context)
  behind `context_resolve_gate` (default True); OFF restores the historical
  entity-wide clear for ablation audit.
- Do NOT open the logged residual witness families here: SUPERSEDE+RESOLVE
  surface-vs-oracle; repeated-MARK+one-RESOLVE; and the NEWLY LOGGED
  read-path GLOBAL-mark-vs-scoped-query divergence. Each is a separate
  tranche with its own gate. (See witness doc's "Not repaired here".)

## Verification contract

Any future session claiming completion of these tranches must reproduce:

- 96/96 pytest.
- Full ladder R0–R10 × seeds 0–4 × reps A–E: E 55/55 all_correct,
  cause_fidelity 1.000.
- Exact witness FORMAT: `FORM a; DEPEND c a; MARK a; RESOLVE a` → oracle
  `c`=PROCEED and E walk `c`=PROCEED (gate ON); gate OFF keeps the recorded
  pinned residual `HOLD prerequisite_missing:a`.
- Exact witness CROSS-CONTEXT: `FORM a; MARK a A; RESOLVE a B` → query `a`
  in A: oracle HOLD `active_contradiction`, E surface AND walk HOLD
  `active_contradiction` (gate ON); gate OFF E PROCEED (entity-wide clear).