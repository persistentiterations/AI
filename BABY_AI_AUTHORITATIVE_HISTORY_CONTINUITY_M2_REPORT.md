# BABY_AI_AUTHORITATIVE_HISTORY_CONTINUITY_M2_REPORT

**Tranche:** M2 — authoritative-history continuity across process death (HOST ONLY).

**Verdict: M2 HOLD (partial).** The core continuity claim holds: event identity,
historical ordering, current authority, causal resolution linkage, and resulting
HOLD/PROCEED behavior all survive genuine process death. But the **provenance
fail-closed invariant does not hold** — reconstruction silently accepts empty
provenance (the exact Motorola defect), and erasing the historical scar silently
proceeds. No v4 dependency, no LLM, Motorola untouched.

## Prior authority

`3782a166e3f30aee9a4d0f5bde73b8661d799cab` (R-001 allocator continuity), tag
`BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1`.

## What was run

Genuine separate-process cycle (cold restart via serialized state, never the same
in-memory object):

- **Invocation A** (`phase-a`): build H1 (safe + contradiction) → `HOLD` → persist.
- **Invocation B** (`phase-b`): load H1 → `HOLD` → RESOLVE → `RELEASE` → persist.
- **Invocation C** (`phase-c`): load H1' → `RELEASE` → verify retained scar + lineage.

Runner: `baby_ai/assays/authoritative_history_continuity.py`. Test:
`baby_ai/tests/test_m2_continuity.py`.

## Canonical state hashes (deterministic)

- before-resolution persisted state semantic hash: `842f2c4990ea3da1`
- after-resolution persisted state semantic hash: `bda266df01592ee5`
- receipt tips: before `1e598d71a4815f24`, after `c23ec6731f34638b`

Determinism verified: both hashes byte-stable across two full re-runs.

## Invariant results

| # | Invariant | Result |
|---|---|---|
| I1 | identity continuity (mem-0000/mem-0001, scar-0000) | **PASS** |
| I2 | ordering continuity (receipt seq chain) | **PASS** |
| I3 | provenance continuity | **PARTIAL / FAIL** (receipt evidence survives; formal `ProvenanceLedger` holds only load-time bookkeeping, no event source binding) |
| I4 | causal-link continuity (scar→memory, lineage [active, resolved]) | **PASS** |
| I5 | archive continuity (scar stays `hold` after resolve) | **PASS** |
| I6 | authority continuity (`scar_statuses={"scar-0000":"resolved"}` survives) | **PASS** |
| I7 | decision continuity (HOLD→HOLD, RELEASE→RELEASE) | **PASS** |
| I8 | cause continuity (`contradiction_scar_blocking` / `formed_decision:RELEASE`) | **PASS** |

## Corruption controls

| Case | Result | Note |
|---|---|---|
| C1 missing provenance | **FAIL (no fail-closed)** | reconstruction accepted empty provenance; ledger repopulated with load-time bookkeeping only (`FormationCore`, `FormationCore/allocator`) |
| C2 tampered content | **PASS (fail-closed)** | `integrity_mismatch` via `semantic_hash` |
| C3 broken causal ref | **PASS (acceptable)** | reverted to `HOLD`, not silent PROCEED |
| C3b scar erased | **FAIL (no fail-closed)** | history erased → silently `RELEASE` |
| C4 ordering corruption | **PASS (fail-closed)** | `integrity_mismatch` via `semantic_hash` |

## Receipts vs provenance (the decisive finding)

The `ReceiptLedger` survives and validates (proves operations happened). The
`ProvenanceLedger` after reload contains only `FormationCore`, `plasticity_executor`,
and `FormationCore/allocator` records — **load-time bookkeeping, not the original
event's source binding** (`domain=warehouse`, `kind=contradiction`). This is exactly
the Motorola finding: **receipt continuity is not provenance continuity.** The
authority-bearing contradiction event does not resolve to any authoritative
provenance record in the formal ledger; its evidence lives only in the receipt
chain and the compressed memory.

## First failing invariant

**I3 (provenance continuity) → C1 (missing provenance does not fail closed).**

## Minimum follow-on repair (proposed, NOT implemented)

Add a provenance-presence/binding gate at the load boundary: record per-event
provenance (source + kind) into the `ProvenanceLedger` at `ingest`/`resolve`, and
require — on reload — that every authority-bearing event (contradiction scar,
resolution) resolves to an authoritative provenance record whose identity matches
the receipt chain; otherwise `HOLD_CONTINUITY_FAILURE: provenance_missing`. The
same gate should treat a missing historical scar (C3b) as a continuity failure,
not silent PROCEED.

## Answers to the twelve questions

1. event identity survived — **YES** (mem-0000/mem-0001, scar-0000).
2. historical ordering survived — **YES** (receipt seq chain).
3. provenance survived — **PARTIAL** (receipt yes; formal provenance ledger no).
4. causal linkage survived — **YES** (scar.memory_ids + lineage).
5. current authority survived — **YES** (resolved status).
6. route decision survived — **YES** (HOLD/PROCEED).
7. route cause survived — **YES** (identical reason strings).
8. legitimate resolution survived — **YES**.
9. original scar/history survived resolution — **YES** (scar stays `hold`).
10. broken provenance failed closed — **NO** (C1 gap).
11. tampering failed closed — **YES** (C2/C4 via semantic_hash).
12. process death revealed hidden in-memory dependency — **NO** (identical results across genuine subprocess reloads).

## Tests

`python -m pytest baby_ai/tests -q` → **102 passed** (100 + 2 M2 tests). Prior
R8/R9/MARK/CROSS/R-001 freezes unchanged; ladder `representations.py` untouched.

## Claim boundary (if the positive half were isolated)

The FormationCore persistence path preserves event identity, historical records,
current authority, causal resolution relationships, and HOLD/PROCEED behavior
across controlled cold restarts. This does **not** extend to provenance-binding
continuity (fails), nor to general machine identity, consciousness, Motorola,
model continuity, or production durability.

---

**M2 STATUS:** HOLD (partial — provenance fail-closed invariant fails)
**PRIOR AUTHORITY:** `3782a166e3f30aee9a4d0f5bde73b8661d799cab`
**M2 IMPLEMENTATION SHA:** (this commit; no freeze tag — see receipt)
**M2 TAG:** NONE (HOLD; not frozen)
**TESTS:** 102 passed
**IDENTITY CONTINUITY:** PASS
**PROVENANCE CONTINUITY:** FAIL (receipt yes; formal provenance ledger no)
**CAUSAL CONTINUITY:** PASS
**AUTHORITY CONTINUITY:** PASS
**COLD-RESTART DECISION CONTINUITY:** PASS
**CORRUPTION CONTROLS:** C2/C4/C3 PASS; C1 + C3b FAIL (no fail-closed)
**PRIOR FREEZES CHANGED:** NONE
**v4 DEPENDENCY:** NONE
**MOTOROLA TOUCHED:** NO
**NEXT ACTION:** implement the provenance-presence/binding gate at the load boundary (minimum repair), then re-run M2
**DO NOT DO YET:** do not touch the Motorola, do not integrate v4, do not freeze M2 as PASS
