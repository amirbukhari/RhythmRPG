"""Overworld tileset: 4 hand-tuned, seamlessly-tiling 16x16 tiles in the
Skatopia palette. Keeps the same tile order (grass, path, water, rock) and
collision (water/rock) the existing assets/tilemaps/overworld.json expects,
so this is a pure art upgrade over the old flat-colour tiles.

Tiles are painted procedurally but deterministically (fixed seed, all feature
placement wraps modulo 16 so 4x4 tiling has no seams). Still "just pixels" --
authored here, rendered to PNG, committed.
"""

from __future__ import annotations

import random
from PIL import Image
from skatopia import PALETTE, save

T = 16


def _img() -> tuple[Image.Image, object]:
    im = Image.new("RGBA", (T, T), (0, 0, 0, 255))
    return im, im.load()


def _wrapx(x: int) -> int:
    return x % T


def grass() -> Image.Image:
    """Dark rot-moss turf -- moody and desaturated for the Skatopia mood, not
    a cheerful meadow: near-black moss base, a few sick-olive blades, rot specks."""
    rng = random.Random(11)
    im, px = _img()
    # base leans on the darkest greens + ink so the world reads gothic
    base = [PALETTE["S"], PALETTE["g"], PALETTE["k"], PALETTE["S"], PALETTE["d"]]
    for y in range(T):
        for x in range(T):
            px[x, y] = base[(x * 3 + y * 5 + rng.randint(0, 4)) % len(base)]
    # sparse blades: mostly dark, only the occasional living tip
    for _ in range(18):
        x = rng.randrange(T)
        y = rng.randrange(2, T)
        px[x, y] = PALETTE["S"]
        px[x, y - 1] = PALETTE["g"] if rng.random() < 0.7 else PALETTE["s"]
    for _ in range(3):
        px[rng.randrange(T), rng.randrange(T)] = PALETTE["G"]  # a rare bright shoot
    # rot specks (dried blood / decay)
    for _ in range(4):
        px[rng.randrange(T), rng.randrange(T)] = PALETTE["Y"]
    return im


def path() -> Image.Image:
    """Salt/bone road: pale staggered brickwork ('turning to salt'), dark
    mortar, a top-lit face on each brick. 8x4 bricks, half-offset per course,
    both dividing 16 so it tiles seamlessly."""
    rng = random.Random(23)
    im, px = _img()
    for y in range(T):
        for x in range(T):
            px[x, y] = PALETTE["w"]
    for y in range(T):
        course = y // 4
        offset = (course % 2) * 4
        for x in range(T):
            horizontal = (y % 4 == 0)
            vertical = ((x + offset) % 8 == 0)
            if horizontal or vertical:
                px[x, y] = PALETTE["V"]
            elif y % 4 == 1:
                px[x, y] = PALETTE["W"]  # top-lit lip of each brick
            elif y % 4 == 3:
                px[x, y] = PALETTE["v"]  # shaded underside
    # weathering: a crack across one brick, scattered salt pitting
    cx = 3
    for y in range(5, 11):
        px[_wrapx(cx), y] = PALETTE["V"]
        cx += rng.choice([0, 1, 1])
    for _ in range(6):
        px[rng.randrange(T), rng.randrange(T)] = PALETTE["v"]
    return im


def water() -> Image.Image:
    """The abyss: deep at the bottom, teal ripples, pearl glints -- 'live in the ocean'."""
    rng = random.Random(37)
    im, px = _img()
    for y in range(T):
        # vertical depth gradient
        band = PALETTE["E"] if y > 10 else PALETTE["e"] if y > 4 else PALETTE["c"]
        for x in range(T):
            px[x, y] = band
    # horizontal ripple strokes (wrap in x)
    for _ in range(14):
        y = rng.randrange(T)
        x0 = rng.randrange(T)
        ln = rng.randint(2, 4)
        col = PALETTE["c"] if y < 8 else PALETTE["e"]
        for i in range(ln):
            px[_wrapx(x0 + i), y] = col
    # bright glints near the surface
    for _ in range(5):
        px[rng.randrange(T), rng.randrange(0, 6)] = PALETTE["C"]
    return im


def rock() -> Image.Image:
    """Wet dark stone with moss in the seams and a top-lit face."""
    rng = random.Random(53)
    im, px = _img()
    for y in range(T):
        for x in range(T):
            px[x, y] = PALETTE["m"] if (x + y) % 2 or rng.random() < 0.5 else PALETTE["N"]
    # blocky facets: lighter tops, darker undersides
    for _ in range(5):
        bx, by = rng.randrange(T), rng.randrange(2, T - 2)
        bw, bh = rng.randint(4, 7), rng.randint(3, 5)
        for y in range(by, min(T, by + bh)):
            for x in range(bx, bx + bw):
                xx = _wrapx(x)
                if y == by:
                    px[xx, y] = PALETTE["M"]
                elif y == by + bh - 1:
                    px[xx, y] = PALETTE["N"]
                else:
                    px[xx, y] = PALETTE["m"]
    # broken rim highlights (not a full row -> no stripe when tiled) + moss
    for _ in range(7):
        x = rng.randrange(T)
        px[x, rng.randrange(0, 2)] = PALETTE["L"]
    for _ in range(12):
        px[rng.randrange(T), rng.randrange(T)] = PALETTE["g"]
    return im


def build() -> Image.Image:
    tiles = [grass(), path(), water(), rock()]
    sheet = Image.new("RGBA", (T * 4, T), (0, 0, 0, 0))
    for i, t in enumerate(tiles):
        sheet.alpha_composite(t, (i * T, 0))
    return sheet


def preview(sheet: Image.Image) -> Image.Image:
    """A 4x4 tiled swatch of each tile so seams are visible at review time."""
    prev = Image.new("RGBA", (T * 4 * 4, T * 4), (0, 0, 0, 0))
    for i in range(4):
        tile = sheet.crop((i * T, 0, i * T + T, T))
        for gy in range(4):
            for gx in range(4):
                prev.alpha_composite(tile, (i * T * 4 + gx * T, gy * T))
    return prev


if __name__ == "__main__":
    sheet = build()
    p = save(sheet, "tilemaps/overworld_tileset.png")
    print("wrote", p)
    prev = preview(sheet)
    prev.save("/tmp/claude-0/-home-user-RhythmRPG/ca0ffd81-5d91-5caa-9e7d-445166acf3ed/scratchpad/tiles_preview.png")
    print("preview written")
