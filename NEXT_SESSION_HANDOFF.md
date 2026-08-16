# NEXT_SESSION_HANDOFF

Status of the Baby AI FormationCore tranche work at end of this session.

## What is committed / frozen

- `fff3b34` — FormationCore DEPENDENCY v0.1 (prior tranche, READ-ONLY).
- `0e64df6` — FormationCore CYCLE / RELIEVE repair R8 (prior session; 13 files;
  message "FormationCore: freeze recursive dependency cycle/relieve repair R8"). Frozen
  package `BABY_AI_FORMATIONCORE_CYCLE_RELIEVE_REPAIR_v0_1`:
  - R8 routes+causes 1200→1248; fp 72→24 (R9 residual only); fh 0.
  - Chromosomal/relieve adversarial 17/17; ablation OFF==historical, ON==repaired,
    RESTORE==ON; A/B/C/D bit-identical to original freeze.
  - Cycle cause fidelity 48/48 exact; pytest 96 passed; deterministic regeneration
    verified byte-identical.
- NEW R9 FREEZE — FormationCore TEMPORAL VALIDITY gate v0.3 (`VALID` window + exact
  `expired_outside_window` cause). Commit: `797598a` "FormationCore: freeze temporal
  validity gate R9 (VALID window, expired_outside_window)". Verifications that stay
  reproducible:
  - R9 census 9 seeds → 24 residuals driven to 0 (a_at_t6 = `expired_outside_window`
    exact decision + cause). Full ladder R0–R10 × seeds 0–4: E completes 55/55 task-runs
    (only incomplete runs are Rep A, the relation-less baseline, untouched); cause
    fidelity 1.0; 96 tests pass.
  - OFF-toggles verified: `validity_gate` OFF resurrects the R9 residuals (VALID→unmodeled);
    `dependency_gate` OFF restores DEPEND→unmodeled. Both are ablation-only, never shipped.
- NEW TRANCH FREEZE — MARK/RESOLVE dependency-walk repair (THIS session), committed on top
  of `797598a` as its own commit, never patched inside the R9 commit. Frozen package:
  `BABY_AI_FORMATIONCORE_MARK_RESOLVE_DEPWALK_v0_1` (package byte-comparison after commit;
  manifest registers the frozen files below... ). Scope: ONLY
  `baby_ai/ladder/representations.py`, the recursive walk's contradiction reading now uses
  the same current plasticity authority as surface routing; new gate
  `contradiction_authority_gate` (default True), OFF re-anchors the recorded pre-repair
  residual for audit. Raw MARK scars kept as ordered history. Witness
  `FORM a; DEPEND c a; MARK a; RESOLVE a` → query `c` = PROCEED (matches oracle) with the
  gate ON (matches oracle PROCEED) and reverts to the pinned pre-repair HOLD
  `prerequisite_missing:a` with the gate OFF. Condition: 96/96 tests; census E 55/55
  all_correct cause fidelity 1.0; R9/R8 freezes untouched.
- Branch `hostile-qualification-v0_1`; NO git remote configured (no GitHub push possible
  without wiring a remote/branch policy first); no CI exists in-repo.

## Documents produced this session (repo root, uncommitted)

New MARK/RESOLVE tranche docs:

- `MARK_RESOLVE_PRE_REPAIR_BOUNDARY.md` — receipt at tree state `797598a` taken BEFORE
  repair (evidence preserved; witness NOT edited to flatter the fix; oracle cause strings
  contractual).
- `MARK_RESOLVE_DEPWALK_DEFECT_WITNESS.md` — pre/post full divergence table, root cause,
  fix, "Not repaired here" list (two additional divergences surfaced during the
  acceptance battery).
- `HISTORICAL_VS_CURRENT_CONTRADICTION_SEMANTICS.md` — the two-semantics model
  (retained scar = history, plast = current authority, single book for surface+walk).
- `BABY_AI_FORMATION_GRAMMAR_REGISTER_v0_1.md` — closed cause set + operation grammar +
  state-keeping rule (v0_1 addition) + claim boundaries.
- `BABY_AI_FUTURE_TEACHING_CONTRACT_v0_1.md` — non-negotiables, repair semantics ledger,
  tranche boundary, verification contract.
- `MARK_RESOLVE_DEPWALK_TRANCHE_MACHINE.json` — machine-readable witness before/after,
  both logged secondary divergences, census numbers.

Prior docs still in repo root (from R8/R9 sessions):

- `FORMATIONCORE_R8_FORMATIVE_INTERPRETATION.md` — post-hoc; explicit first paragraph
  disclaimer; Fabulous Five observations; `CANDIDATE_RESIDUAL_BUILD_SPECIFICATION`;
  `NOT TESTED` for scale invariance.
- `R9_COUNTEREXAMPLE_CENSUS.md` + `R9_COUNTEREXAMPLE_CENSUS_MACHINE.json` — all 24
  residuals (seed 0..23, label `a_at_t6`), single case.
- `R9_FAILURE_CLASSIFICATION.md` — one cluster; single missing relation
  (current-in-window temporal validity → `expired_outside_window`).
- `R9_MINIMUM_RELATION_HYPOTHESIS.md` — BEFORE-implementation hypothesis with the exact
  proposed gate, expected deltas, and ablation protocol.
- `RESIDUAL_BUILD_SPEC_MEASUREMENT_V0.md` + `RESIDUAL_BUILD_SPEC_MEASUREMENT_MACHINE.json`
  — A/B/C experiment; B reconstructs all, C fails at-prefix; no smaller defensible rep;
  honest `NO_MEANINGFUL_RESIDUAL_COMPRESSION`.
- `FORMATIONCORE_FABULOUS_FIVE_CROSSWALK_V0.md` — observation layer only; claim
  boundaries; history-equivalence note.

## R9 state

REPAIRED AND FROZEN (commit `797598a`). Implemented the temporal-validity gate in
`HistoricalFractalish` (`baby_ai/ladder/representations.py`): `validity_gate` toggle (ON by
default), VALID→`record_valid_window` adapter path (OFF→`unmodeled`), `_in_valid_window`
exact mirror of oracle `_in_window` (per-context fallback to GLOBAL, `t is None` anchors to
applied-op count = oracle `t_real = o.time`), surface gate in `route()` appends the exact
cause `expired_outside_window`, `t` threaded through `_dep_ok`/`_prereq_ok` so the
recursive walk honors windows like `_route_internal`. Verified: R9 census 9 seeds → 24
residuals driven to 0 (a_at_t6 = `expired_outside_window` exact); full ladder R0–R10 ×
seeds 0–4 → E completes 55/55 task-runs (only incomplete runs are Rep A, the relation-less
baseline, untouched); cause fidelity 1.0; 96 tests pass; OFF-toggles verified
(validity OFF resurrects R9 residuals, dependency OFF restores DEPEND→`unmodeled`).
Prior R8 freeze (`0e64df6`) untouched and still read-only.

## MARK/RESOLVE tranche state (REPAIRED, this session)

The pre-existing stale-scar defect logged at R9 time (MARK→RESOLVE clears surface
contradiction but the recursive dep-walk still reads the retained MARK scar as active) is
now REPAIRED as its own separate commit on top of `797598a`. The `MARK_RESOLVE_DEPWALK`
hypothesis doc and the witness doc were updated to REPAIRED status. R9 remains frozen and
untouched. Details in the witness doc and machine JSON.

### Two secondary divergences surfaced during acceptance battery (LOGGED, NOT absorbed)

1. **SUPERSEDE+RESOLVE surface divergence**: after `SUPERSEDE a HOLD; RESOLVE a`, E's
   surface for `a` is PROCEED while oracle says HOLD `declared_prohibition`; the walk for a
   dependent `c` already matches the oracle (HOLD `prerequisite_missing:a`). Gate ON/OFF
   neutral; predates tranche. Needs its OWN later tranche on the surface adapter path.
   Minimal witness: `FORM a f; DEPEND c a; SUPERSEDE a f HOLD; RESOLVE a f`.
2. **repeated-MARK + one RESOLVE**: `FORM a f; MARK a f; MARK a f; RESOLVE a f` →
   oracle PROCEED (bool merge), but E keeps two always-active scars so one RESOLVE widens
   nothing; E surface AND walk both HOLD `active_contradiction` (they AGREE — so this is an
   adapter-vs-oracle collision, not a surface/walk split). Gate ON/OFF neutral; predates
   tranche. Next-tranche hypothesis: RESOLVE must supersede EVERY current MARK scar for
   (e,g,ctx), or MARK must merge current authority instead of appending a fresh live scar.

## Things to check on resume

- `git remote -v` empty: no push happened; no GitHub/CI evidence could be produced.
  Remote receipt is `NO_REMOTE_CONFIGURED`; CI receipt is absent (no existing remote
  pipeline). If the user wires a remote + branch policy, pushing unchanged frozen commits
  is the allowed action (no force-push, no auto-merge to main).
- Secret hygiene: none of the new documents/assays touch `.env`/keys/credentials; the
  repo's `.gitignore` covers `baby_ai/artifacts/` (artifacts committed with `-f`).
- Verify prior frozen packages (FREEZE/DEPENDENCY/CONTEXT/APPLICABILITY, R8, R9) remain
  read-only before any further commit (they were, as of this session).
- Assay scripts live in `baby_ai/assays/` (uncommitted, not yet in frozen package hash
  lists).
- Final report deliverables checklist (Parts 7-19): COMMITTED/DEMONSTRATED/.../HOLD
  sections + answers A-O must be produced at session end.

## Commands that work

- Tests: `py -m pytest baby_ai/tests -q` (96 pass). `python -m pytest` FAILS (hermes
  venv has no pytest).
- Freeze regeneration: `python -m baby_ai.assays.repair_cycle_relieve` (deterministic;
  verify by SHA comparison against frozen package, excluding `manifest.json`).
- Census: `python -c "from baby_ai.assays.r9_census import main; main()"`.
- Measurement: `python -c "from baby_ai.assays.residual_build_spec_measurement import main; main()"`.