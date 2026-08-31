# FRACTALISH_V4_FORMATIONCORE_RECONCILIATION_REPORT

Read-only reconciliation audit. No implementation, no merge, no rename, no Motorola action.

## 1. Executive verdict

The Grok "Fractalish AI v4" baseline is real, runs, and is byte-stable across its archive/duplicate locations — but it is a **stateless demo runtime**, not an authority/history core. Its PERCEPT→ATAL→RIGOR→CIRCUIT→GUARD→SERA→SessionGlyph spine is a single-shot event classifier with carry-forward JSON and **no persistence, no current-vs-historical authority, and no determinism** (UUID + wall-clock). The now-authoritative FormationCore (R-001 `3782a16`) already owns the genuinely hard, heavily-qualified parts of that territory (history, contradiction scars with current vs historical authority, MARK/RESOLVE/SUPERSEDE/RELIEVE, dependency walking, temporal validity, deterministic HOLD/PROCEED with causes). The correct reconciliation is **not** to wire six named v4 modules around FormationCore; it is to **retire CIRCUIT and GUARD (stateless duplicates), keep PERCEPT/RIGOR/SERA/ATAL as thin upstream/orthogonal utilities, and keep FormationCore as the sole authority/admissibility core.** v4 contributes nothing to M2. M2 is READY_WITH_PRECONDITIONS on FormationCore alone.

## 2. Evidence inspected

- FormationCore repo: `C:\Users\moop\FractalishBuild\baby-ai-assembly-v0.1`
  - branch `hostile-qualification-v0_1`, HEAD `b9d97824c6509c4553cb420a2b26b4af98d2c3da`
  - R-001 authority tag `BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1` → `3782a166e3f30aee9a4d0f5bde73b8661d799cab`
  - prior authority `9d6317351f74032c77883db198d637777af4a33b`
- v4 baseline worktree: `C:\Users\moop\Cognitive-Basin-Worktrees\grok-fractalish-v4-baseline`
  - git branch `grok/fractalish/v4-baseline-closure`, HEAD `998364174143df69deb2cbae049d9f9de1886dce`
  - modules at `python\fractalish_ai\{percept,atal,rigor,circuit,guard,sera,core_runtime,session_glyph}.py` + `mcva/` (4 py) + `natural_math/` (6 py)
  - demos `fractalish-ai\examples\demo_activation.py`, `demo_full_runtime.py`
  - tests incl. `tests\test_fractalish_v4_replay.py`
- Archive: `…\grok-fractalish-v4-baseline\fractalish-ai\reference\fractalish-ai_v4.zip`
  and `C:\Users\moop\Downloads\Articles on X.com\Natural Math\Fractalish Runtime\fractalish-ai_v4.zip`
  — SHA-256 both `3C4FA0509054F5B9C8179579B28BEC7DFBEF6D43A0721623DCB5B77E9B192B72` (83,827 bytes).
- Duplicate extraction: `C:\Users\moop\Cognitive-Basin-Worktrees\fractalish-ai_v4-extracted\fractalish-ai\fractalish_ai\`
  — all 8 spine modules byte-identical to the worktree (SHA-256 MATCH).
- Guardian Intake: `C:\Users\moop\cognitive-basin-platform\imports\grok-guardian-intake\worker.js` (4,043 bytes).
- SERA literature: `…\Machine Consciousness as Persistent Statehood\SERA_LITERATURE_MINING\{08_REVIEW_PACKETS,11_GROK_REVIEW,13_E1_RECONSTRUCTION}\…` (4 files present, research docs).
- Placeholders: `cognitive-basin-platform\packages\{percept,atal,rigor,circuit,guard,sera}` = 1 file each (`.gitkeep` only).

## 3. v4 provenance / lineage

`fractalish-ai_v4.zip` (original) → Grok baseline worktree `python\fractalish_ai\` → duplicate extraction `fractalish-ai_v4-extracted\fractalish-ai\fractalish_ai\`.

- The two `.zip` copies are **byte-identical** (same SHA-256, same size).
- The 8 spine modules are **byte-identical** between the worktree `python\fractalish_ai\` and the duplicate extraction.
- The duplicate extraction is therefore a faithful copy, **not** a competing authority. Only structural difference: worktree keeps the package under `python\`, the extraction under `fractalish-ai\fractalish_ai\` (this is why the replay test targets the extraction with `PYTHONPATH`).

## 4. v4 runtime reproduction (ran now, no repair)

Commands (read-only reproduction; demos write to their own `outputs/` dir):
```
$env:PYTHONPATH = "C:\Users\moop\Cognitive-Basin-Worktrees\fractalish-ai_v4-extracted\fractalish-ai"
python …\fractalish-ai\examples\demo_activation.py     # Guard: PROCEED, glyph hash present
python …\fractalish-ai\examples\demo_full_runtime.py   # Guard: WATCH, MCVA: MCVA, NM delta 0.3613
python …\tests\test_fractalish_v4_replay.py            # "REPLAY TEST PASSED"
```
Result: **both demos and the replay test pass.** However, the SessionGlyph `state_hash` differs between runs (`d0bbb8a509769fa9` vs `17b6ad4a10172e8a`) because `event_id` is `uuid.uuid4()` and `timestamp` is wall-clock. **v4 is non-deterministic.**

## 5. Module-by-module audit

### PERCEPT (`percept.py`)
- **A. What:** `PerceptToken` dataclass + `create_percept()` — structured token from an event (modality, source, timestamp, content_summary, raw_reference, confidence, uncertainty, provenance dict, domain_tags).
- **B. I/O:** event kwargs → `PerceptToken.to_dict()`. `event_id = uuid.uuid4()` (non-deterministic), `timestamp = datetime.now()`.
- **C. Tests/demos:** exercised via `core_runtime` in both demos. Runs.
- **D. State:** ephemeral dataclass; no persistence.
- **E. Authority:** annotation only — cannot alter truth/routing/authority.
- **F. Provenance:** a free-form `dict`; does **not** bind to any real originating event/source.
- **G. Overlap:** **NON-OVERLAPPING** (upstream event→token; FormationCore's `make_event` does the same deterministically).
- **H. Disposition:** **ADAPT** (upstream ReceptorEvent boundary; must gain deterministic identity + real source binding).

### ATAL (`atal.py`)
- **A. What:** `AtalState` pressure fields (coherence, uncertainty, threat, trust, fatigue, frustration, curiosity, boundary_integrity) + `update_atal()`.
- **B. I/O:** confidence/uncertainty/hold_count/contradiction_count/boundary_violation → mutated `AtalState`.
- **C. Tests/demos:** exercised via `core_runtime`. Runs.
- **D. State:** in-memory dataclass.
- **E. Authority:** none — docstring states "Does not decide truth." Pressure only.
- **F. Provenance:** none.
- **G. Overlap:** **NON-OVERLAPPING** (orthogonal annotation).
- **H. Disposition:** **DEFER** (pressure may inform routing/priority later; must never decide truth — invariant currently holds).

### RIGOR (`rigor.py`)
- **A. What:** `run_rigor_checks(event)` → list of `RigorFinding` (analyzer, state PASS/HOLD/REVERSE/WATCH, severity, reason, evidence_present/missing, recommended_action). Analyzers: source_presence, claim_support, contradiction, scope, speculation, similarity_vs_identity, boundary.
- **B. I/O:** event dict → findings list. Pure function, no mutation.
- **C. Tests/demos:** exercised via `core_runtime`. Runs.
- **D. State:** none (stateless).
- **E. Authority:** produces findings consumed by GUARD; does **not** itself set authority.
- **F. Provenance:** checks that a `source` string is present (not real source binding).
- **G. Overlap:** **PARTIALLY OVERLAPPING.** Its `contradiction` check is a weaker, flat concept (event carries `contradictions`) than FormationCore's scar machinery. But `scope`, `speculation`, `similarity_vs_identity` are genuine pre-admission evidence checks FormationCore does **not** have.
- **H. Disposition:** **ADAPT** (pre-admission evidence-checking rules, upstream of FormationCore, never authority).

### CIRCUIT (`circuit.py`)
- **A. What:** `CircuitState` (memory_nodes, contradiction_scars, recovery_routes, trust_channels, open_loops, unresolved_holds) + `update_circuit()`. Scars are `ContradictionScar(claim_a, claim_b, source_a, source_b, status="unresolved")` — flat, no authority projection.
- **B. I/O:** percept + findings + guard_decision → appended nodes/scars/holds/loops.
- **C. Tests/demos:** exercised via `core_runtime`. Runs.
- **D. State:** in-memory list accumulation; no persistence.
- **E. Authority:** none — merely accumulates records.
- **F. Provenance:** `source_a`/`source_b` strings.
- **G. Overlap:** **DUPLICATIVE** (earlier, weaker implementation of FormationCore history/scars/recovery).
- **H. Disposition:** **REPLACE_WITH_FORMATIONCORE.**

### GUARD (`guard.py`)
- **A. What:** `evaluate_guard(rigor_findings, event)` → `GuardResult(decision PROCEED/HOLD/REVERSE/WATCH, reason, triggered_by, confidence)`. Pure translation of findings.
- **B. I/O:** findings + event → decision dict.
- **C. Tests/demos:** exercised. Runs.
- **D. State:** stateless; no memory of prior decisions.
- **E. Authority:** emits a decision but **statelessly** — would be a second, independent authority alongside FormationCore.
- **F. Provenance:** none.
- **G. Overlap:** **CONFLICTING / PARTIALLY OVERLAPPING** — produces PROCEED/HOLD that FormationCore also produces (statefully, with causes).
- **H. Disposition:** **REPLACE_WITH_FORMATIONCORE** for epistemic/admissibility routing. The extra verbs **REVERSE**/WATCH are policy-layer, not epistemic — defer them separately.

### SERA (`sera.py`)
- **A. What:** `SeraRecord` counters (runtime_ms, input/output size, hold/reverse/unsupported/source_missing/contradiction/retry counts, cost_note, memory_delta) + `SeraTimer` + `build_sera_record()`.
- **B. I/O:** runtime + payloads + findings + decision → counters.
- **C. Tests/demos:** exercised. Runs.
- **D. State:** ephemeral accounting.
- **E. Authority:** none.
- **F. Provenance:** none.
- **G. Overlap:** **NON-OVERLAPPING** (complementary instrumentation).
- **H. Disposition:** **KEEP** (primitive cost/waste instrumentation; the larger SERA research program stays separate).

### SessionGlyph (`session_glyph.py`)
- **A. What:** `SessionGlyph` dataclass (activation_id, purpose, operator_constraints, open_loops, unresolved_holds, contradiction_scars, recovery_routes, key_sources, next_action, state_hash) + `build/export/load` + `compute_hash` (SHA-256 of dict).
- **B. I/O:** circuit + decision → glyph; `export/load` JSON file.
- **C. Tests/demos:** exercised + replay test asserts `state_hash` present.
- **D. State:** serializable JSON snapshot with a hash (not a chained ledger).
- **E. Authority:** none (carry-forward artifact).
- **F. Provenance:** `key_sources` string list — weak.
- **G. Overlap:** **PARTIALLY OVERLAPPING** with `ContinuitySnapshot` (which also has semantic_hash but adds receipt/provenance ledgers).
- **H. Disposition:** **ADAPT** (export idea); `ContinuitySnapshot` is the stronger persistence primitive.

### core_runtime (`core_runtime.py`)
- **A. What:** `run_activation_event(event, basin_state)` wires PERCEPT→RIGOR→GUARD→ATAL→CIRCUIT→SessionGlyph→SERA.
- **B. I/O:** event + basin dict → record dict; `default_basin_state()`, `export_decision_record()`.
- **C. Tests/demos:** exercised. Runs.
- **D. State:** `basin_state` dict passed in/out (in-memory carry-forward; no auto-persist).
- **E. Authority:** indirect — houses GUARD's stateless decision.
- **F. Provenance:** none (passes event `provenance` dict through).
- **G. Overlap:** **PARTIALLY OVERLAPPING** with `FormationCore.ingest` (both process an event), but FormationCore is deterministic + authority-bearing.
- **H. Disposition:** **REPLACE_WITH_FORMATIONCORE** as the authority spine; ADAPT for pre/post instrumentation.

## 6. FormationCore capability map (what the R-001-authoritative core already owns)

retained history · contradiction scars (current vs historical) · MARK / RESOLVE / SUPERSEDE / RELIEVE · context scoping · dependencies + cycle guard · temporal validity (VALID windows) · deterministic HOLD/PROCEED with explicit causes · allocator continuity (R-001: id_continuation + reconcile) · operator migration receipts · continuity snapshot · receipt chain · provenance ledger (host) · deterministic id stream · plasticity executor (scar lifecycle authority).

## 7. Overlap matrix

| Capability | v4 component | FormationCore | Conflict? | Recommended owner |
|---|---|---|---|---|
| provenance | PERCEPT(dict)/SessionGlyph(key_sources) | ProvenanceLedger (host) | no (v4 weaker) | FormationCore |
| event admission | PERCEPT | make_event/ingest | no | PERCEPT (upstream) → FormationCore |
| salience | (none) | salience/retrieval | no | FormationCore |
| evidence checking | RIGOR (source/scope/speculation/sim-vs-id) | (none — op grammar only) | no | RIGOR-ADAPT (pre-admission) |
| contradiction | RIGOR (flat) + CIRCUIT (flat scar) | scars w/ authority | **yes (duplicate)** | FormationCore |
| scars | CIRCUIT ContradictionScar | FormationCore scars | **yes (duplicate, weaker)** | FormationCore |
| recovery | CIRCUIT RecoveryRoute (static text) | RELIEVE/recovery semantics | partial | FormationCore |
| dependency | (none) | DEPEND + cycle guard | no | FormationCore |
| temporal validity | (none) | VALID windows | no | FormationCore |
| authority | (none) | current-vs-historical | no | FormationCore |
| HOLD | GUARD (stateless) | route_decision (stateful) | **yes** | FormationCore |
| PROCEED | GUARD (stateless) | route_decision (stateful) | **yes** | FormationCore |
| REVERSE | GUARD | (absent) | no (new verb) | DEFER (policy layer) |
| WATCH | GUARD | (absent) | no (new verb) | DEFER (policy layer) |
| persistence | SessionGlyph (flat+hash) | ContinuitySnapshot + ledgers | partial | FormationCore |
| receipts | (none) | ReceiptLedger (chained) | no | FormationCore |
| causal lineage | (none) | receipts + provenance (host) | no | FormationCore |
| resource accounting | SERA | (none) | no | SERA-KEEP |
| session export | SessionGlyph | ContinuitySnapshot export | partial | FormationCore |

## 8. Duplicate-authority risks

1. **GUARD (stateless PROCEED/HOLD) vs FormationCore route_decision (stateful PROCEED/HOLD).** Two independent answers to the same question. No precedence contract exists. Must resolve: FormationCore owns epistemic/admissibility routing; GUARD's decision must not be consulted for that layer.
2. **CIRCUIT scars vs FormationCore scars.** Same name, different semantics (flat "unresolved" vs current/historical authority). Treating them as interchangeable corrupts both.
3. **RIGOR "contradiction" (event field check) vs FormationCore contradiction scars.** Different objects; conflating them would let a field flag masquerade as qualified authority.
4. **Two memory stores** (CIRCUIT memory_nodes vs FormationCore memories/attractors) — duplicate memory is exactly what the architecture must avoid.
5. **SessionGlyph state_hash vs ContinuitySnapshot semantic_hash** — two different "state identity" notions; must not be merged casually.

## 9. Melissa qualification compatibility

The candidate evidence-qualification `Q=f(L,R,I,S,C)` (local relevance, source reliability, independence, scope, consistency) has **primitive echoes only** in v4: RIGOR's `source_presence`≈R, `scope`≈S, `claim_support`≈C (weak). FormationCore has **no** evidence-qualification gate (it operates on MARK/RESOLVE/DEPEND/VALID op grammar, not evidence quality). The natural home for a future qualification gate is **upstream of FormationCore**, before ops are admitted — reusing RIGOR-style checks plus real provenance (from a determinized PERCEPT) — without touching the authority core. FormationCore hooks that help: `make_event`/`ingest` (admission boundary), `route_decision` (admissibility surface). Nothing in v4 or FormationCore currently implements "count independent lineages," "below-chance sources lose influence," or "structural forgetting by later relevant formation" — those are new, unimplemented.

## 10. M2 relevance

v4 contributes **nothing worth reusing** for authoritative-history continuity. Its only persistence (SessionGlyph) is a flat snapshot + hash with no chaining, no provenance, no ordering, and is non-deterministic. M2 must depend first on the frozen FormationCore components (`FormationCore.from_dict`, `ContinuitySnapshot`, `ReceiptLedger`, `ProvenanceLedger`, `route_decision`, `MigrationReceiptLedger`) — not v4. Do not let v4 complexity inflate M2.

## 11. APTD relevance

Phase 0–2 candidates: **PERCEPT** (upstream ReceptorEvent→token boundary, after determinizing identity + provenance), **RIGOR** (pre-admission evidence checks), **SERA** (cost/waste instrumentation), **ATAL** (orthogonal pressure annotation). CIRCUIT/GUARD should **not** participate (FormationCore replaces them). The battery-vs-text control concern is real and is correctly an APTD experimental-design question, not a v4 module.

## 12. Guardian Intake assessment

`worker.js` is a Cloudflare intake gateway: `receptorEvent` with `guard_decision: 'allow'` **hardcoded**, a naive `"ignore previous"` substring prompt-injection flag, one-time-view + KV TTL quarantine, and a "full sanitization + R2 in prod" placeholder. It is **GUARD-adjacent in name only** — no real guard semantics, no authority, no provenance binding (source is the raw body; the "provenance recorded" claim in the HTML is misleading). Reusable ideas (concept-level only): one-time-view + quarantine lifecycle posture. **Do not call it GUARD.**

## 13. SERA research/runtime distinction

v4 `sera.py` = a ~2 KB runtime accounting module (`SeraRecord`/`SeraTimer`). The SERA_LITERATURE_MINING corpus (REVIEW_PACKET_FOR_GROK, GROK_EXECUTIVE_REVIEW, GROK_COMPLETION_REPORT, GROK_E1_RECONSTRUCTION_REPORT) = adversarial-review/research artifacts about a much broader SERA program. Keep them separate; no file establishes an interface between them.

## 14. Natural Math / R2R boundaries

v4 bundles `natural_math/` (6 py) and `mcva/` (4 py) as demo companions — these are local demo utilities, **not** integrated into FormationCore. No accidental coupling exists in FormationCore (it does not import v4). `R2R VERBICENTRICS` remains a separate scRNA-seq pipeline and is **not** the Baby AI Research-to-Research engine. Both remain downstream; no integration performed.

## 15. Recommended smallest architecture

```
World event
   │
   ▼
ReceptorEvent (deterministic id + real provenance)         [future; PERCEPT-ADAPT]
   │
   ▼
Evidence qualification (RIGOR-style checks, non-authority) [future; Melissa Q]
   │
   ▼
FormationCore.ingest  ── history / scars / deps / validity [KEEP, frozen, sole authority]
   │
   ├──► route_decision ── HOLD / PROCEED (+ explicit causes)
   │
   ├──► ATAL pressure (orthogonal annotation, never truth) [DEFER]
   │
   └──► SERA accounting                                   [KEEP]
   │
   ▼
ContinuitySnapshot + ReceiptLedger + ProvenanceLedger     [KEEP, frozen persistence]
```

## 16. Per-component disposition

- PERCEPT — **ADAPT** (determinize id; bind real provenance; keep upstream)
- ATAL — **DEFER** (orthogonal; must never decide truth)
- RIGOR — **ADAPT** (pre-admission evidence checks, non-authority)
- CIRCUIT — **REPLACE_WITH_FORMATIONCORE**
- GUARD — **REPLACE_WITH_FORMATIONCORE** (REVERSE/WATCH verbs deferred as policy layer)
- SERA — **KEEP** (primitive instrumentation)
- SessionGlyph — **ADAPT** (export concept; ContinuitySnapshot is stronger)
- core_runtime — **REPLACE_WITH_FORMATIONCORE** (authority spine; ADAPT for instrumentation wiring)

## 17. What must remain frozen

FormationCore `operational_self.py`, R-001 (`3782a16`), R8/R9/MARK/RESOLVE/CROSS_CONTEXT freezes, the ladder (`representations.py`/`oracle.py`/`generator.py`/`runner.py`), the allocator-continuity freeze package, migration receipts. Do **not** merge v4 into the baby-ai repo; do **not** rename or decompose FormationCore.

## 18. M2 readiness verdict

**READY_WITH_PRECONDITIONS.** R-001 is frozen; every persistence/authority component M2 needs is already frozen on the host. Preconditions: (a) define the exact corruption state (the M2 equivalent of `HOLD_CONTINUITY_FAILURE`) and a fail-closed provenance check; (b) keep the runner host-only and FormationCore-only (no v4 dependency); (c) confirm the "receipts ≠ provenance" lesson is encoded — missing authoritative provenance must fail closed.

## 19. Exact next action

Begin M2 as a minimal host-only runner using only FormationCore's `from_dict`, `ContinuitySnapshot`, `ReceiptLedger`, `ProvenanceLedger`, and `route_decision`, proving `X+H1→HOLD → persist→reload→HOLD → +E2→PROCEED → persist→reload→PROCEED` with the blocking event retained and provenance intact. (Do not execute now.)

## 20. Open questions

- Does any v4 subpackage (`mcva`, `natural_math`) contain behavior not yet audited that overlaps FormationCore authority? (Audited only at the spine level.)
- Was the v4 baseline ever byte-frozen/regen-verified, given its UUID/wall-clock non-determinism makes byte-reproducibility impossible as written?
- Is there any surviving Grok note that maps v4 `guard_decision` to a specific FormationCore precedence contract? (None found.)

---

**R-001 AUTHORITY:** `3782a166e3f30aee9a4d0f5bde73b8661d799cab`
**v4 STATUS:** RUNS (demos + replay test pass) but NON-DETERMINISTIC; demo runtime, not authority core
**STRONGEST v4 COMPONENT TO PRESERVE:** PERCEPT (upstream event→token boundary) — needs determinism + real provenance
**BIGGEST DUPLICATE-AUTHORITY RISK:** stateless GUARD PROCEED/HOLD vs stateful FormationCore route_decision
**M2 READINESS:** READY_WITH_PRECONDITIONS
**NEXT ACTION:** host-only M2 runner on FormationCore persistence components (no v4 dependency)
**DO NOT DO YET:** do not merge v4, do not rename FormationCore, do not implement evidence qualification or ReceptorEvents, do not touch the Motorola
