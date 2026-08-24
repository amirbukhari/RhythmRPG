"""Nari -- three years old. Rig, poses, and his animation set.

CANON THIS RIG IS BUILT TO CARRY (world-bible §5)
  * "He must be *specific* -- a real toddler, not a symbol." The specificity
    that survives at 13 world px is PROPORTION and GAIT, not a face. So:
    a head that is nearly a third of his height, a belly that leads, arms that
    hang out from the shoulders because toddlers cannot tuck them, and feet
    planted much too wide.
  * He is the only WARM living thing in a cold world (§11 Tone), which is also
    the readability solution: at 13px he is a small warm note beside a cold
    dark one, and the player never loses him in a crowd.
  * His walk is the load-bearing animation. He does not walk like a small
    adult: he falls forward and catches himself, every step, which is why the
    cycle is 6 frames with two of them off-balance. A player who has watched
    that for two hours should feel the hole when it stops.
  * `follow` is the state he spends the whole first act in -- trailing his
    father, half a beat behind. `reach` is the one that has to hurt: arms up,
    waiting to be picked up, at the moment nobody picks him up.

Figure space matches Mir's: origin between the feet, +y up, +x screen-left.
"""

from __future__ import annotations

import palette as P
from rig import Blob, Clip, Joint, Limb, Painter, Poly, Skeleton, mul_scale

# --------------------------------------------------------------------------
# proportions -- 104px figure, ~3.4 heads. He is chest-high to his father.
# --------------------------------------------------------------------------
H = 104.0
HEAD_R = 15.0  # deliberately huge: this is what says "three" at 13px
PELVIS_Y = 38.0
CHEST_Y = 62.0


def skeleton():
    return Skeleton(
        [
            Joint("pelvis", None, (0.0, PELVIS_Y), 0.0, 0.0),
            Joint("spine", "pelvis", (0.0, 0.0), -4.0, CHEST_Y - PELVIS_Y),
            Joint("neck", "spine", (0.0, 0.0), -3.0, 6.0),
            Joint("head", "neck", (0.0, 0.0), 3.0, 0.0),
            # arms held out from the body -- toddlers do not tuck their elbows
            Joint("shoulder_f", "spine", (2.0, -2.0), 152.0, 15.0),
            Joint("elbow_f", "shoulder_f", (0.0, 0.0), 16.0, 13.0),
            Joint("hand_f", "elbow_f", (0.0, 0.0), 0.0, 0.0),
            Joint("shoulder_b", "spine", (-5.0, -3.0), 206.0, 14.0),
            Joint("elbow_b", "shoulder_b", (0.0, 0.0), -14.0, 12.0),
            Joint("hand_b", "elbow_b", (0.0, 0.0), 0.0, 0.0),
            # legs: short, and set WIDE (the toddler stance)
            Joint("hip_f", "pelvis", (4.0, -1.0), 172.0, 17.0),
            Joint("knee_f", "hip_f", (0.0, 0.0), 8.0, 15.0),
            Joint("foot_f", "knee_f", (0.0, 0.0), 0.0, 0.0),
            Joint("hip_b", "pelvis", (-5.0, -2.0), 188.0, 16.0),
            Joint("knee_b", "hip_b", (0.0, 0.0), 9.0, 14.0),
            Joint("foot_b", "knee_b", (0.0, 0.0), 0.0, 0.0),
        ]
    )


def shapes():
    s = []
    # ---- back limbs ----
    s.append(Limb("shoulder_b", _dim(P.NARI_SMOCK), 15, 9, 8, z=-20))
    s.append(Limb("elbow_b", _dim(P.NARI_SKIN), 12, 7, 6, z=-19))
    s.append(Blob("hand_b", _dim(P.NARI_SKIN), 4.2, 4.6, z=-18))
    s.append(Limb("hip_b", _dim(P.NARI_SMOCK), 16, 12, 9, z=-16, rim=0.5))
    s.append(Limb("knee_b", _dim(P.NARI_SKIN_LEG), 14, 8, 7, z=-15, rim=0.5))
    s.append(Blob("foot_b", _dim(P.NARI_SKIN), 5.0, 3.2, off=(1.0, -1.6), z=-14, rim=0.4))

    # ---- torso: the smock is one soft bell, not a fitted garment ----
    # It is too big for him (canon), so it flares below the belly and hides
    # where his waist would be -- which is exactly what makes him read young.
    s.append(Limb("spine", P.NARI_SMOCK, CHEST_Y - PELVIS_Y, 26, 23, z=0))
    s.append(Poly("pelvis", P.NARI_SMOCK,
                  [(-13, 2), (13, 4), (11, 24), (-12, 22)], z=1))
    # the belly leads: a toddler's centre of mass is out in front of him
    s.append(Blob("pelvis", P.NARI_SMOCK, 12.5, 11.0, off=(3.0, 12.0), z=2))

    # ---- head: nearly a third of him ----
    s.append(Limb("neck", _dim(P.NARI_SKIN), 5, 8, 8, z=3))
    s.append(Blob("head", P.NARI_SKIN, HEAD_R, HEAD_R * 0.96, off=(0.0, HEAD_R * 0.80), z=6))
    # the cheek: a toddler is round on the leading edge, and this is the shape
    # that reads at 13px as "a small child looking that way"
    s.append(Blob("head", P.NARI_SKIN, HEAD_R * 0.52, HEAD_R * 0.46,
                  off=(HEAD_R * 0.52, HEAD_R * 0.60), z=7, rim=0.6))
    # fine wispy hair: a thin cap that does NOT cover the round skull
    s.append(Blob("head", P.NARI_HAIR, HEAD_R * 0.92, HEAD_R * 0.46,
                  off=(-2.2, HEAD_R * 1.24), z=8, rim=0.3))

    # ---- front limbs ----
    s.append(Limb("hip_f", P.NARI_SMOCK, 17, 13, 10, z=10, rim=0.6))
    s.append(Limb("knee_f", P.NARI_SKIN_LEG, 15, 9, 8, z=11, rim=0.6))
    s.append(Blob("foot_f", P.NARI_SKIN, 5.4, 3.4, off=(1.4, -1.8), z=12, rim=0.5))
    s.append(Limb("shoulder_f", P.NARI_SMOCK, 15, 10, 9, z=14))
    s.append(Limb("elbow_f", P.NARI_SKIN, 13, 8, 7, z=15))
    s.append(Blob("hand_f", P.NARI_SKIN, 4.6, 5.0, z=16))
    return s


def _dim(col):
    return tuple(int(c * 0.66) for c in col)


# ==========================================================================
# poses
# ==========================================================================
STAND = {
    "spine": 0, "neck": 0,
    "shoulder_f": 0, "elbow_f": 0, "shoulder_b": 0, "elbow_b": 0,
    "hip_f": 0, "knee_f": 0, "hip_b": 0, "knee_b": 0,
    "foot_f": 0, "foot_b": 0,
}

# idle: he sways. He is three; he cannot stand still, and he does not try.
IDLE_A = dict(STAND, **{"spine": 2, "neck": 3, "shoulder_f": 6, "shoulder_b": -6})
IDLE_B = dict(STAND, **{"spine": -3, "neck": -2, "shoulder_f": -8, "shoulder_b": 8,
                        "knee_f": 5, "knee_b": 4})

# walk: falls forward, catches himself. Frames 2 and 5 are the catch.
#
# THE GAIT IS A PUZZLE MECHANIC, NOT JUST AN ANIMATION.
# world-bible §6.4 builds the Scar's whole middle act out of reading Nari's
# tracks: "Nari's gait is learnable (paired stride, heel dot, faint right-foot
# drag)", set against pilgrim strides, den-thing gaits and decoys that double
# back. That only works if the player has already learned it -- and the only
# place to learn it is here, in the state he spends the entire first act in.
# So the cycle is deliberately ASYMMETRIC in two ways the ground can record:
#
#   paired stride -- the b-side hip swings through 32 degrees against the
#                    f-side's 46, so his steps come in long/short pairs. On the
#                    ground that is a trail with an uneven rhythm, which is what
#                    makes it identifiable at all.
#   right-foot drag -- the b-side knee barely lifts through its swing and the
#                    foot trails toe-down (`foot_b` negative), so that foot
#                    scuffs instead of clearing. On the ground: a smear off the
#                    back of every other print.
#
# Do not "fix" the asymmetry. It is the clue.
W1 = dict(STAND, **{"spine": -7, "hip_f": -26, "knee_f": 24, "hip_b": 14, "knee_b": 8,
                    "foot_b": -6,
                    "shoulder_f": -14, "shoulder_b": 16, "elbow_f": 10})
W2 = dict(STAND, **{"spine": -11, "neck": 4, "hip_f": -4, "knee_f": 8, "hip_b": 0,
                    "knee_b": 14, "foot_b": -14,
                    "shoulder_f": 10, "shoulder_b": -8, "elbow_f": 18})
W3 = dict(STAND, **{"spine": -7, "hip_f": 20, "knee_f": 9, "hip_b": -18, "knee_b": 13,
                    "foot_b": -11,
                    "shoulder_f": 16, "shoulder_b": -14, "elbow_b": 10})
W4 = dict(STAND, **{"spine": -11, "neck": 4, "hip_f": 2, "knee_f": 28, "hip_b": -6,
                    "knee_b": 9, "foot_b": -3,
                    "shoulder_f": -8, "shoulder_b": 10, "elbow_b": 18})

# reach: arms up, waiting to be lifted. The one that has to hurt.
REACH = dict(STAND, **{"spine": 6, "neck": -12, "shoulder_f": 118, "elbow_f": 22,
                       "shoulder_b": -112, "elbow_b": -18, "knee_f": 8, "knee_b": 7})

# sit: he sits down where he is, which is what a three-year-old does when the
# walking stops being interesting.
SIT = dict(STAND, **{"spine": 8, "neck": -6, "shoulder_f": 30, "elbow_f": 34,
                     "shoulder_b": -26, "elbow_b": -30,
                     "hip_f": -84, "knee_f": 92, "hip_b": -80, "knee_b": 88})

# hide: behind his father's leg, shoulders drawn in. Used in the Den beat.
HIDE = dict(STAND, **{"spine": 12, "neck": -8, "shoulder_f": 46, "elbow_f": 52,
                      "shoulder_b": -40, "elbow_b": -48, "knee_f": 12, "knee_b": 10})


def clips():
    z = (0.0, 0.0)
    return {
        "idle": (Clip([(IDLE_A, z, 1.0, "smooth"), (IDLE_B, (0.6, -0.6), 1.0, "smooth"),
                       (IDLE_A, z, 1.0, "smooth")]), 4),
        "run": (Clip([(W1, (0.0, 1.2), 1.0, "smooth"), (W2, z, 0.99, "out"),
                      (W3, (0.0, 1.2), 1.0, "smooth"), (W4, z, 0.99, "out"),
                      (W1, (0.0, 1.2), 1.0, "smooth")]), 6),
        "reach": (Clip([(REACH, z, 1.0, "out"), (REACH, (0.0, 1.0), 1.005, "smooth"),
                        (REACH, z, 1.0, "smooth")]), 4),
        "sit": (Clip([(SIT, z, 1.0, "in"), (SIT, (0.0, -0.5), 1.0, "smooth"),
                      (SIT, z, 1.0, "smooth")]), 3),
        "hide": (Clip([(HIDE, z, 1.0, "smooth"), (HIDE, (-0.8, 0.0), 0.995, "smooth"),
                       (HIDE, z, 1.0, "smooth")]), 3),
    }


def build(frame=(200, 200), figure_h=104.0):
    sk = skeleton()
    sh = shapes()
    scale = figure_h / H
    # A touch warmer key than Mir's: he is the warm thing in the frame.
    painter = Painter(frame, rim_col=(196, 170, 130))
    out = {}
    for name, (clip, n) in clips().items():
        out[name] = [
            painter.render(sk, sh, pose, root=root, scale=mul_scale(scale, s))
            for pose, root, s in clip.sample(n)
        ]
    return out
