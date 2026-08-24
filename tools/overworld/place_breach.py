"""Author the Breach's dressing, and CHECK it against the real map.

    python3 tools/overworld/place_breach.py            # validate + report
    python3 tools/overworld/place_breach.py --write    # rewrite dressing.json

WHAT THIS REGION IS (world-bible §6.3, and it is two things at once):
    "The waterline, staged as a carnival that kept performing after the water
     came. Mir crosses and takes his first breath of surface air; it is agony
     and it is the best moment of his life."
    "**Then the taking** (scripted). He turns for one measure and the boy is
     gone. No blood. No struggle worth the name. Nari did not cry out."

So the layout has to be CHEERFUL first. Not ironic, not ominous -- actually
cheerful, laid out the way a midway is laid out, with the attractions facing the
walk and the bunting strung over the player's head. Region 2 is where the game
stops being underwater and the boy is still holding his father's hand, and if the
player does not have one genuinely nice minute here then the taking is just
another bad thing in a row of bad things.

THREE DECISIONS FOLLOW FROM THAT:

  1. THE WHEEL IS SINGULAR AND IT IS THE FIRST THING. A landmark you meet twice
     is scenery. He enters region 2 by stepping SOUTH off the long row-70
     boundary street onto the col-102 spine, and the wheel stands in the open
     ground immediately east of it (cols 106-115, rows 76-84) -- nine tiles tall
     in an eleven-tile camera, so it fills the right of frame for the first
     eight rows he walks and there is exactly one of it.
  2. THE MIDWAY FACES THE ROAD. The spine runs col 102/103 from row 71 down to
     the row-98 cross-street, and every booth, kiosk and stall is on its flanks
     with its front toward it -- densely on the east, where the ground is open
     for twenty columns, and thinly on the five-tile west shoulder (cols 94-100)
     so the walk has a side to it rather than a wall. The bunting is strung
     ACROSS the spine (see `road_ok`) at rows 74 and 83 and across the
     cross-street at row 98; bunting that does not cross the way the player is
     walking is a washing line.
  3. THE TAKING SITE IS THE QUIETEST PLACE IN THE REGION. It is off the midway
     entirely -- east of the col-122 road at rows 115-124, on the way down to
     node_07 -- four pieces, NO bulbs, nothing broken in a way that suggests a
     struggle. §6.3 is explicit: "No blood. No struggle worth the name." The one
     thing there that is wrong is the swing boat, stopped twenty degrees off
     plumb, which a pendulum cannot do on its own and which nothing in the frame
     explains. Everything else is just a carnival with nobody in it.

THE ROUTE, BECAUSE EVERY VIGNETTE IS PLACED AGAINST IT:
    row 70 boundary street -> col 102/103 spine south (rows 71-97) -> node_06
    (104,98) at the cross-street -> east on row 98 to col 116/122 -> south on
    col 122 (rows 99-128), passing the taking site -> node_07 (122,128) -> west
    to the col 97/98 road -> south (rows 130-166) past node_08 (98,150) and out
    to the Scar. The camera is twenty columns wide, so a piece more than ten
    columns off the road is scenery the player will never resolve; nothing here
    is further out than that except the wheel, which is meant to be seen from
    across the region.

Region 2 is cols 78-145, rows 67-171, with 359 WATER tiles through it as
standing pools -- this is the waterline, so the water is arriving rather than
sitting, and the duckboards go OVER it, not beside it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from place_kit import Kit, place  # noqa: E402

# Must match the breach block of WorldScale.METERS. The kit is authored at 32 px
# per intended tile, so `metres == tiles` here and the world scale lands on its
# 0.5 floor every time -- see the note in WorldScale.ts.
METERS = {
    "wheel": 9.0,
    "tent_pole": 5.5,
    "carousel": 5.0,
    "strength_tester": 4.5,
    "swing_boat": 4.0,
    "tent": 3.2,
    "ticket_booth": 2.8,
    "booth": 2.6,
    "festoon_lamp": 2.2,
    "bunting": 2.0,
    "carousel_horse": 1.6,
    "boardwalk": 0.8,
}
# Bunting is strung OVER the way in; duckboards ARE the way across the water.
# Both exemptions are the same shape as the Fold's arch: a thing whose whole
# meaning is that it spans the route cannot be kept off the route.
KIT = Kit(region_index=2, biome="breach", meters=METERS,
          road_ok={"bunting", "boardwalk"}, water_ok={"boardwalk"})

# ---------------------------------------------------------------------------
# THE MIDWAY -- flanking the col-102/103 spine, rows 71-98
# ---------------------------------------------------------------------------
# Read it north-to-south, which is the way he walks it: he comes off the row-70
# boundary street into bunting, passes the ticket kiosk, and the wheel is on his
# left shoulder for eight rows. Then the stalls thicken, then the cross-street.
#
# THE WHEEL'S FOOTPRINT IS KEPT EMPTY, and that is not fastidiousness. The
# overworld depth-sorts on base row, so anything based ABOVE the wheel's row 84
# draws BEHIND it -- a booth tucked in among the wheel's legs at row 79 does not
# read as depth, it reads as a booth that has been deleted. The nine-by-nine box
# at cols 106-115, rows 76-84 has nothing else in it.
MIDWAY = [
    # -- the way in: off the boundary street, under the bunting
    place("the-midway", "bunting", 103, 74),
    place("the-midway", "ticket_booth", 107, 74),
    place("the-midway", "festoon_lamp", 106, 73),
    place("the-midway", "carousel_horse", 112, 72),
    place("the-midway", "booth", 113, 73, flip=True),

    # -- the wheel, and nothing else inside its box
    place("the-midway", "wheel", 111, 84),
    place("the-midway", "festoon_lamp", 105, 87),
    place("the-midway", "festoon_lamp", 116, 87, flip=True),

    # -- the east plain: the fair proper, two ranks deep
    place("the-midway", "carousel", 118, 90),
    place("the-midway", "carousel_horse", 112, 91),
    place("the-midway", "tent", 121, 86),
    place("the-midway", "tent_pole", 123, 90, flip=True),
    place("the-midway", "booth", 118, 82, flip=True),
    place("the-midway", "ticket_booth", 122, 81),
    place("the-midway", "festoon_lamp", 118, 94, flip=True),
    place("the-midway", "carousel_horse", 124, 93, flip=True),
    place("the-midway", "booth", 116, 95),
    place("the-midway", "strength_tester", 110, 97),
    place("the-midway", "festoon_lamp", 114, 97),

    # -- the west shoulder: five tiles wide, so four pieces and no more
    place("the-midway", "booth", 95, 85, flip=True),
    place("the-midway", "festoon_lamp", 97, 86, flip=True),
    place("the-midway", "carousel_horse", 97, 90, flip=True),
    place("the-midway", "ticket_booth", 96, 93, flip=True),

    # -- strung across the walk, twice on the spine and once on the cross-street
    place("the-midway", "bunting", 103, 83),
    place("the-midway", "bunting", 113, 98),
]

# ---------------------------------------------------------------------------
# THE WATERLINE -- duckboards where the pools are
# ---------------------------------------------------------------------------
# These are placed AT the water, not near it. A boardwalk beside a puddle is a
# pallet; a boardwalk over one is a decision somebody made -- and duckboards over
# standing water is the entire reason duckboards exist, which is why `boardwalk`
# is the one piece in the kit exempt from BOTH the road and the water rule.
# Every base below was picked off a list of tiles whose footprint actually
# OVERLAPS a water tile; there are no dry ones in here.
WATERLINE = [
    place("the-waterline", "boardwalk", 103, 91),
    place("the-waterline", "boardwalk", 105, 96),
    place("the-waterline", "boardwalk", 105, 102),
    place("the-waterline", "boardwalk", 106, 108),
    place("the-waterline", "boardwalk", 100, 113),
    place("the-waterline", "boardwalk", 110, 123),
    place("the-waterline", "boardwalk", 103, 130),
]

# ---------------------------------------------------------------------------
# WHERE HE TURNED -- the taking (§6.3). Four pieces, no bulbs.
# ---------------------------------------------------------------------------
# East of the col-122 road at rows 115-124, which is on the way down to node_07
# and off the midway entirely. Deliberately thin, deliberately unlit. The player
# should be able to walk past here and notice nothing, and then have to come back
# to it in memory. The only wrong note in the frame is the swing boat.
TAKING = [
    place("where-he-turned", "swing_boat", 130, 119),
    place("where-he-turned", "tent_pole", 135, 117),
    place("where-he-turned", "carousel_horse", 128, 120),
    place("where-he-turned", "booth", 133, 123),
]

# ---------------------------------------------------------------------------
# THE FAR END -- the walk out, toward the Scar
# ---------------------------------------------------------------------------
# Along the col-97/98 road, rows 138-160, and it is thinner than the midway with
# the lights LEFT ON. §6.3: everything after this is after the taking. The
# carnival is unchanged; he is not, and the only way to say that with props is to
# leave the props exactly as cheerful as they were. So: bulbs still burning, a
# ride still standing, bunting still up over the last street he walks.
FAR_END = [
    place("the-far-end", "ticket_booth", 102, 139),
    place("the-far-end", "festoon_lamp", 90, 141),
    place("the-far-end", "booth", 105, 141, flip=True),
    place("the-far-end", "strength_tester", 87, 143),
    place("the-far-end", "carousel_horse", 107, 143, flip=True),
    place("the-far-end", "festoon_lamp", 104, 145, flip=True),
    place("the-far-end", "tent", 89, 146),
    place("the-far-end", "bunting", 101, 150),
    place("the-far-end", "carousel", 112, 158),
    place("the-far-end", "festoon_lamp", 110, 156),
    place("the-far-end", "tent_pole", 116, 159, flip=True),
]

BREACH = MIDWAY + WATERLINE + TAKING + FAR_END

if __name__ == "__main__":
    raise SystemExit(KIT.main(sys.argv, BREACH, preview_window=(94, 132, 70, 100)))
