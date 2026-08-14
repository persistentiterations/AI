# COMPONENT STATUS — baby-AI assembly v0.1

Updated: 2026-08-14

Status legend:
- **QUALIFIED/FROZEN** — hash-anchored, self-consistent, independently reproducible qualification record exists.
- **CANDIDATE** — exists as executable artifact, integrity/qualification not yet fully verified.
- **HOLLOW** — declared PASS but artifact content is empty (0-2 bytes). Treat as failed/absent.
- **UNRESOLVED** — bounded search found no identifiable subsystem/project.

| Organ | Status | Verdict / Notes |
|---|---|---|
| CREP (learner + governance wrapper) | QUALIFIED/FROZEN | PASS_CREP_WRAPPER_V0_1; 40/40 unit tests; 2×5-fold WDBC anchored replays; byte-identical determinism; wrapper+freeze SHA-256 verified against sidecar and qualification record. Science claim-bounded/HOLD. NOT the whole baby. Bolt-On/SymLan/PIA/GUARD explicitly NOT integrated — do not retro-describe. |
| BABYAI_TEST_SUITE v1 | HOLLOW | `BABYSTATUS.TXT` claims PASSED 2026-08-14; all PASS files + `baby_ai_completion_run.py` are 0-2 bytes. Not corroborated. |
| MIMIC | UNRESOLVED / POSSIBLE NAME DRIFT | Bounded scan done: only prose uses of the word + 1 article filename + 1 index-key. No subsystem/codebase exists. Closed. |
| CONFIGURATOR (v1.2 SymLan Bridge) | QUALIFIED / RUNNING | Canonical hash `8ec454a5…`. Stdlib-only, 9/9 lanes PASS (A–I), deterministic (only wall-clock differs), self-test PASS, export/replay works. Needs PYTHONIOENCODING=utf-8 (cp1252-only defect). Lineage v0.6→v1.2 all compile/run. SymLan-package copy is a *different fork* (`390cfab0…`, 52539B) — not conflated. |
| BOLT-ON (v0.4) | QUALIFIED / FROZEN | 234/234 pytest PASS, byte-identical determinism. 10-stage governance chain, frozen release v0.4 exists (RC1 head `caede7dc…`). Continuity/authority infrastructure, not the baby. Must use pytest with PYTHONPATH=src. |
| FRACTALISH-AI (OLD / OPERATIONAL SELF) | QUALIFIED / RUNNING | Full `fractalish_ai` package: 113/113 pytest PASS; OperationalSelfEngine demo runs end-to-end (15 events → 15 memories, 2 scars, 6 fog, replay route, decay, 16 JSON artifacts). Formation machinery: compression→attractor→basin regions, contradiction scars, fog/HOLD, decay/purge, replay routes, keyword retrieval gating, self-state + narrative frame, SessionGlyph export/import/recovery (tested). RIGOR→GUARD→SERA→SessionGlyph control pipeline with false_continuity causal control. Effectively deterministic (only self-referential wall-clock state_hash differs). Project SHA-256 `584704b5…`. |
| baby-AI assembly v0.1 (integration) | ASSEMBLED / FREEZE `BABY_AI_CAUSAL_CORE_MVP_2026-08-14` | Head `edb5c73c…`; 17/17 pytest PASS; demo causal trace all-PASS; compileall PASS. **Gap A** (plasticity/corrigibility) CLOSED AT MVP MECHANISM LEVEL — causal chain: formed RELEASE → contradiction scar → HOLD → supersede → old scar ceases gating → RELEASE restored → prior state reconstructible. **Gap B** (second-host restore) CLOSED AT MVP MECHANISM LEVEL — strict clean-host cycle PASS (fresh interpreter, Host A terminated, only exported snapshot + code/schema travel; related RELEASE → ablate → HOLD → restore → RELEASE; snapshot restores complete Operational Self state + plasticity + receipts + provenance). **Gap C** (biography vs formed) OPEN — mechanism-scoped advantage measured in `transfer_control.py` (FORMED/FORMED_EXPORTED route RELEASE where equivalent words do not); stronger claim HELD, not generalized. See `TRUE_MISSING_INNOVATION` in manifest. |
| CNTM (+ Operator Dashboard) | QUALIFIED / RUNNING (superset tree) | CNT Morphology + evolution_prize_validation. Live tree `C:\Users\moop\FractalishBuild\fractalish-ai`: 227 passed / 1 suite-external failure (CNTM-supplied unreachable threshold in `test_visual_similarity…`, NOT qualified-baseline regression). cnt_morphology 10/10 PASS. Operator Dashboard v0.4 = **instrumentation, not cognition** (session store/review/playback; offline HTML fallback). **Gap verdict:** A scar-resolution executor NOT closed (no code writes resolved/superseded/`superseded_by` — detection only); B substrate-level snapshot export/import/reconstruct CLOSED (`_graph_from_dict`/`load_run_artifacts`/`save_final_state`/trace export) but operational_self graph import still MISSING; C comparison MECHANISM closed (`run_replay_probes` exact/noisy/perturbation/null/random/shuffled/cross-generator; `replay_signature` gradient) but biography/plain-text-transfer dimension still MISSING. See `TRUE_MISSING_INNOVATION` in manifest. |
| SYMLAN | NOT YET INVENTORIED | Priority 5. |
| R2R | NOT YET INVENTORIED | Priority 6. |
| APTD / MOTOROLA | NOT YET INVENTORIED | Priority 7 (inventory only). |
| ERACII / DUEL / KINETIC DUELLUM | NOT YET INVENTORIED | Priority 8. |
| PRISMML / BONSAI | NOT YET INVENTORIED | Priority 9. |
| NATURAL MATH | NOT YET INVENTORIED | Priority 10. |
