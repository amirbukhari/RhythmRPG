"""Standalone tests for import_asset.py (run: python3 test_import_asset.py).

Synthesizes 'generated' raw inputs -- off-palette colours, solid backdrops,
oversized -- and asserts the importer produces engine-ready output: correct
frame size, background keyed to transparent, and every opaque colour snapped
into the master palette.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from PIL import Image

import import_asset as I
from skatopia import PALETTE

MASTER = set(I.MASTER_RGB)
_fails: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("  PASS " if cond else "  FAIL ") + msg)
    if not cond:
        _fails.append(msg)


def all_opaque_in_palette(img: Image.Image) -> bool:
    px = img.convert("RGBA").load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a >= 24 and (r, g, b) not in MASTER:
                return False
    return True


def corner_transparent(img: Image.Image) -> bool:
    return img.convert("RGBA").getpixel((0, 0))[3] == 0


def test_cutout_sprite(tmp: Path) -> None:
    print("test: cutout sprite (key bg + downscale + quantize)")
    # 400x400 off-palette teal blob on a bright magenta backdrop (a classic
    # generator-baked background), no alpha.
    im = Image.new("RGBA", (400, 400), (255, 0, 255, 255))
    px = im.load()
    for y in range(400):
        for x in range(400):
            if (x - 200) ** 2 + (y - 200) ** 2 < 150 ** 2:
                px[x, y] = (40, 210, 200, 255)  # off-palette teal
    src = tmp / "raw_sprite.png"
    im.save(src)
    out = I.import_asset(src, 48, 48, do_quantize=True, do_key=True)
    check(out.size == (48, 48), f"frame size is 48x48 (got {out.size})")
    check(corner_transparent(out), "magenta background keyed to transparent")
    check(out.getpixel((24, 24))[3] > 0, "blob centre stayed opaque")
    check(all_opaque_in_palette(out), "every opaque colour is in the master palette")


def test_sprite_strip(tmp: Path) -> None:
    print("test: 6-frame sprite strip (slice + repack)")
    # 6 frames side by side, 128px each, distinct off-palette colours on black.
    im = Image.new("RGBA", (128 * 6, 128), (0, 0, 0, 255))
    px = im.load()
    cols = [(200, 40, 40), (40, 200, 40), (40, 40, 200), (200, 200, 40), (200, 40, 200), (40, 200, 200)]
    for f in range(6):
        for y in range(30, 98):
            for x in range(f * 128 + 30, f * 128 + 98):
                px[x, y] = (*cols[f], 255)
    src = tmp / "raw_strip.png"
    im.save(src)
    out = I.import_asset(src, 48, 48, cols=6, do_quantize=True, do_key=True)
    check(out.size == (48 * 6, 48), f"packed strip is 288x48 (got {out.size})")
    # each frame should still carry a distinct opaque cluster
    distinct = set()
    for f in range(6):
        distinct.add(out.getpixel((f * 48 + 24, 48 // 2))[:3])
    check(len(distinct) >= 4, f"frames keep distinct colours ({len(distinct)} unique centres)")
    check(all_opaque_in_palette(out), "every opaque colour is in the master palette")


def test_tileset_row(tmp: Path) -> None:
    print("test: 4-tile tileset row (grid slice, opaque, quantized)")
    # 4 tiles, 64px each, off-palette solid fills, no alpha, no keying.
    im = Image.new("RGBA", (64 * 4, 64), (0, 0, 0, 255))
    px = im.load()
    fills = [(50, 120, 60), (200, 170, 120), (30, 110, 120), (90, 100, 110)]
    for t in range(4):
        for y in range(64):
            for x in range(t * 64, t * 64 + 64):
                px[x, y] = (*fills[t], 255)
    src = tmp / "raw_tiles.png"
    im.save(src)
    out = I.import_asset(src, 16, 16, cols=4, do_quantize=True, do_key=False)
    check(out.size == (16 * 4, 16), f"tileset row is 64x16 (got {out.size})")
    check(out.getpixel((8, 8))[3] == 255, "tiles stay fully opaque (no keying)")
    check(all_opaque_in_palette(out), "every tile colour is in the master palette")


def test_already_cutout_passthrough(tmp: Path) -> None:
    print("test: input that already has alpha is not re-keyed")
    im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    px = im.load()
    for y in range(20, 80):
        for x in range(20, 80):
            px[x, y] = (40, 210, 200, 255)
    src = tmp / "raw_alpha.png"
    im.save(src)
    out = I.import_asset(src, 48, 48, do_quantize=True, do_key=True)
    check(corner_transparent(out), "existing transparent corner preserved")
    check(out.getpixel((24, 24))[3] > 0, "existing opaque region preserved")


def main() -> int:
    print(f"master palette has {len(MASTER)} unique colours")
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        test_cutout_sprite(tmp)
        test_sprite_strip(tmp)
        test_tileset_row(tmp)
        test_already_cutout_passthrough(tmp)
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}):")
        for m in _fails:
            print("  -", m)
        return 1
    print("ALL IMPORT TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
