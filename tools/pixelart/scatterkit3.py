"""Scatter kit wave 3 (design-audit-3 volume push): 8 MORE pieces per biome
on top of waves 1-2, bringing each region's library to 24. Contrast-aware
backgrounds per piece, object framing throughout.
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
WAVE3: dict[str, dict[str, tuple[str, int, str, int]]] = {
    "shallows": {
        "scatter_lifering": ("one weathered striped life ring half-buried in sand", 16, "light", 13401),
        "scatter_seacrate": ("one waterlogged wooden supply crate with kelp on it", 20, "light", 13402),
        "scatter_harpoon": ("one rusted harpoon stuck upright in the sand", 28, "light", 13403),
        "scatter_starfish": ("a few pale starfish on wet sand, chunky solid shapes", 12, "dark", 13404),
        "scatter_dockpost": ("one leaning dock lantern post with a teal-glowing lamp", 30, "light", 13405),
        "scatter_figurehead": ("one broken ship figurehead statue of a woman, washed ashore", 24, "light", 13406),
        "scatter_seachest": ("one barnacled sunken treasure chest, closed", 20, "light", 13407),
        "scatter_reedclump": ("one tall clump of dark salt reeds", 28, "dark", 13408),
    },
    "saltmines": {
        "scatter_pillar": ("one broken pale salt pillar stub", 24, "dark", 13411),
        "scatter_winch": ("one wooden hand winch with rope", 24, "light", 13412),
        "scatter_ladder": ("one broken wooden ladder leaning", 28, "light", 13413),
        "scatter_candles": ("cluster of lit miner candles melted onto a rock", 18, "light", 13414),
        "scatter_tub": ("one battered metal washing tub", 16, "light", 13415),
        "scatter_bones": ("a few pale bones half-buried in salt", 12, "dark", 13416),
        "scatter_sign": ("one weathered wooden warning sign post", 26, "light", 13417),
        "scatter_stalagmite": ("one pale salt stalagmite spire", 26, "dark", 13418),
    },
    "pit": {
        "scatter_ringpost": ("one padded wrestling ring corner post with frayed rope", 28, "light", 13421),
        "scatter_horn": ("one dented brass tuba horn on the ground", 18, "light", 13422),
        "scatter_flag": ("one tattered victory flag on a short pole", 30, "light", 13423),
        "scatter_weights": ("one stack of old iron weight plates", 16, "light", 13424),
        "scatter_keg": ("one wooden keg with a tap, tipped", 18, "light", 13425),
        "scatter_streamer": ("one pile of faded purple paper streamers", 12, "light", 13426),
        "scatter_megaphone": ("one old tin megaphone on the ground", 14, "light", 13427),
        "scatter_scale": ("one carnival strength-test scale with a bell on top", 30, "light", 13428),
    },
    "attic": {
        "scatter_globe": ("one dusty world globe on a wooden stand", 22, "light", 13431),
        "scatter_sewing": ("one old black sewing machine on a small table", 22, "light", 13432),
        "scatter_phonograph": ("one brass horn phonograph on a crate", 24, "light", 13433),
        "scatter_umbrellas": ("one umbrella stand stuffed with old umbrellas and canes", 24, "light", 13434),
        "scatter_portraits": ("a stack of old framed portrait paintings leaning", 22, "light", 13435),
        "scatter_musicbox": ("one small open music box with a tiny dancer", 16, "light", 13436),
        "scatter_telescope": ("one brass telescope on a tripod", 26, "light", 13437),
        "scatter_typewriter": ("one dusty old typewriter", 14, "light", 13438),
    },
    "hall": {
        "scatter_pew": ("one broken dark wooden pew bench", 20, "light", 13441),
        "scatter_drape": ("one fallen pile of deep violet velvet drapery", 16, "light", 13442),
        "scatter_lyre": ("one tarnished golden lyre", 20, "light", 13443),
        "scatter_votives": ("one ring of small lit votive candles", 12, "light", 13444),
        "scatter_plaque": ("one fallen engraved bronze plaque leaning on stone", 18, "light", 13445),
        "scatter_baton": ("one conductor's baton resting on a velvet cushion", 12, "light", 13446),
        "scatter_gramophone": ("one dark gramophone with a violet-sheened horn", 24, "light", 13447),
        "scatter_hourglass": ("one large ornate hourglass with pale glowing sand", 20, "dark", 13448),
    },
}


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for biome, pieces in WAVE3.items():
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
