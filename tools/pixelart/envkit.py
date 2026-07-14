"""Regenerate the arena environment piece kits with a PINNED top-down camera
(AAA audit B2). The first-generation kits mixed perspectives and biomes --
side-view boats and grass-topped islands on a top-down floor -- because the
prompts never pinned the camera or a shared scale. Every piece here:

  * pins the camera: "seen from above, top-down three-quarter view";
  * shares one biome style clause so a kit reads as ONE place;
  * declares a target logical height (shared scale reference);
  * runs the newband.py cleanup (island filter; pieces skip mist-scrub --
    fog isn't drawn on objects) and the adaptive-palette pixelate.

Usage:
  python tools/pixelart/envkit.py shallows      # one biome
  python tools/pixelart/envkit.py               # all biomes
  SEED_OFFSET=7 python ...                      # reroll
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from generate_ai import SPRITE_PREFIX, gen_pollinations  # noqa: E402
from import_asset import flood_key, pixelate  # noqa: E402
from newband import autocrop, keep_main_island  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "env"

CAMERA = (
    "seen from ABOVE, top-down three-quarter videogame environment asset, "
    "like a Hyper Light Drifter prop, "
)

# biome -> (style clause, {piece: (subject, logical_height_px, seed)})
KITS: dict[str, tuple[str, dict[str, tuple[str, int, int]]]] = {
    "shallows": (
        "drowned tidal ruin, wet dark sand, teal and rust palette, ",
        {
            "boat": ("capsized broken wooden rowboat wreck, hull up", 54, 201),
            "pillar": ("broken barnacled stone pillar stump", 54, 202),
            "rock_a": ("single barnacled wet sea boulder", 35, 203),
            "rock_b": ("cluster of small wet tidal rocks", 22, 204),
            "reeds": ("tuft of dark kelp reeds", 38, 205),
            "lantern": ("rusted iron standing lantern on a pole, faint warm light", 48, 206),
            "campfire": ("small driftwood campfire with embers", 26, 207),
        },
    ),
    "saltmines": (
        "abandoned salt mine, packed earth and timber, amber lamplight palette, ",
        {
            "ore_cart": ("rusted mine ore cart on rails", 45, 211),
            "timber": ("wooden support timber frame post", 58, 212),
            "salt_crystal": ("jagged glowing pale salt crystal formation", 42, 213),
            "ore_rock": ("rough ore boulder with mineral veins", 32, 214),
            "calcified_miner": ("calcified statue of a kneeling miner, salt-crusted", 48, 215),
        },
    ),
    "pit": (
        "ruined carnival fighting pit, faded purple and plum palette, ",
        {
            "ticket_booth": ("collapsed carnival ticket booth", 54, 221),
            "carousel_horse": ("broken fallen carousel horse", 38, 222),
            "tent_pole": ("torn circus tent pole with rope", 61, 223),
            "plum_rubble": ("pile of broken purple-painted planks", 22, 224),
            "rope_coil": ("thick coiled rope on the ground", 16, 225),
        },
    ),
    "attic": (
        "vast dusty attic, warm lamplight and deep shadow, amber palette, ",
        {
            "drawers": ("tall antique chest of drawers, drawers ajar", 58, 231),
            "crate_stack": ("stack of dusty wooden crates", 45, 232),
            "rocking_chair": ("old rocking chair", 42, 233),
            "birdcage": ("tarnished empty standing birdcage", 45, 234),
            "oil_lamp": ("lit brass oil lamp on the floor", 22, 235),
        },
    ),
    "hall": (
        "drowned gothic concert hall, dark marble and violet palette, ",
        {
            "plinth": ("cracked marble plinth", 48, 241),
            "melting_clock": ("surreal melting grandfather clock", 61, 242),
            "music_stand": ("toppled brass music stand with scattered sheets", 35, 243),
            "page_stack": ("pile of waterlogged sheet music pages", 16, 244),
            "chandelier": ("fallen crystal chandelier on the floor", 42, 245),
        },
    ),
    "shared": (
        "drowned gothic world, teal and rust palette, ",
        {
            "save_obelisk": ("ancient standing stone obelisk with glowing teal runes", 58, 251),
        },
    ),
}


def build(biome: str, piece: str, style: str, subject: str, lh: int, seed: int) -> None:
    print(f"[{biome}/{piece}] generating (seed {seed}) ...", flush=True)
    raw = gen_pollinations(SPRITE_PREFIX + CAMERA + style + subject, 768, 768, seed=seed)
    src = Image.open(io.BytesIO(raw)).convert("RGBA")
    cut = autocrop(keep_main_island(flood_key(src, tol=60)))
    ar = cut.width / cut.height
    lw = max(8, round(lh * ar))
    fig = pixelate(cut, lw, lh, dither=False, colors=64)
    outdir = OUT / biome
    outdir.mkdir(parents=True, exist_ok=True)
    fig.save(outdir / f"{piece}.png")
    print(f"[{biome}/{piece}] wrote {lw}x{lh}")


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    off = int(os.environ.get("SEED_OFFSET", "0"))
    for biome, (style, pieces) in KITS.items():
        if only and biome != only:
            continue
        for piece, (subject, lh, seed) in pieces.items():
            build(biome, piece, style, subject, lh, seed + off)


if __name__ == "__main__":
    main()
