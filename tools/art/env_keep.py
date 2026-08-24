#!/usr/bin/env python3
"""The Keep's environment kit -- a drowned concert hall (world-bible §6.5).

    "A drowned concert hall, taken and repurposed. Lunal did not fight anyone
     for it; she arrived first and found it empty, which is why she chose it.
     The hall's own dead are dressing, not characters -- an orchestra that
     drowned mid-performance, stands and chairs and stopped clocks. Beautiful,
     and nobody's story."

FOUR RULES GOVERN EVERY PIECE IN HERE, AND THREE OF THEM ARE ABOUT RESTRAINT.

1. THIS IS THE ONLY REGION BUILT BY PEOPLE WITH MONEY, AND THAT IS THE TRAP.
   Read the kits in order: the Fold is planks and net; the Shelf is wreck; the
   Breach is canvas, rope and cheap paint; the Scar is char, dirt and iron. The
   player has spent four regions in places made by people with nothing. Then
   they walk into mahogany, brass, gilt and velvet. §6.5's room works -- "warm,
   lit, stocked, comfortable" -- only if the hall around it has already taught
   them that this is where nice things live. So every piece here is FINER than
   anything they have seen, and the finish is the point, not the decoration.

2. NOTHING HERE WAS BROKEN BY FORCE. The temptation with "drowned
   mid-performance" is chaos: overturned chairs, a smashed instrument, sheet
   music blown everywhere. Draw that and the orchestra becomes CHARACTERS -- a
   scramble, a panic, a story with people in it -- and §6.5 is explicit that
   they are "dressing, not characters. Beautiful, and NOBODY'S story." The water
   came from below and it came slowly. So: instruments still on their stands.
   Chairs pushed back, not knocked over. One chair pushed back further than the
   others, and that is the entire amount of narrative this hall is allowed.
   Composure is more devastating than wreckage, and it is also honest: a hall
   full of violence would be a hall that mattered to somebody.

3. THE WARMTH IS IN THE MATERIALS, NOT IN THE LIGHT. §3 still holds -- the
   brightest thing must be small -- and the Keep is the last region, so the
   warm room in §7 has to be a STEP UP from the hall, not a repeat of it. The
   hall's lamps are out. Its mahogany, brass and velvet carry the temperature
   on their own, and the only emissive piece in the kit is `candelabra`, which
   `GATE_PROPS` puts at the region boundary: the light Mir walks toward.

4. THE CLOCKS ALL READ THE SAME TIME, AND MIR IS A CLOCK-KEEPER.
   That is his trade -- a sedentary one, which is why the climb has cost him so
   much. He is the one person in the world who cannot walk past a stopped clock,
   and this hall has several, and every one of them stopped at the same minute
   because they all stopped for the same reason. Nobody else in the game would
   notice. He notices immediately, and there is nothing he can do about any of
   it. The kit does not comment on this; it just makes sure the hands agree.

   A CONSEQUENCE FOR PLACEMENT: `stopped_clock` MUST NEVER BE FLIPPED. A mirror
   reverses the hands, and two clocks in one camera reading different times
   destroys the only thing this piece is for. `place_keep.py` enforces it.

AUTHORING: 32 px per intended tile, so `metres == tiles` in
`src/scenes/env/WorldScale.ts` lands on the 0.5 world-scale floor exactly (see
env_scar.py's header for the arithmetic). Every piece needs an EXACT-KEY entry
in that table, above the loose legacy patterns.

VERIFY IN THE BROWSER (`tools/capture.mjs`), NEVER ON A CONTACT SHEET. This kit
is warm and the region grade is warm; a contact sheet on neutral grey will not
tell you whether the hall has gone orange.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rig import Blob, Joint, Painter, Poly, Skeleton  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "env" / "keep"

# Keep materials. Where the Scar's range was dark and NARROW, this one is dark
# and WIDE: a concert hall is built out of deliberately contrasting materials
# (wood against brass against cloth against stone) because that is what money
# buys. The values stay low -- it is still a hundred metres under -- but the
# hues are the most separated in the game.
MAHOG = (58, 34, 26)          # the hall's wood: everything structural
MAHOG_LIT = (108, 62, 42)
MAHOG_DARK = (32, 19, 15)
BRASS = (146, 108, 52)        # fittings, stands, pipes
BRASS_LIT = (208, 166, 90)
BRASS_DARK = (78, 58, 28)
# The timpani bowl is COPPER, not brass, and a century of standing water leaves
# copper green. It is the one cool warm-metal in the kit -- which is exactly why
# the drum reads as a different material from the organ rank two screens away
# instead of as more of the same yellow.
PATINA = (58, 84, 66)
GILT = (196, 158, 84)         # ornament, and ONLY ornament: never a large field
VELVET = (74, 26, 30)         # the seats. A large field, so authored dark.
VELVET_LIT = (118, 44, 44)
VELVET_DARK = (42, 15, 19)
SILT = (74, 68, 56)           # a century of it, over every horizontal surface
SILT_LIT = (108, 100, 82)
SILT_DARK = (46, 42, 34)
MARBLE = (138, 132, 118)      # the floor and the columns
MARBLE_LIT = (176, 170, 152)
MARBLE_DARK = (86, 82, 74)
PAGE = (162, 156, 136)        # sheet music, waterlogged and gone soft
PAGE_DARK = (104, 100, 86)
GUT = (172, 164, 132)         # strings, and they are still strung
IRONWORK = (40, 38, 36)       # the hall's hidden metal: brackets, frames, wire
GLASS = (118, 144, 146)       # chandelier lustres, clock crystal
GLASS_LIT = (192, 216, 214)
CLOCKFACE = (196, 188, 164)   # the one pale disc in the kit that carries meaning
HAND = (24, 20, 18)
CANDLE = (255, 208, 132)      # emissive, and only on `candelabra`
CANDLE_HOT = (255, 246, 220)

# THE TIME. Every clock in this hall reads it, and the number itself is not
# meaningful to anybody but Mir -- what is meaningful is that they AGREE. Stored
# as hand angles in radians, measured clockwise from twelve, so a piece cannot
# accidentally draw a different time by rounding.
CLOCK_HOUR_A = math.radians(30 * 4 + 0.5 * 51)   # a little past four
CLOCK_MIN_A = math.radians(6 * 51)               # fifty-one minutes


def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _root():
    return Skeleton([Joint("root", None, (0.0, 0.0), 0.0, 0.0)])


HALL_RIM = 0.24


def rect(x0, y0, x1, y1, col, z=0, glow=0.0, rim=HALL_RIM):
    return Poly("root", col, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z=z, glow=glow, rim=rim)


def poly(pts, col, z=0, glow=0.0, rim=HALL_RIM):
    return Poly("root", col, pts, z=z, glow=glow, rim=rim)


def blob(col, rx, ry, off, z=0, glow=0.0, rim=HALL_RIM):
    return Blob("root", col, rx, ry, off=off, z=z, glow=glow, rim=rim)


def _h(i, salt=0):
    """Deterministic pseudo-random in [0,1). NO RNG ANYWHERE IN THIS PIPELINE --
    every rebuild must be byte-identical or the palette gate and the plate check
    cannot tell a real regression from noise."""
    x = (i * 2654435761 + salt * 40503 + 12345) & 0xFFFFFFFF
    x ^= (x >> 13)
    x = (x * 1274126177) & 0xFFFFFFFF
    return ((x >> 8) & 0xFFFF) / 65536.0


def _silt(s, x0, x1, y, z=0, n=9, thick=1.0):
    """THE ONE MATERIAL EVERY PIECE IN THIS KIT SHARES.

    A century of settled silt banked against the foot of everything, and it is
    doing three jobs at once. It softens the contact so nothing reads as a decal
    (the Fold's kit learned that). It says "a hundred years" without a caption.
    And it is the only DULL thing in a kit made of polished surfaces, which is
    what keeps the brass and the gilt from reading as a jewellery shop -- the
    finish has to be visibly buried before it reads as abandoned finish.
    """
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
        if _h(i, 347) < 0.22:
            continue
        t = (i + 0.5) / n + (_h(i, 349) - 0.5) * 1.6 / n
        px = x0 + (x1 - x0) * t
        r = ((x1 - x0) / n) * (0.42 + _h(i, 313) ** 2 * 1.5)
        hh = (1.8 + _h(i, 317) ** 2 * 5.0) * thick
        s.append(blob(_lerp(SILT_DARK, SILT, 0.20 + _h(i, 331) * 0.55),
                      r, hh, off=(px, y + hh * 0.35), z=z + i * 0.01))


def _candle(s, x, y, z=6, r=2.6):
    """One candle flame. Layered because `rig.Painter` blurs an emissive shape
    by `9 * SS * glow` -- glow=1.0 on a small blob spreads its whole energy over
    a thirty-six-pixel radius and vanishes, which is how the Breach's festoon
    bulbs shipped as grey beadwork. Dark ember wash, tight envelope, opaque core.
    """
    s.append(blob(_lerp(CANDLE, (62, 30, 8), 0.64), r * 2.5, r * 3.2,
                  off=(x, y), z=z - 0.1, glow=1.0, rim=0.0))
    s.append(blob(_lerp(CANDLE, BRASS, 0.18), r * 1.2, r * 1.7,
                  off=(x, y), z=z, glow=0.24, rim=0.0))
    s.append(blob(CANDLE_HOT, r * 0.42, r * 0.78, off=(x, y + r * 0.3), z=z + 0.1,
                  glow=0.10, rim=0.0))


def _flute(s, cx, y0, y1, hw, col_dark, col_lit, z=0, n=5):
    """A run of vertical flutes -- the column and the organ both need them, and
    both need them IRREGULAR. Evenly-spaced parallel verticals are the strongest
    machine signal there is (§4.5 of the style contract: a centred column of
    dashes became a ladder), and a fluted column is genuinely regular, so the
    irregularity has to come from the LIGHT rather than the spacing: each flute
    gets its own value off a hash, so the run reads as turned stone catching a
    dim room instead of as a barcode.
    """
    for i in range(n):
        t = (i + 0.5) / n
        x = cx + (t - 0.5) * hw * 1.72
        w = hw * 1.72 / n * 0.34
        s.append(poly([(x - w, y0), (x + w, y0), (x + w, y1), (x - w, y1)],
                      _lerp(col_dark, col_lit, 0.10 + _h(i, 337) * 0.62), z=z))


def _clock_hands(s, cx, cy, r, z):
    """The hands, at the one time this hall knows. See rule 4 in the header."""
    for ang, ln, wid, tag in ((CLOCK_HOUR_A, r * 0.52, 1.9, 0), (CLOCK_MIN_A, r * 0.84, 1.3, 1)):
        dx, dy = math.sin(ang), math.cos(ang)
        px, py = -dy, dx
        s.append(poly([(cx + px * wid, cy + py * wid),
                       (cx - px * wid, cy - py * wid),
                       (cx + dx * ln - px * wid * 0.4, cy + dy * ln - py * wid * 0.4),
                       (cx + dx * ln + px * wid * 0.4, cy + dy * ln + py * wid * 0.4)],
                      HAND, z=z + tag * 0.02, rim=0.0))
    s.append(blob(_lerp(HAND, BRASS_DARK, 0.4), 1.9, 1.9, off=(cx, cy), z=z + 0.05, rim=0.0))


# ---------------------------------------------------------------------------
def proscenium():
    """The hall's proscenium arch, ~6.0 tiles. THE LANDMARK.

    The one piece in the kit tall enough to say "concert hall" from off-screen,
    and the only piece in the game where a BUILT silhouette is the correct
    answer. Everywhere else in this world a clean arc reads as manufactured and
    therefore wrong (the Shelf's hull, the Scar's cairn, four goes at the burnt
    spar); here the thing genuinely was manufactured, by people who were paid to
    make it beautiful, and reading as such is the whole job.

    AND IT TOOK FOUR GOES, BECAUSE I KEPT TRYING TO DRAW A FRAGMENT. The idea was
    good -- a complete arch is a doorway, and a doorway is somewhere you go,
    whereas half an arch is a ruin you stand under -- and it does not survive
    contact with a silhouette. Every version of half an arch on one pier came
    back as the same object: a crane, a boom, a level-crossing barrier, a street
    lamp, a shepherd's crook, a faucet. The reason is structural and it is worth
    writing down, because it generalises:

        AN ARCH IS TWO SPRINGINGS. That is what the eye reads -- not the curve,
        the PAIR. One springing and a curve leaving it is a cantilever, and a
        cantilever is machinery. No amount of thickening, gilding, breaking or
        reparameterising turns one springing into an arch, because the missing
        information is not in the curve.

    So the arch is COMPLETE, on two piers, and the ruin is everywhere else: the
    entablature above it is snapped off in a ragged diagonal, the gilt survives
    only in patches, the left capital has lost a corner, and a century of silt is
    banked against both feet. Which is also more truthful about this world --
    §6.5's hall was not smashed, it was ABANDONED, and abandoned buildings keep
    their arches and lose their roofs.
    """
    s = []
    W, H = 240, 192
    R, SPY, TH = 48.0, 84.0, 22.0        # radius, springing height, band depth
    for side, px, cap_chip in ((-1.0, -72.0, True), (1.0, 72.0, False)):
        # the pier: a blocky wall-like mass, NOT a column (`pillar` is a column
        # and lives in this same kit -- three shallow panels, not seven flutes)
        s.append(poly([(px - 24.0, 0.0), (px + 24.0, 0.0), (px + 22.0, SPY), (px - 22.0, SPY)],
                      _lerp(MARBLE, MARBLE_DARK, 0.40 + side * 0.06), z=0))
        _flute(s, px, 12.0, SPY - 8.0, 20.0, _lerp(MARBLE_DARK, MAHOG_DARK, 0.10),
               _lerp(MARBLE, MARBLE_LIT, 0.10 + side * 0.08), z=0.3, n=3)
        s.append(poly([(px - 29.0, 0.0), (px + 29.0, 0.0), (px + 26.0, 9.0), (px - 26.0, 9.0)],
                      _lerp(MARBLE, MARBLE_LIT, 0.26), z=0.6))
        # the impost: the block an arch actually springs off
        s.append(poly([(px - 27.0, SPY - 11.0), (px + 27.0, SPY - 11.0),
                       (px + 25.0, SPY), (px - 25.0, SPY)],
                      _lerp(MARBLE, MARBLE_LIT, 0.18), z=0.9))
        s.append(poly([(px - 27.0, SPY - 4.0), (px + 27.0, SPY - 4.0),
                       (px + 27.0, SPY - 2.0), (px - 27.0, SPY - 2.0)],
                      _lerp(MARBLE_DARK, MARBLE, 0.16), z=0.92))
        if cap_chip:
            # ONE corner gone. A complete pair of imposts is a rendering.
            s.append(poly([(px - 27.0, SPY - 11.0), (px - 14.0, SPY), (px - 27.0, SPY)],
                          _lerp(MARBLE_DARK, SILT_DARK, 0.36), z=1.0))
    # THE ARCH, semicircular, springing off both imposts. Its centre is the
    # midpoint of the span at impost level, so at a = 0 and a = pi it lands
    # exactly on the two blocks and cannot float.
    outer, inner = [], []
    for i in range(33):
        a = math.pi * (i / 32.0)
        cx, cy = -math.cos(a) * R, SPY + math.sin(a) * R
        outer.append((cx * (1.0 + TH / R), SPY + (cy - SPY) * (1.0 + TH / R)))
        inner.append((cx, cy))
    s.append(poly(outer + inner[::-1], _lerp(MARBLE, MARBLE_DARK, 0.26), z=1.2))
    s.append(poly(outer + [(x * 0.94, SPY + (y - SPY) * 0.94) for x, y in outer][::-1],
                  _lerp(MARBLE, MARBLE_LIT, 0.24), z=1.25))
    # the soffit, in shadow -- the underside is what gives an arch its depth
    s.append(poly(inner + [(x * 1.09, SPY + (y - SPY) * 1.09) for x, y in inner][::-1],
                  _lerp(MARBLE_DARK, MAHOG_DARK, 0.28), z=1.3))
    # the keystone, wider than the band and projecting above it
    s.append(poly([(-9.0, SPY + R - 4.0), (9.0, SPY + R - 4.0),
                   (7.0, SPY + R + TH + 7.0), (-7.0, SPY + R + TH + 7.0)],
                  _lerp(MARBLE, MARBLE_LIT, 0.30), z=1.5))
    s.append(blob(_lerp(GILT, BRASS_DARK, 0.34), 4.4, 5.0, off=(0.0, SPY + R + 8.0), z=1.55))
    # GILT ON THE ARCHIVOLT, in fragments. Ornament is never a continuous line --
    # the water took the gesso and left the metal, in patches, unevenly.
    for i in range(23):
        if _h(i, 401) < 0.40:
            continue
        a = math.pi * (i / 22.0)
        rr = 2.8 + _h(i, 403) * 2.4
        s.append(blob(_lerp(GILT, BRASS_DARK, _h(i, 407) * 0.55), rr, rr * 1.3,
                      off=(-math.cos(a) * (R + TH * 0.5), SPY + math.sin(a) * (R + TH * 0.5)),
                      z=1.6))
    # THE ENTABLATURE ABOVE, SNAPPED OFF IN A DIAGONAL. This is where all the
    # ruin lives now, and it is the only ragged line on the piece.
    s.append(poly([(-96.0, SPY + 6.0), (-96.0, SPY + 34.0), (-58.0, SPY + 40.0),
                   (-26.0, SPY + 52.0), (-6.0, SPY + 46.0), (14.0, SPY + 58.0),
                   (44.0, SPY + 43.0), (72.0, SPY + 47.0), (96.0, SPY + 30.0),
                   (96.0, SPY + 6.0)],
                  _lerp(MARBLE, MARBLE_DARK, 0.34), z=0.4))
    s.append(poly([(-96.0, SPY + 6.0), (96.0, SPY + 6.0), (96.0, SPY + 13.0), (-96.0, SPY + 13.0)],
                  _lerp(MARBLE, MARBLE_LIT, 0.22), z=0.45))
    s.append(poly([(-96.0, SPY + 11.0), (96.0, SPY + 11.0), (96.0, SPY + 13.5), (-96.0, SPY + 13.5)],
                  _lerp(GILT, BRASS_DARK, 0.46), z=0.5))
    # the broken top edge, catching the light along the fracture
    for i, (x0, y0, x1, y1) in enumerate(((-96.0, SPY + 34.0, -58.0, SPY + 40.0),
                                          (-58.0, SPY + 40.0, -26.0, SPY + 52.0),
                                          (-26.0, SPY + 52.0, -6.0, SPY + 46.0),
                                          (-6.0, SPY + 46.0, 14.0, SPY + 58.0),
                                          (14.0, SPY + 58.0, 44.0, SPY + 43.0),
                                          (44.0, SPY + 43.0, 72.0, SPY + 47.0),
                                          (72.0, SPY + 47.0, 96.0, SPY + 30.0))):
        s.append(poly([(x0, y0), (x1, y1), (x1, y1 - 3.4), (x0, y0 - 3.4)],
                      _lerp(MARBLE_LIT, SILT, 0.20 + _h(i, 409) * 0.34), z=0.5))
    # rubble at both feet, and MORE of it under the deeper break on the left
    for i in range(11):
        rr = 3.0 + _h(i, 411) * 5.4
        bx = -104.0 + i * 19.0 + (_h(i, 413) - 0.5) * 9.0
        s.append(blob(_lerp(MARBLE_DARK, SILT_DARK, 0.20 + _h(i, 417) * 0.5),
                      rr, rr * 0.60, off=(bx, rr * 0.5 + _h(i, 419) * 2.6), z=2.0))
    _silt(s, -108.0, -34.0, 0.0, z=3.0, n=9, thick=1.25)
    _silt(s, 34.0, 108.0, 0.0, z=3.0, n=8, thick=1.05)
    return s, (W, H)

def organ_pipes():
    """A rank of the hall's organ, ~5.5 tiles.

    THE ONE PLACE IN THIS GAME WHERE MONOTONIC IS CORRECT. The style contract
    forbids monotonic shrinking because it reads as manufactured -- and this is
    manufactured, and a graded run of lengths is the single unambiguous signal
    for "organ". Take it away and the piece is a fence.

    But a pure ramp reads as a BAR CHART, or a xylophone, and the contract names
    xylophone as an already-shipped failure (one vertical strap per crate, in the
    Fold's kit). So the rank is mitred: it climbs, then DROPS to a second shorter
    run, which is how real ranks are laid out when the case is not tall enough --
    and the break is the detail that says "instrument" rather than "graph". Two
    pipes are missing, and the dark slots where they were do more for the read
    than any amount of surface polish.

    The MOUTHS matter. A pipe is a tube with a slot cut in its front near the
    foot; without them these are dowels. They are also the only place on the
    piece where the eye finds a hard dark accent, so they carry the rhythm.
    """
    s = []
    W, H = 160, 176
    # the case: mahogany, with a moulded cornice and a plinth
    s.append(poly([(-72.0, 0.0), (72.0, 0.0), (69.0, 158.0), (-69.0, 158.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.42), z=0))
    s.append(poly([(-72.0, 0.0), (72.0, 0.0), (72.0, 14.0), (-72.0, 14.0)],
                  _lerp(MAHOG, MAHOG_LIT, 0.24), z=0.2))
    s.append(poly([(-76.0, 148.0), (76.0, 148.0), (72.0, 164.0), (-72.0, 164.0)],
                  _lerp(MAHOG, MAHOG_LIT, 0.30), z=0.2))
    s.append(poly([(-76.0, 158.0), (76.0, 158.0), (76.0, 161.0), (-76.0, 161.0)],
                  _lerp(GILT, BRASS_DARK, 0.44), z=0.3))
    # the rank: eleven pipes, climbing then MITRED down to a second run
    # AND THE MITRE MADE A HISTOGRAM. Two monotonic runs side by side is a bar
    # chart with a gap in it -- I traded one machine signal for a worse one. Real
    # ranks are laid out in a MITRE or a V precisely so no two neighbours differ
    # by the same step: the longest pipes go to the OUTSIDE and the short ones to
    # the middle, which is also structurally why organ cases are shaped that way.
    # The run below rises, dips to a short middle, and rises again, so the eye
    # reads a symmetrical instrument instead of a graph -- and the two missing
    # pipes fall on opposite sides of the dip so the symmetry is never exact.
    HEIGHTS = (138.0, 118.0, 96.0, 74.0, 62.0, 78.0, 102.0, 124.0, 142.0)
    MISSING = (2, 7)
    for i, top in enumerate(HEIGHTS):
        x = -60.0 + i * 15.2
        hw = 6.2 - abs(i - 4) * 0.16
        if i in MISSING:
            # the slot where a pipe used to be: the case's dark interior
            s.append(poly([(x - hw, 16.0), (x + hw, 16.0), (x + hw, 16.0 + top * 0.86),
                           (x - hw, 16.0 + top * 0.86)], _lerp(MAHOG_DARK, (14, 10, 9), 0.55), z=0.8))
            continue
        # the body, with a lit edge on one side only -- a tube, not a slab
        s.append(poly([(x - hw, 14.0), (x + hw, 14.0), (x + hw, 14.0 + top), (x - hw, 14.0 + top)],
                      _lerp(BRASS_DARK, BRASS, 0.24 + _h(i, 421) * 0.30), z=1.0 + i * 0.01))
        s.append(poly([(x - hw, 14.0), (x - hw * 0.32, 14.0),
                       (x - hw * 0.32, 14.0 + top), (x - hw, 14.0 + top)],
                      _lerp(BRASS, BRASS_LIT, 0.28 + _h(i, 423) * 0.34), z=1.1 + i * 0.01))
        # the crown: a plain flat cap, slightly wider than the tube
        s.append(poly([(x - hw * 1.25, 14.0 + top), (x + hw * 1.25, 14.0 + top),
                       (x + hw * 1.1, 18.0 + top), (x - hw * 1.1, 18.0 + top)],
                      _lerp(BRASS, BRASS_LIT, 0.42), z=1.3))
        # THE MOUTH: the slot near the foot. Without this they are dowels.
        s.append(poly([(x - hw * 0.62, 26.0), (x + hw * 0.62, 26.0),
                       (x + hw * 0.5, 34.0), (x - hw * 0.5, 34.0)],
                      _lerp(MAHOG_DARK, (12, 9, 8), 0.5), z=1.4))
        s.append(poly([(x - hw * 0.62, 34.0), (x + hw * 0.62, 34.0),
                       (x + hw * 0.62, 36.0), (x - hw * 0.62, 36.0)],
                      _lerp(BRASS_LIT, PAGE, 0.20), z=1.45))
        # silt has settled in every upward-facing crown -- a hundred years of it
        s.append(blob(_lerp(SILT_DARK, SILT, 0.4), hw * 1.05, 1.4,
                      off=(x, 17.0 + top), z=1.5))
    _silt(s, -80.0, 80.0, 0.0, z=3.0, n=10, thick=1.05)
    return s, (W, H)


# ---------------------------------------------------------------------------
def pillar():
    """A hall column, ~5.0 tiles. The piece that makes a space feel expensive.

    Fluted marble, an entasis swell (columns are not cylinders -- the swell is
    why a real one looks alive and a drawn one usually does not), a capital with
    a corner knocked off, and silt banked a third of the way up one side because
    the water had a direction and it kept it for a century.

    THE FLUTES DO NOT VARY IN SPACING. On a fluted column they genuinely are
    evenly spaced, so the anti-machine rule (§4.5: break a repeat on two axes)
    is satisfied through VALUE instead of geometry -- see `_flute`. This is the
    one exception in the game and it is only safe because the object is
    architectural: the eye already expects order from a column, and disordering
    the flutes would read as damage rather than as craft.
    """
    s = []
    W, H = 96, 160
    def hw(y):
        """Entasis: the shaft swells about a third of the way up, then tapers."""
        t = max(0.0, min(1.0, (y - 12.0) / 116.0))
        return 20.0 * (1.0 + 0.075 * math.sin(t * math.pi * 0.92) - t * 0.13)

    shaft_l, shaft_r = [], []
    for i in range(15):
        y = 12.0 + 116.0 * (i / 14.0)
        shaft_l.append((-hw(y), y))
        shaft_r.append((hw(y), y))
    s.append(poly(shaft_r + shaft_l[::-1], _lerp(MARBLE, MARBLE_DARK, 0.38), z=0))
    _flute(s, 0.0, 14.0, 126.0, 19.0, _lerp(MARBLE_DARK, MAHOG_DARK, 0.18), MARBLE_LIT, z=0.3, n=7)
    # the base: two tori and a plinth
    s.append(poly([(-26.0, 0.0), (26.0, 0.0), (24.0, 7.0), (-24.0, 7.0)],
                  _lerp(MARBLE, MARBLE_LIT, 0.26), z=0.6))
    s.append(blob(_lerp(MARBLE, MARBLE_LIT, 0.34), 24.0, 4.0, off=(0.0, 9.0), z=0.7))
    s.append(blob(_lerp(MARBLE, MARBLE_DARK, 0.16), 21.0, 3.0, off=(0.0, 13.5), z=0.8))
    # the capital, WITH A CORNER GONE. A complete capital is a rendering; a
    # capital missing its left volute is a hall that has been under water.
    s.append(poly([(-21.0, 126.0), (21.0, 126.0), (26.0, 138.0), (-26.0, 138.0)],
                  _lerp(MARBLE, MARBLE_DARK, 0.22), z=1.0))
    s.append(poly([(-28.0, 138.0), (28.0, 138.0), (26.0, 150.0),
                   (6.0, 150.0), (-4.0, 145.0), (-26.0, 147.0)],
                  _lerp(MARBLE, MARBLE_LIT, 0.20), z=1.1))
    s.append(poly([(-4.0, 145.0), (6.0, 150.0), (-2.0, 150.0), (-8.0, 146.0)],
                  _lerp(MARBLE_DARK, SILT_DARK, 0.34), z=1.2))
    s.append(blob(_lerp(GILT, BRASS_DARK, 0.5), 8.0, 4.0, off=(13.0, 143.0), z=1.3))
    # a hairline crack, running down from the damaged corner and NOT to the base
    ck = [(-6.0, 140.0), (-9.0, 118.0), (-5.0, 96.0), (-11.0, 74.0), (-7.0, 58.0)]
    s.append(poly([(x - 1.0, y) for x, y in ck] + [(x + 1.0, y) for x, y in ck][::-1],
                  _lerp(MARBLE_DARK, MAHOG_DARK, 0.40), z=1.6))
    # SILT BANKED ON ONE SIDE ONLY. The water had a direction.
    _silt(s, -34.0, 6.0, 0.0, z=2.0, n=7, thick=1.9)
    _silt(s, 4.0, 32.0, 0.0, z=2.0, n=5, thick=0.8)
    return s, (W, H)


# ---------------------------------------------------------------------------
def hall_door():
    """A tall panelled double door, one leaf standing open, ~4.0 tiles.

    §6.5: Lunal "arrived first and found it empty, which is why she chose it."
    An OPEN door is the whole sentence. Nobody forced it, nobody barred it, and
    it has been standing open long enough for the silt to bank against the leaf
    -- so the piece has to be composed so the silt line runs THROUGH the opening
    and up the inside face of the open leaf. A door that opened recently has
    clean floor behind it.

    The closed leaf carries the joinery: six raised-and-fielded panels, a brass
    escutcheon, a lock that was never turned. The open leaf is shown edge-on and
    dark, which is also what keeps the piece from reading as a symmetrical arch.
    """
    s = []
    W, H = 96, 128
    # the case: jamb, jamb, lintel
    s.append(poly([(-46.0, 0.0), (-32.0, 0.0), (-32.0, 116.0), (-46.0, 116.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.30), z=0))
    s.append(poly([(34.0, 0.0), (46.0, 0.0), (46.0, 116.0), (34.0, 116.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.40), z=0))
    s.append(poly([(-48.0, 112.0), (48.0, 112.0), (46.0, 124.0), (-46.0, 124.0)],
                  _lerp(MAHOG, MAHOG_LIT, 0.22), z=0.1))
    s.append(poly([(-48.0, 120.0), (48.0, 120.0), (48.0, 122.5), (-48.0, 122.5)],
                  _lerp(GILT, BRASS_DARK, 0.5), z=0.2))
    # the dark of the room beyond, AND IT HAS TO BE ACTUALLY DARK. The first cut
    # mixed it 62% toward near-black off MAHOG_DARK, which lands at lum 20 -- and
    # 20 next to a leaf at 34 is not a hole, it is a slightly darker plank. So
    # the whole piece read as a CLOSED door with stripes down one half, i.e. a
    # wardrobe. The opening is 8 now, which is the darkest value in the game, and
    # `rim=0` so the silhouette light does not climb into it and fill it back in.
    s.append(poly([(-32.0, 0.0), (34.0, 0.0), (34.0, 112.0), (-32.0, 112.0)],
                  (8, 7, 8), z=0.5, rim=0.0))
    # THE CLOSED LEAF, with the joinery on it
    s.append(poly([(-30.0, 2.0), (2.0, 2.0), (2.0, 110.0), (-30.0, 110.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.16), z=1.0))
    for k, (y0, y1) in enumerate(((8.0, 38.0), (44.0, 72.0), (78.0, 104.0))):
        for j, (x0, x1) in enumerate(((-26.0, -16.0), (-12.0, -2.0))):
            s.append(poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                          _lerp(MAHOG_DARK, MAHOG, 0.30 + _h(k * 2 + j, 431) * 0.26), z=1.1))
            s.append(poly([(x0, y1 - 2.0), (x1, y1 - 2.0), (x1 - 1.2, y1), (x0 + 1.2, y1)],
                          _lerp(MAHOG, MAHOG_LIT, 0.34), z=1.2))
    s.append(blob(_lerp(BRASS, BRASS_LIT, 0.34), 3.0, 5.0, off=(-1.0, 58.0), z=1.4))
    s.append(blob(_lerp(BRASS_DARK, (14, 11, 10), 0.5), 1.0, 1.8, off=(-1.0, 57.0), z=1.5))
    # THE OPEN LEAF, SWUNG OUT TOWARD THE VIEWER. Edge-on was the mistake: a
    # 15px vertical strip beside a 32px one reads as two panels of the same door,
    # and the panel lines on it read as LOUVRES. Swung out it is a TRAPEZOID --
    # wider at the bottom than the top, because it is nearer the camera down
    # there -- and a trapezoid is a plane at an angle, which is the one shape
    # that cannot be mistaken for part of a flat facade.
    LEAF = [(16.0, 3.0), (40.0, -1.0), (37.0, 106.0), (16.0, 107.0)]
    s.append(poly(LEAF, _lerp(MAHOG, MAHOG_DARK, 0.06), z=1.6))
    s.append(poly([(16.0, 3.0), (20.0, 2.4), (20.0, 107.0), (16.0, 107.0)],
                  _lerp(MAHOG, MAHOG_LIT, 0.34), z=1.7))     # the hinge stile, lit
    s.append(poly([(37.0, 106.0), (40.0, -1.0), (36.0, 0.0), (34.0, 105.0)],
                  _lerp(MAHOG_DARK, (14, 11, 11), 0.30), z=1.72))  # its dark edge
    for k, (y0, y1) in enumerate(((10.0, 40.0), (48.0, 76.0), (82.0, 102.0))):
        t0, t1 = y0 / 107.0, y1 / 107.0
        xa0, xa1 = 22.0 + 15.0 * (1.0 - t0), 22.0 + 15.0 * (1.0 - t1)
        s.append(poly([(22.0, y0), (xa0, y0 - 1.0), (xa1, y1 - 1.0), (22.0, y1)],
                      _lerp(MAHOG_DARK, MAHOG, 0.34 + _h(k, 433) * 0.22), z=1.75))
    # the silt runs THROUGH the opening and banks against the inside of the leaf
    _silt(s, -30.0, 30.0, 0.0, z=2.4, n=9, thick=1.25)
    _silt(s, 14.0, 42.0, 1.0, z=2.6, n=5, thick=1.55)
    return s, (W, H)


# ---------------------------------------------------------------------------
def stopped_clock():
    """A longcase clock, ~3.0 tiles. AND MIR IS A CLOCK-KEEPER.

    THE MOST IMPORTANT SMALL OBJECT IN THE GAME. His trade is clocks -- a
    sedentary trade, which is exactly why the climb has cost him what it has --
    and this hall is full of them, and every one reads the same minute, because
    they all stopped for the same reason. He is the only person in the world who
    would notice that at a glance. The game does not tell the player any of
    this. The hands just agree, and if the player has been paying attention to
    who he is, they will find out that they noticed too.

    NEVER FLIP THIS PIECE. A mirror reverses the hands. Two clocks in one camera
    reading different times destroys the only thing the piece exists for, so
    `place_keep.py` refuses to flip it -- see the header, rule 4.

    THE PENDULUM HANGS DEAD CENTRE, and that is the composition. A pendulum
    drawn to one side implies the next swing; a pendulum plumb in the middle of
    its glazed door is a thing that has stopped, and it is the difference between
    a clock that is slow and a clock that is finished. It is also the only
    perfectly vertical line in the kit, which is why the eye lands on it.
    """
    s = []
    W, H = 64, 96
    # the plinth
    s.append(poly([(-20.0, 0.0), (20.0, 0.0), (17.0, 12.0), (-17.0, 12.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.34), z=0))
    s.append(poly([(-20.0, 9.0), (20.0, 9.0), (20.0, 11.5), (-20.0, 11.5)],
                  _lerp(MAHOG, MAHOG_LIT, 0.26), z=0.1))
    # the trunk
    s.append(poly([(-15.0, 11.0), (15.0, 11.0), (14.0, 64.0), (-14.0, 64.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.22), z=0.4))
    s.append(poly([(-15.0, 11.0), (-9.0, 11.0), (-8.5, 64.0), (-14.0, 64.0)],
                  _lerp(MAHOG, MAHOG_LIT, 0.22), z=0.45))
    # the glazed trunk door, and the dead pendulum behind it
    s.append(poly([(-9.5, 18.0), (9.5, 18.0), (9.0, 58.0), (-9.0, 58.0)],
                  _lerp(MAHOG_DARK, (12, 11, 12), 0.5), z=0.6, rim=0.0))
    s.append(poly([(-1.1, 22.0), (1.1, 22.0), (1.1, 30.0), (-1.1, 30.0)],
                  _lerp(BRASS_DARK, BRASS, 0.28), z=0.8, rim=0.0))
    s.append(blob(_lerp(BRASS, BRASS_LIT, 0.22), 5.2, 5.2, off=(0.0, 25.0), z=0.85, rim=0.0))
    s.append(blob(_lerp(BRASS_LIT, PAGE, 0.30), 2.0, 2.0, off=(-1.4, 26.4), z=0.9, rim=0.0))
    # the glass: two faint diagonal lights, and one of them is cracked
    for k, (gx0, gy0, gx1, gy1) in enumerate(((-8.0, 52.0, -2.0, 34.0), (2.0, 56.0, 7.0, 44.0))):
        s.append(poly([(gx0, gy0), (gx0 + 1.6, gy0), (gx1 + 1.6, gy1), (gx1, gy1)],
                      _lerp(GLASS, GLASS_LIT, 0.18 - k * 0.08), z=1.0, rim=0.0))
    s.append(poly([(-9.0, 44.0), (-3.0, 38.0), (-2.2, 39.0), (-8.2, 45.0)],
                  _lerp(GLASS_LIT, PAGE, 0.30), z=1.05, rim=0.0))
    # the hood: waist moulding, then the case, then a BROKEN swan-neck pediment
    s.append(poly([(-18.0, 62.0), (18.0, 62.0), (17.0, 68.0), (-17.0, 68.0)],
                  _lerp(MAHOG, MAHOG_LIT, 0.28), z=1.2))
    s.append(poly([(-17.0, 67.0), (17.0, 67.0), (16.0, 86.0), (-16.0, 86.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.14), z=1.3))
    for d in (-1.0, 1.0):
        s.append(poly([(d * 2.0, 86.0), (d * 16.0, 86.0), (d * 15.0, 90.0 + d * 1.5),
                       (d * 7.0, 93.0), (d * 3.0, 90.0)],
                      _lerp(MAHOG, MAHOG_LIT, 0.20 if d > 0 else 0.08), z=1.4))
    s.append(blob(_lerp(GILT, BRASS_DARK, 0.36), 2.6, 3.4, off=(0.0, 90.0), z=1.5))
    # THE FACE. The one pale disc in the kit that means something.
    s.append(blob(_lerp(BRASS_DARK, BRASS, 0.30), 13.4, 13.4, off=(0.0, 77.0), z=1.6))
    s.append(blob(CLOCKFACE, 11.6, 11.6, off=(0.0, 77.0), z=1.7))
    s.append(blob(_lerp(CLOCKFACE, SILT, 0.30), 11.6, 4.4, off=(0.0, 71.0), z=1.75))
    for i in range(12):
        a = math.pi * 2.0 * (i / 12.0)
        mr = 9.4
        w = 1.5 if i % 3 == 0 else 0.9
        s.append(blob(_lerp(HAND, BRASS_DARK, 0.24), w, w * 1.3,
                      off=(math.sin(a) * mr, 77.0 + math.cos(a) * mr), z=1.8, rim=0.0))
    _clock_hands(s, 0.0, 77.0, 11.6, z=1.9)
    _silt(s, -26.0, 26.0, 0.0, z=2.4, n=7, thick=1.1)
    return s, (W, H)


# ---------------------------------------------------------------------------
def seat_bank():
    """A bank of stall seating, ~6.0 tiles. THE HALL'S AUDIENCE, AND IT IS EMPTY.

    The piece that does the most work for the least drawing, because a row of
    seats is the only object that states an AUDIENCE, and the audience is the
    thing this hall is missing. A ruined stage says "nobody plays here"; a ruined
    row of seats says "nobody listened", which is worse and is the sentence §6.5
    wants under Lunal's hall.

    SEVEN SEATS AND THEY MUST NOT BE SEVEN OF THE SAME SEAT. §4.5 wants a repeat
    broken on two axes, and the axes here are FOLD and VALUE: the tip-up seats
    are folded closed except two, which sit down; and every velvet panel takes a
    different lightness, because a hundred years of a window somewhere lit one
    end of the row more than the other. The geometry stays regular -- seating is
    bolted to a floor and a wobbly row reads as damage, which is the wrong
    story. Nothing here was broken by force (header, rule 2).

    ONE PANEL IS WORN THROUGH to the horsehair. It is the only place in the kit
    where a material's INSIDE is visible, and it is what makes the velvet read
    as cloth instead of as paint.
    """
    s = []
    W, H = 192, 90
    # the floor plinth the standards bolt into, and it is not level any more
    s.append(poly([(-92.0, 0.0), (92.0, 0.0), (90.0, 11.0), (-90.0, 13.0)],
                  _lerp(MARBLE_DARK, SILT_DARK, 0.36), z=0))
    N = 7
    for i in range(N):
        x = -78.0 + i * 26.0
        lv = 0.10 + _h(i, 501) * 0.44          # the axis that is NOT geometry
        down = i in (2, 5)
        # the cast-iron standard: a scrolled bracket, dark, and the only cool
        # neutral on the piece -- it is what keeps seven warm panels from
        # blending into one long smear
        s.append(poly([(x - 13.0, 9.0), (x - 9.0, 9.0), (x - 8.0, 44.0), (x - 12.0, 44.0)],
                      _lerp(IRONWORK, MAHOG_DARK, 0.24), z=0.6))
        s.append(poly([(x - 13.0, 40.0), (x - 4.0, 46.0), (x - 6.0, 49.0), (x - 13.0, 44.0)],
                      _lerp(IRONWORK, BRASS_DARK, 0.30), z=0.7))
        # the seat: folded up (a narrow vertical panel) or down (a horizontal one)
        if down:
            s.append(poly([(x - 11.0, 30.0), (x + 11.0, 30.0), (x + 12.0, 38.0), (x - 12.0, 38.0)],
                          _lerp(VELVET, VELVET_LIT, lv), z=1.0))
            s.append(poly([(x - 12.0, 36.0), (x + 12.0, 36.0), (x + 12.0, 38.5), (x - 12.0, 38.5)],
                          _lerp(VELVET_DARK, VELVET, 0.30), z=1.05))
        else:
            s.append(poly([(x - 10.0, 30.0), (x + 10.0, 30.0), (x + 9.0, 56.0), (x - 9.0, 56.0)],
                          _lerp(VELVET, VELVET_LIT, lv * 0.7), z=1.0))
            s.append(poly([(x - 10.0, 52.0), (x + 10.0, 52.0), (x + 9.0, 56.0), (x - 9.0, 56.0)],
                          _lerp(VELVET_LIT, PAGE, 0.16), z=1.05))
        # the back, always up, with a gilt frame line along its top rail
        s.append(poly([(x - 11.5, 42.0), (x + 11.5, 42.0), (x + 10.5, 74.0), (x - 10.5, 74.0)],
                      _lerp(VELVET, VELVET_DARK, 0.34 - lv * 0.4), z=0.8))
        s.append(poly([(x - 12.0, 72.0), (x + 12.0, 72.0), (x + 11.0, 76.0), (x - 11.0, 76.0)],
                      _lerp(MAHOG, MAHOG_LIT, 0.18 + lv * 0.3), z=0.9))
        s.append(poly([(x - 12.0, 74.5), (x + 12.0, 74.5), (x + 12.0, 76.0), (x - 12.0, 76.0)],
                      _lerp(GILT, BRASS_DARK, 0.40 + _h(i, 503) * 0.34), z=0.95))
        # THE WORN PANEL. One only, and its inside is showing.
        if i == 4:
            s.append(poly([(x - 6.0, 50.0), (x + 4.0, 53.0), (x + 6.0, 64.0),
                           (x - 3.0, 67.0), (x - 8.0, 60.0)],
                          _lerp(GUT, SILT, 0.42), z=1.2))
            s.append(poly([(x - 6.0, 50.0), (x + 4.0, 53.0), (x + 1.0, 56.0), (x - 5.0, 54.0)],
                          _lerp(VELVET_DARK, (18, 8, 10), 0.30), z=1.25))
        # a seat number on the standard: brass, tiny, unreadable, and it is the
        # detail that says somebody had a TICKET
        s.append(blob(_lerp(BRASS, BRASS_LIT, 0.30 + _h(i, 507) * 0.4), 2.2, 1.6,
                      off=(x - 10.5, 24.0), z=1.4))
    _silt(s, -94.0, 94.0, 2.0, z=2.4, n=13, thick=1.35)
    return s, (W, H)


# ---------------------------------------------------------------------------
def chair_row():
    """Four orchestra chairs, ~4.0 tiles. AND ONE OF THEM IS PUSHED BACK.

    THIS IS THE ENTIRE AMOUNT OF NARRATIVE THIS HALL IS ALLOWED, and it is spent
    here, once, on one chair. §6.5 is explicit that the orchestra are "dressing,
    not characters. Beautiful, and NOBODY'S story." Overturn the chairs and they
    become characters -- people who fled, and then the player is owed an account
    of what happened to them, and the hall stops being the quiet expensive room
    that makes §7's warm room land. So three chairs sit square to their stands
    the way a player left mid-rehearsal, and the fourth is turned out and pushed
    back a foot, which is what a chair looks like when somebody stood up.

    Nothing else. No instrument on the floor, no scattered pages under it, no
    dropped bow. One chair, at an angle. If the player feels something, it is
    because they did the work, and a feeling the player assembled themselves is
    the only kind that lands.
    """
    s = []
    W, H = 128, 52
    def one(x, turn, back):
        """turn: 0 square to the stage, 1 turned out. back: how far it slid."""
        z0 = 1.0 - x / 4000.0
        w = 11.0 - turn * 4.0                      # foreshortened when turned
        sk = turn * 5.0                            # the seat becomes a rhombus
        y = 2.0 + back * 0.0
        s.append(poly([(x - w, y + 15.0), (x + w, y + 15.0),
                       (x + w + sk, y + 21.0), (x - w + sk, y + 21.0)],
                      _lerp(MAHOG, MAHOG_LIT, 0.12), z=z0 + 0.4))
        s.append(poly([(x - w + sk, y + 19.5), (x + w + sk, y + 19.5),
                       (x + w + sk, y + 21.5), (x - w + sk, y + 21.5)],
                      _lerp(MAHOG_DARK, MAHOG, 0.24), z=z0 + 0.45))
        # four legs, and the two far ones are darker: that is the whole trick
        for lx, lz, ld in ((-w + 1.5, z0 + 0.1, 0.42), (w - 1.5, z0 + 0.1, 0.42),
                           (-w + 3.0 + sk, z0 + 0.5, 0.06), (w - 3.0 + sk, z0 + 0.5, 0.06)):
            s.append(poly([(x + lx - 1.4, y), (x + lx + 1.4, y),
                           (x + lx + 1.2, y + 16.0), (x + lx - 1.2, y + 16.0)],
                          _lerp(MAHOG, MAHOG_DARK, ld), z=lz))
        # the back: two stiles and a curved crest rail
        for d in (-1.0, 1.0):
            s.append(poly([(x + d * (w - 2.0) - 1.3, y + 19.0), (x + d * (w - 2.0) + 1.3, y + 19.0),
                           (x + d * (w - 3.0) + 1.3, y + 40.0), (x + d * (w - 3.0) - 1.3, y + 40.0)],
                          _lerp(MAHOG, MAHOG_LIT, 0.10 + turn * 0.10), z=z0 + 0.6))
        crest = []
        for i in range(9):
            t = i / 8.0
            crest.append((x - (w - 3.0) + 2.0 * (w - 3.0) * t,
                          y + 40.0 + math.sin(t * math.pi) * 3.4))
        s.append(poly(crest + [(px, py - 6.0) for px, py in crest][::-1],
                      _lerp(MAHOG, MAHOG_LIT, 0.22), z=z0 + 0.7))
        # THE SEAT PAD IS THE WHOLE READ AT WORLD SCALE. These render at 1.6
        # tiles and halve on the way out, so a 4px dark-red strip becomes 2px of
        # nothing and the chair collapses to a wire hoop -- which is what four of
        # them in a row looked like in the browser: croquet. The pad is taller
        # and much lighter now, with a dark shadow line under its front edge,
        # because at this size the eye needs a VALUE BLOCK to sit on, not a hue.
        s.append(poly([(x - w + 1.0, y + 14.0), (x + w - 1.0, y + 14.0),
                       (x + w - 1.0 + sk, y + 21.0), (x - w + 1.0 + sk, y + 21.0)],
                      _lerp(VELVET_LIT, GILT, 0.16), z=z0 + 0.8))
        s.append(poly([(x - w + 1.0 + sk, y + 13.0), (x + w - 1.0 + sk, y + 13.0),
                       (x + w - 1.0 + sk, y + 15.0), (x - w + 1.0 + sk, y + 15.0)],
                      _lerp(VELVET_DARK, MAHOG_DARK, 0.30), z=z0 + 0.82))
    one(-46.0, 0, 0.0)
    one(-16.0, 0, 0.0)
    one(14.0, 0, 0.0)
    one(48.0, 1, 1.0)     # THE ONE. Turned out, and pushed back.
    _silt(s, -62.0, 62.0, 0.0, z=2.4, n=9, thick=0.85)
    return s, (W, H)


# ---------------------------------------------------------------------------
def chair():
    """One orchestra chair, ~1.4 tiles. The scatter piece.

    `chair_row` is the composed statement; this is the one you put alone in a
    corridor, on a landing, or three of at odd angles in the foyer, and it is
    deliberately the plainest thing in the kit. A single chair is also the
    smallest object in the game that implies a PERSON-SIZED body, which is why
    one of them at the far end of an empty hall reads louder than a landmark.
    """
    s = []
    W, H = 46, 46
    for lx, ld, lz in ((-8.0, 0.44, 0.1), (8.0, 0.44, 0.1), (-5.0, 0.08, 0.5), (11.0, 0.08, 0.5)):
        s.append(poly([(lx - 1.5, 0.0), (lx + 1.5, 0.0), (lx + 1.3, 17.0), (lx - 1.3, 17.0)],
                      _lerp(MAHOG, MAHOG_DARK, ld), z=lz))
    s.append(poly([(-10.0, 16.0), (10.0, 16.0), (13.0, 22.0), (-7.0, 22.0)],
                  _lerp(MAHOG, MAHOG_LIT, 0.14), z=0.9))
    s.append(poly([(-9.0, 15.0), (9.0, 15.0), (12.0, 22.0), (-6.0, 22.0)],
                  _lerp(VELVET_LIT, GILT, 0.16), z=1.0))
    s.append(poly([(-9.0, 14.0), (9.0, 14.0), (9.0, 16.0), (-9.0, 16.0)],
                  _lerp(VELVET_DARK, MAHOG_DARK, 0.30), z=1.02))
    for d in (-1.0, 1.0):
        s.append(poly([(d * 8.0 - 1.3, 20.0), (d * 8.0 + 1.3, 20.0),
                       (d * 7.0 + 1.3, 38.0), (d * 7.0 - 1.3, 38.0)],
                      _lerp(MAHOG, MAHOG_LIT, 0.10), z=1.1))
    crest = [(-7.0 + 14.0 * (i / 8.0), 38.0 + math.sin((i / 8.0) * math.pi) * 3.0) for i in range(9)]
    s.append(poly(crest + [(px, py - 5.6) for px, py in crest][::-1],
                  _lerp(MAHOG, MAHOG_LIT, 0.20), z=1.2))
    _silt(s, -14.0, 16.0, 0.0, z=2.0, n=5, thick=0.8)
    return s, (W, H)


# ---------------------------------------------------------------------------
def music_stand():
    """A desk stand with the part still on it, ~2.0 tiles. THE HALL'S SENTENCE.

    §6.5's hall is "the orchestra still on their stands", and the music is the
    half of that phrase that matters. An empty stand is furniture. A stand with a
    part open on it is a person who was reading it four bars ago, and the pages
    are the brightest value in the whole kit, which puts the eye exactly where
    the story is.

    THE PAGES ARE NOT PARALLEL. Two leaves at slightly different angles, and a
    third that has slipped its clip and hangs down over the desk lip -- because a
    flat rectangle on a flat rectangle is a poster, and one curled corner is
    paper. The desk is TILTED (that is what a music desk is), and the tilt is
    what stops the tripod below it from reading as a figure with a placard.
    """
    s = []
    W, H = 52, 64
    # the tripod: three legs, and they are NOT evenly splayed -- one is kicked
    for lx, ly, lw, lz in ((-15.0, 2.0, 2.0, 0.2), (13.0, 1.0, 2.2, 0.2), (2.0, 3.0, 1.6, 0.6)):
        s.append(poly([(lx, ly), (lx + lw * 1.6, ly), (1.6, 20.0), (-1.6, 20.0)],
                      _lerp(IRONWORK, MAHOG_DARK, 0.26 + _h(int(lx), 511) * 0.2), z=lz))
        s.append(blob(_lerp(IRONWORK, BRASS_DARK, 0.34), lw * 1.5, 1.2, off=(lx + lw * 0.8, ly + 0.8), z=lz + 0.05))
    # the stem and its collar
    s.append(poly([(-1.7, 18.0), (1.7, 18.0), (1.5, 40.0), (-1.5, 40.0)],
                  _lerp(IRONWORK, BRASS_DARK, 0.22), z=0.8))
    s.append(blob(_lerp(BRASS, BRASS_LIT, 0.24), 3.2, 2.0, off=(0.0, 30.0), z=0.9))
    # THE DESK, tilted, with a lip along the bottom
    desk = [(-19.0, 38.0), (18.0, 42.0), (20.0, 58.0), (-17.0, 54.0)]
    s.append(poly(desk, _lerp(IRONWORK, MAHOG, 0.30), z=1.0))
    s.append(poly([(-19.0, 38.0), (18.0, 42.0), (18.0, 45.0), (-19.0, 41.0)],
                  _lerp(BRASS_DARK, BRASS, 0.30), z=1.05))
    # the part: two leaves at DIFFERENT angles, and one that has slipped
    s.append(poly([(-16.0, 41.0), (1.0, 43.0), (2.0, 57.0), (-15.0, 55.0)],
                  _lerp(PAGE, PAGE_DARK, 0.22), z=1.2))
    s.append(poly([(0.0, 42.5), (17.0, 45.5), (18.0, 58.0), (1.0, 55.5)],
                  PAGE, z=1.25))
    for i in range(6):                             # staff lines, faint, unequal
        yy = 47.0 + i * 1.9
        s.append(poly([(2.0, yy), (16.0, yy + 1.4), (16.0, yy + 1.9), (2.0, yy + 0.5)],
                      _lerp(PAGE_DARK, IRONWORK, 0.20 + _h(i, 513) * 0.24), z=1.3))
    s.append(poly([(6.0, 43.0), (16.0, 44.6), (15.0, 34.0), (8.0, 33.0), (5.0, 38.0)],
                  _lerp(PAGE, PAGE_DARK, 0.34), z=1.4))    # THE SLIPPED LEAF
    s.append(poly([(15.0, 34.0), (16.0, 44.6), (13.0, 43.0), (12.5, 34.4)],
                  _lerp(PAGE_DARK, SILT_DARK, 0.30), z=1.45))  # its shaded curl
    _silt(s, -20.0, 20.0, 0.0, z=2.2, n=6, thick=0.8)
    return s, (W, H)


# ---------------------------------------------------------------------------
def podium():
    """The conductor's riser, ~2.2 tiles. AND IT IS A BOX. THAT IS THE POINT.

    Two cuts of this had a brass rail on it and both of them read as a HANDBAG,
    then as a clothes iron: a bar arching over a box closes into one outline, and
    the eye takes the whole silhouette as a single object with a handle. Moving
    the rail off-centre helped and did not fix it, because the problem was never
    the placement -- it was that a rail is the biggest shape on a piece this
    small, and the biggest shape decides what the object IS.

    So there is no rail. A conductor's riser is a low box, and the thing worth
    drawing was never the box: it is the RUBBED PATCH on top, where a pair of
    feet stood for however many hundred nights it takes to wear the polish off
    mahogany, and a matching darker band along the front edge where the toes went
    over. Wear is the only way an object can say "used, repeatedly, by one
    person" without saying one word about the person -- and §6.5 will not let this
    hall say anything about the person. Two dull patches on a polished surface,
    and the player knows somebody stood here every night for years, and the game
    never mentions it. That is the whole piece and it did not need a rail.

    NO BATON ON THE FLOOR EITHER. The one narrative beat this hall gets is the
    pushed-back chair in `chair_row`, and a dropped baton would spend it twice.
    """
    s = []
    W, H = 72, 26
    # the lower step, and it is not quite square to the upper one
    s.append(poly([(-34.0, 0.0), (32.0, 0.0), (30.0, 6.0), (-32.0, 7.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.34), z=0))
    s.append(poly([(-32.0, 5.0), (30.0, 4.5), (30.0, 7.0), (-32.0, 7.5)],
                  _lerp(MAHOG, MAHOG_LIT, 0.20), z=0.1))
    # the platform: a wide shallow box, and its front face takes most of the frame
    s.append(poly([(-29.0, 5.5), (27.0, 5.0), (25.0, 15.0), (-27.0, 16.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.14), z=0.4))
    # THE TOE BAND: darker, along the front edge, where a shoe went over it
    s.append(poly([(-19.0, 13.6), (14.0, 13.0), (14.0, 16.2), (-19.0, 16.8)],
                  _lerp(MAHOG_DARK, SILT_DARK, 0.26), z=0.5, rim=0.0))
    # the top surface, seen at a very low angle
    s.append(poly([(-27.0, 15.0), (25.0, 14.0), (28.0, 21.0), (-30.0, 22.0)],
                  _lerp(MAHOG, MAHOG_LIT, 0.32), z=0.6))
    s.append(poly([(-27.0, 15.0), (25.0, 14.0), (25.0, 15.6), (-27.0, 16.6)],
                  _lerp(MAHOG_LIT, GILT, 0.20), z=0.65))    # the polished nosing
    # THE RUBBED PATCH: two dull ovals, not one, because there were two feet, and
    # they are not the same size because nobody stands evenly for thirty years
    for fx, fr in ((-9.0, 7.6), (5.0, 6.2)):
        s.append(blob(_lerp(MAHOG_LIT, SILT, 0.46), fr, 2.8, off=(fx, 19.0), z=0.8, rim=0.0))
        s.append(blob(_lerp(MAHOG_LIT, SILT_LIT, 0.34), fr * 0.58, 1.5, off=(fx, 19.4), z=0.82, rim=0.0))
    # one brass tack per corner, holding a carpet that is long gone
    for tx in (-25.0, 23.0):
        s.append(blob(_lerp(BRASS, BRASS_LIT, 0.24), 1.4, 1.0, off=(tx, 17.5), z=0.9))
    _silt(s, -36.0, 34.0, 0.0, z=2.0, n=7, thick=0.9)
    return s, (W, H)


# ---------------------------------------------------------------------------
def harp():
    """A concert harp, ~3.2 tiles. THE MOST EXPENSIVE OBJECT IN THE GAME.

    §6.5's hall has to teach the player that this is where nice things live, and
    a harp does it in one silhouette: a triangle of gilt and gut, the only object
    in five regions that is obviously worth more than a house. It is also the one
    shape here nothing else resembles, which is why it goes near the road.

    THE STRINGS ARE THE PIECE, AND THEY ARE A TRAP. Thirty-odd evenly spaced
    parallel lines is the exact machine signal §4.5 forbids -- it is the crate
    strap, the organ rank, the xylophone, again. But a harp's strings genuinely
    are evenly spaced, so the disorder has to come from somewhere else: FOUR OF
    THEM ARE BROKEN, and a broken gut string does not vanish, it CURLS. Four
    curls at four different heights, and the regular thirty behind them read as
    craft instead of as a fence.

    NOTHING KNOCKED IT OVER (header, rule 2). It stands on its foot exactly where
    the player left it, and the silt has banked against that foot for a century.
    """
    s = []
    W, H = 70, 102
    # the column: the front post, straight, gilt, with a capital
    s.append(poly([(-26.0, 6.0), (-19.0, 6.0), (-16.0, 82.0), (-23.0, 84.0)],
                  _lerp(GILT, BRASS_DARK, 0.30), z=1.0))
    s.append(poly([(-26.0, 6.0), (-23.0, 6.0), (-21.0, 83.0), (-24.0, 84.0)],
                  _lerp(GILT, BRASS_LIT, 0.34), z=1.05))
    for i in range(5):
        s.append(blob(_lerp(BRASS_DARK, GILT, 0.16), 3.4, 0.7, off=(-21.5, 20.0 + i * 13.0), z=1.1))
    # the neck: the curved top, sweeping right off the column's capital
    neck_o, neck_i = [], []
    for i in range(13):
        t = i / 12.0
        a = math.pi * (0.86 - 0.44 * t)
        neck_o.append((-21.0 + math.cos(a) * -30.0 * t + 30.0 * t,
                       84.0 + math.sin(a) * 10.0 * t + t * 4.0))
        neck_i.append((-21.0 + math.cos(a) * -30.0 * t + 30.0 * t,
                       78.0 + math.sin(a) * 8.0 * t + t * 3.0))
    s.append(poly(neck_o + neck_i[::-1], _lerp(GILT, BRASS_DARK, 0.22), z=1.4))
    s.append(poly(neck_o + [(px, py - 1.8) for px, py in neck_o][::-1],
                  _lerp(GILT, BRASS_LIT, 0.40), z=1.45))
    # the soundbox: a long tapered body leaning back, soundboard lit, belly dark
    box_f = [(24.0, 2.0), (30.0, 6.0), (34.0, 40.0), (32.0, 78.0), (26.0, 88.0)]
    box_b = [(24.0, 2.0), (14.0, 8.0), (10.0, 42.0), (12.0, 76.0), (18.0, 86.0)]
    s.append(poly(box_f + box_b[::-1], _lerp(MAHOG, MAHOG_DARK, 0.30), z=0.8))
    s.append(poly(box_b + [(px - 4.0, py) for px, py in box_b][::-1],
                  _lerp(MAHOG, MAHOG_LIT, 0.26), z=0.85))
    s.append(poly([(24.0, 4.0), (28.0, 8.0), (30.0, 44.0), (24.0, 44.0)],
                  _lerp(MAHOG_DARK, GILT, 0.14), z=0.9))
    # THE STRINGS: regular, and four of them are curled
    BROKEN = (5, 13, 22, 29)
    for i in range(33):
        t = i / 32.0
        ty, tx = 86.0 - t * 6.0, -20.0 + t * 44.0
        by, bx = 8.0 + t * 3.0, 15.0 + t * 12.0
        if i in BROKEN:
            cut = 0.30 + _h(i, 521) * 0.42
            mx, my = bx + (tx - bx) * cut, by + (ty - by) * cut
            s.append(poly([(bx - 0.5, by), (bx + 0.5, by), (mx + 0.5, my), (mx - 0.5, my)],
                          _lerp(GUT, SILT_DARK, 0.30), z=1.6, rim=0.0))
            cxp, cyp = mx, my
            ang = math.atan2(ty - by, tx - bx)
            for k in range(3):
                ang += 1.5 + _h(i * 3 + k, 523) * 0.9
                nl = 4.4 - k * 1.1
                nxp, nyp = cxp + math.cos(ang) * nl, cyp + math.sin(ang) * nl
                s.append(poly([(cxp - 0.5, cyp), (cxp + 0.5, cyp), (nxp + 0.5, nyp), (nxp - 0.5, nyp)],
                              _lerp(GUT, PAGE, 0.20), z=1.62 + k * 0.01, rim=0.0))
                cxp, cyp = nxp, nyp
            continue
        # every seventh string is a coloured C -- how a harpist finds a key, and
        # the only reason this object needs more than one colour of string
        col = (_lerp(GUT, VELVET_LIT, 0.44) if i % 7 == 0
               else _lerp(GUT, PAGE_DARK, 0.20 + _h(i, 527) * 0.3))
        s.append(poly([(bx - 0.5, by), (bx + 0.5, by), (tx + 0.5, ty), (tx - 0.5, ty)],
                      col, z=1.55, rim=0.0))
    s.append(poly([(-28.0, 0.0), (32.0, 0.0), (28.0, 7.0), (-24.0, 7.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.40), z=2.0))
    _silt(s, -32.0, 34.0, 0.0, z=2.4, n=8, thick=1.25)
    return s, (W, H)


# ---------------------------------------------------------------------------
def cello():
    """A cello on its side, ~3.0 tiles. THE ONE THING THAT IS LYING DOWN.

    Every other object in this kit stands. A cello cannot -- it has no foot to
    stand on and a hundred years ago somebody laid it flat, on its side, with the
    scroll toward the wall, the way you leave an instrument you intend to come
    back for. That reading is doing a lot of work: it is not DROPPED (nothing was
    broken by force), it is PUT DOWN, and the difference between those two verbs
    is the difference between a disaster and an errand.

    THE F-HOLES ARE THE WHOLE READ. Take them out and this is a gourd. They are
    two dark curls, mirrored, and they are the only place on the piece where the
    eye finds black.
    """
    s = []
    W, H = 96, 52
    up, dn = [], []
    for i in range(21):
        t = i / 20.0
        x = -40.0 + 62.0 * t
        r = (13.0 * (0.35 + 0.65 * math.sin(min(1.0, t / 0.94) * math.pi) ** 0.55)
             - 4.6 * math.exp(-((t - 0.50) / 0.13) ** 2)
             + 2.0 * math.exp(-((t - 0.82) / 0.16) ** 2))
        up.append((x, 15.0 + r)); dn.append((x, 15.0 - r * 0.72))
    s.append(poly(up + dn[::-1], _lerp(MAHOG, MAHOG_DARK, 0.10), z=0.6))
    s.append(poly(up + [(px, py - 3.4) for px, py in up][::-1],
                  _lerp(MAHOG_LIT, GILT, 0.16), z=0.7))
    s.append(poly(dn + [(px, py + 2.0) for px, py in dn][::-1],
                  _lerp(MAHOG_DARK, (14, 9, 8), 0.24), z=0.65))
    s.append(poly([(px, py - 1.6) for px, py in up] + [(px, py - 2.4) for px, py in up][::-1],
                  _lerp(MAHOG_DARK, PAGE_DARK, 0.30), z=0.75, rim=0.0))
    # THE F-HOLES. Mirrored, and the only black on the piece.
    for d in (1.0, -1.0):
        cy = 15.0 + d * 6.6
        s.append(poly([(-6.0, cy - d * 1.0), (-3.0, cy + d * 3.4), (2.0, cy + d * 3.0),
                       (5.0, cy - d * 1.4), (3.5, cy - d * 1.8), (1.0, cy + d * 1.4),
                       (-3.0, cy + d * 1.6), (-4.6, cy - d * 1.4)],
                      _lerp(MAHOG_DARK, (10, 7, 7), 0.62), z=1.0, rim=0.0))
    s.append(poly([(-2.0, 8.0), (2.0, 8.0), (2.0, 23.0), (-2.0, 23.0)],
                  _lerp(PAGE_DARK, MAHOG_LIT, 0.30), z=1.1))
    s.append(poly([(20.0, 12.0), (46.0, 14.0), (46.0, 18.0), (20.0, 18.0)],
                  _lerp(MAHOG, MAHOG_DARK, 0.34), z=0.9))
    s.append(poly([(20.0, 17.0), (46.0, 17.5), (46.0, 20.0), (20.0, 20.0)],
                  _lerp(IRONWORK, MAHOG_DARK, 0.30), z=0.95))
    for i in range(4):
        yy = 13.4 + i * 1.5
        s.append(poly([(-1.0, 10.5 + i * 2.6), (44.0, yy), (44.0, yy + 0.6), (-1.0, 11.1 + i * 2.6)],
                      _lerp(GUT, PAGE, 0.24 - i * 0.05), z=1.2, rim=0.0))
    s.append(poly([(44.0, 11.0), (52.0, 12.0), (53.0, 21.0), (44.0, 20.0)],
                  _lerp(MAHOG, MAHOG_LIT, 0.14), z=1.3))
    for i, (sx, sy, sr) in enumerate(((54.0, 20.0, 4.6), (55.6, 17.6, 2.8), (54.4, 16.4, 1.4))):
        s.append(blob(_lerp(MAHOG, MAHOG_LIT, 0.10 + i * 0.16), sr, sr, off=(sx, sy), z=1.4 + i * 0.02))
    for i, py in enumerate((12.6, 15.4, 17.0, 19.4)):
        s.append(blob(_lerp(IRONWORK, MAHOG_DARK, 0.24), 1.3, 2.6,
                      off=(46.0 + (i % 2) * 4.0, py), z=1.5))
    _silt(s, -44.0, 44.0, 4.0, z=2.2, n=9, thick=1.05)
    return s, (W, H)


# ---------------------------------------------------------------------------
def timpani():
    """A PAIR of kettledrums, ~3.0 tiles. THE ONLY DRUMS IN A GAME ABOUT RHYTHM.

    Worth saying out loud, because it makes this the one prop in the world with a
    direct line to the mechanic. The player has spent four regions hitting things
    on a beat; here is the object that beat came out of, and it is silt-filled and
    silent. No sting, no glow, no interaction -- §6.5's orchestra is dressing.
    The joke is not pointed out.

    IT TOOK FIVE GOES AND EVERY FAILURE WAS THE SAME FAILURE: a dark bowl under a
    pale disc is a TABLE WITH A DOILY; a bright bowl behind eight pale rods is a
    BIRDCAGE; a pale head resting on a dark hoop is a WHEELBARROW; a bright lip
    over a dark hollow is a TROUGH. Four objects, one cause -- a single drum has
    one large flat-topped mass, and a single large flat-topped mass on legs is
    furniture no matter what you paint on it.

    THE FIX WAS TO STOP DRAWING ONE. Timpani come in pairs; they always have.
    Two overlapping hemispheres at different sizes and different heights have no
    single top surface for the eye to sit a tabletop on, the occlusion states
    depth for free, and the pair is a silhouette nothing else in the world
    resembles. The general lesson, which is now in the style contract: when an
    object keeps resolving into furniture, the problem is usually the SILHOUETTE
    COUNT, not the shading.

    THE BOWLS ARE SPHERES AND THAT IS DONE WITH BANDS -- TWELVE OF THEM, because
    five read as a BARREL. Discrete slices wide enough to see are staves, and
    staves are a coopered vessel; twelve blend into a curve. Brightest just under
    the rim and falling away to almost nothing at the bottom, because copper is a
    mirror and its terminator is high and hard. A gradient across the WIDTH would
    have made a cylinder instead.
    """
    s = []
    W, H = 104, 62

    def kettle(cx, base, rw, depth, z0, lit):
        """One bowl. `lit` shifts the whole family up or down for the far drum."""
        # ONE polygon for the bowl -- a hemisphere outline, nothing stacked
        prof = []
        for k in range(21):
            t = k / 20.0
            prof.append((cx + rw * math.sqrt(max(0.0, 1.0 - t * t * 0.96)),
                         base + depth * (1.0 - t)))
        s.append(poly([(cx - x + cx, y) for x, y in prof][::-1] + prof,
                      _lerp(_lerp(BRASS, PATINA, 0.24), _lerp(BRASS_LIT, GILT, 0.20), lit * 0.42),
                      z=z0))
        # the roundness, in ONE soft pass. A dark blob at the foot as well made a
        # hole in the bottom of the bowl -- the base colour is already the low
        # value, so the only thing missing was the high one.
        s.append(blob(_lerp(BRASS_LIT, GILT, 0.20), rw * 0.90, depth * 0.22,
                      off=(cx - rw * 0.08, base + depth * 0.72), z=z0 + 0.06, rim=0.0))
        # the specular: a short bright arc on the upper-left shoulder ONLY
        s.append(blob(_lerp(GILT, CANDLE, 0.34 * lit), rw * 0.30, 2.0,
                      off=(cx - rw * 0.44, base + depth * 0.80), z=z0 + 0.14, rim=0.0))
        # one patina streak, running down from the rim where the water sat
        s.append(blob(_lerp(PATINA, BRASS_DARK, 0.36), rw * 0.13, depth * 0.42,
                      off=(cx + rw * 0.30, base + depth * 0.42), z=z0 + 0.15, rim=0.0))
        # THE HEAD, sunk inside the rim: a slack dish with a century of silt in it
        head = [(cx - rw * 0.86 + rw * 1.72 * (i / 16.0),
                 base + depth - 2.0 - math.sin(math.pi * (i / 16.0)) * 2.6) for i in range(17)]
        s.append(poly(head + [(hx, hy - 4.4) for hx, hy in head][::-1],
                      _lerp(PAGE, SILT, 0.36), z=z0 + 0.2))
        s.append(blob(_lerp(SILT, SILT_DARK, 0.36), rw * 0.46, 1.9,
                      off=(cx - 0.5, base + depth - 4.0), z=z0 + 0.22, rim=0.0))
        # the counterhoop: bright brass at the lip, in front of the head
        lip = [(cx - rw + rw * 2.0 * (i / 16.0),
                base + depth - math.sin(math.pi * (i / 16.0)) * 2.2) for i in range(17)]
        s.append(poly(lip + [(lx, ly - 3.0) for lx, ly in lip][::-1],
                      _lerp(BRASS_LIT, GILT, 0.24 * lit), z=z0 + 0.3))
        # four tuning rods, dark, thin, hardware not structure -- and one bent
        for k in range(4):
            rx = cx - rw * 0.72 + rw * 1.44 * (k / 3.0)
            bend = 1.8 if k == 1 else 0.0
            s.append(poly([(rx - 0.6, base + depth * 0.42), (rx + 0.6, base + depth * 0.42),
                           (rx + 0.6 + bend, base + depth - 1.0),
                           (rx - 0.6 + bend, base + depth - 1.0)],
                          _lerp(IRONWORK, MAHOG_DARK, 0.12 + _h(k, 537) * 0.16), z=z0 + 0.35, rim=0.06))
        # three legs
        # THE LEGS HAVE TO BE VISIBLE, so the bowl sits well clear of the floor.
        # The first pair started at y=0 and ended at y=base, i.e. at the bowl's
        # own bottom, so both drums appeared to rest on the ground and the tripod
        # -- the thing that says "instrument on a stand" -- was entirely hidden.
        # AND IN THE BROWSER THE PAIR READ AS TWO WINE GLASSES. At three tiles
        # wide the legs were 0.74 of the bowl radius apart and 2.2px thick, which
        # downsamples to a STEM, and a bowl on a stem is stemware. A timpani
        # tripod splays WIDER than the bowl -- it has to, the thing is heavy and
        # gets hit -- so the feet go outside the rim and the legs are thick
        # enough to survive the halving. Cross-braces too: the horizontal is
        # what says "frame" instead of "pedestal".
        for lx, lz in ((cx - rw * 1.02, z0 - 0.1), (cx + rw * 1.00, z0 - 0.1),
                       (cx - 1.0, z0 + 0.4)):
            s.append(poly([(lx - 3.0, 0.0), (lx + 3.0, 0.0),
                           (cx + 2.4, base + 2.0), (cx - 2.4, base + 2.0)],
                          _lerp(IRONWORK, MAHOG_DARK, 0.20), z=lz, rim=0.08))
            s.append(blob(_lerp(BRASS_DARK, BRASS, 0.24), 3.2, 1.1, off=(lx, 1.0), z=lz + 0.05))

    def brace(cx, rw, y):
        s.append(poly([(cx - rw * 0.72, y), (cx + rw * 0.70, y),
                       (cx + rw * 0.70, y + 2.2), (cx - rw * 0.72, y + 2.2)],
                      _lerp(IRONWORK, MAHOG_DARK, 0.14), z=0.35, rim=0.06))

    # the far drum first: smaller, higher, dimmer -- it is BEHIND the near one
    brace(21.0, 17.0, 7.0)
    kettle(21.0, 20.0, 17.0, 24.0, z0=0.4, lit=0.66)
    # the near drum: larger, lower, overlapping it. The occlusion is the piece.
    brace(-15.0, 25.0, 4.0)
    kettle(-15.0, 10.0, 25.0, 40.0, z0=1.4, lit=1.0)
    _silt(s, -50.0, 50.0, 0.0, z=2.6, n=11, thick=1.15)
    return s, (W, H)

def sheet_drift():
    """Sheet music drifted against something, ~4.0 tiles. THE HALL'S SNOW.

    The piece that makes the Keep read as ONE PLACE, the way `oasis_rill` does
    for the Scar: lay four of these along the foot of a wall and the hall
    acquires weather. A century of water moved the loose paper the way water
    moves leaves -- into corners, against the lee side of everything, in a low
    bank that is thick at one end and thins to nothing at the other.

    NOT A NEAT STACK. A stack is a filing cabinet. This is a DRIFT: leaves at
    many angles, mostly buried, showing corners -- and the crucial part is that
    the individual leaves are only legible at the TOP of the bank. Down in the
    mass they have pulped into one grey body, because that is what happens to
    paper, and the difference between the pulped bottom and the crisp top edge is
    the only thing that makes this read as depth rather than as a patterned rug.

    AND IN THE BROWSER IT READ AS BROKEN GLASS. One constant did it: the lit
    leading edge was mixed toward `GLASS_LIT` (192,216,214), a COOL blue-white,
    because it was the brightest thing in the palette and I picked it for its
    value without looking at its hue. Cool white on a thin angular sliver is a
    shard; paper's highlight is warm, because paper is warm. It goes to `CANDLE`
    now, and the leaves are fewer, larger and more overlapped, and the angle
    spread is halved -- paper lies down flat, glass stands up on edge, and the
    difference between the two readings is almost entirely how far from
    horizontal the fragments sit.

    AND IT WAS STILL COLD, because `PAGE` itself is (162,156,136) -- a neutral
    grey with a whisper of yellow -- and at half scale a low pale neutral mass on
    dark ground is SLUSH. Wet paper is grey, which is true and is not the point:
    the piece has to say paper at three tiles, and the only lever left at that
    size is temperature. Every fill here is now pulled toward candle-warm, and
    the body is darker than the leaves so the bank has a bottom.
    """
    s = []
    W, H = 128, 26
    # the pulped body: one mass, thick at the left, thinning to the right
    body = []
    for i in range(17):
        t = i / 16.0
        body.append((-60.0 + 120.0 * t,
                     (11.0 - 9.4 * t ** 1.5) * (1.0 + 0.16 * math.sin(t * 9.0))))
    s.append(poly([(-62.0, 0.0)] + body + [(60.0, 0.0)],
                  _lerp(PAGE_DARK, SILT_DARK, 0.40), z=0))
    s.append(poly([(-62.0, 0.0)] + [(x, y * 0.62) for x, y in body] + [(60.0, 0.0)],
                  _lerp(PAGE_DARK, SILT, 0.24), z=0.1))
    # THE LEGIBLE LEAVES, at the top of the bank only, all at different angles
    for i in range(16):
        t = _h(i, 541)
        x = -58.0 + 116.0 * t
        top = (11.0 - 9.4 * t ** 1.5)
        y = top * (0.42 + _h(i, 543) * 0.72)
        if y > top + 2.0:
            continue
        a = (_h(i, 547) - 0.5) * 0.72
        L = 8.0 + _h(i, 549) * 8.0
        wd = 2.0 + _h(i, 551) * 3.2
        dx, dy = math.cos(a) * L, math.sin(a) * L
        nx, ny = -math.sin(a) * wd, math.cos(a) * wd
        s.append(poly([(x - dx + nx, y - dy + ny), (x + dx + nx, y + dy + ny),
                       (x + dx - nx, y + dy - ny), (x - dx - nx, y - dy - ny)],
                      _lerp(_lerp(PAGE, PAGE_DARK, 0.04 + _h(i, 553) * 0.54), CANDLE, 0.22),
                      z=0.5 + y * 0.01))
        # a lit leading edge on about a third of them: what makes paper read thin
        if _h(i, 557) > 0.62:
            s.append(poly([(x - dx + nx, y - dy + ny), (x + dx + nx, y + dy + ny),
                           (x + dx + nx * 0.4, y + dy + ny * 0.4),
                           (x - dx + nx * 0.4, y - dy + ny * 0.4)],
                          _lerp(PAGE, CANDLE, 0.52), z=0.6 + y * 0.01))
    _silt(s, -64.0, 64.0, 0.0, z=1.6, n=10, thick=0.7)
    return s, (W, H)


# ---------------------------------------------------------------------------
def candelabra():
    """A floor candelabrum, ~2.4 tiles. THE ONLY LIT THING IN THE KEEP.

    Required by name: `GATE_PROPS` in OverworldScene.placeRegionGates puts a pair
    of these at the region-4 boundary, so this is the piece that tells the player
    they have crossed into the last region. Two small warm flames in a doorway,
    and behind them a hall with no light in it at all.

    THAT SCARCITY IS DELIBERATE AND IT IS LOAD-BEARING (header, rule 3). §7's
    warm room -- the one room in this game with people in it and a fire going --
    only lands if the player has just walked a long way through the most
    expensive building in the world in the DARK. If the hall glowed, §7 would be
    a repeat instead of an arrival. So this kit has exactly one emissive piece,
    it stands at the threshold, and it has THREE candles lit out of five.

    THE EMISSIVE BLUR LAW (style contract §4.7). `rig.Painter` blurs a glowing
    shape by `9 * SS * glow`, so a 2px flame at glow 1.0 spreads its whole energy
    over a 36px radius and vanishes. Every flame here is the three-layer stack:
    a DARK bloom at glow 1.0 for the throw, a tight envelope at 0.22, an opaque
    core at 0.10. `_candle` does it; nothing in this file draws a flame by hand.
    """
    s = []
    W, H = 64, 76
    # the tripod foot: three scrolled feet, and the piece leans very slightly
    for fx, fz, fd in ((-16.0, 0.2, 0.30), (15.0, 0.2, 0.30), (-2.0, 0.7, 0.06)):
        s.append(poly([(fx * 1.15, 0.0), (fx * 0.72, 0.0), (-1.4, 12.0), (1.4, 12.0)],
                      _lerp(IRONWORK, BRASS_DARK, fd), z=fz))
        s.append(blob(_lerp(BRASS_DARK, BRASS, 0.24), 3.4, 1.5, off=(fx, 1.2), z=fz + 0.05))
    # the stem: a turned baluster, so it is NOT a smooth taper (§4.7) -- three
    # swellings and two waists, which is what a lathe actually produces
    for i in range(15):
        t = i / 14.0
        y = 11.0 + 40.0 * t
        r = (2.6 + 2.4 * math.exp(-((t - 0.10) / 0.09) ** 2)
             + 3.1 * math.exp(-((t - 0.42) / 0.11) ** 2)
             + 1.9 * math.exp(-((t - 0.78) / 0.08) ** 2))
        s.append(blob(_lerp(BRASS_DARK, BRASS, 0.22 + 0.30 * math.sin(t * 3.1)),
                      r, 2.0, off=(0.0, y), z=0.9 + i * 0.005))
    # the arms: five sockets, and they are at TWO heights, not one. A single
    # level of five is a menorah; two levels is a candelabrum.
    SOCK = ((-21.0, 58.0, True), (-11.0, 63.0, True), (0.0, 66.0, False),
            (11.0, 62.0, True), (20.0, 56.0, False))
    for i, (ax, ay, lit) in enumerate(SOCK):
        if ax != 0.0:
            arm = []
            for k in range(9):
                t = k / 8.0
                arm.append((ax * t, 52.0 + (ay - 52.0) * (t ** 0.55) - 2.0 * math.sin(t * math.pi)))
            s.append(poly(arm + [(px, py + 2.2) for px, py in arm][::-1],
                          _lerp(BRASS_DARK, BRASS, 0.24 + _h(i, 561) * 0.22), z=1.2))
        # the drip pan and the socket
        s.append(blob(_lerp(BRASS, BRASS_LIT, 0.20), 4.6, 1.5, off=(ax, ay), z=1.4))
        s.append(poly([(ax - 2.0, ay), (ax + 2.0, ay), (ax + 1.8, ay + 4.0), (ax - 1.8, ay + 4.0)],
                      _lerp(BRASS_DARK, BRASS, 0.36), z=1.45))
        # the candle: unequal stubs, and the wax has RUN, which is the detail
        ch = 3.0 + _h(i, 563) * 6.0
        s.append(poly([(ax - 1.6, ay + 3.0), (ax + 1.6, ay + 3.0),
                       (ax + 1.4, ay + 3.0 + ch), (ax - 1.4, ay + 3.0 + ch)],
                      _lerp(PAGE, CANDLE, 0.16), z=1.5))
        for k in range(2):
            s.append(poly([(ax - 1.6 + k * 2.4, ay + 3.0), (ax - 0.8 + k * 2.4, ay + 3.0),
                           (ax - 1.0 + k * 2.4, ay + 0.4 - _h(i * 2 + k, 567) * 1.6),
                           (ax - 1.8 + k * 2.4, ay + 0.6)],
                          _lerp(PAGE, SILT_LIT, 0.20), z=1.55))
        if lit:
            _candle(s, ax, ay + 4.4 + ch, z=6.0, r=2.5 + _h(i, 569) * 0.7)
    return s, (W, H)


# ---------------------------------------------------------------------------
def chandelier_down():
    """A chandelier lowered to the floor, ~3.5 tiles. AND IT IS NOT LIT.

    THE BEST SINGLE OBJECT IN THIS KIT, because of one fact about how theatres
    work: you WINCH a chandelier down to change its candles. Somebody lowered
    this to service it, on an ordinary afternoon, and never finished the job.
    Nothing fell. Nothing broke. It is exactly where the work stopped -- and a
    chandelier resting on a floor is the wrong-way-up image that tells the player
    something interrupted this building in the middle of a normal errand, which
    is the whole premise of the world and is stated here without one word.

    IT IS WIDE (4.0 x 2.0 tiles) and it is LOW, which is what a hanging thing
    looks like once it is down -- but the first cut was 3.5 x 1.2 with a corona
    9px tall, and at that aspect the ring collapsed into a bar, the drops were
    four pixels long, and the whole thing read as a heap of wreckage or an
    upturned boat. A ring seen at a low angle still has to be a RING: the minor
    axis needs to be a good third of the major one or the eye gets an ellipse
    with no interior, and the drops have to be long enough to hang. Correct
    reading of a foreshortened circle costs vertical pixels; there is no version
    of this piece that is one tile tall. and it is the only object in the kit whose long axis is
    horizontal apart from `sheet_drift` and `cello`. That silhouette is the tell.
    Its chain runs up out of the top of the sprite -- cut off, still attached to
    something the frame does not show.

    NOT LIT. Its candles are the ones that were being replaced: half of them are
    stubs and half are missing. The kit's one light is `candelabra`, at the gate
    (header, rule 3), and putting a second one here would be the third time in
    this project I lit something because it was easy to light.
    """
    s = []
    W, H = 128, 64
    # the chain, running up and out of frame, and it is SLACK at the bottom --
    # the weight is on the floor now, so the chain is not carrying it
    ch = [(5.0, 46.0), (8.0, 51.0), (4.0, 55.0), (7.0, 60.0), (5.0, 64.0)]
    for i in range(len(ch) - 1):
        (x0, y0), (x1, y1) = ch[i], ch[i + 1]
        s.append(poly([(x0 - 1.2, y0), (x0 + 1.2, y0), (x1 + 1.2, y1), (x1 - 1.2, y1)],
                      _lerp(IRONWORK, BRASS_DARK, 0.22 + _h(i, 571) * 0.2), z=1.8))
    # the corona: a ring seen at a low angle, so it is a wide flat ellipse, and
    # it sits TILTED because it came to rest on an uneven floor
    TILT = 0.13
    RX, RY, RCY = 52.0, 18.0, 26.0
    ring = []
    for i in range(29):
        a = math.pi * 2.0 * (i / 28.0)
        ring.append((math.cos(a) * RX, RCY + math.sin(a) * RY + math.cos(a) * RX * TILT))
    # AND THEN IT WAS A FLYING SAUCER, because `poly()` of a closed loop is a
    # FILLED disc -- I wrote "the ring as a BAND, not a filled disc" in the
    # comment and then handed the rasteriser a single closed outline, which is
    # the most literal possible version of the mistake. An annulus has to be
    # drawn as two arcs: the outer sweep, then the inner sweep BACKWARDS, so the
    # polygon's winding leaves the middle out. The hole in the middle is the
    # entire difference between a ring lying on a floor and a saucer landing.
    IN = 0.74
    inner_ring = [(x * IN, RCY + (y - RCY) * IN) for x, y in ring]
    s.append(poly(ring + inner_ring[::-1], _lerp(BRASS_DARK, BRASS, 0.18), z=1.0))
    # the near half of the band catches the light; the far half is edge-on
    s.append(poly(ring[7:22] + [(x, y - 3.2) for x, y in ring[7:22]][::-1],
                  _lerp(BRASS, BRASS_LIT, 0.30), z=1.05))
    s.append(poly(inner_ring[7:22] + [(x, y + 2.4) for x, y in inner_ring[7:22]][::-1],
                  _lerp(BRASS_DARK, MAHOG_DARK, 0.34), z=1.06))
    # the central shaft rising out of the ring to the chain, and its finial
    s.append(poly([(-3.4, RCY), (3.4, RCY), (2.6, 50.0), (-2.6, 50.0)],
                  _lerp(BRASS_DARK, BRASS, 0.30), z=1.2))
    s.append(blob(_lerp(BRASS, BRASS_LIT, 0.26), 5.0, 3.4, off=(0.0, 50.0), z=1.25))
    s.append(blob(_lerp(BRASS_DARK, BRASS, 0.34), 6.4, 4.0, off=(0.0, RCY - 12.0), z=1.15))
    # THE DROPS: cut glass, hung in a skirt, and a THIRD OF THEM ARE GONE. The
    # gaps are what make it read as a serviced object rather than a decoration.
    for i in range(26):
        a = math.pi * 2.0 * (i / 26.0)
        dx = math.cos(a) * 47.0
        dy = RCY + math.sin(a) * 16.0 + math.cos(a) * 47.0 * TILT
        if _h(i, 573) < 0.34:
            continue
        dl = 7.0 + _h(i, 577) * 8.0
        s.append(poly([(dx - 1.5, dy), (dx + 1.5, dy), (dx + 0.8, dy - dl), (dx - 0.8, dy - dl)],
                      _lerp(GLASS, GLASS_LIT, 0.14 + _h(i, 579) * 0.44), z=1.4, rim=0.10))
        if _h(i, 581) > 0.70:      # a facet catching what little light there is
            s.append(poly([(dx - 0.6, dy - 0.6), (dx + 0.4, dy - 0.4),
                           (dx + 0.2, dy - dl * 0.55), (dx - 0.5, dy - dl * 0.5)],
                          _lerp(GLASS_LIT, PAGE, 0.30), z=1.45, rim=0.0))
    # the sockets around the ring: half stubs, half EMPTY. This is the errand.
    for i in range(12):
        a = math.pi * 2.0 * (i / 12.0) + 0.26
        sx = math.cos(a) * 49.0
        sy = RCY + math.sin(a) * 17.0 + math.cos(a) * 49.0 * TILT
        s.append(blob(_lerp(BRASS, BRASS_LIT, 0.18), 3.4, 1.4, off=(sx, sy + 1.0), z=1.5))
        if _h(i, 583) > 0.50:
            hh = 1.6 + _h(i, 587) * 4.4
            s.append(poly([(sx - 1.5, sy + 1.5), (sx + 1.5, sy + 1.5),
                           (sx + 1.3, sy + 1.5 + hh), (sx - 1.3, sy + 1.5 + hh)],
                          _lerp(PAGE, CANDLE, 0.10), z=1.55))
            s.append(blob(_lerp(IRONWORK, PAGE_DARK, 0.30), 0.6, 1.0,
                          off=(sx, sy + 2.2 + hh), z=1.6))   # the cold black wick
        else:
            s.append(blob(_lerp(BRASS_DARK, (12, 10, 8), 0.44), 1.5, 0.9,
                          off=(sx, sy + 1.6), z=1.55, rim=0.0))
    # a few loose drops on the floor beside it, where they were being taken off
    for i in range(5):
        lx = -44.0 + i * 21.0 + (_h(i, 589) - 0.5) * 11.0
        s.append(poly([(lx - 2.4, 1.0), (lx + 2.4, 1.4), (lx + 1.8, 3.2), (lx - 2.0, 2.8)],
                      _lerp(GLASS, GLASS_LIT, 0.10 + _h(i, 593) * 0.30), z=2.0, rim=0.08))
    _silt(s, -62.0, 62.0, 0.0, z=2.4, n=12, thick=0.85)
    return s, (W, H)


PIECES = {
    # THE ARCHITECTURE -- the pieces that make the hall a BUILDING, and the only
    # place in this world where a clean built silhouette is the right answer
    "proscenium": proscenium,
    "organ_pipes": organ_pipes,
    "pillar": pillar,
    "hall_door": hall_door,
    "seat_bank": seat_bank,
    # THE ORCHESTRA -- still on their stands (§6.5), dressing and NOBODY'S story
    "harp": harp,
    "cello": cello,
    "timpani": timpani,
    "music_stand": music_stand,
    "chair_row": chair_row,
    "chair": chair,
    "podium": podium,
    # THE HALL'S OWN WEATHER
    "sheet_drift": sheet_drift,
    "stopped_clock": stopped_clock,
    # THE ONLY LIT THING IN REGION 4, and it stands at the gate
    "candelabra": candelabra,
    "chandelier_down": chandelier_down,
}


def build(name):
    shapes, size = PIECES[name]()
    # THE WARMEST RIM IN THE GAME. The Fold, Shelf and Breach are lit cold; the
    # Scar is a dusty sun; the Keep is lit by what is left of a room full of
    # gilt, mahogany and brass bouncing a very little daylight around. The rim
    # does the work the LAMPS are not allowed to do (header, rule 3) -- the
    # warmth is in the materials, and this is the material talking.
    p = Painter(size, rim_col=(214, 176, 118))
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
