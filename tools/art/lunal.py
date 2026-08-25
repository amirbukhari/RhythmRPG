"""Lunal -- the finale (world-bible §8, PRD §8.7). Rig, poses, animation set.

WHY SHE IS AUTHORED HERE AND NOT A FLAT PNG
She shipped as a single 432x232 flat sprite out of the retired
`tools/pixelart/lunal_boss.py` -- hard pixels, a baked outline, and the cage
painted into her body -- which is the one register the whole style contract
retired (§0: "a stranger shown any screenshot says 'that's a beautiful
painting'"). Worse, she was the ONE foe with no state set at all: the boss the
entire campaign walks toward could not telegraph, flinch, or fall, while every
trash slime could. She is a character; characters are rigged (style-contract §1).

CANON THIS RIG IS BUILT TO CARRY (world-bible §6.5/§8, style-contract §3)
  * Human-scaled ON PURPOSE (§8.7.1 #6): 22.5 world px, Mir's own height class,
    not the retired Conductor's colossus. Her scale is the argument -- what is
    terrible about her is that she is exactly his size.
  * "Mir's own palette gone cold and certain -- same family, no warmth at all."
    So she is built from Mir's slate-teal, pushed bluer and darker, and she
    carries NONE of his one warm note. The mask is the only pale shape on her.
  * She is his OPPOSITE in posture. Mir is stooped, soft, and never stands
    straight; Lunal is upright, squared, and still. Where his silhouette says
    "not built for this", hers says "certain". That contrast is the read.
  * She holds/walls/disarms, she does not kill (§8.7.2: Mir cannot die). Her
    implement is a hunter's stave held to CONTROL SPACE, never a blade, and her
    telegraph is a braced wall-stance, not a wind-up to a killing blow.
  * The cage is NOT her. It is Nari's, a staged set entity (§8.7.2), so nothing
    of it is baked into this figure -- she is a person, framed by it, not fused
    to it.

Figure space matches Mir's: origin between the feet, +y up, +x screen-left.
"""

from __future__ import annotations

import palette as P
from rig import Blob, Clip, Joint, Limb, Painter, Poly, Skeleton, mul_scale

# --------------------------------------------------------------------------
# proportions -- 180px figure, upright and squared (~6 heads). She stands a
# touch taller than Mir's 176 because she stands STRAIGHT and he does not.
# --------------------------------------------------------------------------
H = 180.0
HEAD_R = 12.6
PELVIS_Y = 80.0
CHEST_Y = 122.0


def skeleton():
    return Skeleton(
        [
            # root at the pelvis; the spine is nearly plumb -- her certainty
            # lives in the fact that she does not lean, where Mir always does
            Joint("pelvis", None, (0.0, PELVIS_Y), 0.0, 0.0),
            Joint("spine", "pelvis", (0.0, 0.0), -1.0, CHEST_Y - PELVIS_Y),
            Joint("neck", "spine", (0.0, 0.0), -2.0, 13.0),
            Joint("head", "neck", (0.0, 0.0), 2.0, 0.0),
            # shoulders sit HIGH and SQUARE -- the opposite of Mir's forward slump
            Joint("shoulder_f", "spine", (3.0, -2.0), 176.0, 31.0),
            Joint("elbow_f", "shoulder_f", (0.0, 0.0), 14.0, 28.0),
            Joint("hand_f", "elbow_f", (0.0, 0.0), 0.0, 0.0),
            Joint("shoulder_b", "spine", (-6.0, -3.0), 184.0, 30.0),
            Joint("elbow_b", "shoulder_b", (0.0, 0.0), 12.0, 27.0),
            Joint("hand_b", "elbow_b", (0.0, 0.0), 0.0, 0.0),
            # legs planted in a controlled, slightly wide hunter's stance
            Joint("hip_f", "pelvis", (4.0, -2.0), 178.0, 40.0),
            Joint("knee_f", "hip_f", (0.0, 0.0), 3.0, 36.0),
            Joint("foot_f", "knee_f", (0.0, 0.0), 0.0, 0.0),
            Joint("hip_b", "pelvis", (-5.0, -3.0), 182.0, 39.0),
            Joint("knee_b", "hip_b", (0.0, 0.0), 4.0, 35.0),
            Joint("foot_b", "knee_b", (0.0, 0.0), 0.0, 0.0),
            # the long coat's hem, for the flare poly
            Joint("hem", "pelvis", (0.0, 0.0), 180.0, 0.0),
            # the stave: PLANTED in the ground at her forward side and standing
            # dead vertical, so it reads as an upright bar at 22px regardless of
            # what the arms do -- the "control of space" note. Rooting it to the
            # hand made it swing out horizontal and read as a rifle.
            Joint("stave", "pelvis", (16.0, -PELVIS_Y), 0.0, 0.0),
        ]
    )


def shapes():
    s = []
    # ---- back limbs (behind the coat) ----
    s.append(Limb("shoulder_b", _dim(P.LUNAL_COAT), 31, 14, 11, z=-20))
    s.append(Limb("elbow_b", _dim(P.LUNAL_COAT), 27, 10, 8, z=-19))
    s.append(Blob("hand_b", _dim(P.LUNAL_SKIN), 5.4, 6.2, z=-18))
    s.append(Limb("hip_b", _dim(P.LUNAL_COAT), 39, 18, 14, z=-16, rim=0.5))
    s.append(Limb("knee_b", _dim(P.LUNAL_COAT), 35, 13, 10, z=-15, rim=0.5))
    s.append(Poly("foot_b", _dim(P.LUNAL_COAT), [(-7, 0), (13, 0), (13, -8), (-7, -8)], z=-14, rim=0.4))

    # ---- the coat: the silhouette. Narrow, squared at the shoulders, flaring
    # to a long controlled hem -- an A-line kept far SHARPER than the wraith's
    # heavy trailing robe, because she is precise and he is not.
    s.append(Limb("spine", P.LUNAL_COAT, CHEST_Y - PELVIS_Y, 30, 27, z=0))
    # a high, standing collar -- the certainty is in the neck being covered and
    # straight, and it caps the dark body so the pale mask sits clear above it
    s.append(Poly("spine", P.LUNAL_COAT, [(-11, 36), (11, 36), (8, 46), (-8, 46)], z=3))
    # the hem flare: sharp, symmetric, deliberate
    s.append(Poly("hem", P.LUNAL_COAT,
                  [(-16, -2), (16, -3), (21, 46), (7, 40), (0, 52), (-8, 40), (-21, 46)],
                  z=1))
    # a single cold metal clasp at the sternum -- one hard edge, no warmth
    s.append(Poly("spine", _dim(P.STONE), [(-3, 24), (3, 24), (3, 30), (-3, 30)], z=4, rim=0.5))

    # ---- head: a hooded dark head, and the mask over the face ----
    s.append(Limb("neck", _dim(P.LUNAL_SKIN), 12, 10, 9, z=4))
    # the head/hood mass (dark) -- fills the whole head; the mask sits ON it, so
    # a thin dark edge frames the pale plate as a hood does, never a ring
    s.append(Blob("head", _dim(P.LUNAL_COAT), HEAD_R * 1.02, HEAD_R * 1.04, off=(-1.0, HEAD_R * 0.88), z=5))
    # a dark crescent of drawn-back hair, upper and behind only
    s.append(Blob("head", _dim(P.LUNAL_COAT), HEAD_R * 0.62, HEAD_R * 0.80,
                  off=(-HEAD_R * 0.66, HEAD_R * 1.02), z=6, rim=0.3))
    # THE MASK: the one pale shape on her (world-bible §8). A solid smooth blank
    # face-plate, filling the front of the head and pushed forward (screen-left)
    # so the facing reads without a drawn face; a FAINT COLD emissive so she has
    # a focal note like every foe -- but cold, never the cast's ember.
    s.append(Blob("head", P.LUNAL_MASK, HEAD_R * 0.80, HEAD_R * 0.94,
                  off=(HEAD_R * 0.24, HEAD_R * 0.80), z=8, glow=0.06, rim=0.25))
    # a soft shadow across the lower mask, so the pale plate reads as a face and
    # not a disc -- the brow catches the key light, the jaw falls into shadow
    s.append(Blob("head", _dim(P.LUNAL_MASK), HEAD_R * 0.58, HEAD_R * 0.34,
                  off=(HEAD_R * 0.30, HEAD_R * 0.52), z=9, rim=0.0))

    # ---- front limbs ----
    s.append(Limb("hip_f", P.LUNAL_COAT, 40, 19, 15, z=10, rim=0.6))
    s.append(Limb("knee_f", P.LUNAL_COAT, 36, 14, 11, z=11, rim=0.6))
    s.append(Poly("foot_f", P.LUNAL_COAT, [(-7, 0), (14, 0), (14, -8), (-7, -8)], z=12, rim=0.5))
    s.append(Limb("shoulder_f", P.LUNAL_COAT, 31, 16, 12, z=14))
    s.append(Limb("elbow_f", P.LUNAL_COAT, 28, 11, 9, z=15))
    # the stave: a long slender cold shaft, planted and vertical, standing about
    # head-high beside her. Wood-dark with a dim pale cap -- a hunter's implement
    # to WALL, not a weapon to kill. Drawn behind the front hand so she reads as
    # resting a hand on it.
    s.append(Limb("stave", _dim(P.STONE), 150, 2.6, 2.2, z=13, rim=0.35))
    s.append(Blob("stave", _dim(P.LUNAL_MASK), 2.8, 3.4, off=(0.0, 150.0), z=13, rim=0.0))
    s.append(Blob("hand_f", P.LUNAL_SKIN, 5.8, 6.6, z=16))
    return s


def _dim(col):
    """Back-side pieces sit a value lower so the figure reads in depth."""
    return tuple(int(c * 0.62) for c in col)


# ==========================================================================
# poses -- joint-name -> degrees of offset from the rest angle
# ==========================================================================
STAND = {
    "spine": 0, "neck": 0,
    "shoulder_f": 0, "elbow_f": 0, "shoulder_b": 0, "elbow_b": 0,
    "hip_f": 0, "knee_f": 0, "hip_b": 0, "knee_b": 0,
    "foot_f": 0, "foot_b": 0, "hem": 0, "stave": 0,
}

# idle: she is STILL. Where Mir sways and settles and never quite holds a pose,
# Lunal barely moves -- a slow, level breath, the stave planted. The stillness
# is the characterisation, so the two keys are almost identical on purpose.
IDLE_A = dict(STAND, **{"spine": 0, "neck": 0, "shoulder_f": 1})
IDLE_B = dict(STAND, **{"spine": -1, "neck": -1, "shoulder_f": -1, "shoulder_b": 1})

# move: a measured, level stride. No fall-and-catch (that is Nari); no labour
# (that is Mir). Controlled, even, and quiet -- a hunter closing distance.
MOVE_1 = dict(STAND, **{"spine": -3, "hip_f": -22, "knee_f": 24, "hip_b": 18, "knee_b": 8,
                        "shoulder_f": -12, "elbow_f": 10, "shoulder_b": 12, "elbow_b": 8})
MOVE_2 = dict(STAND, **{"spine": -4, "hip_f": -3, "knee_f": 10, "hip_b": 2, "knee_b": 20,
                        "shoulder_f": 2, "shoulder_b": -2})
MOVE_3 = dict(STAND, **{"spine": -3, "hip_f": 18, "knee_f": 8, "hip_b": -22, "knee_b": 22,
                        "shoulder_f": 12, "elbow_f": 8, "shoulder_b": -12, "elbow_b": 10})
MOVE_4 = dict(STAND, **{"spine": -4, "hip_f": 2, "knee_f": 22, "hip_b": -3, "knee_b": 10,
                        "shoulder_f": -2, "shoulder_b": 2})

# telegraph: the WALL. She does not wind up to strike -- she braces, plants
# wide, squares fully, and brings the stave up across her body to bar the way.
# The silhouette flips from narrow-upright to wide-braced: that shape change,
# not a scale tween, is what the player reads on the beat.
WALL = dict(STAND, **{"spine": 2, "neck": 1, "hip_f": -30, "knee_f": 20, "hip_b": 30, "knee_b": 20,
                      "shoulder_f": 40, "elbow_f": -58, "shoulder_b": -26, "elbow_b": 20,
                      "hem": 6})

# attack: a controlled stave THRUST/sweep to disarm -- it extends, lands, and
# she recovers on balance. She never over-commits; there is no catching herself.
HIT = dict(STAND, **{"spine": -6, "neck": 2, "hip_f": -18, "knee_f": 14, "hip_b": 16,
                     "shoulder_f": -30, "elbow_f": -8, "shoulder_b": 20, "elbow_b": 12})

# hurt: she barely gives ground. A tight, level flinch -- certainty does not
# fold the way Mir folds.
HURT = dict(STAND, **{"spine": 6, "neck": -4, "shoulder_f": 14, "elbow_f": 12,
                      "shoulder_b": -10, "hip_f": 6, "knee_f": 8})

# "dead": she is PASSED, not killed (§8.7.2). She lowers -- a slow, controlled
# settle onto one knee, the stave grounded, the head bowing. Not a collapse; a
# yielding. This is the terminal frame the fight ends on.
PASS = dict(STAND, **{"spine": 20, "neck": -18, "shoulder_f": 22, "elbow_f": 30,
                      "shoulder_b": 16, "elbow_b": 26, "hip_f": -58, "knee_f": 78,
                      "hip_b": -30, "knee_b": 46, "stave": -6, "hem": -8})


def clips():
    z = (0.0, 0.0)
    return {
        # idle 4: a level breath, almost still
        "idle": (Clip([(IDLE_A, z, 1.0, "smooth"), (IDLE_B, (0.0, -0.5), 1.0, "smooth"),
                       (IDLE_A, z, 1.0, "smooth")]), 4),
        # move 6: an even, measured stride
        "move": (Clip([(MOVE_1, (0.0, 1.0), 1.0, "smooth"), (MOVE_2, z, 1.0, "smooth"),
                       (MOVE_3, (0.0, 1.0), 1.0, "smooth"), (MOVE_4, z, 1.0, "smooth"),
                       (MOVE_1, (0.0, 1.0), 1.0, "smooth")]), 6),
        # telegraph 4: rise from idle into the braced wall and hold it
        "telegraph": (Clip([(IDLE_A, z, 1.0, "out"), (WALL, (-2.0, 0.0), 1.02, "out"),
                            (WALL, (-3.0, 0.0), 1.03, "smooth")]), 4),
        # attack 3: from the wall, a controlled thrust (snap), then recover level
        "attack": (Clip([(WALL, (-3.0, 0.0), 1.03, "in"), (HIT, (7.0, 0.0), 1.0, "snap"),
                         (HIT, (2.0, 0.0), 1.0, "out")]), 3),
        # hurt 2: a tight flinch that barely moves her
        "hurt": (Clip([(HURT, (-3.0, 0.0), 1.0, "snap"), (HURT, (-1.0, 0.0), 1.0, "out")]), 2),
        # dead 4: a slow controlled settle onto one knee -- "passed", not killed
        "dead": (Clip([(HURT, z, 1.0, "in"), (PASS, (-2.0, -3.0), 1.0, "out"),
                       (PASS, (-2.0, -4.0), 1.0, "smooth")]), 4),
    }


def build(frame=(200, 200), figure_h=180.0):
    """Render every clip to a list of frames. Returns {name: [Image, ...]}."""
    sk = skeleton()
    sh = shapes()
    scale = figure_h / H
    # A COLD rim, bluer than the rest of the cast: she is Mir's palette gone
    # cold, and the rim is where that reads at silhouette scale.
    painter = Painter(frame, rim_col=(118, 150, 192))
    out = {}
    for name, (clip, n) in clips().items():
        out[name] = [
            painter.render(sk, sh, pose, root=root, scale=mul_scale(scale, s))
            for pose, root, s in clip.sample(n)
        ]
    return out
