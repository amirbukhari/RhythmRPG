"""The foes. Rigs, poses, and animation sets.

WHY THE FOES GET A RIG TOO
PRD §11.5 asks for >=6 animation states per enemy. The shipped cast had ONE
frame each and the engine faked the rest with squash-and-stretch on the base
scale, which is why a fight read as two blobs pulsing at each other. A state is
only a state if the SHAPE changes.

THE READABILITY CONTRACT (the thing M1 exists to fix)
Every foe must be distinguishable from Mir in a single frozen frame, at 26-40
world px, in motion. Three levers, applied deliberately per foe:

  * SILHOUETTE CLASS. Mir is a narrow upright rectangle. So the slime is a WIDE
    LOW dome (aspect inverted), the drifter is a tall RAGGED vertical with a
    trailing hem (taller and thinner than Mir), and the wraith is a huge
    TRIANGLE that widens downward. No foe shares Mir's proportions.
  * COLOUR FAMILY. Mir is cold slate-teal with one ember accent. The slime is
    sick green, the drifter is drowned brown-grey with a cold void where a face
    should be, the wraith is oxidised copper and violet.
  * TELEGRAPH POSE. The windup is not a scale tween. It is an authored pose
    that changes the silhouette class for the length of the windup -- the slime
    rears UP into a tall column, the drifter throws its arms wide, the wraith
    lifts. That is what makes an attack readable on the beat.

STATES (all six, every foe): idle, move, telegraph, attack, hurt, dead.
"""

from __future__ import annotations

import palette as P
from rig import Blob, Clip, Joint, Limb, Painter, Poly, Skeleton, mul_scale

STATES = ("idle", "move", "telegraph", "attack", "hurt", "dead")


# ==========================================================================
# the rot slime -- a WIDE LOW dome. Inverted aspect vs Mir on purpose.
# ==========================================================================
class Slime(object):
    H = 104.0  # frame-space height; the body only fills the bottom third

    @staticmethod
    def skeleton():
        return Skeleton(
            [
                Joint("base", None, (0.0, 0.0), 0.0, 0.0),
                Joint("body", "base", (0.0, 0.0), 0.0, 0.0),
                Joint("crown", "base", (0.0, 34.0), 0.0, 0.0),
                # three drip points along the rim, so the outline is never a
                # clean ellipse -- a clean ellipse reads as a bubble, not rot
                Joint("drip_a", "base", (26.0, 6.0), 0.0, 0.0),
                Joint("drip_b", "base", (-4.0, 3.0), 0.0, 0.0),
                Joint("drip_c", "base", (-30.0, 7.0), 0.0, 0.0),
            ]
        )

    @staticmethod
    def shapes():
        s = []
        # the mass: overlapping lumps, never one clean arc. A clean arc reads
        # as a bubble or a mushroom; rot has to look like it is COLLAPSING.
        s.append(Blob("body", P.SLIME_BODY, 44.0, 24.0, off=(0.0, 20.0), z=0))
        s.append(Blob("body", P.SLIME_BODY, 30.0, 30.0, off=(-8.0, 24.0), z=1, rim=0.7))
        s.append(Blob("body", P.SLIME_BODY, 17.0, 13.0, off=(21.0, 15.0), z=1, rim=0.5))
        s.append(Blob("body", P.SLIME_BODY, 12.0, 19.0, off=(-27.0, 14.0), z=0, rim=0.5))
        s.append(Blob("body", P.SLIME_BODY, 9.0, 7.0, off=(6.0, 40.0), z=1, rim=0.6))
        # the puddle it is always sitting in -- grounds it, and says "wet"
        s.append(Blob("base", _dim(P.SLIME_BODY), 47.0, 7.0, off=(0.0, 4.0), z=-3, rim=0.2))
        # drips: teardrops hanging BELOW the rim, behind the mass. The first
        # pass put them on top of the body, where two dark ovals read as
        # nostrils and the whole thing looked like the front of a car.
        s.append(Blob("drip_a", _mid(P.SLIME_BODY), 4.0, 8.0, off=(0.0, -3.0), z=-1, rim=0.3))
        s.append(Blob("drip_b", _mid(P.SLIME_BODY), 3.2, 6.0, off=(0.0, -2.0), z=-1, rim=0.3))
        s.append(Blob("drip_c", _mid(P.SLIME_BODY), 4.4, 9.0, off=(0.0, -4.0), z=-1, rim=0.3))
        # suspended silt and a small bone, INSIDE the mass, small enough to be
        # a detail you notice on the second look rather than a prop it holds
        s.append(Blob("body", _dim(P.SLIME_BODY), 2.6, 1.8, off=(15.0, 14.0), z=3, rim=0.0))
        s.append(Poly("body", P.WRAITH_BONE, [(-15, 24), (-8, 26), (-8, 28), (-16, 26)],
                      z=3, rim=0.0))
        # the core: the ONE emissive note, which is also the hit-read -- when
        # the core is bright the thing is alive, and the fade is the death
        s.append(Blob("body", P.SLIME_CORE, 9.0, 7.5, off=(2.0, 20.0), z=4,
                      glow=0.55, rim=0.0))
        return s

    # -- "poses": a slime has no joints to bend, so its animation is pure
    # squash-and-stretch. Every key carries a NON-UNIFORM scale (sx, sy) --
    # that is what lets the telegraph flip the silhouette class from wide-dome
    # to tall-column, which a uniform scale can never do.
    @staticmethod
    def clips():
        z = (0.0, 0.0)
        FLAT = {}
        return {
            # idle: it breathes. Slow, wet, and never quite still.
            "idle": (Clip([(FLAT, z, (1.00, 1.00), "smooth"),
                           (FLAT, (0.0, 0.6), (0.97, 1.06), "smooth"),
                           (FLAT, z, (1.00, 1.00), "smooth")]), 4),
            # move: it heaves. The mass throws itself forward and lands wide.
            "move": (Clip([(FLAT, (-2.0, 0.0), (0.94, 1.10), "out"),
                           (FLAT, (3.0, 0.0), (1.10, 0.88), "in"),
                           (FLAT, (6.0, 0.0), (1.04, 0.98), "out"),
                           (FLAT, (1.0, 0.0), (0.96, 1.06), "in"),
                           (FLAT, (-2.0, 0.0), (0.94, 1.10), "out")]), 6),
            # telegraph: it REARS -- 0.62 wide by 1.62 tall. A player who has
            # seen this once knows a slam is coming, from the shape alone, in
            # peripheral vision, on the beat. That is the whole point.
            "telegraph": (Clip([(FLAT, z, (1.02, 1.00), "out"),
                                (FLAT, (-3.0, 0.0), (0.74, 1.42), "out"),
                                (FLAT, (-4.0, 0.0), (0.62, 1.62), "smooth")]), 4),
            # attack: it comes down and splashes out sideways.
            "attack": (Clip([(FLAT, (-4.0, 0.0), (0.64, 1.58), "in"),
                             (FLAT, (7.0, 0.0), (1.44, 0.56), "snap"),
                             (FLAT, (4.0, 0.0), (1.16, 0.86), "out")]), 3),
            "hurt": (Clip([(FLAT, (-6.0, 0.0), (1.18, 0.80), "snap"),
                           (FLAT, (-2.0, 0.0), (1.04, 0.96), "out")]), 2),
            # dead: it stops holding itself together and spreads out flat
            "dead": (Clip([(FLAT, z, (1.06, 0.88), "in"),
                           (FLAT, (0.0, 0.0), (1.28, 0.44), "out"),
                           (FLAT, (0.0, 0.0), (1.38, 0.26), "smooth")]), 4),
        }

    @staticmethod
    def build(frame=(128, 128), figure_h=104.0):
        return _render(Slime, frame, figure_h, rim=(140, 206, 150))


# ==========================================================================
# the drowned drifter -- TALLER and THINNER than Mir, with a trailing hem.
# ==========================================================================
class Drifter(object):
    H = 122.0

    @staticmethod
    def skeleton():
        return Skeleton(
            [
                Joint("pelvis", None, (0.0, 52.0), 0.0, 0.0),
                Joint("spine", "pelvis", (0.0, 0.0), -2.0, 42.0),
                Joint("neck", "spine", (0.0, 0.0), -4.0, 10.0),
                Joint("head", "neck", (0.0, 0.0), 2.0, 0.0),
                Joint("shoulder_f", "spine", (2.0, -3.0), 168.0, 26.0),
                Joint("elbow_f", "shoulder_f", (0.0, 0.0), 14.0, 24.0),
                Joint("hand_f", "elbow_f", (0.0, 0.0), 0.0, 0.0),
                Joint("shoulder_b", "spine", (-6.0, -5.0), 192.0, 25.0),
                Joint("elbow_b", "shoulder_b", (0.0, 0.0), 12.0, 23.0),
                Joint("hand_b", "elbow_b", (0.0, 0.0), 0.0, 0.0),
                Joint("hem", "pelvis", (0.0, 0.0), 180.0, 0.0),
                # kelp streamers: they trail UP, because it is underwater
                Joint("kelp_a", "shoulder_f", (0.0, 0.0), 250.0, 0.0),
                Joint("kelp_b", "shoulder_b", (0.0, 0.0), 292.0, 0.0),
            ]
        )

    @staticmethod
    def shapes():
        s = []
        s.append(Limb("kelp_b", _dim(P.KELP), 30, 5, 1, z=-24, bow=7.0, rim=0.3))
        s.append(Limb("shoulder_b", _dim(P.DRIFTER_COAT), 25, 11, 8, z=-20))
        s.append(Limb("elbow_b", _dim(P.DRIFTER_COAT), 23, 8, 6, z=-19))
        s.append(Blob("hand_b", _dim(P.DRIFTER_COAT), 4.5, 5.5, z=-18))
        # the coat is the silhouette: narrow at the shoulders, flaring to a
        # long ragged hem that never touches the ground cleanly
        s.append(Limb("spine", P.DRIFTER_COAT, 42, 24, 30, z=0))
        s.append(Poly("hem", P.DRIFTER_COAT,
                      [(-17, -2), (16, -4), (23, 44), (12, 52), (2, 40), (-8, 51), (-21, 42)],
                      z=1))
        # the hood: an empty cowl, and inside it a cold void where a face is
        s.append(Blob("head", P.DRIFTER_COAT, 13.0, 14.5, off=(-1.0, 10.0), z=6))
        s.append(Blob("head", P.DRIFTER_VOID, 6.4, 7.6, off=(3.4, 9.0), z=7,
                      glow=0.42, rim=0.0))
        # barnacle crust on the one shoulder (canon)
        s.append(Blob("shoulder_f", P.WRAITH_BONE, 4.0, 3.2, off=(2.0, 4.0), z=15, rim=0.0))
        s.append(Blob("shoulder_f", P.WRAITH_BONE, 2.6, 2.2, off=(-2.0, 9.0), z=15, rim=0.0))
        s.append(Limb("shoulder_f", P.DRIFTER_COAT, 26, 13, 9, z=14))
        s.append(Limb("elbow_f", P.DRIFTER_COAT, 24, 9, 7, z=15))
        s.append(Blob("hand_f", P.DRIFTER_COAT, 5.0, 6.0, z=16))
        s.append(Limb("kelp_a", _dim(P.KELP), 34, 5, 1, z=18, bow=-8.0, rim=0.3))
        return s

    @staticmethod
    def clips():
        z = (0.0, 0.0)
        BASE = {"spine": 0, "shoulder_f": 0, "elbow_f": 0, "shoulder_b": 0,
                "elbow_b": 0, "hem": 0, "kelp_a": 0, "kelp_b": 0}
        # it drifts rather than walks -- there is no footfall, which is the
        # single creepiest thing about it and it costs nothing to animate
        IDLE_A = dict(BASE, **{"spine": 2, "kelp_a": 8, "kelp_b": -6, "hem": 3})
        IDLE_B = dict(BASE, **{"spine": -2, "kelp_a": -9, "kelp_b": 7, "hem": -4,
                               "shoulder_f": 4, "shoulder_b": -4})
        MOVE_A = dict(BASE, **{"spine": -6, "shoulder_f": -14, "shoulder_b": 12,
                               "hem": 12, "kelp_a": 16, "kelp_b": -12})
        MOVE_B = dict(BASE, **{"spine": -9, "shoulder_f": 10, "shoulder_b": -10,
                               "hem": -9, "kelp_a": -14, "kelp_b": 15})
        TELE = dict(BASE, **{"spine": 8, "shoulder_f": 74, "elbow_f": -34,
                             "shoulder_b": -66, "elbow_b": 30, "hem": -14,
                             "kelp_a": 30, "kelp_b": -28})
        HIT = dict(BASE, **{"spine": -20, "shoulder_f": -78, "elbow_f": 18,
                            "shoulder_b": 62, "hem": 22, "kelp_a": -26, "kelp_b": 22})
        HURT = dict(BASE, **{"spine": 16, "shoulder_f": 34, "elbow_f": 30,
                             "shoulder_b": -28, "hem": -10})
        DEAD = dict(BASE, **{"spine": 40, "shoulder_f": 52, "elbow_f": 56,
                             "shoulder_b": -46, "elbow_b": -50, "hem": -26,
                             "kelp_a": -40, "kelp_b": 36})
        return {
            "idle": (Clip([(IDLE_A, z, 1.0, "smooth"), (IDLE_B, (0.0, 2.0), 1.0, "smooth"),
                           (IDLE_A, z, 1.0, "smooth")]), 4),
            "move": (Clip([(MOVE_A, (0.0, 1.6), 1.0, "smooth"), (MOVE_B, z, 1.0, "smooth"),
                           (MOVE_A, (0.0, 1.6), 1.0, "smooth")]), 6),
            "telegraph": (Clip([(IDLE_A, z, 1.0, "out"), (TELE, (-3.0, 1.0), 1.04, "out"),
                                (TELE, (-4.0, 2.0), 1.06, "smooth")]), 4),
            "attack": (Clip([(TELE, (-4.0, 1.0), 1.05, "in"), (HIT, (8.0, -2.0), 1.0, "snap"),
                             (HIT, (4.0, 0.0), 0.99, "out")]), 3),
            "hurt": (Clip([(HURT, (-5.0, 0.0), 0.98, "snap"), (HURT, (-2.0, 0.0), 1.0, "out")]), 2),
            "dead": (Clip([(HURT, z, 1.0, "in"), (DEAD, (-4.0, -6.0), 0.96, "out"),
                           (DEAD, (-4.0, -9.0), 0.92, "smooth")]), 4),
        }

    @staticmethod
    def build(frame=(140, 140), figure_h=122.0):
        # Touch-up pass (art-cohesion audit P4): the rim WAS (96,178,178), a
        # neon cyan LOUDER than the hood-void it was supposed to defer to, so
        # the figure had two accents fighting and the brightest thing on it was
        # a rim -- against the "brightest thing is small" rule. Dialled toward
        # STONE (97,110,122): a cold desaturated stone-blue that still lifts the
        # silhouette off near-black ground but leaves the glowing head-orb
        # (DRIFTER_VOID) as the one accent it was meant to be.
        return _render(Drifter, frame, figure_h, rim=(100, 126, 134))


# ==========================================================================
# the elite wraith -- a TRIANGLE that widens downward. Regal, not monstrous.
# ==========================================================================
class Wraith(object):
    H = 158.0

    @staticmethod
    def skeleton():
        return Skeleton(
            [
                Joint("pelvis", None, (0.0, 58.0), 0.0, 0.0),
                Joint("spine", "pelvis", (0.0, 0.0), 0.0, 58.0),
                Joint("neck", "spine", (0.0, 0.0), -2.0, 14.0),
                Joint("head", "neck", (0.0, 0.0), 2.0, 0.0),
                Joint("crown", "head", (0.0, 0.0), 0.0, 0.0),
                Joint("shoulder_f", "spine", (3.0, -6.0), 158.0, 38.0),
                Joint("elbow_f", "shoulder_f", (0.0, 0.0), 22.0, 36.0),
                Joint("hand_f", "elbow_f", (0.0, 0.0), 0.0, 0.0),
                Joint("shoulder_b", "spine", (-8.0, -8.0), 202.0, 36.0),
                Joint("elbow_b", "shoulder_b", (0.0, 0.0), -20.0, 34.0),
                Joint("hand_b", "elbow_b", (0.0, 0.0), 0.0, 0.0),
                Joint("robe", "pelvis", (0.0, 0.0), 180.0, 0.0),
                Joint("hair", "head", (0.0, 0.0), 300.0, 0.0),
            ]
        )

    @staticmethod
    def shapes():
        s = []
        s.append(Limb("shoulder_b", _dim(P.WRAITH_ROBE), 36, 13, 8, z=-20))
        s.append(Limb("elbow_b", _dim(P.WRAITH_ROBE), 34, 8, 5, z=-19))
        s.append(Blob("hand_b", _dim(P.WRAITH_BONE), 4.0, 6.0, z=-18))
        # the robe: the triangle. Far too long, trailing, and it is 60% of him.
        s.append(Poly("robe", P.WRAITH_ROBE,
                      [(-16, -4), (15, -6), (34, 50), (18, 60), (6, 46), (-6, 61),
                       (-22, 48), (-31, 54)], z=-2))
        s.append(Limb("spine", P.WRAITH_ROBE, 58, 26, 34, z=0))
        # a copper band at the waist -- the one hard edge on a soft figure
        s.append(Poly("pelvis", P.BRASS, [(-13, 4), (12, 6), (12, 11), (-13, 9)],
                      z=1, rim=0.5))
        # head: a narrow mask-like face, no eyes, a too-wide mouth
        s.append(Blob("head", _dim(P.WRAITH_ROBE), 11.0, 13.5, off=(-1.0, 11.0), z=5))
        s.append(Blob("head", P.WRAITH_BONE, 6.6, 9.6, off=(3.2, 10.5), z=6))
        s.append(Poly("head", _dim(P.ABYSS), [(1, 6), (9, 7), (9, 9), (1, 8)], z=7, rim=0.0))
        # the crown of salt-crusted bone
        s.append(Poly("crown", P.WRAITH_BONE,
                      [(-9, 20), (-6, 33), (-2, 22), (2, 34), (6, 22), (9, 31), (11, 19)],
                      z=8, rim=0.6))
        # long white hair drifting upward
        s.append(Limb("hair", P.WRAITH_BONE, 40, 9, 1, z=-6, bow=11.0, rim=0.3))
        s.append(Limb("hair", _dim(P.WRAITH_BONE), 32, 6, 1, z=-7, bow=-14.0, rim=0.2))
        # the ember burning in the chest cavity (canon)
        s.append(Blob("spine", P.EMBER, 5.2, 6.4, off=(2.0, 40.0), z=3, glow=0.7, rim=0.0))
        s.append(Limb("shoulder_f", P.WRAITH_ROBE, 38, 15, 9, z=14))
        s.append(Limb("elbow_f", P.WRAITH_ROBE, 36, 9, 5, z=15))
        # long fingers, as three tapers
        s.append(Limb("hand_f", P.WRAITH_BONE, 13, 4, 1, z=16, rim=0.7))
        s.append(Limb("hand_f", P.WRAITH_BONE, 11, 3, 1, z=16, bow=4.0, rim=0.7))
        s.append(Limb("hand_f", P.WRAITH_BONE, 10, 3, 1, z=16, bow=-5.0, rim=0.7))
        return s

    @staticmethod
    def clips():
        z = (0.0, 0.0)
        BASE = {"spine": 0, "shoulder_f": 0, "elbow_f": 0, "shoulder_b": 0,
                "elbow_b": 0, "robe": 0, "hair": 0, "head": 0}
        IDLE_A = dict(BASE, **{"spine": 1, "hair": 6, "robe": 2, "head": 2})
        IDLE_B = dict(BASE, **{"spine": -1, "hair": -7, "robe": -3, "head": -2,
                               "shoulder_f": 3, "shoulder_b": -3})
        MOVE_A = dict(BASE, **{"spine": -4, "robe": 14, "hair": 12,
                               "shoulder_f": -10, "shoulder_b": 9})
        MOVE_B = dict(BASE, **{"spine": -6, "robe": -11, "hair": -13,
                               "shoulder_f": 8, "shoulder_b": -8})
        # it does not crouch to strike. It RISES -- the scale key does the lift.
        TELE = dict(BASE, **{"spine": 4, "head": -8, "shoulder_f": 96, "elbow_f": -46,
                             "shoulder_b": -88, "elbow_b": 40, "robe": -18, "hair": 26})
        HIT = dict(BASE, **{"spine": -14, "head": 10, "shoulder_f": -92, "elbow_f": 22,
                            "shoulder_b": 74, "robe": 26, "hair": -30})
        HURT = dict(BASE, **{"spine": 12, "head": -10, "shoulder_f": 28, "elbow_f": 24,
                             "shoulder_b": -24, "robe": -12, "hair": -14})
        DEAD = dict(BASE, **{"spine": 30, "head": -26, "shoulder_f": 44, "elbow_f": 48,
                             "shoulder_b": -38, "elbow_b": -42, "robe": -30, "hair": -44})
        return {
            "idle": (Clip([(IDLE_A, z, 1.0, "smooth"), (IDLE_B, (0.0, 2.4), 1.0, "smooth"),
                           (IDLE_A, z, 1.0, "smooth")]), 4),
            "move": (Clip([(MOVE_A, (0.0, 2.0), 1.0, "smooth"), (MOVE_B, z, 1.0, "smooth"),
                           (MOVE_A, (0.0, 2.0), 1.0, "smooth")]), 6),
            "telegraph": (Clip([(IDLE_A, z, 1.0, "out"), (TELE, (-2.0, 5.0), 1.04, "out"),
                                (TELE, (-3.0, 8.0), 1.07, "smooth")]), 4),
            "attack": (Clip([(TELE, (-3.0, 7.0), 1.06, "in"), (HIT, (9.0, -3.0), 1.0, "snap"),
                             (HIT, (5.0, 0.0), 0.99, "out")]), 3),
            "hurt": (Clip([(HURT, (-5.0, 0.0), 0.98, "snap"), (HURT, (-2.0, 0.0), 1.0, "out")]), 2),
            "dead": (Clip([(HURT, z, 1.0, "in"), (DEAD, (-3.0, -8.0), 0.94, "out"),
                           (DEAD, (-3.0, -13.0), 0.88, "smooth")]), 4),
        }

    @staticmethod
    def build(frame=(180, 180), figure_h=158.0):
        return _render(Wraith, frame, figure_h, rim=(178, 150, 208))


# ==========================================================================
FOES = {"slime": Slime, "drifter": Drifter, "elite_wraith": Wraith}


def _dim(col):
    return tuple(int(c * 0.62) for c in col)


def _mid(col):
    return tuple(int(c * 0.82) for c in col)


def _render(cls, frame, figure_h, rim):
    sk = cls.skeleton()
    sh = cls.shapes()
    scale = figure_h / cls.H
    painter = Painter(frame, rim_col=rim)
    out = {}
    for name, (clip, n) in cls.clips().items():
        out[name] = [
            painter.render(sk, sh, pose, root=root, scale=mul_scale(scale, s))
            for pose, root, s in clip.sample(n)
        ]
    return out
