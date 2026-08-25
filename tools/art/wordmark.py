"""Painterly wordmark for THE DROWNED CHORUS.

Retires the old 7x9 hand-bitmapped glyph sheet (tools/pixelart/wordmark.py),
which was pure pixel art -- chunky stems upscaled with NEAREST -- the one
register the style contract froze off (§0: "a stranger shown any screenshot
says 'that's a beautiful painting'"). The wordmark was the loudest pixel
surface still shipping.

Same title, same read -- bone "THE DROWNED", teal "CHORUS", a slow sinking
sway, and wet drips off the baseline (the title is drowning) -- but authored
the way the rest of the cast is: a heavy serif set at 4x, given internal value
(a cold underlight bleeding up from the deep), a soft dark halo instead of a
1px ink outline, and downsampled with LANCZOS so every edge is painted, not
stair-stepped. Deterministic; regenerate with:

    python3 tools/art/wordmark.py

Output: assets/ui/wordmark.png (178x72, to preserve the menu/finale layout
that draws it at setScale(0.5)).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "ui" / "wordmark.png"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

# final footprint (unchanged from the retired sheet so nothing in the UI moves)
FINAL_W, FINAL_H = 178, 72
S = 6  # supersample: author big, paint the edges, shrink with LANCZOS

# one palette, two of its moods (style-contract §3): bone is the drowned light,
# teal is the chorus. Each letter carries a value from its own crown down into
# the cold deep, so the glyphs read as lit matter, not flat fill.
BONE_HI = (248, 244, 233)
BONE_LO = (176, 188, 190)
TEAL_HI = (126, 224, 214)
TEAL_LO = (44, 132, 138)
DEEP = (12, 40, 60)  # the cold underlight welling up the stems
INK = (4, 6, 10)  # the soft dark halo (style-contract: a soft dark AO is REQUIRED)

# hand-tuned per-letter vertical sway (px at final scale) -- the title does not
# sit level; it is going under. Mirrors the retired sheet's SWAY tables.
SWAY_1 = [0, 2, 0, 1, 2, 0, 2, 1, 0, 3, 1]  # THE DROWNED
SWAY_2 = [2, 0, 1, 3, 0, 2]  # CHORUS
# drips: (letter index, fraction across the glyph, length px at final scale)
DRIPS_1 = [(1, 0.5, 5), (5, 0.3, 4), (8, 0.6, 7), (10, 0.4, 4)]
DRIPS_2 = [(0, 0.5, 5), (2, 0.35, 4), (4, 0.6, 6)]


def _vgrad(w: int, h: int, top: tuple, bot: tuple) -> Image.Image:
    """A vertical top->bottom colour ramp, full alpha."""
    g = Image.new("RGBA", (w, h))
    px = g.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = (c[0], c[1], c[2], 255)
    return g


def draw_line(text, hi, lo, sway, drips, track):
    """Render one line to a tight RGBA image at S-times final resolution."""
    font = ImageFont.truetype(FONT_PATH, int(46 * S))
    asc, desc = font.getmetrics()
    trk = int(track * S)
    widths = [font.getsize(ch)[0] for ch in text]  # advance width per glyph
    sway_px = [v * S for v in sway]
    max_sway = max(sway_px)
    glyph_h = asc + desc
    pad = 10 * S
    W = sum(widths) + trk * (len(text) - 1) + 2 * pad
    H = glyph_h + max_sway + pad + 14 * S  # extra room below for drips
    top = pad  # y of the em-box top before sway
    baseline = top + asc

    # 1) the glyph coverage mask (grayscale alpha), placed with tracking + sway.
    #    Baselines align because every glyph shares the same em-box top.
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    x = pad
    spans = []  # (x_left, glyph_w, top_y) per letter, for drips
    for i, ch in enumerate(text):
        gy = top + sway_px[i % len(sway_px)]
        md.text((x, gy), ch, font=font, fill=255)
        spans.append((x, widths[i], gy))
        x += widths[i] + trk

    # 2) fill the mask with a vertical value ramp (crown light -> cold deep),
    #    with a final short push to DEEP at the very bottom of the stems so the
    #    letters look like they are standing in the water they are sinking into
    grad = _vgrad(W, H, hi, lo)
    deep = _vgrad(W, H, lo, DEEP)
    # blend the lower ~35% toward the deep ramp
    ramp = Image.new("L", (W, H), 0)
    rpx = ramp.load()
    for y in range(H):
        t = max(0.0, (y - (baseline)) / max(1, H - baseline))
        rpx_val = int(min(1.0, t * 1.4) * 255)
        for xx in range(W):
            rpx[xx, y] = rpx_val
    body = Image.composite(deep, grad, ramp)
    body.putalpha(mask)

    # 3) a wet top sheen: a slim brighter edge along each crown
    inner = mask.filter(ImageFilter.MinFilter(2 * S + 1))
    crown = Image.new("L", (W, H), 0)
    cpx, ipx, mpx = crown.load(), inner.load(), mask.load()
    for y in range(H):
        for xx in range(W):
            if mpx[xx, y] > 40 and ipx[xx, y] < 40 and y < baseline + 2 * S:
                cpx[xx, y] = 150
    sheen = Image.new("RGBA", (W, H), (*BONE_HI, 0))
    sheen.putalpha(crown.filter(ImageFilter.GaussianBlur(S * 0.6)))
    body = Image.alpha_composite(body, sheen)

    # 4) drips -- soft tapering streaks of the letter colour welling downward
    dd = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ddraw = ImageDraw.Draw(dd)
    for li, frac, length in drips:
        if li >= len(text) or text[li] == " ":
            continue
        gx0, gw, gtop = spans[li]
        cx = gx0 + int(gw * frac)
        base_y = gtop + glyph_h - int(4 * S)
        L = length * S
        rad = int(1.6 * S)
        for d in range(L):
            t = d / max(1, L)
            r = max(1, int(rad * (1 - t * 0.7)))
            a = int(200 * (1 - t) ** 1.3)
            c = tuple(int(lo[i] + (DEEP[i] - lo[i]) * t) for i in range(3))
            ddraw.ellipse([cx - r, base_y + d - r, cx + r, base_y + d + r], fill=(*c, a))
        ddraw.ellipse([cx - rad - S, base_y + L - S, cx + rad + S, base_y + L + int(2.2 * S)],
                      fill=(*DEEP, 150))  # the hanging bead
    dd = dd.filter(ImageFilter.GaussianBlur(S * 0.5))
    body = Image.alpha_composite(dd, body)  # drips sit BEHIND the glyph faces

    return body, mask


def with_halo(line: Image.Image, mask: Image.Image) -> Image.Image:
    """A soft dark halo behind the whole line -- the contract's required AO,
    doing here what a hard 1px ink outline used to, but painted."""
    W, H = line.size
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    halo.putalpha(mask.filter(ImageFilter.MaxFilter(2 * S + 1)).filter(ImageFilter.GaussianBlur(S * 1.4)))
    dark = Image.new("RGBA", (W, H), (*INK, 0))
    dark.putalpha(Image.eval(halo.getchannel("A"), lambda v: int(v * 0.85)))
    return Image.alpha_composite(dark, line)


def trim(im: Image.Image) -> Image.Image:
    bbox = im.getchannel("A").getbbox()
    return im.crop(bbox) if bbox else im


def main() -> None:
    l1, m1 = draw_line("THE DROWNED", BONE_HI, BONE_LO, SWAY_1, DRIPS_1, track=3)
    l2, m2 = draw_line("CHORUS", TEAL_HI, TEAL_LO, SWAY_2, DRIPS_2, track=6)
    l1 = trim(with_halo(l1, m1))
    l2 = trim(with_halo(l2, m2))

    gap = int(6 * S)
    W = max(l1.width, l2.width)
    H = l1.height + gap + l2.height
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sheet.alpha_composite(l1, ((W - l1.width) // 2, 0))
    sheet.alpha_composite(l2, ((W - l2.width) // 2, l1.height + gap))

    # fit into the frozen footprint, preserving aspect, then paint the edges down
    scale = min(FINAL_W / sheet.width, FINAL_H / sheet.height)
    tw, th = max(1, round(sheet.width * scale)), max(1, round(sheet.height * scale))
    sheet = sheet.resize((tw, th), Image.LANCZOS)
    out = Image.new("RGBA", (FINAL_W, FINAL_H), (0, 0, 0, 0))
    out.alpha_composite(sheet, ((FINAL_W - tw) // 2, (FINAL_H - th) // 2))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({out.width}x{out.height})")


if __name__ == "__main__":
    main()
