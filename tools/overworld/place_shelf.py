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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from place_kit import Kit, place  # noqa: E402

# The metres MUST match the shelf block of WorldScale.METERS -- the engine's scale
# wins over any authored one, so the footprint maths has to use the engine's
# number. This is the one table still duplicated on purpose: it is small, every
# entry is exercised against the shipped PNG by `Kit._sizes`, and importing
# TypeScript from Python is not a trade worth making.
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
# Pieces allowed to stand ON a road. Only the plank bridge: it is a crossing, and
# §6.2's "bad gaps" are gaps in the way the player is actually walking. The rest
# of the rules live in place_kit.py, which is now the single copy of them.
KIT = Kit(region_index=1, biome="shelf", meters=METERS, road_ok={"plank_bridge"})

# ---------------------------------------------------------------------------
# THE DEAD FOREST -- a stand of fifty-seven, flanking the col-44 climb
# ---------------------------------------------------------------------------
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

if __name__ == "__main__":
    # the window frames the climb, the mine, and the northward thinning
    raise SystemExit(KIT.main(sys.argv, SHELF, preview_window=(16, 82, 28, 98)))
