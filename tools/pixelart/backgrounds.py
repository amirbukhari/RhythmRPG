"""Battle backdrops (320x180) with real depth, painted deterministically in
the Skatopia palette: the drowned world the party fights through. Built in
layers with atmospheric perspective (distant things fade into the water fog),
god-ray shafts, floor caustics, drifting motes, and a near-foreground of
bone spires -- so the scene reads as a deep space, not a flat wall.

Outputs the composited backdrop PLUS a separate tiling `caustics` overlay
the BattleScene scrolls slowly for an underwater shimmer.
"""

from __future__ import annotations

import random
from PIL import Image
from skatopia import PALETTE, save

W, H = 320, 180
HORIZON = 118


def _lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def _put(px, x, y, c, a=1.0):
    if 0 <= x < W and 0 <= y < H:
        if a >= 1.0:
            px[x, y] = c
        else:
            o = px[x, y]
            px[x, y] = tuple(round(o[i] + (c[i] - o[i]) * a) for i in range(3)) + (255,)


def _water(px, boss):
    surface = PALETTE["c"] if not boss else PALETTE["P"]
    deep = PALETTE["E"] if not boss else PALETTE["X"]
    for y in range(HORIZON):
        t = y / HORIZON
        c = _lerp(surface, deep, t * t)
        for x in range(W):
            px[x, y] = c


def _godrays(px, boss):
    ray = PALETTE["C"] if not boss else PALETTE["u"]
    for cx, wtop in [(70, 10), (150, 16), (232, 12)]:
        for y in range(0, HORIZON):
            t = y / HORIZON
            half = wtop * (0.5 + t)  # widen as they descend
            skew = int(t * 26)  # slant
            a = 0.10 * (1 - t)
            for x in range(int(cx + skew - half), int(cx + skew + half)):
                _put(px, x, y, ray, a)


def _obelisks(px, boss):
    fog = PALETTE["e"] if not boss else PALETTE["X"]
    # (cx, height, halfwidth, depth 0..1) -- deeper = more faded into fog
    rows = [
        (30, 60, 5, 0.85), (110, 74, 6, 0.7), (200, 66, 6, 0.78), (300, 58, 5, 0.9),  # far
        (66, 96, 8, 0.35), (250, 104, 9, 0.3),  # mid
        (158, 120, 11, 0.0),  # near, sharp
    ]
    for cx, ht, hw, depth in sorted(rows, key=lambda r: -r[3]):
        body = _lerp(PALETTE["V"], fog, depth)
        edge = _lerp(PALETTE["w"], fog, depth)
        top = HORIZON + 8 - ht
        for y in range(top, HORIZON + 8):
            t = (y - top) / max(1, ht)
            half = max(1, round(hw * (0.45 + 0.55 * t)))
            for x in range(cx - half, cx + half):
                _put(px, x, y, body)
            _put(px, cx - half, y, edge)
            _put(px, cx + half - 1, y, edge)
        # carved glyph glow, only on the nearer stones
        if depth < 0.4:
            glow = PALETTE["B"] if boss else PALETTE["C"]
            for i in range(3):
                _put(px, cx, top + 6 + i * 4, glow, 0.8)


def _clocks(px):
    for cx, cy, r in [(58, 38, 6), (255, 44, 7), (150, 26, 5)]:
        for a in range(360):
            import math
            x = cx + int(r * math.cos(math.radians(a)))
            y = cy + int(r * math.sin(math.radians(a)))
            _put(px, x, y, PALETTE["k"])
        _put(px, cx, cy, PALETTE["W"])
        _put(px, cx, cy - r + 2, PALETTE["B"], 0.9)  # hand
        _put(px, cx + r - 2, cy, PALETTE["r"], 0.9)


def _floor(px, boss):
    near = PALETTE["N"]
    far = _lerp(PALETTE["m"], PALETTE["e"], 0.4)
    for y in range(HORIZON, H):
        t = (y - HORIZON) / (H - HORIZON)
        c = _lerp(far, PALETTE["k"], t)
        for x in range(W):
            px[x, y] = c
    # contact glow where floor meets water
    for x in range(W):
        _put(px, x, HORIZON, PALETTE["c"] if not boss else PALETTE["p"], 0.5)
        _put(px, x, HORIZON + 1, near, 0.6)
    # caustic light pools on the floor + scattered rubble
    rng = random.Random(3 if not boss else 9)
    for _ in range(26):
        cx, cy = rng.randrange(W), rng.randrange(HORIZON + 3, H - 4)
        rr = rng.randint(4, 9)
        for a in range(0, 360, 20):
            import math
            x = cx + int(rr * math.cos(math.radians(a)))
            y = cy + int(rr * 0.4 * math.sin(math.radians(a)))
            _put(px, x, y, PALETTE["c"], 0.12)
    for _ in range(200):
        x, y = rng.randrange(W), rng.randrange(HORIZON, H)
        r = rng.random()
        _put(px, x, y, PALETTE["m"] if r < 0.5 else PALETTE["d"] if r < 0.82 else PALETTE["g"])


def _foreground(px):
    """Near-black bone spires rising from the bottom corners for depth framing."""
    rng = random.Random(21)
    for base_x in [-6, 8, 300, 320]:
        h = rng.randint(38, 60)
        w = rng.randint(6, 10)
        for y in range(H - h, H):
            t = (y - (H - h)) / h
            half = int(w * (0.3 + 0.7 * t))
            for x in range(base_x - half, base_x + half):
                _put(px, x, y, PALETTE["K"])
            _put(px, base_x - half, y, PALETTE["d"], 0.7)


def _motes(px):
    rng = random.Random(5)
    for _ in range(70):
        x, y = rng.randrange(W), rng.randrange(0, HORIZON)
        _put(px, x, y, PALETTE["C"] if rng.random() < 0.5 else PALETTE["a"], 0.7)


def _vignette(px):
    for y in range(H):
        for x in range(W):
            d = min(x, W - 1 - x, y, H - 1 - y)
            if d < 30:
                f = d / 30
                c = px[x, y]
                px[x, y] = tuple(round(c[i] * (0.4 + 0.6 * f)) for i in range(3)) + (255,)


def build(boss: bool = False) -> Image.Image:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    px = im.load()
    _water(px, boss)
    _godrays(px, boss)
    _motes(px)
    _obelisks(px, boss)
    if boss:
        _clocks(px)
    _floor(px, boss)
    _foreground(px)
    _vignette(px)
    return im


def caustics() -> Image.Image:
    """A seamlessly-tiling translucent caustic-light overlay the scene scrolls
    slowly over the water for shimmer."""
    import math
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = im.load()
    for y in range(64):
        for x in range(64):
            v = math.sin(x / 5.0) * math.sin(y / 7.0) + math.sin((x + y) / 6.0)
            if v > 1.2:
                a = min(70, int((v - 1.2) * 120))
                px[x, y] = (PALETTE["C"][0], PALETTE["C"][1], PALETTE["C"][2], a)
    return im


if __name__ == "__main__":
    save(build(False), "backgrounds/battle_abyss.png")
    save(build(True), "backgrounds/battle_conductor.png")
    save(caustics(), "backgrounds/caustics.png")
    print("backgrounds written")
