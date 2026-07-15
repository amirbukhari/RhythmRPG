"""Venue-kit reroll (design-audit-3 E): the original envkit pieces that dress
fight venues (ArenaComposer) were generated with environment framing, so half
came out as doll-house room-corner DIORAMAS (a whole miniature room where a
dresser should be) or flood-key shreds. Reroll with the object framing +
contrast-aware backgrounds proven on the scatter kits. Logical sizes are read
from the existing files so every ArenaLayout placement keeps working.
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
from scatter_reroll import CAM_DARK, CAM_LIGHT  # noqa: E402
from scatterkit import OUT, SCATTER, gen_with_retry  # noqa: E402

# (biome, piece, subject, "light"|"dark", seed)
REROLLS: list[tuple[str, str, str, str, int]] = [
    ("attic", "crate_stack", "stack of dusty wooden crates, chunky solid shape", "light", 12331),
    ("attic", "oil_lamp", "one standing brass oil lamp on a pole, lit with a warm flame", "light", 12332),
    ("attic", "rocking_chair", "one old wooden rocking chair, chunky solid shape", "light", 12333),
    ("hall", "chandelier", "one tall standing brass candelabra tower with violet candle flames", "light", 12341),
    ("hall", "music_stand", "one brass music stand holding white sheet music", "light", 12342),
    ("hall", "plinth", "one tall marble plinth column with a carved stone bust on top, chunky solid shape", "dark", 12343),
    ("hall", "melting_clock", "one large clock face melting and drooping over a stone block", "light", 12344),
    ("hall", "page_stack", "messy pile of waterlogged white sheet music pages", "dark", 12345),
    ("pit", "rope_coil", "one thick coil of heavy rope on the ground, chunky solid shape", "light", 12321),
    ("pit", "plum_rubble", "one pile of broken purple-painted planks and stone rubble, chunky solid shape", "light", 12322),
    ("pit", "ticket_booth", "one small ruined carnival ticket booth with faded purple stripes, chunky solid shape", "light", 12323),
    ("saltmines", "calcified_miner", "one statue of a miner encrusted in pale white salt, frozen mid-stride, chunky solid shape", "dark", 12311),
    ("saltmines", "ore_cart", "one wooden mine cart on small iron wheels, full of glowing amber ore chunks", "light", 12312),
    ("saltmines", "salt_crystal", "one cluster of huge glowing pale salt crystal shards, chunky solid shapes", "dark", 12313),
    ("saltmines", "timber", "one broken timber support frame, two thick posts and a lintel beam, chunky solid shape", "light", 12314),
]


def main() -> int:
    for biome, piece, subject, bg, seed in REROLLS:
        dest = OUT / biome / f"{piece}.png"
        old = Image.open(dest)
        lh = old.height  # keep the logical size every ArenaLayout expects
        style = SCATTER[biome][0]
        cam = CAM_LIGHT if bg == "light" else CAM_DARK
        print(f"[{biome}/{piece}] reroll (seed {seed}, keep h={lh}) ...", flush=True)
        raw = gen_with_retry(SPRITE_PREFIX + cam + style + subject, seed)
        src = Image.open(io.BytesIO(raw)).convert("RGBA")
        cut = autocrop(keep_main_island(flood_key(src, tol=60)))
        lw = max(6, round(lh * cut.width / cut.height))
        smooth_downscale(cut, lw, lh).save(dest)
        print(f"[{biome}/{piece}] wrote {lw}x{lh}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
