# R-001 FINAL DEVICE QUALIFICATION / CONTINUITY-INTEGRITY-002 — FINAL REPORT

Governing principle: **the host may verify what the phone produced; it may not
testify that the phone did something the host never observed.** The property under
qualification: a continuity-bearing system must acquire a future without rewriting
the identity of its past.

Run: 2026-08-21 (host). Evidence root:
`baby_ai/artifacts/repair/BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1/`

## A. Gate table (every defined gate, including G3)

| Gate | Purpose | Result |
|------|---------|--------|
| G1 | next_index > max(existing suffix) for all 7 families, incl. sparse/gapped histories | PASS |
| G2 | authoritative pre-repair state loads unchanged -> derived_legacy for all 7 families | PASS |
| G3 | pre-formation identity snapshot/hash of every inherited identity-bearing structure | PASS (baseline captured; self_id preserved) |
| G4 | >=10k records: zero dup IDs, zero overwritten inherited IDs, zero inherited mutation, monotonic streams | PASS |
| G5 | cold restart + form more; export -> clean import -> form more; inherited state re-compared | PASS |
| G6 | adversarial continuation matrix -> deterministic formation_blocked/HOLD (declared closed set) | PASS |
| G7 | prove deployed Motorola production _form path consumes + preserves allocator contract | HOLD / UNSATISFIED (BYPASS DISCOVERED) |
| G8 | manual operator counter handoff produces permanent migration receipts | PASS |

### G3 bookkeeping resolution

G3 was present in the manifest as evidence but absent from the pass/fail `gates`
dict in the prior run. It is not a boolean torture test: it produces the identity
baseline that G4/G5 `verify_inherited_unchanged` consume. Status now explicit:
PASS — aggregate hash `238dc2931edc8be8`; stable authority token `self_id`
(`oself-baby-mvp-A`) verified unchanged after formation. Coverage: all
allocator-managed collections, registries, receipts, provenance. Documented
exclusion: the evolving self-model `state` is not in the no-mutation hash (it
legitimately changes); only its stable `self_id` is identity-bearing and checked
separately. No gate was renumbered.

## B. G7 device evidence (read-only; nothing modified on device)

- Device: serial `ZY22HFN93K`, moto g stylus (2023), SKU `XT2317-2`, codename
  `gnevan`, Android 14, build `U1THS34.65-74-1-7-24`.
- Deployed build: `llc.bonacqui.aptd` `0.1.0-aptd` (versionCode 1), installed
  2026-08-17, updated 2026-08-18. APK SHA-256
  `4b1c590758e8e63ebc1f454d8063120c22ab2294a1bb5796c129985a1f07ddc1`.
  Runtime: Chaquopy embedded CPython 3.11; bundles the whole `baby_ai` package (.pyc).
- Production route (code-level trace): `ReceptorEvent -> aptd.intake/guard ->
  aptd_host_main._form -> FormationCore.make_event -> FormationCore.ingest ->
  persist(basin_core.json)`.

**Bypass discovered (not patched).** The on-device `operational_self.pyc` is a
PRE-R-001 build: it has `DeterministicIdStream`/`nid`/`counters` and the earlier
context/dependency/valid-window repairs, but ZERO allocator-continuation
identifiers (no `id_continuation`, `reconcile_allocator`, `ALLOCATOR_CONTRACT_VERSION`,
`ALLOCATOR_PREFIXES`, `derived_legacy`, `_formation_blocked`,
`apply_operator_allocator_override`, `allocator_family_ids`, `_derive_counters`).
Its `from_dict` never touches `ids`/`counters`; `to_dict` emits no `id_continuation`.
After every cold load the ID stream starts empty -> next ingest re-issues suffix 0
for every family. This is a reset-on-load allocator: exactly the bypass R-001 removes.

**Observed damage (real device state).** `basin_core.json` (167,062,057 bytes,
SHA-256 `ed9bccd8315fe40a69d15df4975f268d81775267cdf5b1b770961df2051edf8f`):

| Family | Objects | Distinct | Max suffix | Duplicate objects |
|--------|--------:|---------:|-----------:|------------------:|
| mem    | 90,073  | 90,073   | 90,072     | 0 (dict overwrite hides damage) |
| attr   | 90,073  | 90,073   | 90,072     | 0 (dict overwrite hides damage) |
| fog    | 100,395 | 90,073   | 90,072     | **10,322** |
| scar/lnk/replay | 0 | 0 | - | 0 |

`fog-0000/0001/0002` each appear 3x (all referencing mem-0000/1/2); 8,828 suffixes
appear 2x, 747 appear 3x. Duplicate suffixes are only possible from counter resets.
The append-only fog list witnesses the resets; mem/attr dicts silently overwrite.

Per the adversarial rule, the bypass stops the device positive-path qualification.
A repaired build must be deployed, existing state migrated with an operator receipt,
then device formation/restart/export re-run under observation.

## C. Host allocator table (qualified host path)

Starting next index = max(existing suffix) + 1 (never cardinality). G2 derived:
mem 2, attr 2, fog 2, scar 0, lnk 0, replay 0, evt 0.

| Family | Start | Consumed (G4) | Next after G4 | Consumed (G5 cold+import) | Dups | Overwrites | Mutation |
|--------|------:|--------------:|--------------:|--------------------------:|------|-----------:|----------|
| mem    | 2     | 10,000        | 10,002        | 50 + 50                   | 0    | 0          | none |
| attr   | 2     | 10,000        | 10,002        | 50 + 50                   | 0    | 0          | none |
| fog    | 2     | 9,000         | 9,002         | 45 + 45                   | 0    | 0          | none |
| scar   | 0     | 2,000         | 2,000         | 10 + 10                   | 0    | 0          | none |
| lnk    | 0     | 26,659        | 26,659        | 268 + 268                 | 0    | 0          | none |
| replay | 0     | 10            | 10            | 0 + 0                     | 0    | 0          | none |
| evt    | 0     | 10,000        | 10,000        | 50 + 50                   | 0    | 0          | none |

All seven streams monotonic; receipt chain valid throughout.

## D. Integrity

- G3 aggregate hash `238dc2931edc8be8`; G4 `zero_inherited_mutation=true`;
  G5 clean-import `mutations={}`; `self_id` preserved across formation and restart.
- Host receipt chain valid (G4 `receipt_chain_valid=true`).
- On-device receipt ledger: 302,073 entries, prev/hash chain valid, tip matches.
- On-device provenance ledger: EMPTY (`{"records": []}`) despite 167 MB formed state.

## E. Provenance observation

Host path: provenance ledger records reconcile/load evidence; receipt chain valid.
Device path: receipts ARE maintained (302,073 chained entries) but the provenance
ledger carries **zero** records. R-001 (identity continuity) is distinct from
R-002 (provenance-bearing continuity); R-001 passing does not imply R-002.

## F. Verdict

**R-001 = CANDIDATE / HOLD — host-adapter gates PASS; MOTOROLA device gate
UNSATISFIED (BYPASS DISCOVERED).**

Blocker: the deployed Motorola production formation path (`llc.bonacqui.aptd`
`0.1.0-aptd`) runs a pre-R-001 FormationCore that does not consume the
allocator-continuation contract; its allocator resets on every load, which has
already produced 10,322 duplicate family IDs in the device's persisted state.
Required: deploy a build containing the R-001 `id_continuation` contract, migrate
existing device state with an operator receipt, then re-run device
formation/restart/export under observation.

## G. R-002 handoff (bounded next-step specification)

- Exact current defect: device provenance ledger is empty (0 records) despite
  302,073 receipts and 167 MB formed state; the on-device formation path does not
  populate provenance.
- Affected structures: `baby_ai/core/provenance.py` (ProvenanceLedger),
  `llc/bonacqui/aptd/aptd_host_main.pyc` (`_load_ledgers`, `persist`,
  `EVENT_PROVENANCE_STATE`), the on-device formation/persist path.
- Minimum acceptance criteria: after device formation + restart + export, the
  provenance ledger contains >=1 record per formation source with
  component/organ/reuse_kind/path/sha256/modifications, and survives restart/export.
- Proposed sequence: (1) observational instrumentation of device formation to
  record provenance; (2) verify provenance persists across restart and export;
  (3) host verifier checks device provenance non-emptiness; (4) re-run G7.
- Risks: keep provenance changes additive/orthogonal to the already-qualified
  allocator path to avoid contaminating R-001.
