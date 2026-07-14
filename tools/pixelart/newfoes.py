"""Resprite the lyric foes in the SAME register as the new band (AAA audit
B3): the old enemy sheets predate the generation pipeline and read goofy
(beige googly-eyed slime) next to the new cast. One AI base pose per foe via
the proven sprite path + newband cleanup passes, then a 2-frame breathing idle
derived from the base -- exactly the strips `enemy_<id>` already loads
(96x48, 2 frames of 48x48). The colossal Conductor is intentionally NOT
touched (audit: it lands; don't churn).

Usage:
  python tools/pixelart/newfoes.py           # all three
  python tools/pixelart/newfoes.py slime     # one foe
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
from newband import autocrop, keep_main_island, scrub_mist, fit_to_frame, breathe, pack  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "enemies"

STYLE = (
    "16-bit video game enemy sprite, bold menacing silhouette, chunky pixels, "
    "flat cel shading, drowned gothic horror, dark teal and rust palette, "
    "full body SIDE VIEW facing LEFT, "
)

FOES: dict[str, tuple[str, int]] = {
    "slime": (
        STYLE + "heaving mound of black-green rot ooze with a jagged mouth of "
        "pearl-white teeth and small glowing teal eyes, dripping",
        61,
    ),
    "drifter": (
        STYLE + "gaunt drowned wanderer ghost, waterlogged long coat, kelp "
        "tangled around the arms, glowing pale eyes, reaching forward",
        62,
    ),
    "elite_wraith": (
        STYLE + "tall spectral wraith wearing a crown of pearl teeth, tattered "
        "flowing robes fading to mist below the waist, long clawed fingers",
        63,
    ),
}


def build(foe: str, subject: str, seed: int) -> None:
    print(f"[{foe}] generating (seed {seed}) ...", flush=True)
    raw = gen_pollinations(SPRITE_PREFIX + subject, 768, 768, seed=seed)
    src = Image.open(io.BytesIO(raw)).convert("RGBA")
    cut = autocrop(keep_main_island(scrub_mist(autocrop(flood_key(src, tol=60)))))
    ar = cut.width / cut.height
    lh = 44
    lw = max(16, min(48, round(lh * ar)))
    fig = pixelate(cut, lw, lh, dither=False, colors=28)
    base = fit_to_frame(fig)
    OUT.mkdir(parents=True, exist_ok=True)
    pack([base, breathe(base)]).save(OUT / f"{foe}.png")
    print(f"[{foe}] wrote 2-frame idle -> {OUT / (foe + '.png')}")


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    off = int(os.environ.get("SEED_OFFSET", "0"))
    for foe, (subject, seed) in FOES.items():
        if only and foe != only:
            continue
        build(foe, subject, seed + off)


if __name__ == "__main__":
    main()
