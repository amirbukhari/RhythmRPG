"""Asset importer -- turn a generated/commissioned raw PNG into an engine-ready
asset and drop it into the right assets/ slot.

The game loads PNGs directly, so any art you generate from
docs/design/art-prompts.md becomes real in-game art after this pass:

  * palette-quantize   -> snap every colour to the Skatopia master palette
                          (skatopia.py PALETTE) so the whole game stays cohesive
  * key background     -> auto-detect a flat backdrop and make it transparent
                          (for cutout sprites/props/enemies)
  * downscale          -> LANCZOS down to the target pixel size, then quantize
                          removes the blur -> crisp pixel art
  * slice / pack       -> cut a horizontal strip or a grid into frames and
                          re-pack them at the engine's exact frame size

CLI:
  python3 import_asset.py --input raw.png --out assets/.../foo.png \
      --frames 6 --frame 48x48           # a 6-frame 48x48 sprite strip
  python3 import_asset.py --input tiles.png --out assets/tilemaps/x.png \
      --grid 4x1 --frame 16x16 --opaque  # a 4-tile tileset row (no keying)
  python3 import_asset.py --input bg.png --out assets/backgrounds/x.png \
      --frame 320x180 --opaque --no-quantize   # a background, palette free

Everything is importable (see functions below) and covered by
test_import_asset.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from skatopia import PALETTE

# Unique RGB triples of the master palette (drop alpha; all are opaque).
MASTER_RGB: list[tuple[int, int, int]] = sorted({(r, g, b) for (r, g, b, _a) in PALETTE.values()})


def _nearest(rgb: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    r, g, b = rgb
    best = palette[0]
    best_d = 1 << 30
    for pr, pg, pb in palette:
        # perceptual-ish weighting (eyes are greener); good enough for snapping
        d = 2 * (pr - r) ** 2 + 4 * (pg - g) ** 2 + 3 * (pb - b) ** 2
        if d < best_d:
            best_d, best = d, (pr, pg, pb)
    return best


def quantize(img: Image.Image, palette: list[tuple[int, int, int]] | None = None) -> Image.Image:
    """Snap every opaque pixel to its nearest master-palette colour. Alpha is
    preserved; fully/near-transparent pixels are left transparent. A small
    cache keeps this fast on flat pixel art."""
    palette = palette or MASTER_RGB
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 24:
                px[x, y] = (0, 0, 0, 0)
                continue
            key = (r, g, b)
            snapped = cache.get(key)
            if snapped is None:
                snapped = _nearest(key, palette)
                cache[key] = snapped
            px[x, y] = (snapped[0], snapped[1], snapped[2], a)
    return img


def key_background(img: Image.Image, tol: int = 28, key: str | None = None) -> Image.Image:
    """Global colour key: make every pixel within `tol` of the key (or the
    dominant corner colour) transparent. Best when the backdrop is a known flat
    chroma; for AI images that embed the subject, prefer flood_key()."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    if key:
        kc = tuple(int(key.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    else:
        corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
        counts: dict[tuple[int, int, int], int] = {}
        for c in corners:
            counts[c[:3]] = counts.get(c[:3], 0) + 1
        kc = max(counts, key=counts.get)
    tol2 = tol * tol * 3
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and (r - kc[0]) ** 2 + (g - kc[1]) ** 2 + (b - kc[2]) ** 2 <= tol2:
                px[x, y] = (0, 0, 0, 0)
    return img


def flood_key(img: Image.Image, tol: int = 60) -> Image.Image:
    """Remove the background of a centred subject by flood-filling inward from
    every border pixel: only pixels *connected to the edge* and within `tol` of
    the local border colour go transparent. Interior colours survive even if
    they match the backdrop (so white highlights inside a subject on a white
    background are kept). Robust for AI-generated 'sprite on plain background'
    images where an exact chroma key fails."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    # seed colour = mean of the four corners
    cs = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    kc = tuple(sum(c[i] for c in cs) // 4 for i in range(3))
    tol2 = tol * tol * 3
    seen = bytearray(w * h)
    stack: list[tuple[int, int]] = []
    for x in range(w):
        stack.append((x, 0)); stack.append((x, h - 1))
    for y in range(h):
        stack.append((0, y)); stack.append((w - 1, y))
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        r, g, b, _a = px[x, y]
        if (r - kc[0]) ** 2 + (g - kc[1]) ** 2 + (b - kc[2]) ** 2 > tol2:
            continue  # hit the subject; stop
        px[x, y] = (0, 0, 0, 0)
        stack.append((x + 1, y)); stack.append((x - 1, y))
        stack.append((x, y + 1)); stack.append((x, y - 1))
    return img


def _palette_image(palette: list[tuple[int, int, int]]) -> Image.Image:
    """A PIL 'P'-mode image carrying `palette` (padded to 256), for quantize()."""
    flat: list[int] = []
    for r, g, b in palette:
        flat += [r, g, b]
    flat += [0, 0, 0] * (256 - len(palette))
    pal = Image.new("P", (1, 1))
    pal.putpalette(flat)
    return pal


def pixelate(img: Image.Image, logical_w: int, logical_h: int, *,
             palette: list[tuple[int, int, int]] | None = None, dither: bool = True,
             upscale_w: int | None = None, upscale_h: int | None = None,
             darken: float = 0.0) -> Image.Image:
    """Turn a detailed/painterly image into real 8-bit pixel art: collapse to a
    chunky logical resolution (kills painterly micro-detail), snap to a limited
    palette with optional Floyd–Steinberg dithering, then nearest-upscale so the
    pixels stay crisp and blocky. Alpha is preserved as a hard mask."""
    img = img.convert("RGBA")
    alpha = img.getchannel("A").resize((logical_w, logical_h), Image.BILINEAR)
    small = img.convert("RGB").resize((logical_w, logical_h), Image.BILINEAR)
    if darken > 0:
        small = small.point(lambda v: int(v * (1.0 - darken)))
    palimg = _palette_image(palette or MASTER_RGB)
    q = small.quantize(palette=palimg, dither=Image.FLOYDSTEINBERG if dither else Image.NONE).convert("RGBA")
    q.putalpha(alpha.point(lambda a: 255 if a >= 128 else 0))
    uw, uh = upscale_w or logical_w, upscale_h or logical_h
    if (uw, uh) != (logical_w, logical_h):
        q = q.resize((uw, uh), Image.NEAREST)
    return q


def downscale(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize down to the target pixel size. LANCZOS for the area average
    (quantize afterward restores crisp flat colours)."""
    if img.size == (target_w, target_h):
        return img
    return img.resize((target_w, target_h), Image.LANCZOS)


def slice_frames(img: Image.Image, cols: int, rows: int = 1) -> list[Image.Image]:
    """Cut a strip/grid into cols*rows equal cells, row-major."""
    w, h = img.size
    fw, fh = w // cols, h // rows
    out: list[Image.Image] = []
    for r in range(rows):
        for c in range(cols):
            out.append(img.crop((c * fw, r * fh, c * fw + fw, r * fh + fh)))
    return out


def pack_strip(frames: list[Image.Image], fw: int, fh: int) -> Image.Image:
    """Re-pack frames into one horizontal strip at the engine frame size."""
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        if f.size != (fw, fh):
            f = f.resize((fw, fh), Image.LANCZOS)
        sheet.alpha_composite(f.convert("RGBA"), (i * fw, 0))
    return sheet


def import_asset(
    input_path: str | Path,
    frame_w: int,
    frame_h: int,
    *,
    cols: int = 1,
    rows: int = 1,
    do_quantize: bool = True,
    do_key: bool = True,
    key_color: str | None = None,
    tol: int = 28,
) -> Image.Image:
    """Full pipeline. Returns the finished RGBA image (a `frame_w*cols`-wide
    strip for multi-frame, or a single frame). Caller writes it to the slot."""
    src = Image.open(input_path).convert("RGBA")
    already_cutout = src.getextrema()[3][0] < 8  # has real transparency already
    if do_key and not already_cutout:
        src = key_background(src, tol=tol, key=key_color)
    frames = slice_frames(src, cols, rows) if (cols * rows) > 1 else [src]
    frames = [downscale(f, frame_w, frame_h) for f in frames]
    out = pack_strip(frames, frame_w, frame_h)
    if do_quantize:
        out = quantize(out)
    return out


def _parse_size(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def main() -> None:
    ap = argparse.ArgumentParser(description="Import generated art into an engine asset slot.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True, help="asset path to write (relative to repo or absolute)")
    ap.add_argument("--frame", required=True, help="per-frame WxH, e.g. 48x48")
    ap.add_argument("--frames", type=int, default=1, help="horizontal frame count")
    ap.add_argument("--grid", default=None, help="COLSxROWS for a grid sheet (overrides --frames)")
    ap.add_argument("--opaque", action="store_true", help="skip background keying (tilesets/backgrounds)")
    ap.add_argument("--no-quantize", action="store_true", help="skip master-palette snap")
    ap.add_argument("--key", default=None, help="explicit background hex to key, e.g. #ff00ff")
    ap.add_argument("--tol", type=int, default=28)
    args = ap.parse_args()

    fw, fh = _parse_size(args.frame)
    if args.grid:
        cols, rows = _parse_size(args.grid)
    else:
        cols, rows = args.frames, 1

    out = import_asset(
        args.input, fw, fh, cols=cols, rows=rows,
        do_quantize=not args.no_quantize, do_key=not args.opaque,
        key_color=args.key, tol=args.tol,
    )
    dst = Path(args.out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    print(f"wrote {dst} ({out.width}x{out.height}, {cols * rows} frame(s))")


if __name__ == "__main__":
    main()
