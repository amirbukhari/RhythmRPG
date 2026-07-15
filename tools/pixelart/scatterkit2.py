"""Scatter kit wave 2 (design-audit-3 C): 8 MORE pieces per biome on top of
scatterkit.py's first 8, doubling each region's library to 16. Backgrounds
are contrast-aware from the start (the wave-1 lesson: dark props on the
prompted dark background get shredded by the flood key).
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from generate_ai import SPRITE_PREFIX  # noqa: E402
from import_asset import flood_key, smooth_downscale  # noqa: E402
from newband import autocrop, keep_main_island  # noqa: E402
from scatter_reroll import CAM_DARK, CAM_LIGHT  # noqa: E402
from scatterkit import OUT, SCATTER, gen_with_retry  # noqa: E402

# biome -> {piece: (subject, logical_height_px, "light"|"dark" bg, seed)}
WAVE2: dict[str, dict[str, tuple[str, int, str, int]]] = {
    "shallows": {
        "scatter_buoy": ("one weathered striped fishing buoy lying on its side", 22, "light", 7401),
        "scatter_crab": ("one small teal crab", 12, "light", 7402),
        "scatter_bottle": ("one message bottle stuck neck-down in sand", 18, "dark", 7403),
        "scatter_plank": ("small pile of broken ship planks", 18, "light", 7404),
        "scatter_shiplantern": ("one rusted ship lantern with a faint teal glow", 22, "light", 7405),
        "scatter_coral": ("one small branching dead coral cluster", 22, "dark", 7406),
        "scatter_skiff": ("one tiny broken rowboat half-buried in sand", 24, "light", 7407),
        "scatter_piling": ("one barnacled broken dock piling stump with rope", 28, "light", 7408),
    },
    "saltmines": {
        "scatter_cart": ("one small broken wooden ore cart", 26, "light", 7411),
        "scatter_sacks": ("small pile of burlap salt sacks, one spilling", 20, "light", 7412),
        "scatter_beam": ("one collapsed timber support beam leaning", 26, "light", 7413),
        "scatter_brazier": ("one iron brazier with glowing embers", 24, "light", 7414),
        "scatter_chain": ("heavy iron chain heaped on the ground", 16, "light", 7415),
        "scatter_bucket": ("one wooden bucket filled with salt chunks", 18, "light", 7416),
        "scatter_rail": ("short broken segment of mine-cart rail track", 16, "light", 7417),
        "scatter_geode": ("one cracked-open geode with glowing amber crystals inside", 20, "light", 7418),
    },
    "pit": {
        "scatter_glove": ("one worn purple boxing glove on the ground", 16, "light", 7421),
        "scatter_poster": ("one torn wrestling poster board leaning on a stick", 26, "light", 7422),
        "scatter_drum": ("one broken carnival bass drum", 22, "light", 7423),
        "scatter_bench": ("one broken wooden spectator bench", 22, "light", 7424),
        "scatter_cage": ("one small bent iron cage, door hanging open", 24, "light", 7425),
        "scatter_dumbbell": ("one old iron dumbbell", 14, "light", 7426),
        "scatter_torch": ("one standing torch pole with purple flame", 30, "light", 7427),
        "scatter_crate": ("one broken carnival crate with faded purple paint", 20, "light", 7428),
    },
    "attic": {
        "scatter_lamp": ("one stained-glass tiffany lamp glowing warmly", 24, "light", 7431),
        "scatter_mirror": ("one cracked ornate hand mirror", 20, "light", 7432),
        "scatter_radio": ("one old wooden tube radio", 20, "light", 7433),
        "scatter_trunk": ("one old leather travel trunk with straps", 22, "light", 7434),
        "scatter_hatbox": ("stack of two round dusty hatboxes", 20, "light", 7435),
        "scatter_birdcage": ("one empty brass birdcage, door open", 26, "light", 7436),
        "scatter_clock": ("one mantel clock with a cracked face", 20, "light", 7437),
        "scatter_rockinghorse": ("one faded wooden rocking horse", 24, "light", 7438),
    },
    "hall": {
        "scatter_bust": ("one marble bust of a composer on a broken plinth", 26, "dark", 7441),
        "scatter_harp": ("one small broken harp with snapped strings", 26, "light", 7442),
        "scatter_chandelier": ("one fallen brass chandelier lying on the floor", 24, "light", 7443),
        "scatter_pipe": ("one fallen tarnished brass organ pipe", 22, "light", 7444),
        "scatter_operamask": ("one white opera mask on the floor", 14, "dark", 7445),
        "scatter_stand": ("one bent brass music stand with sheet music", 26, "light", 7446),
        "scatter_goblet": ("one tipped-over silver goblet", 14, "light", 7447),
        "scatter_cello": ("one cracked cello leaning on a stone", 30, "light", 7448),
    },
}


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for biome, pieces in WAVE2.items():
        if only and biome != only:
            continue
        style = SCATTER[biome][0]
        for piece, (subject, lh, bg, seed) in pieces.items():
            dest = OUT / biome / f"{piece}.png"
            if dest.exists() and os.environ.get("FORCE") != "1":
                print(f"[{biome}/{piece}] exists, skip")
                continue
            cam = CAM_LIGHT if bg == "light" else CAM_DARK
            print(f"[{biome}/{piece}] generating (seed {seed}, bg {bg}) ...", flush=True)
            raw = gen_with_retry(SPRITE_PREFIX + cam + style + subject, seed)
            src = Image.open(io.BytesIO(raw)).convert("RGBA")
            cut = autocrop(keep_main_island(flood_key(src, tol=60)))
            lw = max(6, round(lh * cut.width / cut.height))
            fig = smooth_downscale(cut, lw, lh)
            fig.save(dest)
            print(f"[{biome}/{piece}] wrote {lw}x{lh}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
