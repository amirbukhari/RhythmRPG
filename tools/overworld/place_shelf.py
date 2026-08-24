"""Author the Kelp Shelf's dressing, and CHECK it against the real map.

    python3 tools/overworld/place_shelf.py            # validate + report
    python3 tools/overworld/place_shelf.py --write    # rewrite dressing.json

WHY THIS EXISTS AT ALL, WHICH IS A WORSE STORY THAN THE FOLD'S
`dressing.json` already held 64 placements for this region. Every one of them
was dead. They named textures from a piece vocabulary that was never built --
`env_saltmines_calcified_miner`, `env_saltmines_ore_rock`, thirty-four distinct
keys, all missing -- and `OverworldScene` skips a placement whose texture does
not exist (`if (!this.textures.exists(p.key)) continue`). So it skipped all of
them, silently, and had been doing so for the whole life of the file. The same
was true of the other three regions: 234 placements, 132 distinct keys, 132
missing. FOUR FIFTHS OF THE WORLD HAD NO PROPS IN IT and nothing ever said so,
because a silent `continue` is indistinguishable from an empty region.

That is worth writing down twice: the dressing file LOOKED authored. It had
counts. A reviewer skimming it would have seen a dressed world.

WHAT THIS REGION IS (world-bible §6.2, quoted because it is the whole brief)
    "Ship skeletons standing like a dead forest, every hull pointing up, and
     the salt-wracked remains of a mining town that dug into something and
     stayed."

Two subjects, and they are staged differently on purpose:

  * THE DEAD FOREST IS A CROWD. This is the one vignette in the game where
    quantity IS the composition -- a forest is not three trees, and "standing
    like a dead forest" fails if the player can count the hulls. So the wrecks
    come in a stand of eighteen, flanking the long climb up col 44, and they are
    varied by SILHOUETTE and FACING rather than by size (the engine's world
    scale wins over any authored one, by design -- see WorldScale.ts). Hulls,
    snapped hulls, bare masts, and rib sections, staggered in base row so they
    occlude each other and the stand reads as having depth.
  * THE MINE IS A PLACE. It is one tight cluster on the north side of the row-64
    main street: a headframe over the shaft, two shacks, the carts and rail that
    served it, a winch, and a lamp still burning. A mining town scattered evenly
    across a region is not a town.

AND THE CLIMB IS 28 TILES LONG AND STRAIGHT
Rows 64-92 up col 44 is the longest unbroken walk in the game. That is where the
stand goes, because §6.2's real job is "Nari is *with him* here, and this region
exists to make that hurt later" -- so the player should spend a long, quiet,
undefended stretch looking at dead ships with a child in tow. The two
`plank_bridge` crossings sit ON that road (see ROAD_OK) because §6.2 says the boy
"has to be carried over the bad gaps", and a crossing that does not cross the
road the player is walking is a decoration in a field.

COORDINATES ARE ABSOLUTE tiles on the 356x200 map. Region 1 is cols 0-109,
rows 0-141, and it has NO water tiles -- this is exposed seabed, which is why
the kelp is dry and stiff and the wrecks are stranded rather than sunk.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "assets" / "tilemaps" / "overworld.json"
DRESSING = ROOT / "src" / "data" / "content" / "overworld" / "dressing.json"
KIT = ROOT / "assets" / "sprites" / "env" / "shelf"
REGION_INDEX = 1
REGION_NAME = "shelf"

TILE = 16
PX_PER_METER = 15  # src/scenes/env/WorldScale.ts
MIN_SCALE, MAX_SCALE = 0.28, 1.6
# Must match the shelf block of WorldScale.METERS -- the engine's scale wins over
# any authored one, so the footprint maths has to use the engine's number.
METERS = {
    "hull": 7.5,
    "mast": 6.0,
    "headframe": 6.0,
    "hull_broken": 4.5,
    "kelp_stand": 4.0,
    "shack": 3.4,
    "ribs": 2.4,
    "lantern": 2.2,
    "winch": 1.4,
    "ore_cart": 1.4,
    "plank_bridge": 1.2,
    "rail_bend": 0.9,
}
# Pieces allowed to stand ON a road. Only the plank bridge: it is a crossing,
# and §6.2's "bad gaps" are gaps in the way the player is actually walking.
ROAD_OK = {"plank_bridge"}
FOOT_DEPTH = 10
FOOT_TOL = 0.3


def place(vignette, piece, col, row, flip=False, dx=0, dy=0):
    return {"vignette": vignette, "piece": piece, "col": col, "row": row,
            "flip": flip, "dx": dx, "dy": dy}


# ---------------------------------------------------------------------------
# THE DEAD FOREST -- a stand of eighteen, flanking the col-44 climb
# ---------------------------------------------------------------------------
# Base rows are staggered deliberately: the engine sorts by base Y, so a wreck
# two rows nearer the camera occludes the one behind it, and the stand gets
# depth instead of reading as a row of cut-outs on one line. Flips alternate
# irregularly -- a strict alternation is as readable a pattern as none at all.
# THE ROAD GEOMETRY SETS THE MINIMUM BASE ROW, AND IT IS NOT NEGOTIABLE.
# A sprite is drawn from its base, so a 14-metre hull occupies the FOURTEEN ROWS
# NORTH of the tile it stands on. The row-64 street runs cols 28-66 and the climb
# runs col 44 from row 36 to row 92, which means a hull standing anywhere on the
# long stretch must be based at row 79 or lower or its masthead lands on the
# street; a mast needs row 76, a snapped hull row 73, a rib section row 68. Every
# base row below comes out of that arithmetic, not out of the picture -- eight of
# the first draft's placements had their prows through the main road.
#
# AND THE COUNT IS THE POINT. The first draft put nineteen wrecks across a
# 66-by-70-tile stretch of region and the review verdict was the correct one:
# that is SCATTERED, not a forest. "Ship skeletons standing like a dead forest"
# (§6.2) fails the moment the player can count them, so this is thirty-three,
# packed into two dense bands either side of the climb with every piece on its
# own base row so they overlap and occlude. Walking up col 44 should feel like
# walking through a wood, with the road the only clear line in the frame.
#
# One consequence worth stating: base rows are all distinct by design, which is
# also what keeps the ground-contact test quiet -- two pieces one row apart are
# 16px apart in base Y and FOOT_DEPTH is 10, so they are read as one standing
# behind the other rather than as two things fighting for the same ground.
# THE ROAD GEOMETRY SETS THE MINIMUM BASE ROW, AND IT IS NOT NEGOTIABLE.
# A sprite is drawn from its base, so a piece occupies the rows NORTH of the tile
# it stands on. The row-64 street runs cols 28-66 and the climb runs col 44 from
# row 36 to row 92, so a hull (7 rows tall) standing on the long stretch must be
# based at row 71 or lower or its prow lands on the street; the east band needs
# row 74, because a second junction runs through rows 65-67 over there.
#
# AND THE COUNT IS THE POINT -- TWICE OVER. The first draft put nineteen wrecks
# across a 66-by-70-tile stretch and read as scattered; thirty-three read as a
# forest but the pieces were then twice this size and the frame was a solid wall
# of timber with no ground and no sky in it. Now that the tall pieces ship at
# half their authored height (see WorldScale), a hull is ~3 tiles wide instead of
# ~6, so the same stand needs about twice the trunks: fifty-seven, in two bands
# either side of the climb, one piece per base row so they overlap and occlude.
# Walking up col 44 should feel like walking through a wood, with the road the
# only clear line in the frame -- and the prow of every one of them in shot.
FOREST = [
    # -- WEST BAND: cols 25-42, the long stretch --------------------------
    place("the-dead-forest", "hull", 28, 96),
    place("the-dead-forest", "mast", 34, 95, flip=True),
    place("the-dead-forest", "hull", 40, 94),
    place("the-dead-forest", "hull_broken", 31, 92),
    place("the-dead-forest", "hull", 37, 91, flip=True),
    place("the-dead-forest", "hull", 26, 90),
    place("the-dead-forest", "mast", 33, 89),
    place("the-dead-forest", "hull", 39, 88, flip=True),
    place("the-dead-forest", "hull_broken", 29, 87),
    place("the-dead-forest", "hull", 36, 86),
    place("the-dead-forest", "hull", 42, 85, flip=True),
    place("the-dead-forest", "mast", 31, 84, flip=True),
    place("the-dead-forest", "hull", 38, 83),
    place("the-dead-forest", "hull", 27, 82, flip=True),
    place("the-dead-forest", "hull_broken", 34, 81),
    place("the-dead-forest", "hull", 40, 80),
    place("the-dead-forest", "hull", 30, 79, flip=True),
    place("the-dead-forest", "mast", 37, 78),
    place("the-dead-forest", "hull", 42, 77, flip=True),
    place("the-dead-forest", "hull_broken", 28, 76),
    place("the-dead-forest", "hull", 35, 75),
    place("the-dead-forest", "hull", 41, 74, flip=True),
    place("the-dead-forest", "mast", 32, 73),
    place("the-dead-forest", "hull", 39, 72, flip=True),
    place("the-dead-forest", "hull", 26, 71),
    place("the-dead-forest", "ribs", 30, 70),
    place("the-dead-forest", "ribs", 37, 69, flip=True),
    place("the-dead-forest", "ribs", 25, 68),
    # -- EAST BAND: cols 47-63. Starts higher: the rows 65-67 junction.---
    place("the-dead-forest", "hull", 49, 91),
    place("the-dead-forest", "mast", 55, 90, flip=True),
    place("the-dead-forest", "hull", 61, 89),
    place("the-dead-forest", "hull_broken", 52, 88),
    place("the-dead-forest", "hull", 58, 87, flip=True),
    place("the-dead-forest", "hull", 48, 86),
    place("the-dead-forest", "mast", 54, 85),
    place("the-dead-forest", "hull", 60, 84, flip=True),
    place("the-dead-forest", "hull_broken", 50, 83),
    place("the-dead-forest", "hull", 56, 82),
    place("the-dead-forest", "hull", 62, 81, flip=True),
    place("the-dead-forest", "mast", 51, 80, flip=True),
    place("the-dead-forest", "hull", 57, 79),
    place("the-dead-forest", "hull", 63, 78, flip=True),
    place("the-dead-forest", "hull_broken", 49, 77),
    place("the-dead-forest", "hull", 55, 76),
    place("the-dead-forest", "hull", 61, 75, flip=True),
    place("the-dead-forest", "mast", 52, 74),
    place("the-dead-forest", "ribs", 53, 72),
    place("the-dead-forest", "ribs", 59, 71, flip=True),
    place("the-dead-forest", "ribs", 49, 70),
    # -- NORTH OF THE STREET: eight, thinning. The forest should be
    #    behind him by the time he reaches the Breach. -------------------
    place("the-dead-forest", "hull", 36, 62),
    place("the-dead-forest", "hull_broken", 40, 60, flip=True),
    place("the-dead-forest", "hull", 33, 58),
    place("the-dead-forest", "mast", 38, 55, flip=True),
    place("the-dead-forest", "hull", 34, 52),
    place("the-dead-forest", "hull_broken", 40, 48, flip=True),
    place("the-dead-forest", "mast", 33, 44),
    place("the-dead-forest", "ribs", 39, 41),
]

# ---------------------------------------------------------------------------
# THE MINE THAT STAYED -- one cluster, north side of the row-64 main street
# ---------------------------------------------------------------------------
# The headframe is the anchor and everything else is arranged BY FUNCTION around
# it: the rail runs out of the shaft, the carts sit on the rail, the winch sits
# where the rope comes off the sheave, the shacks face the yard, and the lamps
# are where a person would have hung them -- at the head of the path in, and at
# the far end of the rail where you would be working in the dark. Arranged by
# function is the difference between a mine and a pile of mining-themed objects.
MINE = [
    place("the-mine-that-stayed", "headframe", 52, 62),
    place("the-mine-that-stayed", "shack", 59, 61, flip=True),
    place("the-mine-that-stayed", "shack", 48, 58),
    place("the-mine-that-stayed", "rail_bend", 51, 63),
    place("the-mine-that-stayed", "ore_cart", 56, 63),
    place("the-mine-that-stayed", "winch", 61, 63),
    place("the-mine-that-stayed", "lantern", 46, 63),
    place("the-mine-that-stayed", "rail_bend", 58, 55),
    place("the-mine-that-stayed", "ore_cart", 54, 55, flip=True),
    place("the-mine-that-stayed", "lantern", 62, 57),
]

# ---------------------------------------------------------------------------
# THE BAD GAPS -- the region's mechanic, drawn (world-bible §6.2)
# ---------------------------------------------------------------------------
# Two of them, and they are the only pieces in the region standing on the road.
# Both sit on the col-44 climb, spaced so the player crosses one early in the
# long straight and one near the top -- the two near-drops Lunal brings up at
# the Keep are "both of them the player's own hands on the controller", and this
# is the picture the player will have in mind when she does.
GAPS = [
    place("the-bad-gaps", "plank_bridge", 44, 84),
    place("the-bad-gaps", "plank_bridge", 44, 71),
]

# ---------------------------------------------------------------------------
# THE KELP -- clumps, never singles
# ---------------------------------------------------------------------------
# Kelp grows from a holdfast and spreads, so it comes in twos and threes; a lone
# frond in open ground is a houseplant. These are the region's only vertical soft
# edge -- everything else here is timber, iron, or salt.
KELP = [
    place("the-last-kelp", "kelp_stand", 20, 88),
    place("the-last-kelp", "kelp_stand", 18, 86, flip=True),
    place("the-last-kelp", "kelp_stand", 22, 90),
    place("the-last-kelp", "kelp_stand", 70, 84),
    place("the-last-kelp", "kelp_stand", 69, 82, flip=True),
    place("the-last-kelp", "kelp_stand", 72, 85),
    place("the-last-kelp", "kelp_stand", 20, 58),
    place("the-last-kelp", "kelp_stand", 22, 56, flip=True),
    place("the-last-kelp", "kelp_stand", 74, 62),
    place("the-last-kelp", "kelp_stand", 76, 60, flip=True),
    place("the-last-kelp", "kelp_stand", 52, 34),
    place("the-last-kelp", "kelp_stand", 54, 32, flip=True),
]

SHELF = FOREST + MINE + GAPS + KELP


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
        s = max(0.5, round(s * 2) / 2)  # worldScaleFor()'s half-step snap
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

    for p in SHELF:
        vig, piece, col, row = p["vignette"], p["piece"], p["col"], p["row"]
        x0, y0, x1, y1 = _box(sizes, p)
        if region(col, row) != REGION_INDEX:
            problems.append("%s %s (%d,%d): base is in region %s, not the Shelf"
                            % (vig, piece, col, row, region(col, row)))
        for c in range(int(x0 // TILE), int((x1 - 1) // TILE) + 1):
            for r in range(int(y0 // TILE), int((y1 - 1) // TILE) + 1):
                k = kind(c, r)
                if k == 1 and piece not in ROAD_OK:
                    problems.append("%s %s (%d,%d): covers ROAD tile (%d,%d)"
                                    % (vig, piece, col, row, c, r))
                if k == 2:
                    problems.append("%s %s (%d,%d): covers WATER tile (%d,%d)"
                                    % (vig, piece, col, row, c, r))

    for i, a in enumerate(SHELF):
        for b in SHELF[i + 1 :]:
            ax0, _ay0, ax1, ay1 = _box(sizes, a)
            bx0, _by0, bx1, by1 = _box(sizes, b)
            if abs(ay1 - by1) > FOOT_DEPTH:
                continue
            ow = min(ax1, bx1) - max(ax0, bx0)
            if ow <= 0:
                continue
            frac = ow / min(ax1 - ax0, bx1 - bx0)
            if frac > FOOT_TOL:
                problems.append(
                    "%s %s (%d,%d) shares ground with %s %s (%d,%d) -- %.0f%% of its width"
                    % (a["vignette"], a["piece"], a["col"], a["row"],
                       b["vignette"], b["piece"], b["col"], b["row"], frac * 100))
    return problems


def placements():
    return [
        {"vignette": p["vignette"], "key": "env_shelf_%s" % p["piece"],
         "col": p["col"], "row": p["row"], "dx": p["dx"], "dy": p["dy"],
         "scale": 1.0, "flip": p["flip"]}
        for p in SHELF
    ]


def write():
    doc = json.loads(DRESSING.read_text())
    for region in doc["regions"]:
        if region["region"] in ("saltmines", REGION_NAME):
            region["region"] = REGION_NAME
            region["placements"] = placements()
            break
    else:
        doc["regions"].append({"region": REGION_NAME, "placements": placements()})
    DRESSING.write_text(json.dumps(doc, indent=1) + "\n")
    return len(placements())


PREVIEW = ROOT / "tools" / "overworld" / ".preview"
KIND_COL = {0: (34, 44, 46), 1: (72, 66, 56), 2: (14, 30, 40), 3: (52, 58, 62), None: (8, 9, 12)}


def preview(c0=16, c1=82, r0=28, r1=98, zoom=3):
    # PAD, then crop. A 14-metre hull based on the top row of the window has its
    # prow 13 rows above the window, and `alpha_composite` refuses a negative
    # destination -- so the canvas is grown by the tallest piece in the kit and
    # cropped back at the end. Clipping the window instead would have hidden
    # exactly the pieces whose height is the thing under review.
    doc, mw, data = _map()
    sizes = _sizes()
    PAD = int(max(h for _w, h in sizes.values())) + TILE
    W, H = (c1 - c0) * TILE, (r1 - r0) * TILE
    img = Image.new("RGBA", (W + PAD * 2, H + PAD * 2))
    px = img.load()
    for c in range(c0, c1):
        for r in range(r0, r1):
            gid = data[r * mw + c]
            k = None if gid == 0 else (gid - 1) % 4
            col = KIND_COL[k] + (255,)
            for i in range(TILE):
                for j in range(TILE):
                    px[PAD + (c - c0) * TILE + i, PAD + (r - r0) * TILE + j] = col
    for p in sorted(SHELF, key=lambda t: t["row"]):
        with Image.open(KIT / ("%s.png" % p["piece"])) as src:
            src = src.convert("RGBA")
            w, h = sizes[p["piece"]]
            sp = src.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
            if p["flip"]:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        x0, y0, _x1, _y1 = _box(sizes, p)
        img.alpha_composite(sp, (PAD + int(x0) - c0 * TILE, PAD + int(y0) - r0 * TILE))
    PREVIEW.mkdir(parents=True, exist_ok=True)
    out = PREVIEW / "shelf.png"
    img = img.crop((PAD, PAD, PAD + W, PAD + H))
    img.convert("RGB").resize((W * zoom, H * zoom), Image.NEAREST).save(out)
    return out


def main(argv):
    problems = check()
    for p in problems:
        print("FAIL  %s" % p)
    if problems:
        print("\n%d problem(s) -- nothing written." % len(problems))
        return 1
    print("%d placements, all clear of roads and water." % len(SHELF))
    if "--preview" in argv or "--write" in argv:
        print("preview -> %s" % preview().relative_to(ROOT))
    if "--write" in argv:
        print("wrote %d placements -> %s" % (write(), DRESSING.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
