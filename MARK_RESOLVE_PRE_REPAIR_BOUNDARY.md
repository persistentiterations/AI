# MARK/RESOLVE pre-repair boundary receipt

Taken before the recursive-walk contradiction repair (tranche
`MARK_RESOLVE_DEPWALK`). The wrong behavior below is valuable evidence; it was
deliberately preserved unchanged as `MARK_RESOLVE_DEPWALK_DEFECT_WITNESS.md`
(and re-verified here at the tranche start).

## Repo state at boundary

- repo root: `C:\Users\moop\FractalishBuild\baby-ai-assembly-v0.1`
- branch: `hostile-qualification-v0_1`
- HEAD: `797598a` = `797598ad525a7e7980c435f88e72d9467892127f`
  (R9 temporal-validity freeze)
- worktree status at boundary: clean for tracked files (only untracked scratch
  artifacts from earlier sessions present, none load-bearing)
- prior freezes present in history: `fff3b34` (DEPENDENCY v0.1),
  `0e64df6` (CYCLE/RELIEVE R8), `797598a` (temporal validity R9)
- tests: 96/96 passing (`python -m pytest baby_ai/tests -q`)

## Exact pre-repair witness behavior (HEAD `797598a`)

Minimal failing sequence (all ops group `f`, context `*`):

```
FORM    a  f
DEPEND  c  a
MARK    a  f
RESOLVE a  f
```

query `c` (after all four ops):

```
oracle (route_oracle, ctx=*, t=None): PROCEED []
E surface (route): PROCEED []
E recursive walk (dep c): HOLD ["prerequisite_missing:a"]
```

Internal state at the walk:

```
_dep_ok(a)            -> False     (should be True)
_own_contradicted(a)  -> True      (stale: reads raw retained MARK scar)
_dep_grounded(a)      -> True
plast scar status     -> "superseded"  (surface authority says cleared)
raw scar retained     -> scar-0000 kind=MARK (history, untouched)
```

## R9 OFF/ON behavior (unchanged by this tranche)

- `validity_gate=False`: R9 residuals reappear (VALID unmodeled), walk defect
  remains present. R9 was already frozen; this tranche does not touch the
  validity gate.
- `validity_gate=True`: R9 census 24 residuals -> 0 (frozen).

## Pre-R9 reproduction evidence

Both target and the two secondary divergences reproduced on detached worktrees
at `159ba7f` (pre-R9) and `797598a` (pre-tranche):

- MARK/RESOLVE walk defect: present pre-R9 and pre-tranche. Surface PROCEED,
  walk HOLD.
- SUPERSEDE+RESOLVE surface divergence (second defect, NOT repaired here):
  oracle keeps `declared_prohibition`; E surface PROCEEDs; E recursive walk
  HOLDs (`prerequisite_missing`) — the WALK already matches the oracle. Gate
  ON/OFF neutral. Predates tranche.
- repeated-MARK + one RESOLVE (third, orthogonal defect, NOT repaired here):
  oracle collapses repeated MARKs to a single contradiction cleared by one
  RESOLVE; E retains an older unresolved MARK scar, so surface AND walk both
  HOLD. Gate ON/OFF neutral. Predates tranche. Surface and walk AGREE, so it
  is an adapter-vs-oracle collision, not a surface/walk disagreement.

## Boundary contract

- Witness must NOT be edited to make the repair look cleaner.
- Oracle cause strings are contractual (`prerequisite_missing:<prereq>`,
  `active_contradiction`, `declared_prohibition`, `expired_outside_window`,
  `evidence_missing`). The recursive walk never invents generic HOLDs.
- Tranche target ONLY: make the recursive dependency walk read CURRENT
  contradiction authority through the plasticity scar-status projection
  (same source the surface uses), preserving raw MARK scars as history.
- SUPERSEDE+RESOLVE and repeated-MARK+RESOLVE are preserved as separate
  witnesses and handled in their own tranches.