"""Author the Scar's dressing, and CHECK it against the real map.

    python3 tools/overworld/place_scar.py            # validate + report
    python3 tools/overworld/place_scar.py --write    # rewrite dressing.json

WHAT THIS REGION IS (world-bible §6.4)
    "The long middle, and now the region with the best secret in the game. On the
     way through, it reads as hostile country: gouged, burned, pitted,
     picked-over, with a den at the far end. Mir believes a beast took his son and
     the landscape obliges the belief. The player believes it too."
    "Then the den, and the man in it, and the ground stops being a wasteland and
     becomes a search. Everything the player crossed to get here means something
     else on the walk back out."

THE DRESSING IS THE TWIST, WHICH IS WHY THE COUNTS MATTER MORE THAN THE PIECES.
§6.4's reveal only works if the evidence was in front of the player the whole
time and they read it wrong. The evidence is SPOIL HEAPS: thirty-one of them
across this region, more than twice any other piece, because one heap of turned
earth is a molehill and thirty-one is a man who has been looking for something
here for years. On the way in they are "pitted, picked-over" -- the landscape
obliging the belief. On the way out they are the answer, and they always were.

Nothing here plants false evidence. No claw marks, no gnawed bones, no arranged
skulls -- see the rules at the top of tools/art/env_scar.py. The player is not
lied to; they just read a dug-over landscape the way a frightened man reads it.

THE FOUR STRETCHES, AND THEY FOLLOW §6.4'S OWN STRUCTURE
The eleven nodes run 09(142,170) 10(184,180) 11(218,158) 12(190,120) 13(156,98)
14(210,86) 15(252,110) 16(286,152) 17(318,128) 18(300,84) 19(264,58) -- and note
that 11->12->13->14 goes north, then WEST, then EAST again. The route physically
doubles back, which is §6.4's middle stretch ("decoys that double back") built
into the level geometry before any prop was placed. So:

  1. THE FRESH TRAIL (nodes 09-11, the southwest). "Clear prints, hope with
     teeth." Gouged and burned country and the first spoil, and NO cairns and NO
     dig equipment -- both of those are human, and the first stretch is the one
     where the player is allowed to keep believing in the beast.
  2. THE FALSE TRAILS (nodes 12-15, the double-back). The densest stretch, and
     where the CAIRNS are, because a cairn is the physical form of a pilgrim
     stride: a thing only a person makes, standing in country the player has
     decided belongs to a monster. Every one of them is the region quietly
     disagreeing. The abandoned packs are here too.
  3. THE DEN'S MOUTH (nodes 16-19, the northeast, and the way out to the Keep).
     "All tracks lead one way, none lead back." Exactly ONE `den_mouth` in the
     region -- a landmark you meet twice is scenery -- and around it a CAMP:
     windlass, dig frame, barrow, two lamps, and the heaviest concentration of
     spoil anywhere. This is the only stretch with equipment in it, and equipment
     is the reveal.
  4. THE OASIS (off the road entirely, cols 232-246 / rows 124-138). §6.4: "one
     pocket of living green ... No reward but itself, and only a player who has
     stopped hurrying will ever stand in it." It contains nothing but the three
     `oasis_*` pieces. No spoil, no char, no bones. The absence is the point --
     it is the only place in the region nobody has dug.

WHY THIS FILE USES `snap`
Regions 0-2 were placed by enumerating every legal base in a window and picking
from the list by hand. Region 3 is 43,384 tiles with eleven nodes in it, and at
that scale hand-picking stops being authorship and becomes data entry. So the
bases below are AUTHORED INTENT and `Kit.resolve` nudges each one to the nearest
legal tile within three tiles, reporting every move -- see its docstring for why
the radius is small and why every move is printed.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from place_kit import Kit, place  # noqa: E402

# Must match the scar block of WorldScale.METERS. The kit is authored at 32 px
# per intended tile, so `metres == tiles` here -- see env_scar.py's SIZE
# CONVENTION note.
METERS = {
    "burnt_spar": 6.0,
    "den_mouth": 5.5,
    "dig_frame": 4.5,
    "burnt_stand": 3.5,
    "windlass": 3.0,
    "oasis_shoot": 2.8,
    "cairn": 2.6,
    "spoil_heap": 1.6,   # 130x48: at 2.4 on a 76px canvas the slope was 50deg, i.e. a mountain
    "dig_lamp": 2.2,
    "bone_pile": 2.0,
    "barrow": 1.6,
    "oasis_spring": 1.4,
    "pilgrim_pack": 0.8,   # it LIES FLAT (46x24 canvas), so 1.4 was sizing the object by air
    "trench": 1.2,
    "oasis_rill": 1.0,
}
# Nothing in this kit crosses the road and nothing stands in water. The Fold's
# arch and the Breach's duckboards had a reason (a thing whose whole meaning is
# that it spans the route cannot be kept off the route); a spoil heap in the
# middle of the path is just an obstacle nobody can walk round.
KIT = Kit(region_index=3, biome="scar", meters=METERS)


# ---------------------------------------------------------------------------
# 1. THE FRESH TRAIL -- nodes 09-11, the southwest. "Hope with teeth."
# ---------------------------------------------------------------------------
# Gouged and burned, and the burning is what carries it: this is the first
# stretch of surface the player has ever seen and the first thing it says is that
# something happened here. The spoil is present but THIN -- five heaps, spread --
# so that the density climbing through stretch 2 and peaking at the camp reads as
# a gradient the player is walking up rather than a texture.
FRESH_TRAIL = [
    place("the-fresh-trail", "burnt_spar", 150, 166),
    place("the-fresh-trail", "burnt_stand", 137, 176, flip=True),
    place("the-fresh-trail", "trench", 158, 174),
    place("the-fresh-trail", "spoil_heap", 148, 180),
    place("the-fresh-trail", "burnt_stand", 166, 162),
    place("the-fresh-trail", "bone_pile", 155, 184),
    place("the-fresh-trail", "burnt_spar", 172, 176, flip=True),
    place("the-fresh-trail", "spoil_heap", 178, 170),
    place("the-fresh-trail", "trench", 190, 174),
    place("the-fresh-trail", "burnt_stand", 196, 184, flip=True),
    place("the-fresh-trail", "burnt_spar", 192, 166),
    place("the-fresh-trail", "spoil_heap", 202, 178),
    place("the-fresh-trail", "bone_pile", 186, 186),
    place("the-fresh-trail", "burnt_stand", 208, 168),
    place("the-fresh-trail", "trench", 214, 176, flip=True),
    place("the-fresh-trail", "spoil_heap", 220, 166),
    place("the-fresh-trail", "burnt_spar", 224, 152, flip=True),
    place("the-fresh-trail", "burnt_stand", 212, 148),
    place("the-fresh-trail", "spoil_heap", 206, 154),
    place("the-fresh-trail", "trench", 200, 160),
    place("the-fresh-trail", "burnt_stand", 176, 156, flip=True),
    place("the-fresh-trail", "burnt_spar", 164, 150),
    place("the-fresh-trail", "bone_pile", 170, 146),
    place("the-fresh-trail", "spoil_heap", 144, 158),
    place("the-fresh-trail", "burnt_stand", 152, 152),
    place("the-fresh-trail", "trench", 138, 164, flip=True),
]

# ---------------------------------------------------------------------------
# 2. THE FALSE TRAILS -- nodes 12-15, the double-back. The densest stretch.
# ---------------------------------------------------------------------------
# THE CAIRNS ARE THE ARGUMENT AND THERE ARE NINE OF THEM. §6.4's "pilgrim
# strides" made physical: nine markers, built by hand, in country the player has
# decided belongs to a beast. They are also all LEANING (the piece is authored
# going over), which is the second half of the story -- whoever built them is not
# coming back to straighten them.
#
# The packs are here for the same reason and the opposite effect: a cairn says
# somebody came through, a dropped pack says somebody did not come back, and the
# player is meant to take the second reading. They will be wrong about it, but
# not because anything here lied.
FALSE_TRAILS = [
    # -- the leg north out of node_11, cols 186-200
    place("the-false-trails", "cairn", 194, 142),
    place("the-false-trails", "spoil_heap", 186, 136),
    place("the-false-trails", "burnt_spar", 198, 132, flip=True),
    place("the-false-trails", "trench", 184, 128),
    place("the-false-trails", "cairn", 196, 124),
    place("the-false-trails", "pilgrim_pack", 188, 122),
    place("the-false-trails", "spoil_heap", 200, 116),
    place("the-false-trails", "burnt_stand", 182, 114),
    place("the-false-trails", "bone_pile", 194, 112),
    # -- the leg WEST to node_13. This is the double-back, and it is where the
    #    cairns cluster: three inside ten tiles, all pointing different ways.
    place("the-false-trails", "cairn", 176, 108),
    place("the-false-trails", "cairn", 170, 104, flip=True),
    place("the-false-trails", "cairn", 180, 100),
    place("the-false-trails", "spoil_heap", 166, 110),
    place("the-false-trails", "trench", 172, 96, flip=True),
    place("the-false-trails", "burnt_spar", 160, 106),
    place("the-false-trails", "pilgrim_pack", 162, 100),
    place("the-false-trails", "burnt_stand", 150, 104, flip=True),
    place("the-false-trails", "spoil_heap", 152, 94),
    place("the-false-trails", "bone_pile", 146, 100),
    # -- the leg back EAST to node_14, which the player has already walked once
    place("the-false-trails", "cairn", 188, 92),
    place("the-false-trails", "spoil_heap", 194, 90),
    place("the-false-trails", "trench", 200, 94),
    place("the-false-trails", "burnt_stand", 204, 90, flip=True),
    place("the-false-trails", "cairn", 216, 92),
    place("the-false-trails", "pilgrim_pack", 210, 96),
    place("the-false-trails", "burnt_spar", 226, 93),
    place("the-false-trails", "spoil_heap", 228, 94),
    place("the-false-trails", "bone_pile", 234, 90, flip=True),
    # -- the leg southeast to node_15
    place("the-false-trails", "cairn", 240, 100),
    place("the-false-trails", "spoil_heap", 246, 104),
    place("the-false-trails", "trench", 234, 106, flip=True),
    place("the-false-trails", "burnt_stand", 256, 106),
    place("the-false-trails", "cairn", 248, 116),
    place("the-false-trails", "spoil_heap", 258, 118),
    place("the-false-trails", "pilgrim_pack", 242, 120),
    place("the-false-trails", "burnt_spar", 264, 114, flip=True),
]

# ---------------------------------------------------------------------------
# 3. THE DEN'S MOUTH -- nodes 16-19, and the way out to the Keep.
# ---------------------------------------------------------------------------
# THE ONLY STRETCH WITH EQUIPMENT IN IT, and equipment is the reveal. A windlass,
# a dig frame, a barrow and two burning lamps are not things a beast owns, and by
# the time the player is close enough to read them they are already committed to
# the monster story -- which is exactly the position §6.4 wants them in when they
# meet him.
#
# THE SPOIL PEAKS HERE: eleven heaps and four trenches inside forty tiles, after
# five in stretch 1 and eight in stretch 2. The player has been walking up that
# gradient for the whole region without being told it was a gradient.
#
# EXACTLY ONE `den_mouth`, at the north end past node_18, because it is the last
# thing in the region and a landmark you meet twice is scenery.
DENS_MOUTH = [
    # -- the approach up the col-288 road from node_16
    place("the-dens-mouth", "spoil_heap", 282, 146),
    place("the-dens-mouth", "trench", 292, 140),
    place("the-dens-mouth", "burnt_spar", 280, 134),
    place("the-dens-mouth", "spoil_heap", 294, 128),
    place("the-dens-mouth", "cairn", 284, 122),
    place("the-dens-mouth", "spoil_heap", 296, 116),
    place("the-dens-mouth", "burnt_stand", 282, 110, flip=True),
    place("the-dens-mouth", "trench", 294, 104),
    place("the-dens-mouth", "spoil_heap", 284, 100),
    # -- THE EASTERN CUT, past node_18 toward node_17. A man who has been at this
    #    for years has dug in more than one place, and this is the one he gave up
    #    on: equipment left in it, no lamp, and the spoil already settling.
    place("the-dens-mouth", "dig_frame", 306, 92),
    place("the-dens-mouth", "spoil_heap", 303, 95),
    place("the-dens-mouth", "trench", 313, 88),
    place("the-dens-mouth", "spoil_heap", 313, 80),
    place("the-dens-mouth", "barrow", 305, 79),
    place("the-dens-mouth", "spoil_heap", 308, 73),
    place("the-dens-mouth", "burnt_stand", 316, 83, flip=True),
    # -- THE CAMP, and it is AT the den's mouth, not near it. Read it as one
    #    man's working area, because it is one: the winch over the shaft he is
    #    actually sinking, the frame he moved here from the eastern cut, a barrow
    #    left where he put it down, and two lamps still burning.
    #    AND IT FITS ONE CAMERA. The first pass had the den based at row 67 and
    #    the frame at row 79 -- twelve rows apart in a viewport that shows ELEVEN,
    #    so the den and the equipment that explains it could never be in the same
    #    frame, and the whole point of the camp is that the player reads them
    #    together. Everything here is now inside rows 68-76.
    place("the-dens-mouth", "windlass", 296, 73),
    place("the-dens-mouth", "dig_lamp", 293, 70),
    place("the-dens-mouth", "barrow", 298, 70, flip=True),
    place("the-dens-mouth", "spoil_heap", 288, 72),
    place("the-dens-mouth", "dig_frame", 286, 76),
    place("the-dens-mouth", "dig_lamp", 284, 71),
    place("the-dens-mouth", "trench", 292, 76),
    place("the-dens-mouth", "spoil_heap", 298, 77),
    place("the-dens-mouth", "spoil_heap", 283, 68),
    # -- THE DEN ITSELF, and the col-288 road DEAD-ENDS AT IT. That is not a
    #    coincidence I arranged after the fact: the road runs from node_16 all the
    #    way up the region and stops here, which is §6.4's "all tracks lead one
    #    way, none lead back" written in the level's own geometry.
    place("the-dens-mouth", "den_mouth", 290, 67),
    place("the-dens-mouth", "spoil_heap", 296, 64),
    place("the-dens-mouth", "pilgrim_pack", 296, 68),
    place("the-dens-mouth", "trench", 292, 62),
    # -- the walk out to the Keep, past node_19, and it thins to nothing
    place("the-dens-mouth", "spoil_heap", 284, 61),
    place("the-dens-mouth", "burnt_stand", 276, 62, flip=True),
    place("the-dens-mouth", "cairn", 270, 56),
    place("the-dens-mouth", "burnt_spar", 262, 62),
]

# ---------------------------------------------------------------------------
# 4. THE OASIS -- off the road, and it contains NOTHING ELSE.
# ---------------------------------------------------------------------------
# §6.4: "one pocket of living green -- warm moss, a clear spring, and visible
# growth, new shoots, something in bud. The only place in the game where anything
# is in motion. No reward but itself, and only a player who has stopped hurrying
# will ever stand in it."
#
# So it is small, it is fourteen tiles off the nearest road, and the ONLY pieces
# in it are the three `oasis_*` ones. That absence is doing as much work as the
# green is: every other pocket of ground in this region has been turned over by
# somebody, and this is the one nobody has dug. A single spoil heap at the edge
# of it would say a man had been here and decided to leave it alone, which is a
# nicer thought and a worse one, because it makes the Oasis about him. It is not.
# It is about the player choosing to stop.
OASIS = [
    # THE OASIS IS THE ONE PLACE IN THIS REGION THE PLAYER DOES NOT HAVE TO
    # FIND, and the first cut of it was eight placements of three pieces --
    # a spring, three copies of the moss, four of the shoots -- which came back
    # in-engine as four identical green mounds around a grey slab. Two things
    # were wrong and only one of them was the art:
    #
    #   * THREE PIECES CANNOT DRESS A PLACE. They can only tile it. -- AND THEN
    #     I MADE FIVE AND TWO OF THEM WERE ANIMALS. `oasis_fern` came back a
    #     SPIDER twice and `oasis_moss` came back BROCCOLI, and both are gone
    #     (tools/art/env_scar.py's PIECES note has the post-mortem). The answer
    #     was never more botany. A pocket of green is dressed by what it does to
    #     the GROUND -- the district under it carries the colour -- plus three
    #     shapes the region does not otherwise contain: still water, a thread of
    #     it running out, and nine straight vertical stems.
    #   * IT HAD NO WAY IN. §6.4: "only a player who has stopped hurrying will
    #     ever stand in it" -- which is a statement about ATTENTION, not about
    #     the map hiding it. A player who has stopped hurrying has to be given
    #     something to notice, and what they notice is the overflow: four rill
    #     segments running downhill to the south-west, OUT of the green district
    #     and onto bare brown ground, getting thinner as they go. Follow the
    #     water uphill and you arrive. That is the only navigation in the game
    #     that is not a road, and it is the only reason the Oasis can be found
    #     from the wrong side.
    #
    # AND IT FITS ONE CAMERA. Cols 228-247, rows 125-135 -- nineteen by eleven,
    # which is the viewport (20x11) with a tile to spare. The one place in the
    # region that is meant to be RESTFUL cannot be a place you have to pan
    # around to take in. The rill trail is the only part that leaves the frame,
    # and it leaves it deliberately, downhill and westward, the way you came.
    #
    # ALMOST NOTHING MADE IS IN HERE, AND THE EXCEPTION IS THE POINT. The first
    # cut had none at all -- no cairn, no pack, no lamp, not one spoil heap, and
    # there are thirty-one of those within two screens of it -- on the argument
    # that §6.4's "no reward but itself" means the absence IS the reward. That is
    # nearly right and it undersells the region. This is the place people came
    # looking for and did not come back from; an empty garden is pretty, and one
    # pack set down beside the water by somebody who rested here and then went
    # on up is the same image with a person in it. So there is exactly ONE made
    # thing. Two would be a camp, and a camp has a fire and a story and other
    # people in it, and then the pocket is somewhere you arrive rather than
    # somewhere you are the first to stand in a hundred years.
    place("the-oasis", "oasis_spring", 238, 131),
    # THE ONE MADE THING. Set down at the water's edge, not dropped, not spilled
    # -- and never picked up. It is the smallest sprite in the pocket and it is
    # the only one the player will remember.
    place("the-oasis", "pilgrim_pack", 234, 134),
    # the shoots, at the edges where the light gets in. One of them is in bud,
    # and it is the only object in this game that will be different next week.
    place("the-oasis", "oasis_shoot", 235, 128),
    place("the-oasis", "oasis_shoot", 241, 127, flip=True),
    place("the-oasis", "oasis_shoot", 243, 133),
    place("the-oasis", "oasis_shoot", 230, 132, flip=True),
    # THE THREAD OUT. Downhill, south-west, thinning -- the last one is on bare
    # ground with the green almost gone off it. Follow the water uphill and you
    # arrive; it is the only navigation in the game that is not a road.
    place("the-oasis", "oasis_rill", 233, 133),
    place("the-oasis", "oasis_rill", 228, 134, flip=True),
    place("the-oasis", "oasis_rill", 223, 135),
    place("the-oasis", "oasis_rill", 218, 136, flip=True),
]

SCAR = FRESH_TRAIL + FALSE_TRAILS + DENS_MOUTH + OASIS

if __name__ == "__main__":
    # the preview window frames the camp and the den, which is the stretch whose
    # composition is doing the most work
    raise SystemExit(KIT.main(sys.argv, SCAR, preview_window=(272, 322, 58, 100), snap=3))
