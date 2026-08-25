"""Mir -- the clock-keeper. Rig, poses, and the full animation set.

CANON THIS RIG IS BUILT TO CARRY (world-bible §5, PRD §8.4)
  * "sedentary, soft-handed, indoor, unfit, and forty" -- so: sloping
    shoulders, a real paunch, a stooped upper back, short stride, no heroic
    silhouette anywhere. He should look wrong for this from the first frame.
  * "His only real competence is that he does not stop" -- so his run is
    laboured and his recoveries are slow, but nothing ever knocks him over
    permanently.
  * "The hands." (§11 "Tone") The one visual arc that runs the whole game:
    clean and precise at the Fold, ruined by the Keep. The hands are separate
    shapes with their own colour so a later stage can darken and thicken them
    without touching the rest of the figure -- see `hands_wear`.
  * The brass turning tool is on his belt in EVERY frame, emissive, because it
    is what opens the cage in the ending and the player has to have been
    looking at it for three hours.

Figure space: origin between the feet, +y up, +x screen-left (the facing).
"""

from __future__ import annotations

import palette as P
from rig import Blob, Clip, Joint, Limb, Painter, Poly, Skeleton, mul_scale

# --------------------------------------------------------------------------
# proportions -- 176px figure, deliberately unheroic (~5.8 heads)
# --------------------------------------------------------------------------
H = 176.0
HEAD_R = 13.2
PELVIS_Y = 74.0
CHEST_Y = 112.0


def skeleton():
    return Skeleton(
        [
            # root at the pelvis; a slight forward lean lives in `spine`
            Joint("pelvis", None, (0.0, PELVIS_Y), 0.0, 0.0),
            Joint("spine", "pelvis", (0.0, 0.0), -6.0, CHEST_Y - PELVIS_Y),
            Joint("neck", "spine", (0.0, 0.0), -8.0, 14.0),
            Joint("head", "neck", (0.0, 0.0), 4.0, 0.0),
            # arms: shoulders sit low and forward (the slump)
            Joint("shoulder_f", "spine", (3.0, -4.0), 172.0, 30.0),
            Joint("elbow_f", "shoulder_f", (0.0, 0.0), 12.0, 27.0),
            Joint("hand_f", "elbow_f", (0.0, 0.0), 0.0, 0.0),
            Joint("shoulder_b", "spine", (-7.0, -6.0), 186.0, 29.0),
            Joint("elbow_b", "shoulder_b", (0.0, 0.0), 10.0, 26.0),
            Joint("hand_b", "elbow_b", (0.0, 0.0), 0.0, 0.0),
            # legs
            Joint("hip_f", "pelvis", (4.0, -2.0), 178.0, 38.0),
            Joint("knee_f", "hip_f", (0.0, 0.0), 4.0, 34.0),
            Joint("foot_f", "knee_f", (0.0, 0.0), 0.0, 0.0),
            Joint("hip_b", "pelvis", (-5.0, -3.0), 182.0, 37.0),
            Joint("knee_b", "hip_b", (0.0, 0.0), 5.0, 33.0),
            Joint("foot_b", "knee_b", (0.0, 0.0), 0.0, 0.0),
            # the tool, on the belt, always visible
            Joint("belt", "pelvis", (7.0, 4.0), 0.0, 0.0),
        ]
    )


def shapes(hand_col=P.MIR_SKIN, hand_w=1.0):
    """The painted body. `hand_col`/`hand_w` drive the hands arc."""
    s = []
    # ---- back limbs (behind the torso) ----
    s.append(Limb("shoulder_b", _dim(P.MIR_SHIRT), 30, 15, 12, z=-20))
    s.append(Limb("elbow_b", _dim(P.MIR_SKIN_DARK), 26, 11, 9, z=-19))
    s.append(Blob("hand_b", _dim(hand_col), 6.0 * hand_w, 7.0 * hand_w, z=-18))
    s.append(Limb("hip_b", _dim(P.MIR_TROUSER), 37, 19, 15, z=-16, rim=0.5))
    s.append(Limb("knee_b", _dim(P.MIR_TROUSER), 33, 14, 11, z=-15, rim=0.5))
    s.append(Poly("foot_b", _dim(P.MIR_BOOT), [(-7, 0), (13, 0), (13, -8), (-7, -8)], z=-14, rim=0.4))

    # ---- torso ----
    # The torso is the WAISTCOAT (dark), not the shirt: he has to read as a
    # dark silhouette with a pale collar, or he disappears against the Fold's
    # pale silt paths. The first pass made the shirt the whole torso and he
    # read as a man wearing a sandwich board.
    s.append(Limb("spine", P.MIR_COAT, CHEST_Y - PELVIS_Y, 34, 29, z=0))
    # the stoop, as a SHAPE and not just an angle: a rounded mass on the upper
    # back. "an upper back stooped from a lifetime hunched over a workbench"
    # has to be visible in one frozen frame or it is only a pose note.
    s.append(Blob("spine", P.MIR_COAT, 13.0, 15.5, off=(-7.0, 27.0), z=-1))
    # the paunch: a soft mass pushed FORWARD over the belt, the whole point of
    # the character design -- he is not built for this
    s.append(Blob("pelvis", P.MIR_COAT, 20.0, 17.5, off=(4.0, 16.0), z=2))
    # collar + open placket: the only pale cloth on him, at the throat, which
    # is also where the eye goes to read the head
    s.append(Blob("neck", P.MIR_LINEN, 10.0, 6.4, off=(1.4, 2.0), z=3))
    s.append(Poly("spine", P.MIR_LINEN, [(-3, 27), (4, 26), (2, 37), (-2, 37)], z=3, rim=0.4))
    # ---- head ----
    # Smaller than the first pass: an oversized pale ovoid pulled the eye off
    # the tool and read as a bald egg. The head is now mostly hair (dark), with
    # only the face plane catching light.
    s.append(Limb("neck", P.MIR_SKIN_DARK, 13, 12, 11, z=4))
    s.append(Blob("head", P.MIR_SKIN_DARK, HEAD_R, HEAD_R * 1.02, off=(0.0, HEAD_R * 0.86), z=6))
    # the face plane: a smaller lit ellipse pushed FORWARD (screen-left), which
    # is what makes the facing readable at 22px without a drawn face
    s.append(Blob("head", P.MIR_SKIN, HEAD_R * 0.62, HEAD_R * 0.76,
                  off=(HEAD_R * 0.44, HEAD_R * 0.80), z=7))
    # a soft brow/nose bump on the leading edge -- one more directional cue
    s.append(Blob("head", P.MIR_SKIN, HEAD_R * 0.20, HEAD_R * 0.17,
                  off=(HEAD_R * 0.92, HEAD_R * 0.80), z=8, rim=0.0))
    # receding hair: a heavy dark mass over the crown and down the back of the
    # skull, leaving the brow bare -- forty, and losing it
    s.append(Blob("head", P.MIR_HAIR, HEAD_R * 0.98, HEAD_R * 0.74,
                  off=(-3.4, HEAD_R * 1.20), z=9, rim=0.35))
    s.append(Blob("head", P.MIR_HAIR, HEAD_R * 0.42, HEAD_R * 0.58,
                  off=(-HEAD_R * 0.72, HEAD_R * 0.72), z=9, rim=0.3))

    # ---- the tool: the one warm thing on him ----
    s.append(Blob("belt", P.EMBER, 3.6, 6.0, z=8, glow=0.75, rim=0.0))

    # ---- front limbs ----
    s.append(Limb("hip_f", P.MIR_TROUSER, 38, 20, 16, z=10, rim=0.6))
    s.append(Limb("knee_f", P.MIR_TROUSER, 34, 15, 12, z=11, rim=0.6))
    s.append(Poly("foot_f", P.MIR_BOOT, [(-7, 0), (14, 0), (14, -8), (-7, -8)], z=12, rim=0.5))
    s.append(Limb("shoulder_f", P.MIR_SHIRT, 30, 17, 13, z=14))
    s.append(Limb("elbow_f", P.MIR_SKIN, 24, 11, 9, z=15))
    s.append(Blob("hand_f", hand_col, 6.4 * hand_w, 7.4 * hand_w, z=16))
    return s


def _dim(col):
    """Back-side limbs sit a value lower so the figure reads in depth."""
    return tuple(int(c * 0.62) for c in col)


def hands_wear(stage):
    """The hands arc (world-bible §11). 0 = the Fold (clean, soft),
    1 = the Keep (wrecked). Used to re-render the cast per act."""
    stage = max(0.0, min(1.0, stage))
    col = tuple(
        int(a + (b - a) * stage) for a, b in zip(P.MIR_SKIN, P.HARROW_HAND)
    )
    return col, 1.0 + 0.22 * stage


# ==========================================================================
# poses
# ==========================================================================
# A pose is joint-name -> degrees of offset from the rest angle.
REST = {}

STAND = {
    "spine": 0, "neck": 0,
    "shoulder_f": 4, "elbow_f": 6,
    "shoulder_b": -3, "elbow_b": 8,
    "hip_f": 2, "knee_f": 2, "hip_b": -2, "knee_b": 3,
}

# idle: he does not stand up straight, ever. Weight settles, the head dips.
IDLE_A = dict(STAND, **{"spine": 1, "neck": 2, "shoulder_f": 6, "shoulder_b": -5})
IDLE_B = dict(STAND, **{"spine": 3, "neck": 5, "shoulder_f": 9, "shoulder_b": -2,
                        "knee_f": 5, "knee_b": 6})

# run: laboured. Short stride, heavy forward lean, arms barely swing --
# he is not an athlete and the animation should say so before the writing does.
RUN_1 = dict(STAND, **{"spine": -10, "neck": 6, "hip_f": -30, "knee_f": 34,
                       "hip_b": 26, "knee_b": 12, "shoulder_f": -22, "elbow_f": 34,
                       "shoulder_b": 20, "elbow_b": 26})
RUN_2 = dict(STAND, **{"spine": -13, "neck": 8, "hip_f": -6, "knee_f": 10,
                       "hip_b": 4, "knee_b": 44, "shoulder_f": -4, "elbow_f": 24,
                       "shoulder_b": 4, "elbow_b": 30})
RUN_3 = dict(STAND, **{"spine": -10, "neck": 6, "hip_f": 26, "knee_f": 12,
                       "hip_b": -30, "knee_b": 33, "shoulder_f": 20, "elbow_f": 26,
                       "shoulder_b": -22, "elbow_b": 34})
RUN_4 = dict(STAND, **{"spine": -13, "neck": 8, "hip_f": 4, "knee_f": 42,
                       "hip_b": -6, "knee_b": 11, "shoulder_f": 4, "elbow_f": 30,
                       "shoulder_b": -4, "elbow_b": 24})

# light attack: he swings the way a man swings who has never swung anything --
# all shoulder, no hips, and he over-commits and has to catch himself.
L_WIND = dict(STAND, **{"spine": 8, "neck": -4, "shoulder_f": 62, "elbow_f": 44,
                        "shoulder_b": -18, "hip_f": 6, "knee_f": 8})
L_HIT = dict(STAND, **{"spine": -16, "neck": 8, "shoulder_f": -66, "elbow_f": 6,
                       "shoulder_b": 24, "hip_f": -12, "knee_f": 14})
L_REC = dict(STAND, **{"spine": -6, "neck": 6, "shoulder_f": -24, "elbow_f": 22,
                       "shoulder_b": 10, "knee_f": 8})

# heavy: a whole-body commitment he cannot control. Big anticipation, then
# he throws himself and nearly loses his footing.
H_WIND = dict(STAND, **{"spine": 16, "neck": -10, "shoulder_f": 96, "elbow_f": 62,
                        "shoulder_b": -34, "hip_f": 14, "knee_f": 16, "knee_b": 12})
H_HIT = dict(STAND, **{"spine": -24, "neck": 12, "shoulder_f": -88, "elbow_f": 4,
                       "shoulder_b": 40, "hip_f": -26, "knee_f": 24, "hip_b": 16})
H_REC = dict(STAND, **{"spine": -14, "neck": 14, "shoulder_f": -40, "elbow_f": 34,
                       "shoulder_b": 18, "hip_f": -10, "knee_f": 20, "knee_b": 8})

# dash: not a roll. A clumsy shove of the whole body, arms trailing.
DASH = dict(STAND, **{"spine": -26, "neck": 14, "shoulder_f": 34, "elbow_f": 48,
                      "shoulder_b": 42, "elbow_b": 40, "hip_f": -34, "knee_f": 30,
                      "hip_b": 22, "knee_b": 40})

# parry: the clock-keeper's move -- he does not block, he CATCHES. Compact,
# both hands up, elbows in, the one thing his trade actually taught him.
PARRY = dict(STAND, **{"spine": 6, "neck": -2, "shoulder_f": 74, "elbow_f": 78,
                       "shoulder_b": 66, "elbow_b": 82, "knee_f": 12, "knee_b": 12})

# hurt: he folds. Middle-aged men fold.
HURT = dict(STAND, **{"spine": 20, "neck": -14, "shoulder_f": 40, "elbow_f": 56,
                      "shoulder_b": 34, "elbow_b": 50, "hip_f": 14, "knee_f": 22,
                      "knee_b": 18})

# down / death: he does not die dramatically. He sits down.
DOWN = dict(STAND, **{"spine": 34, "neck": -22, "shoulder_f": 26, "elbow_f": 70,
                      "shoulder_b": 20, "elbow_b": 66, "hip_f": -74, "knee_f": 86,
                      "hip_b": -70, "knee_b": 84})

# interact / pick: kneeling over a mechanism -- the ending's posture, and the
# only time in the game his body is doing the thing it is actually good at.
PICK = dict(STAND, **{"spine": 24, "neck": -26, "shoulder_f": 84, "elbow_f": 66,
                      "shoulder_b": 78, "elbow_b": 62, "hip_f": -66, "knee_f": 80,
                      "hip_b": -60, "knee_b": 76})


# ==========================================================================
# clips  (frame budgets per PRD §11.1.2 step 2)
# ==========================================================================
def clips():
    z = (0.0, 0.0)
    return {
        # idle 2-4 frames: a slow settle, not a bounce
        "idle": (Clip([(IDLE_A, z, 1.0, "smooth"), (IDLE_B, (0.0, -1.2), 0.995, "smooth"),
                       (IDLE_A, z, 1.0, "smooth")]), 4),
        # run 4-6
        "run": (Clip([(RUN_1, (0.0, 1.5), 1.0, "smooth"), (RUN_2, z, 0.99, "smooth"),
                      (RUN_3, (0.0, 1.5), 1.0, "smooth"), (RUN_4, z, 0.99, "smooth"),
                      (RUN_1, (0.0, 1.5), 1.0, "smooth")]), 6),
        # attack 3-5: anticipation -> impact (snap) -> recovery
        "attack": (Clip([(L_WIND, (-2.0, 0.0), 0.99, "in"),
                         (L_HIT, (5.0, 0.0), 1.02, "snap"),
                         (L_REC, (1.0, 0.0), 1.0, "out")]), 3),
        "heavy": (Clip([(H_WIND, (-4.0, 0.0), 0.97, "in"),
                        (H_WIND, (-5.0, 0.0), 0.97, "linear"),
                        (H_HIT, (9.0, -1.0), 1.05, "snap"),
                        (H_REC, (3.0, 0.0), 1.0, "out")]), 5),
        "dash": (Clip([(DASH, (0.0, 0.0), 1.0, "out"), (DASH, (4.0, 0.0), 1.0, "linear")]), 2),
        "parry": (Clip([(PARRY, z, 1.0, "snap"), (PARRY, (0.0, 1.0), 1.01, "out")]), 2),
        "hurt": (Clip([(HURT, (-4.0, 0.0), 0.99, "snap"), (HURT, (-2.0, 0.0), 1.0, "out")]), 2),
        "down": (Clip([(HURT, z, 1.0, "in"), (DOWN, (-6.0, 0.0), 1.0, "out"),
                       (DOWN, (-6.0, 0.0), 1.0, "linear")]), 4),
        "pick": (Clip([(PICK, z, 1.0, "smooth"), (PICK, (0.0, -0.8), 1.0, "smooth"),
                       (PICK, z, 1.0, "smooth")]), 4),
    }


def build(frame=(200, 200), figure_h=176.0, hands=0.0):
    """Render every clip to a list of frames. Returns {name: [Image, ...]}."""
    sk = skeleton()
    hc, hw = hands_wear(hands)
    sh = shapes(hand_col=hc, hand_w=hw)
    scale = figure_h / H
    # Touch-up pass (art-cohesion audit P3): Mir read as a soft muddy blob with
    # a bright teal outline. Three levers fix the value structure without
    # touching his forms or his one-warm-note face: deeper, cooler shadow cores
    # (0.38 vs the cast 0.46) so the coat, arm and trousers separate by VALUE;
    # a hair more key so the lit planes actually catch light; a TIGHTER dark
    # halo (1.35 vs 2.0) that hugs the silhouette as a contour instead of a
    # murky glow; and a thinner rim so the cool edge is an accent, not a border.
    painter = Painter(frame, ao=(1.35, 0.86), shade=(0.38, 1.22), rim_width=1.0)
    out = {}
    for name, (clip, n) in clips().items():
        frames = []
        for pose, root, s in clip.sample(n):
            frames.append(painter.render(sk, sh, pose, root=root, scale=mul_scale(scale, s)))
        out[name] = frames
    return out
