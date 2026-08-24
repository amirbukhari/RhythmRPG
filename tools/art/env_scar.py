"""The Scar's environment kit -- hostile country, and the lie it is telling.

    python3 tools/art/env_scar.py            # all pieces
    python3 tools/art/env_scar.py den_mouth spoil_heap

WHAT THIS REGION IS (world-bible §6.4, and it is a TRICK)
    "On the way through, it reads as hostile country: gouged, burned, pitted,
     picked-over, with a den at the far end. Mir believes a beast took his son
     and the landscape obliges the belief. The player believes it too."
    "Then the den, and the man in it, and the ground stops being a wasteland and
     becomes a search. Everything the player crossed to get here means something
     else on the walk back out."

THE KIT HAS TO WORK TWICE, AND THAT IS THE WHOLE BRIEF. First pass: a beast
lives here. Second pass, after the man: a person has been digging here for
years, alone, and the state of the country is what that does to a place. Every
piece below is chosen because it supports BOTH readings honestly, which means the
first reading is never a cheat -- the player is not lied to, they just read a
dug-over landscape the way a frightened man reads it.

So the rules this kit is authored under are mostly rules about what is NOT here:

  * NO CLAW MARKS, NO TEETH, NO GNAWED ANYTHING, and no bones arranged at a
    threshold. Every one of those is a monster signal that would be a LIE, and
    §6.4 is explicit that the evidence rots the monster story from below: "no
    blood anywhere". A kit that plants fake evidence makes the reveal a twist
    instead of a re-read.
  * NO SKULLS. `bone_pile` is ribs and long bones -- the leftovers of a meal
    somebody had. A skull is a genre signal and it means "predator". Ribs mean
    "hungry".
  * THE MOST-REPEATED PIECE IS A SPOIL HEAP, because "picked-over" is a COUNT,
    not a texture. Twenty heaps of turned earth across a region says somebody
    has been looking for something here for a very long time, and it says it in
    both readings at once. It is also the honest one: it is the reveal, sitting
    in plain sight, for the whole middle of the game.

MATERIAL DISCIPLINE
Authored ~30% darker than it reads right in isolation, for the reason
env_fold.py documents: the overworld lays additive haze and god-rays over
everything and a tall sprite collects far more of both. Verify in the browser
(tools/capture.mjs), never on a contact sheet.

THE ONE WARM RIM IN THE GAME. The Fold, the Shelf and the Breach are all lit
cold -- teal, kelp green, and the Breach's pale cold surface. The Scar is the
first region with nothing overhead but sky, so its rim is a dusty warm sun, and
that single change is what makes the crossing out of region 2 feel like a
different world rather than the next twenty tiles of the same one.

WHERE THE COLOUR IS ALLOWED TO BE
§3: the brightest thing must be small. In this region there are exactly two
places with any saturation in them, and both are tiny:
  * `dig_lamp`'s flame -- somebody works here at night, looking down;
  * the Oasis pieces, which are the only living green and the only clean water
    in the region, and one of which is IN BUD (§6.4: "the only place in the game
    where anything is in motion").
Nothing else here is allowed a hue. Rust is a material, not a wash.

SIZE CONVENTION -- 32 PX PER INTENDED TILE
`worldScaleFor` floors the render scale at 0.5 and snaps to halves, so a piece
authored at 32 px per tile lands on exactly 0.5, downsamples through the
renderer's 4x supersampling instead of being resized twice, and ships EXACTLY as
tall as it was composed. With that convention `metres == tiles` in
`src/scenes/env/WorldScale.ts`, which is why the numbers in the scar block there
look like tile counts. They are. Every piece needs an exact-key entry: without
one, loose patterns already in that table claim these names.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rig import Blob, Joint, Painter, Poly, Skeleton  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "env" / "scar"

# Scar materials. The range is DARK and the range is NARROW -- burnt country has
# no mid-tones in it, it has char and it has ash and almost nothing between.
CHAR = (26, 22, 20)           # burnt through to carbon
CHAR_LIT = (54, 46, 40)
ASH = (106, 102, 96)          # cold pale ash: the only large light value here
ASH_DARK = (68, 65, 60)
EARTH = (62, 44, 33)          # turned dirt, red-brown, freshly cut
EARTH_LIT = (98, 71, 50)
EARTH_DARK = (36, 26, 20)
# The Scar's metal was authored cold (a neutral 44/42/40) back when the ground
# under it was a saturated orange and the contrast was welcome. With the ground
# corrected to a dark warm brown the barrow and the windlass read as ALUMINIUM
# -- cold pale objects on warm dirt. Same lesson as `den_mouth`'s facade, one
# scale down: temperature contrast pops harder than value contrast, and a tool
# somebody carried here for years belongs to the place it has been rusting in.
IRON = (46, 41, 36)
IRON_LIT = (76, 66, 54)
RUST = (122, 62, 30)          # a MATERIAL, not a wash. Used on iron, nowhere else.
BONE = (152, 146, 128)
BONE_DARK = (94, 90, 78)
ROPE = (82, 74, 58)
TIMBER = (52, 44, 34)         # scavenged, re-used, never milled
TIMBER_LIT = (86, 73, 55)
TIMBER_DARK = (30, 26, 20)
SACK = (100, 92, 74)          # pilgrim cloth
STONE = (78, 76, 72)
STONE_LIT = (114, 111, 104)
FLAME = (255, 206, 128)       # emissive, and always small
FLAME_HOT = (255, 244, 216)
# --- THE OASIS, AND NOTHING ELSE IN THIS FILE MAY TOUCH THESE ---------------
# Six colours, quarantined by comment because the temptation to sprinkle "a
# little green" through a brown region is exactly how a region loses its one
# pocket of relief. If any piece other than the three `oasis_*` ones references
# these, the Oasis has stopped being the only place anything is alive.
MOSS = (44, 90, 48)
MOSS_LIT = (88, 144, 72)
LEAF = (110, 160, 78)
BUD = (208, 216, 130)         # pale green-gold: the one thing in bud
# THE SPRING CAME BACK AS CONCRETE. `WATER` was (72,102,102) -- 29% saturation,
# which is the same desaturated grey-teal every OTHER surface in this game is
# painted in, and the result was a lumpy grey slab that read as a boulder or a
# beached animal. It is the only clean water in the world (§6.4) and the only
# restful image in five regions, so it is allowed -- required -- to be the one
# saturated cold thing in the frame. It stays SMALL, which is what §3 actually
# asks: the brightest thing must be small, not absent.
WATER = (38, 96, 116)         # clear cold spring, and it is finally blue
WATER_DEEP = (18, 54, 70)     # the far edge, where you stop seeing the bottom
WATER_LIT = (150, 206, 214)
SKY_GLINT = (226, 242, 240)   # the sky, reflected. The one specular in the kit.


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
    """Deterministic pseudo-random in [0,1). NO RNG ANYWHERE IN THIS PIPELINE --
    every rebuild must be byte-identical or the palette gate and the plate check
    cannot tell a real regression from noise."""
    x = (i * 2654435761 + salt * 40503 + 12345) & 0xFFFFFFFF
    x ^= (x >> 13)
    x = (x * 1274126177) & 0xFFFFFFFF
    return ((x >> 8) & 0xFFFF) / 65536.0


def _flame(s, x, y, z=6, r=3.0):
    """One small flame, layered the way env_breach's bulbs had to be.

    `rig.Painter` blurs an emissive shape by `9 * SS * glow`, so glow=1.0 on a
    three-pixel blob spreads its whole energy over a thirty-six-pixel radius and
    vanishes. The Breach shipped that mistake once (a region whose only warm
    light read as grey beadwork), so: a DARK ember disc at glow=1.0 for the wash,
    a tight envelope, and an opaque hot core that survives the composite.
    """
    s.append(blob(_lerp(FLAME, (56, 26, 6), 0.62), r * 2.6, r * 3.0,
                  off=(x, y), z=z - 0.1, glow=1.0, rim=0.0))
    s.append(blob(_lerp(FLAME, RUST, 0.16), r * 1.3, r * 1.7,
                  off=(x, y), z=z, glow=0.24, rim=0.0))
    s.append(blob(FLAME_HOT, r * 0.5, r * 0.8, off=(x, y + r * 0.3), z=z + 0.1,
                  glow=0.10, rim=0.0))


def _spoil(s, x, w, h, z=0, n=9, warm=0.0):
    """A fan of thrown earth at ground level. Used by every dug piece, because
    the thing all of them have in common is that the material came OUT."""
    for i in range(n):
        t = (i + 0.5) / n
        px = x + (t - 0.5) * w
        r = (w / n) * (0.7 + _h(i, 71) * 0.7)
        hh = h * (1.0 - abs(t - 0.5) * 1.5) * (0.6 + _h(i, 73) * 0.7)
        s.append(blob(_lerp(EARTH_DARK, EARTH, 0.25 + _h(i, 79) * 0.5 + warm),
                      r, max(1.5, hh), off=(px, max(1.0, hh * 0.55)), z=z + i * 0.01))


def _grit(s, x0, x1, y, z=0, n=10, col=None):
    """Loose stones and clinker along a base line. Nothing in this region has a
    clean footing; a hard edge against the ground reads as a decal."""
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
        if _h(i, 103) < 0.28:
            continue
        t = (i + 0.5) / n + (_h(i, 107) - 0.5) * 1.7 / n
        px = x0 + (x1 - x0) * t
        r = 1.1 + _h(i, 89) ** 2 * 4.2
        s.append(blob(col or _lerp(CHAR, ASH_DARK, _h(i, 97) * 0.6),
                      r, r * 0.6, off=(px, y + _h(i, 101) * 2.0), z=z))


# ---------------------------------------------------------------------------
def den_mouth():
    """The den at the far end (§6.4), ~5.5 tiles -- and it is A MINE ADIT.

    THIS IS THE MOST IMPORTANT PIECE IN THE REGION AND ITS JOB IS TO BE HONEST.
    §6.4's whole structure is that the player believes the beast story and the
    ground never actually said it. So this shape has no teeth in it, no claw
    scoring, no bones at the threshold, no organic lip. What it has is:

      * SHORING. Two posts and a cap beam, hand-cut, out of true. Nothing digs a
        hole and then TIMBERS it.
      * A SPOIL FAN, on the OUTSIDE, wide and old. Everything that is no longer
        in the hole is in front of it.
      * A ROPE, tied off to the near post and running in.
      * DRAG MARKS THAT GO IN. Both directions would be traffic. One direction is
        §6.4's "all tracks lead one way, none lead back", and it is also just what
        dragging a full sack out and an empty one back in looks like.

    Every one of those reads as a lair to a man who has decided it is a lair, and
    as a working dig to anybody looking at it afterwards. That is the trick, and
    the trick is not a lie: it IS a working dig, and it always was.

    THE FIRST CUT READ AS AN IGLOO. The cut face was a smooth symmetrical dome
    with neat pale strata banded across it, which is a snow house, or a kiln, or a
    beehive -- anything built, and anything built has a smooth outline. Rock that
    has been torn open does not: the face is now ANGULAR and asymmetric, stepped
    on one side where it has calved away in blocks, with a vertical fracture
    running up past the mouth and a slab that has already fallen out of it lying
    at the foot. Nothing in the silhouette closes in a curve.

    The mouth itself is the darkest value in the game outside the Keep's
    orchestra pit. It has to be, because a dark hole is the only thing here the
    player will actually feel afraid of, and a dark hole is free.

    AND THEN IT READ AS A TOMB. Third failure, and this one only showed up
    in-engine, after the Scar's ground was pulled out of its orange phase into a
    dark warm brown: a face built out of cool STONE greys, twenty-two thousand
    pixels of it -- five times the area of any other piece in the kit -- sitting
    on warm earth. Measured, it is DARKER than the ground it stands on (mean
    luminance 42 against 61), and it still read as the brightest thing in the
    frame, because a large neutral-cold field against a warm ground pops no
    matter what its value is. What it looked like was poured concrete: a bunker,
    or a mausoleum, with a pale timber portal set into it.

    Which is the wrong lie. §6.4 wants a den the player will believe is a lair
    and that turns out to be a working dig -- both of those are holes in the
    GROUND. A masonry facade is a third thing, an institution, and there are no
    institutions in the Scar. So the rock is lerped toward EARTH throughout: the
    face body, the calved step faces, the strata, the fallen slab. It keeps its
    value break from the dirt (a cut face catches light the flat ground does
    not) and loses the temperature break entirely. The timbers came down too --
    at TIMBER_LIT 0.44 the shoring was the pale bright frame that made the whole
    thing read as BUILT, and shoring in a hole a man dug by himself is not
    joinery, it is two posts and a beam that is already sagging.
    """
    s = []
    W, H = 240, 176
    # THE CUT FACE: angular, asymmetric, stepped where it has calved
    # THE TOP IS BROAD AND FLAT, not peaked. The previous outline came to an apex
    # over the mouth and read as a CHAPEL -- a gabled portal in a stone facade,
    # which is a built thing again, just a different built thing than the igloo.
    # Rock above a cut runs on; it does not resolve into a roofline.
    face = [(-108.0, 0.0), (-102.0, 34.0), (-84.0, 40.0), (-80.0, 74.0),
            (-62.0, 80.0), (-58.0, 118.0), (-40.0, 134.0), (-4.0, 141.0),
            (34.0, 140.0), (52.0, 128.0), (56.0, 104.0), (78.0, 96.0),
            (84.0, 58.0), (100.0, 44.0), (104.0, 0.0)]
    ROCK = _lerp(_lerp(STONE, EARTH, 0.42), CHAR, 0.46)      # the cut face: earth, not masonry
    ROCK_LIT = _lerp(_lerp(STONE, EARTH_LIT, 0.36), ASH_DARK, 0.30)  # what a step face catches
    s.append(poly(face, ROCK, z=0))
    # the calved steps catch the light on their upper faces -- this is what makes
    # the face read as BLOCKY rather than as a shaded dome
    for (ax, ay), (bx, by) in (((-102.0, 34.0), (-84.0, 40.0)),
                               ((-80.0, 74.0), (-62.0, 80.0)),
                               ((54.0, 104.0), (78.0, 96.0)),
                               ((84.0, 58.0), (100.0, 44.0))):
        s.append(poly([(ax, ay), (bx, by), (bx, by - 5.0), (ax, ay - 5.0)],
                      ROCK_LIT, z=0.2))
    # A VERTICAL FRACTURE, running up past the mouth and out of frame at the top
    s.append(poly([(58.0, 8.0), (63.0, 8.0), (52.0, 128.0), (46.0, 126.0)],
                  _lerp(CHAR, ROCK, 0.22), z=0.3))
    # strata: broken ACROSS the fracture, offset either side of it (that offset
    # is the whole reason a fracture reads as a fracture)
    # ...and they are CLAMPED INSIDE THE FACE. The first cut ran them at fixed
    # x-extents while the face narrows with height, so the top three bands stuck
    # out past the silhouette and read as pale dashes floating in the air beside
    # the rock. A band of strata must never be wider than the rock it is in.
    def face_hw(y):
        """Half-width of the cut face at height y, following the outline above."""
        t = max(0.0, min(1.0, y / 146.0))
        return 106.0 * (1.0 - t ** 1.55 * 0.62) - 26.0 * max(0.0, t - 0.62) / 0.38 * 1.6
    for i in range(6):
        y = 16.0 + i * 20.0
        lim = face_hw(y) - 8.0
        if lim < 20.0:
            continue
        off = 7.0 if i % 2 else -5.0
        for x0, x1 in ((max(-lim, -96.0 + _h(i, 11) * 10.0), min(48.0, lim)),
                       (64.0, min(lim, 96.0 - _h(i, 13) * 8.0))):
            if x1 - x0 < 8.0:
                continue
            yy = y + (off if x0 > 0 else 0.0)
            s.append(poly([(x0, yy), (x1, yy + 2.0), (x1, yy + 6.0), (x0, yy + 4.0)],
                          _lerp(ROCK, ROCK_LIT, 0.30 + _h(i, 17) * 0.44), z=0.4))
    # the overhang's underside, darker: this is what makes it lean OUT
    s.append(poly([(-56.0, 108.0), (48.0, 116.0), (40.0, 134.0), (-46.0, 126.0)],
                  _lerp(CHAR, ROCK, 0.18), z=0.5))
    # THE MOUTH: the darkest value in the region, and NOT symmetric
    mouth = [(-42.0, 4.0), (-48.0, 48.0), (-36.0, 78.0), (-8.0, 92.0),
             (26.0, 84.0), (40.0, 54.0), (34.0, 4.0)]
    s.append(poly(mouth, (7, 8, 9), z=1.0, rim=0.0))
    s.append(poly([(-38.0, 4.0), (30.0, 4.0), (20.0, 15.0), (-24.0, 15.0)],
                  _lerp((7, 8, 9), ROCK, 0.20), z=1.1, rim=0.0))
    # THE SHORING. Hand-cut, out of true, and the cap beam has taken a sag.
    for sx, lean in ((-50.0, -0.050), (44.0, 0.034)):
        top = 92.0 + _h(int(sx), 23) * 10.0
        s.append(poly([(sx - 7.0, 0.0), (sx + 7.0, 0.0),
                       (sx + 7.0 + top * lean, top), (sx - 7.0 + top * lean, top)],
                      _lerp(TIMBER, TIMBER_DARK, 0.18), z=1.4))
        s.append(poly([(sx - 7.0, 0.0), (sx - 2.5, 0.0),
                       (sx - 2.5 + top * lean, top), (sx - 7.0 + top * lean, top)],
                      _lerp(TIMBER, TIMBER_LIT, 0.26), z=1.5))
    s.append(poly([(-60.0, 92.0), (52.0, 97.0), (52.0, 109.0), (-60.0, 104.0)],
                  _lerp(TIMBER, TIMBER_DARK, 0.32), z=1.6))
    s.append(poly([(-60.0, 104.0), (52.0, 109.0), (52.0, 112.0), (-60.0, 107.0)],
                  _lerp(TIMBER, TIMBER_LIT, 0.22), z=1.7))
    # THE ROPE: tied off to the near post, running in over the lip
    rope = [(-50.0 + 92.0 * (k / 10.0) ** 1.4, 78.0 - 60.0 * (k / 10.0) ** 0.7)
            for k in range(11)]
    s.append(poly([(x, y + 2.4) for x, y in rope] + [(x, y) for x, y in rope][::-1],
                  _lerp(ROPE, TIMBER_DARK, 0.22), z=2.0))
    # A SLAB that already fell out of the face, lying at the foot
    s.append(poly([(72.0, 2.0), (108.0, 6.0), (102.0, 22.0), (66.0, 17.0)],
                  _lerp(ROCK, CHAR, 0.14), z=2.6))
    s.append(poly([(72.0, 2.0), (108.0, 6.0), (107.0, 9.0), (71.0, 5.0)],
                  ROCK_LIT, z=2.7))
    # THE SPOIL FAN -- old, wide, and the edges have started to settle
    _spoil(s, -6.0, 200.0, 24.0, z=3.0, n=15)
    # DRAG MARKS, going IN. Two of them, converging, and they cut the spoil.
    for k, sx in ((0, -34.0), (1, 30.0)):
        pts = [(sx + (-4.0 - sx) * (i / 6.0), 8.0 - i * 0.7) for i in range(7)]
        s.append(poly([(x - 4.0, y) for x, y in pts] + [(x + 4.0, y) for x, y in pts][::-1],
                      _lerp(EARTH_DARK, CHAR, 0.34 + k * 0.10), z=4.0))
    _grit(s, -112.0, 112.0, 1.0, z=5, n=18)
    return s, (W, H)

# ---------------------------------------------------------------------------
def spoil_heap():
    """A heap of turned earth with one shovel-cut face, ~2.4 tiles.

    THE MOST-REPEATED PIECE IN THE REGION, ON PURPOSE -- thirty-one of them. §6.4
    wants "picked-over", and picked-over is a COUNT: one heap is a molehill,
    thirty-one across a region is a man who has been searching for years. It is
    also the reveal hiding in plain sight for the whole middle of the game.

    Because it repeats more than anything else, its silhouette gets the most
    scrutiny, and the first cut failed that: a smooth cone with a flat-cut face
    down one side reads as a PYRAMID, or a pup tent -- two straight edges meeting
    at a single apex is a built shape, and thirty-one of them in a region would
    have read as a campsite. Three things fix it:

      * THE CREST IS LUMPY, NOT AN APEX. Four offset lobes at different heights,
        so the top of the silhouette is a ragged ridge. Spoil is thrown one
        shovelful at a time and it never lands in a point.
      * THE SHOVEL FACE IS PARTIAL. It cuts the lower two-thirds and stops; above
        that the heap slumps over its own cut, which is what actually happens
        when you dig into a pile and then throw more onto it.
      * THE BASE IS WIDER THAN THE SLOPE WANTS. A steep cone is dry sand; wet
        turned earth spreads. The foot runs out further than the profile implies
        and dissolves into clods rather than ending on a line.

    ONE FACE IS CUT AND THE REST IS NOT. That asymmetry is the entire difference
    between "a heap" and "a heap somebody made": a spade leaves a plane, slumping
    leaves a curve, and having both on the same object is what says a tool was here.
    """

    # ...AND THIRTY-ONE OF THEM SHIPPED AS MUSHROOMS, and then as MOUNTAINS.
    # Both failures are geometry, and the second one is arithmetic you can do
    # before drawing anything.
    #
    # THE MUSHROOMS: the crest was four `blob`s -- ellipses -- each with a lit
    # lower half and a dark band along its top, sitting on a stack of nine
    # tapering ellipses. A lit dome over a narrower tapering mass IS a mushroom,
    # and four of them is a fairy ring. The body stack was the same mistake
    # again: stacked ellipses are a staircase, not a slope (see the Keep's
    # timpani), and every step reads as another cap.
    #
    # THE MOUNTAINS: replacing the domes with a ragged polygon ridge was right
    # about the material and wrong about the PROPORTION. At 130x76 and 2.4m the
    # piece renders four tiles wide and two and a half tall, which is a fifty
    # degree slope -- steeper than dry earth can stand. Loose spoil sits at its
    # ANGLE OF REPOSE, about thirty-five degrees, and anything steeper is a
    # mountain or a pyramid no matter how ragged you make the top of it. The
    # canvas is 130x48 now and the piece is 1.6m, which is the same 0.5 world
    # scale and a slope that earth can actually hold.
    s = []
    W, H = 130, 48
    # the foot: wet turned earth spreads, so it runs out past the profile
    s.append(blob(_lerp(EARTH_DARK, EARTH, 0.26), 62.0, 7.0, off=(0.0, 3.5), z=0))
    # THE MASS, as one polygon with a RAGGED top: nine shovelfuls, none of them
    # the apex, each one landing a little short of the last.
    RIDGE = ((-28.0, 25.0), (-21.0, 30.0), (-13.0, 27.0), (-5.0, 33.0), (3.0, 29.0),
             (11.0, 32.0), (19.0, 26.0), (26.0, 27.5), (33.0, 21.0))
    outline = [(-58.0, 1.0), (-50.0, 8.0), (-42.0, 14.0), (-35.0, 20.0)]
    outline += list(RIDGE)
    outline += [(41.0, 16.0), (48.0, 9.0), (54.0, 3.5), (58.0, 1.5)]
    s.append(poly(outline, _lerp(EARTH_DARK, EARTH, 0.56), z=0.2))
    # the lit slope faces the light (upper-left); the far slope does not
    s.append(poly([(-58.0, 1.0), (-50.0, 8.0), (-42.0, 14.0), (-35.0, 20.0),
                   (-28.0, 25.0), (-21.0, 30.0), (-17.0, 26.0), (-24.0, 18.0),
                   (-33.0, 10.0), (-44.0, 2.0)],
                  _lerp(EARTH, EARTH_LIT, 0.40), z=0.4, rim=0.0))
    s.append(poly([(19.0, 26.0), (26.0, 27.5), (33.0, 21.0), (41.0, 16.0),
                   (48.0, 9.0), (54.0, 3.5), (58.0, 1.5), (42.0, 2.0), (28.0, 13.0)],
                  _lerp(EARTH, EARTH_DARK, 0.26), z=0.4, rim=0.0))
    # each shovelful catches a little light on its uphill side: short slivers
    # along the ridge, NOT domes
    for i in range(len(RIDGE) - 1):
        (x0, y0), (x1, y1) = RIDGE[i], RIDGE[i + 1]
        s.append(poly([(x0, y0), (x1, y1), (x1 - 1.0, y1 - 2.4), (x0 - 1.0, y0 - 2.2)],
                      _lerp(EARTH, EARTH_LIT, 0.22 + _h(i, 37) * 0.26), z=0.8, rim=0.0))
    # THE SHOVEL-CUT FACE. One flat plane where a spade went in, on ONE flank,
    # narrow and near the mass in value -- as a big pale centred quad it read as
    # a tent flap, which is the pyramid failure wearing a different hat.
    s.append(poly([(20.0, 2.0), (43.0, 4.0), (34.0, 20.0), (19.0, 21.0)],
                  _lerp(EARTH, EARTH_LIT, 0.16), z=1.5))
    s.append(poly([(20.0, 2.0), (24.0, 2.4), (21.5, 20.8), (19.0, 21.0)],
                  _lerp(EARTH, EARTH_DARK, 0.30), z=1.6))
    s.append(blob(_lerp(EARTH, EARTH_DARK, 0.46), 11.0, 2.4, off=(29.0, 20.4), z=1.7, rim=0.0))
    # clods: ANGULAR, because a clod of dug earth has corners and a pebble does
    for i in range(15):
        cx0 = -50.0 + i * 6.8 + (_h(i, 47) - 0.5) * 7.0
        cy0 = 2.5 + _h(i, 53) * 20.0
        cw = 1.6 + _h(i, 41) * 3.2
        s.append(poly([(cx0, cy0), (cx0 + cw, cy0 - 0.4), (cx0 + cw * 1.1, cy0 + cw * 0.8),
                       (cx0 + cw * 0.3, cy0 + cw * 1.1), (cx0 - 0.5, cy0 + cw * 0.5)],
                      _lerp(EARTH, ASH_DARK, _h(i, 43) * 0.40), z=2.0 + i * 0.01))
    _grit(s, -62.0, 62.0, 1.0, z=3, n=11,
          col=_lerp(EARTH_DARK, EARTH, 0.4))
    return s, (W, H)

# ---------------------------------------------------------------------------
def trench():
    """An open cut with timber shoring and one plank across, ~1.2 tiles.

    Low and wide, so it reads as a HOLE and not a wall -- the whole point of a
    pit prop in a top-down-ish view is the dark interior, and that means the near
    lip has to be lower than the far one.

    THE PLANK IS THE HUMAN DETAIL. A pit is geology. A pit with a board laid over
    it is somebody who crosses here often enough to get tired of walking round.
    """
    s = []
    W, H = 170, 38
    # far lip, then the dark, then the near lip in front of it
    s.append(poly([(-76.0, 12.0), (74.0, 15.0), (70.0, 26.0), (-72.0, 23.0)],
                  _lerp(EARTH_DARK, EARTH, 0.22), z=0))
    s.append(poly([(-70.0, 9.0), (68.0, 12.0), (64.0, 21.0), (-66.0, 18.0)],
                  (11, 10, 10), z=0.4, rim=0.0))
    s.append(poly([(-78.0, 2.0), (76.0, 4.0), (72.0, 13.0), (-74.0, 11.0)],
                  _lerp(EARTH, EARTH_LIT, 0.24), z=0.8))
    # shoring: three uprights leaning in, and one has slipped
    for i, sx in enumerate((-52.0, -6.0, 44.0)):
        lean = -0.10 if i == 2 else 0.03
        s.append(poly([(sx - 3.5, 6.0), (sx + 3.5, 6.0),
                       (sx + 3.5 + 22.0 * lean, 28.0), (sx - 3.5 + 22.0 * lean, 28.0)],
                      _lerp(TIMBER, TIMBER_DARK, 0.18), z=1.0))
    # the plank across, sagging, worn pale where feet land
    pl = [(-84.0 + 168.0 * (k / 8.0), 22.0 - 2.4 * math.sin((k / 8.0) * math.pi))
          for k in range(9)]
    s.append(poly([(x, y) for x, y in pl] + [(x, y + 5.0) for x, y in pl][::-1],
                  _lerp(TIMBER, TIMBER_DARK, 0.28), z=1.6))
    s.append(poly([(x, y + 4.0) for x, y in pl] + [(x, y + 5.0) for x, y in pl][::-1],
                  _lerp(TIMBER_LIT, ASH, 0.30), z=1.7))
    _spoil(s, 0.0, 150.0, 8.0, z=2.0, n=10)
    return s, (W, H)


# ---------------------------------------------------------------------------
def burnt_spar():
    """A charred standing trunk, snapped high, ~6.0 tiles -- and it burned STANDING.

    THIS SILHOUETTE HAS FAILED TWICE. First as a MISSILE: a smooth monotone
    taper closing to a point with a spiral bark seam, which at ship size read as
    a rocket. That fix -- near-constant width, a snapped top, branch stubs --
    then shipped, and the in-engine frame came back with a saguaro CACTUS in it.
    Both failures have one cause and it is worth naming precisely, because it is
    the third distinct shape this trunk has accidentally been:

        A VERTICAL SHAFT OF CONSTANT WIDTH IS NOT A TREE. It is whatever the
        details on it suggest. Give it a nose cone and it is a missile; give it
        arms that rise and it is a cactus. The trunk itself was carrying no
        information at all, so the details were carrying all of it.

    A tree carries its own information, and the load-bearing signal is not
    texture -- it is that IT NEVER STOOD STRAIGHT AND IT IS NOT STRAIGHT NOW.
    So four things changed and none of them are surface detail:

      * IT LEANS, AND THE LEAN CURVES. Four times the old lean, applied on a
        power curve, so the top is displaced most and no two thirds of the
        trunk share an axis. A cactus is plumb; a fifteen-year-dead trunk with
        three years of surface weather on it is not.
      * THE STUBS DROOP. This is the whole cactus fix in one sign flip. The old
        stubs rose off the trunk (`rise` positive, tip above root) at four
        alternating heights -- which is precisely, unmistakably, how a saguaro
        holds its arms. Dead branches sag: every stub now angles DOWN, and they
        are no longer alternating (two on the lee side of the lean, which is
        where a burnt tree keeps its wood, one on the windward).
      * THE WIDTH VARIES NON-MONOTONICALLY. A burnt-through waist at mid-height
        and a knot swelling below it, so no two heights measure the same and the
        sequence does not simply shrink. (The same law the cairn learned twice.)
      * IT IS BURNT HOLLOW AT THE FOOT. Fire comes from the ground. A black
        cavity eaten into the base is the one detail no cactus and no rocket can
        have, and it says "fire" without a single ember.

    Fissures run up it, but only three and they are irregular and branching --
    cactus ribs are evenly spaced and parallel, so evenly-spaced verticals are
    the wrong texture here even though they are the right texture for wood.

    Tallest piece in the kit, so it collects the most additive haze -- see the
    material note at the top of the file. Authored dark on purpose.
    """
    s = []
    W, H = 90, 192
    BREAK = 150.0

    def cxx(y):
        """The lean, CURVED. A straight lean is still an axis; this one has no
        single axis, and it kicks back slightly low down where the root held."""
        t = max(0.0, min(1.0, y / BREAK))
        return 26.0 * t ** 1.7 - 3.2 * t ** 0.6

    def hw(y):
        """Half-width. NOT monotone: a root flare, a knot at a third height, and
        a burnt-through waist above it, so the profile has news in it."""
        t = max(0.0, min(1.0, y / BREAK))
        flare = 1.0 + 0.95 * max(0.0, 1.0 - t / 0.17) ** 1.8
        knot = 1.0 + 0.30 * math.exp(-((t - 0.34) / 0.075) ** 2)
        waist = 1.0 - 0.34 * math.exp(-((t - 0.56) / 0.10) ** 2)
        return (9.6 - t * 1.9) * flare * knot * waist

    # the trunk, up to the break. Both edges wobble: bark is not extruded.
    outer, inner = [], []
    for i in range(25):
        y = BREAK * (i / 24.0)
        w = hw(y)
        outer.append((cxx(y) + w * (1.0 + (_h(i, 11) - 0.5) * 0.22), y))
        inner.append((cxx(y) - w * (1.0 + (_h(i, 13) - 0.5) * 0.22), y))
    s.append(poly(outer + inner[::-1], _lerp(CHAR, CHAR_LIT, 0.16), z=1))

    # BLOTCHY CHAR: patches, not a ramp. Some pale ash, some burnt through.
    for i in range(22):
        y = 6.0 + _h(i, 17) * (BREAK - 16.0)
        w = hw(y)
        r = 2.2 + _h(i, 19) * 4.2
        px = cxx(y) + (_h(i, 23) - 0.5) * 2.0 * max(0.5, w - r * 0.5)
        pale = _h(i, 29) > 0.55
        s.append(blob(_lerp(CHAR, ASH_DARK, 0.55) if pale else _lerp(CHAR, (14, 12, 11), 0.6),
                      r, r * (1.1 + _h(i, 31) * 1.4), off=(px, y), z=1.2 + i * 0.005))

    # FISSURES -- three, irregular, one of them forked. Wood checks lengthwise
    # as it dries; the reason there are only three and none of them are parallel
    # is that evenly-spaced parallel verticals are cactus ribs.
    for k, (y0, y1, fx, fork) in enumerate(((18.0, 74.0, -0.44, True),
                                            (48.0, 118.0, 0.52, False),
                                            (86.0, 140.0, -0.18, False))):
        pts_l, pts_r = [], []
        for i in range(9):
            y = y0 + (y1 - y0) * (i / 8.0)
            w = hw(y)
            bx = cxx(y) + fx * w + (_h(i, 53 + k) - 0.5) * 2.2
            hwid = 0.7 + _h(i, 59 + k) * 1.5
            pts_l.append((bx - hwid, y))
            pts_r.append((bx + hwid, y))
        s.append(poly(pts_l + pts_r[::-1], _lerp(CHAR, (10, 9, 8), 0.66), z=2.6))
        if fork:
            fy = y0 + (y1 - y0) * 0.62
            s.append(poly([(cxx(fy) + fx * hw(fy), fy),
                           (cxx(fy) + fx * hw(fy) + 1.6, fy + 1.0),
                           (cxx(y1) + (fx + 0.34) * hw(y1), y1 - 12.0),
                           (cxx(y1) + (fx + 0.34) * hw(y1) - 1.4, y1 - 13.0)],
                          _lerp(CHAR, (10, 9, 8), 0.58), z=2.6))

    # BURNT HOLLOW AT THE FOOT. Fire comes from the ground, and the one thing
    # neither a cactus nor a shell casing has is a cavity eaten into its base.
    hy = 16.0
    s.append(poly([(cxx(0) - hw(0) * 0.30, 0.0), (cxx(0) + hw(0) * 0.16, 1.0),
                   (cxx(hy) + hw(hy) * 0.30, hy - 2.0), (cxx(hy) - hw(hy) * 0.10, hy + 3.0),
                   (cxx(hy) - hw(hy) * 0.52, hy - 4.0)],
                  (9, 8, 8), z=2.9))
    # a rind of pale ash around the burn's lip: the fire stopped HERE
    s.append(poly([(cxx(hy) - hw(hy) * 0.62, hy - 6.0), (cxx(hy) + hw(hy) * 0.40, hy - 1.0),
                   (cxx(hy) + hw(hy) * 0.30, hy + 3.0), (cxx(hy) - hw(hy) * 0.66, hy - 2.0)],
                  _lerp(ASH_DARK, ASH, 0.30), z=2.85))

    # THE SNAP: a ragged break, offset hard to the lee side, then ONE long
    # splinter and one short nub -- never a matched pair, which is a crown.
    lipL, lipR = cxx(BREAK) - hw(BREAK), cxx(BREAK) + hw(BREAK)
    wound = [(lipL, BREAK - 7.0)]
    for k in range(6):
        t = (k + 1) / 7.0
        wound.append((lipL + (lipR - lipL) * t, BREAK - 7.0 + (2.0 + _h(k, 37) * 10.0)))
    wound.append((lipR, BREAK - 3.0))
    # THE WOUND IS WEATHERED, NOT FRESH. At `_lerp(BONE_DARK, ASH, 0.30)` this
    # measured luminance 93 on a piece whose mean is 39 -- so the snap was the
    # brightest thing on the trunk by a factor of two, a pale wedge at the top of
    # a dark leaning shaft, and the in-engine frame read it as a BLADE. Fourth
    # accidental shape for this silhouette (missile, cactus, ladder, sword), and
    # the fix is chronology: this tree burned, then stood in the open for years.
    # Torn wood goes grey in a season. Nothing up there is pale any more.
    s.append(poly(wound + [(lipR, BREAK - 13.0), (lipL, BREAK - 15.0)],
                  _lerp(BONE_DARK, CHAR, 0.46), z=2.0))
    # the long one leans further out than the trunk does; the nub barely clears
    for k, (sx, top, wid, kick) in enumerate(((0.70, 181.0, 4.4, 11.0),
                                              (-0.46, 158.0, 2.6, -2.0))):
        bx = cxx(BREAK) + sx * hw(BREAK)
        tipx = bx + kick
        s.append(poly([(bx - wid, BREAK - 9.0), (bx + wid, BREAK - 6.0),
                       (tipx + wid * 0.22, top), (tipx - wid * 0.30, top - 4.0)],
                      _lerp(CHAR, CHAR_LIT, 0.24 + k * 0.14), z=1.9 - k * 0.1))
        # torn fibre on the inside face of each splinter: pale, and small
        s.append(poly([(bx - wid * 0.4, BREAK - 6.0), (bx + wid * 0.3, BREAK - 5.0),
                       (tipx * 0.5 + bx * 0.5, top - 8.0), (bx - wid * 0.3, top - 11.0)],
                      _lerp(BONE_DARK, CHAR, 0.34), z=2.1))

    # DROOPING STUBS -- and the droop IS the fix. Three, not four; two on the
    # lee side where a leaning trunk keeps its wood, one windward; every tip
    # BELOW its root; lengths in no order.
    # (and they must not read as a SET, or three bars down one side of a post
    # scan as RUNGS -- a nailed climbing ladder, which is a made thing again.
    # So: three different thicknesses, three different droop angles, and one of
    # them is a stub two pixels long that barely clears the bark.)
    for k, (y, side, L, drop, th) in enumerate(((40.0, 1.0, 22.0, -9.0, 4.6),
                                                (72.0, -1.0, 6.0, -3.0, 3.0),
                                                (114.0, 1.0, 14.0, -19.0, 2.2))):
        w0 = hw(y)
        x0 = cxx(y) + side * w0 * 0.66
        x1 = x0 + side * L
        s.append(poly([(x0, y + th * 1.15), (x1, y + drop + th * 0.55),
                       (x1, y + drop - th * 0.45), (x0, y - th * 0.85)],
                      _lerp(CHAR, CHAR_LIT, 0.10 + _h(k, 43) * 0.16), z=2.4))
        # the sheared end: a pale disc, three pixels of it
        s.append(blob(_lerp(BONE_DARK, ASH_DARK, 0.4), th * 0.52, th * 0.60,
                      off=(x1, y + drop + 0.4), z=2.5))

    # bark sloughing off in plates near the base -- vertical, not spiral
    for i in range(4):
        y = 8.0 + i * 17.0
        w = hw(y)
        s.append(poly([(cxx(y) + w * 0.34, y), (cxx(y) + w * 0.96, y + 3.0),
                       (cxx(y) + w * 0.80, y + 13.0), (cxx(y) + w * 0.22, y + 10.0)],
                      _lerp(CHAR, TIMBER_DARK, 0.30 + _h(i, 47) * 0.28), z=2.8))
    _grit(s, -30.0, 34.0, 1.0, z=3, n=13)
    return s, (W, H)

# ---------------------------------------------------------------------------
def burnt_stand():
    """Five charred stumps of a burnt copse, ~3.5 tiles.

    The companion to `burnt_spar`, and it exists so the region can say "this
    burned" WITHOUT a forest of six-tile trunks eating the camera. Same fire,
    different survivors: these are the ones that went all the way down.

    THE FIRST CUT READ AS BOLLARDS -- five tapered posts of the same profile at
    five heights, evenly spread, each with a clean flat top. That is a fence, or
    a row of mooring posts, and the fix is that a burnt stump's TOP is where all
    its information is. So every one of these now ends in a different kind of
    failure: one split down the middle, one burnt hollow, one sheared at an
    angle, one gnarled with the flare still on it, one snapped to a spike. Widths
    vary by nearly 2:1, and two of them lean toward each other, which is the one
    arrangement a fence never makes.
    """
    s = []
    W, H = 150, 112
    # (x, top, tilt, base half-width, failure)
    STUMPS = [(-56.0, 100.0, 0.030, 13.0, "split"),
              (-26.0, 54.0, -0.075, 9.0, "hollow"),
              (2.0, 82.0, 0.055, 15.5, "shear"),
              (34.0, 40.0, -0.020, 8.0, "gnarl"),
              (56.0, 66.0, -0.085, 10.5, "spike")]
    for i, (sx, top, tilt, bw, fail) in enumerate(STUMPS):
        def hw(y, top=top, bw=bw):
            t = max(0.0, min(1.0, y / top))
            flare = 1.0 + 1.05 * max(0.0, 1.0 - t / 0.20) ** 1.7
            return bw * (1.0 - t * 0.30) * flare

        outer, inner = [], []
        for k in range(15):
            y = top * (k / 14.0)
            w = hw(y)
            outer.append((sx + tilt * y + w * (1.0 + (_h(i * 8 + k, 53) - 0.5) * 0.14), y))
            inner.append((sx + tilt * y - w * (1.0 + (_h(i * 8 + k, 59) - 0.5) * 0.14), y))
        s.append(poly(outer + inner[::-1],
                      _lerp(CHAR, CHAR_LIT, 0.08 + _h(i, 61) * 0.14), z=i * 0.3))
        # blotchy char, same discipline as the spar
        for k in range(7):
            y = 4.0 + _h(i * 9 + k, 67) * (top - 10.0)
            w = hw(y)
            r = 2.0 + _h(i * 9 + k, 71) * 3.4
            s.append(blob(_lerp(CHAR, ASH_DARK, 0.5) if _h(i * 9 + k, 73) > 0.5
                          else _lerp(CHAR, (13, 11, 10), 0.55),
                          r, r * 1.5,
                          off=(sx + tilt * y + (_h(i * 9 + k, 79) - 0.5) * 1.6 * w, y),
                          z=i * 0.3 + 0.1))
        tx, tw = sx + tilt * top, hw(top * 0.96)
        pale = _lerp(BONE_DARK, ASH, 0.24 + _h(i, 83) * 0.22)
        if fail == "split":        # cleaved down the middle
            s.append(poly([(tx - tw, top - 4.0), (tx - 1.5, top - 26.0),
                           (tx + 1.5, top - 26.0), (tx + tw, top - 2.0),
                           (tx + tw * 0.6, top), (tx - tw * 0.7, top - 1.0)], pale, z=i * 0.3 + 0.2))
            s.append(rect(tx - 2.0, top - 30.0, tx + 2.0, top - 2.0, (10, 9, 9), z=i * 0.3 + 0.25))
        elif fail == "hollow":     # burnt out inside: a ring of wall, nothing in it
            s.append(blob(pale, tw, tw * 0.34, off=(tx, top - 2.0), z=i * 0.3 + 0.2))
            s.append(blob((9, 9, 9), tw * 0.62, tw * 0.20, off=(tx, top - 2.4),
                          z=i * 0.3 + 0.25, rim=0.0))
        elif fail == "shear":      # taken off at an angle
            s.append(poly([(tx - tw, top - 14.0), (tx + tw, top),
                           (tx + tw * 0.9, top - 4.0), (tx - tw, top - 19.0)],
                          pale, z=i * 0.3 + 0.2))
        elif fail == "gnarl":      # never broke; just died standing, knotted
            for k in range(3):
                s.append(blob(_lerp(CHAR, CHAR_LIT, 0.3),
                              tw * (0.5 - k * 0.1), tw * 0.4,
                              off=(tx + (k - 1) * tw * 0.6, top - 3.0 + k * 2.0),
                              z=i * 0.3 + 0.2 + k * 0.02))
        else:                      # snapped to a spike
            s.append(poly([(tx - tw, top - 8.0), (tx + tw * 0.4, top - 6.0),
                           (tx + tw * 0.1, top + 16.0), (tx - tw * 0.3, top + 12.0)],
                          _lerp(CHAR, CHAR_LIT, 0.20), z=i * 0.3 + 0.2))
            s.append(poly([(tx - tw * 0.5, top - 7.0), (tx + tw * 0.1, top - 6.0),
                           (tx - tw * 0.05, top + 12.0)], pale, z=i * 0.3 + 0.25))
    _grit(s, -70.0, 70.0, 1.0, z=4, n=16)
    return s, (W, H)

# ---------------------------------------------------------------------------
def bone_pile():
    """Picked-over bones, ~2.0 tiles. RIBS AND LONG BONES. NO SKULL.

    A skull is a genre signal and it means predator, which is the one thing §6.4
    must not assert -- "no blood anywhere" is the evidence rotting the monster
    story from below, and a kit that plants a skull has taken the beast's side.
    Ribs and a cracked long bone are the leftovers of a MEAL. Somebody was
    hungry. That reads as menace on the way in and as a man living rough on the
    way out, which is exactly the double duty every piece here has to do.

    They are also BLEACHED and half-buried, i.e. old. Fresh bones would date the
    kill to this week and make the beast present tense.
    """

    # AND IT SHIPPED AS A BARBELL. Measured cause, worth keeping: the five rib
    # arcs swept `ang` from about -0.4 to 0.65 radians, and the rise of an arc
    # over that span is `1 - cos(ang)`, which near zero is nothing at all -- each
    # rib came out 19px wide and THREE PIXELS TALL. Five flat dashes at y 8-11,
    # with a horizontal long bone at y 8-13 laid over them and a 5px sphere on
    # each of its ends, and the whole pile collapsed into one bar with two knobs.
    # An arc only reads as an arc where the tangent TURNS, so the sweep has to
    # cross the vertical; and a bone end is a CONDYLE, a flattened lozenge wider
    # than the shaft, never a ball.
    s = []
    W, H = 140, 64
    # half-buried in a shallow scrape, so the ground owns them
    s.append(blob(_lerp(EARTH_DARK, EARTH, 0.3), 62.0, 13.0, off=(0.0, 8.0), z=0))
    # THE RIB CAGE: six arcs springing UP off the ground line, splayed like a
    # wrecked hull's frames, the near ones taller. Two are snapped short.
    for i in range(6):
        base_x = -42.0 + i * 15.0 + (_h(i, 59) - 0.5) * 4.0
        L = 26.0 + _h(i, 61) * 12.0 - abs(i - 2) * 2.0
        if i in (1, 4):
            L *= 0.52                      # these two snapped
        lean = (-0.55 + i * 0.20) + (_h(i, 63) - 0.5) * 0.20
        pts = []
        for k in range(9):
            t = k / 8.0
            # sweep the tangent from vertical to horizontal: THIS is the arc
            ang = t * 1.42
            pts.append((base_x + math.sin(ang) * L * 0.78 + lean * t * L * 0.5,
                        4.0 + (1.0 - math.cos(ang)) * L * 1.35))
        wid = 2.6 - _h(i, 67) * 0.7
        s.append(poly([(x - wid, y) for x, y in pts] + [(x + wid, y) for x, y in pts][::-1],
                      _lerp(BONE_DARK, BONE, 0.30 + _h(i, 71) * 0.40), z=1 + i * 0.05))
    # two loose long bones, at DIFFERENT diagonals so neither is the horizon
    for k, (x0, y0, x1, y1, w0) in enumerate(((-52.0, 6.0, -12.0, 17.0, 3.0),
                                              (16.0, 15.0, 56.0, 5.0, 2.6))):
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln * w0, dx / ln * w0
        s.append(poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                       (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)],
                      _lerp(BONE_DARK, BONE, 0.42), z=2 + k * 0.1))
        for ex, ey, sg in ((x0, y0, -1.0), (x1, y1, 1.0)):
            # the condyle: a lozenge across the shaft, not a ball on the end
            s.append(poly([(ex + nx * 1.9 + dx / ln * sg * 1.5, ey + ny * 1.9 + dy / ln * sg * 1.5),
                           (ex + nx * 1.1 + dx / ln * sg * 4.6, ey + ny * 1.1 + dy / ln * sg * 4.6),
                           (ex - nx * 1.1 + dx / ln * sg * 4.6, ey - ny * 1.1 + dy / ln * sg * 4.6),
                           (ex - nx * 1.9 + dx / ln * sg * 1.5, ey - ny * 1.9 + dy / ln * sg * 1.5)],
                          _lerp(BONE_DARK, BONE, 0.58), z=2.2 + k * 0.1))
    # chips: what is left after something ate here
    for i in range(7):
        cx0 = -50.0 + i * 16.0 + (_h(i, 73) - 0.5) * 9.0
        cy0 = 2.0 + _h(i, 79) * 6.0
        cw = 2.0 + _h(i, 83) * 3.4
        s.append(poly([(cx0, cy0), (cx0 + cw, cy0 + 0.6), (cx0 + cw * 0.7, cy0 + 2.4),
                       (cx0 - 0.6, cy0 + 1.8)], _lerp(BONE_DARK, BONE, 0.34), z=2.6))
    _grit(s, -60.0, 60.0, 1.0, z=3, n=7)
    return s, (W, H)

# ---------------------------------------------------------------------------
def cairn():
    """A stacked stone marker, ~2.6 tiles -- and it is an ARGUMENT.

    §6.4's middle stretch is "the false trails -- pilgrim strides, den-thing
    gaits, decoys that double back". A cairn is the physical form of a pilgrim
    stride: a thing only a person makes, standing in country the player has
    decided belongs to a beast. Every one of these the player walks past is the
    region quietly disagreeing with them.

    THIS PIECE HAS FAILED TWICE AND BOTH FAILURES ARE THE SAME MISTAKE. First it
    was a cone of pebbles -- ellipses shrinking smoothly with height, which is a
    soft-serve. The fix was flat contacts and angular slabs, and that produced a
    WEDDING CAKE: eleven slabs still shrinking smoothly, each with a bright lit
    top face, so the piece read as tiers, and it was also the brightest large
    shape in the region (§3 says the brightest thing must be small).

    The mistake underneath both is MONOTONIC SHRINKING. A real cairn is built
    from whatever stones were to hand, so the sequence of widths is ragged --
    there is a wide one high up, and two thin ones stacked together low down --
    and only about a third of the joins catch light, because most stones are not
    lying flat. Seven stones, not eleven. Values pulled down under the ash. And
    the lean is now three times what it was, so the top stone sits a full stone's
    width off the base and the thing is visibly going over.

    A neat cairn is decoration; a careful cairn going over is a person who is no
    longer coming back to fix it.
    """
    s = []
    W, H = 70, 84
    # (base height, half-width, thickness, does the top face catch light)
    # NON-MONOTONIC ON PURPOSE: #4 is wider than #3, and #5/#6 are two thin ones
    # stacked. Only three of the seven are lit.
    SLABS = [(0.0, 24.0, 13.0, True),
             (12.5, 16.0, 9.0, False),
             (21.0, 13.0, 7.0, False),
             (27.5, 19.0, 6.0, True),
             (33.0, 10.0, 5.0, False),
             (37.5, 12.0, 4.0, False),
             (41.0, 15.0, 11.0, True),
             (51.5, 9.0, 8.0, False),
             (59.0, 11.0, 6.0, False)]
    lean = 0.30
    for i, (y, hw, th, lit) in enumerate(SLABS):
        x = lean * y
        # each stone is a quad with a flat bottom and a NOT-flat top, and its
        # two sides are not parallel -- that is what stops it reading as a brick
        j0 = (_h(i, 67) - 0.5) * 0.44
        j1 = (_h(i, 71) - 0.5) * 0.44
        tiltt = (_h(i, 73) - 0.5) * th * 0.7
        pts = [(x - hw * (1.0 + j0), y), (x + hw * (1.0 - j1), y),
               (x + hw * (1.0 - j1) * 0.93, y + th + tiltt),
               (x - hw * (1.0 + j0) * 0.93, y + th - tiltt)]
        # values sit UNDER the ash: this stack must not be the brightest thing
        s.append(poly(pts, _lerp(STONE, CHAR, 0.30 - _h(i, 79) * 0.26), z=i * 0.3))
        # the shaded underside, so each stone sits ON the one below
        s.append(poly([(x - hw * (1.0 + j0), y), (x + hw * (1.0 - j1), y),
                       (x + hw * (1.0 - j1) * 0.97, y + 2.4),
                       (x - hw * (1.0 + j0) * 0.97, y + 2.4)],
                      _lerp(STONE, CHAR, 0.62), z=i * 0.3 + 0.05))
        if lit:
            s.append(poly([(x - hw * (1.0 + j0) * 0.93, y + th - tiltt - 2.0),
                           (x + hw * (1.0 - j1) * 0.93, y + th + tiltt - 2.0),
                           (x + hw * (1.0 - j1) * 0.90, y + th + tiltt),
                           (x - hw * (1.0 + j0) * 0.90, y + th - tiltt)],
                          _lerp(STONE_LIT, ASH_DARK, 0.36), z=i * 0.3 + 0.1))
    # the top stone is a different rock and somebody CHOSE it: rounder, and the
    # one thing on the piece that is not a slab
    s.append(blob(_lerp(STONE, BONE_DARK, 0.30), 7.0, 5.0,
                  off=(lean * 66.0, 68.0), z=4.0))
    # two stones that have already fallen off, at the foot, DOWNHILL of the lean
    for k, (fx, fr) in enumerate(((22.0, 6.0), (30.0, 4.4))):
        s.append(poly([(fx - fr, 1.0), (fx + fr, 2.0), (fx + fr * 0.8, 2.0 + fr),
                       (fx - fr * 0.9, 1.0 + fr * 0.8)],
                      _lerp(STONE, CHAR, 0.22 + k * 0.16), z=4.2))
    _grit(s, -28.0, 36.0, 1.0, z=4.4, n=8)
    return s, (W, H)

# ---------------------------------------------------------------------------
def pilgrim_pack():
    """An abandoned pack, ~0.8 tiles, LYING FLAT. Straps cut, contents gone.

    The smallest, saddest piece in the kit and it does a specific job: §6.4's
    false trails need a reason the player believes somebody DIED making them.
    A dropped pack says that. Cut straps say somebody in a hurry, or somebody who
    could not get it off any other way. It is also the ONE MADE THING in the
    Oasis (see `place_scar.OASIS`), so if it does not read as made it costs the
    vignette its whole point.

    FIVE CUTS -- a rock, a chest of drawers, a cooking pot, a tent, and then this
    one. The four failures are worth keeping because together they say something
    general about small props in a top-down world:

    1. A LUMP AT GROUND VALUE IS A ROCK. The body was luminance 72 on Oasis
       ground that measures 70, so only the silhouette carried it.
    2. "MADE" IS NOT "RECTILINEAR". A straight hem, a lashed bedroll and two
       parallel vertical straps put four straight lines in an 80px box and
       arrived as a CHEST OF DRAWERS. Fittings say made; straight edges do not.
    3. A ROUNDED MASS WITH A CENTRED DARK MOUTH IS A POT, always.
    4. A NARROW TOP FLARING TO A WIDE HEM WITH RADIATING FACETS IS A TENT. The
       drapery fan was right about cloth and wrong about the object.

    THE COMMON CAUSE: ALL FOUR WERE STANDING UP. A soft mass of this size
    standing on the ground has only a handful of readings available in a
    top-down view and they are all wrong -- boulder, vessel, tent. An emptied
    pack does not stand anyway; it LIES DOWN. Flat, the silhouette is wider than
    it is tall, which no boulder-or-vessel reading survives, and the two cut
    shoulder straps get to lie ACROSS the body as long curves -- the strongest
    "somebody wore this" signal available, and impossible on a rock.

    Canvas is 46x24 rather than 80x44 for the same reason: the piece is flat, so
    a tall canvas would have been mostly empty and `worldScaleFor` would have
    sized the object by air. See `place_scar.METERS` -- 0.8, not 1.4.

    NOTHING IS SPILLED OUT OF IT. An emptied pack with its contents strewn about
    is a struggle; an emptied pack with nothing near it means whoever emptied it
    took everything and walked away, which is worse and is also just what a man
    living out here for years would do.
    """
    s = []
    W, H = 46, 24
    # PALE, and it has to stay pale: every shape in this pipeline is drawn with
    # a dark silhouette halo behind it, and on a 46x24 sprite the halo is a big
    # fraction of the object. Cut five drew two full-length straps across the
    # body in TIMBER and the halo plus the straps swallowed the cloth entirely --
    # it came back a dark smudge. ONE strap, thin, and most of the piece bright.
    CLOTH = _lerp(SACK, BONE, 0.62)
    CLOTH_LIT = _lerp(BONE, (0xE2, 0xDA, 0xC2), 0.30)
    CLOTH_DARK = _lerp(SACK, TIMBER_DARK, 0.30)
    STRAP = _lerp(TIMBER, ROPE, 0.72)
    s.append(blob(_lerp(EARTH_DARK, TIMBER_DARK, 0.5), 19.0, 3.2, off=(1.0, 2.2), z=-0.4, rim=0.0))
    # the body: wider than tall, notched twice where the empty cloth folded under
    body = [(-20.0, 5.0), (-17.0, 13.0), (-9.0, 16.0), (-11.0, 12.0), (-1.0, 17.0),
            (9.0, 16.0), (15.0, 18.0), (14.0, 13.0), (20.0, 8.0), (18.0, 3.0),
            (6.0, 1.0), (-5.0, 2.0), (-15.0, 1.6)]
    s.append(poly(body, CLOTH, z=0))
    s.append(poly([(-20.0, 5.0), (-17.0, 13.0), (-9.0, 16.0), (-1.0, 17.0),
                   (3.0, 9.5), (-9.0, 6.0), (-16.0, 4.0)], CLOTH_LIT, z=0.2, rim=0.0))
    s.append(poly([(9.0, 16.0), (15.0, 18.0), (14.0, 13.0), (20.0, 8.0), (18.0, 3.0),
                   (10.0, 2.0), (8.0, 10.0)], CLOTH_DARK, z=0.2, rim=0.0))
    # THE FLAP, folded back on itself: its UNDERSIDE shows, which is a thing
    # only cloth and leather do
    s.append(poly([(1.0, 2.6), (14.0, 2.0), (16.0, 7.4), (4.0, 8.8)],
                  _lerp(SACK, TIMBER_DARK, 0.56), z=0.7))
    s.append(poly([(1.0, 2.6), (14.0, 2.0), (14.6, 3.4), (1.4, 4.0)],
                  CLOTH_LIT, z=0.75, rim=0.0))
    # THE GATHER at the throat, off in the far corner
    for gx, gy, gr in ((-15.0, 9.0, 2.2), (-12.2, 12.2, 1.9)):
        s.append(blob(CLOTH_LIT, gr, gr * 0.82, off=(gx, gy), z=0.9))
        s.append(blob(CLOTH_DARK, gr * 0.5, gr * 0.36, off=(gx + 0.5, gy - 1.2), z=0.95, rim=0.0))
    # THE CUT SHOULDER STRAP, lying ACROSS the body and trailing off it onto the
    # ground: the strongest "somebody wore this" signal available, and the one
    # thing a rock cannot have. Thin, curved, and it is the only dark line here.
    band_t, band_b = [], []
    for i in range(9):
        t = i / 8.0
        x, y = -12.0 + 28.0 * t, 11.0 - 7.0 * t + math.sin(t * 3.1) * 1.4
        band_t.append((x, y + 1.1)); band_b.append((x, y - 1.1))
    s.append(poly(band_t + band_b[::-1], STRAP, z=1.2))
    s.append(poly([(-12.0, 12.1), (-12.0, 9.9), (-22.0, 7.4), (-24.0, 8.6), (-20.0, 10.4)],
                  STRAP, z=1.15))
    for f in range(3):
        s.append(poly([(-24.0, 8.0 + f * 0.8), (-24.0, 8.7 + f * 0.8),
                       (-27.0 - f, 9.2 + f * 1.0), (-27.0 - f, 8.5 + f * 1.0)],
                      _lerp(ROPE, BONE_DARK, 0.40), z=1.2))
    s.append(blob(_lerp(IRON, RUST, 0.46), 2.4, 1.8, off=(12.0, 5.0), z=1.5))
    # the second strap survives only as a stub still buckled to the far shoulder
    s.append(poly([(-8.0, 15.4), (-4.0, 16.2), (-1.0, 12.0), (-4.4, 11.0)], STRAP, z=1.1))
    s.append(blob(_lerp(IRON, RUST, 0.46), 2.2, 1.7, off=(-6.0, 15.0), z=1.5))
    _grit(s, -22.0, 22.0, 0.8, z=2.6, n=7)
    return s, (W, H)

# ---------------------------------------------------------------------------
def windlass():
    """A hand winch over a shaft, ~3.0 tiles.

    The digger's, and the piece that makes the dig read as EQUIPPED rather than
    frantic. A man scratching at the ground with his hands is desperate; a man
    who built a windlass has been at this long enough to build one, and that
    length of time is the sad part.

    THE FIRST CUT WAS A SAWHORSE WITH A ROLLING PIN ON IT. Two failures: the drum
    sat at the very top of two long splayed legs, which is the silhouette of a
    trestle, and the crank was a nub instead of an arm. A windlass reads by its
    CRANK -- an offset arm with a handle across the end of it, sticking out past
    the frame, at a height a standing person would turn. So the drum has come
    down to two-thirds height, the legs are near-vertical with a cross-brace
    (which is what actually stops a winch racking), and the crank is a real
    two-part arm with the handle at right angles to it.

    THE DRUM IS WORN BRIGHT WHERE THE ROPE RUNS AND NOWHERE ELSE. Wear that is
    only where a hand or a rope actually touches is the cheapest way to say a
    thing has been used, and it is the detail this whole region runs on.
    """
    s = []
    W, H = 120, 96
    DRUM_Y = 58.0
    # the shaft collar, and the dark below it
    s.append(blob(_lerp(EARTH_DARK, EARTH, 0.24), 38.0, 10.0, off=(0.0, 9.0), z=0))
    s.append(blob((10, 10, 11), 26.0, 6.5, off=(0.0, 9.0), z=0.3, rim=0.0))
    # two near-vertical legs, and a cross-brace between them
    for sx, lean in ((-26.0, 0.055), (26.0, -0.055)):
        s.append(poly([(sx - 5.5, 3.0), (sx + 5.5, 3.0),
                       (sx + 4.5 + 72.0 * lean, 75.0), (sx - 4.5 + 72.0 * lean, 75.0)],
                      _lerp(TIMBER, TIMBER_DARK, 0.22), z=1))
        s.append(poly([(sx - 5.5, 3.0), (sx - 2.0, 3.0),
                       (sx - 2.0 + 72.0 * lean, 75.0), (sx - 5.5 + 72.0 * lean, 75.0)],
                      _lerp(TIMBER, TIMBER_LIT, 0.40), z=1.1))
    s.append(poly([(-24.0, 30.0), (24.0, 32.0), (24.0, 37.0), (-24.0, 35.0)],
                  _lerp(TIMBER, TIMBER_DARK, 0.36), z=0.9))
    # the drum: iron, rusted, at two-thirds height where a hand would reach it
    s.append(rect(-21.0, DRUM_Y - 8.0, 21.0, DRUM_Y + 8.0, _lerp(IRON, RUST, 0.36), z=2))
    s.append(rect(-21.0, DRUM_Y + 3.0, 21.0, DRUM_Y + 8.0, _lerp(IRON_LIT, ASH, 0.20), z=2.1))
    s.append(rect(-5.0, DRUM_Y - 8.0, 5.0, DRUM_Y + 8.0, _lerp(IRON_LIT, ASH, 0.44), z=2.2))
    for ex in (-23.0, 23.0):
        s.append(blob(_lerp(IRON, RUST, 0.5), 4.5, 9.0, off=(ex, DRUM_Y), z=2.3))
    # rope wound on the drum, a few turns, and they are not evenly pitched
    for k in range(5):
        rx = -16.0 + k * 8.0 + (_h(k, 91) - 0.5) * 2.0
        s.append(rect(rx, DRUM_Y - 7.0, rx + 3.0, DRUM_Y + 7.0,
                      _lerp(ROPE, TIMBER_DARK, 0.2 + _h(k, 93) * 0.3), z=2.4))
    # THE CRANK: an offset arm out past the frame, with the handle across its end
    s.append(poly([(23.0, DRUM_Y - 3.0), (27.0, DRUM_Y - 3.0),
                   (41.0, DRUM_Y - 24.0), (37.0, DRUM_Y - 26.0)],
                  _lerp(IRON, IRON_LIT, 0.30), z=2.6))
    s.append(poly([(34.0, DRUM_Y - 30.0), (46.0, DRUM_Y - 22.0),
                   (43.0, DRUM_Y - 18.0), (31.0, DRUM_Y - 26.0)],
                  _lerp(IRON, RUST, 0.30), z=2.7))
    # the wooden grip, worn pale -- the one place a hand actually goes
    s.append(blob(_lerp(TIMBER_LIT, ASH, 0.34), 4.0, 6.4, off=(44.0, DRUM_Y - 21.0), z=2.8))
    # the rope, hanging into the hole, with a bucket just below the lip
    s.append(rect(-2.2, 14.0, 2.2, DRUM_Y - 6.0, _lerp(ROPE, TIMBER_DARK, 0.3), z=1.8))
    s.append(poly([(-10.0, 6.0), (10.0, 6.0), (8.5, 21.0), (-8.5, 21.0)],
                  _lerp(IRON, RUST, 0.5), z=1.9))
    s.append(poly([(-10.0, 19.0), (10.0, 19.0), (10.0, 21.0), (-10.0, 21.0)],
                  _lerp(IRON_LIT, RUST, 0.4), z=1.95))
    _spoil(s, 0.0, 106.0, 12.0, z=4.0, n=11)
    return s, (W, H)

# ---------------------------------------------------------------------------
def dig_frame():
    """A scavenged timber A-frame over a hole, ~4.5 tiles.

    THE POINT OF THIS PIECE IS THAT NONE OF IT MATCHES. Three different timbers,
    one of them a ship's spar with the rope-holes still in it, one a squared beam
    from a building, one a raw pole. Lashed, not jointed. It is the Shelf's
    headframe built by one man out of whatever the tide left, and a player who
    came up through region 1 has seen the real thing to compare it to.

    That comparison is the region's argument in a single object: somebody who
    knows how mines are built, working alone, with no materials.
    """
    s = []
    W, H = 140, 144
    apex = (2.0, 118.0)
    # leg A: a ship's spar, round, with rope-holes
    s.append(poly([(-54.0, 0.0), (-42.0, 0.0), (apex[0] + 5.0, apex[1]),
                   (apex[0] - 5.0, apex[1])], _lerp(TIMBER, TIMBER_DARK, 0.14), z=1))
    s.append(poly([(-54.0, 0.0), (-49.0, 0.0), (apex[0] - 1.0, apex[1]),
                   (apex[0] - 5.0, apex[1])], _lerp(TIMBER, TIMBER_LIT, 0.44), z=1.1))
    for k in range(3):
        t = 0.24 + k * 0.24
        s.append(blob((13, 12, 11), 2.6, 2.6,
                      off=(-48.0 + (apex[0] + 48.0) * t, apex[1] * t), z=1.2, rim=0.0))
    # leg B: a squared beam, and it is the only straight edge in the piece
    s.append(poly([(46.0, 0.0), (58.0, 0.0), (apex[0] + 8.0, apex[1]),
                   (apex[0] - 1.0, apex[1])], _lerp(TIMBER, TIMBER_DARK, 0.30), z=0.9))
    # leg C: a raw pole, bracing the back, shorter
    s.append(poly([(22.0, 0.0), (30.0, 0.0), (apex[0] + 12.0, 82.0),
                   (apex[0] + 6.0, 84.0)], _lerp(TIMBER, TIMBER_DARK, 0.44), z=0.7))
    # the lashings: rope, not iron. Three wraps, uneven.
    for k, y in enumerate((apex[1] - 6.0, apex[1] - 14.0, apex[1] - 23.0)):
        w = 11.0 + k * 2.6
        s.append(poly([(apex[0] - w, y), (apex[0] + w, y + 1.0),
                       (apex[0] + w, y + 4.0), (apex[0] - w, y + 3.0)],
                      _lerp(ROPE, TIMBER_DARK, 0.18 + _h(k, 83) * 0.3), z=2 + k * 0.05))
    # the sheave: a wooden pulley, and it is a REAL hole, not a pale disc
    # (env_shelf's first sheave shipped as a filled rust circle and read as a
    # clock face -- in a game whose protagonist keeps clocks)
    s.append(blob(_lerp(TIMBER, TIMBER_DARK, 0.2), 10.0, 10.0, off=(apex[0], apex[1] - 2.0), z=2.4))
    s.append(blob((12, 11, 10), 5.4, 5.4, off=(apex[0] - 0.6, apex[1] - 1.4), z=2.5, rim=0.0))
    # the rope down into the hole
    s.append(rect(apex[0] - 2.0, 6.0, apex[0] + 2.0, apex[1] - 6.0,
                  _lerp(ROPE, TIMBER_DARK, 0.34), z=2.2))
    s.append(blob((10, 10, 11), 22.0, 6.0, off=(apex[0], 6.0), z=0.4, rim=0.0))
    _spoil(s, 0.0, 124.0, 14.0, z=4.0, n=12)
    return s, (W, H)


# ---------------------------------------------------------------------------
def barrow():
    """A wheelbarrow, tipped on its side, ~1.6 tiles.

    Tipped, not broken. Broken says violence; tipped says somebody set it down
    hard and did not come back for it today, and "not today" repeated for years
    is what this region is.

    THE WHEEL IS OFF THE GROUND, which is the whole read: a barrow standing on
    its wheel is parked, a barrow on its side is abandoned, and the difference is
    about six pixels of rotation.
    """
    s = []
    W, H = 110, 52
    # the tray, on its side, mouth toward us
    tray = [(-34.0, 6.0), (26.0, 3.0), (36.0, 30.0), (-24.0, 36.0)]
    s.append(poly(tray, _lerp(IRON, RUST, 0.30), z=0))
    s.append(poly([(-30.0, 9.0), (22.0, 6.5), (30.0, 27.0), (-21.0, 32.0)],
                  _lerp(IRON, IRON_LIT, 0.26), z=0.3))
    # rust bloom, and it is on the inside where water stood
    for i in range(5):
        r = 3.0 + _h(i, 89) * 4.0
        s.append(blob(_lerp(RUST, IRON, 0.30), r, r * 0.7,
                      off=(-20.0 + i * 12.0, 12.0 + _h(i, 91) * 12.0), z=0.5))
    # the handles, both up in the air
    for k, (y0, y1) in enumerate(((8.0, 16.0), (16.0, 26.0))):
        s.append(poly([(26.0, y0), (66.0, y0 + 10.0 + k * 3.0),
                       (66.0, y0 + 14.0 + k * 3.0), (26.0, y0 + 4.0)],
                      _lerp(TIMBER, TIMBER_LIT, 0.32 - k * 0.14), z=1 + k * 0.1))
    # THE WHEEL, off the ground, and you can see through it
    s.append(blob(_lerp(IRON, RUST, 0.44), 13.0, 13.0, off=(-40.0, 26.0), z=1.4))
    s.append(blob((12, 12, 12), 8.0, 8.0, off=(-40.0, 26.0), z=1.5, rim=0.0))
    for k in range(4):
        a = math.pi * k / 4.0 + 0.3
        s.append(poly([(-40.0 + math.cos(a) * 12.0, 26.0 + math.sin(a) * 12.0),
                       (-40.0 - math.cos(a) * 12.0, 26.0 - math.sin(a) * 12.0),
                       (-40.0 - math.cos(a) * 12.0 + 1.6, 26.0 - math.sin(a) * 12.0 + 1.6),
                       (-40.0 + math.cos(a) * 12.0 + 1.6, 26.0 + math.sin(a) * 12.0 + 1.6)],
                      _lerp(IRON_LIT, RUST, 0.3), z=1.6))
    _grit(s, -46.0, 46.0, 1.0, z=2, n=8)
    return s, (W, H)


# ---------------------------------------------------------------------------
def dig_lamp():
    """The Scar's gate light, ~2.2 tiles -- and it is a DIGGING lamp.

    `GATE_PROPS` in OverworldScene names this piece for region 3's entrance, so
    it is the first thing the player sees of the Scar and it has to set the
    region up in one object. Its counterpart is the Shelf's `lantern`, which is a
    miner's SAFETY lamp: gauze bars, because down there people knew the air was
    bad. This one has no gauze -- up here the air is fine, and that difference is
    the crossing.

    What it has instead is A REFLECTOR HOOD, POINTED DOWN. Not out at the road,
    not up at the sky: at the ground. Somebody works here at night, and what they
    are looking at is the dirt. That single angle is the region's whole activity
    stated before the player has walked a tile into it, and it is also the
    tracking mechanic (§6.4: "the tracking progression runs in the ground")
    given a physical reason to exist.

    It is still burning, because nothing in this world decays -- and it is the
    brightest thing in region 3, and it is small (§3).
    """
    s = []
    W, H = 64, 70
    # a driven iron stake, bent where it hit something
    s.append(poly([(-3.0, 0.0), (3.0, 0.0), (5.0, 30.0), (-1.0, 30.0)],
                  _lerp(IRON, RUST, 0.34), z=0))
    s.append(poly([(-1.0, 30.0), (5.0, 30.0), (9.0, 54.0), (3.0, 54.0)],
                  _lerp(IRON, IRON_LIT, 0.26), z=0.1))
    _spoil(s, 0.0, 40.0, 5.0, z=0.2, n=6, warm=0.05)
    # the oil vessel
    s.append(poly([(-9.0, 50.0), (13.0, 50.0), (11.0, 60.0), (-7.0, 60.0)],
                  _lerp(IRON, RUST, 0.44), z=1))
    s.append(poly([(-9.0, 50.0), (-3.0, 50.0), (-1.0, 60.0), (-7.0, 60.0)],
                  _lerp(IRON_LIT, ASH, 0.18), z=1.1))
    # THE HOOD, and it is angled DOWN and to the near side
    hood = [(-16.0, 66.0), (18.0, 62.0), (24.0, 52.0), (-10.0, 56.0)]
    s.append(poly(hood, _lerp(IRON, IRON_LIT, 0.20), z=2.4))
    s.append(poly([(-16.0, 66.0), (18.0, 62.0), (17.0, 64.0), (-15.0, 68.0)],
                  _lerp(IRON_LIT, ASH, 0.30), z=2.5))
    # the reflector's inside, catching the flame -- warm, and NOT emissive:
    # this is reflected light, and making it glow too would double-count it
    s.append(poly([(-10.0, 56.0), (24.0, 52.0), (20.0, 58.0), (-8.0, 61.0)],
                  _lerp(FLAME, RUST, 0.52), z=2.2))
    # the flame, under the hood, small
    _flame(s, 4.0, 58.0, z=3.0, r=3.4)
    # and the pool it throws on the ground, which is the point of the whole prop
    s.append(blob(_lerp(FLAME, (48, 30, 12), 0.72), 22.0, 6.0, off=(2.0, 4.0),
                  z=0.05, glow=1.0, rim=0.0))
    return s, (W, H)


def oasis_spring():
    """A clear spring, ~4.4 tiles. THE ONLY CLEAN WATER, AND THE THIRD ATTEMPT.

    Every other water surface the player has crossed since region 0 has been
    something they were under, or something standing in a hole. This one has a
    BOTTOM you can see, and that is the whole trick: visible depth means clear,
    and clear is the single most restful thing an image can contain after four
    regions of murk. §6.4: "no reward but itself, and only a player who has
    stopped hurrying will ever stand in it."

    THE FIRST CUT READ AS A CONCRETE SLAB: the water was the same 29%-saturated
    grey-teal as every other surface, and there was no specular at all.

    THE SECOND CUT READ AS A BEACHED WHALE WITH A STICKER ON IT, and the two
    causes are now laws in the style contract:

      * A SMOOTH ELLIPSE IS A MANUFACTURED SILHOUETTE. Fifteenth instance. A
        puddle has never once in the history of the world been an ellipse; it is
        the shape of the ground that holds it. The outline is authored point by
        point now, with two lobes and a pinch between them, because water finds
        the low line and the low line is not round.

      * A SPECULAR IS A THIN BROKEN LINE, NOT A ROUNDED PILL. I read "a specular
        is what makes a surface read as liquid" and drew three fat lozenges,
        which is a plastic label, not a reflection. A real sky-glint on still
        water is a set of very long very THIN slivers of unequal length lying
        along the surface, and the brightest one is the shortest. Aspect ratio
        is the whole tell: at 15:1 it is water, at 4:1 it is a badge.

    AND THE THING THAT ACTUALLY SELLS IT IS THE REFLECTION. A dark inverted
    smear of the back rock, hanging down INTO the pool from where the rock meets
    the surface. Nothing else in this game reflects anything; one dark smudge in
    the right place does more than every glint on the piece.
    """
    s = []
    W, H = 140, 44
    # the ground the pool sits in: a shallow damp bowl, darker than the plate
    s.append(blob(_lerp(EARTH_DARK, EARTH, 0.30), 66.0, 15.0, off=(0.0, 15.0), z=0))
    s.append(blob(_lerp(EARTH, MOSS, 0.16), 58.0, 11.5, off=(2.0, 14.0), z=0.1))

    # THE OUTLINE, authored. Two lobes and a pinch: the shape of the low ground.
    RIM = [(-56.0, 14.0), (-49.0, 20.5), (-38.0, 24.0), (-25.0, 25.5), (-14.0, 23.0),
           (-6.0, 19.5), (2.0, 22.0), (13.0, 25.0), (26.0, 24.0), (37.0, 20.0),
           (44.0, 14.5), (41.0, 8.5), (30.0, 4.5), (16.0, 3.0), (3.0, 4.5),
           (-9.0, 3.5), (-24.0, 4.0), (-38.0, 6.5), (-50.0, 9.5)]
    s.append(poly(RIM, WATER_DEEP, z=1.0, rim=0.0))
    # the shallows: the same outline pulled in toward the near edge, so the pool
    # is deep at the BACK and you can see the bottom at the front
    near = [(x * 0.86, 5.0 + (y - 5.0) * 0.62) for x, y in RIM]
    s.append(poly(near, WATER, z=1.1, rim=0.0))
    # four stones ON THE BOTTOM, seen THROUGH the water, so they are DARKER than
    # it and never break the surface. Clustered, unequal, and not in a line.
    for i, (bx, by, br) in enumerate(((-31.0, 11.0, 5.4), (-24.0, 14.5, 3.2),
                                      (-27.5, 8.0, 2.4), (19.0, 12.0, 4.0))):
        s.append(blob(_lerp(WATER_DEEP, STONE, 0.20 + _h(i, 811) * 0.14),
                      br, br * 0.62, off=(bx, by), z=1.3, rim=0.0))

    # THE BACK ROCK, half-sunk at the far lip and overlapping the water: the
    # occlusion is what makes the pool sit IN the ground instead of on it.
    # AND IT WAS A STICKER. Seven points, near-regular, pale grey, and sitting
    # DEAD CENTRE on the pool -- so it read as a hexagon decal pasted onto the
    # water rather than a boulder standing behind it. Three fixes: OFF-CENTRE
    # (nothing important belongs in the middle of a symmetrical shape), LOWER
    # AND WIDER (a rock at a waterhole is half-buried, not a standing slab), and
    # an outline with no two edges the same length -- regularity is what made a
    # rock read as a shape.
    s.append(poly([(-44.0, 17.0), (-36.0, 21.5), (-27.0, 22.0), (-19.0, 19.0),
                   (-15.0, 24.0), (-21.0, 29.0), (-33.0, 30.5), (-43.0, 26.0),
                   (-47.0, 21.0)],
                  _lerp(STONE, EARTH, 0.48), z=1.6))
    s.append(poly([(-44.0, 17.0), (-36.0, 21.5), (-27.0, 22.0), (-19.0, 19.0),
                   (-22.0, 22.5), (-33.0, 25.0), (-42.0, 21.0)],
                  _lerp(STONE_LIT, BONE_DARK, 0.42), z=1.65))
    # THE REFLECTION. One dark smear, hanging straight down off the contact.
    s.append(poly([(-42.0, 17.5), (-18.0, 18.5), (-21.0, 10.0), (-30.0, 7.0), (-39.0, 11.0)],
                  _lerp(WATER_DEEP, CHAR, 0.34), z=1.7, rim=0.0))

    # THE GLINTS: five slivers, 12:1 to 22:1, unequal, and the brightest is the
    # shortest. They lie along the surface, never across it.
    for i, (gx, gy, gw, ga) in enumerate(((-40.0, 12.0, 15.5, 0.34),
                                          (-18.0, 8.0, 9.0, 0.20),
                                          (14.0, 19.0, 11.0, 0.52),
                                          (24.0, 13.5, 6.5, 1.00),
                                          (33.0, 9.0, 4.0, 0.44))):
        s.append(blob(_lerp(WATER_LIT, SKY_GLINT, ga), gw, gw / (13.0 + i * 2.2),
                      off=(gx, gy), z=2.0 + i * 0.01, rim=0.0))
    # the near meniscus: a broken bright hairline where the water meets the
    # earth, and it is broken because a continuous one is a drawn edge
    for i, (mx, mw) in enumerate(((-44.0, 9.0), (-27.0, 13.0), (-4.0, 7.0), (22.0, 11.0))):
        s.append(blob(_lerp(WATER_LIT, MOSS_LIT, 0.22), mw, 0.62,
                      off=(mx, 4.4 + _h(i, 813) * 1.6), z=2.2, rim=0.0))
    # damp moss where the water actually touches -- two clumps, one bank only.
    # BLADES, NOT BEADS: three flattened green ellipses at the rim read as peas
    # on a plate. A plant at a waterhole is a tuft, and a tuft is thin verticals.
    for i, (mx, my, mn) in enumerate(((-52.0, 9.0, 5), (36.0, 11.0, 4), (24.0, 5.5, 3))):
        for k in range(mn):
            bx = mx + (k - mn * 0.5) * 3.1 + (_h(i * 9 + k, 817) - 0.5) * 2.6
            hgt = 4.2 + _h(i * 9 + k, 819) * 5.0
            lean = (_h(i * 9 + k, 821) - 0.5) * 4.2
            s.append(poly([(bx - 1.0, my), (bx + 1.0, my),
                           (bx + lean + 0.4, my + hgt), (bx + lean - 0.4, my + hgt)],
                          _lerp(MOSS, MOSS_LIT, 0.14 + _h(i * 9 + k, 823) * 0.52), z=2.4))
    _grit(s, -62.0, 62.0, 1.0, z=3.0, n=10)
    return s, (W, H)


def oasis_shoot():
    """New growth, ~2.8 tiles -- and ONE OF THEM IS IN BUD.

    §6.4 names this exactly: "visible growth, new shoots, something in bud". The
    bud is the brightest small thing in region 3 after the dig lamp's flame, and
    it is the only object in the whole game that is going to be DIFFERENT
    TOMORROW. Everything else in this world is preserved -- that is the setting's
    premise, nothing decays, the lamps are still lit a century on. A bud is the
    one thing here that has a next week.

    THIN, AND UPRIGHT, AND EVERY STEM A DIFFERENT HEIGHT. The Scar's silhouette
    vocabulary is broken stumps and slumped heaps -- all horizontals and all
    snapped. Nine straight vertical lines is a shape this region does not
    otherwise contain, so the Oasis reads from off-screen before the colour does.
    """
    s = []
    W, H = 100, 90
    # a low pad of moss for them to come out of (they are not growing in ash)
    s.append(blob(_lerp(MOSS, (24, 56, 36), 0.36), 34.0, 8.0, off=(0.0, 6.0), z=0))
    stems = [(-30.0, 40.0, 0.10), (-22.0, 62.0, -0.04), (-13.0, 52.0, 0.06),
             (-4.0, 78.0, -0.02), (5.0, 58.0, 0.08), (13.0, 70.0, -0.06),
             (22.0, 46.0, 0.03), (30.0, 64.0, -0.09), (-36.0, 30.0, 0.14)]
    for i, (sx, top, bow) in enumerate(stems):
        pts = []
        for k in range(9):
            t = k / 8.0
            pts.append((sx + bow * top * (t ** 1.6), 4.0 + (top - 4.0) * t))
        w = 1.5 + _h(i, 157) * 0.9
        s.append(poly([(x - w, y) for x, y in pts] + [(x + w, y) for x, y in pts][::-1],
                      _lerp(MOSS_LIT, LEAF, 0.20 + _h(i, 163) * 0.55), z=1 + i * 0.05))
        # two leaves per stem, alternating, and they are small
        for k, ft in ((0, 0.42), (1, 0.68)):
            lx = sx + bow * top * (ft ** 1.6)
            ly = 4.0 + (top - 4.0) * ft
            d = 1.0 if (i + k) % 2 == 0 else -1.0
            s.append(poly([(lx, ly), (lx + d * 11.0, ly + 4.0), (lx + d * 8.0, ly + 7.5)],
                          _lerp(LEAF, MOSS, 0.24 + _h(i * 2 + k, 167) * 0.34),
                          z=1.4 + i * 0.05))
    # THE BUD, on the tallest stem, and it is the only thing in the Scar that is
    # about to happen
    bx, by = -4.0 - 0.02 * 78.0 * 1.0, 78.0
    s.append(blob(_lerp(BUD, LEAF, 0.42), 4.6, 8.0, off=(bx, by + 3.0), z=3.0))
    s.append(blob(_lerp(BUD, (246, 244, 206), 0.34), 2.6, 5.4, off=(bx - 1.0, by + 4.2), z=3.1))
    for d in (-1.0, 1.0):   # the sepals still holding it closed
        s.append(poly([(bx, by - 1.0), (bx + d * 6.0, by + 3.0), (bx + d * 2.0, by + 6.0)],
                      _lerp(MOSS_LIT, LEAF, 0.3), z=3.2))
    return s, (W, H)


def oasis_rill():
    """The spring's overflow, ~4.0 tiles. The seam that makes the Oasis ONE place.

    Without it the Oasis is a scatter of unrelated green props; with it the water
    has a source and a direction, and four of these laid end to end downhill say
    "this came from up there" without a word.

    THREE CUTS, THREE DIFFERENT WRONG OBJECTS, one cause each time:

    A MILLIPEDE -- twenty-six green bobbles in two even rows.
    A BAND-AID -- a hard-edged saturated blue lozenge with green nubs on it.
    A BARNACLED LOG -- and this one is the instructive failure. The water had
    been fixed (three pixels, dark, only three dashes) but the CHANNEL had not:
    a 120x10 polygon of dark earth with a continuous lit edge running its whole
    length is the textbook way to draw a CYLINDER, and round green blobs sitting
    on a cylinder are barnacles. A continuous highlight along a long mass states
    curvature, so it can only ever be a log, a pipe or a rope. The lit lip is
    broken into four short segments now -- ground catches light in patches,
    because ground is not turned -- and the channel is narrower and mid-valued
    instead of near-black, so it reads as a groove IN something rather than a
    thing lying ON something.

    A rill is a scratch. The channel is four tiles long, the wet thread inside it
    is three pixels across, and the green is on ONE bank, in two clumps, as
    BLADES rather than beads -- a bead is a barnacle, a blade is a plant.
    """
    s = []
    W, H = 130, 32
    # the cut channel: irregular width, and it MEANDERS -- a straight one is a gutter
    def wob(t):
        return math.sin(t * 5.4) * 2.6 + math.sin(t * 11.0 + 1.2) * 1.1
    top, bot = [], []
    for i in range(19):
        t = i / 18.0
        x = -60.0 + 120.0 * t
        y = 11.0 + wob(t)
        hw = 3.1 + 1.4 * math.sin(t * 7.3 + 0.6)
        top.append((x, y + hw))
        bot.append((x, y - hw))
    s.append(poly(top + bot[::-1], _lerp(EARTH_DARK, EARTH, 0.62), z=0, rim=0.0))
    # the uphill lip catches the light IN PATCHES -- a continuous run of it down
    # a long mass is what made this a log. Four segments, uneven, with gaps.
    for i0, i1 in ((1, 4), (6, 9), (11, 13), (15, 18)):
        seg = top[i0:i1 + 1]
        s.append(poly(seg + [(x, y - 1.3) for x, y in seg][::-1],
                      _lerp(EARTH, EARTH_LIT, 0.30), z=0.2, rim=0.0))
    # THE WET THREAD: three pixels, and it is water, not a hole
    thr_t, thr_b = [], []
    for i in range(19):
        t = i / 18.0
        x = -58.0 + 116.0 * t
        y = 11.0 + wob(t) * 0.92
        hw = 1.4 + 0.6 * math.sin(t * 9.1 + 2.0)
        thr_t.append((x, y + hw)); thr_b.append((x, y - hw))
    s.append(poly(thr_t + thr_b[::-1], _lerp(WATER_DEEP, WATER, 0.42), z=1.0, rim=0.0))
    # three dashes where it shoals at a bend -- and nowhere else
    for i, t in enumerate((0.17, 0.53, 0.79)):
        x = -58.0 + 116.0 * t
        s.append(blob(_lerp(WATER, WATER_LIT, 0.30 + i * 0.22),
                      4.2 - i * 0.9, 0.5, off=(x, 11.0 + wob(t) * 0.92), z=1.2, rim=0.0))
    # green on ONE bank, two clumps, bare between -- BLADES, not beads
    for i, (t0, t1) in enumerate(((0.06, 0.24), (0.58, 0.81))):
        n = 4 + i
        for k in range(n):
            t = t0 + (t1 - t0) * (k / max(1, n - 1))
            x = -58.0 + 116.0 * t + (_h(i * 7 + k, 829) - 0.5) * 5.0
            y0 = 11.0 + wob(t) + 4.4
            hgt = 5.6 + _h(i * 5 + k, 823) * 5.4
            lean = (_h(i * 5 + k, 833) - 0.5) * 5.0
            wdt = 1.1 + _h(k, 839) * 0.7
            s.append(poly([(x - wdt, y0), (x + wdt, y0),
                           (x + lean + 0.5, y0 + hgt), (x + lean - 0.5, y0 + hgt)],
                          _lerp(MOSS, MOSS_LIT, 0.10 + _h(i * 5 + k, 827) * 0.52), z=1.6))
    # one blade of something, leaning over the water. The tallest here.
    s.append(poly([(-22.0, 15.0), (-20.4, 15.0), (-12.0, 26.0), (-13.8, 26.6)],
                  _lerp(MOSS_LIT, LEAF, 0.44), z=1.8))
    _grit(s, -64.0, 64.0, 1.0, z=2.4, n=8)
    return s, (W, H)

# RECONSTRUCTED BY HAND, TWICE. A `swap()`-style splice that cuts from `def
# <name>:` to the next `\ndef ` deletes everything in between -- and what sits
# between the last piece and `def build` is THIS DICT. If you script an edit to
# a piece in this file, bound the cut at `\nPIECES` as well, and check the
# assertion below before you walk away.
PIECES = {
    # THE LANDMARKS -- one of these is enough to name the region from off-screen
    "den_mouth": den_mouth,
    "dig_frame": dig_frame,
    "burnt_spar": burnt_spar,
    "burnt_stand": burnt_stand,
    # THE WORKINGS -- somebody dug here, and stopped
    "windlass": windlass,
    "cairn": cairn,
    "spoil_heap": spoil_heap,
    "trench": trench,
    "barrow": barrow,
    "dig_lamp": dig_lamp,
    # WHAT IS LEFT OF THE PEOPLE
    "bone_pile": bone_pile,
    "pilgrim_pack": pilgrim_pack,
    # THE OASIS -- the one pocket of living green in the region (§6.4)
    "oasis_spring": oasis_spring,
    "oasis_shoot": oasis_shoot,
    "oasis_rill": oasis_rill,
}
assert len(PIECES) == 15, "env_scar ships 15 pieces; got %d (splice bug?)" % len(PIECES)


def build(name):
    shapes, size = PIECES[name]()
    # THE ONE WARM RIM IN THE GAME -- see the note at the top of the file. The
    # Fold, Shelf and Breach are lit cold (teal, kelp, pale surface); the Scar is
    # the first region with open sky over it and its light is a dusty sun.
    p = Painter(size, rim_col=(198, 164, 126))
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
        print("%-14s %5.2fs  %dx%d" % (name, time.time() - t, img.width, img.height))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
