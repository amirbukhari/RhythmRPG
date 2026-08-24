"""The Breach's environment kit -- a drowned carnival, still open.

    python3 tools/art/env_breach.py            # all pieces
    python3 tools/art/env_breach.py wheel      # one

THE BRIEF, verbatim (world-bible §6.3): "The waterline, staged as a carnival
that kept performing after the water came. Mir crosses and takes his first
breath of surface air; it is agony and it is the best moment of his life."

Then, in the same section, the taking. So this region has to do two jobs that
fight each other: it is the happiest place in the game for about a minute, and
then it is the worst thing that has ever happened to anybody. Neither reads if
the art is generically grim. A carnival is BUILT TO BE CHEERFUL, and the whole
effect depends on that cheer being intact and pointless -- bunting still strung,
the wheel still loaded, the bulbs still lit, and nobody there.

THE STRIPES ARE VALUE, NOT HUE, and this is the rule the region lives or dies on.
A carnival is stripes; stripes are the one place a hard repeat is the subject
rather than a mistake (style contract §4.5, same exemption the Keep's seat rows
get). But `docs/design/art-prompts.md` is explicit that the carnival relocated to
the waterline and its palette came with it BLEACHED -- it is not the retired
cosmology's plum fairground, and there is no purple in this world (§3). Sun, salt
and a century of water take the chroma out of canvas long before they take the
pattern out, so the stripes here are a light band and a dark band of the same
near-neutral, and the only saturated colour in the kit is:

  * the GHOST OF FAIRGROUND RED on painted woodwork, at about a third of the
    saturation it was mixed at, and
  * the BULBS, which are small, warm and emissive -- and which are the only
    thing in the region that is still doing its job.

That contrast is the region. Everything wide is grey; everything lit is tiny.

AUTHORING RULE (learned the hard way on the Shelf -- see WorldScale.ts): the
engine floors world scale at 0.5, so a piece's height in TILES is fixed by its
source canvas and declaring fewer metres cannot shrink it. Author at 32 px per
intended tile and the scale lands on 0.5 every time. The camera shows eleven
tiles, so nothing here is authored past ~9 of them: on the Shelf a hull came in
at fourteen and its prow was permanently off-screen.
"""

from __future__ import annotations

import math
import sys
import time
from PIL import Image
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import palette as P  # noqa: E402
from rig import Blob, Joint, Painter, Poly, Skeleton  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "env" / "breach"

# Breach materials. Note how few of these have any chroma at all: the bleach is
# the point, and a palette that cheats it back in with "just a little" warmth
# everywhere ends up as sepia, which is a different lie about the same place.
# THE CANVAS WAS TOO BRIGHT AND IT BROKE §3. These were 150/96/182, which is a
# defensible value for bleached duck in daylight and wrong for this region: at
# those numbers the tent canopies and booth awnings were the BRIGHTEST LARGE
# SHAPES in the frame, and §3 is "the brightest thing must be small". The bulbs
# -- the one thing here still doing its job -- lost to a tent roof. Pulled down
# ~12%, which keeps the light/dark stripe contrast (132 against 84 is still two
# clear steps) and hands the top of the value range back to the emissives.
CANVAS = (132, 133, 126)      # the light stripe: bleached duck canvas
CANVAS_DARK = (84, 87, 82)    # the dark stripe. SAME neutral, lower value.
CANVAS_LIT = (158, 157, 147)
TIMBER = (58, 53, 44)         # fairground woodwork, paint mostly gone
TIMBER_LIT = (88, 80, 66)
TIMBER_DARK = (34, 31, 26)
PAINT_RED = (118, 72, 58)     # the ghost of it. Mixed at ~1/3 saturation.
PAINT_CREAM = (166, 154, 124)
IRON = (46, 50, 50)
IRON_LIT = (72, 78, 76)
RUST = (104, 58, 32)
GILT = (150, 121, 66)         # the carousel's brass, tarnished
ROPE = (86, 80, 64)
BULB = (255, 234, 182)        # emissive, and always small
BULB_HOT = (255, 250, 226)
WEED = (52, 62, 44)           # the waterline's fringe
SILT = (118, 116, 104)


def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _root():
    return Skeleton([Joint("root", None, (0.0, 0.0), 0.0, 0.0)])


STONE_RIM = 0.22


def rect(x0, y0, x1, y1, col, z=0, glow=0.0, rim=STONE_RIM):
    return Poly("root", col, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z=z, glow=glow, rim=rim)


def poly(pts, col, z=0, glow=0.0, rim=STONE_RIM):
    return Poly("root", col, pts, z=z, glow=glow, rim=rim)


def blob(col, rx, ry, off, z=0, glow=0.0, rim=STONE_RIM):
    return Blob("root", col, rx, ry, off=off, z=z, glow=glow, rim=rim)


def _h(i, salt=0):
    """Deterministic jitter -- no RNG anywhere in the art pipeline."""
    v = (i * 73856093) ^ (salt * 19349663)
    v &= 0xFFFFFFFF
    v = (v ^ (v >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65536.0


def _tide(s, x0, x1, y, z=40, n=None, scale=1.0):
    """The waterline's fringe along a horizontal edge -- weed and silt rather
    than the Shelf's salt crust. Same job: it is what ties a brass carousel and a
    rotten plank into one place. The Shelf gets crusted; the Breach gets a
    TIDE MARK, because here the water is still arriving and leaving."""
    n = n or max(3, int((x1 - x0) / 9.0))
    for i in range(n):
        # A BEAD ROW IS NOT DEBRIS. `t = (i + 0.5) / n` with a couple of pixels
        # of jitter spaces these evenly, and evenly-spaced dots along the foot of
        # a prop read as a ZIPPER or a string of pearls -- it was on every piece
        # in every kit, because all five kits copied the same loop. Loose
        # material collects in CLUMPS with bare stretches between, so two things
        # change: a hash-driven skip opens real gaps, and the jitter is nearly a
        # full slot wide so neighbours cross and cluster. The radius is squared
        # off the hash too, which biases most of them small and lets a few be
        # obviously bigger -- an even size is as much of a tell as even spacing.
        if _h(i, 41) < 0.26:
            continue
        t = (i + 0.5) / n + (_h(i, 43) - 0.5) * 1.7 / n
        x = x0 + (x1 - x0) * t
        r = (1.5 + _h(i, 23) ** 2 * 4.4) * scale
        s.append(blob(_lerp(WEED, SILT, _h(i, 29) * 0.7), r, r * 0.55,
                      off=(x, y + (_h(i, 37) - 0.5) * 3.0), z=z))


def _bulb(s, x, y, z=6, r=2.0, hot=True):
    """One festoon bulb. Small on purpose -- see the module docstring: these are
    the only saturated, only emissive, and only still-working things here.

    THREE DISCS, AND THE REASON IS THE BLUR RADIUS. `rig.Painter` blurs an
    emissive shape by `9 * SS * glow`, so `glow=1.0` on a two-pixel blob spreads
    that blob's entire energy over a thirty-six-pixel radius and the result is
    invisible -- which is exactly what the first cut of this kit shipped: a
    region whose only warm light read as a row of grey PEARLS, and the one thing
    in the Breach that is still doing its job looked like beadwork.

    So the glow is built in layers instead. A wide dim disc at `glow=1.0` for the
    bloom that says "there is a light source here" from across the frame; a tight
    disc at `glow=0.30` (blur ~3 px on the shipped sprite) that keeps the light
    ATTACHED to the fitting instead of hovering near it; and an opaque hot core
    so the bulb still reads as an object when the additive pass is composited
    down. The kit ships at 32 px per tile and the engine halves it, so every
    radius here is twice what it will be on screen -- a bulb authored at r=2 is
    ONE PIXEL in game, and one pixel cannot glow.
    """
    # The bloom source is DARK -- a dim ember, not a white disc. It is the only
    # one of the three at glow=1.0, i.e. blurred over a 36 px radius, so its own
    # colour is what the wash ends up being; feeding it BULB puts a white kidney
    # bean the size of the fitting on the ground, which is what the second cut
    # of this shipped, and two lamps close together merged into one.
    s.append(blob(_lerp(BULB, (46, 26, 8), 0.66), r * 2.4, r * 2.4,
                  off=(x, y), z=z - 0.1, glow=1.0, rim=0.0))
    s.append(blob(_lerp(BULB, RUST, 0.18), r * 1.5, r * 1.5,
                  off=(x, y), z=z, glow=0.22, rim=0.0))          # the envelope
    if hot:
        s.append(blob(BULB_HOT, r * 0.62, r * 0.62, off=(x, y), z=z + 0.1,
                      glow=0.10, rim=0.0))                       # the filament


def _striped(s, pts_fn, n, y0, y1, z=0, pitch=9.0, wob=0.0):
    """Fill a vertical span with canvas stripes, light/dark alternating.

    `pts_fn(y)` returns (xl, xr) for that height, so this works on a cone, a
    wall, or a sagging tent. The pitch WOBBLES: a carnival's stripes were sewn
    by somebody, and a machined pitch is the difference between "sewn" and
    "extruded" -- which is §4.5's whole point about when a repeat is allowed.
    """
    k = 0
    y = y0
    while y < y1:
        h = pitch * (1.0 + (_h(k, 41) - 0.5) * 2.0 * wob)
        ye = min(y1, y + h)
        xl0, xr0 = pts_fn(y)
        xl1, xr1 = pts_fn(ye)
        col = CANVAS if k % 2 == 0 else CANVAS_DARK
        s.append(poly([(xl0, y), (xr0, y), (xr1, ye), (xl1, ye)], col, z=z + k * 0.001))
        y = ye
        k += 1


# ---------------------------------------------------------------------------
# the wheel -- stopped, loaded, and the region's landmark. THE piece.
# ---------------------------------------------------------------------------
def wheel():
    """A stopped Ferris wheel, ~9m, one car still at the top.

    THE ECHO IS THE SPEC: "It stopped with someone still at the top. The car is
    up there. It has always been up there." So the piece has to state three
    things in silhouette, from a camera eleven tiles high:

      1. IT IS A CIRCLE, AND CIRCLES DO NOT OCCUR OUT HERE. Nothing else in the
         game is a true circle at this size -- the Fold is arches and the Shelf
         is tapers -- so the ring alone identifies the region from a screen away.
      2. IT IS STOPPED, which is said by the CARS, not by the wheel. Cars hang
         from pivots, so a turning wheel has them all plumb; a stopped one has
         them plumb too. What says stopped is that the wheel is off-index: the
         spokes do not line up with the ground, one car sits at the very top
         where nobody would ever be left, and the drive belt is slack on its
         pulley.
      3. YOU CAN SEE THROUGH IT. Same lesson as the Shelf's sheave wheel, which
         shipped as a filled pale disc and read as a clock face. A wheel is a
         RIM and SPOKES with the world behind them; the moment the interior is
         filled it becomes a dial, a coin, or a moon.

    AND IT LEANS INTO ITS OWN A-FRAME. A wheel dead upright on symmetrical legs
    is a diagram. The near leg has sunk, so the whole ring is canted about five
    degrees and the axle is no longer level -- which is also the cheapest way to
    say "this will never turn again" without breaking anything visibly.
    """
    s = []
    W, H = 300, 288
    CXp, CYp, R = 8.0, 176.0, 108.0
    TILT = -0.085                                   # radians; the near leg sank

    def rot(x, y):
        c, si = math.cos(TILT), math.sin(TILT)
        return (CXp + x * c - y * si, CYp + x * si + y * c)

    # --- the A-frame, first, so the ring sits in front of it ---------------
    for sx, lean in ((-1.0, 1.0), (1.0, 1.0)):
        foot = CXp + sx * 74.0
        top = rot(sx * 9.0, -6.0)
        s.append(poly([(foot - 9.0, 0.0), (foot + 9.0, 0.0),
                       (top[0] + 5.0, top[1]), (top[0] - 5.0, top[1])],
                      _lerp(IRON, IRON_LIT, 0.34 if sx < 0 else 0.0), z=0))
    # the cross-brace, and it is NOT level -- see the docstring
    b0, b1 = (CXp - 62.0, 44.0), (CXp + 66.0, 52.0)
    s.append(poly([b0, b1, (b1[0], b1[1] + 6.0), (b0[0], b0[1] + 6.0)], IRON, z=0.2))
    _tide(s, CXp - 84.0, CXp + 84.0, 3.0, z=40, n=12)

    # --- the drive: a pulley with the belt hanging slack off it -------------
    px, py = CXp - 58.0, 30.0
    s.append(blob(IRON, 13.0, 13.0, off=(px, py), z=0.4))
    s.append(blob(_lerp(IRON, RUST, 0.5), 8.0, 8.0, off=(px, py), z=0.5))
    belt = [(px + 11.0, py + 6.0)]
    for k in range(1, 10):
        u = k / 9.0
        belt.append((px + 11.0 + 56.0 * u, py + 6.0 - 30.0 * math.sin(u * math.pi) + 34.0 * u))
    s.append(poly([(x, y + 2.2) for x, y in belt] + [(x, y - 2.2) for x, y in belt][::-1],
                  _lerp(IRON, TIMBER_DARK, 0.5), z=0.6))

    # --- the RIM: two concentric rings, and the gap between them is the tyre
    for rr, col, zz in ((R, _lerp(IRON, IRON_LIT, 0.30), 3.0),
                        (R - 7.0, _lerp(IRON, RUST, 0.22), 2.6)):
        prev = None
        for k in range(97):
            a = k / 96.0 * math.tau
            pt = rot(math.cos(a) * rr, math.sin(a) * rr)
            if prev is not None:
                # a segmented rim, not a stroked circle: a fairground wheel is
                # bolted up out of straight sections and the flats show
                s.append(poly([prev, pt,
                               (pt[0] + 2.6, pt[1] + 2.6), (prev[0] + 2.6, prev[1] + 2.6)],
                              col, z=zz))
            prev = pt

    # --- the spokes. Tension rods, so they are THIN, and there are many ----
    # Sixteen, which is odd-looking on purpose: an even count read across a
    # canted ring still resolves as a symmetric star, and this thing has to look
    # like it stopped somewhere arbitrary.
    for k in range(16):
        a = k / 16.0 * math.tau + 0.19
        o = rot(math.cos(a) * (R - 8.0), math.sin(a) * (R - 8.0))
        i0 = rot(math.cos(a) * 12.0, math.sin(a) * 12.0)
        s.append(poly([i0, o, (o[0] + 1.9, o[1] + 1.4), (i0[0] + 1.9, i0[1] + 1.4)],
                      _lerp(IRON, IRON_LIT, 0.42 if k % 3 else 0.10), z=2.2))
    s.append(blob(IRON, 15.0, 15.0, off=rot(0.0, 0.0), z=4))          # the hub
    s.append(blob(_lerp(IRON, GILT, 0.30), 8.0, 8.0, off=rot(0.0, 0.0), z=4.1))

    # --- the CARS. Eight, hanging plumb, one of them at the very top -------
    for k in range(8):
        a = k / 8.0 * math.tau + 0.19 + math.tau / 32.0
        ax, ay = rot(math.cos(a) * (R - 10.0), math.sin(a) * (R - 10.0))
        top_car = ay > CYp + R * 0.78
        s.append(poly([(ax - 1.6, ay), (ax + 1.6, ay),
                       (ax + 1.6, ay - 13.0), (ax - 1.6, ay - 13.0)], IRON, z=5))  # the hanger
        cw, ch = 15.0, 11.0
        cy = ay - 13.0
        # the tub. Painted, and the paint is the one place chroma is allowed.
        s.append(poly([(ax - cw, cy), (ax + cw, cy),
                       (ax + cw * 0.82, cy - ch), (ax - cw * 0.82, cy - ch)],
                      _lerp(PAINT_RED, TIMBER, 0.10 + _h(k, 43) * 0.22), z=5.1))
        s.append(poly([(ax - cw, cy), (ax + cw, cy), (ax + cw, cy - 2.6), (ax - cw, cy - 2.6)],
                      _lerp(PAINT_CREAM, CANVAS_DARK, 0.4), z=5.2))   # the gunwale
        if top_car:
            # THE ONE THAT MATTERS. It gets the only bulb on the wheel, so the
            # eye goes to the top of the ring and stays there.
            _bulb(s, ax, cy + 3.0, z=6.0, r=2.1)
    return s, (W, H)


# ---------------------------------------------------------------------------
def carousel():
    """The roundabout, ~5 tiles: a conical striped canopy on a centre mast.

    A CONE ON A POLE IS A PARASOL. What makes it a carousel is the ring of
    POLES hanging below the canopy rim with nothing on most of them -- the
    verticals say "things went round on this", and the empty ones say where the
    horses went. One horse is still up (see `carousel_horse` for the one that
    is not), and it is deliberately not centred in the piece.

    IT HAS DROPPED ON ONE SIDE, so the canopy rim is an ellipse tilted off the
    horizontal. A level rim would read as a tent.
    """
    s = []
    W, H = 220, 160
    cx, top = 4.0, 132.0
    RIMX, RIMY = 86.0, 22.0
    DROP = 9.0                                    # the low side of the rim

    def rim_y(t):
        return top - 44.0 + math.sin(t * math.tau) * RIMY * 0.34 - DROP * math.cos(t * math.tau)

    # the centre mast
    s.append(rect(cx - 5.0, 0.0, cx + 5.0, top, _lerp(TIMBER, TIMBER_DARK, 0.2), z=0))
    s.append(rect(cx - 5.0, 0.0, cx - 1.5, top, _lerp(TIMBER, TIMBER_LIT, 0.5), z=0.1))
    # the canopy: a striped cone. Stripes run down the slope, so each is a
    # wedge, not a band -- that is what a real carousel top does.
    for k in range(18):
        a0 = k / 18.0 * math.tau
        a1 = (k + 1) / 18.0 * math.tau
        p0 = (cx + math.cos(a0) * RIMX, rim_y(k / 18.0))
        p1 = (cx + math.cos(a1) * RIMX, rim_y((k + 1) / 18.0))
        s.append(poly([(cx, top), p0, p1], CANVAS if k % 2 == 0 else CANVAS_DARK, z=1 + k * 0.001))
    # the scalloped valance under the rim -- the detail that makes it fairground
    for k in range(19):
        t = k / 18.0
        x = cx + math.cos(t * math.tau) * RIMX
        y = rim_y(t)
        s.append(blob(_lerp(CANVAS_DARK, PAINT_CREAM, 0.3), 6.0, 4.4, off=(x, y - 3.0), z=1.4))
    # the poles. Most are empty, and that is the sentence.
    for k in range(11):
        t = (k + 0.5) / 11.0
        x = cx + math.cos(t * math.tau) * RIMX * 0.88
        y = rim_y(t)
        depth = 0.6 if math.sin(t * math.tau) > 0 else 3.0   # far side behind mast
        s.append(rect(x - 1.7, top - 118.0, x + 1.7, y - 2.0, _lerp(GILT, IRON, 0.42), z=depth))
        if k == 7:                                            # the one still up
            _horse(s, x, top - 96.0, z=depth + 0.2, flip=True, scale=0.62)
    _tide(s, cx - RIMX, cx + RIMX, 2.0, z=40, n=14)
    return s, (W, H)


def _horse(s, x, y, z=0, flip=False, scale=1.0):
    """A carousel horse, drawn from a point so `carousel` and `carousel_horse`
    share one animal. Legs tucked, neck arched, because that is the pose every
    one of them is carved in -- and because a horse standing normally reads as
    a horse, where a horse frozen mid-canter reads as a MACHINE'S horse."""
    k = scale
    sg = -1.0 if flip else 1.0

    def pt(dx, dy):
        return (x + sg * dx * k, y + dy * k)
    body = _lerp(PAINT_CREAM, CANVAS, 0.4)
    s.append(poly([pt(-20, 0), pt(16, 4), pt(20, 16), pt(-14, 14)], body, z=z))
    s.append(poly([pt(12, 8), pt(30, 26), pt(24, 34), pt(8, 16)], body, z=z + 0.1))     # neck
    s.append(poly([pt(24, 30), pt(40, 34), pt(38, 24), pt(26, 22)], body, z=z + 0.2))   # head
    s.append(poly([pt(34, 34), pt(38, 41), pt(33, 37)], body, z=z + 0.2))               # ear
    for dx, kick in ((-16.0, -1.0), (-9.0, 1.0), (10.0, -1.0), (16.0, 1.0)):
        s.append(poly([pt(dx, 2), pt(dx + 4, 2), pt(dx + 4 + kick * 9, -16), pt(dx + kick * 9, -16)],
                      _lerp(body, TIMBER, 0.22), z=z - 0.05))
    # the mane and tail: the only place the ghost-red is allowed on the animal
    for i in range(5):
        s.append(poly([pt(22 - i * 3.4, 30), pt(26 - i * 3.4, 32), pt(19 - i * 3.4, 20)],
                      _lerp(PAINT_RED, TIMBER, 0.08), z=z + 0.25))
    s.append(poly([pt(-20, 12), pt(-34, 20), pt(-30, 4), pt(-19, 2)],
                  _lerp(PAINT_RED, TIMBER, 0.14), z=z - 0.02))
    s.append(poly([pt(-4, 12), pt(6, 14), pt(6, 10), pt(-4, 8)], _lerp(GILT, RUST, 0.3), z=z + 0.3))
    return s


def carousel_horse():
    """One horse off its pole, ~1.6 tiles, lying on its side in the silt.

    ON ITS SIDE, which is the whole reason the piece exists separately from the
    carousel. Standing, it is a fairground fitting; fallen, with its brass pole
    still through it and one leg up, it is a small body. The player has a child
    with them for exactly one more region.
    """
    s = []
    W, H = 120, 52
    _horse(s, 4.0, 22.0, z=1, flip=False, scale=0.86)
    # the pole, snapped, still through the saddle
    s.append(poly([(-14.0, 8.0), (-9.0, 9.0), (24.0, 40.0), (19.0, 41.0)],
                  _lerp(GILT, IRON, 0.36), z=2))
    _tide(s, -46.0, 44.0, 3.0, z=40, n=8)
    return s, (W, H)


# ---------------------------------------------------------------------------
def strength_tester():
    """The high striker, ~4.5 tiles: a column, a bell, and a hammer left down.

    THE MOST LEGIBLE CARNIVAL SILHOUETTE THERE IS -- a tall thin column with a
    disc on top and numbers up the side. It costs almost nothing and it names
    the region from across a screen, which is the job the wheel does at distance
    and this does at street level.

    THE BELL IS STILL AT THE TOP AND THE PUCK IS STILL AT THE BOTTOM. Nobody
    won. The hammer is on the ground where it was dropped rather than leaning
    tidily against the post, because a tool put away is a place that closed and
    a tool dropped is a place that was left.
    """
    s = []
    W, H = 100, 144
    cx = 6.0
    s.append(rect(cx - 7.0, 0.0, cx + 7.0, 124.0, _lerp(TIMBER, TIMBER_DARK, 0.16), z=0))
    s.append(rect(cx - 7.0, 0.0, cx - 2.5, 124.0, _lerp(TIMBER, TIMBER_LIT, 0.46), z=0.1))
    s.append(rect(cx - 14.0, 0.0, cx + 14.0, 7.0, _lerp(TIMBER, TIMBER_DARK, 0.4), z=0.2))
    # the score plate: rungs up the post. Reads as numbers without being any.
    for k in range(11):
        y = 20.0 + k * 9.4
        w = 9.0 if k % 5 else 13.0
        s.append(rect(cx - w, y, cx + w, y + 2.6,
                      _lerp(PAINT_CREAM, CANVAS_DARK, 0.2 + _h(k, 47) * 0.3), z=0.3))
    # the bell
    s.append(poly([(cx - 15.0, 124.0), (cx + 15.0, 124.0), (cx + 10.0, 138.0), (cx - 10.0, 138.0)],
                  _lerp(GILT, RUST, 0.26), z=1))
    s.append(poly([(cx - 15.0, 124.0), (cx - 8.0, 124.0), (cx - 5.0, 138.0), (cx - 10.0, 138.0)],
                  _lerp(GILT, BULB, 0.22), z=1.1))
    s.append(blob(_lerp(GILT, RUST, 0.5), 4.0, 3.0, off=(cx, 141.0), z=1.2))
    # the puck, still at the bottom
    s.append(blob(_lerp(IRON, RUST, 0.4), 9.0, 4.0, off=(cx, 12.0), z=0.4))
    # the hammer, dropped
    s.append(poly([(cx + 16.0, 4.0), (cx + 54.0, 11.0), (cx + 54.0, 7.0), (cx + 16.0, 1.0)],
                  _lerp(TIMBER, TIMBER_LIT, 0.3), z=0.5))
    s.append(poly([(cx + 52.0, 14.0), (cx + 64.0, 16.0), (cx + 65.0, 4.0), (cx + 53.0, 3.0)],
                  _lerp(IRON, RUST, 0.34), z=0.6))
    _tide(s, cx - 20.0, cx + 66.0, 2.0, z=40, n=8)
    return s, (W, H)


# ---------------------------------------------------------------------------
def ticket_booth():
    """A ticket kiosk, ~2.8 tiles, hatch still open.

    THE HATCH IS OPEN AND THE SHELF INSIDE IS EMPTY. A closed kiosk is a place
    that shut; an open one with nobody in it is a place that was abandoned
    mid-transaction, which is the tense this whole region is in ("a carnival
    that KEPT PERFORMING after the water came").

    Its roof is striped and its body is not, because a booth with stripes on
    every surface is a beach hut. One striped plane per object is the rule the
    whole kit follows.
    """
    s = []
    W, H = 120, 90
    x0, x1 = -30.0, 30.0
    s.append(rect(x0, 0.0, x1, 58.0, _lerp(TIMBER, TIMBER_DARK, 0.1), z=0))
    s.append(rect(x0, 0.0, x0 + 8.0, 58.0, _lerp(TIMBER, TIMBER_LIT, 0.42), z=0.1))
    # the ghost-red skirt board: the one chroma note on the body
    s.append(rect(x0, 4.0, x1, 14.0, _lerp(PAINT_RED, TIMBER, 0.10), z=0.2))
    # the hatch: a dark hole with a counter under it and a shelf inside
    s.append(rect(-19.0, 26.0, 19.0, 48.0, (16, 18, 18), z=0.3))
    s.append(rect(-22.0, 22.0, 24.0, 27.0, _lerp(TIMBER, TIMBER_LIT, 0.5), z=0.5))  # counter
    s.append(rect(-15.0, 33.0, 15.0, 35.4, _lerp(TIMBER, TIMBER_DARK, 0.3), z=0.4))  # empty shelf
    # the propped-up hatch lid, angled -- says "open", cheaply
    s.append(poly([(-20.0, 48.0), (20.0, 48.0), (28.0, 64.0), (-12.0, 64.0)],
                  _lerp(TIMBER, TIMBER_LIT, 0.24), z=0.6))
    # the striped roof, and it overhangs
    def span(y):
        t = (y - 58.0) / 20.0
        w = 38.0 - t * 12.0
        return (-w, w)
    _striped(s, span, 6, 58.0, 76.0, z=1.0, pitch=4.6, wob=0.3)
    s.append(poly([(-40.0, 58.0), (40.0, 58.0), (34.0, 62.0), (-34.0, 62.0)],
                  _lerp(CANVAS_DARK, TIMBER, 0.3), z=1.4))
    _bulb(s, 26.0, 66.0, z=2.0, r=1.9)
    _bulb(s, -27.0, 66.0, z=2.0, r=1.9)
    _tide(s, x0 - 6.0, x1 + 6.0, 2.0, z=40, n=8)
    return s, (W, H)


# ---------------------------------------------------------------------------
def booth():
    """A midway game stall, ~2.6 tiles, prizes still on the back shelf.

    THE PRIZES ARE THE POINT AND THEY ARE ALMOST INVISIBLE -- four little
    lumps on a shelf at the back, no bigger than three pixels each at ship
    size. That is correct. §6.3's job here is that the region was CHEERFUL, and
    cheerful is carried by the fact that somebody stocked the shelf, not by the
    player being able to identify a plush duck.

    The counter sags in the middle. Everything horizontal in this region sags:
    it is the difference between a set that was built and a set that was left.
    """
    s = []
    W, H = 160, 84
    x0, x1 = -46.0, 46.0
    # the back wall, then the shelf, then the awning over the top
    s.append(rect(x0, 0.0, x1, 50.0, _lerp(TIMBER, TIMBER_DARK, 0.34), z=0))
    s.append(rect(x0 + 4.0, 30.0, x1 - 4.0, 33.0, _lerp(TIMBER, TIMBER_LIT, 0.36), z=0.4))
    for i in range(4):
        px = x0 + 14.0 + i * 21.0
        r = 3.4 + _h(i, 53) * 1.6
        s.append(blob(_lerp(PAINT_CREAM, PAINT_RED, _h(i, 59) * 0.55), r, r * 1.2,
                      off=(px, 33.0 + r), z=0.5))
    # the counter, sagging
    ctr = [(x0 - 4.0 + (x1 - x0 + 8.0) * (k / 8.0),
            22.0 - 3.4 * math.sin((k / 8.0) * math.pi)) for k in range(9)]
    s.append(poly([(x, y + 5.0) for x, y in ctr] + [(x, y) for x, y in ctr][::-1],
                  _lerp(TIMBER, TIMBER_LIT, 0.30), z=1.0))
    s.append(poly([(x, y + 5.0) for x, y in ctr] + [(x, y + 6.8) for x, y in ctr][::-1],
                  _lerp(PAINT_RED, PAINT_CREAM, 0.34), z=1.1))
    # the awning: striped, sagging, and it is the only striped plane here
    def span(y):
        return (x0 - 6.0, x1 + 6.0)
    _striped(s, span, 5, 50.0, 66.0, z=1.5, pitch=4.2, wob=0.34)
    for k in range(7):
        t = k / 6.0
        _bulb(s, x0 - 6.0 + (x1 - x0 + 12.0) * t,
              48.0 - 4.0 * math.sin(t * math.pi), z=2.0, r=1.7, hot=(k % 2 == 0))
    _tide(s, x0 - 8.0, x1 + 8.0, 2.0, z=40, n=10)
    return s, (W, H)


# ---------------------------------------------------------------------------
def tent():
    """A collapsed marquee, ~3.2 tiles: canvas down over its own poles.

    COLLAPSED, NOT PITCHED. There is already a standing striped thing in this
    kit (the carousel) and a second one would make the region a campsite. What
    this piece contributes is the shape of a big soft thing that has come down
    over a hard frame -- so the silhouette is two humps where the poles still
    hold it up and a long sag between them, and one pole has come through.
    """
    s = []
    W, H = 200, 102
    def sheet(y):
        return (-84.0, 84.0)
    # the fallen canvas: a profile with two peaks and a deep sag
    prof = []
    for k in range(25):
        u = k / 24.0
        x = -86.0 + 172.0 * u
        y = (58.0 * math.exp(-((u - 0.24) ** 2) / 0.012)
             + 44.0 * math.exp(-((u - 0.76) ** 2) / 0.016)
             + 12.0 * math.exp(-((u - 0.5) ** 2) / 0.05) + 5.0)
        prof.append((x, y))
    # stripes, following the profile: each band is a vertical slice of the heap
    for k in range(len(prof) - 1):
        (xa, ya), (xb, yb) = prof[k], prof[k + 1]
        col = CANVAS if k % 2 == 0 else CANVAS_DARK
        s.append(poly([(xa, 0.0), (xa, ya), (xb, yb), (xb, 0.0)], col, z=1 + k * 0.001))
    # the edge, catching light along the top of the heap
    s.append(poly([(x, y) for x, y in prof] + [(x, y - 3.4) for x, y in prof][::-1],
                  CANVAS_LIT, z=2.0))
    # the pole that came through, and the guy rope still pegged
    s.append(poly([(6.0, 4.0), (12.0, 4.0), (34.0, 78.0), (28.0, 78.0)],
                  _lerp(TIMBER, TIMBER_LIT, 0.3), z=3))
    rope = [(34.0, 76.0), (56.0, 44.0), (74.0, 20.0), (82.0, 3.0)]
    s.append(poly([(x + 1.6, y) for x, y in rope] + [(x - 1.6, y) for x, y in rope][::-1],
                  ROPE, z=3.1))
    s.append(poly([(78.0, 0.0), (84.0, 0.0), (85.0, 10.0), (79.0, 10.0)], TIMBER_DARK, z=3.2))
    _tide(s, -90.0, 90.0, 2.0, z=40, n=12)
    return s, (W, H)


# ---------------------------------------------------------------------------
def tent_pole():
    """A bare marquee pole, ~5.5 tiles, one rag of canvas still lashed on.

    THE KIT NEEDS SOMETHING TALL AND THIN THAT IS NOT A WRECK. The Shelf's
    verticals were all hulls and masts; if the Breach's are all wheel and
    carousel then the region has two silhouettes and no texture between them.
    A stripped pole with a flag of canvas snapping off it gives the midway
    rhythm at height, and it is the piece that can be repeated down a road
    without becoming the subject.

    THE RAG IS ON THE LEE SIDE, on every copy. There is a current here (the
    Shelf's kelp establishes it) and a rag that streams the other way on the
    next pole reads as two different days.
    """
    s = []
    W, H = 110, 176
    cx = 2.0
    s.append(rect(cx - 4.6, 0.0, cx + 4.6, 156.0, _lerp(TIMBER, TIMBER_DARK, 0.14), z=0))
    s.append(rect(cx - 4.6, 0.0, cx - 1.4, 156.0, _lerp(TIMBER, TIMBER_LIT, 0.44), z=0.1))
    s.append(blob(_lerp(GILT, IRON, 0.4), 6.0, 5.0, off=(cx, 158.0), z=0.4))   # the finial
    # the lashing, and the rag streaming off it
    s.append(rect(cx - 7.0, 118.0, cx + 7.0, 126.0, ROPE, z=0.5))
    rag = [(cx + 6.0, 124.0)]
    for k in range(1, 9):
        u = k / 8.0
        rag.append((cx + 6.0 + 52.0 * u, 124.0 - 30.0 * u + 9.0 * math.sin(u * 5.2)))
    s.append(poly([(x, y + 9.0 * (1.0 - i / 8.0)) for i, (x, y) in enumerate(rag)]
                  + [(x, y) for x, y in rag][::-1], CANVAS, z=1))
    s.append(poly([(x, y) for x, y in rag]
                  + [(x, y - 3.0 * (1.0 - i / 8.0)) for i, (x, y) in enumerate(rag)][::-1],
                  CANVAS_DARK, z=1.1))
    # two guy ropes, both slack
    for sg in (-1.0, 1.0):
        g = [(cx + sg * 3.0, 150.0)]
        for k in range(1, 7):
            u = k / 6.0
            g.append((cx + sg * (3.0 + 40.0 * u), 150.0 - 150.0 * u - 8.0 * math.sin(u * math.pi)))
        s.append(poly([(x + 1.4, y) for x, y in g] + [(x - 1.4, y) for x, y in g][::-1],
                      ROPE, z=0.3))
    _tide(s, cx - 16.0, cx + 46.0, 2.0, z=40, n=6)
    return s, (W, H)


# ---------------------------------------------------------------------------
def bunting():
    """A line of salt-stiffened flags between two stakes, ~2 tiles.

    STIFF, NOT LIMP, and that is the only interesting decision in the piece.
    Bunting that hangs slack is bunting in still air. Bunting that has dried
    hard in the shape the last wind left it -- every triangle locked at a
    slightly different angle, none of them plumb -- is bunting that stopped
    moving a long time ago and nobody took down. §2's rule that nothing in this
    world decays is doing the work: it did not rot, it SET.
    """
    s = []
    W, H = 180, 64
    x0, x1 = -76.0, 76.0
    for x in (x0, x1):
        s.append(rect(x - 3.0, 0.0, x + 3.0, 52.0, _lerp(TIMBER, TIMBER_DARK, 0.2), z=0))
    line = [(x0, 52.0)]
    for k in range(1, 13):
        u = k / 12.0
        line.append((x0 + (x1 - x0) * u, 52.0 - 15.0 * math.sin(u * math.pi)))
    s.append(poly([(x, y + 1.5) for x, y in line] + [(x, y - 1.5) for x, y in line][::-1],
                  ROPE, z=1))
    for k in range(12):
        ax, ay = line[k]
        bx, by = line[k + 1]
        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
        lean = (_h(k, 61) - 0.5) * 0.9        # each flag set at its own angle
        dx, dy = math.sin(lean) * 15.0, -math.cos(lean) * 15.0
        s.append(poly([(ax, ay), (bx, by), (mx + dx, my + dy)],
                      CANVAS if k % 2 == 0 else _lerp(CANVAS_DARK, PAINT_RED, 0.40), z=1.2))
    _tide(s, x0 - 6.0, x1 + 6.0, 2.0, z=40, n=8)
    return s, (W, H)


# ---------------------------------------------------------------------------
def festoon_lamp():
    """A festoon bulb off a wire on a stake, ~2.2 tiles. THE GATE PROP.

    `OverworldScene.GATE_PROPS` names this key: it is the warm light beside the
    road where the Shelf hands off to the Breach. Those gate lights are the only
    warm things between the Fold and the Keep, and the shape of the climb is that
    Mir walks away from the last warm room he will ever stand in -- so each one
    has to be a small kindness rather than a checkpoint marker.

    The Shelf's is a miner's safety lamp: a flame in wire gauze, carried by
    people who knew the air was bad. This one is a party light on a wire. Same
    job, opposite world, and the pair of them says the transition better than
    any sign would: you have left the place where light was equipment.
    """
    s = []
    W, H = 90, 72
    cx = -14.0
    s.append(poly([(cx - 3.0, 0.0), (cx + 3.0, 0.0), (cx + 6.0, 54.0), (cx, 54.0)],
                  _lerp(TIMBER, TIMBER_DARK, 0.2), z=0))
    s.append(poly([(cx + 1.0, 0.0), (cx + 3.0, 0.0), (cx + 6.0, 54.0), (cx + 4.0, 54.0)],
                  _lerp(TIMBER, TIMBER_LIT, 0.46), z=0.1))
    wire = [(cx + 5.0, 53.0)]
    for k in range(1, 9):
        u = k / 8.0
        wire.append((cx + 5.0 + 44.0 * u, 53.0 - 18.0 * math.sin(u * math.pi) - 4.0 * u))
    s.append(poly([(x, y + 1.3) for x, y in wire] + [(x, y - 1.3) for x, y in wire][::-1],
                  _lerp(IRON, TIMBER_DARK, 0.4), z=1))
    for k, (bx, by) in enumerate(wire[2::2]):
        s.append(rect(bx - 1.8, by - 5.0, bx + 1.8, by - 1.0, IRON, z=1.4))   # the socket
        _bulb(s, bx, by - 8.0, z=2.0, r=2.6 if k == 1 else 2.1, hot=True)
    _tide(s, cx - 8.0, cx + 52.0, 2.0, z=40, n=5)
    return s, (W, H)


# ---------------------------------------------------------------------------
def swing_boat():
    """A pendulum swing boat, ~4 tiles, stopped off vertical.

    STOPPED OFF VERTICAL IS THE WHOLE PIECE. A pendulum at rest hangs plumb.
    This one does not -- it is held about twenty degrees over, which is a thing
    a pendulum physically cannot do unless something is jamming it. Nothing in
    the frame explains what. That unexplained tilt is worth more than any amount
    of added wreckage: the region's premise is that the machinery KEPT GOING
    after it should have stopped, and this is the one piece that is caught in
    the act.
    """
    s = []
    W, H = 170, 128
    cx, ax_y = 4.0, 104.0
    ANG = 0.36
    # the A-frame
    for sg in (-1.0, 1.0):
        s.append(poly([(cx + sg * 52.0 - 7.0, 0.0), (cx + sg * 52.0 + 7.0, 0.0),
                       (cx + sg * 5.0 + 4.0, ax_y), (cx + sg * 5.0 - 4.0, ax_y)],
                      _lerp(TIMBER, TIMBER_LIT, 0.3 if sg < 0 else 0.0), z=0))
    s.append(rect(cx - 58.0, 40.0, cx + 58.0, 46.0, _lerp(TIMBER, TIMBER_DARK, 0.2), z=0.2))
    s.append(blob(IRON, 8.0, 8.0, off=(cx, ax_y), z=1))
    # the arms and the boat, swung over
    dx, dy = math.sin(ANG), -math.cos(ANG)
    bx, by = cx + dx * 68.0, ax_y + dy * 68.0
    for sg in (-1.0, 1.0):
        s.append(poly([(cx + sg * 4.0, ax_y), (bx + sg * 13.0, by),
                       (bx + sg * 13.0 + 3.0, by), (cx + sg * 4.0 + 3.0, ax_y)],
                      _lerp(IRON, IRON_LIT, 0.3), z=1.2))
    # the hull of the boat: pointed both ends, gunwale in ghost-red
    hullpts = [(bx - 30.0, by + 6.0), (bx - 8.0, by - 12.0), (bx + 8.0, by - 12.0),
               (bx + 30.0, by + 6.0), (bx + 22.0, by + 14.0), (bx - 22.0, by + 14.0)]
    s.append(poly(hullpts, _lerp(PAINT_CREAM, TIMBER, 0.42), z=2))
    s.append(poly([(bx - 30.0, by + 6.0), (bx + 30.0, by + 6.0),
                   (bx + 30.0, by + 9.4), (bx - 30.0, by + 9.4)],
                  _lerp(PAINT_RED, TIMBER, 0.06), z=2.1))
    _bulb(s, bx, by + 16.0, z=3.0, r=1.9)
    _tide(s, cx - 62.0, cx + 62.0, 2.0, z=40, n=10)
    return s, (W, H)


# ---------------------------------------------------------------------------
def boardwalk():
    """Duckboards over the waterline, ~0.8 tiles: the midway underfoot.

    THE ONLY PIECE HERE THAT IS INFRASTRUCTURE, and the region needs one. Region
    2 has 359 water tiles scattered through it as standing pools, and a carnival
    with no way to walk between its attractions is a set of attractions in a
    swamp. Boards say people came through here on purpose.

    ONE BOARD IS MISSING AND TWO ARE FLOATED OFF TRUE. A complete run of
    duckboards is a floor; a run with a gap in it is a route somebody has to
    step over, which is the same authorship as the Shelf's `plank_bridge`.
    """
    s = []
    W, H = 180, 26
    for i in range(13):
        if i == 8:
            continue                                   # the missing board
        x = -78.0 + i * 12.6
        drift = (_h(i, 67) - 0.5) * 3.4
        tilt = (_h(i, 71) - 0.5) * 2.6 if i in (5, 11) else 0.0
        s.append(poly([(x + drift, 4.0 + tilt), (x + drift + 9.4, 4.0 - tilt),
                       (x + drift + 9.4, 12.0 - tilt), (x + drift, 12.0 + tilt)],
                      _lerp(TIMBER, TIMBER_LIT, 0.16 + _h(i, 73) * 0.34), z=1 + i * 0.01))
    for y in (5.0, 11.0):                              # the two stringers under
        s.append(rect(-82.0, y - 2.0, 82.0, y + 1.0, _lerp(TIMBER, TIMBER_DARK, 0.44), z=0))
    _tide(s, -84.0, 84.0, 2.0, z=40, n=12, scale=0.8)
    return s, (W, H)


PIECES = {
    "wheel": wheel,
    "carousel": carousel,
    "carousel_horse": carousel_horse,
    "strength_tester": strength_tester,
    "ticket_booth": ticket_booth,
    "booth": booth,
    "tent": tent,
    "tent_pole": tent_pole,
    "bunting": bunting,
    "festoon_lamp": festoon_lamp,
    "swing_boat": swing_boat,
    "boardwalk": boardwalk,
}


def build(name):
    shapes, size = PIECES[name]()
    # The rim is the WATERLINE's light, not the Shelf's kelp green: up here the
    # surface is close enough to throw a pale, slightly cold sky onto every top
    # edge. It is the cheapest way to say "the sky is a real thing again".
    p = Painter(size, rim_col=(168, 190, 196))
    return p.render(_root(), shapes, {})


def main(argv):
    want = argv[1:] or list(PIECES)
    OUT.mkdir(parents=True, exist_ok=True)
    for name in want:
        if name not in PIECES:
            print("unknown piece: %s (have: %s)" % (name, ", ".join(PIECES)))
            return 2
        t = time.time()
        img = build(name)
        img.save(OUT / ("%s.png" % name))
        print("%-16s %5.2fs  %dx%d" % (name, time.time() - t, img.width, img.height))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
