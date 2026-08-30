"""CONTINUITY-INTEGRITY-002 — R-001 CLOSURE RUN.

Executes the R-001 allocator-continuity gate suite against the candidate repair
(FormationCore id_continuation + reconcile_allocator). The candidate is treated
as not-yet-promoted: every gate writes evidence; nothing is inferred silently.

Run:  python -m baby_ai.qualifications.r001_closure

Evidence is written under
  <PACKAGE>/artifacts/repair/BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1/

Gate summary
  G1  next_index > max(existing suffix) for ALL seven families, incl. sparse
      IDs (0,1,42 -> resume at 43, never 3) and imported noncontiguous histories
      with deletions/gaps.
  G2  authoritative pre-repair state loaded UNCHANGED -> derived_legacy, exact
      derived allocator state recorded for all seven families as evidence.
  G3  pre-formation identity snapshot/hash of every inherited identity-bearing
      structure (memory, attractor, fog, scar, link, route, authority-bearing
      state, receipts, provenance, registries).
  G4  >=10,000 new records through the authoritative formation path: zero
      duplicate IDs, zero overwritten inherited IDs, zero inherited-object
      mutation, all seven streams monotonic, receipt chain valid.
  G5  cold restart + form more; export -> clean import + form more; inherited
      state re-compared after every stage.
  G6  adversarial continuation payload matrix: every unsafe case must yield
      deterministic formation_blocked/HOLD — never silent repair.
  G7  MOTOROLA device route inventory (IS THE DEVICE CONSULTING THIS CONTRACT?).
  G8  manual operator counter handoffs produce PERMANENT migration receipts.

Every stage is deterministic; the report is reproducible by rerunning this file.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from baby_ai import domain as D
from baby_ai._env import PACKAGE
from baby_ai.adapters.operational_self import (
    ALLOCATOR_PREFIXES,
    ALLOCATOR_INDEX_HEADROOM,
    FormationCore,
)
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.migration_receipts import MigrationReceiptLedger
from baby_ai.core.receipts import ReceiptLedger
from baby_ai.core.semantics import canonical_json, semantic_digest

OUT_DIR = PACKAGE / "artifacts" / "repair" / "BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1"

PRE_REPAIR_SNAPSHOT = PACKAGE / "artifacts" / "snapshot_host_A.json"

ITEMS = ["flux_alpha", "flux_beta", "dura_gamma"]

# G6 — DECLARED CLOSED SET of deterministic HOLD reasons an adversarial (allocator-
# rejected) load may legitimately surface. This is a strict allow-list, NOT
# "any HOLD is acceptable": a future, unrelated HOLD reason must NOT inherit
# legitimacy here without being explicitly added to this set.
#   EVIDENCE                      -> would-be RELEASE downgraded by the allocator block
#   contradiction_scar_blocking   -> route already held independently on a formed scar
ALLOWED_ADVERSARIAL_HOLD_REASONS = frozenset({"EVIDENCE", "contradiction_scar_blocking"})

# -------------------------------------------------------------------- helpers


def _id_suffix(family: str, raw: str) -> int:
    """Numeric suffix of a family id (handles both - and _ separators)."""
    for sep in ("-", "_"):
        marker = family + sep
        if marker in raw:
            return int(raw.split(marker, 1)[1])
    raise ValueError(f"id {raw!r} carries no {family} suffix")


def _strip_continuation(payload: dict) -> dict:
    out = dict(payload)
    out.pop("id_continuation", None)
    return out


def sparse_fixture(source_payload: dict, family: str, ids: list[str]) -> dict:
    """Take a formed payload and return a legacy payload (no id_continuation)
    whose `family` contains objects with EXACTLY the given id suffixes,
    leaving all other families empty. Used to prove next_index resumes above
    max(existing suffix) and never equals cardinality."""
    import copy

    p = copy.deepcopy(source_payload)
    p.pop("id_continuation", None)
    empty_collections = {
        "memories": {}, "attractors": {}, "fog": [], "scars": [], "links": [], "routes": [],
    }
    for k in ("mem_contexts", "mem_tuples", "scar_contexts", "scar_kinds"):
        empty_collections.setdefault(k, {})
    for key in empty_collections:
        p[key] = empty_collections[key]
    p["dependencies"] = {}
    p["dependency_ledger"] = []
    p["valid_windows"] = {}

    if family == "mem":
        assert "memories" in p and "attractors" in p
        p["memories"] = {f"mem-{i:04d}": src for i, src in zip(ids, source_payload["memories"].values())}
        p["attractors"] = {f"attr_{i:04d}": src for i, src in zip(ids, source_payload["attractors"].values())}
        for i in ids:
            p["memories"][f"mem-{i:04d}"]["memory_id"] = f"mem-{i:04d}"
            p["attractors"][f"attr_{i:04d}"]["memory_id"] = f"mem-{i:04d}"
            p["attractors"][f"attr_{i:04d}"]["attractor_id"] = f"attr_{i:04d}"
    elif family == "attr":
        p["attractors"] = {f"attr_{i:04d}": src for i, src in zip(ids, source_payload["attractors"].values())}
        for i in ids:
            p["attractors"][f"attr_{i:04d}"]["attractor_id"] = f"attr_{i:04d}"
    elif family == "fog":
        p["fog"] = [dict(o) for i, o in zip(ids, source_payload["fog"])]
        for i, o in zip(ids, p["fog"]):
            o["fog_id"] = f"fog-{i:04d}"
    elif family == "scar":
        p["scars"] = [dict(o) for i, o in zip(ids, source_payload["scars"])]
        for i, o in zip(ids, p["scars"]):
            o["scar_id"] = f"scar-{i:04d}"
    elif family == "lnk":
        p["links"] = [dict(o) for i, o in zip(ids, source_payload["links"])]
        for i, o in zip(ids, p["links"]):
            o["link_id"] = f"lnk-{i:04d}"
    elif family == "replay":
        p["routes"] = [dict(o) for i, o in zip(ids, source_payload["routes"])]
        for i, o in zip(ids, p["routes"]):
            o["route_id"] = f"replay-{i:04d}"
    elif family == "evt":
        pass  # evt has no persistent collection; its floor derives to 0
    else:
        raise ValueError(family)
    # drop objects with nonexistent referents so the fixture is loadable
    p["links"] = [] if family != "lnk" else p["links"]
    p["scars"] = [] if family != "scar" else p["scars"]
    p["routes"] = [] if family != "replay" else p["routes"]
    p["fog"] = [] if family != "fog" else p["fog"]
    p["attractors"] = {} if family != "attr" else p["attractors"]
    return p


def family_id_map(opself: dict, family: str) -> list[str]:
    """Present id strings for a family in a serialized payload."""
    if family == "mem":
        return list(opself.get("memories", {}))
    if family == "attr":
        return list(opself.get("attractors", {}))
    if family == "fog":
        return [o["fog_id"] for o in opself.get("fog", [])]
    if family == "scar":
        return [o["scar_id"] for o in opself.get("scars", [])]
    if family == "lnk":
        return [o["link_id"] for o in opself.get("links", [])]
    if family == "replay":
        return [o["route_id"] for o in opself.get("routes", [])]
    if family == "evt":
        return []
    raise ValueError(family)


def identity_snapshot(opself: dict, receipts: dict, provenance: dict) -> dict:
    """Hash every inherited identity-bearing structure. Keys are stable so a
    later stage can verify ZERO mutation of inherited objects; appends (new
    memories, new receipts, new provenance rows) are additions, not mutations,
    and are separately counted."""
    snap: dict = {"family_content": {}, "registries": {}, "receipts": {}, "provenance": {}}
    for fid, obj in opself.get("memories", {}).items():
        snap["family_content"].setdefault("mem", {})[fid] = semantic_digest(obj)
    for fid, obj in opself.get("attractors", {}).items():
        snap["family_content"].setdefault("attr", {})[fid] = semantic_digest(obj)
    for fam_col, fam in (("fog", "fog"), ("scars", "scar"), ("links", "lnk"), ("routes", "replay")):
        for obj in opself.get(fam_col, []):
            snap["family_content"].setdefault(fam, {})[f"{obj.get('fog_id' if fam == 'fog' else (obj.get('scar_id') if fam == 'scar' else (obj.get('link_id') if fam == 'lnk' else obj.get('route_id'))))}"] = semantic_digest(obj)
    for key in ("mem_contexts", "mem_tuples", "scar_contexts", "scar_kinds"):
        snap["registries"][key] = {k: semantic_digest(v) for k, v in opself.get(key, {}).items()}
    snap["registries"]["dependencies"] = {k: semantic_digest(v) for k, v in opself.get("dependencies", {}).items()}
    snap["registries"]["dependency_ledger"] = [semantic_digest(r) for r in opself.get("dependency_ledger", [])]
    snap["registries"]["valid_windows"] = {semantic_digest(k): semantic_digest(v) for k, v in opself.get("valid_windows", {}).items()}
    snap["receipts"]["entries"] = semantic_digest(receipts.get("entries", []))
    snap["receipts"]["tip"] = receipts.get("tip")
    snap["provenance"]["records"] = [semantic_digest(r) for r in provenance.get("records", [])]
    snap["aggregate"] = semantic_digest({
        "family_content": snap["family_content"],
        "registries": snap["registries"],
        "receipts_entries": snap["receipts"]["entries"],
        "provenance_record_count": len(provenance.get("records", [])),
    })
    return snap


def verify_inherited_unchanged(baseline: dict, opself: dict, receipts: dict, provenance: dict,
                               *, allow_appended: bool = True) -> dict:
    """Return {ok, mutations, appends} comparing a later state to the baseline
    identity snapshot taken before formation."""
    now = identity_snapshot(opself, receipts, provenance)
    mutations: dict[str, list] = {}
    appends: dict[str, int] = {}
    for fam, initial in baseline["family_content"].items():
        for _id, h in initial.items():
            current = now["family_content"].get(fam, {}).get(_id)
            if current != h:
                mutations.setdefault(fam, []).append(_id)
        if allow_appended and fam in now["family_content"]:
            appends[fam] = len(now["family_content"][fam]) - len(initial)
    for reg in ("mem_contexts", "mem_tuples", "scar_contexts", "scar_kinds", "dependencies"):
        base_keys = set(baseline["registries"].get(reg, {}))
        for k in base_keys:
            if baseline["registries"].get(reg, {}).get(k) != now["registries"].get(reg, {}).get(k):
                mutations.setdefault("registries", []).append(f"{reg}:{k}")
        if allow_appended:
            appends[reg] = len(now["registries"].get(reg, {})) - len(base_keys)
    for reg in ("dependency_ledger", "valid_windows"):
        if baseline["registries"].get(reg) != now["registries"].get(reg):
            # append-only: inherited prefix must be preserved
            base = baseline["registries"].get(reg, []) if isinstance(baseline["registries"].get(reg), list) else baseline["registries"].get(reg, {})
            cur = now["registries"].get(reg, []) if isinstance(now["registries"].get(reg), list) else now["registries"].get(reg, {})
            base_slice = base[: len(now["registries"].get(reg, []))] if isinstance(base, list) else {k: base.get(k) for k in base}
            if (isinstance(base, list) and cur[: len(base)] != base) or (
                not isinstance(base, list) and any(base.get(k) != cur.get(k) for k in base)
            ):
                mutations.setdefault("registries", []).append(reg)
            if allow_appended:
                appends[reg] = (len(cur) - len(base)) if isinstance(base, list) else (len(cur) - len(base))
    if baseline["receipts"]["entries"] != now["receipts"]["entries"]:
        # receipt ledger is append-only: prefix must be preserved
        base_len = baseline.get("_receipt_count", 0)
        cur_entries = receipts.get("entries", [])
        ok_prefix = True
        if base_len > 0:
            for old_e, new_e in zip(baseline["_receipt_entries"], cur_entries[: len(baseline["_receipt_entries"])]):
                ok_prefix = ok_prefix and old_e == new_e
        if not ok_prefix:
            mutations.setdefault("receipts", []).append("prefix changed")
        appends["receipts"] = max(0, len(cur_entries) - base_len)
    # provenance: allow appended rows; forbid edits to inherited rows
    base_prov = baseline["provenance"]["records"]
    cur_prov = [semantic_digest(r) for r in provenance.get("records", [])]
    if cur_prov[: len(base_prov)] != base_prov:
        mutations.setdefault("provenance", []).append("inherited record changed")
    appends["provenance"] = max(0, len(cur_prov) - len(base_prov))
    return {"ok": not mutations, "mutations": mutations, "appends": appends}


# --------------------------------------------------------------------- gates

def gate1(sparse_template: dict) -> dict:
    """next_index > max(existing suffix) for all 7 families; sparse 0,1,42 -> 43."""
    results: dict = {}
    all_ok = True
    for family in ALLOCATOR_PREFIXES:
        if family == "evt":
            # transient family: no persistent collection, floor derives to 0
            payload = _strip_continuation(sparse_template)
            core = FormationCore.from_dict(payload, activation_id="r1-ev0")
            floor = core.ids.counters["evt"]
            results[family] = {"floor": floor, "present_suffixes": [], "resume_at_ge_max": True}
            all_ok = all_ok and floor == 0
            continue
        ids = [0, 1, 42]
        fixture = sparse_fixture(sparse_template, family, ids)
        core = FormationCore.from_dict(fixture, activation_id=f"r1-{family}")
        ready = core.formation_ready()
        kind = core.allocator_status["kind"]
        floor = core.ids.counters[family]
        present = sorted(_id_suffix(family, i) for i in family_id_map(fixture, family))
        resume_beyond = floor == 43 and all(floor > s for s in present)
        never_cardinality = floor != len(present)
        ok = ready and kind == "derived_legacy" and resume_beyond and never_cardinality
        results[family] = {
            "floor": floor, "present_suffixes(sample)": present, "resume_at_43": resume_beyond,
            "never_equaled_cardinality": never_cardinality, "derived_legacy": kind == "derived_legacy", "ok": ok,
        }
        all_ok = all_ok and ok
    return {"ok": all_ok, "families": results}


def gate2(source_payload: dict, source_hash: str) -> dict:
    """Load authoritative pre-repair state unchanged -> derived_legacy + exact counters."""
    loaded = FormationCore.from_dict(dict(source_payload), activation_id="r1-transfer001")
    derived = dict(loaded.ids.counters)
    evidence = {
        "source_file": str(PRE_REPAIR_SNAPSHOT),
        "source_sha256": source_hash,
        "was_modified_before_load": False,
        "id_continuation_present": "id_continuation" in source_payload,
        "allocator_status": loaded.allocator_status,
        "derived_counters_all_seven": {f: derived.get(f, 0) for f in ALLOCATOR_PREFIXES},
        "formation_ready": loaded.formation_ready(),
        "route_flux_alpha": loaded.route_decision("flux_alpha")["decision"],
        "counts": loaded.counts(),
    }
    evidence["ok"] = (
        (not evidence["id_continuation_present"])
        and loaded.allocator_status["kind"] == "derived_legacy"
        and evidence["formation_ready"]
        and evidence["route_flux_alpha"] == "RELEASE"
    )
    return evidence


def gate4(baseline: dict, core: FormationCore, n: int) -> dict:
    """Form n records through the authoritative ingest path; audit streams."""
    inherited_ids = {}
    for fam in ALLOCATOR_PREFIXES:
        inherited_ids[fam] = set(core.allocator_family_ids(fam))
    start_floor = dict(core.ids.counters)  # derived floor established at load

    allocs: dict[str, list[int]] = {f: [] for f in ALLOCATOR_PREFIXES}
    dups: dict[str, list[int]] = {f: [] for f in ALLOCATOR_PREFIXES}
    overwrites: list[str] = []

    def watch(family: str, fid: str, inherited: set):
        idx = _id_suffix(family, fid)
        if fid in inherited:
            overwrites.append(fid)
        allocs[family].append(idx)
        if len({str(a) for a in allocs[family]}) != len(allocs[family]):
            dups[family].append(idx)

    t0 = time.perf_counter()
    for i in range(n):
        item = ITEMS[i % len(ITEMS)]
        tag = D.ITEMS[item]["tags"][0]
        # every 1000th record is a tagged "build" event so lnk + replay streams
        # keep advancing; everything else stays cheap (no tag in claims => no
        # per-ingest full-memory link scan).
        if i % 1000 == 500:
            ev = core.make_event(
                raw_summary=f"{item} build clearance obtained.",
                structured_summary=f"build clearance obtained for {item}",
                claims=[item, tag, "safe_for_release"],
                decisions=["RELEASE"],
                tags=D.ITEMS[item]["tags"],
                guard_status="WATCH", importance_hint=0.7, confidence=0.8, uncertainty=0.2,
                provenance_extra={"domain": "warehouse", "kind": "clearance"},
            )
        elif i % 10 >= 8:
            ev = core.make_event(
                raw_summary=f"{item} is NOT safe. Similarity is not identity.",
                structured_summary=f"contradiction notice for {item}",
                claims=[f"{item} is unsafe", "similarity is not identity", item],
                decisions=["HOLD"],
                tags=D.ITEMS[item]["tags"] + ["contradiction"],
                guard_status="HOLD", importance_hint=0.9, confidence=0.9, uncertainty=0.1,
                provenance_extra={"domain": "warehouse", "kind": "contradiction"},
            )
        elif i % 10 == 7:
            ev = core.make_event(
                raw_summary=f"{item} clearance re-verified under guard with new evidence.",
                structured_summary=f"superseding evidence for {item}",
                claims=[f"{item} is safe", "governed_release_verified", item],
                decisions=["RELEASE_WITH_GUARD"],
                tags=D.ITEMS[item]["tags"],
                guard_status="WATCH", importance_hint=0.8, confidence=0.95, uncertainty=0.05,
                provenance_extra={"domain": "warehouse", "kind": "resolve"},
            )
        else:
            ev = core.make_event(
                raw_summary=f"{item} clearance obtained.",
                structured_summary=f"clearance obtained for {item}",
                claims=[f"{item} is safe", "safe_for_release"],
                decisions=["RELEASE"],
                tags=D.ITEMS[item]["tags"],
                guard_status="WATCH", importance_hint=0.7, confidence=0.8, uncertainty=0.2,
                provenance_extra={"domain": "warehouse", "kind": "clearance"},
            )
        pre_links = len(core.links)
        pre_routes = len(core.routes)
        res = core.ingest(ev)
        assert res.get("error") != "formation_blocked", f"blocked midway: {res}"
        watch("evt", res["event_id"], inherited_ids["evt"])
        watch("mem", res["memory_id"], inherited_ids["mem"])
        watch("attr", res["attractor_id"], inherited_ids["attr"])
        for sid in res.get("scar_ids", []):
            watch("scar", sid, inherited_ids["scar"])
        if res.get("fog_id"):
            watch("fog", res["fog_id"], inherited_ids["fog"])
        for lnk in core.links[pre_links:]:
            watch("lnk", lnk.link_id, inherited_ids["lnk"])
        for rte in core.routes[pre_routes:]:
            watch("replay", rte.route_id, inherited_ids["replay"])
    elapsed = time.perf_counter() - t0

    monotonic = {f: all(a < b for a, b in zip(s, s[1:])) if s else True for f, s in allocs.items()}
    no_dups = all(not v for v in dups.values())
    no_overwrite = not overwrites
    streams_ok = {
        f: core.ids.counters[f] == start_floor.get(f, 0) + len(set(allocs[f]))
        for f in ALLOCATOR_PREFIXES
    }

    inherited_check = verify_inherited_unchanged(baseline, core.to_dict(), core.receipts.to_dict(), core.provenance.to_dict())
    chain_ok, chain_msg = core.receipts.verify_chain()
    return {
        "formed_records": n,
        "elapsed_sec": round(elapsed, 3),
        "per_record_sec": round(elapsed / n, 6),
        "allocations_per_family": {f: len(s) for f, s in allocs.items()},
        "streams_strictly_monotonic": monotonic,
        "no_duplicate_ids": no_dups,
        "duplicates": {f: v[:10] for f, v in dups.items() if v},
        "no_overwritten_inherited_ids": no_overwrite,
        "zero_inherited_mutation": inherited_check["ok"],
        "mutations": inherited_check["mutations"],
        "appended_records": inherited_check["appends"],
        "streams_advanced_exactly": streams_ok,
        "counters_after": dict(core.ids.counters),
        "receipt_chain_valid": chain_ok,
        "receipt_chain_msg": chain_msg,
        "ok": no_dups and no_overwrite and inherited_check["ok"] and all(monotonic.values())
              and all(streams_ok.values()) and chain_ok,
    }


def gate5_stage(core: FormationCore, baseline: dict, label: str, extra: int) -> dict:
    """Form `extra` more records, then re-verify inherited objects are intact."""
    out = gate4(baseline, core, extra)
    out["label"] = label
    return out


# ------------------------------------------------------------------ harness
def _load_authoritative() -> tuple[Any, dict, str]:
    """Load the pre-repair snapshot file WITHOUT modification; capture its hash."""
    raw = PRE_REPAIR_SNAPSHOT.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    snap = ContinuitySnapshot.read(PRE_REPAIR_SNAPSHOT)
    return snap, snap.operational_self, sha


def adversarial_cases(payload: dict) -> dict:
    """8 targeted unsafe payloads -> every one must yield formation_blocked/HOLD."""
    base = dict(payload)
    floor = 0
    for k in base["id_continuation"]["counters"]:
        pass
    counters = dict(base["id_continuation"]["counters"])
    floor_mem = 1  # reference floor recomputed by the loader; we base mutations on a formed core
    cases = {}
    # 1 stale persisted next index (mem counter below its derived floor)
    c = dict(counters); c["mem"] = counters.get("mem", 0) - 1
    cases["stale_persisted_next_index"] = c
    # 2 next index equal to an occupied id (mem counter == floor-1 => collides with last id)
    c = dict(counters); c["mem"] = counters.get("mem", 0) - 1
    cases["next_index_equals_occupied_id"] = c
    # 3 partial block (one family missing)
    c = dict(counters); c.pop("evt", None)
    cases["partial_continuation_block"] = c
    # 4 malformed family (bool is not an index)
    c = dict(counters); c["fog"] = True
    cases["malformed_family"] = c
    # 5 missing family entirely
    c = {k: v for k, v in counters.items() if k != "scar"}
    cases["missing_family"] = c
    # 6 negative index
    c = dict(counters); c["lnk"] = -7
    cases["negative_index"] = c
    # 7 nonsensical/overflow value far beyond floor + headroom
    c = dict(counters); c["replay"] = counters.get("replay", 0) + ALLOCATOR_INDEX_HEADROOM + 1_000_000
    cases["overflow_nonsensical_value"] = c
    # 8 explicit counter below derived legacy floor
    c = dict(counters); c["mem"] = 0
    cases["explicit_below_derived_floor"] = c
    return cases


def run_adversarial_gate(payload: dict) -> dict:
    results = {}
    all_ok = True
    for label, counters in adversarial_cases(payload).items():
        p = dict(payload)
        p["id_continuation"] = {"version": "v0.1", "counters": counters}
        core = FormationCore.from_dict(p, activation_id=f"adv-{label}")
        # snapshot allocator state immediately after the load boundary: a reject
        # must leave the counter stream untouched ({}). Measuring after the probe
        # event below would conflate one evt id consumed by OUR make_event call.
        counters_after_load = dict(core.ids.counters)
        route = core.route_decision("flux_alpha")
        ingest = core.ingest(D.experience_safe(core, "flux_alpha"))
        # Deterministic HOLD required: either the would-be RELEASE was downgraded
        # to EVIDENCE, or the route held independently (e.g. scar-blocking). In
        # every blocked reply the allocator status is attached, so an operator
        # always sees the rejection reason next to what the route would have done.
        safe = (
            (not core.formation_ready())
            and core.allocator_status["kind"] == "FAIL"
            and route["decision"] == "HOLD"
            and "allocator" in route
            and route.get("reason") in ALLOWED_ADVERSARIAL_HOLD_REASONS
            and ingest.get("error") == "formation_blocked"
            and ingest["decision"] == "HOLD"
            and counters_after_load == {}  # never silently repaired
        )
        results[label] = {
            "formation_blocked": not core.formation_ready(),
            "kind": core.allocator_status["kind"],
            "reason": core.allocator_status["reason"],
            "route_decision": route["decision"],
            "route_reason": route.get("reason"),
            "route_reason_in_closed_set": route.get("reason") in ALLOWED_ADVERSARIAL_HOLD_REASONS,
            "ingest_error": ingest.get("error"),
            "counters_left_untouched": counters_after_load == {},
            "downgraded_to_evidence": route.get("reason") == "EVIDENCE",
            "allocator_attached": "allocator" in route,
            "ok": safe,
        }
        all_ok = all_ok and safe
    return {
        "ok": all_ok,
        "allowed_hold_reasons_closed_set": sorted(ALLOWED_ADVERSARIAL_HOLD_REASONS),
        "cases": results,
    }


def gate8_operator_override(core: FormationCore, receipt_dir: Path) -> dict:
    """Manual operator counter handoff must produce a PERMANENT migration receipt."""
    ledger = MigrationReceiptLedger(receipt_dir)
    pre_count = len(ledger.read_all())
    floor = core._derive_counters()["mem"]
    core.apply_operator_allocator_override(
        "mem", floor + 500_000,
        reason="collapsed legacy batch: appended id range was purged before export "
               "(collections can no longer prove those suffixes); derived floor would reissue them",
        ledger_root=receipt_dir,
    )
    receipts = ledger.read_all()
    fresh = receipts[pre_count:]
    ok = bool(fresh) and all(
        {"pre_migration_state_hash", "derived_allocator_floor", "operator_value",
         "reason_derived_value_insufficient", "post_migration_state_hash"} <= set(r)
        for r in fresh
    )
    ok = ok and fresh[-1]["derived_allocator_floor"] == floor
    ok = ok and fresh[-1]["operator_value"] == floor + 500_000
    ok = ok and fresh[-1]["pre_migration_state_hash"] != fresh[-1]["post_migration_state_hash"]
    verify_ok, verify_msg = ledger.verify()
    # below-floor override must be refused
    refused = False
    try:
        core.apply_operator_allocator_override(
            "mem", floor - 1, reason="attempt to lower floor", ledger_root=receipt_dir)
    except ValueError:
        refused = True
    return {
        "ok": ok and verify_ok and refused,
        "receipts_written": fresh,
        "receipt_file": str(ledger.path),
        "ledger_verify": verify_msg,
        "below_floor_refused": refused,
    }


def main() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    snap, opself, snap_sha = _load_authoritative()
    report: dict = {
        "title": "CONTINUITY-INTEGRITY-002 — R-001 CLOSURE RUN",
        "candidate": "allocator-continuity repair (NOT YET PROMOTED)",
        "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version.split()[0],
        "package": str(PACKAGE),
        "gate1_next_index_semantics": None,
        "gate2_pre_repair_load": None,
        "gate3_identity_baseline": None,
        "gate4_mass_formation": None,
        "gate5_cold_restart_export_import": {},
        "gate6_adversarial": None,
        "gate7_motorola_device_route": None,
        "gate8_migration_receipts": None,
        "verdict": None,
    }

    # ---- G1 (needs a sparse template; build one by forming through the real path)
    seed = FormationCore(activation_id="r1-seed")
    for item in ITEMS:
        tag = D.ITEMS[item]["tags"][0]
        safe = seed.make_event(
            raw_summary=f"{item} build clearance obtained.",
            structured_summary=f"build clearance obtained for {item}",
            claims=[item, tag, "safe_for_release"],
            decisions=["RELEASE"],
            tags=D.ITEMS[item]["tags"], guard_status="WATCH", importance_hint=0.7,
            confidence=0.8, uncertainty=0.2, provenance_extra={"domain": "warehouse", "kind": "clearance"},
        )
        seed.ingest(safe)
        seed.ingest(D.experience_contradiction(seed, item))
        seed.ingest(D.experience_resolving(seed, item))
    report["gate1_next_index_semantics"] = gate1(seed.to_dict())

    # ---- G2 authoritative pre-repair load (unchanged file)
    report["gate2_pre_repair_load"] = gate2(opself, snap_sha)

    # ---- G3 identity baseline over the (legacy-loaded) inherited state
    legacy_core = FormationCore.from_dict(dict(opself), activation_id="r1-transfer001")
    baseline = identity_snapshot(
        legacy_core.to_dict(),
        legacy_core.receipts.to_dict(),
        legacy_core.provenance.to_dict(),
    )
    baseline["_receipt_entries"] = list(legacy_core.receipts.entries)
    baseline["_receipt_count"] = len(legacy_core.receipts.entries)
    _self_id_at_baseline = legacy_core.state.self_id
    report["gate3_identity_baseline"] = {
        "films": baseline,
        "inherited_records_by_family": {
            f: len(family_id_map(legacy_core.to_dict(), f)) for f in ALLOCATOR_PREFIXES
        },
        "aggregate_hash": baseline["aggregate"],
        "authority_self_id_at_baseline": _self_id_at_baseline,
        "documented_exclusions": [
            "state (OperationalSelfState) is the evolving self-model and is intentionally "
            "NOT in the no-mutation hash; its stable identity token (self_id) is captured "
            "separately and checked for preservation after formation."
        ],
    }

    # ---- G4 mass formation through the authoritative path
    report["gate4_mass_formation"] = gate4(baseline, legacy_core, 10_000)

    # ---- G5 cold restart (subprocess) then export -> clean import
    snap2 = ContinuitySnapshot()
    snap2.pack(
        operational_self=legacy_core.to_dict(),
        plasticity={},
        receipts=legacy_core.receipts.to_dict(),
        provenance=legacy_core.provenance.to_dict(),
        domain={"junk": "none"},
    )
    cold_fixture_path = OUT_DIR / "cold_restart_input.snapshot.json"
    cold_result_path = OUT_DIR / "cold_restart_result.json"
    cold_script = OUT_DIR / "_cold_restart_worker.py"
    _parent, _fixture, _result = str(PACKAGE.parent), str(cold_fixture_path), str(cold_result_path)
    cold_script.write_text(
        f"""import sys, json
sys.path.insert(0, r"{_parent}")
from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.receipts import ReceiptLedger
from baby_ai.core.provenance import ProvenanceLedger
from baby_ai import domain as D
s=ContinuitySnapshot.read(r"{_fixture}")
rcpts=ReceiptLedger.from_dict(s.receipts)
prov=ProvenanceLedger.from_dict(s.provenance, rcpts)
c=FormationCore.from_dict(s.operational_self, activation_id='r1-cold',
                          receipts=rcpts, provenance=prov)
out={{'ready': c.formation_ready(), 'status': c.allocator_status,
      'route': c.route_decision('flux_alpha')['decision'],
      'receipt_count': len(c.receipts.entries),
      'prov_count': len(c.provenance.records)}}
for i in range(50):
    c.ingest(D.experience_safe(c, ('flux_alpha' if i%3==0 else ('flux_beta' if i%3==1 else 'dura_gamma'))))
out['counts_after']=c.counts(); out['ids']=dict(c.ids.counters)
out['ok']=out['ready'] and out['receipt_count']>0 and out['prov_count']>0 and out['ids']['mem']>0
open(r"{_result}","w").write(json.dumps(out, sort_keys=True, default=str))
""",
        encoding="utf-8",
    )
    cold_fixture_path.write_text(canonical_json(snap2.to_dict()), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(cold_script)],
        capture_output=True, text=True, timeout=600, cwd=str(PACKAGE),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cold restart worker failed rc={proc.returncode}: {proc.stderr[-2000:]}")
    cold_result = json.loads(cold_result_path.read_text(encoding="utf-8"))
    cold_ok = bool(cold_result.get("ok"))
    reimport = {
        **gate5_stage(legacy_core, baseline, "post-mass", 50),
        "cold_restart": cold_ok,
        "cold_restart_status": cold_result["status"],
    }
    # export -> clean import (carry the inherited ledgers, do not start blank)
    from baby_ai.core.receipts import ReceiptLedger as _ReceiptLedger
    from baby_ai.core.provenance import ProvenanceLedger as _ProvenanceLedger
    _rcpts = _ReceiptLedger.from_dict(legacy_core.receipts.to_dict())
    _prov = _ProvenanceLedger.from_dict(legacy_core.provenance.to_dict(), _rcpts)
    fresh = FormationCore.from_dict(legacy_core.to_dict(), activation_id="r1-reimport",
                                    receipts=_rcpts, provenance=_prov)
    reimport["clean_import"] = gate5_stage(fresh, baseline, "post-clean-import", 50)
    report["gate5_cold_restart_export_import"] = reimport

    # ---- G6 adversarial matrix
    adversarial_payload = legacy_core.to_dict()
    report["gate6_adversarial"] = run_adversarial_gate(adversarial_payload)

    # ---- G7 Motorola device route: host inventory + read-only device investigation
    motorola = _inventory_motorola()
    g7_device = _load_g7_device_investigation()
    motorola["device_investigation"] = g7_device
    if g7_device:
        finding = g7_device.get("finding")
        if finding == "BYPASS_DISCOVERED":
            motorola["verdict"] = "UNSATISFIED_BYPASS_DISCOVERED"
            motorola["device_blocker"] = g7_device.get("blocker")
            motorola["device_summary"] = {
                "package": g7_device["deployed_build"]["package"],
                "versionName": g7_device["deployed_build"]["versionName"],
                "apk_sha256": g7_device["deployed_build"]["apk_sha256"],
                "contract_present_on_device": g7_device["contract_scan_on_device"]["contract_present"],
                "from_dict_restores_counters": g7_device["contract_scan_on_device"]["from_dict_touches_ids_or_counters"],
                "duplicate_family_ids_observed": g7_device["collision_evidence"]["total_duplicate_family_objects"],
                "provenance_record_count_on_device": g7_device["provenance_observation"]["provenance_record_count"],
            }
    report["gate7_motorola_device_route"] = motorola

    # ---- G8 migration receipts
    mig_core = FormationCore.from_dict(legacy_core.to_dict(), activation_id="r1-mig")
    report["gate8_migration_receipts"] = gate8_operator_override(mig_core, OUT_DIR / "migration_receipts")

    # ---- G3 authority-token preservation (self_id) after formation/restart
    g3_self_id_preserved = legacy_core.state.self_id == _self_id_at_baseline
    report["gate3_identity_baseline"]["authority_self_id_preserved_after_formation"] = g3_self_id_preserved

    # ---- verdict
    g1 = report["gate1_next_index_semantics"]["ok"]
    g2 = report["gate2_pre_repair_load"]["ok"]
    g3 = bool(baseline["aggregate"]) and g3_self_id_preserved
    g4 = report["gate4_mass_formation"]["ok"]
    g5 = reimport["ok"] and reimport["clean_import"]["ok"] and cold_ok
    g6 = report["gate6_adversarial"]["ok"]
    g7 = motorola["verdict"] == "SATISFIED"
    g8 = report["gate8_migration_receipts"]["ok"]
    gates = {"gate1_next_index_semantics": g1, "gate2_pre_repair_load": g2,
             "gate3_identity_baseline": g3, "gate4_mass_formation": g4,
             "gate5_cold_restart_export_import": g5, "gate6_adversarial": g6,
             "gate7_motorola_device_route": g7, "gate8_migration_receipts": g8}
    report["gates"] = gates

    g7_blocker = motorola.get("device_blocker") or (
        "No deployable Motorola `_form` route is present or inventoried on this machine; "
        "device-layer consumption of the id_continuation contract cannot be asserted."
    )
    report["verdict"] = {
        "host_adapter_layer": all(x for k, x in gates.items() if k != "gate7_motorola_device_route"),
        "device_layer": g7,
        "r001_frozen": g7 and all(gates.values()),
        "freeze_label": ("R-001 = CLOSED — APPEND_ONLY_IDENTITY_CONTINUATION_QUALIFIED"
                         if (g7 and all(gates.values())) else
                         "R-001 = CANDIDATE / HOLD — host-adapter gates PASS; MOTOROLA device gate UNSATISFIED"),
        "g7_blocker": g7_blocker,
        "notes": [
            "The host may verify what the phone produced. It may not testify that the phone "
            "did something the host never observed.",
            "A physical Motorola device (ZY22HFN93K) IS reachable via adb; the deployed "
            "llc.bonacqui.aptd build was inspected read-only (see G7_DEVICE_INVESTIGATION.json).",
            "The deployed production path (aptd_host_main._form -> FormationCore.ingest) runs a "
            "PRE-R-001 FormationCore lacking the allocator-continuation contract; its allocator "
            "resets on every load, and this has already produced duplicate family IDs on the device.",
            "Device safety is NOT inferred from host-side passes. G7 remains unsatisfied until a "
            "build containing the R-001 id_continuation contract is deployed, the existing state "
            "is migrated with an operator receipt, and device formation/restart/export is observed.",
        ],
    }

    # ---- gate register: enumerate every defined gate (id, purpose, result, evidence, reason)
    report["gate_register"] = _gate_register(report, gates)

    manifest_path = OUT_DIR / "MANIFEST.json"
    evidence_path = OUT_DIR / "R001_CLOSURE_EVIDENCE.json"
    manifest_path.write_text(canonical_json(report), encoding="utf-8")
    evidence = {k: v for k, v in report.items()}
    evidence_path.write_text(canonical_json(evidence), encoding="utf-8")
    return report


def _load_g7_device_investigation() -> dict | None:
    """Load the frozen G7 device investigation if present. This artifact is produced
    by read-only adb observation of the physical device and is NOT host simulation."""
    path = OUT_DIR / "G7_DEVICE_INVESTIGATION.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _gate_register(report: dict, gates: dict) -> dict:
    """Enumerate every defined gate: id, purpose, result, evidence, reason if N/A."""
    reg = {
        "gate1_next_index_semantics": {
            "purpose": "next_index > max(existing suffix) for all seven families, incl. sparse/gapped histories",
            "result": "PASS" if gates["gate1_next_index_semantics"] else "FAIL",
            "evidence": "gate1_next_index_semantics",
        },
        "gate2_pre_repair_load": {
            "purpose": "authoritative pre-repair state loads unchanged -> derived_legacy for all families",
            "result": "PASS" if gates["gate2_pre_repair_load"] else "FAIL",
            "evidence": "gate2_pre_repair_load",
        },
        "gate3_identity_baseline": {
            "purpose": "pre-formation identity snapshot/hash of every inherited identity-bearing structure",
            "result": "PASS (evidence baseline captured; self_id preserved)" if gates["gate3_identity_baseline"] else "FAIL",
            "evidence": "gate3_identity_baseline",
            "reason": "evidence baseline consumed by G4/G5 inherited-unchanged checks; not a boolean torture test. "
                      "Documented exclusion: evolving self-model `state` (its stable self_id is checked separately).",
        },
        "gate4_mass_formation": {
            "purpose": ">=10k new records: zero duplicate IDs, zero overwritten inherited IDs, zero inherited mutation, all streams monotonic",
            "result": "PASS" if gates["gate4_mass_formation"] else "FAIL",
            "evidence": "gate4_mass_formation",
        },
        "gate5_cold_restart_export_import": {
            "purpose": "cold restart + form more; export -> clean import -> form more; inherited state re-compared",
            "result": "PASS" if gates["gate5_cold_restart_export_import"] else "FAIL",
            "evidence": "gate5_cold_restart_export_import",
        },
        "gate6_adversarial": {
            "purpose": "adversarial continuation matrix: every unsafe case yields deterministic formation_blocked/HOLD (closed set of reasons)",
            "result": "PASS" if gates["gate6_adversarial"] else "FAIL",
            "evidence": "gate6_adversarial",
        },
        "gate7_motorola_device_route": {
            "purpose": "prove the deployed Motorola production _form path consumes + preserves the allocator-continuation contract",
            "result": "HOLD / UNSATISFIED" if not gates["gate7_motorola_device_route"] else "SATISFIED",
            "evidence": "gate7_motorola_device_route + G7_DEVICE_INVESTIGATION.json",
            "reason": report.get("verdict", {}).get("g7_blocker", "device gate not satisfied"),
        },
        "gate8_migration_receipts": {
            "purpose": "manual operator counter handoffs produce PERMANENT migration receipts",
            "result": "PASS" if gates["gate8_migration_receipts"] else "FAIL",
            "evidence": "gate8_migration_receipts",
        },
    }
    return reg


def _inventory_motorola() -> dict:
    """Artifact search bounding any Motorola/APTD device route on this machine.
    This does NOT prove device behavior; it only bounds what exists here."""
    import subprocess as _sp

    hits = []
    roots = [str(PACKAGE.parent), r"C:\Users\moop\Downloads\Articles on X.com\Fractalish.com"]
    for root in roots:
        try:
            r = _sp.run(
                ["rg", "-l", "-i", "motorola|aptd", root, "--glob", "*.py", "--glob", "*.js", "--glob", "*.json", "--glob", "*.md"],
                capture_output=True, text=True, timeout=300,
            )
            if r.stdout.strip():
                hits.extend(r.stdout.strip().splitlines())
        except Exception as e:  # noqa: BLE001
            hits.append(f"<rg error on {root}: {e}>")
    unique = sorted(set(hits))
    route_defs = [h for h in unique if "_form" in open(h, encoding="utf-8", errors="ignore").read().lower()] if unique else []
    return {
        "search_roots": roots,
        "hits": unique,
        "containing_form_route": route_defs,
        "verdict": "UNVERIFIED" if unique else "NO_MOTOROLA_ARTIFACT",
        "note": "No deployable Motorola `_form` route is present or inventoried on this machine. "
                "Device-layer consumption of the id_continuation contract CANNOT be asserted. "
                "This gate is UNSATISFIED until the APTD/MOTOROLA inventory (COMPONENT_STATUS.md priority 7) is completed.",
    }


if __name__ == "__main__":
    rep = main()
    print(json.dumps(rep["verdict"], indent=2))