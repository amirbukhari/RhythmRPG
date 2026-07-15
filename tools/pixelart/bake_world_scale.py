"""Bake world scale INTO the art (owner: "still pixelly as fuck and when I
look at HLD it's not"). Root cause: pieces rendered at fractional scales
(0.28-1.6 from WorldScale.ts), so every sprite had different-sized,
non-integer pixels -- uneven gritty texels instead of HLD's uniform chunky
ones. This tool resamples every environment piece to its CANONICAL world
size (the same metre table as WorldScale.ts -- keep them in sync), so at
runtime everything draws at scale ~1.0: one texel = one world pixel,
everywhere.

Run AFTER any generation batch, BEFORE fidelity_pass.py.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from import_asset import smooth_downscale  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ENV = ROOT / "assets" / "sprites" / "env"

PX_PER_METER = 15
MIN_PX = 9

# mirror of src/scenes/env/WorldScale.ts METERS -- keep in sync
METERS: list[tuple[str, float]] = [
    ("ticket_booth", 3.2), ("tent_pole", 3.4), ("carousel_horse", 2.2),
    ("melting_clock", 2.5), ("save_obelisk", 2.4), ("calcified_miner", 1.9),
    ("figurehead", 1.9), ("dockpost", 2.4), ("_lantern$", 2.2),
    ("scatter_lantern", 0.5), ("_pillar$", 2.4), ("scatter_pillar", 1.6),
    ("_timber$", 2.4), ("oil_lamp", 1.8), ("torch", 1.9), ("scatter_scale", 1.9),
    ("scatter_flag$", 2.0), ("pennant", 2.0), ("chandelier$", 2.0),
    ("scatter_chandelier", 0.8), ("candelabra", 1.7), ("harpoon", 1.7),
    ("scatter_sign", 1.7), ("salt_crystal", 1.8), ("plinth", 1.6),
    ("piling", 1.6), ("scatter_bell$", 1.6), ("telescope", 1.5),
    ("scatter_lamp$", 1.4), ("ladder", 2.0), ("beam", 1.8), ("harp$", 1.5),
    ("crate_stack", 1.5), ("music_stand", 1.4), ("ringpost", 1.4),
    ("stand$", 1.3), ("cello", 1.4), ("ore_cart", 1.3), ("scatter_cart", 1.3),
    ("winch", 1.3), ("reedclump|reeds$", 1.25), ("drawers", 1.3),
    ("stalagmite", 1.4), ("crystal", 1.4), ("boat$", 1.4), ("cage$", 1.2),
    ("birdcage$", 1.1), ("umbrellas", 1.1), ("brazier", 1.1),
    ("rocking_chair", 1.1), ("oar", 1.3), ("anchor", 1.3), ("skiff", 1.0),
    ("stake", 1.0), ("chair", 1.0), ("poster", 1.5), ("globe", 1.0),
    ("phonograph|gramophone", 0.95), ("portraits", 1.0), ("net$", 1.0),
    ("pew|bench", 0.9), ("barrel", 0.9), ("drum", 0.9), ("keg", 0.8),
    ("wheel", 0.9), ("ore_rock", 0.9), ("pick$", 0.9), ("sewing", 0.9),
    ("pipe$", 0.9), ("scatter_frame", 0.95), ("bust", 0.85),
    ("rockinghorse", 0.8), ("crate$|seacrate", 0.8), ("campfire", 0.75),
    ("lyre", 0.7), ("trunk|seachest", 0.7), ("marble", 0.7),
    ("buoy|lifering", 0.65), ("coral", 0.6), ("plaque", 0.7), ("violin", 0.6),
    ("gear$", 0.6), ("horn$", 0.6), ("sacks", 0.65), ("chest$", 0.55),
    ("kelp|stone$|nodule", 0.5),
    ("geode|radio|hatbox|clock$|tub$|belljar|shiplantern|drape|rubble", 0.5),
    ("mirror|plank|driftwood|ore$|rope$|rope_coil|bucket|weights|jar$|hourglass|tidepool|books", 0.42),
    ("metronome|quill|megaphone|doll|musicbox|typewriter|candles", 0.35),
    ("mask|bottle|glove|chain|bones|rail|candle$|shells|streamer", 0.3),
    ("goblet|votives|baton|sheets|page_stack|operamask|ticket$|starfish|crab|teacup", 0.22),
]

LANDFORM_SCALE = 0.78  # landforms bake at their long-standing render scale


def target_height(key: str, h: int) -> int:
    if "landform_" in key:
        return max(24, round(h * LANDFORM_SCALE))
    meters = 0.5
    for pat, m in METERS:
        if re.search(pat, key):
            meters = m
            break
    boost = 1.5 if meters <= 0.5 else (1.15 if meters <= 1 else 1)
    return max(MIN_PX, round(meters * PX_PER_METER * boost))


def main() -> int:
    n = 0
    for p in sorted(ENV.rglob("*.png")):
        key = f"env_{p.parent.name}_{p.stem}"
        im = Image.open(p).convert("RGBA")
        th = target_height(key, im.height)
        if abs(th - im.height) <= 1:
            continue
        tw = max(4, round(im.width * th / im.height))
        if th > im.height:
            # upscale: LANCZOS then fidelity_pass re-pixels at the final res
            im.resize((tw, th), Image.LANCZOS).save(p)
        else:
            smooth_downscale(im, tw, th).save(p)
        n += 1
    print(f"baked world scale into {n} pieces")
    return 0


if __name__ == "__main__":
    sys.exit(main())
