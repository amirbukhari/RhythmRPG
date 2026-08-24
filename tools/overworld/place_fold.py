"""Author the Fold's dressing, and CHECK it against the real map.

    python3 tools/overworld/place_fold.py            # validate + report
    python3 tools/overworld/place_fold.py --write    # rewrite dressing.json

WHY THIS EXISTS
Props in this world are placed BY HAND (owner: "items need to be placed with
intention. none of this scattering shit"), and by hand is right -- but a hand
cannot see a prop's FOOTPRINT. At the canonical world scale a 7m house is
3.3 x 6.6 tiles: it covers the seven tiles NORTH of the tile it stands on,
because sprites are drawn from their base. Eyeballing coordinates off an ASCII
map puts buildings on roads. So the placements are authored here, next to the
checker, and every one is verified against `assets/tilemaps/overworld.json`:

  * no piece may cover a PATH tile -- a house drawn over the road makes the
    road look like a mistake (the ARCH is exempt, see THE ARCH below)
  * no piece may cover a WATER tile
  * pieces may stand on ROCK, and mostly should: rock already blocks movement,
    so a building on rock is a building the player cannot walk through, and the
    collision layer and the picture finally agree
  * pieces may not overlap each other by more than OVERLAP_TOL

THE MAP ALREADY HAD ARCHITECTURE IN IT
`generate_overworld_map.py` laid down hollow rectangles of rock around the
Fold -- (17-21, 166-170), (30-34, 162-166), (26-30, 177-181). Those are walled
yards, and nothing had ever been drawn on them. This file dresses them.

WHAT THE PLAYER SEES FIRST
Mir spawns at (26,172) with the town obelisk three tiles north at (26,169). The
camera is 20 x 11 tiles, so the opening frame is roughly cols 16-36, rows
166-178, and that frame is the whole first impression of the game's one warm
place (world-bible §6.1: the player "should like it here"). Density is spent
there first and thins outward, which is also how a real town looks.

COORDINATES ARE ABSOLUTE
`col`/`row` are tiles on the 356x200 map. They used to be region-local, offset
by `region_index * 26` -- a formula from the pre-v15 map that is 10x smaller
than the world it now indexes. Region 0 actually occupies cols 0-75, rows
127-199, so every authored vignette was being drawn ~140 tiles north of the
region it belonged to, in a corner of the Saltmines. Absolute is the fix: a
prop placed by hand belongs at a PLACE, not at an offset from a constant.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "assets" / "tilemaps" / "overworld.json"
DRESSING = ROOT / "src" / "data" / "content" / "overworld" / "dressing.json"
KIT = ROOT / "assets" / "sprites" / "env" / "fold"

TILE = 16
PX_PER_METER = 15  # src/scenes/env/WorldScale.ts
MIN_SCALE, MAX_SCALE = 0.28, 1.6
# Must match the fold block of WorldScale.METERS -- the engine's scale wins
# over any authored one, so the footprint maths has to use the engine's number.
METERS = {
    "house_tall": 9.0,
    "house_row": 6.5,
    "well": 1.9,
    "crate_stack": 1.1,
    "cart": 1.3,
    "house_a": 7.0,
    "house_b": 5.0,
    "arch": 5.0,
    "lamp": 2.6,
    "shrine": 2.2,
    "bench": 0.9,
    "ring_stone": 0.45,
}
# Pieces allowed to stand ON a road. Only the arch: it is a gate, and a gate
# that does not straddle the road it gates is a decoration in a field.
# Pieces allowed to stand on PAVING. The arch is a gate, and a gate that does
# not straddle the road it gates is a decoration in a field. The kneeling stones
# belong on the plaza for the same reason: the paved tiles around the obelisk ARE
# the plaza, and the Rite is performed on them.
ROAD_OK = {"arch", "ring_stone"}
# Two pieces collide when their GROUND CONTACT overlaps -- not their bounding
# boxes. Boxes were the first rule and it was wrong: a lamp standing in FRONT of
# a house is inside the house's box by definition (the house is 6 tiles tall and
# drawn from its base), and the engine already sorts by base Y so the lamp simply
# occludes it. What is actually broken is two pieces standing on the same GROUND,
# so the test is: x-ranges overlap AND bases within FOOT_DEPTH pixels.
FOOT_DEPTH = 10
FOOT_TOL = 0.3  # fraction of the narrower piece's width that may share ground

# ---------------------------------------------------------------------------
# THE TOWN
# ---------------------------------------------------------------------------
# `dx`/`dy` are pixel offsets from the tile's bottom-centre, for anything whose
# position matters to less than a 16px tile -- the kneeling rings in particular,
# which are a circle and cannot be expressed on a grid.
OBELISK = (26, 169)  # the `town_obelisk` marker in overworld.json
# OverworldScene draws seven kneeling worshippers around the monolith on an
# ellipse of radius 26 squashed to 0.42 -- the world's ground plane. The stone
# rings below use the SAME ellipse at larger radii, so all three rings share one
# perspective instead of three.
RING_SQUASH = 0.42


def place(vignette, piece, col, row, flip=False, dx=0, dy=0):
    return {"vignette": vignette, "piece": piece, "col": col, "row": row,
            "flip": flip, "dx": dx, "dy": dy}


def _kneeling_rings():
    """The Rite's concentric rings (world-bible §6.1), as stones in the paving.

    Two arcs outside the worshippers, open at the north because the monolith
    stands there and open at the west because the road runs through col 23 --
    a ring that closes across a road reads as rubble, not as ritual.
    """
    out = []
    ocx = OBELISK[0] * TILE + TILE / 2
    ocy = OBELISK[1] * TILE + TILE
    for ri, (radius, n, a0, a1) in enumerate(((52.0, 7, 0.10, 0.90), (82.0, 9, 0.06, 0.94))):
        for i in range(n):
            t = a0 + (a1 - a0) * (i / float(n - 1))
            ang = math.pi * t                      # 0..pi sweeps the SOUTH arc
            x = ocx + math.cos(ang) * radius
            y = ocy + math.sin(ang) * radius * RING_SQUASH
            col = int(x // TILE)
            row = int((y - TILE) // TILE) + 1
            out.append(place("the-kneeling-rings", "ring_stone", col, row,
                             flip=x < ocx,
                             dx=int(round(x - (col * TILE + TILE / 2))),
                             dy=int(round(y - (row * TILE + TILE)))))
    return out


TOWN = _kneeling_rings() + [
    # -- THE HEART. The obelisk itself is placed by OverworldScene from the
    # `town_obelisk` marker; this is what stands AROUND it. Mir spawns at
    # (26,172) -- inside his own town's rings, which is where the Rite opens.
    place("the-heart", "shrine", 21, 171),
    place("the-heart", "bench", 33, 172),
    place("the-heart", "lamp", 19, 172),
    place("the-heart", "crate_stack", 30, 174),
    # -- THE SPINE: the east-west street at row 168. Lamps march along it at a
    # 6-tile interval, because §6.1 makes the prayer-lamps the only warm light in
    # the region and a lit street is the whole feeling of the place. Six tiles is
    # deliberate: the pools of light nearly touch, so the street reads as lit
    # rather than as separate lamps in the dark.
    place("the-street-of-lamps", "lamp", 25, 167),
    place("the-street-of-lamps", "lamp", 31, 167, flip=True),
    place("the-street-of-lamps", "lamp", 37, 167),
    place("the-street-of-lamps", "lamp", 43, 167, flip=True),
    place("the-street-of-lamps", "bench", 34, 167),
    place("the-street-of-lamps", "well", 38, 170),
    place("the-street-of-lamps", "cart", 36, 174, flip=True),
    place("the-street-of-lamps", "crate_stack", 41, 170),
    # -- THE UPPER TERRACE, north of the row-164 road: the town seen ACROSS the
    # street, and the reason the Fold has a skyline. The terrace is one piece
    # (see house_row) and the tall house abuts its west end, so the roofline
    # steps down eastward instead of standing as a wall.
    place("the-upper-terrace", "house_tall", 26, 163),
    place("the-upper-terrace", "house_row", 34, 163),
    place("the-upper-terrace", "lamp", 30, 166),
    place("the-upper-terrace", "lamp", 41, 163, flip=True),
    place("the-upper-terrace", "crate_stack", 28, 166),
    # -- THE ARCH: the north gate, standing ON the col-23 road where it leaves
    # town. Leaving the Fold means walking under it -- which is the point, since
    # every leaving in this story is one-way. See ROAD_OK.
    place("the-north-gate", "arch", 23, 160),
    place("the-north-gate", "lamp", 21, 161),
    place("the-north-gate", "lamp", 25, 161, flip=True),
    # -- THE SALT YARD: the walled rock ring at (17-21, 166-170) was drawn by
    # the map generator and never dressed. A workshop stands west of it and a
    # lamp burns inside the wall, so the wall reads as enclosing something.
    place("the-salt-yard", "house_b", 13, 167),
    place("the-salt-yard", "lamp", 19, 165, flip=True),
    place("the-salt-yard", "bench", 20, 172, flip=True),
    place("the-salt-yard", "cart", 16, 165),
    # -- THE WEST QUARTER: the older half, downhill of the street's west end.
    # A terrace, two houses, and only two lamps for the whole quarter -- the
    # Fold's warmth is not evenly distributed, and the street gets it first.
    place("the-west-quarter", "house_row", 11, 175),
    place("the-west-quarter", "house_a", 9, 183),
    place("the-west-quarter", "house_tall", 15, 185, flip=True),
    place("the-west-quarter", "bench", 14, 177),
    place("the-west-quarter", "lamp", 17, 172),
    place("the-west-quarter", "lamp", 13, 180, flip=True),
    place("the-west-quarter", "crate_stack", 18, 178),
    place("the-west-quarter", "well", 11, 179),
    # -- THE SOUTH SIDE: a house inside the second walled yard (26-30, 177-181),
    # so the street has depth on both sides instead of a lit front and a void.
    place("the-lower-yard", "house_b", 28, 178, flip=True),
    place("the-lower-yard", "lamp", 33, 177),
    place("the-lower-yard", "cart", 26, 183),
    # -- THE LAST HOUSE: past the second crossing, where the road climbs out of
    # town. One house, one lamp, then nothing -- the edge of the only warm place
    # in the game should be findable.
    place("the-last-house", "house_a", 51, 170, flip=True),
    place("the-last-house", "lamp", 48, 173),
]


def _map():
    doc = json.loads(MAP.read_text())
    w = doc["width"]
    data = next(l for l in doc["layers"] if l["name"] == "ground")["data"]
    return doc, w, data


def _sizes():
    out = {}
    for name, m in METERS.items():
        with Image.open(KIT / ("%s.png" % name)) as im:
            src_w, src_h = im.size
        s = max(MIN_SCALE, min(MAX_SCALE, (m * PX_PER_METER) / src_h))
        out[name] = (src_w * s, src_h * s)
    return out


def _box(sizes, p):
    """Pixel bounds, origin bottom-centre (matches setOrigin(0.5, 1))."""
    w, h = sizes[p["piece"]]
    x = p["col"] * TILE + TILE / 2 + p["dx"]
    y = p["row"] * TILE + TILE + p["dy"]
    return (x - w / 2, y - h, x + w / 2, y)


def check():
    doc, mw, data = _map()
    sizes = _sizes()
    problems = []

    def kind(c, r):
        if not (0 <= c < mw and 0 <= r < doc["height"]):
            return None
        gid = data[r * mw + c]
        return None if gid == 0 else (gid - 1) % 4

    def region(c, r):
        gid = data[r * mw + c]
        return None if gid == 0 else min(4, max(0, (gid - 1) // 4))

    for p in TOWN:
        vig, piece, col, row = p["vignette"], p["piece"], p["col"], p["row"]
        x0, y0, x1, y1 = _box(sizes, p)
        if region(col, row) != 0:
            problems.append("%s %s (%d,%d): base is in region %s, not the Fold" % (vig, piece, col, row, region(col, row)))
        for c in range(int(x0 // TILE), int((x1 - 1) // TILE) + 1):
            for r in range(int(y0 // TILE), int((y1 - 1) // TILE) + 1):
                k = kind(c, r)
                if k == 1 and piece not in ROAD_OK:
                    problems.append("%s %s (%d,%d): covers ROAD tile (%d,%d)" % (vig, piece, col, row, c, r))
                if k == 2:
                    problems.append("%s %s (%d,%d): covers WATER tile (%d,%d)" % (vig, piece, col, row, c, r))

    for i, a in enumerate(TOWN):
        for b in TOWN[i + 1 :]:
            ax0, _ay0, ax1, ay1 = _box(sizes, a)
            bx0, _by0, bx1, by1 = _box(sizes, b)
            if abs(ay1 - by1) > FOOT_DEPTH:
                continue  # different depth: one stands in front of the other
            ow = min(ax1, bx1) - max(ax0, bx0)
            if ow <= 0:
                continue
            frac = ow / min(ax1 - ax0, bx1 - bx0)
            if frac > FOOT_TOL:
                problems.append(
                    "%s %s (%d,%d) shares ground with %s %s (%d,%d) -- %.0f%% of its width"
                    % (a["vignette"], a["piece"], a["col"], a["row"],
                       b["vignette"], b["piece"], b["col"], b["row"], frac * 100)
                )
    return problems


def placements():
    return [
        {
            "vignette": p["vignette"],
            "key": "env_fold_%s" % p["piece"],
            "col": p["col"],
            "row": p["row"],
            "dx": p["dx"],
            "dy": p["dy"],
            "scale": 1.0,  # the engine's world scale wins; see WorldScale
            "flip": p["flip"],
        }
        for p in TOWN
    ]


def write():
    doc = json.loads(DRESSING.read_text())
    for region in doc["regions"]:
        if region["region"] in ("shallows", "fold"):
            region["region"] = "fold"
            region["placements"] = placements()
            break
    else:
        doc["regions"].insert(0, {"region": "fold", "placements": placements()})
    DRESSING.write_text(json.dumps(doc, indent=1) + "\n")
    return len(placements())


# The review gate (PRD §11.1.2): a layout is not written unlooked-at. Draws
# the town over a flat map of the terrain kinds, at true world scale, in the
# engine's own draw order (by base Y, so a nearer house occludes a farther one).
PREVIEW = ROOT / "tools" / "overworld" / ".preview"
KIND_COL = {0: (34, 44, 46), 1: (72, 66, 56), 2: (14, 30, 40), 3: (52, 58, 62), None: (8, 9, 12)}


def preview(c0=6, c1=54, r0=154, r1=192, zoom=3):
    doc, mw, data = _map()
    sizes = _sizes()
    W, H = (c1 - c0) * TILE, (r1 - r0) * TILE
    img = Image.new("RGB", (W, H))
    px = img.load()
    for c in range(c0, c1):
        for r in range(r0, r1):
            gid = data[r * mw + c]
            k = None if gid == 0 else (gid - 1) % 4
            col = KIND_COL[k]
            for i in range(TILE):
                for j in range(TILE):
                    px[(c - c0) * TILE + i, (r - r0) * TILE + j] = col
    for p in sorted(TOWN, key=lambda t: t["row"]):
        piece, flip = p["piece"], p["flip"]
        with Image.open(KIT / ("%s.png" % piece)) as src:
            src = src.convert("RGBA")
            w, h = sizes[piece]
            sp = src.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
            if flip:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        x0, y0, _x1, _y1 = _box(sizes, p)
        img.alpha_composite(sp, (int(x0) - c0 * TILE, int(y0) - r0 * TILE)) if img.mode == "RGBA" else img.paste(
            sp, (int(x0) - c0 * TILE, int(y0) - r0 * TILE), sp
        )
    PREVIEW.mkdir(parents=True, exist_ok=True)
    out = PREVIEW / "fold.png"
    img.resize((W * zoom, H * zoom), Image.NEAREST).save(out)
    return out


def main(argv):
    problems = check()
    for p in problems:
        print("FAIL  %s" % p)
    if problems:
        print("\n%d problem(s) -- nothing written." % len(problems))
        return 1
    print("%d placements, all clear of roads and water." % len(TOWN))
    if "--preview" in argv or "--write" in argv:
        print("preview -> %s" % preview().relative_to(ROOT))
    if "--write" in argv:
        print("wrote %d placements -> %s" % (write(), DRESSING.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
