"""Reroll the landform variants that failed contact-sheet review. Failure
modes this batch: "attic district" wording produced room INTERIORS, two
generations kept a framed background card, two got shredded by the island
filter. Fixes: freestanding-object phrasing ("seen from outside, not a
room") and an explicit contrast background per piece.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from landformkit import CAMERA, LANDFORMS, build  # noqa: E402
import landformkit  # noqa: E402

BG_DARK = "on a plain flat solid black background, no frame, no border, "
BG_LIGHT = "on a plain flat solid pale grey background, no frame, no border, "

# (biome, piece, subject, bg, logical_height, seed)
REROLLS: list[tuple[str, str, str, str, int, int]] = [
    ("shallows", "landform_outcrop3", "one colossal freestanding barnacled broken stone tower stump, solid chunky silhouette", BG_LIGHT, 96, 8301),
    ("saltmines", "landform_outcrop2", "one colossal freestanding wooden mine headframe tower structure with amber lanterns, seen from outside on open ground", BG_LIGHT, 96, 8311),
    ("saltmines", "landform_outcrop3", "one huge freestanding mound of pale salt boulders shored with dark timber props, solid chunky silhouette", BG_DARK, 78, 8312),
    ("saltmines", "landform_canopy2", "one giant freestanding branching pale salt crystal tree, wide crown", BG_DARK, 84, 8313),
    ("pit", "landform_canopy2", "one giant freestanding bare dead tree with faded purple pennant flags hanging in the wide crown", BG_LIGHT, 84, 8321),
    ("attic", "landform_outcrop2", "one colossal freestanding grandfather clock furniture piece leaning, cracked face, dusty dark wood, seen from outside, not a room", BG_LIGHT, 96, 8331),
    ("attic", "landform_outcrop3", "one colossal freestanding leaning tower stacked from giant dusty leather books, seen from outside, not a room", BG_DARK, 80, 8332),
    ("attic", "landform_canopy2", "one giant freestanding twisted dead tree draped with old dark cloaks, wide spreading crown", BG_LIGHT, 84, 8333),
    ("hall", "landform_canopy2", "one giant freestanding branching black iron candelabra tree with violet candle flames, wide crown", BG_LIGHT, 84, 8341),
]


def main() -> None:
    base_camera = CAMERA
    for biome, piece, subject, bg, lh, seed in REROLLS:
        style = LANDFORMS[biome][0]
        # build() reads landformkit's CAMERA global at call time; patch it
        # per piece so each reroll carries its own background clause.
        landformkit.CAMERA = base_camera + bg
        build(biome, piece, style, subject, lh, seed)
    landformkit.CAMERA = base_camera


if __name__ == "__main__":
    main()
