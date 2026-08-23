# CURRENT AUTHORITY — Baby AI / FormationCore

This file records the current authoritative frozen Baby AI implementation and its
lineage, for archival/backup purposes. It is a **pointer**, not the implementation.

## Authoritative implementation (frozen)

- **Implementation freeze commit:** `9d6317351f74032c77883db198d637777af4a33b`
  - message: `CROSS_CONTEXT_RESOLVE: (e,ctx)-scoped RESOLVE authority behind context_resolve_gate; freeze v0.1 package (separate tranche)`
- **Frozen package:** `BABY_AI_FORMATIONCORE_CROSS_CONTEXT_RESOLVE_v0_1`
  - location: `baby_ai/artifacts/repair/BABY_AI_FORMATIONCORE_CROSS_CONTEXT_RESOLVE_v0_1/`
- **Tag:** `BABY_AI_FORMATIONCORE_CROSS_CONTEXT_RESOLVE_v0_1`

## Lineage (linear, oldest -> newest)

| Commit | Role |
|--------|------|
| `0e64df61a61e94f591242e69bce297ee3912f0d9` | R8 freeze — recursive dependency cycle/relieve repair (`BABY_AI_FORMATIONCORE_CYCLE_RELIEVE_REPAIR_v0_1`) |
| `797598ad525a7e7980c435f88e72d9467892127f` | R9 freeze — temporal validity gate (VALID window / `expired_outside_window`) |
| `8735911704fb257c096983c2d36059bb6da234f1` | MARK/RESOLVE repair (contradiction_authority_gate) |
| `9f044318b5855aed2aef871623d02ea7af44ec79` | docs: record tranche head 8735911 |
| `d64c45b89e9b8273a8e586cd26ef9a84e3759e90` | MARK/RESOLVE freeze (`BABY_AI_FORMATIONCORE_MARK_RESOLVE_DEPWALK_v0_1`) |
| `9d6317351f74032c77883db198d637777af4a33b` | **CROSS_CONTEXT_RESOLVE freeze (CURRENT AUTHORITY)** |
| `442cb7f7156868a12153ff38b911d010ad0847a5` | docs: record tranche head 9d63173 (project's own docs head) |

`main` branch tip (`1919578214b938d39a54e00c5a81797113c3c953`,
BABY_AI_CAUSAL_CORE_MVP_2026-08-14) is an ancestor of this lineage.

## Implementation SHA vs archival SHA

- **Implementation authority = `9d6317351f74032c77883db198d637777af4a33b`** (frozen source + package).
- This receipt and any later backup/archival commit are **metadata only** and do not
  redefine the implementation freeze.

## Verify / regenerate

```bash
# tests
python -m pytest baby_ai/tests -q                       # -> 96 passed

# census + cause fidelity (also regenerates FULL_LADDER_REGRESSION.json)
python -m baby_ai.assays.cross_ctx_resolve_freeze       # E 55/55 all_correct, cause fidelity 1.0

# MARK/RESOLVE deterministic regeneration (run at its own freeze commit d64c45b)
python -m baby_ai.assays.mark_resolve_depwalk_freeze    # byte-identical at d64c45b

# R9 residual census (0 residuals expected post-repair)
python -c "from baby_ai.assays.r9_census import main; main()"
```

NOTE: the R9 census command rewrites `R9_COUNTEREXAMPLE_CENSUS_MACHINE.json` (a frozen
pre-repair artifact). Run it in a throwaway worktree; do not run it in the authoritative
checkout.

## Verification results re-confirmed during the GitHub backup session (2026-08-23)

- pytest: **96/96 passed** (clean worktree at 442cb7f).
- CROSS_CONTEXT_RESOLVE full ladder: E **55/55 all_correct**, cause fidelity **1.0**.
- R9 residual census: **0 residuals** (repair holds).
- MARK/RESOLVE witness: gate ON -> **PROCEED** (matches oracle); gate OFF ->
  **HOLD prerequisite_missing:a** (pre-repair residual preserved).
- CROSS_CONTEXT witness: gate ON -> **HOLD active_contradiction** (matches oracle);
  gate OFF -> **PROCEED** (pre-repair residual).
- Deterministic regeneration: CROSS_CONTEXT_RESOLVE byte-identical at HEAD;
  MARK_RESOLVE_DEPWALK byte-identical at its own commit d64c45b (at HEAD one
  adversarial case differs because the later CROSS_CONTEXT tranche changed RESOLVE
  semantics — expected, per-tranche snapshots).
- R8/R9 freeze packages: **untouched** (git status clean; no history rewrite).
