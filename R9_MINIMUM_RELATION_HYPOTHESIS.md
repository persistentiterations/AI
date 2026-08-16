# R9 Minimum Relation Hypothesis (before implementation)

Written **before** any R9 implementation. Status: PROPOSED. If this proposal is later
implemented, this file plus the R9 ablation must demonstrate causal responsibility;
until then it is a hypothesis only. Constraint: Natural Math v5 must not be modified;
no theoretical operators may be imported.

## 1. Counterexamples explained by this hypothesis

The 24 frozen R9 residuals (`a_at_t6`, seeds 0..23) are all the same single case: an
entity `a` was FORMed (RELEASE) and carries a declared `VALID(e=a, g, from=2, to=4)`
window; the query asks `t=6`, which is outside `[2,4]`. The oracle HOLDs with
`expired_outside_window`; the current CortexCore/FormationCore route cannot distinguish
"formed" from "formed but currently outside its declared validity window", so it
PROCEEDs (false proceed, empty causes).

The other three R9 queries (`a_at_t2`, `a_at_t3`, `unrelated`) are already correct on
all 24 seeds and must continue to be.

## 2. Current incorrect inference

FC answers `a` at any query time as PROCEED with `causes == []` the moment a RELEASE
(formed) record exists and no supercede/contradiction/dependency applies. It implicitly
infers: *formed memory ⇒ currently admissible at every past, present, and future
query*. That inference is sound for every earlier rung (R0..R8 never pose a query
outside an applicable window) but is exactly what R9's `a_at_t6` destroys.

## 3. Missing relation

`current-in-window temporal validity`: a formation record may carry a declared
validity window `[from, to]`; at route time the evaluator must additionally gate on
whether any applicable window contains the query time `t` (per-entity, falling back to
the recorded window; when the entity has no window, behavior is unchanged, i.e. always
in-window).

The oracle implements this as `OracleState.valid` + `_in_window` in
`baby_ai/ladder/oracle.py`; the missing relation in FC route is the equivalent of
`expired_outside_window` as a block cause.

## 4. Proposed state / evaluator change (minimal, not yet implemented)

- State: record the declared `VALID` window on the memory record for `a`
  (e.g. `valid_windows: dict[(subject, group, ctx), list[(from, to)]]` on the core /
  a per-instance ledger entry), populated when `apply(VALID)` runs. The op is no longer
  dropped to `unmodeled`.
- Evaluator: in `rep.route(...)` (and, only if required for transitive prereqs, in
  the dependency walk), when a window is recorded for the queried entity and the query
  supplies a time, gate PROCEED on `any(from <= t <= to)`; violation produces cause
  `expired_outside_window` exactly (oracle cause string, not truncated). When the query
  time is absent or the entity has no window, the gate is inert → all earlier rungs and
  the deterministic battery behavior are untouched.
- This touches routing only for records that actually carry a window, i.e. R9 rows.

## 5. Why existing machinery cannot represent it today

- `HistoricalFractalish.apply("VALID")` appends `"VALID"` to `unmodeled` and stores
  nothing (representations.py `elif kind == "VALID"` branch).
- `route()` calls `core.route_decision(e, ...)` which consults memories/scars/by
  declared scope; it has no time parameter and no window field, so a window can never be
  stored or consulted. `t` is typed but unused.
- No existing cause string is `expired_outside_window`; the closest (`evidence_missing`)
  would be wrong (a IS formed). Neither A..D representations nor the dependency gate
  provides a time gate.

## 6. Expected effect on prior tranches / freezes

- R0..R8 rows never declare a window and never time-bound a query; the gate must be
  inert for them → A/B/C/D and all previously repaired rows remain byte-identical on
  `rep/level/seed/label/route_correct/cause_fidelity/state_bytes_after_prefix`.
- Gate OFF (ablation toggle mirroring `dependency_gate`) must reproduce the current
  frozen R9 numbers (72/96, 24 false proceeds), i.e. historical behavior.
- No new false holds predicted inside R0..R8.

## 7. Predicted new failure modes

- Introducing a time gate could, in a future rung, interact with the dependency walk
  (a prerequisite whose window expired should block its dependents). That interaction
  is NOT required to fix the 24 residuals (R9 has no dependencies) and is out of scope
  unless the adversarial battery demands it.
- Risk of cause-string drift if the gate is placed before/after the dependency check;
  must verify exact ordering to keep `expired_outside_window` the emitted cause for the
  `a_at_t6` HOLD (and not, e.g., a wrong `evidence_missing` or `prerequisite_missing`).
- Risk that a window recorded at the wrong (e,ctx) granularity changes unrelated rows.

## 8. Ablation to establish causal responsibility

- Toggle (e.g. `time_gate`/`validity_gate`): OFF → frozen R9 baseline reproduces
  (72/96, fp 24); ON → R9 96/96, totals route 1248→1296? (n=96 R9 rows: +24 correct),
  fp 24→0, fh 0; RESTORE == ON.
- Cross-check every prior freeze's FULL_LADDER_REGRESSION bytes with gate ON and OFF;
  both must show A/B/C/D bit-identical and only R9 delta.
- Cause fidelity: the 24 formerly-false rows must match oracle causes exactly
  (`["expired_outside_window"]`); no other change of causes in R9.
- This ablation (labeled `CAUSAL_IMPLEMENTATION_EVIDENCE_WITHIN_THE_SOFTWARE_ASSAY`)
  attributes the +24 to the gate, scoped to this assay only.

A decision to implement is out of scope for this hypothesis document; this file exists
so that if implementation happens, the claim is pre-registered with predicted effects
and the exact ablation protocol.