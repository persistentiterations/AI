# FormationCore CONTEXT REPAIR - v0.1

Repair ID: BABY_AI_FORMATIONCORE_CONTEXT_REPAIR_v0_1
Lineage: BABY_AI_FORMATIONCORE_APPLICABILITY_REPAIR_v0_1 -> this tranche
Baseline freeze: BABY_AI_COMPLEXITY_LADDER_v0_1 (read-only, untouched)

## Governing rule

> A memory grounds a decision only in the context it was grounded in.
> A contradiction blocks only in the context where it was raised (or globally).
> Context is part of identity, not a decoration on the surface string.

## The defect (traced)

The router had no context dimension. A query carrying a declared context (`ctx`)
was routed against the entire formed store as if every record were grounded in
every context:

* **R7 (context-scoped contradiction):** `MARK(a, ctx_scoped)` created a scar with
  no context binding. Querying `a` in `ctx_base` / another context still hit the
  scar and came back HOLD, even though the contradiction never applied there
  (48 false holds: `a_other_ctx`, `b_other_ctx`).
* **R10 (context-scoped supersede over global state):** a globally-formed state was
  followed by `SUPERSEDE(a, HOLD, ctx_new)`. The supersede scar had no context
  binding either, so it revoked the global RELEASE in *every* context, including
  `ctx_new` where it belonged, and `ctx_base`/`ctx_other` where it must not apply
  (72 false proceeds: the base/other contexts incorrectly fell over).
* **Cause ambiguity:** every scar-blocking HOLD collapsed to the opaque token
  `contradiction_scar_blocking`, conflating "old state was actively contradicted"
  with "old state was declared obsolete" and with "nothing relevant was grounded
  here at all."

This is an APPLICABILITY-COUPLED error in the router layer: it treated stable
identity as memory_id + family tag, and dropped the third component of the key
that the ORACLE uses - the context. Retrieval is unchanged.

## The repair (structural, keyed)

`route_decision` now accepts an optional `context`. Everything downstream becomes
context-aware while the upstream retrieval stays read-only:

1. **Grounding is recorded at ingest.** Each event carries its declared context
   and op-kind in provenance; the adapter records `mem_contexts` (which context it
   was formed/marked/resolved in) and `scar_contexts` + `scar_kinds` (where each
   scar was raised, and by which op).
2. **Context identity admission.** A memory is admissible for a context-qualified
   query only if it was grounded in that context **or** the global context (`*`).
   Records grounded elsewhere are retrieved-but-not-consequential (same separation
   as the applicability gate: retrieval may expose a possibility; context makes it
   admissible).
3. **Scar placement matters.** A scar blocks only in its own context or globally.
   The R7 scar lives in `ctx_scoped`; it no longer leaks into `ctx_base`. The R10
   supersede scar lives in `ctx_new`; the global FORM stays authoritative in
   `ctx_base` / `ctx_other`, while `ctx_new` continues to HOLD.
4. **Precise causes.** A blocked route names the scar's origin: `MARK` ->
   `active_contradiction`; `SUPERSEDE` HOLD -> `declared_prohibition`. When
   nothing in the query's context actually grounds a RELEASE decision, the cause
   set additionally carries `evidence_missing` (faithful: HOLD because of a
   context-specific contradiction is not HOLD because no memory was found; in R7
   `a_scoped_ctx`, `a` is not grounded in the scoped context, so both hold).

The E ladder threads each op's `ctx`/op-kind into its events and passes the query's
`ctx` through; the gate toggles (`context_gate` class flag) for the ablation.

## Non-negotiable constraints honored

- NO lexical patch: no context-name special cases, no threshold tuning, no
  substring exclusions. Gate keys on context identity (`record ctx == query ctx`)
  and the explicit global marker only.
- Boring/keyed representation preferred: three-token key (tag, context, sequence)
  is exactly what the oracle contract states; no graph machinery introduced.
- Cause fidelity: context HOLDs cite `active_contradiction`,
  `declared_prohibition`, `evidence_missing` - never the opaque
  `contradiction_scar_blocking`.
- Causal ablation: OFF reproduces the historical context failure class exactly;
  ON removes it; RESTORE reproduces ON (deterministic).
- Frozen-ladder regression: A/B/C/D bit-identical to the v0_1 freeze; unit suite
  96/96.

## Results (frozen, 24 seeds [0..23] inclusive)

| metric | pre-tranche E (context OFF) | repaired E (context ON) | delta |
|--------|--------------------------|------------------------|-------|
| route_correct | 1128/1272 | 1200/1272 | +72 |
| cause_fidelity | 900/1272 | 1068/1272 | +168 |
| route regressions | - | 0 | 0 |
| cause regressions | - | 0 | 0 |
| false_hold | 48 | 0 | -48 |
| false_proceed | 96 | 72 (R8/R9, out of scope) | -24 |

Context demand class (168 queries): route **168/168**; cause fidelity **144/168**
(the 24 residual cause-only rows are R7 `b_scoped_ctx`, which cite
`active_contradiction, evidence_missing` but the oracle demands
`prerequisite_missing` - that is a DEPEND-primitive gap, deferred to the
dependency tranche; the route remains correct).

Precise-cause gains beyond the context class (positive side effects of scar-origin
honesty): R1 `after_mark` HOLD now cites `active_contradiction` (24/24 exact), and
R3 `parent_after_supersede` + R4 `chain0_post` now cite `declared_prohibition`
(48/48 exact).

Ablation (per ABLATION.json): gate OFF totals exactly reproduce the historical
return; gate ON removes exactly the context-class failures; gate RESTORE than ON.

## Claim boundary

The context failure class is traced to the router (a missing component of the key)
and closed by the declared-context scoping gate recorded at ingest, with precise
scar-origin causation. Causal ablation and frozen-ladder regression are frozen
under this package. No other failure class is claimed fixed this tranche: R8 cyclic
constraints (dependency/cycle primitive), R9 temporal validity (time primitive),
and DEPEND-guarded `prerequisite_missing` causation all remain DEFERRED and stay
honest failures in the repaired E.

Evidence: `BASELINE_FAILURES.json`, `REPAIR_MECHANISM.json`, `ABLATION.json`,
`FULL_LADDER_REGRESSION.json`, `CAUSE_FIDELITY.json`, `manifest.json`.