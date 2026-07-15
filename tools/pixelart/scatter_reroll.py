"""Reroll the scatter pieces that failed contact-sheet review. The first
batch's dark-background framing keyed dark objects into fragments (flood_key
ate them), so each reroll picks a background that CONTRASTS with the object:
pale grey behind dark props, dark behind pale ones. Off-brief pieces get
re-worded subjects. Run after scatterkit.py; overwrites only the listed
pieces.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from generate_ai import SPRITE_PREFIX  # noqa: E402
from import_asset import flood_key, smooth_downscale  # noqa: E402
from newband import autocrop, keep_main_island  # noqa: E402
from scatterkit import OUT, SCATTER, gen_with_retry  # noqa: E402

# "no ground under it": generated pieces kept baking a patch of floor/plinth
# into the art (owner: "it looks like there's cement under everything.....
# but then it goes to grass????") -- the object must end at its own feet so
# it sits on whatever the painted world provides.
CAM_DARK = (
    "one single isolated small videogame prop OBJECT, big and centered, "
    "viewed from above at a three-quarter angle, filling most of the frame, "
    "on a plain flat solid black background, NO ground under it, no floor, "
    "no base, no platform, no shadow, the object ends at its own feet, "
    "nothing else in frame, no scene, "
    "no frame, no border, crisp sharp pixel art, "
)
CAM_LIGHT = (
    "one single isolated small videogame prop OBJECT, big and centered, "
    "viewed from above at a three-quarter angle, filling most of the frame, "
    "on a plain flat solid pale grey background, NO ground under it, no "
    "floor, no base, no platform, no shadow, the object ends at its own "
    "feet, nothing else in frame, "
    "no scene, no frame, no border, crisp sharp pixel art, "
)

# (biome, piece, subject override or None, background, seed)
REROLLS: list[tuple[str, str, str | None, str, int]] = [
    ("shallows", "scatter_net", "bundled torn fishing net wrapped around a wooden stake, chunky solid shape", "light", 6101),
    ("shallows", "scatter_stone", "one large rounded barnacled boulder, chunky solid shape", "light", 6102),
    ("shallows", "scatter_oar", "wooden rowing oar planted upright in a small sand mound", "light", 6103),
    ("shallows", "scatter_driftwood", "thick gnarled driftwood log, chunky solid shape", "light", 6104),
    ("shallows", "scatter_anchor", "one rusted iron ship anchor, chunky solid shape", "light", 6105),
    ("saltmines", "scatter_pick", "rusted iron mining pickaxe stuck in a small rock, chunky solid shape", "light", 6111),
    ("saltmines", "scatter_rope", "thick coiled rope pile, chunky solid shape", "light", 6112),
    ("saltmines", "scatter_wheel", "one wooden ore-cart wheel with iron rim leaning on a rock", "light", 6113),
    ("saltmines", "scatter_ore", "one chunky rock of dark ore with glowing amber veins", "light", 6114),
    ("pit", "scatter_stake", "short wooden corner post with a coiled rope around it, chunky solid shape", "light", 6121),
    ("pit", "scatter_ticket", "small crumpled paper ticket stub pile", "dark", 6122),
    ("attic", "scatter_chest", "one small closed wooden keepsake chest with brass fittings, chunky solid shape", "light", 6131),
    ("attic", "scatter_jar", "one corked glass jar with something glowing faintly inside, chunky solid shape", "light", 6132),
    ("attic", "scatter_doll", "one old porcelain doll in a dusty dress sitting upright, chunky solid shape", "light", 6133),
    ("hall", "scatter_belljar", "one glass bell jar on a wooden base with a glowing wisp inside, chunky solid shape", "light", 6141),
    ("hall", "scatter_candelabra", "one standing brass candelabra with three lit candles, chunky solid shape", "light", 6142),
    ("hall", "scatter_metronome", "one wooden pyramid metronome with a brass pendulum, chunky solid shape", "light", 6143),
    ("hall", "scatter_violin", "one violin leaning against a small stone, chunky solid shape", "light", 6151),
]


def main() -> int:
    for biome, piece, subject, bg, seed in REROLLS:
        style, pieces = SCATTER[biome]
        orig_subject, lh, _ = pieces[piece]
        subj = subject or orig_subject
        cam = CAM_LIGHT if bg == "light" else CAM_DARK
        print(f"[{biome}/{piece}] reroll (seed {seed}, bg {bg}) ...", flush=True)
        raw = gen_with_retry(SPRITE_PREFIX + cam + style + subj, seed)
        src = Image.open(io.BytesIO(raw)).convert("RGBA")
        cut = autocrop(keep_main_island(flood_key(src, tol=60)))
        ar = cut.width / cut.height
        lw = max(6, round(lh * ar))
        fig = smooth_downscale(cut, lw, lh)
        fig.save(OUT / biome / f"{piece}.png")
        print(f"[{biome}/{piece}] wrote {lw}x{lh}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
