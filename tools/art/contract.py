"""THE FROZEN STYLE CONTRACT (PRD §11.1.2 step 2: "freeze the rules
immediately; never prompt each asset from scratch").

Every generated slot in the game is STYLE + one per-slot subject line. Nothing
prompts from scratch, so the cast reads as one game. Change this file and the
whole cast moves together -- which is the point.

Fixed at M1, derived from PRD §11.1 (painterly HD, HLD staging register) and
world-bible §11 (tone, and the hands motif).

WHAT CHANGED FROM THE OLD CONTRACT, AND WHY
  - "Pixel art / ordered dithering / crisp pixels"  -> DELETED. PRD v11.0
    retired deliberate pixelation as a style. The beauty bar is "a stranger
    shown any screenshot says 'that's a beautiful painting'."
  - "full body SIDE VIEW facing LEFT"               -> REPLACED by the
    top-down 3/4 camera clause. The game's camera looks DOWN (§7.1); side-view
    sprites are why the old cast never sat in the world.
  - "a looming Conductor" in the world clause       -> DELETED. world-bible
    v16.0 replaced him with the Harrow and moved the finale to Lunal.
  - "VIVID saturated neon" everywhere              -> TEMPERED. The register is
    a vivid *limited* palette on desaturated near-black (§11.1), not neon on
    neon; the accent has to be the emissive, or nothing reads as emissive.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# the shared clauses
# --------------------------------------------------------------------------

RENDER = (
    "beautiful painterly digital game illustration, hand-painted concept-art "
    "quality, smooth soft-edged brushwork, rich material rendering, subtle "
    "atmospheric depth. Absolutely NO pixel art, NO dithering, NO posterization, "
    "NO black outlines, NO cel-shading, NO text, NO watermark, NO signature. "
)

# The camera is PINNED. Every figure in the game is seen from the same height,
# or the cast will not stand on the same floor.
CAMERA = (
    "CAMERA IS FIXED AND MUST NOT CHANGE: seen from ABOVE at a steep "
    "three-quarter overhead game camera, roughly 55 degrees down, looking DOWN "
    "onto the subject. The top of the head and the tops of the shoulders are "
    "clearly visible; the body is foreshortened below them; the ground plane is "
    "not shown. Facing screen LEFT in profile-three-quarter. "
)

# One key light for the whole game, so every asset shares a light source.
LIGHT = (
    "LIGHTING: a single cool overcast key light from the upper LEFT, deep "
    "indigo-teal shadow on the right side, plus a narrow cool teal rim light "
    "along the silhouette edge that separates the figure from a near-black "
    "background. One small WARM EMBER-GOLD emissive accent per figure. "
)

PALETTE = (
    "PALETTE is limited and mostly desaturated: abyssal teal, slate blue-grey, "
    "cold stone, rust and oxidised copper, with ONE saturated ember-gold accent "
    "and deep indigo darks. Muted and painterly, not neon, not garish. "
)

ISOLATION = (
    "The subject is fully ISOLATED on a plain, flat, pure white background. NO "
    "ground, NO floor, NO cast shadow, NO fog, NO mist, NO vignette, NO border, "
    "NO frame, NO props beyond those described. Full body, centered, complete, "
    "not cropped. "
)

# The world clause -- for environment/prop slots that DO want context.
WORLD = (
    "World: 'The Drowned Chorus' -- a lightless drowned world of silt and salt "
    "and rust, a gothic town on the ocean floor beneath a stone obelisk, "
    "climbing to a harsh scarred surface. Beautiful-grim, quiet, and warm only "
    "where it counts. "
)

CHARACTER = RENDER + CAMERA + LIGHT + PALETTE + ISOLATION
PROP = RENDER + CAMERA + LIGHT + PALETTE + ISOLATION


# --------------------------------------------------------------------------
# scale contract -- one ground line, one set of sizes
# --------------------------------------------------------------------------
# frame: the sprite-sheet cell. figure: the painted figure's height inside it.
# Source art is generated at 768px and downsampled into these, so every slot is
# authored well above its rendered size (PRD §11.1).
#
# Rendered world height = figure_h * render_scale. Mir is the yardstick at
# 25 world px (§11.1.2), and everything else is sized in relation to HIM --
# because the story is about the difference between a man, his small son, and
# what is bigger than both.
SCALE = {
    #                frame      figure  render  world px
    "mir":          ((200, 200), 176,   0.125),  # 22.0 -- the yardstick
    "nari":         ((200, 200), 104,   0.125),  # 13.0 -- a three-year-old, chest-high to his father
    "lunal":        ((200, 200), 180,   0.125),  # 22.5 -- human-scaled on purpose (§8.7.1 #6)
    "harrow":       ((200, 200), 168,   0.125),  # 21.0 -- SMALLER than Mir; his work is what is huge
    "slime":        ((128, 128), 104,   0.25),   # 26.0
    "drifter":      ((140, 140), 122,   0.25),   # 30.5
    "elite_wraith": ((180, 180), 158,   0.25),   # 39.5
}


# --------------------------------------------------------------------------
# the cast -- canon-correct subjects (world-bible §5)
# --------------------------------------------------------------------------

SUBJECTS = {
    # ---- Mir ------------------------------------------------------------
    # canon: a clock-keeper. "sedentary, soft-handed, indoor, unfit, and
    # forty." His competence is fine motor control and refusal to stop. The
    # brass turning tool is load-bearing -- it opens the cage in the ending.
    "mir": (
        "MIR: a village CLOCK-KEEPER and a father, about forty. He is SEDENTARY "
        "and UNFIT and soft-bodied -- rounded sloping shoulders, a slight paunch, "
        "an upper back stooped from a lifetime hunched over a workbench. He is "
        "emphatically NOT a warrior, NOT muscular, NOT heroic, NOT armoured. "
        "Plain working clothes: a worn charcoal slate-teal woollen waistcoat over "
        "a pale oatmeal linen shirt with the sleeves rolled to the elbow, heavy "
        "dark trousers, scuffed leather boots. Thinning dark hair, a tired kind "
        "face, several days unshaven. His HANDS are soft, clean and careful. A "
        "small BRASS CLOCKMAKER'S TURNING TOOL hangs at his belt and glows a "
        "faint warm gold -- the one bright thing on him. "
        "NO weapon, NO sword, NO guitar, NO instrument, NO cloak, NO hood."
    ),
    # ---- Nari -----------------------------------------------------------
    # canon: "He must be *specific* -- a real toddler, not a symbol."
    # Silhouette rule: at 13 world px he has to read as A CHILD, which means
    # the head does the work.
    "nari": (
        "NARI: a real THREE-YEAR-OLD TODDLER boy, small and top-heavy with a "
        "large round head and a soft rounded belly, short stubby arms and legs, "
        "unsteady stance with his feet apart. Fine pale wispy hair. He wears a "
        "simple oversized knitted tunic-smock the colour of warm oatmeal, much "
        "too big for him, and he is BAREFOOT. He holds nothing. His expression is "
        "calm and unbothered and slightly curious. He glows very faintly warm, "
        "the only warm thing in a cold world. "
        "NOT a doll, NOT a cherub, NOT stylised chibi, NOT an older child."
    ),
    # ---- the rot slime --------------------------------------------------
    "slime": (
        "A ROT SLIME: a low heaped amorphous mound of translucent gelatinous "
        "sludge, the colour of drowned kelp and bile -- sickly desaturated "
        "green-teal, lit dimly from within so its core glows. No legs, no arms, "
        "no face, no humanoid shape whatsoever. Its surface is wet and beaded; "
        "strands of ooze drip and stretch from its rim. Fragments of silt and "
        "small bones are suspended inside it. "
        "NOT cute, NOT a cartoon slime, NOT a character, NOT smiling."
    ),
    # ---- the drowned drifter --------------------------------------------
    "drifter": (
        "A DROWNED DRIFTER: the gaunt waterlogged remains of a person who has "
        "been under a long time, still upright and still walking. A heavy "
        "salt-wracked oilskin coat, bleached and split, hanging off a frame that "
        "is too thin for it. Where the face should be there is only a dim cold "
        "teal void inside the hood. Ribbons of kelp and cloth trail from the "
        "arms and drift upward as if underwater. Barnacle crust along one "
        "shoulder. Slow, heavy, and sad rather than monstrous."
    ),
    # ---- the elite wraith ----------------------------------------------
    "elite_wraith": (
        "An ELITE WRAITH: a tall regal terrifying figure in ragged funeral robes "
        "of oxidised copper and deep indigo, far too long, trailing. A crown of "
        "pale salt-crusted bone. Long white hair drifting upward as though "
        "underwater. Beneath the crown, a narrow mask-like face with no eyes and "
        "a too-wide mouth. Thin elongated arms with long fingers. It is ONE "
        "single connected figure, imposing and vertical, with a faint ember-gold "
        "glow burning deep in its chest cavity."
    ),
}
