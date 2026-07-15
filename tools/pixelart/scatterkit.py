"""Per-biome overworld scatter kits (design-audit-3 B: "a blurry ass lamp
scattered literally everywhere"). The old decoration was ONE shared 6-frame
24x32 sheet -- the same lamp/tombstone repeated across all five regions. This
generates a proper scatter library: 8 distinct pieces PER BIOME through the
AI pipeline, landing in assets/sprites/env/<biome>/scatter_*.png so
BootScene's env glob auto-loads them (env_<biome>_scatter_<name>) with zero
loader changes. OverworldScene scatters from the local biome's kit only.

Usage:
  python3 tools/pixelart/scatterkit.py            # all biomes
  python3 tools/pixelart/scatterkit.py shallows   # one biome
"""

from __future__ import annotations

import io
import os
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from generate_ai import SPRITE_PREFIX, gen_pollinations  # noqa: E402
from import_asset import flood_key, smooth_downscale  # noqa: E402
from newband import autocrop, keep_main_island  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "env"

# Small props need OBJECT framing, not environment framing -- the diorama
# phrasing (envkit's CAMERA) made the model draw tiny framed scenes instead
# of isolated items (caught in the first batch's contact-sheet review).
CAMERA = (
    "one single isolated small videogame prop OBJECT, viewed from above at a "
    "three-quarter angle, centered on a plain dark background, nothing else "
    "in frame, no scene, no room, no frame, no border, crisp sharp pixel art, "
)

# biome -> (style clause, {piece: (subject, logical_height_px, seed)})
SCATTER: dict[str, tuple[str, dict[str, tuple[str, int, int]]]] = {
    "shallows": (
        "drowned tidal ruin style, wet dark sand, teal and rust palette, ",
        {
            "scatter_kelp": ("small tuft of dark kelp", 30, 5401),
            "scatter_stone": ("small barnacled wet stone", 22, 5402),
            "scatter_driftwood": ("piece of pale driftwood", 24, 5403),
            "scatter_tidepool": ("tiny glowing tide pool with anemones", 26, 5404),
            "scatter_oar": ("broken wooden oar half-buried in sand", 28, 5405),
            "scatter_shells": ("small cluster of pearl shells", 18, 5406),
            "scatter_anchor": ("small rusted anchor fragment", 30, 5407),
            "scatter_net": ("torn fishing net snagged on a stick", 30, 5408),
        },
    ),
    "saltmines": (
        "abandoned salt mine style, packed earth and timber, amber lamplight palette, ",
        {
            "scatter_nodule": ("small pale salt nodule cluster", 22, 5411),
            "scatter_timber": ("broken timber post stub", 28, 5412),
            "scatter_pick": ("rusted mining pick left in the ground", 26, 5413),
            "scatter_ore": ("small ore chunk with glinting veins", 20, 5414),
            "scatter_crystal": ("small glowing salt crystal spray", 26, 5415),
            "scatter_lantern": ("small rusted iron miner's lantern, sharply drawn, warm glow", 28, 5416),
            "scatter_wheel": ("broken ore-cart wheel leaning", 26, 5417),
            "scatter_rope": ("coil of old rope", 18, 5418),
        },
    ),
    "pit": (
        "ruined carnival style, faded purple and plum palette, ",
        {
            "scatter_chair": ("broken wooden folding chair", 26, 5421),
            "scatter_pennant": ("torn purple pennant flag on a short pole", 32, 5422),
            "scatter_rubble": ("small pile of broken painted planks", 20, 5423),
            "scatter_mask": ("discarded luchador wrestling mask", 16, 5424),
            "scatter_stake": ("wooden ring stake with frayed rope", 26, 5425),
            "scatter_bell": ("small tarnished boxing bell on a post", 28, 5426),
            "scatter_ticket": ("a few scattered faded carnival tickets", 12, 5427),
            "scatter_barrel": ("broken wooden barrel", 26, 5428),
        },
    ),
    "attic": (
        "dusty antique style, warm lamplight, amber palette, ",
        {
            "scatter_books": ("small stack of dusty old books", 22, 5431),
            "scatter_candle": ("melted candle stub with a tiny flame", 20, 5432),
            "scatter_jar": ("dusty glass jar", 20, 5433),
            "scatter_frame": ("broken ornate picture frame leaning", 26, 5434),
            "scatter_teacup": ("cracked porcelain teacup", 14, 5435),
            "scatter_chest": ("tiny wooden keepsake chest ajar", 22, 5436),
            "scatter_gear": ("large fallen brass clock gear", 22, 5437),
            "scatter_doll": ("abandoned porcelain doll sitting", 24, 5438),
        },
    ),
    "hall": (
        "drowned gothic concert hall style, dark marble and violet palette, ",
        {
            "scatter_violin": ("broken violin", 22, 5441),
            "scatter_sheets": ("pile of waterlogged sheet music pages", 16, 5442),
            "scatter_candelabra": ("small fallen brass candelabra", 26, 5443),
            "scatter_marble": ("chunk of carved marble cornice", 22, 5444),
            "scatter_rose": ("single black rose", 20, 5445),
            "scatter_belljar": ("glass bell jar with a faint glow inside", 24, 5446),
            "scatter_metronome": ("old wooden metronome", 24, 5447),
            "scatter_quill": ("ink pot with a raven feather quill", 20, 5448),
        },
    ),
}


def gen_with_retry(prompt: str, seed: int, attempts: int = 4) -> bytes:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return gen_pollinations(prompt, 640, 640, seed=seed + i * 1000)
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"  retry {i + 1}/{attempts} after: {e}", flush=True)
            time.sleep(3 * (i + 1))
    raise last  # type: ignore[misc]


def build(biome: str, piece: str, style: str, subject: str, lh: int, seed: int) -> None:
    outdir = OUT / biome
    dest = outdir / f"{piece}.png"
    if dest.exists() and os.environ.get("FORCE") != "1":
        print(f"[{biome}/{piece}] exists, skip")
        return
    print(f"[{biome}/{piece}] generating (seed {seed}) ...", flush=True)
    raw = gen_with_retry(SPRITE_PREFIX + CAMERA + style + subject, seed)
    src = Image.open(io.BytesIO(raw)).convert("RGBA")
    cut = autocrop(keep_main_island(flood_key(src, tol=60)))
    ar = cut.width / cut.height
    lw = max(6, round(lh * ar))
    fig = smooth_downscale(cut, lw, lh)
    outdir.mkdir(parents=True, exist_ok=True)
    fig.save(dest)
    print(f"[{biome}/{piece}] wrote {lw}x{lh}")


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for biome, (style, pieces) in SCATTER.items():
        if only and biome != only:
            continue
        for piece, (subject, lh, seed) in pieces.items():
            build(biome, piece, style, subject, lh, seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
