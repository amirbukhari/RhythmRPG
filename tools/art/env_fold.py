"""The Fold's environment kit -- the town, so the Fold is a place and not a hue.

    python3 tools/art/env_fold.py            # all pieces
    python3 tools/art/env_fold.py lamp house_a

WHY THIS EXISTS
The overworld already has a hand-placement system (ArenaComposer's kits and
OverworldScene.decorate, both authored piece by piece -- "items need to be placed
with intention. none of this scattering shit"). What it did NOT have was art:
of the 171 `env_*` texture keys the code asks for, exactly one existed, so every
authored placement silently rendered nothing. The Fold therefore read as
monochrome teal rock -- no houses, no windows, and not one prayer-lamp, in a
region world-bible §6.1 describes as somewhere the player "should like it here."

WHY NOT THE EXISTING MANIFEST
Region 0's kit was named `shallows` and its keys are nautical -- boat, buoy,
lifering, net, oar, crab, starfish. That is a harbour beach. The Fold is "a
gothic town built in the silt around a massive obelisk" at the bottom of a
lightless sea (world-bible §2), and its accent is already Fold teal, so the slot
is right and the contents were stale. Building 36 nautical props would have been
building the wrong game very carefully. The retired `attic` / `hall` / `pit` /
`saltmines` kits are left alone for the same reason -- they belong to a
cosmology v16.0 deleted, and they are M4's problem, not this file's.

THE PIECES, AND WHAT EACH ONE IS FOR
Every piece is here because canon names it, not because a town generally has one:

  lamp       the prayer-lamps -- "the only warm light in the frame" (§6.1). The
             single most important piece in the kit: it is the one warm accent
             in an all-teal region, and there were none.
  house_a/b  salt-crusted gothic houses with lit windows. Turns rock into a town.
  house_tall a steeper, narrower neighbour, so a street has a skyline.
  house_row  a TERRACE of three -- the density piece. See house_row's docstring:
             a street of separately-placed houses reads as a hamlet.
  arch       a street arch, for framing a view down the plaza.
  bench      the clock-keeper's bench -- Mir's trade (§5), and the one prop in
             the world that is specifically HIS.
  ring_stone the worn kneeling stones of the Rite's concentric rings (§6.1).
  well       the town well -- a reason to stand in the middle of a plaza.
  crate_stack/cart  salt crates and an abandoned handcart, for the wall feet and
             the empty middles. Density is what separates a town from buildings.
  shrine     a wall niche with a small stone figure -- a domestic echo of the
             stone child, so the litho's image recurs at ankle height.

Rendered through the same `rig.Painter` as the cast, deliberately: one key light,
the cool rim, the dark silhouette halo, the additive emissive pass and the same
deterministic grain. A kit built on its own renderer would read as a different
game standing next to Mir.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import palette as P  # noqa: E402
from rig import Blob, Joint, Painter, Poly, Skeleton  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "env" / "fold"

# Fold materials. Salt-crusted stone reads COLDER than the cast so the figures
# stay the warmest-lit things on screen; the lamps are the only exception.
#
# THESE ARE DARKER THAN THEY LOOK RIGHT IN ISOLATION, ON PURPOSE. The first
# values (STONE 58,70,76) previewed correctly against a flat dark ground and
# came back from the game as a pale grey-blue billboard: the overworld lays
# additive haze and god-rays over everything, and a tall sprite collects more of
# both than a low one, so a building is lifted toward the light far harder than a
# prop is. Stone is therefore authored ~30% down from where it reads right, which
# is what leaves the lit windows as the brightest thing on the street -- the
# whole point of §6.1's "only warm light in the frame".
STONE = (40, 49, 55)
STONE_LIT = (62, 74, 80)
STONE_DARK = (24, 31, 36)
SALT = (128, 139, 136)
ROOF = (26, 32, 40)
ROOF_LIT = (40, 48, 57)
IRON = (28, 33, 38)
WINDOW = (236, 190, 112)
TIMBER = (62, 52, 44)


def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _root():
    """A static piece is a one-joint skeleton: no animation, but it inherits the
    cast's exact lighting, rim, halo and grain."""
    return Skeleton([Joint("root", None, (0.0, 0.0), 0.0, 0.0)])


# Architecture takes a MUCH weaker rim than the cast, and this is the single
# thing that separates a building from a neon sign. The rim light is a thin
# bright line on the lit silhouette edge: on a small rounded figure it reads as
# atmosphere, but on a big flat rectangle it traces all four edges evenly and the
# piece comes back looking like a wireframe. Figures keep rim 1.0; stone gets
# 0.22, enough to lift an edge off the ground plate and no more.
STONE_RIM = 0.22


def rect(x0, y0, x1, y1, col, z=0, glow=0.0, rim=STONE_RIM):
    return Poly("root", col, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z=z, glow=glow, rim=rim)


def poly(pts, col, z=0, glow=0.0, rim=STONE_RIM):
    return Poly("root", col, pts, z=z, glow=glow, rim=rim)


def blob(col, rx, ry, off, z=0, glow=0.0, rim=STONE_RIM):
    """A rounded mass at the ARCHITECTURE rim, not the cast's.

    `Blob` defaults to the figure rim (1.0) and it shows: every wheel, kneeling
    stone and salt heap in the kit came back wearing a bright teal outline, which
    on a small dark object reads as a neon decal rather than as a rim light. Use
    this for anything made of stone, iron or timber; keep the raw `Blob` for the
    emissive flames, which want the full treatment."""
    return Blob("root", col, rx, ry, off=off, z=z, glow=glow, rim=rim)


def _h(i, salt=0):
    """Deterministic jitter -- no RNG anywhere in the art pipeline."""
    v = (i * 73856093) ^ (salt * 19349663)
    v &= 0xFFFFFFFF
    v = (v ^ (v >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65536.0


# ---------------------------------------------------------------------------
# the prayer-lamp -- §6.1's "only warm light". Iron cage, warm flame, on a post.
# ---------------------------------------------------------------------------
def lamp():
    s = []
    s.append(rect(-2.0, 0.0, 2.0, 96.0, IRON, z=0))            # post
    s.append(rect(-9.0, 6.0, 9.0, 10.0, IRON, z=1))            # foot
    s.append(poly([(-1.5, 96.0), (14.0, 108.0), (16.0, 104.0), (0.5, 92.0)], IRON, z=1))  # arm
    # the cage: four uprights and two hoops, drawn as thin bars so the flame
    # shows between them -- a solid lantern body would hide the one warm note.
    for dx in (8.0, 12.0, 20.0, 24.0):
        s.append(rect(dx, 76.0, dx + 1.6, 102.0, IRON, z=3))
    s.append(rect(7.0, 100.0, 25.0, 103.5, IRON, z=3))
    s.append(rect(7.0, 74.0, 25.0, 77.5, IRON, z=3))
    s.append(poly([(7.0, 103.0), (16.0, 114.0), (25.0, 103.0)], IRON, z=4))  # cap
    # the flame, emissive
    s.append(blob((255, 214, 140), 5.4, 8.0, off=(16.0, 88.0), z=2, glow=1.0))
    s.append(blob((255, 246, 214), 2.6, 4.2, off=(16.0, 89.0), z=2, glow=1.0))
    return s, (56, 124)


# One window in four is DARK. This is the cheapest sad detail in the kit and it
# was missing: with every window in every house lit, the Fold read as a
# gingerbread village. A town where some windows are out is both truer and
# quieter -- and it matters later, because the story is about somebody leaving.
# Deterministic off `_h(index, salt)`, so a house is dark in the same windows
# every rebuild.
DARK_RATE = 0.26
DARK_GLASS = (20, 26, 31)


def _windows(s, cells, z=3, salt=0):
    """Windows. Warm, small, and never a whole facade of them: the palette rule
    is that the brightest thing must be SMALL, and a wall of lit glass turns a
    house into a lantern."""
    for i, (x0, y0, w, h) in enumerate(cells):
        s.append(rect(x0 - 1.2, y0 - 1.2, x0 + w + 1.2, y0 + h + 1.2, IRON, z=z))
        if _h(i, 101 + salt) < DARK_RATE:
            s.append(rect(x0, y0, x0 + w, y0 + h, DARK_GLASS, z=z + 1, rim=0.0))
            # a single glint, so a dark window still reads as GLASS and not a hole
            s.append(poly([(x0, y0 + h), (x0 + w * 0.45, y0 + h), (x0, y0 + h * 0.5)],
                          _lerp(DARK_GLASS, STONE_LIT, 0.5), z=z + 2, rim=0.0))
        else:
            s.append(rect(x0, y0, x0 + w, y0 + h, WINDOW, z=z + 1, glow=0.8))


def _crust(s, x0, x1, y, z=5):
    """Salt crusting along a ledge -- the detail that says 'this has been under
    water for a very long time' without a single extra texture.

    Evenly spaced same-sized blobs read as RIVETS, which is worse than no
    detail at all, so size, spacing and height all jitter off a hash and the
    colour is well down from `SALT` -- crusting is a texture, not a highlight.
    """
    x = x0 + 2.0
    i = 0
    while x < x1 - 2.0:
        k = _h(i, 7)
        rx = 1.8 + k * 3.4
        s.append(blob(_lerp(SALT, STONE_LIT, 0.45 + _h(i, 9) * 0.4),
                      rx, 0.9 + _h(i, 11) * 1.1,
                      off=(x, y + _h(i, 13) * 2.2 - 0.6), z=z, rim=0.0))
        x += rx * 1.6 + 2.0 + _h(i, 17) * 5.0
        i += 1


# ---------------------------------------------------------------------------
# THE HOUSES, AND WHY THEY ARE THIS WIDE
# The first cut of these was 30 units wide and 196 tall. Rendered into the world
# at the canonical scale (9m tall, 2.8m wide) they came back as LIGHTHOUSES: a
# preview of the whole town read as six isolated towers standing in a field.
# A town house in this projection is its facade, and a facade is about as wide
# as it is tall -- so the bodies below are 1:1 to 1:2, never 1:3. The frames are
# kept tight to the art for the same reason: `worldScaleFor` scales by SOURCE
# HEIGHT, so empty pixels above the roof silently shrink the building.
# ---------------------------------------------------------------------------
def house_a():
    """The default Fold house: two storeys, steep gable, four lit windows."""
    s = []
    s.append(rect(-72.0, 0.0, 72.0, 128.0, STONE, z=0))
    s.append(rect(-72.0, 0.0, -52.0, 128.0, STONE_DARK, z=1))     # shaded return
    s.append(rect(50.0, 0.0, 72.0, 128.0, STONE_LIT, z=1))        # lit face
    s.append(rect(-72.0, 120.0, 72.0, 128.0, STONE_LIT, z=2))     # eaves course
    s.append(poly([(-84.0, 126.0), (0.0, 186.0), (84.0, 126.0)], ROOF, z=2))
    s.append(poly([(0.0, 186.0), (84.0, 126.0), (70.0, 126.0), (0.0, 176.0)], ROOF_LIT, z=3))
    s.append(rect(-12.0, 0.0, 14.0, 48.0, TIMBER, z=2))           # door, off-centre
    s.append(rect(-14.0, 46.0, 16.0, 50.0, IRON, z=3))            # lintel
    _windows(s, [(-52.0, 62.0, 18.0, 22.0), (24.0, 62.0, 18.0, 22.0),
                 (-52.0, 96.0, 18.0, 18.0), (24.0, 96.0, 18.0, 18.0),
                 (-9.0, 140.0, 16.0, 16.0)], salt=3)              # attic light
    _crust(s, -72.0, 72.0, 4.0)
    return s, (176, 194)


def house_b():
    """Squat and wide -- a workshop, roof pitched off-centre so it never reads
    as house_a flipped."""
    s = []
    s.append(rect(-92.0, 0.0, 92.0, 86.0, STONE, z=0))
    s.append(rect(-92.0, 0.0, -70.0, 86.0, STONE_DARK, z=1))
    s.append(rect(68.0, 0.0, 92.0, 86.0, STONE_LIT, z=1))
    s.append(rect(-92.0, 79.0, 92.0, 86.0, STONE_LIT, z=2))
    s.append(poly([(-104.0, 84.0), (-14.0, 126.0), (104.0, 84.0)], ROOF, z=2))
    s.append(poly([(-14.0, 126.0), (104.0, 84.0), (88.0, 84.0), (-14.0, 117.0)], ROOF_LIT, z=3))
    s.append(rect(26.0, 0.0, 54.0, 44.0, TIMBER, z=2))
    s.append(rect(24.0, 42.0, 56.0, 46.0, IRON, z=3))
    _windows(s, [(-74.0, 44.0, 20.0, 22.0), (-44.0, 44.0, 20.0, 22.0), (-12.0, 44.0, 20.0, 22.0)], salt=11)
    _crust(s, -92.0, 92.0, 4.0)
    return s, (212, 132)


def house_tall():
    """The skyline piece: three storeys and a chimney, so a street has something
    to look up at. Narrow, but 1:2 -- not the 1:3 spike this started as."""
    s = []
    s.append(rect(-48.0, 0.0, 48.0, 190.0, STONE, z=0))
    s.append(rect(-48.0, 0.0, -33.0, 190.0, STONE_DARK, z=1))
    s.append(rect(32.0, 0.0, 48.0, 190.0, STONE_LIT, z=1))
    for y in (64.0, 122.0):                                        # floor bands
        s.append(rect(-48.0, y, 48.0, y + 4.0, STONE_DARK, z=2))
    s.append(rect(-48.0, 183.0, 48.0, 190.0, STONE_LIT, z=2))
    s.append(poly([(-58.0, 188.0), (0.0, 244.0), (58.0, 188.0)], ROOF, z=2))
    s.append(poly([(0.0, 244.0), (58.0, 188.0), (46.0, 188.0), (0.0, 235.0)], ROOF_LIT, z=3))
    # Same fix as house_row: the roof at x=34 is y=211, so a base at 232 hung
    # 21px clear of the tiles. Buried under the downhill corner instead.
    s.append(rect(18.0, 206.0, 34.0, 240.0, STONE_DARK, z=4))      # chimney
    s.append(rect(19.0, 206.0, 22.0, 240.0, _lerp(STONE, STONE_DARK, 0.4), z=4.1))
    s.append(rect(15.0, 236.0, 37.0, 241.0, IRON, z=5))
    s.append(rect(-11.0, 0.0, 13.0, 44.0, TIMBER, z=2))
    _windows(s, [(-30.0, 24.0, 16.0, 20.0),
                 (-30.0, 80.0, 16.0, 20.0), (10.0, 80.0, 16.0, 20.0),
                 (-30.0, 138.0, 16.0, 20.0), (10.0, 138.0, 16.0, 20.0)], salt=19)
    _crust(s, -48.0, 48.0, 4.0)
    return s, (128, 272)


def house_row():
    """A TERRACE -- three houses sharing two party walls, as one piece.

    This exists because of density, and density is the difference between a town
    and some buildings. Placed as singles at world scale, the houses have to sit
    four tiles apart to avoid overlapping, and a street of four-tile gaps reads
    as a hamlet. Real towns are terraces. Bay heights, door positions and lit
    windows all jitter off `_h`, so the three bays are neighbours rather than
    one stamp repeated -- and the whole street front is a single placement.
    """
    s = []
    bays = [(-168.0, -56.0), (-56.0, 56.0), (56.0, 168.0)]
    for bi, (x0, x1) in enumerate(bays):
        top = 88.0 + _h(bi, 41) * 46.0                             # uneven roofline
        mid = (x0 + x1) / 2.0
        s.append(rect(x0, 0.0, x1, top, STONE, z=0))
        s.append(rect(x0, 0.0, x0 + 14.0, top, STONE_DARK, z=1))   # party-wall shadow
        s.append(rect(x1 - 12.0, 0.0, x1, top, STONE_LIT, z=1))
        s.append(rect(x0, top - 7.0, x1, top, STONE_LIT, z=2))
        apex = top + 30.0 + _h(bi, 43) * 26.0
        s.append(poly([(x0 - 6.0, top - 2.0), (mid, apex), (x1 + 6.0, top - 2.0)], ROOF, z=2))
        s.append(poly([(mid, apex), (x1 + 6.0, top - 2.0), (x1 - 6.0, top - 2.0), (mid, apex - 9.0)],
                      ROOF_LIT, z=3))
        dx = mid - 13.0 + (_h(bi, 47) - 0.5) * 40.0
        s.append(rect(dx, 0.0, dx + 26.0, 44.0, TIMBER, z=2))
        s.append(rect(dx - 2.0, 42.0, dx + 28.0, 46.0, IRON, z=3))
        # one bay in three keeps its upper windows dark -- somebody is out
        cells = [(mid - 42.0, 58.0, 18.0, 20.0), (mid + 24.0, 58.0, 18.0, 20.0)]
        if _h(bi, 53) > 0.34:
            cells.append((mid - 9.0, top - 30.0, 16.0, 16.0))
        _windows(s, cells, salt=23 + bi * 7)
        # A CHIMNEY IS BUILT INTO A ROOF, so its base has to come from the ROOF
        # SURFACE and not from `apex`. This measured the base off the ridge and
        # then placed the stack two-thirds of the way DOWN the slope, so it hung
        # ~20px clear of the tiles: in-world, two chimneys floating in open water
        # above the terrace. Take the height under the stack's DOWNHILL corner --
        # the lowest point of its footprint -- and bury the base below it, and it
        # cannot detach at any bay height the jitter picks.
        def roof_y(x, x0=x0, x1=x1, mid=mid, top=top, apex=apex):
            if x <= mid:
                t = (x - (x0 - 6.0)) / max(1.0, mid - (x0 - 6.0))
            else:
                t = ((x1 + 6.0) - x) / max(1.0, (x1 + 6.0) - mid)
            return (top - 2.0) + (apex - (top - 2.0)) * max(0.0, min(1.0, t))

        if _h(bi, 59) > 0.55:
            ck = mid + 14.0 + _h(bi, 61) * 24.0            # on the lit slope
            cb = roof_y(ck + 7.0) - 5.0                    # downhill corner, buried
            s.append(rect(ck - 7.0, cb, ck + 7.0, cb + 34.0, STONE_DARK, z=4))
            s.append(rect(ck - 6.0, cb, ck - 3.0, cb + 34.0, _lerp(STONE, STONE_DARK, 0.4), z=4.1))
            s.append(rect(ck - 9.5, cb + 30.0, ck + 9.5, cb + 35.0, IRON, z=5))
    _crust(s, -168.0, 168.0, 4.0)
    return s, (356, 180)


def arch():
    """A street arch. Frames a view down the plaza and gives the flat middle
    distance a foreground to sit behind.

    AN ARCH IS A HOLE, AND THE HOLE HAS TO BE EMPTY. This drew its opening as an
    opaque arched polygon in (14, 18, 23) -- a "dark interior" -- and at the 55px
    world size it ships at, 25 levels of separation from the piers is nothing:
    the whole piece arrived as a solid dark slab with a salt-crusted bottom edge,
    reading as a floating wall. Nothing is drawn in the opening now. What makes
    the arch an arch is the SPANDREL: the stone between the curve and the
    lintel, which is what gives the silhouette its arched underside.
    """
    s = []
    springs = 96.0
    R = 19.0
    for sx in (-1.0, 1.0):
        s.append(rect(sx * 30.0 - 11.0, 0.0, sx * 30.0 + 11.0, 118.0, STONE, z=0))
        s.append(rect(sx * 30.0 - 11.0, 0.0, sx * 30.0 - 5.0, 118.0, STONE_DARK, z=1))
    s.append(rect(-44.0, 116.0, 44.0, 138.0, STONE, z=2))
    s.append(rect(-44.0, 132.0, 44.0, 138.0, STONE_LIT, z=3))
    # the spandrel: stone from the arch curve up to the lintel's underside, so
    # the opening's top edge is a curve instead of a straight soffit
    span = [(-R, springs)]
    for i in range(13):
        a = math.pi * (1.0 - i / 12.0)
        span.append((math.cos(a) * R, springs + math.sin(a) * R))
    span += [(R, 118.0), (-R, 118.0)]
    s.append(poly(span, STONE, z=4))
    # and the arch ring itself, one shade down, so the curve is a MOULDING and
    # not just where two flat shapes happen to meet
    ring = []
    for i in range(17):
        a = math.pi * (1.0 - i / 16.0)
        ring.append((math.cos(a) * R, springs + math.sin(a) * R))
    for i in range(17):
        a = math.pi * (i / 16.0)
        ring.append((math.cos(a) * (R - 3.2), springs + math.sin(a) * (R - 3.2)))
    s.append(poly(ring, _lerp(STONE, STONE_LIT, 0.45), z=5))
    # the crust follows the PIERS, not the span: run it across the opening and
    # salt blobs float in mid-air where the gap is
    for sx in (-1.0, 1.0):
        _crust(s, sx * 30.0 - 11.0, sx * 30.0 + 11.0, 4.0)
    _crust(s, -44.0, 44.0, 138.0)
    return s, (110, 160)


def bench():
    """The clock-keeper's bench (§5) -- the one prop in the world that is
    specifically Mir's. A plank, two iron legs, and a small brass part left on
    it, because he never finishes anything before he has to go."""
    s = []
    s.append(rect(-26.0, 20.0, 26.0, 26.0, TIMBER, z=1))
    s.append(rect(-26.0, 24.0, 26.0, 26.0, (86, 72, 60), z=2))
    for x in (-22.0, 18.0):
        s.append(rect(x, 0.0, x + 4.0, 20.0, IRON, z=0))
    s.append(rect(-26.0, 8.0, 26.0, 10.5, IRON, z=0))
    s.append(blob(P.BRASS, 3.4, 3.4, off=(8.0, 29.0), z=3, glow=0.5))
    s.append(blob(P.BRASS, 1.8, 1.8, off=(-6.0, 28.0), z=3, glow=0.4))
    return s, (72, 44)


def ring_stone():
    """One of the worn kneeling stones of the Rite's concentric rings (§6.1).
    Low, rounded, and polished on top by a very large number of knees."""
    #
    # LIGHTER THAN THE REST OF THE STONE, and deliberately. The rings sit on the
    # plaza's pale paving rather than against dark silt, and they are low enough
    # to collect almost none of the haze that forced the buildings down -- at the
    # buildings' value they came back as a ring of black tyres around the
    # monolith. These are stones a town has knelt on for generations: worn, and
    # polished enough to catch the light.
    #
    # AND IT ONLY GETS TWO TONES. `worldScaleFor` clamps this piece at
    # MIN_SCALE, so it ships at 12x6 PIXELS. The first cut layered three blobs;
    # at 6 pixels tall the 3-unit polished highlight rendered sub-pixel and
    # vanished, the wide dark contact blob did not, and the ring came back
    # reading as black beans on pale paving -- the exact failure the comment
    # above was written to prevent, reintroduced by detail rather than by value.
    # Two tones, both light, and no contact blob at all: `placeAuthoredDressing`
    # already draws every piece a proportional ground shadow, so a second one
    # baked into the sprite was just darkening the average.
    s = []
    s.append(blob(_lerp(STONE, SALT, 0.44), 13.0, 6.4, off=(0.0, 6.2), z=0))
    s.append(blob(_lerp(SALT, STONE_LIT, 0.30), 9.0, 3.6, off=(0.8, 9.0), z=1))
    return s, (44, 24)


def shrine():
    """A wall niche with a small stone figure -- a domestic echo of the stone
    child, so the image the premise hangs on recurs at ankle height instead of
    only in a cutscene."""
    s = []
    s.append(rect(-20.0, 0.0, 20.0, 92.0, STONE, z=0))
    s.append(rect(-20.0, 0.0, -12.0, 92.0, STONE_DARK, z=1))
    s.append(poly([(-22.0, 90.0), (0.0, 104.0), (22.0, 90.0)], STONE_LIT, z=2))
    s.append(rect(-11.0, 30.0, 11.0, 72.0, (18, 22, 27), z=3, rim=0.0))   # the niche
    # THE FIGURE, AND WHY IT IS NOT TWO BLOBS.
    # It was: a 9px SALT head over a 13x20 SALT ellipse, in a 22x42 black box.
    # In-world that is one pale egg filling a phone booth -- the two blobs share
    # a tone so they merge, SALT is the palest colour in the kit so the largest
    # object in the piece became its brightest (style-contract §3 says the
    # brightest thing is SMALL, and here that is the votive), and an ellipse has
    # no shoulders so nothing says "figure" at all.
    #
    # THE VOTIVE IS BELOW IT, so the light comes from UNDERNEATH. That is the
    # whole trick: carve the value gradient upward-dark, and a lump becomes a
    # thing being lit by a candle. Stone tones, a shoulder taper, and a ledge to
    # stand on -- the same three moves the obelisk needed.
    s.append(rect(-9.0, 42.0, 9.0, 45.0, _lerp(STONE, STONE_DARK, 0.5), z=4, rim=0.0))  # ledge
    body = [(-5.4, 45.0), (5.4, 45.0), (4.0, 56.0), (3.0, 59.0), (-3.0, 59.0), (-4.0, 56.0)]
    s.append(poly(body, _lerp(STONE, SALT, 0.30), z=4, rim=0.0))         # swaddling
    s.append(poly([(-5.4, 45.0), (5.4, 45.0), (4.6, 49.0), (-4.6, 49.0)],
                  _lerp(STONE, SALT, 0.52), z=4.1, rim=0.0))             # uplit hem
    s.append(poly([(-4.0, 54.0), (4.0, 54.0), (3.0, 59.0), (-3.0, 59.0)],
                  _lerp(STONE, STONE_DARK, 0.30), z=4.2, rim=0.0))       # shoulders, in shade
    s.append(blob(_lerp(STONE, SALT, 0.16), 3.4, 3.6, off=(0.6, 62.4), z=4.3, rim=0.0))
    s.append(blob(_lerp(STONE, SALT, 0.44), 2.6, 1.5, off=(0.4, 60.6), z=4.4, rim=0.0))  # chin
    # the candle's own shadow, thrown UP the back wall -- proof of the direction
    s.append(poly([(-6.5, 59.0), (6.5, 59.0), (8.0, 72.0), (-8.0, 72.0)],
                  (11, 14, 18), z=3.5, rim=0.0))
    s.append(blob((255, 210, 138), 3.0, 3.0, off=(0.0, 34.0), z=5, glow=1.0))  # a votive
    _crust(s, -20.0, 20.0, 4.0)
    return s, (60, 116)


def well():
    """The town well -- the one piece of Fold architecture that is a REASON to
    stand somewhere. A plaza with nothing in the middle of it is a field, and
    the street between the obelisk and the terrace was reading as one."""
    s = []
    s.append(blob(STONE_DARK, 30.0, 11.0, off=(0.0, 6.0), z=0))
    s.append(rect(-26.0, 4.0, 26.0, 38.0, STONE, z=1))
    s.append(rect(-26.0, 4.0, -17.0, 38.0, STONE_DARK, z=2))
    s.append(rect(16.0, 4.0, 26.0, 38.0, STONE_LIT, z=2))
    s.append(blob((10, 14, 18), 22.0, 7.0, off=(0.0, 38.0), z=3, rim=0.0))   # the shaft
    s.append(blob(_lerp((10, 14, 18), P.FOLD, 0.35), 13.0, 4.0, off=(1.0, 37.0), z=4, rim=0.0))
    for x in (-22.0, 18.0):                                                          # the frame
        s.append(rect(x, 34.0, x + 4.0, 82.0, TIMBER, z=4))
    s.append(rect(-24.0, 78.0, 22.0, 84.0, TIMBER, z=5))
    s.append(rect(-6.0, 66.0, 6.0, 78.0, IRON, z=5))                                 # windlass
    s.append(rect(-0.8, 44.0, 0.8, 66.0, IRON, z=4))                                 # the rope
    s.append(rect(-5.0, 40.0, 5.0, 46.0, IRON, z=5))                                 # the bucket
    _crust(s, -26.0, 26.0, 6.0)
    return s, (72, 96)


def crate_stack():
    """Salt crates, stacked and strapped. Fills a wall foot without pretending
    to be a landmark."""
    s = []
    # A CRATE READS FROM ITS BRACE, and the first cut got that wrong. It drew
    # one vertical iron strap down each box, which at the 17-world-px size this
    # ships at split every crate into two tall bars -- the stack came back
    # looking like a xylophone. What says "crate" small is a LID LINE plus a
    # DIAGONAL: the diagonal is the only mark in the vocabulary that cannot be
    # read as a plank, and it is what the eye uses to call the box wooden.
    # The boxes are also wider than tall now: a crate you can lift is.
    boxes = [(-24.0, 0.0, 26.0, 19.0), (4.0, 0.0, 24.0, 23.0), (-16.0, 19.0, 23.0, 17.0)]
    for i, (x0, y0, w, h) in enumerate(boxes):
        z = i * 3
        lit = _lerp(TIMBER, (108, 92, 74), 0.3 + _h(i, 61) * 0.4)
        s.append(rect(x0, y0, x0 + w, y0 + h, TIMBER, z=z))
        s.append(rect(x0, y0, x0 + 2.0, y0 + h, _lerp(TIMBER, IRON, 0.6), z=z + 1))   # shaded left
        s.append(rect(x0, y0, x0 + w, y0 + 1.8, _lerp(TIMBER, IRON, 0.6), z=z + 1))   # dark foot
        s.append(rect(x0 + w - 3.0, y0, x0 + w, y0 + h, lit, z=z + 1))                # lit right
        s.append(rect(x0, y0 + h - 3.4, x0 + w, y0 + h, lit, z=z + 1))                # the LID
        s.append(rect(x0, y0 + h - 4.6, x0 + w, y0 + h - 3.4, IRON, z=z + 2))         # lid seam
        # the diagonal brace, corner to corner, in the lit timber
        s.append(poly([(x0 + 1.5, y0 + 2.0), (x0 + 4.5, y0 + 2.0),
                       (x0 + w - 1.5, y0 + h - 4.6), (x0 + w - 4.5, y0 + h - 4.6)],
                      lit, z=z + 2))
    _crust(s, -24.0, 28.0, 1.0)
    return s, (60, 56)


def cart():
    """A handcart, still loaded, left where it stood. Nobody is coming for it --
    the same note the whole region is written in.

    The first pass drew a tilted bed with one wheel and a single raised shaft and
    read unmistakably as a CANNON. A cart is legible from three things and it
    needs all three: a level bed, TWO wheels at different depths, and two shafts
    running down to the ground.
    """
    s = []
    # the shafts, down to the ground -- this is what says "put down", not "aimed"
    for dy in (0.0, 5.0):
        s.append(poly([(22.0, 22.0 - dy), (52.0, 3.0 - dy), (54.0, 7.0 - dy), (24.0, 26.0 - dy)],
                      TIMBER, z=0))
    # THE WHEELS NEED SPOKES OR THE CART IS A TABLE. Two dark discs under a
    # level bed vanish into the ground plate at this size, and what is left
    # reads as a bench with a plank top. Spokes are the whole tell: they are the
    # only wheel feature that survives being 8 pixels across.
    def wheel(cx, cy, r, z, tone):
        s.append(blob(IRON, r, r, off=(cx, cy), z=z))
        s.append(blob(_lerp(STONE_DARK, tone, 0.55), r * 0.74, r * 0.74, off=(cx, cy), z=z + 0.1, rim=0.0))
        for k in range(4):
            a = k * math.pi / 4.0 + 0.35
            dx, dy = math.cos(a) * r * 0.66, math.sin(a) * r * 0.66
            s.append(poly([(cx - dx - 0.9, cy - dy), (cx - dx + 0.9, cy - dy),
                           (cx + dx + 0.9, cy + dy), (cx + dx - 0.9, cy + dy)],
                          _lerp(IRON, TIMBER, 0.55), z=z + 0.2, rim=0.0))
        s.append(blob(_lerp(TIMBER, (108, 92, 74), 0.5), r * 0.2, r * 0.2, off=(cx, cy), z=z + 0.3, rim=0.0))

    wheel(6.0, 12.0, 11.0, 1, IRON)                                   # far wheel
    s.append(rect(-30.0, 20.0, 26.0, 32.0, TIMBER, z=3))                     # the bed
    s.append(rect(-30.0, 29.0, 26.0, 32.0, (98, 84, 68), z=4))               # lit top rail
    s.append(rect(-30.0, 20.0, 26.0, 22.5, IRON, z=4))                       # under-rail
    for x in (-26.0, -8.0, 10.0):                                            # side boards
        s.append(rect(x, 22.0, x + 2.2, 30.0, STONE_DARK, z=4))
    wheel(-12.0, 13.0, 13.0, 5, TIMBER)                              # near wheel
    # the load: salt, heaped and still there
    s.append(blob(_lerp(SALT, STONE_DARK, 0.5), 12.0, 3.6, off=(-8.0, 32.0), z=4))
    s.append(blob(_lerp(SALT, STONE_LIT, 0.45), 6.5, 2.0, off=(-11.0, 33.5), z=5, rim=0.0))
    s.append(blob(_lerp(SALT, STONE_LIT, 0.55), 6.0, 2.2, off=(30.0, 3.0), z=3))  # spill
    return s, (120, 60)


# ---------------------------------------------------------------------------
# THE OBELISK -- the thing the town is built around (world-bible §2), and the
# thing the Rite is addressed to (§6.1).
#
# WHAT THIS REPLACES. `OverworldScene.placeTownObelisk` drew it with five
# `Graphics` polygons: a flat silhouette, a flat lit half, and five identical
# cyan rectangles down the middle. In the shipped build that reads as a grey
# gradient WEDGE with tick marks on it -- and style-contract §0 has a rule for
# exactly this case: "an abstraction is not an image." This is the first
# landmark a new player sees, it is the save point they return to all game, and
# it is the object the entire premise hangs off. It cannot be a triangle.
#
# THE FOUR THINGS THAT MAKE IT STONE RATHER THAN A WEDGE
#   1. Volume in FIVE stepped bands, not two. A two-tone split reads as folded
#      paper because the value jump lands on a single hard line down the middle;
#      five bands following the taper read as a round-cornered quarried shaft.
#   2. Courses. It is BUILT: eleven blocks, each seam a thin dark line with a
#      lit lip under it, and the seams jitter so it is masonry and not a ruler.
#   3. Damage. Chips off both silhouette edges and a missing corner off the
#      plinth. An undamaged monolith at the bottom of the sea is a render.
#   4. An old waterline. Salt crust bands the plinth and reappears a third of
#      the way up, where the water used to stand -- so the stone tells you the
#      sea rose, which is the whole geography of the game in one detail.
#
# WHY IT IS BARELY TAPERED. An Egyptian obelisk is close to a slab: 31 units
# at the foot to 17 at the shoulder over 372 of height. The first cut ran
# 34 -> 13 and read as a SPIRE, which is a church, not a monolith -- and a
# spire plus a wide plinth plus lit courses is a rocket.
#
# AND THE GLYPHS ARE WRITING. The five equal dashes are replaced by a recessed
# channel with a lipped edge, holding lines of glyphs of DIFFERENT lengths --
# some short, some running the full channel, a few blank where the carving is
# worn away. You cannot read it, which is correct, but you can tell that
# somebody wrote it, which the dashes could not say.
# ---------------------------------------------------------------------------
def obelisk():
    s = []
    H_SHAFT = 372.0      # plinth top -> pyramidion base
    Y0 = 34.0            # plinth top
    W_BOT, W_TOP = 31.0, 17.0   # nearly a slab: see WHY IT IS BARELY TAPERED

    def half_w(y):
        """The shaft's half-width at height y -- one taper, used by every band,
        every seam and every chip, so nothing can drift off the silhouette."""
        t = max(0.0, min(1.0, (y - Y0) / H_SHAFT))
        return W_BOT + (W_TOP - W_BOT) * t

    # --- the plinth: low and narrow -------------------------------------
    # The first cut gave it a 124-wide two-tier pad and the whole piece read as
    # a ROCKET ON A LAUNCH PLATFORM. A monolith stands IN the ground; it does
    # not perch on a podium. Two shallow courses, barely wider than the shaft.
    s.append(rect(-44.0, 0.0, 44.0, 14.0, STONE_DARK, z=0))
    s.append(rect(-44.0, 11.0, 44.0, 14.0, _lerp(STONE, STONE_DARK, 0.35), z=1))
    s.append(poly([(-44.0, 0.0), (-44.0, 9.0), (-35.0, 0.0)], STONE_DARK, z=1))  # broken corner
    s.append(rect(-38.0, 14.0, 38.0, 34.0, STONE, z=1))
    s.append(rect(-38.0, 14.0, -27.0, 34.0, STONE_DARK, z=2))    # shaded return
    s.append(rect(28.0, 14.0, 38.0, 34.0, _lerp(STONE, STONE_DARK, 0.4), z=2))
    s.append(rect(-38.0, 31.0, 38.0, 34.0, STONE, z=3))

    # --- the shaft in five bands, lit on the left --------------------------
    # Fractions of the half-width, left (lit) to right (shadow). The narrow 4th
    # band is the shadow TURN -- a body this size needs its dark side to begin
    # before the silhouette edge, or the dark side looks pasted on.
    # WEIGHTED DARK. The first cut gave STONE_LIT the whole left 20% of the
    # shaft and mid-tones the next 23%, and in-world the monolith came back
    # PALER THAN THE HOUSES -- a light grey mast in a dark teal town. It is the
    # same measurement §4.1 records for the houses: the overworld's additive haze
    # and god-rays lift a tall sprite much harder than a prop, so a tall piece
    # must be authored darker than it looks right in isolation. The lit band is
    # now a 7% sliver at the silhouette edge and the shaft's body is STONE.
    # The ramp must also be MONOTONIC AND SMOOTH end to end. It already was --
    # but the carved channel below used to put a bright lip up the middle of it,
    # and pale/mid/dark/BRIGHT/dark/mid/dark is not a slab, it is a bundle of
    # pipes. The lip is gone; these steps are softened so nothing else can read
    # as an edge inside the silhouette.
    BANDS = [(-1.00, -0.88, STONE_LIT), (-0.88, -0.50, _lerp(STONE, STONE_LIT, 0.30)),
             (-0.50, 0.40, STONE), (0.40, 0.76, _lerp(STONE, STONE_DARK, 0.50)),
             (0.76, 1.00, STONE_DARK)]
    yb, yt = Y0, Y0 + H_SHAFT
    for i, (f0, f1, col) in enumerate(BANDS):
        s.append(poly([(half_w(yb) * f0, yb), (half_w(yb) * f1, yb),
                       (half_w(yt) * f1, yt), (half_w(yt) * f0, yt)], col, z=2 + i * 0.01))

    # --- seams, kept FAINT ------------------------------------------------
    # Eleven full-width courses with lit lips turned it into a stack of floors,
    # which together with the glyph blocks read as an office tower. It is a
    # quarried monolith: a few shallow seams, only where the light would catch
    # one, and none across the shadow side.
    # They also stay ABOVE the inscription panel -- a course line crossing the
    # writing put a hard horizontal through it and brought the ladder back.
    for k in range(3):
        y = Y0 + H_SHAFT * 0.44 + (H_SHAFT * 0.44) * (k / 2.0) + (_h(k, 31) - 0.5) * 9.0
        w = half_w(y)
        s.append(poly([(-w, y), (w * 0.5, y), (w * 0.5, y + 1.2), (-w, y + 1.2)],
                      _lerp(STONE, STONE_DARK, 0.55), z=8))

    # --- the inscription, and where it is ---------------------------------
    # WRITING SITS AT EYE LEVEL. This ran a recessed channel with a lit lip the
    # full 372px of the shaft, filled with evenly-spaced marks. In isolation it
    # read as a weathered text. IN-WORLD, at the 28 world px the shaft ships at,
    # it read as a LADDER -- a single centred column of regularly spaced rungs
    # is a ladder, and a ladder up a tall shaft with a lit tip is a launch
    # gantry, which is the one thing this must never be. Two rules came out of
    # looking at it in the browser:
    #   1. the inscription occupies the BOTTOM THIRD only. That is where someone
    #      standing at the plinth could have carved it, and it leaves the 6m
    #      above as unbroken stone -- the unbroken part is what reads as MASS.
    #   2. a line of text is SEVERAL marks with gaps at a varied left margin.
    #      One mark per row, centred, can only ever be a rung.
    INS_Y0, INS_Y1 = Y0 + 26.0, Y0 + H_SHAFT * 0.34
    # a shallow dressed panel, a hair darker than the face, and NO lit lip
    pw0, pw1 = half_w(INS_Y0) * 0.62, half_w(INS_Y1) * 0.62
    s.append(poly([(-pw0, INS_Y0 - 6.0), (pw0, INS_Y0 - 6.0),
                   (pw1, INS_Y1 + 6.0), (-pw1, INS_Y1 + 6.0)],
                  _lerp(STONE, STONE_DARK, 0.22), z=9, rim=0.0))
    y = INS_Y0
    row = 0
    while y < INS_Y1:
        t = (y - INS_Y0) / max(1.0, INS_Y1 - INS_Y0)
        pw = pw0 + (pw1 - pw0) * t
        if _h(row, 53) >= 0.28:                       # worn-blank courses
            x = -pw * (0.62 + _h(row, 59) * 0.24)     # a varied left margin
            k = 0
            while x < pw * 0.70 and k < 5:
                gw = pw * (0.11 + _h(row * 7 + k, 61) * 0.17)
                # DIM. At full glow this column was the brightest object in the
                # region and the stone stopped reading at all; the palette rule
                # is that the brightest thing is SMALL (style-contract §3).
                if _h(row * 7 + k, 67) > 0.74:        # the odd upright stroke,
                    s.append(rect(x, y - 2.6, x + gw * 0.42, y + 2.9,   # which is
                                  (78, 178, 172), z=10, glow=0.58, rim=0.0))
                else:                                  # what a rung cannot do
                    s.append(rect(x, y, x + gw, y + 1.3,
                                  (78, 178, 172), z=10, glow=0.58, rim=0.0))
                x += gw + pw * (0.07 + _h(row * 7 + k, 71) * 0.11)
                k += 1
        y += 7.4 + _h(row, 73) * 2.8
        row += 1

    # --- damage: chips off both edges -------------------------------------
    for k in range(7):
        y = Y0 + 20.0 + (H_SHAFT - 40.0) * _h(k, 71)
        side = 1.0 if _h(k, 73) > 0.5 else -1.0
        w = half_w(y) * side
        d = 2.2 + _h(k, 79) * 4.4
        s.append(poly([(w, y), (w - side * d, y + d * 0.7), (w, y + d * 1.6)],
                      STONE_DARK if side < 0 else _lerp(STONE_DARK, STONE, 0.3), z=11))

    # --- the pyramidion ---------------------------------------------------
    ya = Y0 + H_SHAFT
    wt = half_w(ya)
    apex = ya + 40.0
    s.append(poly([(-wt, ya), (wt, ya), (0.0, apex)], STONE_DARK, z=12))
    s.append(poly([(-wt, ya), (0.0, ya), (0.0, apex)], _lerp(STONE, STONE_LIT, 0.4), z=12.1))
    s.append(poly([(-wt * 0.34, ya + 14.0), (0.0, ya + 14.0), (0.0, apex)], STONE_LIT, z=12.2))
    # the apex light: small and hot. The overworld adds its own beat-driven
    # crown glow on top of this, so the sprite only needs the SOURCE.
    s.append(blob((176, 255, 246), 2.8, 3.2, off=(0.0, apex - 5.0), z=13, glow=1.0, rim=0.0))

    # --- the old waterline, and silt at the foot ---------------------------
    # The crust runs COOL and low here: on a house ledge it is a highlight, but
    # smeared up a 9m shaft it turned the whole silhouette pale.
    _crust(s, -38.0, 38.0, 33.0, z=14)                      # the plinth top
    wl = Y0 + H_SHAFT * 0.30
    _crust(s, -half_w(wl), half_w(wl), wl, z=14)            # where the sea stood
    for k in range(6):
        s.append(blob(_lerp(STONE_DARK, (18, 30, 28), 0.6),
                      5.0 + _h(k, 83) * 8.0, 1.8 + _h(k, 89) * 1.8,
                      off=(-34.0 + k * 14.0 + _h(k, 97) * 5.0, 1.6 + _h(k, 101) * 2.6),
                      z=15, rim=0.0))
    return s, (108, 452)


PIECES = {
    "lamp": lamp,
    "house_a": house_a,
    "house_b": house_b,
    "house_tall": house_tall,
    "house_row": house_row,
    "arch": arch,
    "bench": bench,
    "ring_stone": ring_stone,
    "shrine": shrine,
    "well": well,
    "crate_stack": crate_stack,
    "cart": cart,
    "obelisk": obelisk,
}


def build(name):
    shapes, size = PIECES[name]()
    # The kit's rim is the Fold's own hue, so the whole region reads as one
    # place; the cast keeps its own warmer rim and stays separable from it.
    painter = Painter(size, rim_col=(96, 170, 168))
    return painter.render(_root(), shapes, {})


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
        print("%-11s %5.2fs  %dx%d" % (name, time.time() - t, img.width, img.height))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
