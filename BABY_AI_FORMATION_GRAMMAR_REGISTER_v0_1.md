# BABY_AI_FORMATION_GRAMMAR_REGISTER v0_1

Formal register of the route-decision grammar covered by the FormationCore
ladder (R0–R10) as frozen, plus the delta introduced by the
`MARK_RESOLVE_DEPWALK` tranche. Versioned: this register supersedes the
informal listing in earlier handoffs (v0.0 implicit).

## Decision alphabet

Single decision type with a required cause from the closed set below.

| token                    | emitted as                                        | introduced at |
|--------------------------|---------------------------------------------------|---------------|
| PROCEED                  | decision, empty causes                            | R0 base       |
| prerequisite_missing:<x> | recursive walk HOLD, first unmet prereq          | R1 DEPEND     |
| active_contradiction     | surface HOLD, entity currently contradicted       | R2 MARK       |
| declared_prohibition     | surface HOLD, SUPERSEDE decision=HOLD active      | R3            |
| expired_outside_window   | surface+walk HOLD, VALID window elapsed           | R9            |
| evidence_missing         | walk HOLD, dependency lookup absent               | R4            |

The recursive walk never invents a generic HOLD; every HOLD resolves to a
member of the closed cause set.

## Operation grammar (ladder OP stream)

- `FORM e g` — declare entity for group/context.
- `DEPEND a b` — edge a<-b; walk b before a.
- `MARK e g ctx` — call entity into question in exactly that context.
- `RESOLVE e g ctx` — close the contradiction contest in exactly that context.
- `SUPERSEDE e g HOLD|PASS` — authoritative decision on a contested entity.
- (R9) `VALID e g window:w1..w2` — temporal admissibility.

## State-keeping rule (v0_1 addition)

History vs current authority:

- Retained scar records are append-only and never erased (audit/provenance).
- Current authority is the plasticity projection (plast status), the single
  source for BOTH surface routing AND the recursive walk.
- `contradiction_authority_gate=True` (default) binds the walk to current
  authority; `=False` re-anchors it to the pre-repair historical reading
  (ablation/residual audit only, never shipped).

## Context-key authority rule (CROSS_CONTEXT_RESOLVE tranche addition)

Qualification and RESOLVE are strictly per-(entity, context):

- A MARK issued in context X raises current authority ONLY in X; a RESOLVE
  issued in context Y pays back ONLY authority raised in Y.
- Qualifying (RESOLVE) or disqualifying (MARK) in one context does not
  rewrite authority in another context.
- Historical event provenance stays intact: raw scar records are never
  deleted; the registry `_scar_for[(e, ctx)]` and plast projections are the
  current-authority projection, keyed by context.
- This mirrors the oracle's exact keying `contradicted[(e,g,ctx)]`; a GLOBAL
  ("*") key blocks only GLOBAL queries and never leaks into a scoped context.
- `context_resolve_gate=True` (default) keyed per (entity, context);
  `=False` restores the pre-repair entity-wide clear (ablation only).

## Claim boundaries

- This register documents the ladder grammar and the closed cause set; it
  does not claim scale invariance, generality beyond the Frozen fixture
  ladder, or any theoretical operator semantics (Natural Math v5 untouched).
- Registry of what changed this tranche: RESOLVE's current-authority clear is
  scoped to the (entity, context) it names, gated by `context_resolve_gate` in
  `HistoricalFractalish`; no cause tokens added, none removed. A read-path
  divergence (GLOBAL mark vs scoped query) was logged during this tranche but
  is NOT part of its claim; it needs its own tranche.