# MARK/RESOLVE dependency-walk defect — frozen witness

Status: LOGGED ONLY, NOT REPAIRED, leave frozen. Discovered incidentally by the R9
temporal-validity adversarial boundary battery. Orthogonal to R9; R9 does not create or
remove it, and it predates R9 (reproduces on the pre-R9 committed tree).

## Witness (minimal failing operation sequence)

All ops in group `f`, global context `*`. Query target: `c`, after all four ops.

```
FORM    a  f
DEPEND  c  a          (c depends on a)
MARK    a  f
RESOLVE a  f
```

```
oracle (route_oracle, ctx=*, t=None): decision PROCEED, causes []
E      (HistoricalFractalish route):   decision HOLD,  causes ["prerequisite_missing:a"]
```

## Minimality controls

| Sequence | Oracle(c) | E(c) | Diverges |
|---|---|---|---|
| FORM+DEPEND+MARK+RESOLVE (witness) | PROCEED [] | HOLD [prerequisite_missing:a] | YES |
| FORM+MARK+RESOLVE (no DEPEND) | PROCEED [] | PROCEED [] | no (DEPEND edge is the trigger surface) |
| FORM+DEPEND+MARK (no RESOLVE) | HOLD [prerequisite_missing:a] | HOLD [prerequisite_missing:a] | no (MARK alone is symmetric) |
| FORM+VALID[2,4]+DEPEND+MARK+RESOLVE | HOLD [prerequisite_missing:a] | HOLD [prerequisite_missing:a] | no (window semantics aligned in the walk; defect unchanged) |
| DEPEND+MARK+RESOLVE (no FORM) | — | KeyError in E | E requires a prior FORMed belief before RESOLVE; FORM is load-bearing in E |

The four-op sequence is minimal among sequences whose surface `c` oracle answer is
PROCEED: dropping DEPEND removes the failing surface, dropping RESOLVE removes the
reversal that the oracle honors, and dropping MARK removes the stale scar.

## Earliest internal divergence

At prefix 4 (after `RESOLVE`), the recursive walk still evaluates `a` as unsatisfied:

```
prefix=0: dep_internal(a) not applicable        | surface a OK, dependent c OK
prefix=1: dep_internal(a)=True  (after FORM)    | c OK (PROCEED)
prefix=2: dep_internal(a)=True  (after +DEPEND) | c OK (PROCEED)
prefix=3: dep_internal(a)=False (after +MARK)   | c OK (HOLD prerequisite_missing:a)  <- correct, active contradiction
prefix=4: dep_internal(a)=False (after +RESOLVE)| c DIVERGES (expected PROCEED, got HOLD) <- stale scar
```

`_dep_ok("a", "f", "*", frozenset())` returns `False` at prefix 4; the disabling condition
is `_own_contradicted("a", "f", "*") == True`.

## Earliest route/cause divergence

Also at prefix 4, query `c`:

```
expected: PROCEED / []                      (oracle honors the RESOLVE)
got:      HOLD      / ["prerequisite_missing:a"]
```

## Surface-route behavior vs recursive _dep_ok behavior

At prefix 4 the surface route for the scarred entity is CORRECT, the recursive walk is NOT:

```
route("a", "f", ctx=*) -> PROCEED []                 (matches oracle; RESOLVE cleared current contradiction)
_dep_ok("a", "f", "*", frozenset()) -> False         (sees the retained MARK scar as an active contradiction)
route("c", "f", ctx=*) -> HOLD ["prerequisite_missing:a"]   (depends on the false negative)
```

So RESOLVE correctly clears the contradiction state that `route_decision` consults for the
SURFACE query, but `_own_contradicted` (used only by the dependency walk) still interprets
the retained MARK scar as currently active. This is the exact mechanism the next tranche
must address.

## R9 ON/OFF neutrality

Toggling `HistoricalFractalish.validity_gate` on the witness changes nothing:

```
R9 ON  -> HOLD ["prerequisite_missing:a"]   (defect present)
R9 OFF -> HOLD ["prerequisite_missing:a"]   (defect present)
```

The gate-path (`_in_valid_window`) is inert on this sequence: no VALID window queries drive
it, and adding a VALID window ([2,4]) keeps oracle and E in agreement. R9 neither creates
nor removes the defect.

## Defect predates the R9 change

Reproduced from a detached worktree at git `159ba7f` (pre-R9 committed tree, before any R9
edit):

```
baseline oracle c       -> PROCEED []
baseline E surface c    -> HOLD ["prerequisite_missing:a"]   (same divergence)
baseline _dep_ok(a)     -> False, _own_contradicted(a) -> True
```

Confirmed : the defect exists on the historical baseline with the R9 change absent.

## Do not repair inside R9

R9's hypothesis — current-in-window temporal validity with exact cause
`expired_outside_window` — is COMPLETE and VERIFIED on its declared target (the 24 R9
residuals driven to 0; full census + ablation + OFF toggles pass). This MARK/RESOLVE
defect is a separate tranche with its own initial hypothesis
(see `MARK_RESOLVE_DEPWALK_TRANCHE.md`).