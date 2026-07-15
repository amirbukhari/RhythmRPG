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
from import_asset import flood_key, pixelate, smooth_downscale  # noqa: E402
from newband import autocrop, keep_main_island, scrub_mist, fit_to_frame, breathe, pack  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "enemies"

# The first pass's shared "dark teal and rust palette" clause homogenized the
# bestiary into three near-identical hooded ghosts (the same failure mode the
# band had). Same fix: each foe gets a DISTINCT silhouette and one bold
# signature colour that dominates it.
STYLE = (
    "16-bit video game enemy sprite, bold menacing silhouette, chunky pixels, "
    "flat cel shading, drowned gothic horror, ONE bold saturated signature "
    "colour dominating the creature, full body SIDE VIEW facing LEFT, "
)

FOES: dict[str, tuple[str, int]] = {
    "slime": (
        STYLE + "hulking amorphous SLIME BLOB creature, a heaped mound of "
        "luminous translucent TOXIC TEAL-GREEN ooze with no legs and no "
        "humanoid shape, one wide jagged dark mouth of pearl-white teeth, "
        "dripping goo",
        561,
    ),
    "drifter": (
        STYLE + "gaunt drowned wanderer ghost in a waterlogged RUST-ORANGE "
        "long coat, kelp tangled around the arms, hunched and reaching "
        "forward, glowing pale eyes",
        562,
    ),
    "elite_wraith": (
        STYLE + "tall regal spectral wraith in flowing VIOLET-PURPLE tattered "
        "robes fading to mist below the waist, BONE-WHITE crown of pearl "
        "teeth, long clawed fingers raised",
        563,
    ),
}


def build(foe: str, subject: str, seed: int) -> None:
    print(f"[{foe}] generating (seed {seed}) ...", flush=True)
    raw = gen_pollinations(SPRITE_PREFIX + subject, 768, 768, seed=seed)
    src = Image.open(io.BytesIO(raw)).convert("RGBA")
    cut = autocrop(keep_main_island(scrub_mist(autocrop(flood_key(src, tol=60)))))
    ar = cut.width / cut.height
    lh = 66
    lw = max(16, min(48, round(lh * ar)))
    fig = smooth_downscale(cut, lw, lh)
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
