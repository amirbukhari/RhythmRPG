"""Generate Mir, the playable character (PRD v10.0 solo pivot; formerly the
four-piece band tool -- bassist/vocalist/drummer were retired with the band
fiction, and the lead slot was renamed amir -> mir).

ONE AI generation (a full-body, side-view, left-facing musician on
a plain white background -- the proven Pollinations sprite path), flood-keyed,
pixelated to the engine's 48x48 frame on the master palette (band cohesion),
then the animation strips are DERIVED procedurally from that base pose --
breathing idle (2f), bobbing/leaning run (4f), windup/swing/recover attack (3f).
One consistent source pose per member keeps identity rock-solid across frames,
which per-frame AI generation cannot do.

Output: assets/sprites/band/<member>/{idle,run,attack}.png -- the exact slots
the engine already loads (band_<member>[_run|_attack]), so no code changes.

Usage:
  python tools/pixelart/newband.py       # regenerate Mir
  SEED_OFFSET=3 python ...                    # reroll variants
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from generate_ai import SPRITE_PREFIX, gen_pollinations  # noqa: E402
from import_asset import flood_key, pixelate, smooth_downscale  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "band"

FRAME = 72  # engine frame size (BootScene loads 72x72; AAA legibility pass)
FIG_H = 66  # figure height inside the frame (feet anchored near the bottom)
FOOT_Y = 69  # baseline the feet sit on

# The shared style clause that kept the cast in one register; kept for Mir
# (and any future story figure -- Nari/Lunal staging art should reuse it).
STYLE = (
    "16-bit video game character sprite, bold clean silhouette, chunky pixels, "
    "flat cel shading, gothic drowned-rock musician, pale teal-tinged skin, "
    "ONE bold saturated signature costume colour dominating the outfit, "
    "standing full body SIDE VIEW facing LEFT, both feet visible and planted, "
    "NO fog, NO mist, NO smoke, NO ground, NO pedestal, NO base under the feet, "
)

MEMBERS: dict[str, tuple[str, int]] = {
    # member -> (subject prompt, seed)
    "mir": (
        STYLE + "lead guitarist playing a rusted BRIGHT RED electric guitar slung low, "
        "tall BRIGHT TEAL mohawk, NO hood, bare arms, black leather vest with teal trim",
        11,
    ),
}


def autocrop(img: Image.Image) -> Image.Image:
    box = img.getbbox()
    return img.crop(box) if box else img


def scrub_mist(img: Image.Image) -> Image.Image:
    """Flux insists on drawing pale fog around a 'drowned gothic' figure's legs
    no matter how the prompt forbids it. Remove near-white, low-saturation
    pixels in the lower 45% of the cutout -- the characters wear dark boots, so
    only the mist matches."""
    img = img.copy()
    px = img.load()
    w, h = img.size
    for y in range(int(h * 0.4), h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and min(r, g, b) > 175 and max(r, g, b) - min(r, g, b) < 34:
                px[x, y] = (0, 0, 0, 0)
    return img


def keep_main_island(img: Image.Image) -> Image.Image:
    """Drop small disconnected opaque islands (floating headstock specks, drum
    fragments): keep only components >= 8% of the largest one's area."""
    img = img.copy()
    w, h = img.size
    px = img.load()
    label = [0] * (w * h)
    sizes: list[int] = [0]  # sizes[k] = area of component k
    nxt = 1
    for sy in range(h):
        for sx in range(w):
            i0 = sy * w + sx
            if label[i0] or px[sx, sy][3] == 0:
                continue
            stack = [(sx, sy)]
            label[i0] = nxt
            area = 0
            while stack:
                x, y = stack.pop()
                area += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                    nx2, ny2 = x + dx, y + dy
                    if 0 <= nx2 < w and 0 <= ny2 < h:
                        j = ny2 * w + nx2
                        if not label[j] and px[nx2, ny2][3] != 0:
                            label[j] = nxt
                            stack.append((nx2, ny2))
            sizes.append(area)
            nxt += 1
    if nxt <= 2:
        return img
    biggest = max(sizes)
    keep = {k for k, s in enumerate(sizes) if s >= biggest * 0.08}
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and label[y * w + x] not in keep:
                px[x, y] = (0, 0, 0, 0)
    return img


def fit_to_frame(fig: Image.Image) -> Image.Image:
    """Scale the cutout to FIG_H tall and anchor its feet at FOOT_Y, centered."""
    fig = autocrop(fig)
    scale = FIG_H / fig.height
    w = max(1, round(fig.width * scale))
    fig = fig.resize((w, FIG_H), Image.LANCZOS)
    frame = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    frame.alpha_composite(fig, ((FRAME - w) // 2, FOOT_Y - FIG_H))
    return frame


def shift(img: Image.Image, dx: int, dy: int) -> Image.Image:
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(img, (dx, dy))
    return out


def split_y(img: Image.Image, y: int) -> tuple[Image.Image, Image.Image]:
    """(top part above y, bottom part from y down), each on a full-size canvas."""
    top = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bot = Image.new("RGBA", img.size, (0, 0, 0, 0))
    top.alpha_composite(img.crop((0, 0, img.width, y)), (0, 0))
    bot.alpha_composite(img.crop((0, y, img.width, img.height)), (0, y))
    return top, bot


def breathe(base: Image.Image) -> Image.Image:
    """Idle frame 2: the torso settles 1px -- a pixel-art breath."""
    hips = FOOT_Y - FIG_H // 2
    top, bot = split_y(base, hips)
    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out.alpha_composite(shift(top, 0, 1))
    out.alpha_composite(bot)
    return out


def run_frames(base: Image.Image) -> list[Image.Image]:
    """4-frame run: body bob + forward lean + alternating leg scissor. The art
    faces LEFT, so 'forward' is -x."""
    hips = FOOT_Y - FIG_H // 2
    knees = FOOT_Y - FIG_H // 4
    frames: list[Image.Image] = []
    for i, (bob, legs) in enumerate([(0, 1), (-1, 0), (0, -1), (-1, 0)]):
        top, bot = split_y(base, hips)
        upper = shift(top, -1, bob)  # constant forward lean + bob
        thighs, feet = split_y(bot, knees)
        stride = shift(thighs, 0, bob), shift(feet, legs, max(0, bob + (1 if i % 2 else 0)))
        out = Image.new("RGBA", base.size, (0, 0, 0, 0))
        out.alpha_composite(stride[0])
        out.alpha_composite(stride[1])
        out.alpha_composite(upper)
        frames.append(out)
    return frames


def attack_frames(base: Image.Image) -> list[Image.Image]:
    """3-frame attack: windup (rear back +x), swing (lunge -x, dip), recover."""
    hips = FOOT_Y - FIG_H // 2
    top, bot = split_y(base, hips)
    windup = Image.new("RGBA", base.size, (0, 0, 0, 0))
    windup.alpha_composite(shift(top, 2, 0))
    windup.alpha_composite(bot)
    swing = Image.new("RGBA", base.size, (0, 0, 0, 0))
    swing.alpha_composite(shift(top, -3, 1))
    swing.alpha_composite(shift(bot, -1, 0))
    recover = Image.new("RGBA", base.size, (0, 0, 0, 0))
    recover.alpha_composite(shift(top, -1, 0))
    recover.alpha_composite(bot)
    return [windup, swing, recover]


def pack(frames: list[Image.Image]) -> Image.Image:
    sheet = Image.new("RGBA", (FRAME * len(frames), FRAME), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * FRAME, 0))
    return sheet


def build(member: str, subject: str, seed: int) -> None:
    print(f"[{member}] generating (seed {seed}) ...", flush=True)
    raw = gen_pollinations(SPRITE_PREFIX + subject, 768, 768, seed=seed)
    src = Image.open(__import__("io").BytesIO(raw)).convert("RGBA")
    cut = flood_key(src, tol=60)
    # rich adaptive palette (per-member identity), no dither: crisp pixel read
    c = scrub_mist(autocrop(cut))
    c = autocrop(keep_main_island(c))
    ar = c.width / c.height
    lh = 66
    lw = max(16, min(48, round(lh * ar)))
    fig = smooth_downscale(c, lw, lh)
    base = fit_to_frame(fig)

    outdir = OUT / member
    outdir.mkdir(parents=True, exist_ok=True)
    pack([base, breathe(base)]).save(outdir / "idle.png")
    pack(run_frames(base)).save(outdir / "run.png")
    pack(attack_frames(base)).save(outdir / "attack.png")
    print(f"[{member}] wrote idle(2f)/run(4f)/attack(3f) -> {outdir}")


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    off = int(os.environ.get("SEED_OFFSET", "0"))
    for member, (subject, seed) in MEMBERS.items():
        if only and member != only:
            continue
        build(member, subject, seed + off)


if __name__ == "__main__":
    main()
