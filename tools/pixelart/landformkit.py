"""Landform kit -- LANDSCAPE-scale forms over the overworld (PRD v7.15 /
§11.1.1 landform direction: "giant rocks and hills and trees over the scene").

Per region: one colossal OUTCROP (breaks the map silhouette, scenery layer)
and one CANOPY tree (drawn ABOVE the player layer by OverworldScene, alpha-
fading when the player walks beneath -- the HLD trick that gives a flat
top-down map its sense of height). Pieces land in assets/sprites/env/<biome>/
as landform_outcrop.png / landform_canopy.png, so BootScene's env glob loads
them as env_<biome>_landform_* with zero engine loader changes.

Same pinned-camera + cleanup pipeline as envkit.py (AAA audit B2 rules).

Usage:
  python tools/pixelart/landformkit.py            # all biomes
  python tools/pixelart/landformkit.py shallows   # one biome
  SEED_OFFSET=7 python ...                        # reroll
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from generate_ai import SPRITE_PREFIX, gen_pollinations  # noqa: E402
from import_asset import flood_key, smooth_downscale  # noqa: E402
from newband import autocrop, keep_main_island  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "env"

CAMERA = (
    "seen from ABOVE, top-down three-quarter videogame environment asset, "
    "like a Hyper Light Drifter prop, "
)

# biome -> (style clause, {piece: (subject, logical_height_px, seed)})
LANDFORMS: dict[str, tuple[str, dict[str, tuple[str, int, int]]]] = {
    "shallows": (
        "drowned tidal ruin, wet dark sand, teal and rust palette, ",
        {
            "landform_outcrop": ("colossal towering barnacled sea-stack rock outcrop", 96, 301),
            "landform_canopy": ("giant drowned cypress tree with a wide spreading dark teal canopy crown", 88, 302),
        },
    ),
    "saltmines": (
        "abandoned salt mine, packed earth and timber, amber lamplight palette, ",
        {
            "landform_outcrop": ("towering salt-crusted cliff rock formation", 96, 311),
            "landform_canopy": ("giant petrified tree with pale crystalline branches, wide crown", 88, 312),
        },
    ),
    "pit": (
        "ruined carnival fighting pit, faded purple and plum palette, ",
        {
            "landform_outcrop": ("colossal jagged plum-purple rock spire cluster", 96, 321),
            "landform_canopy": ("giant dead oak tree with tattered purple pennants in a wide bare crown", 88, 322),
        },
    ),
    "attic": (
        "vast dusty attic district, warm lamplight and deep shadow, amber palette, ",
        {
            "landform_outcrop": ("colossal tower of ruined stacked furniture and roof beams", 96, 331),
            "landform_canopy": ("giant twisted dead tree with a sprawling bare crown", 88, 332),
        },
    ),
    "hall": (
        "drowned gothic concert hall district, dark marble and violet palette, ",
        {
            "landform_outcrop": ("colossal black marble shard rock outcrop with violet sheen", 96, 341),
            "landform_canopy": ("giant weeping willow of black kelp strands with a wide drooping crown", 88, 342),
        },
    ),
}


def gen_with_retry(prompt: str, seed: int, attempts: int = 4) -> bytes:
    """Pollinations 500s intermittently; retry with a nudged seed (a different
    seed routes to a different render, which usually clears the error)."""
    import time

    last: Exception | None = None
    for i in range(attempts):
        try:
            return gen_pollinations(prompt, 768, 768, seed=seed + i * 1000)
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"  retry {i + 1}/{attempts} after: {e}", flush=True)
            time.sleep(3 * (i + 1))
    raise last  # type: ignore[misc]


def build(biome: str, piece: str, style: str, subject: str, lh: int, seed: int) -> None:
    print(f"[{biome}/{piece}] generating (seed {seed}) ...", flush=True)
    raw = gen_with_retry(SPRITE_PREFIX + CAMERA + style + subject, seed)
    src = Image.open(io.BytesIO(raw)).convert("RGBA")
    cut = autocrop(keep_main_island(flood_key(src, tol=60)))
    ar = cut.width / cut.height
    lw = max(8, round(lh * ar))
    fig = smooth_downscale(cut, lw, lh)
    outdir = OUT / biome
    outdir.mkdir(parents=True, exist_ok=True)
    fig.save(outdir / f"{piece}.png")
    print(f"[{biome}/{piece}] wrote {lw}x{lh}")


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    off = int(os.environ.get("SEED_OFFSET", "0"))
    for biome, (style, pieces) in LANDFORMS.items():
        if only and biome != only:
            continue
        for piece, (subject, lh, seed) in pieces.items():
            build(biome, piece, style, subject, lh, seed + off)


if __name__ == "__main__":
    main()
