"""The master palette. Every authored colour in the game comes from here.

"One palette, five moods" (PRD §11.1.1) only holds if the palette is a single
shared object rather than a note in a doc, so this module IS the discipline:
characters and props pull named colours, and each region pulls a dominant hue
that tints its own dressing.

Values are the canon accents already live in the engine (`WorldFight`'s accent
table, `FinaleScene`'s parchment) so authored art and runtime FX agree.
"""

from __future__ import annotations

# ---- ground values -------------------------------------------------------
ABYSS = (5, 6, 10)  # near-black, the depths
INK = (15, 17, 26)
SLATE = (28, 31, 43)
STONE = (97, 110, 122)

# ---- the five region hues (§8.8.1) --------------------------------------
FOLD = (73, 198, 189)  # abyssal teal   -- the drowned town
KELP = (108, 168, 116)  # kelp green     -- the climb
BREACH = (216, 206, 182)  # sand / foam  -- the waterline
SCAR = (194, 84, 36)  # blood / rust     -- the surface
KEEP = (142, 123, 181)  # storm violet   -- the hall

# ---- warm / emissive ----------------------------------------------------
EMBER = (244, 210, 122)  # the one warm accent; Mir's tool, prayer-lamps
BRASS = (198, 152, 78)
PARCHMENT = (216, 206, 182)
BLOOD = (194, 47, 52)

# ---- Mir, the clock-keeper ----------------------------------------------
# Cold clothes, one warm tool: he carries the only warm thing in the world,
# and it is the thing that opens the cage (world-bible §8).
MIR_COAT = (34, 50, 58)  # deep slate-teal waistcoat -- the silhouette
MIR_SHIRT = (96, 95, 86)  # oatmeal linen, WORN and dirty. See note below.
# At 22 world px only three values survive: ground, silhouette, accent. The
# first pass gave the shirt luma 132 across the whole upper arm and chest, so
# Mir read as a pale smudge with no silhouette at all. The shirt is now a dim
# mid-dark; only the COLLAR keeps the clean linen value, as a single small
# bright note at the throat where the eye already goes to read the head.
MIR_LINEN = (170, 166, 150)
MIR_TROUSER = (26, 31, 41)
MIR_BOOT = (46, 40, 38)
MIR_SKIN = (150, 116, 98)
MIR_SKIN_DARK = (110, 84, 72)
MIR_HAIR = (34, 30, 32)

# ---- Nari ---------------------------------------------------------------
# Faintly warm: the only warm living thing, so he reads instantly at 13px.
NARI_SMOCK = (166, 148, 118)  # a value step below his skin, or he reads as one
# featureless warm lozenge at 13px and the head stops being a head
NARI_SKIN = (214, 176, 150)
NARI_HAIR = (150, 128, 104)
NARI_SKIN_LEG = (196, 158, 134)  # bare shins below the smock -- he is barefoot

# ---- foes ---------------------------------------------------------------
# Sickly BILE green, deliberately lighter and yellower than the Fold's ground
# teal. The first pass was (86,122,84) -- the same value and nearly the same
# hue as the drowned town's silt, so a rot slime standing on Fold ground was
# invisible until it moved. A foe has to separate from every ground it fights
# on; hue alone never does that, value has to.
SLIME_BODY = (124, 152, 86)
SLIME_CORE = (196, 226, 132)
DRIFTER_COAT = (72, 68, 60)
DRIFTER_VOID = (60, 150, 150)
WRAITH_ROBE = (92, 84, 112)
WRAITH_BONE = (214, 208, 190)

# ---- Lunal & the Harrow (the finale, §8.7) ------------------------------
# Lunal reads as Mir's own palette gone cold and certain -- same family,
# no warmth at all. The mask is the only pale shape on her (it comes off in P3).
LUNAL_COAT = (48, 56, 78)
LUNAL_MASK = (206, 198, 178)
LUNAL_SKIN = (184, 148, 130)
# The Harrow is the colour of the ground he has been turning over.
HARROW_RAG = (86, 62, 46)
HARROW_HAND = (156, 96, 74)  # ruined past use -- the hands arc


def tint(col, hue, amount):
    """Pull a colour toward a region hue -- how one palette becomes five moods."""
    return tuple(int(c * (1.0 - amount) + h * amount) for c, h in zip(col, hue))
