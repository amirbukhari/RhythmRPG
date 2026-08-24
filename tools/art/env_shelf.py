"""The Kelp Shelf's environment kit -- the dead forest, and the town that dug.

    python3 tools/art/env_shelf.py            # all pieces
    python3 tools/art/env_shelf.py hull mast

WHAT THIS REGION IS
world-bible §6.2, the flight: "Ship skeletons standing like a dead forest, every
hull pointing up, and the salt-wracked remains of a mining town that dug into
something and stayed."

And underneath that, the thing the region actually exists for: "Nari is *with
him* here, and this region exists to make that hurt later." The two near-drops
happen here, both of them the player's own hands. So the kit has to build a
place you climb, with gaps in it -- not scenery you walk past.

WHY THE HULLS POINT UP, AND WHY THAT IS THE WHOLE REGION
It is the region's one image and it is doing two jobs at once. Literally: every
ship that ever sank was heading for the surface, so a seabed full of wrecks is
a seabed full of arrows pointing the way out. And structurally: they are the
LADDER. The echoes already say it -- "Every ship that ever sank points the same
way. Up." and "Dead ships stand like trees down here. We climb them to feel
tall." A wreck lying on its side would be debris. Standing, it is hope, and it
is the reason a clock-keeper with no business climbing anything is climbing.

WHY THE KIT IS NOT THE RETIRED `saltmines`
Region 1's kit slot was named `saltmines` and its accent was ochre. The mine is
half-right -- §6.2 does put a mining town here -- but the region is SUBMERGED
(its districts are `kelpforest`, `mastsilt`, `paleshoal`, all cold greens), and
an ember-lit ochre mine road belongs to a dry cosmology that v16.0 deleted. So
the mine is here, drowned: iron gone to rust under salt, timber waterlogged
black, nothing lit. The one warm thing in this region is Mir's own lamp, and he
brought it.

MATERIAL DISCIPLINE, INHERITED FROM THE FOLD
Everything is authored ~30% darker than it reads right in isolation, for the
reason env_fold.py documents at length: the overworld lays additive haze and
god-rays over the whole scene, and a TALL sprite collects far more of both than
a low one. These are the tallest pieces in the game, so they are the most
exposed to it -- a hull authored at a comfortable value comes back a pale grey
billboard. Verify in the browser (tools/capture.mjs), never on a contact sheet.

SIZE CONVENTION
Author at ~2x canonical, i.e. **30 px per metre**. `worldScaleFor` floors the
render scale at 0.5 and snaps to halves, so a piece authored at twice its real
pixel height lands on 0.5 exactly and downsamples through the renderer's 4x
supersampling instead of being resized twice. Every piece here has an exact-key
entry in `src/scenes/env/WorldScale.ts` -- without one, loose patterns already in
that table claim these names (`/kelp/` -> 0.5m, `/rail/` -> 0.3m, `/ladder/` ->
2.0m), and a 14-metre shipwreck would ship at the size of a teacup.
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
OUT = ROOT / "assets" / "sprites" / "env" / "shelf"

# Shelf materials. Colder and GREENER than the Fold's stone, because the Shelf's
# accent is kelp green and the region is a drowned forest, not a town. Timber
# reads warm-black rather than brown: a century in salt water takes the brown
# out of oak and leaves it the colour of wet slate with a memory of grain.
TIMBER = (44, 41, 34)
TIMBER_LIT = (68, 63, 52)
TIMBER_DARK = (25, 23, 19)
IRON = (33, 37, 36)
IRON_LIT = (54, 60, 57)
RUST = (92, 52, 30)          # the mine's iron, oxidised -- the only warm note
SALT = (122, 133, 126)       # the crust that gets on everything
KELP = (24, 54, 38)
KELP_LIT = (46, 88, 58)
KELP_DARK = (14, 32, 24)
ROPE = (74, 68, 52)
BONE = (150, 152, 138)       # shell and barnacle


def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _root():
    return Skeleton([Joint("root", None, (0.0, 0.0), 0.0, 0.0)])


# Same reasoning as the Fold: a big flat plane traced on all four edges by a
# bright rim reads as a wireframe, not as a lit object.
STONE_RIM = 0.22


def rect(x0, y0, x1, y1, col, z=0, glow=0.0, rim=STONE_RIM):
    return Poly("root", col, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z=z, glow=glow, rim=rim)


def poly(pts, col, z=0, glow=0.0, rim=STONE_RIM):
    return Poly("root", col, pts, z=z, glow=glow, rim=rim)


def blob(col, rx, ry, off, z=0, glow=0.0, rim=STONE_RIM):
    return Blob("root", col, rx, ry, off=off, z=z, glow=glow, rim=rim)


def _h(i, salt=0):
    """Deterministic jitter -- no RNG anywhere in the art pipeline, so a rebuild
    is byte-identical and a diff means the art actually changed."""
    v = (i * 73856093) ^ (salt * 19349663)
    v &= 0xFFFFFFFF
    v = (v ^ (v >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65536.0


def _crust(s, x0, x1, y, z=40, n=None, scale=1.0):
    """Salt crust along a horizontal edge. Everything on the Shelf has it: it is
    what ties a rusted iron cart and a black timber rib into one place."""
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
        if _h(i, 21) < 0.26:
            continue
        t = (i + 0.5) / n + (_h(i, 23) - 0.5) * 1.7 / n
        x = x0 + (x1 - x0) * t
        r = (1.4 + _h(i, 11) ** 2 * 4.6) * scale
        s.append(blob(_lerp(SALT, BONE, _h(i, 13) * 0.5), r, r * 0.62,
                      off=(x, y + (_h(i, 19) - 0.5) * 3.0), z=z))


# ---------------------------------------------------------------------------
# the hull -- a ship stood on its stern, prow to the surface. THE piece.
# ---------------------------------------------------------------------------
def hull():
    """A ship's skeleton standing upright, ~14m, prow pointing up.

    WHAT MAKES IT READ AS A HULL AND NOT A TOWER. Three things, and all three
    are load-bearing:

      1. THE RIBS CURVE OUT FROM A KEEL. A vertical mast with horizontal bars
         is a pylon. Frames that bow outward from a central spine and close
         again at both ends are a ribcage, and a ribcage is the only shape in
         the world that reads as "this was alive or it carried something".
      2. THE SILHOUETTE IS A CONE, NOT AN OGIVE -- BROAD AND CUT FLAT AT THE
         BOTTOM, fining to a POINT at the top. That point is the prow, and it
         is what aims the piece at the surface; a blunt top would be a chimney.
         But the BOTTOM is the half that took two tries. An ogive closes to a
         point at both ends, and a shape that closes to a point at both ends
         with regular bars across it is a LEAF -- which is what the second cut
         came back as, having just stopped being a fishbone. A leaf is also
         symmetric about its axis, and a wreck never is. So the stern is left
         broad and cut off square, and the frames alternate reach: two ways of
         saying "this was torn, not grown".
      3. IT IS MOSTLY EMPTY. The planking is gone; what is left is the frame
         and a few strakes still clinging on. If the hull were skinned it would
         be a solid slab, which is exactly the failure the Fold's arch had --
         see `env_fold.arch`. Emptiness is the subject.

    AND IT LEANS. Nothing sinks upright and stays upright by choice; it leans
    against the slope it came to rest on. The lean is 4 degrees and it is the
    difference between a wreck and a monument.
    """
    s = []
    H = 420.0
    # 0.115 is ~6.6 degrees. It was 0.075 and it was not reading -- at ship size
    # a 4-degree lean is one pixel of offset over the whole height, which is to
    # say none, and an upright symmetric shape is exactly the leaf described
    # above. The lean is the cheapest asymmetry available and it does the most.
    LEAN = 0.115                       # x-offset per unit height

    def cx(y):
        return y * LEAN

    def half_w(y):
        """Beam at height y. Peaks at ~0.35H and closes to a point at the prow.

        WIDER THAN IT WANTS TO BE, AND MONOTONE. Two failures are baked into
        this one function. The first cut peaked at 44 over a 420 height --
        1:4.8 -- and read as a FEATHER, or a fern frond, or (worst and most
        accurate) a FISH SKELETON: ribs off a tapering central spine is the
        textbook picture of a fishbone. Widening it to 1:3 fixed that and
        produced a LEAF instead, because the sine lobe closed the shape to a
        point at the BOTTOM as well as the top.

        So the beam now DECREASES ALL THE WAY UP from a broad flat stern. The
        only inflection is a slight turn of the bilge in the lower third, which
        is where a real hull carries its volume. A monotone taper from a square
        end cannot be a leaf, and it cannot be a fishbone either.
        """
        t = max(0.0, min(1.0, y / H))
        taper = (1.0 - t ** 1.30) ** 0.58        # broad at the stern, fine at the prow
        bilge = 1.0 + 0.11 * math.sin(math.pi * min(1.0, t * 1.9))
        return 58.0 * taper * bilge

    # --- THE TRANSOM: the square-cut stern, said out loud -------------------
    # The taper alone leaves the bottom broad, but nothing at the bottom EDGE
    # says "cut". A flat board across the full beam does, and it is also the one
    # piece of planking that would survive down there in the silt.
    tw = half_w(4.0)
    s.append(poly([(cx(0.0) - tw, 0.0), (cx(0.0) + tw, 0.0),
                   (cx(16.0) + tw * 0.97, 16.0), (cx(16.0) - tw * 0.97, 16.0)],
                  _lerp(TIMBER, TIMBER_DARK, 0.30), z=1.2))
    s.append(poly([(cx(16.0) - tw * 0.97, 16.0), (cx(16.0) + tw * 0.97, 16.0),
                   (cx(19.0) + tw * 0.95, 19.0), (cx(19.0) - tw * 0.95, 19.0)],
                  _lerp(TIMBER_LIT, SALT, 0.18), z=1.3))

    # --- the keel: the spine, dead centre, dark ----------------------------
    keel = []
    for i in range(19):
        y = H * i / 18.0
        keel.append((cx(y) - 7.0, y))
    for i in range(19):
        y = H * (18 - i) / 18.0
        keel.append((cx(y) + 7.0, y))
    s.append(poly(keel, TIMBER_DARK, z=0))

    # --- the frames. 17 pairs, and NOT evenly spaced -----------------------
    # A rib cage is organic-regular, which is the one case where a repeat is the
    # subject -- but §4.5 still applies: an EXACT repeat reads as machined
    # scaffolding. So the pitch wobbles ~20%, four ribs are snapped short, and
    # the lit and shadow sides get different tones so the cage has a light
    # direction instead of a stripe pattern.
    NRIB = 17
    for i in range(NRIB):
        base = (i + 0.6) / (NRIB + 0.8)
        y = H * (base + (_h(i, 3) - 0.5) * 0.028)
        if y < 8.0 or y > H - 14.0:
            continue
        w = half_w(y)
        if w < 4.0:
            continue
        th = 3.4 + _h(i, 5) * 2.2
        snapped = _h(i, 7) > 0.74
        for sx in (-1.0, 1.0):
            # a rib is an arc: it leaves the keel angled up-and-out, then flattens
            reach = w * (0.42 if (snapped and sx > 0) else 1.0)
            pts = []
            NSEG = 7
            # THE BOW IS SMALL, AND IT VARIES PER RIB. It was a flat 0.30 for
            # every frame, which meant every rib made the same shallow arch and
            # the NEGATIVE SPACE between two consecutive ribs was a perfect
            # downward wedge. Seventeen of those stacked up the hull and the
            # piece read as a column of chevrons -- arrows, pointing down, in a
            # region whose one line is "every ship points the same way: up".
            # The gaps have to be irregular or they become the subject.
            bow = 0.09 + _h(i, 11) * 0.13
            for k in range(NSEG + 1):
                u = k / float(NSEG)
                px = cx(y) + sx * reach * u
                py = y + reach * bow * math.sin(u * math.pi * 0.55)
                pts.append((px, py))
            for k in range(NSEG, -1, -1):
                u = k / float(NSEG)
                px = cx(y) + sx * reach * u
                py = y + reach * 0.30 * math.sin(u * math.pi * 0.55) - th
                pts.append((px, py))
            lit = sx < 0                       # key light upper-LEFT, as the cast
            col = _lerp(TIMBER, TIMBER_LIT, 0.55) if lit else _lerp(TIMBER, TIMBER_DARK, 0.5)
            s.append(poly(pts, col, z=1 + i * 0.01 + (0.005 if lit else 0)))

    # --- THE SHEER STRAKES: the two members that make this a boat -----------
    # This is the whole difference between a hull and a fishbone. A rib cage with
    # nothing joining the rib TIPS is a spine with spines on it. A ship's frames
    # are tied together along their outer edge by a continuous longitudinal --
    # the sheer clamp under the gunwale -- and that single unbroken line running
    # the length of both sides is what the eye reads as "this enclosed a volume".
    # It survives on a real wreck long after the planking is gone, because it is
    # the heaviest timber in the topsides, so it is honest as well as legible.
    for sx in (-1.0, 1.0):
        lit = sx < 0
        outer, inner = [], []
        for k in range(25):
            y = H * k / 24.0
            w = half_w(y)
            if w < 2.0:
                w = 2.0
            outer.append((cx(y) + sx * w, y))
            inner.append((cx(y) + sx * max(2.0, w - 7.0), y))
        # a GAP in the near-side strake where it has been stove in, so the line
        # is continuous but not machined -- an unbroken sweep both sides would
        # read as a moulded plastic hull rather than as a hundred-year wreck.
        #
        # AS TWO POLYGONS, NOT ONE WITH A BITE OUT OF IT. The gap used to be cut
        # by deleting points 9..12 from `outer` and `inner` and filling the
        # result as a single polygon -- which does not make a gap, it makes a
        # long diagonal CHORD across the missing stretch, and the fill between
        # that chord and the opposite edge is a big solid TRIANGLE. Seventeen
        # hulls each wearing a downward-pointing wedge is why this region kept
        # coming back reading as a column of chevrons, and it survived the fix to
        # the rib bow because the ribs were never the thing making them.
        spans = [(0, 9), (13, len(outer))] if lit else [(0, len(outer))]
        body = _lerp(TIMBER, TIMBER_LIT, 0.60) if lit else _lerp(TIMBER, TIMBER_DARK, 0.44)
        for a, b in spans:
            if b - a < 2:
                continue
            s.append(poly(outer[a:b] + inner[a:b][::-1], body, z=2.5 + (0.05 if lit else 0)))
            if lit:   # the light catches the top edge of the sheer
                s.append(poly(outer[a:b] + [(px + 2.6, py) for px, py in outer[a:b]][::-1],
                              _lerp(TIMBER_LIT, SALT, 0.26), z=2.7))

    # --- the strakes still clinging on -------------------------------------
    # Three patches of surviving planking, on the SHADOW side only. Planking on
    # the lit side would fill the silhouette's bright edge and kill the cage
    # read; in shadow it registers as "there used to be a skin here" and no more.
    for pi, (y0f, y1f) in enumerate(((0.10, 0.27), (0.44, 0.55), (0.68, 0.76))):
        y0, y1 = H * y0f, H * y1f
        w0, w1 = half_w(y0), half_w(y1)
        s.append(poly([(cx(y0) + w0 * 0.30, y0), (cx(y0) + w0 * 0.94, y0),
                       (cx(y1) + w1 * 0.90, y1), (cx(y1) + w1 * 0.26, y1)],
                      _lerp(TIMBER_DARK, TIMBER, 0.42), z=3 + pi * 0.1))
        # plank seams: horizontal, and only 2-3, so it is a surface not a grille
        for k in range(3):
            yy = y0 + (y1 - y0) * (0.26 + k * 0.28)
            ww = half_w(yy)
            s.append(rect(cx(yy) + ww * 0.28, yy, cx(yy) + ww * 0.92, yy + 1.6,
                          TIMBER_DARK, z=3.5 + pi * 0.1))

    # --- the prow: a point, and the one place light lands cleanly ----------
    ty = H - 10.0
    s.append(poly([(cx(ty) - 6.0, ty - 46.0), (cx(ty) + 6.0, ty - 46.0),
                   (cx(H) + 2.0, H), (cx(H) - 2.0, H)],
                  _lerp(TIMBER, TIMBER_LIT, 0.34), z=6))
    s.append(poly([(cx(ty) - 6.0, ty - 46.0), (cx(ty) - 2.0, ty - 46.0),
                   (cx(H) - 2.0, H), (cx(H) - 2.0, H)],
                  _lerp(TIMBER_LIT, SALT, 0.30), z=6.1))

    # --- kelp has moved in, because a century has passed -------------------
    for i in range(7):
        y = H * (0.06 + _h(i, 23) * 0.46)
        w = half_w(y)
        sx = 1.0 if _h(i, 29) > 0.5 else -1.0
        s.append(poly([(cx(y) + sx * w * 0.7, y),
                       (cx(y) + sx * w * 0.95, y + 16.0 + _h(i, 31) * 22.0),
                       (cx(y) + sx * w * 0.42, y + 10.0 + _h(i, 37) * 26.0)],
                      _lerp(KELP, KELP_DARK, _h(i, 41) * 0.6), z=7 + i * 0.01))

    # --- buried in silt, and crusted --------------------------------------
    s.append(blob(TIMBER_DARK, 52.0, 13.0, off=(0.0, 8.0), z=-1))
    _crust(s, -40.0, 40.0, 6.0, z=40, n=9)
    _crust(s, cx(H * 0.3) - 30.0, cx(H * 0.3) + 30.0, H * 0.3, z=40, n=5, scale=0.7)
    return s, (170, 452)


def hull_broken():
    """A shorter wreck, ~7m, snapped off two-thirds up and canted harder.

    A FOREST NEEDS MORE THAN ONE TREE, AND MORE THAN ONE HEIGHT. Placed beside
    `hull` this is what makes the region read as a stand of wrecks rather than
    as one prop repeated -- and the snapped top matters more than the height:
    the tall one points at the surface, this one FAILED to. A slope with both on
    it says the climb is survivable and not guaranteed, which is the region.
    """
    s = []
    H = 210.0
    LEAN = 0.17                      # canted much harder: it lost

    def cx(y):
        return y * LEAN

    def half_w(y):
        # Monotone from a broad square stern, for both the reasons in
        # `hull.half_w`: a sine lobe here made a leaf too, and a SHORT leaf is
        # if anything worse -- at 8 metres it was the exact proportion of a bay
        # leaf. The taper stops early because this hull is snapped, so it never
        # gets near the fine end where a prow would be.
        t = max(0.0, min(1.0, y / H))
        taper = (1.0 - (t * 0.72) ** 1.25) ** 0.55
        bilge = 1.0 + 0.10 * math.sin(math.pi * min(1.0, t * 1.7))
        return 50.0 * taper * bilge

    keel = [(cx(y) - 6.5, y) for y in (H * i / 12.0 for i in range(13))]
    keel += [(cx(y) + 6.5, y) for y in (H * (12 - i) / 12.0 for i in range(13))]
    s.append(poly(keel, TIMBER_DARK, z=0))

    NRIB = 10
    for i in range(NRIB):
        y = H * ((i + 0.7) / (NRIB + 0.9) + (_h(i, 43) - 0.5) * 0.03)
        w = half_w(y)
        if w < 4.0 or y > H - 8.0:
            continue
        th = 3.6 + _h(i, 47) * 2.0
        for sx in (-1.0, 1.0):
            # the top three ribs on the lit side are sheared off at the break
            reach = w * (0.30 if (y > H * 0.66 and sx < 0) else 1.0)
            pts = []
            for k in range(8):
                u = k / 7.0
                pts.append((cx(y) + sx * reach * u, y + reach * 0.28 * math.sin(u * 1.7)))
            for k in range(7, -1, -1):
                u = k / 7.0
                pts.append((cx(y) + sx * reach * u, y + reach * 0.28 * math.sin(u * 1.7) - th))
            lit = sx < 0
            col = _lerp(TIMBER, TIMBER_LIT, 0.5) if lit else _lerp(TIMBER, TIMBER_DARK, 0.52)
            s.append(poly(pts, col, z=1 + i * 0.01))

    # the sheer strakes, stopping dead at the break -- see `hull`
    for sx in (-1.0, 1.0):
        lit = sx < 0
        outer, inner = [], []
        for k in range(17):
            y = H * k / 16.0
            w = max(2.0, half_w(y))
            outer.append((cx(y) + sx * w, y))
            inner.append((cx(y) + sx * max(2.0, w - 6.5), y))
        s.append(poly(outer + inner[::-1],
                      _lerp(TIMBER, TIMBER_LIT, 0.54) if lit else _lerp(TIMBER, TIMBER_DARK, 0.46),
                      z=2.5))

    # THE BREAK. Splintered, not cut: three teeth of different lengths, which is
    # the only thing that separates "snapped" from "sawn".
    tw = half_w(H)
    for k, f in enumerate((0.22, 0.62, 0.86)):
        x = cx(H) - tw * 0.7 + tw * 1.4 * f
        s.append(poly([(x - 4.0, H - 6.0), (x + 4.0, H - 6.0),
                       (x + 1.0, H + 8.0 + f * 22.0), (x - 2.0, H + 6.0 + f * 18.0)],
                      _lerp(TIMBER, SALT, 0.22), z=6 + k * 0.1))

    s.append(blob(TIMBER_DARK, 44.0, 12.0, off=(0.0, 7.0), z=-1))
    _crust(s, -34.0, 36.0, 5.0, z=40, n=8)
    return s, (150, 242)


def ribs():
    """A rib section half-buried and lying over, ~2.4m at the high end.

    THE LOW-DENSITY PIECE, and the kit needs one badly. A forest of tall things
    is a colonnade; what makes it a graveyard is the wreckage between the
    standing ones, at ankle height, that you walk over without stopping. This is
    also the piece that goes on the bad gaps' edges -- ribs sticking out of the
    slope are the handholds §6.2's climb is made of.
    """
    s = []
    s.append(poly([(-52.0, 6.0), (46.0, 2.0), (48.0, 12.0), (-50.0, 16.0)], TIMBER_DARK, z=0))
    for i in range(6):
        t = i / 5.0
        x = -44.0 + 84.0 * t
        h = 26.0 + math.sin(t * 2.6) * 34.0 + (_h(i, 53) - 0.5) * 12.0
        lean = (t - 0.45) * 26.0
        th = 3.2 + _h(i, 59) * 1.8
        pts = []
        for k in range(7):
            u = k / 6.0
            pts.append((x + lean * u * u, 8.0 + h * u))
        for k in range(6, -1, -1):
            u = k / 6.0
            pts.append((x + lean * u * u + th, 8.0 + h * u))
        s.append(poly(pts, _lerp(TIMBER, TIMBER_LIT if i < 3 else TIMBER_DARK, 0.46),
                      z=1 + i * 0.01))
    # A FRAGMENT OF THE SHEER, across the rib tips. Without it this piece read
    # as a palm frond for exactly the reason `hull` did -- see hull.half_w. Here
    # it is only a fragment, spanning three or four frames, because the piece is
    # a torn-out SECTION of a side rather than a standing wreck: a full
    # unbroken line would make it look salvageable.
    tips = []
    for i in range(1, 5):
        t = i / 5.0
        x = -44.0 + 84.0 * t
        hgt = 26.0 + math.sin(t * 2.6) * 34.0 + (_h(i, 53) - 0.5) * 12.0
        tips.append((x + (t - 0.45) * 26.0, 8.0 + hgt))
    s.append(poly(tips + [(p[0] + 3.0, p[1] + 7.0) for p in tips][::-1],
                  _lerp(TIMBER, TIMBER_LIT, 0.52), z=7))
    for i in range(3):
        x = -30.0 + i * 30.0
        s.append(poly([(x, 12.0), (x + 18.0, 10.0), (x + 15.0, 26.0), (x + 2.0, 28.0)],
                      _lerp(KELP, KELP_DARK, 0.4), z=8 + i * 0.1))
    _crust(s, -50.0, 46.0, 4.0, z=40, n=8)
    return s, (128, 78)


def mast():
    """A mast still standing, ~11m, one yard across it and the rigging gone slack.

    WHY THE YARD IS OFF-CENTRE AND THERE IS ONLY ONE. A vertical pole with
    evenly-spaced horizontal bars is a ladder, and a ladder with a wheel on top
    would be a gantry -- the exact misread the Fold's obelisk cost two passes to
    kill (style-contract §4.5). One yard, set high and hung off-centre, is
    unmistakably a spar. Two would start a rhythm.

    IT IS ALSO A HANDHOLD, and the echoes already made it one: "Little prints on
    the mast beside mine. He was still with me here. Still with me here." So
    there are three lashed rungs at the bottom, at a child's spacing -- the only
    thing in this kit that is scaled to Nari rather than to Mir.
    """
    s = []
    H = 330.0
    # tapered: a mast is a tree, thicker where it is stepped
    for i in range(12):
        y0, y1 = H * i / 12.0, H * (i + 1) / 12.0
        w0 = 9.0 - 4.6 * (y0 / H)
        w1 = 9.0 - 4.6 * (y1 / H)
        s.append(poly([(-w0, y0), (w0, y0), (w1, y1), (-w1, y1)], TIMBER, z=0))
        s.append(poly([(-w0, y0), (-w0 * 0.34, y0), (-w1 * 0.34, y1), (-w1, y1)],
                      _lerp(TIMBER, TIMBER_LIT, 0.5), z=0.5))

    # the yard: high, and hung crooked because one lift parted
    yy = H * 0.78
    s.append(poly([(-74.0, yy + 13.0), (66.0, yy - 5.0), (66.0, yy + 3.0), (-74.0, yy + 21.0)],
                  _lerp(TIMBER, TIMBER_DARK, 0.3), z=2))
    s.append(poly([(-74.0, yy + 13.0), (66.0, yy - 5.0), (66.0, yy - 2.0), (-74.0, yy + 16.0)],
                  _lerp(TIMBER, TIMBER_LIT, 0.42), z=2.1))
    # the parted lift, hanging
    for k in range(6):
        s.append(rect(60.0 - k * 1.2, yy - 6.0 - k * 9.0, 62.0 - k * 1.2, yy + 3.0 - k * 9.0,
                      ROPE, z=3))
    # slack rigging: catenaries, which is the whole reason rope reads as rope
    # A ROPE IS A LINE, NOT A ROW OF BEADS. These were eleven discrete blobs per
    # stay, and at ship size the gaps between them survived the downsample: both
    # stays came back as dotted strings and the mast read as a maypole with
    # bunting on it. Drawn as a continuous strip instead, so the catenary is a
    # curve rather than a rhythm.
    for ri, (x0, x1, sag) in enumerate(((-70.0, -6.0, 54.0), (62.0, 6.0, 40.0))):
        top, bot = [], []
        for k in range(15):
            u = k / 14.0
            x = x0 + (x1 - x0) * u
            y = yy + 14.0 - sag * math.sin(u * math.pi) - u * 30.0
            top.append((x, y + 1.7))
            bot.append((x, y - 1.7))
        s.append(poly(top + bot[::-1], ROPE, z=3.2 + ri * 0.1))

    # a child's rungs, low, lashed on. Spaced for a four-year-old.
    for k in range(3):
        y = 26.0 + k * 21.0
        s.append(rect(-16.0, y, 16.0, y + 3.4, TIMBER_DARK, z=4))
        s.append(blob(ROPE, 3.0, 2.2, off=(-13.0, y + 1.6), z=4.1))
        s.append(blob(ROPE, 3.0, 2.2, off=(13.0, y + 1.6), z=4.1))

    for i in range(5):
        y = 8.0 + _h(i, 61) * 90.0
        sx = 1.0 if _h(i, 67) > 0.5 else -1.0
        s.append(poly([(sx * 6.0, y), (sx * 22.0, y + 20.0 + _h(i, 71) * 18.0),
                       (sx * 5.0, y + 14.0 + _h(i, 73) * 20.0)],
                      _lerp(KELP, KELP_DARK, 0.45), z=5 + i * 0.01))
    s.append(blob(TIMBER_DARK, 30.0, 10.0, off=(0.0, 6.0), z=-1))
    _crust(s, -22.0, 22.0, 4.0, z=40, n=5)
    return s, (170, 356)


def headframe():
    """The mine's headframe, ~9m: two braced legs and a sheave wheel over a shaft.

    THE ONE PIECE THAT SAYS "SOMEBODY WORKED HERE ON PURPOSE." §6.2's mining
    town "dug into something and stayed", and a headframe is the only structure
    whose silhouette states its function outright -- a wheel on legs over a hole
    is a way DOWN, and this whole region is about the way up. That contradiction
    is why it belongs here and not in the Scar.

    IT IS NOT SYMMETRIC. A symmetric A-frame is a drawing of a headframe; a real
    one has the back leg raked much further than the front to take the hoist's
    pull, and this one has also lost a brace and settled. Symmetry is what made
    the first cut read as a swingset.
    """
    s = []
    H = 270.0
    # front leg: near-vertical. back leg: heavily raked, taking the pull.
    s.append(poly([(-14.0, 0.0), (-4.0, 0.0), (12.0, H), (2.0, H)], TIMBER, z=1))
    s.append(poly([(-14.0, 0.0), (-9.0, 0.0), (7.0, H), (2.0, H)],
                  _lerp(TIMBER, TIMBER_LIT, 0.48), z=1.1))
    s.append(poly([(72.0, 0.0), (86.0, 0.0), (26.0, H), (16.0, H)], TIMBER_DARK, z=0))
    s.append(poly([(72.0, 0.0), (78.0, 0.0), (20.0, H), (16.0, H)],
                  _lerp(TIMBER_DARK, TIMBER, 0.5), z=0.5))
    # cross-bracing: three, at UNEVEN heights, and the lowest one is gone --
    # only its two stubs remain, which is what says "this was maintained once".
    for k, f in enumerate((0.30, 0.58, 0.83)):
        y = H * f
        x0 = -9.0 + (14.0 + 9.0) * f
        x1 = 79.0 - (79.0 - 20.0) * f
        s.append(poly([(x0, y), (x1, y - 6.0), (x1, y + 2.0), (x0, y + 8.0)],
                      _lerp(TIMBER, TIMBER_DARK, 0.34), z=2 + k * 0.1))
    for x in (2.0, 62.0):                       # the missing brace's stubs
        s.append(rect(x, H * 0.13, x + 15.0, H * 0.13 + 6.0,
                      _lerp(TIMBER, TIMBER_DARK, 0.5), z=2))
    # THE SHEAVE WHEEL -- A RIM YOU CAN SEE THROUGH, NOT A DISC.
    #
    # The first cut filled the wheel solid: an IRON blob at R, a rust blob at
    # 0.80R on top of it, and six spokes in `_lerp(IRON, RUST, 0.28)` laid over
    # the rust. Three near-identical values stacked in that order means the
    # spokes are invisible and the wheel is a flat pale disc with a ring around
    # it -- which is a CLOCK FACE. In this game, of all games. Mir is a
    # clock-keeper; a stopped dial is loaded imagery that belongs to the Keep
    # and to the end of the story, and having one turn up by accident on a mine
    # in region 1 spends it for nothing.
    #
    # A wheel reads as a wheel because the ground shows through between the
    # spokes. So the interior is painted near-black (it is genuinely the shaded
    # inside of the housing) and the spokes are laid over it in the LIT iron --
    # five of them, not six, because an odd count cannot be mistaken for a
    # symmetric grille, and thick enough to survive the 0.5 downsample.
    wx, wy, R = 16.0, H + 6.0, 30.0
    s.append(blob(IRON, R, R * 0.96, off=(wx, wy), z=4))                  # rim
    s.append(blob((11, 14, 15), R * 0.82, R * 0.79, off=(wx - 1.0, wy + 1.0), z=4.1))
    s.append(blob(_lerp(IRON, RUST, 0.52), R * 0.94, R * 0.90, off=(wx - 1.5, wy + 1.5), z=3.9))
    for k in range(5):                          # spokes, uneven: two are bent
        a = math.pi * k / 5.0 + 0.22
        bend = 0.13 if k in (1, 4) else 0.0
        col = _lerp(IRON_LIT, SALT, 0.20) if k % 2 == 0 else _lerp(IRON, IRON_LIT, 0.62)
        ax, ay = math.cos(a) * R * 0.84, math.sin(a) * R * 0.84
        bx, by = math.cos(a + bend) * -R * 0.84, math.sin(a + bend) * -R * 0.84
        s.append(poly([(wx + ax, wy + ay), (wx + bx, wy + by),
                       (wx + bx + 3.6, wy + by + 2.4), (wx + ax + 3.6, wy + ay + 2.4)],
                      col, z=4.2))
    s.append(blob(_lerp(IRON, RUST, 0.62), R * 0.22, R * 0.22, off=(wx - 2.0, wy + 2.0), z=4.4))
    # the hoist rope, still reeved over the rim and running down the shaft.
    # A STRIP, not nine spaced blobs -- at ship size those read as a dotted
    # line, the same failure the mast's stays had.
    rope = [(wx + 26.0 + math.sin(k * 0.7) * 1.4, wy - 26.0 - k * 19.0) for k in range(11)]
    s.append(poly([(x - 1.8, y) for x, y in rope] + [(x + 1.8, y) for x, y in rope][::-1],
                  ROPE, z=3.4))
    # the collar of the shaft: a dark mouth at the foot. The way down.
    s.append(blob((10, 13, 14), 30.0, 8.0, off=(30.0, 7.0), z=-1))
    s.append(blob(TIMBER_DARK, 36.0, 10.0, off=(30.0, 4.0), z=-2))
    _crust(s, -18.0, 90.0, 3.0, z=40, n=9)
    return s, (200, 316)


def shack():
    """A mine shack, ~3.4m, roof caved in on the downhill side.

    A ROOF THAT HAS FAILED IS MORE INFORMATIVE THAN A ROOF. An intact hut says
    "building"; a hut whose ridge has broken and dropped on one side says
    nobody has been inside for a hundred years, which is the sentence the whole
    region is trying to say. It fails DOWNHILL, and the light comes from the
    upper left, so the surviving slope is the lit one -- that is the only reason
    the collapse reads as depth rather than as a smudge.
    """
    s = []
    s.append(rect(-52.0, 0.0, 52.0, 62.0, TIMBER, z=0))
    s.append(rect(-52.0, 0.0, -38.0, 62.0, _lerp(TIMBER, TIMBER_LIT, 0.5), z=0.5))
    s.append(rect(18.0, 0.0, 52.0, 62.0, _lerp(TIMBER, TIMBER_DARK, 0.42), z=0.5))
    # board seams, vertical, irregular -- planks are not a fence
    x = -48.0
    i = 0
    while x < 50.0:
        s.append(rect(x, 2.0, x + 1.6, 60.0, TIMBER_DARK, z=1))
        x += 8.0 + _h(i, 79) * 7.0
        i += 1
    # the doorway: black, and the darkest value in the piece
    s.append(rect(-16.0, 0.0, 8.0, 42.0, (9, 11, 12), z=2))
    s.append(rect(-18.0, 40.0, 10.0, 45.0, TIMBER_DARK, z=2.1))
    # the roof: one surviving slope, one collapsed
    s.append(poly([(-60.0, 60.0), (4.0, 60.0), (10.0, 92.0), (-58.0, 74.0)],
                  _lerp(TIMBER, TIMBER_LIT, 0.30), z=3))
    s.append(poly([(-58.0, 74.0), (10.0, 92.0), (14.0, 96.0), (-56.0, 78.0)],
                  _lerp(TIMBER_LIT, SALT, 0.34), z=3.2))     # the lit ridge edge
    s.append(poly([(4.0, 60.0), (60.0, 60.0), (56.0, 66.0), (12.0, 78.0)],
                  TIMBER_DARK, z=3.1))                        # the caved side
    for k in range(4):                                        # broken rafters
        xx = 14.0 + k * 11.0
        s.append(poly([(xx, 60.0), (xx + 3.0, 60.0), (xx + 9.0 - k * 2.0, 74.0 - k * 4.0),
                       (xx + 6.0 - k * 2.0, 74.0 - k * 4.0)],
                      _lerp(TIMBER, TIMBER_DARK, 0.2), z=3.3))
    _crust(s, -54.0, 54.0, 2.0, z=40, n=9)
    _crust(s, -58.0, 6.0, 62.0, z=41, n=5, scale=0.7)
    return s, (140, 108)


def ore_cart():
    """A tipped ore cart, ~1.4m, spilled where it stopped.

    TIPPED, NOT PARKED. An upright cart is equipment; a cart on its side with its
    load still lying in front of it is the moment work stopped, and that moment
    is what §6.2's town "stayed" through. The spill is the reason to tip it: the
    ore is what makes the shape legible at 20 pixels, because a small dark box is
    a small dark box and a small dark box with a fan of rubble pouring out of it
    is an accident.
    """
    s = []
    s.append(poly([(-26.0, 6.0), (16.0, 2.0), (22.0, 30.0), (-20.0, 34.0)], IRON, z=1))
    s.append(poly([(-26.0, 6.0), (16.0, 2.0), (15.0, 8.0), (-25.0, 12.0)],
                  _lerp(IRON, RUST, 0.5), z=1.2))
    s.append(poly([(-20.0, 34.0), (22.0, 30.0), (18.0, 24.0), (-17.0, 28.0)],
                  _lerp(IRON, IRON_LIT, 0.42), z=1.3))       # the lit upper lip
    s.append(poly([(-24.0, 10.0), (12.0, 6.0), (16.0, 26.0), (-19.0, 30.0)],
                  (12, 14, 15), z=1.4))                       # the empty inside
    for k in range(2):                                        # wheels, off the rail
        s.append(blob(_lerp(IRON, RUST, 0.34), 7.0, 7.0, off=(-8.0 + k * 22.0, 36.0 + k * 3.0), z=2))
        s.append(blob(IRON_LIT, 2.2, 2.2, off=(-9.0 + k * 22.0, 37.0 + k * 3.0), z=2.1))
    for i in range(11):                                       # the spill
        r = 2.4 + _h(i, 83) * 3.6
        s.append(blob(_lerp(IRON, (58, 52, 46), _h(i, 89)), r, r * 0.7,
                      off=(-34.0 - _h(i, 97) * 22.0, 4.0 + _h(i, 101) * 14.0), z=0))
    _crust(s, -24.0, 20.0, 3.0, z=40, n=5, scale=0.8)
    return s, (110, 56)


def rail_bend():
    """A short run of rail, ~0.5m tall, buckled up out of the silt.

    THE GROUND MOVED. Two straight rails would be infrastructure and would read
    as a tidy line, which is the last thing this region is. Buckled, they say
    something shifted under them after they were laid -- and that is the mine's
    whole story in one prop, given that §6.2's town "dug into something."
    Sleepers stay STRAIGHT while the rails bend: bending both would look like a
    drawing error rather than like steel losing an argument with the earth.
    """
    s = []
    for k in range(5):                                        # sleepers, straight
        x = -52.0 + k * 26.0
        s.append(poly([(x, 4.0), (x + 17.0, 2.0), (x + 17.0, 10.0), (x, 12.0)],
                      _lerp(TIMBER_DARK, TIMBER, 0.4), z=0))
    for side, y0 in ((0, 6.0), (1, 13.0)):                    # two rails, buckling
        pts_top, pts_bot = [], []
        for k in range(13):
            u = k / 12.0
            x = -56.0 + 112.0 * u
            lift = 16.0 * math.exp(-((u - 0.58) ** 2) / 0.018) + 4.0 * math.exp(-((u - 0.22) ** 2) / 0.02)
            y = y0 + lift * (1.0 - side * 0.25)
            pts_top.append((x, y + 3.0))
            pts_bot.append((x, y))
        s.append(poly(pts_top + pts_bot[::-1],
                      _lerp(IRON, RUST, 0.48 if side else 0.34), z=1 + side * 0.1))
        s.append(poly([(p[0], p[1] + 1.2) for p in pts_top] + pts_top[::-1],
                      _lerp(IRON_LIT, RUST, 0.30), z=1.2 + side * 0.1))
    _crust(s, -54.0, 54.0, 2.0, z=40, n=7, scale=0.7)
    return s, (128, 44)


def winch():
    """A hoist winch, ~1.4m, drum still wound, handle gone.

    THE ROPE IS STILL ON IT. That is the piece. A bare drum is scrap; a drum
    with rope still coiled on it was loaded when it was abandoned, and the coil
    is also what makes a cylinder read as a cylinder at this size -- concentric
    banding is depth information a flat disc cannot carry.
    """
    s = []
    s.append(poly([(-30.0, 0.0), (-20.0, 0.0), (-18.0, 34.0), (-28.0, 34.0)], TIMBER, z=0))
    s.append(poly([(24.0, 0.0), (34.0, 0.0), (30.0, 34.0), (20.0, 34.0)], TIMBER_DARK, z=0))
    s.append(rect(-26.0, 26.0, 30.0, 40.0, IRON, z=1))
    for k in range(7):                                        # the coil
        t = k / 6.0
        s.append(rect(-24.0 + t * 50.0, 27.0, -20.0 + t * 50.0, 39.0,
                      _lerp(ROPE, (52, 47, 36), (k % 2) * 0.5), z=1.1 + k * 0.01))
    s.append(rect(-26.0, 37.0, 30.0, 40.0, _lerp(IRON_LIT, ROPE, 0.4), z=1.6))
    s.append(blob(_lerp(IRON, RUST, 0.5), 8.0, 8.0, off=(-28.0, 33.0), z=2))
    s.append(blob(IRON_LIT, 2.4, 2.4, off=(-29.0, 34.0), z=2.1))
    s.append(rect(-27.0, 6.0, 31.0, 10.0, _lerp(TIMBER, TIMBER_DARK, 0.4), z=0.5))
    _crust(s, -28.0, 32.0, 2.0, z=40, n=5, scale=0.8)
    return s, (110, 56)


def kelp_stand():
    """A stand of kelp, ~2.8m, the region's vertical texture.

    THE ONLY PIECE HERE THAT IS ALIVE, and it is the region's name. Kelp grows
    as straps with gas bladders at intervals -- organic-regular again, so the
    bladders are jittered in both spacing and size, and the fronds lean to a
    COMMON CURRENT. That shared lean is the important part: a bundle of fronds
    each bending its own way is a bush, and this world has a current in it.

    AND IT IS DRIED, WHICH IS A VALUE PROBLEM BEFORE IT IS A COLOUR ONE. The
    first version came back from a real frame as the brightest LARGE shape in
    the region -- brighter than the timber, brighter than the salt road, second
    only to the miner's lamp, and about four tiles tall. Style contract §3 is
    explicit that the brightest thing in this world must be SMALL, and a
    four-tile plant lit like a highlight breaks it as plainly as anything can.
    Two compounding causes: the tones ran up to KELP_LIT, and the kit's cool
    rim light is itself green (`rim_col=(92, 168, 124)`), so every frond edge
    got a second helping of exactly the hue it already had.

    It is also just wrong for the place. This region has NO water tiles -- it is
    exposed seabed -- so this kelp has been out of the sea for as long as
    anything here has, and dried kelp is olive-brown and matte, not sea-green.
    So the range now tops out well below KELP_LIT and the gas bladders, which
    were the brightest pixels of all, are the dull amber of a bladder that has
    gone hard.
    """
    s = []
    for i in range(9):
        x0 = -26.0 + i * 6.4 + (_h(i, 103) - 0.5) * 5.0
        Hf = 52.0 + _h(i, 107) * 66.0
        lean = 16.0 + _h(i, 109) * 20.0            # all the same direction
        w = 2.6 + _h(i, 113) * 2.4
        pts_l, pts_r = [], []
        for k in range(9):
            u = k / 8.0
            x = x0 + lean * u * u
            y = 4.0 + Hf * u
            pts_l.append((x - w * (1.0 - u * 0.4), y))
            pts_r.append((x + w * (1.0 - u * 0.4), y))
        dark = _h(i, 127)
        # tops out at 0.44 of the way to KELP_LIT, not 0.75 -- see the docstring
        s.append(poly(pts_l + pts_r[::-1],
                      _lerp(KELP_DARK, _lerp(KELP, (58, 62, 40), 0.42), dark * 0.62),
                      z=i * 0.02))
        nb = 2 + int(_h(i, 131) * 3)
        for b in range(nb):
            u = 0.30 + b * (0.62 / max(1, nb)) + _h(i * 5 + b, 137) * 0.10
            r = 3.0 + _h(i * 5 + b, 139) * 2.2
            s.append(blob(_lerp(KELP, (96, 82, 46), 0.44), r, r * 1.25,
                          off=(x0 + lean * u * u + w * 1.2, 4.0 + Hf * u), z=i * 0.02 + 0.01))
    s.append(blob(KELP_DARK, 30.0, 8.0, off=(0.0, 4.0), z=-1))
    return s, (120, 140)


def plank_bridge():
    """Two planks lashed across a gap, ~0.5m, sagging in the middle.

    THIS PIECE IS THE REGION'S MECHANIC, DRAWN. §6.2: the boy "has to be carried
    over the bad gaps by a man with no business carrying anything anywhere", and
    the two near-drops are "both of them the player's own hands on the
    controller." A crossing you can see is a crossing you can dread.

    IT SAGS, AND ONE PLANK IS SHORTER THAN THE OTHER. A flat pair of boards is a
    floor. A sag says the span is too long for the timber, and a short plank that
    stops before the far side says somebody crossed this anyway.
    """
    s = []
    for pi, (w, short) in enumerate(((9.0, 0.0), (7.0, 16.0))):
        top, bot = [], []
        for k in range(13):
            u = k / 12.0
            x = -60.0 + (116.0 - short) * u
            y = 12.0 - 9.0 * math.sin(u * math.pi) + pi * 10.0
            top.append((x, y + w))
            bot.append((x, y))
        s.append(poly(top + bot[::-1], _lerp(TIMBER, TIMBER_DARK, 0.28 + pi * 0.2), z=pi))
        s.append(poly([(p[0], p[1] + 2.0) for p in top] + top[::-1],
                      _lerp(TIMBER, TIMBER_LIT, 0.44 - pi * 0.18), z=pi + 0.1))
    for x in (-54.0, 46.0):                                   # the lashings
        for k in range(3):
            s.append(rect(x + k * 4.0, 6.0, x + 2.4 + k * 4.0, 26.0, ROPE, z=3))
    _crust(s, -60.0, 56.0, 8.0, z=40, n=6, scale=0.6)
    return s, (140, 48)


def lantern():
    """A miner's safety lamp hung on a driven stake, ~2.2m.

    WHY THE KIT NEEDED ONE MORE PIECE. `OverworldScene` marks every region
    boundary with a GATE PROP -- a small object with a warm glow beside the road
    where one region hands off to the next -- and the table had no entry that
    resolved for this region, so the Shelf's gate was unlit. That matters more
    than a missing prop usually would: the gates are the only warm light between
    the Fold and the Keep, and the whole shape of the climb is that Mir walks
    away from the last warm thing he will ever stand in.

    IT IS A SAFETY LAMP, NOT A LANTERN ON A POLE. The distinction is the gauze
    cylinder: a flame inside wire mesh, which is what you carry into a working
    face because a bare flame in bad air kills everybody. So the lamp says
    "people worked here and knew the air was wrong", which is the region in one
    object -- a town "that dug into something and stayed" (world-bible §6.2).

    AND IT IS STILL LIT. Nothing in this world decays (§2: "Nothing in the Fold
    grows... Rope does not fray"), so a lamp left burning is still burning, and
    the fact that it has been burning alone for longer than anyone can remember
    is the sad part. It is not a checkpoint. It is somebody's lamp.
    """
    s = []
    # the stake: driven at an angle, because a plumb post reads as installed
    s.append(poly([(-3.0, 0.0), (3.0, 0.0), (7.0, 52.0), (1.0, 52.0)], TIMBER, z=0))
    s.append(poly([(1.0, 0.0), (3.0, 0.0), (7.0, 52.0), (5.0, 52.0)],
                  _lerp(TIMBER, TIMBER_LIT, 0.5), z=0.1))
    _crust(s, -9.0, 9.0, 2.0, z=40, n=4, scale=0.5)
    # the hook and the bail
    s.append(poly([(4.0, 50.0), (16.0, 54.0), (16.0, 50.0), (4.0, 46.0)], IRON, z=1))
    s.append(poly([(11.0, 50.0), (13.0, 50.0), (13.0, 40.0), (11.0, 40.0)], IRON, z=1))
    # THE GAUZE. Vertical bars with the flame behind them, so the light comes
    # through in slats. A solid body would hide the only warm note in the piece.
    s.append(blob((255, 226, 158), 6.2, 8.4, off=(12.0, 30.0), z=1.5, glow=1.0))
    s.append(blob((255, 250, 226), 2.8, 4.0, off=(12.0, 30.5), z=1.6, glow=1.0))
    for dx in (6.6, 10.0, 13.4, 16.8):
        s.append(rect(dx, 21.0, dx + 1.5, 39.0, IRON, z=2))
    s.append(rect(5.4, 38.0, 18.6, 41.0, _lerp(IRON, RUST, 0.34), z=2.2))   # top ring
    s.append(rect(5.4, 19.0, 18.6, 22.0, _lerp(IRON, RUST, 0.34), z=2.2))   # base ring
    s.append(poly([(5.4, 41.0), (12.0, 47.0), (18.6, 41.0)], IRON, z=2.4))  # bonnet
    # the oil vessel below the gauze -- brass, and the only curve on the piece
    s.append(blob(_lerp(RUST, SALT, 0.30), 6.8, 5.0, off=(12.0, 16.0), z=2.3))
    s.append(blob(_lerp(SALT, (255, 236, 190), 0.34), 2.6, 1.5, off=(10.0, 18.0), z=2.5))
    return s, (64, 72)


# AUTHORED AT 2x AND DOWNSAMPLED -- because the camera is eleven tiles tall.
#
# `worldScaleFor()` floors the world scale at 0.5 (WorldScale.ts), so a piece's
# shipped HEIGHT IN TILES is set by its source canvas and nothing else: declaring
# fewer metres cannot shrink it. The tall pieces were authored at ~30 px/metre so
# the scale would land exactly on 0.5, and in-game that made the hull 226 world
# px -- FOURTEEN TILES -- in a viewport that shows eleven. The first real frame
# of the region was a corridor of grey slabs with no prow visible in it, which
# loses the one line the whole region is built on ("Every ship that ever sank
# points the same way. Up."). If the point is off-screen there is no ship.
#
# So the four tall pieces render at the size they were drawn and are then halved
# on the way out. That is not a compromise: rendering large and downsampling IS
# supersampling, so these four come out CLEANER than the pieces that ship at 1:1.
SHRINK = {"hull": 2.0, "mast": 2.0, "headframe": 1.7, "hull_broken": 1.6}

PIECES = {
    "hull": hull,
    "hull_broken": hull_broken,
    "ribs": ribs,
    "mast": mast,
    "headframe": headframe,
    "shack": shack,
    "ore_cart": ore_cart,
    "rail_bend": rail_bend,
    "winch": winch,
    "kelp_stand": kelp_stand,
    "plank_bridge": plank_bridge,
    "lantern": lantern,
}


def build(name):
    shapes, size = PIECES[name]()
    # The kit's rim is the Shelf's own accent, so the whole region reads as one
    # place -- the Fold's kit uses its teal for exactly the same reason, and a
    # piece carrying the wrong region's rim is the fastest way to make two
    # regions look like one.
    painter = Painter(size, rim_col=(92, 168, 124))
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
        k = SHRINK.get(name)
        if k:
            img = img.resize((max(1, int(round(img.width / k))),
                              max(1, int(round(img.height / k)))), Image.LANCZOS)
        img.save(OUT / ("%s.png" % name))
        print("%-13s %5.2fs  %dx%d" % (name, time.time() - t, img.width, img.height))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
