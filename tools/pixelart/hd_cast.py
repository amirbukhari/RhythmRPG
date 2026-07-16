"""HD cast + foes (PRD v11.0 beauty pivot): regenerate the playable
character and the bestiary as PAINTERLY high-fidelity sprites -- the pixel
crunch (pixelate/quantize/outline/bake) is retired; art is imported at 4x
the old frame sizes and rendered smooth, downscaled by the engine.

Slots + frame contracts (BootScene must match):
    band/mir/{idle,run,attack}.png     200x200 frames (was 50)
    enemies/slime.png                  128x128 x2     (was 32)
    enemies/drifter.png                140x140 x2     (was 35)
    enemies/elite_wraith.png           180x180 x2     (was 45)
    enemies/the_conductor.png          192x192 x2     (was 48)
    enemies/conductor_colossal.png     208x288 x2     (was 52x72)

Animation strips derive from ONE base pose per character (identity
stability), same transforms as the pixel era, scaled to the HD grid.

Usage:
  python tools/pixelart/hd_cast.py            # everything
  python tools/pixelart/hd_cast.py mir slime  # specific pieces
  SEED_OFFSET=3 python ...                    # reroll variants
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from generate_ai import gen_pollinations  # noqa: E402
from import_asset import flood_key  # noqa: E402
from newband import autocrop, keep_main_island, scrub_mist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

# Pieces whose art contains large pale/white areas (bone crowns, pearl teeth)
# key against a grey generation backdrop instead of white, or the flood key
# eats the figure (the wraith shredded on white).
GREY_BG = {"elite_wraith"}

# One shared painterly clause so the whole cast reads as one game.
# Register: HYPER LIGHT DRIFTER — vivid, luminous, saturated (owner: "you're
# generating shit way too dark. it's gotta be like hyperlite drifter").
# Darkness is an accent for contrast, never the body of the figure.
STYLE = (
    "beautiful game character art in the style of Hyper Light Drifter, "
    "painterly digital illustration, VIVID saturated neon-tinged colors: "
    "luminous cyan-teal, hot magenta-pink, ember gold, coral red, glowing "
    "accents and bright rim light, colorful and radiant against small deep "
    "indigo shadow accents, NOT dark, NOT murky, NOT monochrome, "
    "full body SIDE VIEW facing LEFT, standing, feet planted, centered, "
    "isolated on a plain pure white background, NO ground, NO floor, NO cast "
    "shadow, NO fog, NO mist, NO text, NO border, "
)

# id -> (subject, seed, out path, frame (w,h), figure height in frame)
PIECES: dict[str, tuple[str, int, str, tuple[int, int], int]] = {
    "mir": (
        STYLE + "a wandering guitarist hero named Mir, lean and nimble, a flowing "
        "LUMINOUS CYAN-TEAL cloak-jacket over deep indigo underlayers, pale "
        "teal-tinged skin, short dark hair, a BRIGHT CORAL-RED electric "
        "guitar slung low across his body, determined expression",
        11, "assets/sprites/band/mir", (200, 200), 176,
    ),
    "slime": (
        STYLE + "a hulking amorphous SLIME BLOB monster, a heaped glistening mound "
        "of GLOWING radioactive TOXIC TEAL-GREEN ooze lit from within, no "
        "legs, no humanoid shape, one wide jagged maw of pearl-white teeth, "
        "dripping luminous strands of goo",
        561, "assets/sprites/enemies/slime.png", (128, 128), 104,
    ),
    "drifter": (
        STYLE + "a gaunt drowned wanderer ghost wrapped in a BLAZING SATURATED "
        "BURNT-ORANGE hooded greatcoat with gold trim, glowing cyan void "
        "where the face should be, trailing luminous tatters",
        231, "assets/sprites/enemies/drifter.png", (140, 140), 122,
    ),
    "elite_wraith": (
        STYLE + "a regal terrifying wraith in flowing VIVID ELECTRIC-VIOLET and "
        "magenta funeral robes, a crown of pale glowing bone, feather-like "
        "white hair drifting upward as if underwater, a too-wide mouth of "
        "pearl teeth, hot pink inner glow, ONE single connected figure",
        154, "assets/sprites/enemies/elite_wraith.png", (180, 180), 158,
    ),
    "the_conductor": (
        STYLE + "THE CONDUCTOR: a gaunt spectral Victorian orchestra conductor in "
        "a deep indigo-plum tailcoat with BLAZING EMBER-GOLD trim and tall "
        "top hat, an exposed RADIANT glowing amber clock face embedded in "
        "his chest casting warm light up his figure, one skeletal hand "
        "raising a conductor's baton",
        4, "assets/sprites/enemies/the_conductor.png", (192, 192), 170,
    ),
    "conductor_colossal": (
        STYLE + "THE CONDUCTOR as a COLOSSUS: a towering gaunt spectral Victorian "
        "orchestra conductor in a vast tattered deep indigo-plum tailcoat "
        "with BLAZING EMBER-GOLD trim flaring like smoke, tall top hat, a "
        "RADIANT glowing amber clock face embedded in the chest casting "
        "warm light across the figure, skeletal hand raising a baton, "
        "monumental and terrifying",
        4, "assets/sprites/enemies/conductor_colossal.png", (208, 288), 272,
    ),
}


def shift(img: Image.Image, dx: int, dy: int) -> Image.Image:
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(img, (dx, dy))
    return out


def split_y(img: Image.Image, y: int) -> tuple[Image.Image, Image.Image]:
    top = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bot = Image.new("RGBA", img.size, (0, 0, 0, 0))
    top.alpha_composite(img.crop((0, 0, img.width, y)), (0, 0))
    bot.alpha_composite(img.crop((0, y, img.width, img.height)), (0, y))
    return top, bot


def fit_to_frame(fig: Image.Image, frame: tuple[int, int], fig_h: int) -> Image.Image:
    fig = autocrop(fig)
    s = fig_h / fig.height
    w = max(1, round(fig.width * s))
    fig = fig.resize((w, fig_h), Image.LANCZOS)
    fw, fh = frame
    foot_y = fh - max(2, fh // 50)
    out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    out.alpha_composite(fig, ((fw - w) // 2, foot_y - fig_h))
    return out


def pack(frames: list[Image.Image]) -> Image.Image:
    fw, fh = frames[0].size
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * fw, 0))
    return sheet


def breathe(base: Image.Image, fig_h: int) -> Image.Image:
    """Idle frame 2: the torso settles -- the HD version of the 1px breath."""
    foot_y = base.height - max(2, base.height // 50)
    hips = foot_y - fig_h // 2
    d = max(2, fig_h // 60)
    top, bot = split_y(base, hips)
    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out.alpha_composite(shift(top, 0, d))
    out.alpha_composite(bot)
    return out


def run_frames(base: Image.Image, fig_h: int) -> list[Image.Image]:
    foot_y = base.height - max(2, base.height // 50)
    hips = foot_y - fig_h // 2
    knees = foot_y - fig_h // 4
    u = max(2, fig_h // 44)  # the HD unit step (was 1px at 66px figures)
    frames: list[Image.Image] = []
    for i, (bob, legs) in enumerate([(0, 1), (-1, 0), (0, -1), (-1, 0)]):
        top, bot = split_y(base, hips)
        upper = shift(top, -u, bob * u)
        thighs, feet = split_y(bot, knees)
        stride = shift(thighs, 0, bob * u), shift(feet, legs * u, max(0, (bob + (1 if i % 2 else 0)) * u))
        out = Image.new("RGBA", base.size, (0, 0, 0, 0))
        out.alpha_composite(stride[0])
        out.alpha_composite(stride[1])
        out.alpha_composite(upper)
        frames.append(out)
    return frames


def attack_frames(base: Image.Image, fig_h: int) -> list[Image.Image]:
    foot_y = base.height - max(2, base.height // 50)
    hips = foot_y - fig_h // 2
    u = max(2, fig_h // 44)
    top, bot = split_y(base, hips)
    windup = Image.new("RGBA", base.size, (0, 0, 0, 0))
    windup.alpha_composite(shift(top, 2 * u, 0))
    windup.alpha_composite(bot)
    swing = Image.new("RGBA", base.size, (0, 0, 0, 0))
    swing.alpha_composite(shift(top, -3 * u, u))
    swing.alpha_composite(shift(bot, -u, 0))
    recover = Image.new("RGBA", base.size, (0, 0, 0, 0))
    recover.alpha_composite(shift(top, -u, 0))
    recover.alpha_composite(bot)
    return [windup, swing, recover]


def build(piece: str) -> None:
    subject, seed, out, frame, fig_h = PIECES[piece]
    seed += int(os.environ.get("SEED_OFFSET", "0"))
    gw, gh = (768, 1024) if frame[1] > frame[0] else (768, 768)
    print(f"[{piece}] generating (seed {seed}) ...", flush=True)
    if piece in GREY_BG:
        subject = subject.replace("plain pure white background", "plain solid flat MID-GREY background")
    raw = gen_pollinations(subject, gw, gh, seed=seed)
    src = Image.open(io.BytesIO(raw)).convert("RGBA")
    cut = scrub_mist(autocrop(flood_key(src, tol=60)))
    cut = autocrop(keep_main_island(cut))
    base = fit_to_frame(cut, frame, fig_h)

    dst = ROOT / out
    if piece == "mir":
        dst.mkdir(parents=True, exist_ok=True)
        pack([base, breathe(base, fig_h)]).save(dst / "idle.png")
        pack(run_frames(base, fig_h)).save(dst / "run.png")
        pack(attack_frames(base, fig_h)).save(dst / "attack.png")
        print(f"[{piece}] wrote idle(2f)/run(4f)/attack(3f) -> {dst}")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        pack([base, breathe(base, fig_h)]).save(dst)
        print(f"[{piece}] wrote 2f idle -> {dst}")


def main() -> None:
    only = set(sys.argv[1:])
    for piece in PIECES:
        if only and piece not in only:
            continue
        build(piece)


if __name__ == "__main__":
    main()
