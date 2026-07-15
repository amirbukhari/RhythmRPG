"""Landform VARIANTS (design-audit-3 C): each biome had exactly one outcrop
and one canopy silhouette, so regions repeated a single form wall-to-wall.
Adds outcrop2/outcrop3/canopy2 per biome (15 pieces); OverworldScene picks
deterministically among whichever variants exist.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from landformkit import LANDFORMS, OUT, build  # noqa: E402

VARIANTS: dict[str, dict[str, tuple[str, int, int]]] = {
    "shallows": {
        "landform_outcrop2": ("colossal tilted shipwreck hull half-buried in wet sand, rusted iron and rotten planks", 90, 7301),
        "landform_outcrop3": ("colossal barnacled stone lighthouse ruin stump", 96, 7302),
        "landform_canopy2": ("giant leaning drowned tree with a wide flat dark teal frond crown", 84, 7303),
    },
    "saltmines": {
        "landform_outcrop2": ("colossal wooden mine headframe tower with glowing amber lanterns", 96, 7311),
        "landform_outcrop3": ("huge mound of pale salt boulders shored up with timber supports", 78, 7312),
        "landform_canopy2": ("giant pale crystalline salt formation branching like a wide tree", 84, 7313),
    },
    "pit": {
        "landform_outcrop2": ("colossal collapsed carnival big-top tent, torn faded purple canvas over bent poles", 88, 7321),
        "landform_outcrop3": ("colossal broken ferris wheel segment leaning against rocks, faded purple", 96, 7322),
        "landform_canopy2": ("giant dead tree strung with faded purple bunting flags, wide bare crown", 84, 7323),
    },
    "attic": {
        "landform_outcrop2": ("colossal leaning grandfather clock with a cracked face, dusty dark wood", 96, 7331),
        "landform_outcrop3": ("huge hill-sized pile of giant dusty leather books", 76, 7332),
        "landform_canopy2": ("giant twisted coat-rack tree hung with old dark cloaks, wide spreading arms", 84, 7333),
    },
    "hall": {
        "landform_outcrop2": ("colossal ruined pipe organ facade, dark marble and tarnished brass pipes", 96, 7341),
        "landform_outcrop3": ("colossal fallen marble column section with carved reliefs, violet sheen", 70, 7342),
        "landform_canopy2": ("giant branching black iron candelabra tree with violet flames, wide crown", 84, 7343),
    },
}


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for biome, pieces in VARIANTS.items():
        if only and biome != only:
            continue
        style = LANDFORMS[biome][0]
        for piece, (subject, lh, seed) in pieces.items():
            if (OUT / biome / f"{piece}.png").exists() and os.environ.get("FORCE") != "1":
                print(f"[{biome}/{piece}] exists, skip")
                continue
            build(biome, piece, style, subject, lh, seed)


if __name__ == "__main__":
    main()
