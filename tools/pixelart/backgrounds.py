"""Arena backdrops (320x180) for The Drowned Chorus.

PRD §11.1.1: every arena is a SPECIFIC PLACE with an untold story staged in
its set pieces -- no generic battlefields, no palette-swaps of a shared
scene. Five painters, one per movement (canonical staging in
docs/design/world-bible.md §5a):

  shallows  -- drowned village green; boat-ring round a sunken maypole, one
               boat still straining at its rope toward the surface
  saltmines -- gallery of miners calcified mid-listen, all facing one
               glowing tunnel mouth; one statue caught mid-run the other way
  pit       -- sunken carnival wrestling ring, ropes snapped OUTWARD, crowd
               chairs tipped facing away, two lanterns still burning
  attic     -- the Attic of Teeth: rafters, a door clawed on the INSIDE,
               walls black with scrawl + gouged staves, a bed of pens
  hall      -- the Conductor's orchestra: rows of stands with blank pages
               (the last row's are full), melting stopped clocks, bone organ

Also keeps the legacy `build()` abyss/conductor pair (menus + the retained
turn-based scene) and the tiling `caustics()` overlay. All deterministic.
"""

from __future__ import annotations

import math
import random
from PIL import Image
from skatopia import PALETTE, save

W, H = 320, 180
HORIZON = 118


def _lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def _mk():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    return im, im.load()


def _put(px, x, y, c, a=1.0):
    if 0 <= x < W and 0 <= y < H:
        if a >= 1.0:
            px[x, y] = c
        else:
            o = px[x, y]
            px[x, y] = tuple(round(o[i] + (c[i] - o[i]) * a) for i in range(3)) + (255,)


def _rect(px, x0, y0, x1, y1, c, a=1.0):
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            _put(px, x, y, c, a)


def _water(px, surface, deep, y1=HORIZON):
    for y in range(y1):
        t = y / y1
        c = _lerp(surface, deep, t * t)
        for x in range(W):
            px[x, y] = c


def _floor(px, tone, y0=HORIZON):
    far = _lerp(tone, PALETTE["e"], 0.35)
    for y in range(y0, H):
        t = (y - y0) / (H - y0)
        c = _lerp(far, PALETTE["K"], t)
        for x in range(W):
            px[x, y] = c
    for x in range(W):
        _put(px, x, y0, PALETTE["m"], 0.55)
    rng = random.Random(4)
    for _ in range(170):
        x, y = rng.randrange(W), rng.randrange(y0, H)
        _put(px, x, y, PALETTE["m"] if rng.random() < 0.6 else PALETTE["d"])


def _motes(px, col, n=60, seed=5, y1=HORIZON):
    rng = random.Random(seed)
    for _ in range(n):
        _put(px, rng.randrange(W), rng.randrange(y1), col, 0.65)


def _godray(px, cx, wtop, col, y1=HORIZON, strength=0.10):
    for y in range(y1):
        t = y / y1
        half = wtop * (0.5 + t)
        skew = int(t * 22)
        a = strength * (1 - t)
        for x in range(int(cx + skew - half), int(cx + skew + half)):
            _put(px, x, y, col, a)


def _vignette(px, depth=28):
    for y in range(H):
        for x in range(W):
            d = min(x, W - 1 - x, y, H - 1 - y)
            if d < depth:
                f = d / depth
                c = px[x, y]
                px[x, y] = tuple(round(c[i] * (0.42 + 0.58 * f)) for i in range(3)) + (255,)


# ---------------------------------------------------------------------------
# 1. THE SHALLOWS -- drowned village green (teal)
# ---------------------------------------------------------------------------


def _house(px, cx, base, w, h, body, roof):
    _rect(px, cx - w // 2, base - h, cx + w // 2, base, body)
    for i in range(w // 2 + 2):  # gable roof
        y = base - h - (w // 2 - i) // 2
        _rect(px, cx - i, y, cx + i, y + 1, roof)
    _put(px, cx + w // 4, base - h + 3, PALETTE["C"], 0.9)  # a window still lit


def _boat(px, cx, cy, w, hull, up=False):
    for i in range(w // 2):
        d = i // 3
        _rect(px, cx - w // 2 + i, cy + d, cx - w // 2 + i + 1, cy + 2 + d - (1 if i > w // 3 else 0), hull)
        _rect(px, cx + w // 2 - i, cy + d, cx + w // 2 - i + 1, cy + 2 + d - (1 if i > w // 3 else 0), hull)
    _rect(px, cx - w // 2 + 2, cy, cx + w // 2 - 1, cy + 2, hull)
    if up:
        _rect(px, cx - w // 2 + 2, cy - 1, cx + w // 2 - 1, cy, _lerp(hull, PALETTE["W"], 0.3))


def shallows() -> Image.Image:
    im, px = _mk()
    _water(px, PALETTE["c"], PALETTE["E"])
    _godray(px, 90, 14, PALETTE["C"])
    _godray(px, 240, 10, PALETTE["C"])
    _motes(px, PALETTE["C"])
    village = _lerp(PALETTE["e"], PALETTE["V"], 0.4)
    roof = _lerp(PALETTE["e"], PALETTE["Y"], 0.35)
    # sunken rooftops breaking the green
    _house(px, 48, HORIZON + 4, 34, 26, village, roof)
    _house(px, 268, HORIZON + 2, 30, 22, village, roof)
    _house(px, 120, HORIZON + 6, 26, 16, _lerp(village, PALETTE["E"], 0.4), _lerp(roof, PALETTE["E"], 0.4))
    # chapel spire, leaning
    for i in range(52):
        xx = 196 + i // 9
        _rect(px, xx - max(1, (52 - i) // 8), HORIZON + 2 - i, xx + max(1, (52 - i) // 8), HORIZON + 3 - i, village)
    _put(px, 202, HORIZON - 50, PALETTE["o"], 0.9)  # spire lamp -- the story light
    # the maypole and its ring of moored boats
    mp_x, mp_y = 160, HORIZON - 2
    _rect(px, mp_x, mp_y - 34, mp_x + 2, mp_y, PALETTE["V"])
    hull = _lerp(PALETTE["Y"], PALETTE["e"], 0.45)
    ring = [(-34, 6), (-18, 10), (2, 12), (22, 10), (36, 5)]
    for dx, dy in ring:
        _boat(px, mp_x + dx, mp_y + dy - 8, 16, hull)
        # slack mooring line to the pole
        steps = 10
        for s in range(steps):
            t = s / steps
            lx = round(mp_x + 1 + (dx) * t)
            ly = round(mp_y - 30 + (dy + 22) * t + 6 * math.sin(t * math.pi))
            _put(px, lx, ly, PALETTE["v"], 0.7)
    # ...and ONE boat above, still tied, straining toward the surface
    bx, by = 150, 26
    _boat(px, bx, by, 18, _lerp(PALETTE["Y"], PALETTE["w"], 0.25), up=True)
    for s in range(26):  # taut rope, dead straight
        t = s / 25
        _put(px, round(bx + (mp_x + 1 - bx) * t), round(by + 3 + (mp_y - 34 - by - 3) * t), PALETTE["w"], 0.8)
    _floor(px, _lerp(PALETTE["g"], PALETTE["e"], 0.5))
    _vignette(px)
    return im


# ---------------------------------------------------------------------------
# 2. THE SALT MINES -- gallery of the calcified (ember)
# ---------------------------------------------------------------------------


def _salt_miner(px, cx, base, h, facing=1, running=False):
    salt = PALETTE["w"]
    lit = PALETTE["W"]
    head = base - h
    _rect(px, cx - 2, head, cx + 3, head + 4, salt)  # head
    _rect(px, cx - 3, head + 4, cx + 4, base - h // 3, salt)  # torso
    if running:
        _rect(px, cx - 5, base - h // 3, cx - 2, base, salt)  # legs split
        _rect(px, cx + 2, base - h // 3, cx + 5, base - 2, salt)
        _rect(px, cx - 6, head + 5, cx - 3, head + 7, salt)  # arms pumping
    else:
        _rect(px, cx - 2, base - h // 3, cx + 3, base, salt)
        # tool raised toward the tunnel
        _rect(px, cx + 3 * facing, head + 2, cx + (3 + 6) * facing, head + 4, salt)
        _rect(px, cx + (3 + 5) * facing, head - 3, cx + (3 + 7) * facing, head + 2, PALETTE["m"])
    for i in range(h // 3):  # top-lit
        _put(px, cx - 2 + (i % 5), head + i, lit, 0.35)


def saltmines() -> Image.Image:
    im, px = _mk()
    _water(px, _lerp(PALETTE["Y"], PALETTE["k"], 0.25), PALETTE["K"])
    # the singing tunnel mouth, glowing faintly -- the story light
    tx = 258
    for r in range(30, 0, -1):
        a = 0.05 + (30 - r) * 0.012
        col = _lerp(PALETTE["Y"], PALETTE["o"], (30 - r) / 30)
        for ang in range(0, 181, 4):
            x = tx + int(r * math.cos(math.radians(ang)))
            y = HORIZON + 2 - int(r * 0.9 * math.sin(math.radians(ang)))
            _put(px, x, y, col, a)
    _rect(px, tx - 16, HORIZON - 20, tx + 16, HORIZON + 2, PALETTE["K"], 0.85)  # the dark within
    # rock strata
    rng = random.Random(13)
    for _ in range(240):
        x, y = rng.randrange(W), rng.randrange(HORIZON)
        _put(px, x, y, PALETTE["Y"] if rng.random() < 0.4 else PALETTE["d"], 0.35)
    # mine-cart rails running toward the tunnel
    for x in range(0, W, 2):
        y = HORIZON + 26 - x // 24
        _put(px, x, y, PALETTE["m"], 0.9)
        _put(px, x, y + 4, PALETTE["m"], 0.9)
        if x % 12 == 0:
            _rect(px, x, y, x + 2, y + 5, PALETTE["N"])
    # an abandoned cart
    _rect(px, 36, HORIZON + 12, 62, HORIZON + 24, PALETTE["N"])
    _rect(px, 38, HORIZON + 10, 60, HORIZON + 12, PALETTE["m"])
    _rect(px, 40, HORIZON + 6, 58, HORIZON + 10, PALETTE["w"], 0.9)  # heaped salt
    # the calcified: miners mid-listen, ALL facing the tunnel
    for cx, h in [(96, 30), (130, 26), (172, 32), (208, 27), (232, 24)]:
        _salt_miner(px, cx, HORIZON + 2, h, facing=1)
    # ...and the foreman, mid-run the other way, three steps from the lift
    _salt_miner(px, 20, HORIZON + 2, 26, facing=-1, running=True)
    _rect(px, 2, HORIZON - 44, 12, HORIZON + 2, PALETTE["N"])  # the lift cage
    _rect(px, 3, HORIZON - 44, 4, HORIZON + 2, PALETTE["m"])
    _floor(px, _lerp(PALETTE["Y"], PALETTE["N"], 0.5))
    _vignette(px)
    return im


# ---------------------------------------------------------------------------
# 3. THE PIT BELOW -- sunken carnival ring (plum)
# ---------------------------------------------------------------------------


def pit() -> Image.Image:
    im, px = _mk()
    _water(px, PALETTE["P"], PALETTE["X"])
    _motes(px, PALETTE["u"], seed=8)
    # banked seating bowls on both sides
    seat = _lerp(PALETTE["p"], PALETTE["K"], 0.3)
    for row in range(5):
        y0 = 34 + row * 16
        _rect(px, 0, y0, 92 - row * 14, y0 + 7, seat)
        _rect(px, W - 92 + row * 14, y0, W, y0 + 7, seat)
    # tipped chairs, all facing AWAY from the ring
    rng = random.Random(31)
    for side, x0, x1 in [(-1, 6, 80), (1, 244, 312)]:
        for _ in range(7):
            x = rng.randrange(x0, x1)
            y = 40 + rng.randrange(0, 60)
            _rect(px, x, y, x + 6, y + 2, PALETTE["v"])  # seat on its side
            _rect(px, x + (6 if side < 0 else -2), y - 4, x + (8 if side < 0 else 0), y + 2, PALETTE["v"])  # back pointing away
    # lantern strings sagging overhead -- dead...
    for x in range(10, W - 10):
        y = 16 + int(14 * math.sin((x - 10) / (W - 20) * math.pi))
        _put(px, x, y, PALETTE["d"], 0.9)
        if x % 22 == 0:
            _rect(px, x - 1, y + 1, x + 2, y + 5, PALETTE["k"])
    # ...except two, still burning -- the story lights
    for lx in [142, 208]:
        ly = 16 + int(14 * math.sin((lx - 10) / (W - 20) * math.pi)) + 3
        for r in range(7, 0, -1):
            for ang in range(0, 360, 30):
                _put(px, lx + int(r * math.cos(math.radians(ang))), ly + int(r * 0.8 * math.sin(math.radians(ang))), PALETTE["o"], 0.06)
        _rect(px, lx - 1, ly - 2, lx + 2, ly + 2, PALETTE["y"])
    # the wrestling ring
    rx0, rx1 = 108, 212
    ry = HORIZON + 10
    _rect(px, rx0, ry, rx1, ry + 6, _lerp(PALETTE["p"], PALETTE["v"], 0.4))  # apron
    for cx in [rx0, rx1]:
        _rect(px, cx - 1, ry - 26, cx + 2, ry, PALETTE["v"])  # corner posts
    for line in range(3):
        y = ry - 8 - line * 8
        for x in range(rx0, (rx0 + rx1) // 2 + 14):  # left half of ropes intact
            _put(px, x, y, PALETTE["B"], 0.9)
        # right half SNAPPED OUTWARD: rope ends whip past the right post
        for s in range(26):
            t = s / 25
            xx = (rx0 + rx1) // 2 + 14 + int(60 * t) + line * 6
            yy = y + int(18 * t * t) - line * 2
            _put(px, xx, yy, PALETTE["B"], max(0.15, 0.9 - t))
    _floor(px, _lerp(PALETTE["p"], PALETTE["N"], 0.55))
    _vignette(px)
    return im


# ---------------------------------------------------------------------------
# 4. THE ATTIC OF TEETH -- a locked room (blood/rust). Interior: no water.
# ---------------------------------------------------------------------------


def attic() -> Image.Image:
    im, px = _mk()
    # close air, not water
    _water(px, _lerp(PALETTE["X"], PALETTE["k"], 0.4), PALETTE["K"], y1=H)
    wall = _lerp(PALETTE["X"], PALETTE["d"], 0.5)
    _rect(px, 0, 0, W, HORIZON + 8, wall)
    # layered scrawl blackening the walls, with gouged musical staves
    rng = random.Random(77)
    for _ in range(1400):
        x, y = rng.randrange(W), rng.randrange(8, HORIZON)
        ln = rng.randint(2, 7)
        for i in range(ln):
            _put(px, x + i, y, PALETTE["K"], rng.uniform(0.25, 0.7))
    for sy in [30, 58, 86]:  # staves scratched among the words
        for line in range(5):
            for x in range(24, 296):
                if rng.random() < 0.85:
                    _put(px, x, sy + line * 3, PALETTE["h"], 0.5)
        for _ in range(9):  # desperate note-heads
            nx = rng.randrange(30, 290)
            _rect(px, nx, sy + rng.randrange(0, 13), nx + 3, sy + rng.randrange(0, 13) + 3, PALETTE["K"])
    # slanted rafters
    for i in range(6):
        x0 = -40 + i * 70
        for s in range(150):
            _put(px, x0 + s, s // 3, PALETTE["k"], 0.9)
            _put(px, x0 + s, s // 3 + 1, PALETTE["d"], 0.9)
    # the bolted door, high in the back wall, clawed on the INSIDE
    dx0, dy0 = 236, 26
    _rect(px, dx0, dy0, dx0 + 34, dy0 + 56, _lerp(PALETTE["Y"], PALETTE["k"], 0.5))
    _rect(px, dx0 + 1, dy0 + 1, dx0 + 33, dy0 + 55, _lerp(PALETTE["Y"], PALETTE["d"], 0.35))
    _rect(px, dx0 - 2, dy0 + 24, dx0 + 36, dy0 + 28, PALETTE["m"])  # the bolt, thrown
    for gx, gy, gl in [(6, 8, 14), (12, 6, 18), (19, 10, 15), (25, 7, 17)]:  # claw gouges
        for s in range(gl):
            _put(px, dx0 + gx + s // 5, dy0 + gy + s, PALETTE["B"], 0.85)
    # the keyhole glow -- the story light
    _rect(px, dx0 + 28, dy0 + 30, dx0 + 30, dy0 + 33, PALETTE["o"])
    # the bed of pens + the spill of tiny bones
    rng2 = random.Random(9)
    for _ in range(70):
        x = 34 + rng2.randrange(56)
        y = HORIZON + 14 + rng2.randrange(12)
        ang = rng2.choice([(1, 0), (3, 1), (2, -1)])
        for s in range(7):
            _put(px, x + s * ang[0] // 2, y + s * ang[1] // 3, PALETTE["e"] if rng2.random() < 0.5 else PALETTE["m"])
        _put(px, x, y, PALETTE["C"], 0.5)  # nib glints
    for _ in range(26):
        x = 120 + rng2.randrange(40)
        y = HORIZON + 20 + rng2.randrange(10)
        _rect(px, x, y, x + 2, y + 1, PALETTE["W"])
    _floor(px, _lerp(PALETTE["X"], PALETTE["N"], 0.4))
    _vignette(px, depth=36)
    return im


# ---------------------------------------------------------------------------
# 5. THE CONDUCTOR'S HALL -- an orchestra with no orchestra (ink + ember)
# ---------------------------------------------------------------------------


def _clock(px, cx, cy, r, hand_ang, melt):
    for a in range(0, 360, 6):
        x = cx + int(r * math.cos(math.radians(a)))
        y = cy + int(r * math.sin(math.radians(a))) + (int(melt * max(0, math.sin(math.radians(a)))) if a < 180 else 0)
        _put(px, x, y, PALETTE["k"])
    _put(px, cx, cy, PALETTE["W"])
    _put(px, cx + int((r - 2) * math.cos(hand_ang)), cy + int((r - 2) * math.sin(hand_ang)), PALETTE["B"], 0.95)
    for d in range(melt):  # the drip
        _put(px, cx, cy + r + d, PALETTE["k"], max(0.2, 0.9 - d * 0.1))


def hall() -> Image.Image:
    im, px = _mk()
    _water(px, _lerp(PALETTE["p"], PALETTE["K"], 0.35), PALETTE["K"])
    _godray(px, 160, 18, PALETTE["u"], strength=0.08)
    # bone organ across the back
    for i, ph in enumerate([40, 58, 74, 86, 74, 58, 40]):
        x0 = 118 + i * 12
        _rect(px, x0, HORIZON - 8 - ph, x0 + 8, HORIZON - 8, _lerp(PALETTE["w"], PALETTE["k"], 0.45))
        _rect(px, x0 + 1, HORIZON - 8 - ph, x0 + 3, HORIZON - 8, _lerp(PALETTE["w"], PALETTE["k"], 0.25))
    # the podium -- the story light burns on it
    _rect(px, 150, HORIZON - 18, 172, HORIZON + 2, _lerp(PALETTE["V"], PALETTE["k"], 0.4))
    _rect(px, 146, HORIZON - 22, 176, HORIZON - 18, PALETTE["V"])
    for r in range(9, 0, -1):
        for a in range(0, 360, 30):
            _put(px, 161 + int(r * math.cos(math.radians(a))), HORIZON - 26 + int(r * 0.7 * math.sin(math.radians(a))), PALETTE["o"], 0.07)
    _rect(px, 160, HORIZON - 28, 163, HORIZON - 24, PALETTE["y"])
    # rows of empty music stands receding; every page blank...
    def stand(cx, base, s, full):
        _rect(px, cx, base - 10 * s // 10, cx + 1, base, _lerp(PALETTE["m"], PALETTE["k"], 0.3))
        page = PALETTE["W"] if not full else PALETTE["w"]
        _rect(px, cx - 3 * s // 10 - 1, base - 14 * s // 10, cx + 3 * s // 10 + 2, base - 9 * s // 10, page)
        if full:  # ...except the last row's, dense with ink
            for yy in range(base - 13 * s // 10, base - 10 * s // 10):
                for xx in range(cx - 3 * s // 10, cx + 3 * s // 10 + 1):
                    if (xx + yy) % 2:
                        _put(px, xx, yy, PALETTE["K"], 0.8)
    for row, (y, s, n) in enumerate([(HORIZON - 34, 6, 6), (HORIZON - 16, 8, 5), (HORIZON + 6, 10, 4)]):
        for i in range(n):
            cx = 160 + (i - (n - 1) / 2) * (26 + row * 10)
            stand(int(cx), y, s, full=(row == 2))
    # black clocks line the walls, stopped at DIFFERENT times, melting
    for cx, cy, r, ang, melt in [(30, 30, 8, 0.7, 4), (70, 52, 6, 2.4, 3), (288, 34, 8, 4.1, 5), (252, 58, 6, 5.5, 3), (110, 24, 5, 1.6, 2)]:
        _clock(px, cx, cy, r, ang, melt)
    _floor(px, _lerp(PALETTE["p"], PALETTE["K"], 0.3))
    _vignette(px, depth=32)
    return im


ARENAS = {"shallows": shallows, "saltmines": saltmines, "pit": pit, "attic": attic, "hall": hall}


# --- legacy pair (menus + retained turn-based scene) ------------------------


def build(boss: bool = False) -> Image.Image:
    return hall() if boss else shallows()


def caustics() -> Image.Image:
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
    import os
    # The arena backdrops are now AI-generated (tools/pixelart/generate_ai.py,
    # committed under assets/backgrounds/arena_*.png). These procedural painters
    # are kept as the fallback/reference but do NOT clobber the shipped AI art
    # unless REGEN_ARENAS=1 is set explicitly.
    if os.environ.get("REGEN_ARENAS") == "1":
        for name, fn in ARENAS.items():
            save(fn(), f"backgrounds/arena_{name}.png")
        print("procedural arenas regenerated:", ", ".join(ARENAS))
    else:
        print("skipping arena painters (AI art is source of truth; REGEN_ARENAS=1 to override)")
    save(build(False), "backgrounds/battle_abyss.png")
    save(build(True), "backgrounds/battle_conductor.png")
    save(caustics(), "backgrounds/caustics.png")
    print("backgrounds written (abyss/conductor/caustics)")
