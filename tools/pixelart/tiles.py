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

# --- designed-tile craft (PRD §11.1 criterion 7): intentional pixel art with
# a light source, value ramps, ordered dithering (never per-pixel RNG fills),
# and hand-placed motifs. Local higher-contrast ramps (not the muddy near-black
# fills the noise tiles used) so grass reads as grass, water as water.
_GREEN = [_c for _c in (  # dark -> light moss/turf ramp
    (0x20, 0x33, 0x1e, 255), (0x2f, 0x50, 0x2b, 255), (0x3f, 0x6f, 0x36, 255),
    (0x5a, 0x93, 0x46, 255), (0x7c, 0xb8, 0x5a, 255),
)]
_SALT = [_c for _c in (  # bone/salt road ramp
    (0x4b, 0x46, 0x38, 255), (0x6f, 0x67, 0x54, 255), (0x9c, 0x92, 0x7a, 255),
    (0xcf, 0xc6, 0xae, 255), (0xf1, 0xec, 0xdd, 255),
)]
_AQUA = [_c for _c in (  # abyss depth ramp
    (0x0b, 0x22, 0x33, 255), (0x15, 0x3a, 0x52, 255), (0x1f, 0x6f, 0x77, 255),
    (0x49, 0xc6, 0xbd, 255), (0x9f, 0xe8, 0xe0, 255),
)]
_STONE = [_c for _c in (  # wet stone ramp
    (0x23, 0x28, 0x30, 255), (0x3a, 0x43, 0x4f, 255), (0x58, 0x64, 0x70, 255),
    (0x97, 0xa2, 0xae, 255), (0xcc, 0xd4, 0xdc, 255),
)]

# 4x4 ordered (Bayer) dither matrix, values 0..15 -> smooth ramp transitions.
_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def _img() -> tuple[Image.Image, object]:
    im = Image.new("RGBA", (T, T), (0, 0, 0, 255))
    return im, im.load()


def _wrapx(x: int) -> int:
    return x % T


def _dither(px, x: int, y: int, lo, hi, level: int) -> None:
    """Place hi where the Bayer threshold is below `level` (0..16), else lo --
    an ordered dither between two ramp steps, seamless and grain-free."""
    px[x % T, y % T] = hi if _BAYER[y % 4][x % 4] < level else lo


def grass() -> Image.Image:
    """Rot-moss turf, designed: a top-lit dithered green base, soft darker soil
    patches, and hand-placed blade tufts with lit tips -- reads as turf, moody
    but not muddy."""
    im, px = _img()
    # uniform dithered base (no per-tile gradient -> no banding when tiled)
    for y in range(T):
        for x in range(T):
            _dither(px, x, y, _GREEN[1], _GREEN[2], 6)
    # soft darker soil dapple (deterministic circular patches, wrapped)
    for (cx, cy, r) in ((4, 12, 3), (12, 5, 3), (9, 14, 2), (14, 10, 2)):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    _dither(px, x, y, _GREEN[0], _GREEN[1], 7)
    # blade tufts: dark base, bright lit tip (hand-placed, wrap-safe)
    for (bx, by) in ((3, 11), (7, 14), (10, 6), (13, 13), (5, 4), (14, 3), (1, 8)):
        for dx, h in ((-1, 2), (0, 3), (1, 2)):
            x = (bx + dx) % T
            for k in range(h):
                y = (by - k) % T
                px[x, y] = _GREEN[4] if k == h - 1 else _GREEN[3] if k == h - 2 else _GREEN[1]
    # a pebble + a tiny flower for a focal fleck
    px[8, 10] = _SALT[1]; px[9, 10] = _SALT[0]
    px[11, 9] = (0xf0, 0xa6, 0xc0, 255); px[11, 8] = (0xf4, 0xd2, 0x7a, 255)
    return im


def path() -> Image.Image:
    """Salt/bone road: staggered brick with a top-lit lip, shaded underside,
    dark mortar, and light dither in each face. 8x4 bricks, half-offset per
    course -- both divide 16 so it tiles seamlessly."""
    im, px = _img()
    mort = _SALT[0]
    for y in range(T):
        course = y // 4
        offset = (course % 2) * 4
        for x in range(T):
            if y % 4 == 0 or (x + offset) % 8 == 0:
                px[x, y] = mort  # mortar grid
            elif y % 4 == 1:
                px[x, y] = _SALT[4] if (x + offset) % 8 in (1, 2) else _SALT[3]  # top-lit lip
            elif y % 4 == 3:
                px[x, y] = _SALT[1]  # shaded underside
            else:
                _dither(px, x, y, _SALT[2], _SALT[3], 5)  # brick face
    # a hairline crack down one brick + a couple of moss specks in the mortar
    cx = 3
    for y in range(5, 11):
        px[_wrapx(cx), y] = _SALT[0]
        cx += (y % 2)
    px[0, 6] = _GREEN[1]; px[8, 10] = _GREEN[1]
    return im


def water() -> Image.Image:
    """The abyss: a vertical depth gradient (dark bottom -> teal top) with
    hand-placed horizontal wave crests and pearl foam highlights."""
    im, px = _img()
    # uniform mid-depth base (no per-tile gradient -> seamless in big bodies)
    for y in range(T):
        for x in range(T):
            _dither(px, x, y, _AQUA[1], _AQUA[2], 6)
    # wave crests: bright teal lines with a foam glint, offset per row (wrap)
    for (cy, phase) in ((3, 0), (8, 3), (12, 6), (15, 1)):
        for x in range(T):
            y = (cy + (1 if (x + phase) % 6 < 2 else 0)) % T
            px[x, y] = _AQUA[3]
            if (x + phase) % 6 == 0:
                px[x, (y - 1) % T] = _AQUA[4]  # foam highlight
    return im


def rock() -> Image.Image:
    """Wet dark stone: a dithered base with hand-placed faceted boulders --
    each a lit top-left plane, mid body, and dark bottom-right, with a rim and
    moss in the seams."""
    im, px = _img()
    for y in range(T):
        for x in range(T):
            _dither(px, x, y, _STONE[0], _STONE[1], 6)
    for (cx, cy, r) in ((5, 6, 4), (11, 11, 5), (13, 3, 3)):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if d2 > r * r:
                    continue
                xx, yy = x % T, y % T
                s = (x - cx) + (y - cy)
                if d2 >= (r - 0) ** 2 - 1:
                    px[xx, yy] = _STONE[0]  # rim
                elif s < -r // 2:
                    px[xx, yy] = _STONE[3]  # top-left lit
                elif s > r // 2:
                    px[xx, yy] = _STONE[1]  # bottom-right shade
                else:
                    px[xx, yy] = _STONE[2]  # body
    # moss in the seams between boulders
    for (mx, my) in ((8, 8), (2, 12), (14, 9), (9, 1)):
        px[mx % T, my % T] = _GREEN[1]
    return im


def build() -> Image.Image:
    tiles = [grass(), path(), water(), rock()]
    sheet = Image.new("RGBA", (T * 4, T), (0, 0, 0, 0))
    for i, t in enumerate(tiles):
        sheet.alpha_composite(t, (i * T, 0))
    return sheet


# --- multi-region variants (PRD §8.8 / world-bible §5b) --------------------
# One dominant accent hue per region (matching each region's arena, §11.1.1)
# tinted over the same 4 base tiles, so the explorable world visually
# telegraphs which movement you're approaching without redrawing from
# scratch. Order matches the campaign graph: Shallows -> Salt Mines ->
# Pit Below -> Attic of Teeth -> Conductor's Hall.
REGIONS = ["shallows", "saltmines", "pit", "attic", "hall"]
REGION_ACCENT: dict[str, tuple] = {
    "shallows": PALETTE["C"],
    "saltmines": PALETTE["o"],
    "pit": PALETTE["P"],
    "attic": PALETTE["r"],
    "hall": PALETTE["p"],
}


def _tint(img: Image.Image, accent: tuple, amt: float) -> Image.Image:
    px = img.load()
    for y in range(T):
        for x in range(T):
            c = px[x, y]
            px[x, y] = tuple(round(c[i] + (accent[i] - c[i]) * amt) for i in range(3)) + (255,)
    return img


def region_tiles(region: str) -> list[Image.Image]:
    accent = REGION_ACCENT[region]
    return [
        _tint(grass(), accent, 0.38),
        _tint(path(), accent, 0.24),
        _tint(water(), accent, 0.48),
        _tint(rock(), accent, 0.32),
    ]


def build_multi_region() -> Image.Image:
    """One row of 4 tiles (grass/path/water/rock) per region, 20 tiles total,
    tile id = region_index*4 + {0,1,2,3} -- the convention the overworld
    generator and OverworldScene both key off of."""
    sheet = Image.new("RGBA", (T * 4 * len(REGIONS), T), (0, 0, 0, 0))
    for ri, region in enumerate(REGIONS):
        for ti, tile in enumerate(region_tiles(region)):
            sheet.alpha_composite(tile, ((ri * 4 + ti) * T, 0))
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
