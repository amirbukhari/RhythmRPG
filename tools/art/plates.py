"""Cutscene stage plates -- the game's told beats, as painted images.

    python3 tools/art/plates.py [fold] [obelisk] [litho] [house] [waterline] [scar] [rain]

WHY THESE ARE GENERATED AND THE CAST IS NOT
A cutscene plate is the one thing generation is unambiguously best at: a single
full-screen static painting, no animation, no identity to hold across states, no
silhouette to keep readable at 22 pixels. Everything that made the generator the
wrong tool for Mir makes it the right tool here.

WHAT THIS REPLACES, AND WHY IT HAD TO GO
`CutsceneScene.drawStage` drew each of these as a handful of procedural shapes.
The stone child -- the image the entire premise hangs on -- was two grey circles
with two dark dots for eyes. world-bible §0 has a rule for exactly this:

    "an abstraction is not an image."

These are the moments the game DOES tell you something outright. They are the
first thing a new player sees. They cannot be two circles.

THE PROMPT BUDGET, AND THE MEASUREMENT BEHIND IT
Every prompt here is under `BUDGET` characters, and `build()` asserts it. That
is not tidiness, it is the single most important fact known about this endpoint,
measured directly (`tools/art/probe_dilution.py`):

    the same trailing clause -- "a large potted lemon tree in a terracotta pot
    stands in the centre of the room" -- renders at a 162-character prompt and
    DISAPPEARS ENTIRELY at 587, padded only with bland filler. It is still gone
    at 1012 and at 1522.

So this is dilution, not truncation: there is no cliff to stay under, the signal
just thins until it stops arriving. Long "cinematic painterly atmospheric"
preambles do not add style, they *delete subject matter* -- and they cost three
bad batches here before being measured. Every clause below is load-bearing, and
the canon-critical fact comes first. If a plate needs something more, cut
something else, do not append.

THE AUTHORED TWO
`obelisk` and `rain` are NOT generated -- see `tools/art/authored.py`. The same
split that governs the cast governs the plates: generation wins where an image is
organic and material-rich (a wet street, a bench of brass tools, a slope of
sunken hulls), and loses where it is geometric or particulate. Six batches could
not make the endpoint produce one flat vertical slab -- it returned a mountain, a
canyon, a framed painting of a canyon, and a pair of brutalist office blocks --
or a single visible falling raindrop, offering a waterfall and a mossy gorge
instead. Both of those images are a few dozen lines of PIL, exactly on canon, and
deterministic. Fighting a prior you can simply draw is a waste.

CONTRACT
Plates are 1280x720, which is native 1:1 on the 320x180-at-4x canvas
(GameConfig RENDER_SCALE), so nothing is ever upsampled. They are placed in
design space at scale 0.25.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageFilter  # noqa: E402

import authored  # noqa: E402
import gen  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites" / "cutscene"

W, H = 1280, 720

# Two style clauses, because ONE did not fit all seven plates and pretending
# otherwise cost a batch. Both are short -- see THE PROMPT BUDGET.
#
# `contract.RENDER + LIGHT + PALETTE + WORLD` (~1000 chars) is exactly the filler
# the dilution probe condemns, so none of it is used here.
#
# The PREFIX form names the medium and is what produced the shipped `fold`,
# `house` and `waterline`. Position is a volume knob: as a *tail* the same words
# lost outright and every plate came back a photographic still.
STYLE_PREFIX = "Painterly oil painting, dim desaturated light. "
# The TAIL form names NO medium at all, and exists because "oil painting" up
# front is read as an OBJECT rather than a style: it returned the obelisk as a
# framed canvas hanging on a gallery wall, put the stone child on a bright white
# gallery backdrop, and dragged `scar` and `rain` into classic oil-painting
# subjects -- a romantic valley and a waterfall. Plates whose subject the
# endpoint keeps "improving" into landscape art use this one.
STYLE_TAIL = " Dim desaturated light, heavy atmosphere."

# Total prompt ceiling, asserted in build(). The probe measured clean at 162
# chars and diluted by 587; this sits deliberately near the low end, because the
# batch at ~300 chars lost compositional detail the batch at ~200 kept.
BUDGET = 250

# ---------------------------------------------------------------------------
# One dense line per stage. These are canon, not decoration -- each cites what
# it carries, so a reroll can't quietly drift off the world-bible. The comment
# is where the detail lives now; the prompt only gets what must be in the frame.
# ---------------------------------------------------------------------------
# The complete prompt is stored per stage, style clause included, rather than
# assembled from a shared tail. That is deliberate: different plates needed
# different treatment (see the two STYLE_* constants), and a table that cannot
# reproduce the art that shipped is worse than a verbose one.
STAGES = {
    # world-bible §2: "a gothic town built in the silt around a massive
    # obelisk", "at the bottom of a lightless sea". §6.1: prayer-lamps, and the
    # player "should like it here" -- so: cared-for, not frightening.
    #
    # FRAMED UP A STREET ON PURPOSE. Asked for a town "on the deep-sea floor"
    # with a wide establishing shot, the endpoint returned a lovely moonlit
    # canal town with clouds and an open sky -- the exact opposite of the
    # premise. Negations do not remove a sky (see THE PROMPT BUDGET). Framing
    # does: a narrow street shot from the silt has no room in it for one.
    "fold": (
        STYLE_PREFIX + "A narrow street between tall salt-crusted gothic houses "
        "that fill the frame on both sides, small warm lamps in iron cages, grey "
        "silt underfoot, black water where the sky would be.",
        4411,
    ),
    # §2: "A small stone idol with an infant's face and no breath behind it."
    # THE image of the game, and the one that took the most tries:
    #   - "a small carved granite idol with the face of a sleeping infant" gave a
    #     handsome ADULT relief carving with a laurel crown; the face won and the
    #     object lost.
    #   - "swaddled infant" fixed the age but summoned newborn-photography: a
    #     real, living, pink baby.
    #   - "an alcove cut into a black wall" put it in a small box on a BRIGHT
    #     WHITE gallery wall, and a white plate is fatal under 8px text.
    # What works is naming the MATERIAL twice and the enclosure as darkness:
    # "stone carving", "colourless stone", "deep shadow surrounding it". The
    # result has no breath behind it, which is the whole line.
    "litho": (
        "A weathered stone carving of a sleeping baby's head and shoulders "
        "emerging from rough dark granite, colourless stone, one dim warm light, "
        "deep shadow surrounding it." + STYLE_TAIL,
        1503,
    ),
    # §6.1: "two parents and a sleeping boy, one packing a bag, one already out
    # the door" -- the room where the argument does not happen. Mir is a
    # clock-keeper (§5), so the room is his trade, and the BENCH leads: asking
    # for "a clock-keeper's workroom" returned an empty stone room with a bright
    # daylit window and no clock in it anywhere.
    "house": (
        STYLE_PREFIX + "A watchmaker's bench at night crowded with tiny clock "
        "gears, springs and brass tools, one oil lamp, a cramped dark stone room "
        "around it, a child's empty cot in the shadow behind.",
        6083,
    ),
    # §6.3 the Breach: the boundary, seen from below, the way the Fold sees it.
    # The hulls lead -- as a tail clause they vanished and left bare seabed.
    "waterline": (
        STYLE_PREFIX + "Rows of sunken ship hulls standing upright on a dark "
        "seabed slope like a dead forest, every prow pointing up, seen from "
        "below, pale shafts of light from the water surface far overhead.",
        3374,
    ),
    # §6.4 the Scar: the surface, and "the Scar IS his search" -- ground turned
    # over by someone looking for something. The DIGGING has to lead; as a tail
    # clause it produced a flat empty plain with no trench in it at all, and
    # "nothing green" produced green rolling hills, because negations do not
    # subtract (see THE PROMPT BUDGET). The dead things are named positively now.
    "scar": (
        "Long deep trenches and heaped earth dug in rows across a barren "
        "rust-coloured plain, pools of brown water, shattered shale, a dead "
        "tree, flat grey light." + STYLE_TAIL,
        9156,
    ),
}

def prompt_for(name):
    """The stage's full prompt and seed, exactly as it was generated."""
    return STAGES[name]


def build(name, reroll=0):
    """Render one plate. Authored stages go to the renderer; the rest are
    generated. See THE AUTHORED TWO above for why that line is where it is."""
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / ("%s.png" % name)
    if name in authored.PLATES:
        img = authored.PLATES[name](W, H)
    else:
        prompt, seed = prompt_for(name)
        if len(prompt) > BUDGET:
            raise AssertionError(
                "%s prompt is %d chars, over the %d budget -- cut something, do "
                "not append (see THE PROMPT BUDGET in this file)"
                % (name, len(prompt), BUDGET)
            )
        img = gen.generate(prompt, W, H, seed + reroll * 977)
        img = img.convert("RGB").resize((W, H), Image.LANCZOS)
        # A hair of blur before the game's own vignette and text go over the
        # top: generated plates carry high-frequency detail that fights 8px
        # type, and the plate is a BACKDROP -- it must never compete with the
        # words on it. The authored plates are built to value already, so they
        # are not blurred.
        img = img.filter(ImageFilter.GaussianBlur(0.6))
    img.convert("RGB").save(path)
    return path


def all_names():
    return list(STAGES) + [n for n in authored.PLATES if n not in STAGES]


def main(argv):
    want = argv[1:] or all_names()
    plates = []
    for name in want:
        if name not in all_names():
            print("unknown stage: %s (have: %s)" % (name, ", ".join(all_names())))
            return 2
        t = time.time()
        path = build(name)
        how = "authored" if name in authored.PLATES else "%3dch" % len(prompt_for(name)[0])
        print("%-11s %5.1fs  %-8s %s" % (name, time.time() - t, how, path.name))
        plates.append(Image.open(path))
    # the review gate (PRD §11.1.2 step 5): a batch is not shipped unlooked-at
    if plates:
        sheet = gen.contact_sheet(plates, cols=2, cell=(640, 360))
        sheet.save(OUT / "_contact.png")
        print("contact sheet -> %s" % (OUT / "_contact.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
