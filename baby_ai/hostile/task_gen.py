"""Frozen deterministic task generator for hostile qualification.

Every task family has the SAME causal structure:
    formation item (safe, tagged) -> withheld related item (shared tag) should
    inherit the RELEASE consequence; unrelated item (different tag) must NOT.
    Plus optional interference history.

All surfaces (domain terms, item lexemes, tag tokens, claim phrases, decision
labels) are derived PURELY from a seed via splitmix64, so the generator is a
frozen, reproducible function of seed. No withheld answer is hand-written after
observing system behavior.

Task roles (section 5):
    FORMATION      - the item we form over (learn clearance)
    CALIBRATION    - direct query of the formation item itself (trivially reachable)
    WITHHELD       - related item sharing the tag group (never seen, must inherit)
    UNRELATED      - different tag group (must stay HOLD)
    INTERFERENCE   - unrelated formed history (poisoning probes, section 6)

Returns dicts of plain string surfaces; adapters map them onto MemoryEvents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SEEDS = list(range(0, 24))  # frozen seed set for the hostile run


def splitmix64(seed: int) -> Any:
    """Deterministic 64-bit PRNG state machine (SplitMix64). Generator only."""
    state = seed & 0xFFFFFFFFFFFFFFFF

    def next_u64() -> int:
        nonlocal state
        state = (state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        z = z ^ (z >> 31)
        return z

    return next_u64


# surface vocab pools (fixed; the seed picks combinations)
ITEM_SYLS = ["zor", "kix", "vel", "thum", "polt", "grin", "wesk", "mold", "qesh", "yarn", "blor", "dwyn"]
TAG_TOKENS = ["band", "ring", "couplet", "cluster", "lattice", "mesh", "bloc", "tendril"]
VERDICTS = ["RELEASE", "HOLD"]
ITEM_NUM_ALPHA = "abcdefghk"


@dataclass
class TaskFamily:
    seed: int
    # surfaces
    lesson: str            # domain term for "safe to release" e.g. "flux" (semantic, kept stable)
    formed_item: str
    withheld_item: str
    unrelated_item: str
    tag_group: str
    formed_claim: str
    related_claim: str
    unrelated_claim: str
    # pre-generated interference surfaces
    interference_items: list[str] = field(default_factory=list)
    # bookkeeping
    generation_recipe: dict[str, Any] = field(default_factory=dict)

    def role_items(self) -> dict[str, str]:
        return {
            "formed": self.formed_item,
            "withheld": self.withheld_item,
            "unrelated": self.unrelated_item,
        }


def _item_from(prng, bar: str) -> str:
    return bar + "_" + ITEM_SYLS[prng() % len(ITEM_SYLS)] + ITEM_NUM_ALPHA[prng() % len(ITEM_NUM_ALPHA)]


def _tag_for(seed: int, bar: str) -> str:
    """Deterministic tag token per (seed,bar) — independent of item lexemes."""
    prng = splitmix64(seed * 1000003 + sum(ord(c) for c in bar))
    return TAG_TOKENS[prng() % len(TAG_TOKENS)]


def generate_family(seed: int, *, with_interference: int = 0) -> TaskFamily:
    """Frozen generator: one causal structure, fully surface-randomized by seed.

    Relatedness is modeled honestly like the MVP: items in the same causal group
    share the GROUP TOKEN in their surface identity (flux_alpha / flux_beta both
    carry 'flux'), which is exactly what qualified retrieval sees. The token
    itself is randomized per seed, so no fixed string carries the test.
    """
    prng = splitmix64(seed)

    tag_g = _tag_for(seed, "alpha")

    formed = f"{tag_g}_{_item_from(prng, 'a')}"
    withheld = f"{tag_g}_{_item_from(prng, 'b')}"
    unrelated = f"other_{_item_from(prng, 'x')}"

    formed_claim = f"{formed} {VERDICTS[0].lower()} clearance under {tag_g}"
    related_claim = f"{withheld} inherits {tag_g} clearing"
    unrelated_claim = f"{unrelated} stays outsider under distinct group"

    inter_items: list[str] = []
    for i in range(with_interference):
        bar = f"intr{i}"
        inter_items.append(f"other_{_item_from(splitmix64(seed * 131 + i), bar)}")

    recipe = {
        "seed": seed,
        "bars": {"formed": "a", "withheld": "b", "unrelated": "x"},
        "tag_token": tag_g,
        "interference_count": with_interference,
    }
    return TaskFamily(
        seed=seed,
        lesson=tag_g,
        formed_item=formed,
        withheld_item=withheld,
        unrelated_item=unrelated,
        tag_group=tag_g,
        formed_claim=formed_claim,
        related_claim=related_claim,
        unrelated_claim=unrelated_claim,
        interference_items=inter_items,
        generation_recipe=recipe,
    )


def generate_seed_set(count: int | None = None) -> dict[int, TaskFamily]:
    """Frozen map seed -> TaskFamily (defaults to the whole frozen seed set)."""
    seeds = SEEDS if count is None else SEEDS[:count]
    return {s: generate_family(s) for s in seeds}


def family_brief(fam: TaskFamily) -> str:
    return (
        f"seed={fam.seed} tag={fam.tag_group!r} "
        f"formed={fam.formed_item!r} withheld={fam.withheld_item!r} unrelated={fam.unrelated_item!r}"
    )