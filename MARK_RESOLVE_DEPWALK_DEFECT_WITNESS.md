# MARK/RESOLVE recursive-walk defect witness (BEFORE repair)

Defect: after `MARK e` then `RESOLVE e`, the top-level surface query on `e`
succeeds but a dependent entity `c` reached through the recursive dependency
walk still reports `HOLD ["prerequisite_missing:e"]`. The walk read a stale,
historical contradiction instead of the resolved (current) authority.

## Minimal repro (group f, context *)

ops:

```
FORM    a  f
DEPEND  c  a
MARK    a  f
RESOLVE a  f
```

full query `c`:

| source            | decision | causes               |
|-------------------|----------|----------------------|
| oracle            | PROCEED  | []                   |
| E surface         | PROCEED  | []                   |
| E recursive walk  | HOLD     | [prerequisite_missing:a] |

## Root cause (pre-repair)

`_own_contradicted(e,g,ctx)` in `historical_fractalish` was pinned to the raw
retained MARK scar and never rechecked after the `RESOLVE` operation mutated
plasticity state (`plast`). The surface query rebinds through
`setPLASTI_CITNESSn`/plasticity status ("superseded") and therefore returned
PROCEED, but the recursive walk path (walking dependencies before deciding)
still called the raw-contradiction predicate and produced a HOLD. History and
current authority diverged inside one representation, causing a surface/walk
disagreement.

## Boundary

- Worktree state at first observation: HEAD `797598a` (pre-tranche), gate
  state unmodified; validity_gate True; 96/96 tests passing.
- Repro confirmed on detached `159ba7f` (pre-R9) AND `797598a` (pre-tranche),
  OFF/ON of contradiction_authority_gate both reproduced the walk HOLD.

## Fix applied (tranche `MARK_RESOLVE_DEPWALK`)

The recursive walk now consults the same current contradiction authority that
the surface uses: `_own_contradicted` is bound to the plasticity scar-status
projection (`READ_CURRENT`) whenever the repair gate is enabled
(`contradiction_authority_gate`), exactly mirroring `_blocking_scars_for`
only when the raw retained-mark predicate sunders from the surface. Raw MARK
scars remain ordered history; only current authority reads through plast.

## Post-repair (re-run)

| source            | decision | causes               |
|-------------------|----------|----------------------|
| oracle            | PROCEED  | []                   |
| E recursive walk  | PROCEED  | []                   |

With `contradiction_authority_gate=False`, the walk reverts to the pinned
pre-repair residual (HOLD prerequisite_missing) so the old behavior remains
auditable offline; default True.

## Not repaired here (separate tranches, logged)

1. `<docs>HISTORICAL_VS_CURRENT_CONTRADICTION_SEMANTICS.md`: doc only, no code.
2. SUPERSEDE+RESOLVE surface divergence: oracle keeps `declared_prohibition`
   for a RESOLVEd SUPERSEDE-HOLD; E surface PROCEEDs; E recursive walk
   HOLDs (matches oracle). Gate ON/OFF neutral, predates tranche. Minimal
   witness: `FORM a f; SUPERSEDE a f HOLD; RESOLVE a f; DEPEND c a` →
   E surface `c` = PROCEED (oracle HOLD declared_prohibition). Separate
   next-tranche hypothesis: RESOLVE must not clear declared_prohibition
   unless the scar provenance is contradiction-marking; must repair surface
   adapter path.
3. repeated-MARK + one RESOLVE: oracle collapses repeated MARKs (bool merge);
   E keeps two always-active scars so one RESOLVE cannot clear both; surface
   AND walk both HOLD (they agree — an adapter-vs-oracle collision, not a
   surface/walk split). Gate ON/OFF neutral, predates tranche. Minimal
   witness: `FORM a f; MARK a f; MARK a f; RESOLVE a f` → E surface PROCEED
   (oracle PROCEED) but E `_own_contradicted(a)` remains True on a dependent.
   Actually distinct defect: RESOLVE only pops the single most recent
   `_scar_for[e]`; second MARK's scar stays unresolved. Next-tranche
   hypothesis: RESOLVE must supersede every current MARK scar for (e,g,ctx),
   or MARK must merge current authority instead of appending a fresh live
   scar.

## Post-conditions

- Full ladder census (R0-R10 x seeds 0-4 x A-E): 55/55 E runs all_correct,
  cause_fidelity 1.000; 96/96 suite green.
- R9 validity gate untouched (<11>/24 interplay re-run: residuals stay 0 ON,
  reappear OFF as previously recorded).
- All cause strings identical to oracle (`prerequisite_missing:<prereq>`,
  `active_contradiction`, `declared_prohibition`, `expired_outside_window`,
  `evidence_missing`, cycle HOLD via mutual prerequisite_missing).