"""The two cutscene plates that are drawn, not generated.

`plates.py` explains the split; the short version is that generation loses on
geometry and on particles. Six batches could not get one flat vertical slab out
of the endpoint (it offered a mountain, a canyon, a framed painting of a canyon,
and two brutalist office blocks) and none produced a single visible raindrop.
Both images are simple to draw, exactly on canon when drawn, and deterministic.

Everything here renders at 2x and downsamples with LANCZOS, matching rig.py's
rule that nothing is ever upsampled and nothing is ever quantized.
"""

from __future__ import annotations

import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

import palette as P  # noqa: E402

SS = 2  # supersample


def _hash(x, y, salt=0):
    """Deterministic pseudo-random in [0,1). No RNG anywhere in the art
    pipeline -- the same source must produce byte-identical PNGs."""
    h = (x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)
    h &= 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 0x1000000


def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _over(img, col, mask):
    """Composite a flat colour through `mask` and return (new_image, new_draw).

    Image.composite() returns a NEW image, so an ImageDraw handle taken before
    it silently keeps writing into the orphaned one. That bug ate the entire
    town at the obelisk's foot and every flagstone joint in the rain -- both
    were being drawn, into a buffer that was then thrown away. Everything
    composites through here so the draw handle can never go stale."""
    out = Image.composite(Image.new("RGB", img.size, col), img, mask)
    return out, ImageDraw.Draw(out)


# ---------------------------------------------------------------------------
# obelisk -- world-bible §2: "They did not raise the obelisk. It was there."
#
# The beat is scale and indifference. Three things carry it, and the first two
# were learned by getting them wrong:
#
#   1. The slab needs a visible EDGE. Filled edge-to-edge it reads as a dark
#      backdrop, not an object -- the eye has nothing to measure. With one
#      vertical edge and slightly lighter water beyond it, the same pixels read
#      as a colossal thing standing in front of something.
#   2. The town has to silhouette against a LIT haze, and it has to vary. Drawn
#      as one row of similar roofs it read as a picket fence; it is now three
#      depth bands at three values, with towers, flat roofs and chimneys.
#   3. Its top is not in the picture, and the seam does not reach the bottom.
#      It is opening, not open.
# ---------------------------------------------------------------------------
def obelisk(w, h):
    W, H = w * SS, h * SS
    EDGE = int(W * 0.80)  # the slab's right edge; water beyond it
    base = int(H * 0.885)

    # black water first -- everything is composed against this
    img = Image.new("RGB", (W, H), (10, 14, 20))
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=_lerp((12, 17, 25), (26, 34, 42), (y / H) ** 0.8))

    # the stone
    stone = Image.new("L", (W, H), 0)
    ImageDraw.Draw(stone).rectangle([0, 0, EDGE, H], fill=255)
    slab = Image.new("RGB", (W, H), (0, 0, 0))
    sd = ImageDraw.Draw(slab)
    for y in range(H):
        sd.line([(0, y), (W, y)], fill=_lerp((30, 39, 49), (74, 88, 98), (y / H) ** 0.66))
    # coarse courses, faint -- one object first, masonry second
    course = int(104 * SS)
    for i in range(1, H // course + 2):
        y = i * course + int(_hash(i, 3, 11) * 10 * SS)
        sd.line([(0, y), (EDGE, y)], fill=_lerp((30, 39, 49), (74, 88, 98), (y / float(H)) ** 0.66), width=max(1, SS))
        sd.line([(0, y), (EDGE, y)], fill=(27, 35, 44), width=max(1, SS))
        off = int(_hash(i, 7, 23) * course)
        for k in range(0, EDGE // course + 2):
            x = k * course + off
            if _hash(k, i, 31) < 0.22:  # not every joint -- a regular grid reads as tile
                continue
            sd.line([(x, y), (x, y + course)], fill=(29, 37, 46), width=max(1, SS))
    img = Image.composite(slab, img, stone)
    d = ImageDraw.Draw(img)
    # the lit edge: stone catches the water's light along its corner
    d.line([(EDGE, 0), (EDGE, base)], fill=(96, 116, 126), width=max(1, int(2 * SS)))

    # wet sheen
    sheen = Image.new("L", (W, H), 0)
    shd = ImageDraw.Draw(sheen)
    for i in range(12):
        x = int(_hash(i, 41, 5) * EDGE)
        wid = int((8 + _hash(i, 42, 6) * 30) * SS)
        shd.rectangle([x, 0, x + wid, H], fill=int(20 + _hash(i, 43, 7) * 46))
    sheen = Image.composite(sheen, Image.new("L", (W, H), 0), stone)
    sheen = sheen.filter(ImageFilter.GaussianBlur(22 * SS))
    img, d = _over(img, (118, 140, 150), sheen)

    # the seam
    sx = int(W * 0.41)
    seam = Image.new("L", (W, H), 0)
    smd = ImageDraw.Draw(seam)
    for y in range(0, int(H * 0.90)):
        t = y / H
        x = sx + int(math.sin(t * 2.1) * 6 * SS)
        half = max(1, int((1.4 + t * 2.6) * SS))
        smd.rectangle([x - half, y, x + half, y + 1], fill=255)
    bloom = seam.filter(ImageFilter.GaussianBlur(34 * SS)).point(lambda v: min(255, int(v * 4.2)))
    core = seam.filter(ImageFilter.GaussianBlur(1.1 * SS))
    img, d = _over(img, P.tint((18, 26, 32), P.FOLD, 0.7), bloom)
    img, d = _over(img, (214, 250, 244), core)

    # silt haze -- the town's backlight. Brightest just above the ground line.
    haze = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(haze)
    for k in range(int(96 * SS)):
        y = base - int(84 * SS) + k
        hd.line([(0, y), (W, y)], fill=int(255 * (k / (96.0 * SS)) ** 0.62))
    hd.rectangle([0, base, W, H], fill=255)
    haze = haze.filter(ImageFilter.GaussianBlur(26 * SS))
    img, d = _over(img, (128, 156, 162), haze)

    # the town: three depth bands, far to near, each darker than the last
    for band, (dy, val, scale) in enumerate((
            (int(-16 * SS), (54, 68, 76), 0.62),
            (int(-6 * SS), (24, 32, 40), 0.82),
            (0, (5, 7, 11), 1.0))):
        y0 = base + dy
        x = -int(30 * SS)
        i = 0
        while x < W + 40 * SS:
            k = _hash(i, 61 + band, 3)
            bw = int((22 + k * 52) * SS * scale)
            bh = int((14 + _hash(i, 62 + band, 4) * 46) * SS * scale)
            top_y = y0 - bh
            shape = _hash(i, 64 + band, 8)
            if shape > 0.82:  # a tower
                bw = int(bw * 0.5)
                bh = int(bh * 1.9)
                top_y = y0 - bh
                d.rectangle([x, top_y, x + bw, y0], fill=val)
                d.polygon([(x - int(2 * SS), top_y), (x + bw // 2, top_y - int(20 * SS)),
                           (x + bw + int(2 * SS), top_y)], fill=val)
            elif shape > 0.62:  # flat roof
                d.rectangle([x, top_y, x + bw, y0], fill=val)
            else:  # pitched
                d.rectangle([x, top_y, x + bw, y0], fill=val)
                d.polygon([(x - int(3 * SS), top_y), (x + bw // 2, top_y - int(15 * SS) * scale),
                           (x + bw + int(3 * SS), top_y)], fill=val)
                if _hash(i, 65 + band, 12) > 0.6:  # chimney
                    cx = x + int(bw * 0.72)
                    d.rectangle([cx, top_y - int(13 * SS) * scale, cx + int(4 * SS), top_y], fill=val)
            if band == 2 and _hash(i, 71, 9) > 0.52:  # a lit window, nearest band only
                wx = x + int(bw * (0.28 + _hash(i, 72, 2) * 0.44))
                wy = top_y + int(bh * 0.42)
                r = max(1, int(1.8 * SS))
                d.ellipse([wx - r, wy - r, wx + r, wy + r], fill=(224, 158, 84))
            x += bw + int((2 + _hash(i, 63 + band, 5) * 9) * SS)
            i += 1
    d.rectangle([0, base, W, H], fill=(5, 7, 11))

    _motes(img, W, H, count=170, salt=91)
    return _finish(img, w, h)


# ---------------------------------------------------------------------------
# rain -- the ending register (PRD §8.7.2's aftermath).
#
# world-bible §11 makes rain the one gentle image in the game, so it is built
# soft: no hard white, one warm lamp, and the streaks thin toward the top so the
# frame has air. It is the last thing the player sees, and the only plate with
# warmth in it.
# ---------------------------------------------------------------------------
def rain(w, h):
    W, H = w * SS, h * SS
    ground = int(H * 0.78)
    img = Image.new("RGB", (W, H), (18, 22, 34))
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=_lerp((30, 36, 52), (14, 17, 26), (y / H) ** 0.9))

    # the lamp: a real source, on a post, far off to one side
    lx, ly = int(W * 0.70), int(H * 0.34)
    d.rectangle([lx - int(1.6 * SS), ly, lx + int(1.6 * SS), ground], fill=(9, 11, 16))
    d.rectangle([lx - int(9 * SS), ly - int(5 * SS), lx + int(9 * SS), ly], fill=(11, 13, 19))
    lamp = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(lamp)
    r = int(7 * SS)
    ld.ellipse([lx - r, ly - r, lx + r, ly + r], fill=255)
    img, d = _over(img, (255, 226, 178), lamp.filter(ImageFilter.GaussianBlur(1.4 * SS)))
    halo = lamp.filter(ImageFilter.GaussianBlur(70 * SS)).point(lambda v: min(255, int(v * 5.4)))
    img, d = _over(img, (206, 150, 84), halo)
    # the light's cone, caught in the falling water
    cone = Image.new("L", (W, H), 0)
    ImageDraw.Draw(cone).polygon(
        [(lx - int(10 * SS), ly), (lx + int(10 * SS), ly),
         (lx + int(120 * SS), ground), (lx - int(120 * SS), ground)], fill=54)
    img, d = _over(img, (188, 142, 88), cone.filter(ImageFilter.GaussianBlur(30 * SS)))

    # the rain: a far faint sheet and a near, longer, brighter pass
    for far in (True, False):
        layer = Image.new("L", (W, H), 0)
        pd = ImageDraw.Draw(layer)
        n = 1700 if far else 700
        lean = 5 * SS if far else 12 * SS
        salt = 1 if far else 2
        for i in range(n):
            x = _hash(i, 11, salt) * (W + 220 * SS) - 110 * SS
            y = _hash(i, 12, salt) * H
            if _hash(i, 13, salt) > 0.22 + 0.78 * (y / H):  # thin out upward
                continue
            ln = (11 + _hash(i, 14, salt) * 24) * SS * (1.0 if far else 2.2)
            v = int((58 + _hash(i, 15, salt) * 52) * (1.0 if far else 1.9))
            pd.line([(x, y), (x - lean, y + ln)], fill=min(255, v),
                    width=max(1, int(SS * (1 if far else 1.7))))
        if far:
            layer = layer.filter(ImageFilter.GaussianBlur(1.5 * SS))
        img, d = _over(img, (158, 184, 198) if far else (206, 224, 230), layer)

    # wet stone, and the lamp drawn down it in a long broken reflection
    d.rectangle([0, ground, W, H], fill=(9, 12, 17))
    for i in range(26):
        y = ground + int(_hash(i, 41, 4) * (H - ground))
        d.line([(0, y), (W, y)], fill=(15, 19, 25), width=max(1, SS))
    refl = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(refl)
    for i in range(70):
        y = ground + int(_hash(i, 31, 8) * (H - ground))
        t = (y - ground) / float(H - ground)
        spread = int((10 + t * 96 + _hash(i, 32, 9) * 26) * SS)
        rd.rectangle([lx - spread, y, lx + spread, y + max(1, int(1.8 * SS))],
                     fill=int((190 - t * 90) * (0.5 + _hash(i, 33, 10) * 0.5)))
    img, d = _over(img, (208, 150, 84), refl.filter(ImageFilter.GaussianBlur(4 * SS)))

    # splashes breaking on the stone
    splash = Image.new("L", (W, H), 0)
    spd = ImageDraw.Draw(splash)
    for i in range(320):
        x = _hash(i, 51, 6) * W
        y = ground + _hash(i, 52, 7) * (H - ground)
        rr = (1.2 + _hash(i, 53, 8) * 3.6) * SS
        spd.ellipse([x - rr, y - rr * 0.32, x + rr, y + rr * 0.32],
                    outline=int(64 + _hash(i, 54, 9) * 96), width=max(1, int(SS * 0.9)))
    img, d = _over(img, (168, 186, 194), splash.filter(ImageFilter.GaussianBlur(0.9 * SS)))
    return _finish(img, w, h)


def _motes(img, W, H, count, salt):
    """Suspended silt. Every underwater frame in this game has it; it is what
    stops black water reading as an empty background."""
    d = ImageDraw.Draw(img)
    for i in range(count):
        x = _hash(i, 1, salt) * W
        y = _hash(i, 2, salt) * H
        r = (0.5 + _hash(i, 3, salt) * 1.7) * SS
        v = int(26 + _hash(i, 4, salt) * 54)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(v, v + 6, v + 10))


def _finish(img, w, h):
    """Vignette, a whisper of grain, and the downsample."""
    W, H = img.size
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    m = int(min(W, H) * 0.30)
    vd.ellipse([-m, -m, W + m, H + m], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(min(W, H) * 0.10)).point(lambda v: 255 - int(v * 0.34))
    img, d = _over(img, (3, 4, 7), vig)

    px = img.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            g = int(_hash(x, y, 777) * 7) - 3
            r0, g0, b0 = px[x, y]
            px[x, y] = (max(0, min(255, r0 + g)), max(0, min(255, g0 + g)), max(0, min(255, b0 + g)))
    return img.resize((w, h), Image.LANCZOS)


PLATES = {"obelisk": obelisk, "rain": rain}
