# R9 Counterexample Census — 24 residual false proceeds

Status: description of evidence only; **no repair was performed during the census**.
Census produced programmatically by `baby_ai/assays/r9_census.py`; machine-readable
equivalent in `R9_COUNTEREXAMPLE_CENSUS_MACHINE.json` (24 records, one per residual).

Frozen context: commit `0e64df6` (R8 cycle/relieve repair). After R8, the only E-level
battery failure class remaining is the R9 temporal-validity residual: across the 24
frozen seeds of `make_R9`, exactly **24/96** R9 queries are wrong, all in row
`a_at_t6` (route `false_proceed`: E says PROCEED, oracle says HOLD
`expired_outside_window`). `a_at_t2`, `a_at_t3`, and `unrelated` are correct on all 24
seeds (72/96 correct). R9 = `temporal_validity`; causal demand: "a FORMed with a VALID
window [2,4]. Why PROCEED at t=2,3: inside window. Why HOLD at t=6: expired_outside_window."

## 1. Per-fixture records (all 24)

Each record (see machine file `R9_COUNTEREXAMPLE_CENSUS_MACHINE.json` → `residuals[]`)
contains:

| field | meaning |
|---|---|
| `case_id` | `R9-S<seed:02d>-a_at_t6` |
| `seed` | frozen seed 0..23 |
| `label` | always `a_at_t6` |
| `op_stream` | the 3-op R9 program (`FORM(a)` → `VALID(a,[2,4])` → `FORM(other)`), plus the query |
| `query` | `{"label":"a_at_t6","e":<a>,"g":<fam>,"t":6}` |
| `divergence.earliest_state_divergence` | op index 1: the `VALID` op. Oracle records `o.valid[(a,ctx)]=[(2,4)]`; FC marks the op `unmodeled` (no temporal primitive), so no window is ever stored |
| `divergence.at_query_index` / `point_kind` | the residual surfaces at query-evaluation: oracle applies `_in_window` (t=6 ∉ [2,4] → HOLD), FC's `route()` has no time gate → PROCEED |
| `oracle_route` / `oracle_causes` | `HOLD` / `["expired_outside_window"]` |
| `fc_route` / `fc_causes` | `PROCEED` / `[]` |
| `divergence_kind` | `route_false_proceed` (all 24) |
| `missing_causes` | `["expired_outside_window"]` (the relation E cannot express) |
| `formed_state` | both `a` and the second item are formed (ReLEASE decision), both under the same family token |
| `contradiction_state` | 0 scars, no contradiction, no supersede |
| `dependency_state` | `dependencies` empty; `dependency_ledger` empty (R9 has no DEPEND/RELIEVE) |
| `applicability_ctx_state` | query ctx `*` (global), family token set, `t=6`, recorded window `[2,4]` |
| `scars_history` | none; `unmodeled=["VALID"]` on the FC replay |
| `core_snapshot` | full FC `memories` (2 memorized subjects; both decision `RELEASE`), scars, dependencies, ledger, unmodeled |

All 24 seeds are structurally identical in every field except the seeded surface/grand
family names; therefore the residual is **species-stable across seeds**: any one record
describes all 24.

## 2. Divergence locus

- Earliest op at which FC state diverges from oracle state: **op index 1, `VALID`**
  (`VALID(e=a, g=<fam>, from=2, to=4)`); the window is simply not captured by FC
  (`unmodeled`).
- Earliest query at which the divergence is observable: **`a_at_t6`** (t=6); at t=2 and
  t=3 both sides agree (PROCEED) because the expired/outside case never arises inside
  the window.
- The oracle cause E is missing is exactly `expired_outside_window`, which corresponds
  to `OracleState.valid` / `_in_window`: the relation "entity is currently within an
  applicable VALID time window" does not exist in FC's routing.

## 3. What is NOT in this census

- No repair, no hypothesis, no code change. This file records counterexamples only.
- No claim that VALID windows are the *only* possible R9 demand; the census reports the
  24 residuals that actually exist in the frozen battery.

See `R9_FAILURE_CLASSIFICATION.md` for the single observed cluster, and
`R9_MINIMUM_RELATION_HYPOTHESIS.md` for the before-implementation proposal.