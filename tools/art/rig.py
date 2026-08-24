"""A small 2D skeletal rig + painterly renderer for the cast.

WHY A RIG INSTEAD OF GENERATED FRAMES
The generator is good at painterly *scenes* and bad at everything this cast
needs: it will not hold one identity across 22 animation states, it fights the
combination of full-body + stylised + isolated background, and it has a hard
prior toward handsome lean heroes that a canon description of a soft, stooped,
forty-year-old clock-keeper cannot overcome. The old pipeline's answer was to
generate one pose and shift halves of the bitmap around, which is why the cast
animated like a jiggling blob.

At the size this game actually renders (Mir is 22 world px tall), facial detail
is worth nothing and silhouette, value structure, palette and ANIMATION are
worth everything -- all four of which a rig gives exactly. So characters are
authored here and environments stay generated (`gen.py`), which is the split
each tool is actually good at.

HOW IT WORKS
  * A `Skeleton` is a tree of `Joint`s in figure-space (origin at the feet,
    +y up, +x forward/screen-left).
  * `Shape`s hang off joints -- tapered limbs, ellipses, polygons -- and are
    painted with form shading, a warm key from upper-left, a cool rim light on
    the silhouette, and optional emissive glow.
  * A `Pose` is joint angles plus a root transform; animations are keyframed
    poses interpolated with easing.
  * Everything renders at SS× supersample and downsamples with LANCZOS, so
    edges are soft and painterly -- never pixelated (PRD §11.1).

Palette discipline is enforced by construction: every colour comes from
`palette.py`, so "one palette, five moods" is not a review note, it is the API.
"""

from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

SS = 4  # supersample factor


# ==========================================================================
# geometry
# ==========================================================================
def _rot(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return x * c - y * s, x * s + y * c


class Joint(object):
    """A named point in the skeleton. `angle` is degrees, relative to parent."""

    __slots__ = ("name", "parent", "offset", "angle", "length")

    def __init__(self, name, parent=None, offset=(0.0, 0.0), angle=0.0, length=0.0):
        self.name = name
        self.parent = parent
        self.offset = offset
        self.angle = angle
        self.length = length


class Skeleton(object):
    def __init__(self, joints):
        self.joints = {}
        self.order = []
        for j in joints:
            self.joints[j.name] = j
            self.order.append(j.name)

    def solve(self, pose):
        """Resolve every joint to (x, y, absolute_angle) in figure space."""
        out = {}
        for name in self.order:
            j = self.joints[name]
            ang = j.angle + float(pose.get(name, 0.0))
            ox, oy = j.offset
            if j.parent is None:
                out[name] = (ox, oy, math.radians(ang))
            else:
                px, py, pa = out[j.parent]
                # the parent's length carries the child down its own axis
                plen = self.joints[j.parent].length
                if plen:
                    dx, dy = _rot(0.0, plen, pa)
                    px, py = px + dx, py + dy
                dx, dy = _rot(ox, oy, pa)
                out[name] = (px + dx, py + dy, pa + math.radians(ang))
        return out


# ==========================================================================
# shapes
# ==========================================================================
class Shape(object):
    """Base: a painted piece of a body, attached to a joint.

    z orders front-to-back. `col` is (r,g,b); shading is derived from it so a
    piece only ever needs one authored colour.
    """

    def __init__(self, joint, col, z=0, glow=0.0, rim=1.0):
        self.joint = joint
        self.col = col
        self.z = z
        self.glow = glow
        self.rim = rim

    def polygon(self, frame):  # pragma: no cover - overridden
        raise NotImplementedError


class Limb(Shape):
    """A tapered capsule from the joint, down its axis: thighs, arms, necks."""

    def __init__(self, joint, col, length, w0, w1, z=0, glow=0.0, rim=1.0, bow=0.0):
        Shape.__init__(self, joint, col, z, glow, rim)
        self.length = length
        self.w0 = w0
        self.w1 = w1
        self.bow = bow  # lateral curve, for a slumped arm or a bowed leg

    def polygon(self, frame):
        x, y, a = frame[self.joint]
        pts_l, pts_r = [], []
        steps = 10
        for i in range(steps + 1):
            t = float(i) / steps
            w = (self.w0 * (1 - t) + self.w1 * t) * 0.5
            # local point down the axis, with a sine bow
            lx = self.bow * math.sin(t * math.pi)
            ly = self.length * t
            dx, dy = _rot(lx, ly, a)
            nx, ny = _rot(w, 0.0, a)
            pts_l.append((x + dx + nx, y + dy + ny))
            pts_r.append((x + dx - nx, y + dy - ny))
        return pts_l + list(reversed(pts_r))


class Blob(Shape):
    """An ellipse: head, belly, a slime's mass. `squash` shapes it live."""

    def __init__(self, joint, col, rx, ry, off=(0.0, 0.0), z=0, glow=0.0, rim=1.0, tilt=0.0):
        Shape.__init__(self, joint, col, z, glow, rim)
        self.rx = rx
        self.ry = ry
        self.off = off
        self.tilt = tilt

    def polygon(self, frame):
        x, y, a = frame[self.joint]
        ox, oy = _rot(self.off[0], self.off[1], a)
        cx, cy = x + ox, y + oy
        a = a + math.radians(self.tilt)
        pts = []
        for i in range(28):
            t = 2 * math.pi * i / 28.0
            lx, ly = self.rx * math.cos(t), self.ry * math.sin(t)
            dx, dy = _rot(lx, ly, a)
            pts.append((cx + dx, cy + dy))
        return pts


class Poly(Shape):
    """An authored polygon in joint-local space: a waistcoat, a coat flare."""

    def __init__(self, joint, col, pts, z=0, glow=0.0, rim=1.0):
        Shape.__init__(self, joint, col, z, glow, rim)
        self.pts = pts

    def polygon(self, frame):
        x, y, a = frame[self.joint]
        out = []
        for lx, ly in self.pts:
            dx, dy = _rot(lx, ly, a)
            out.append((x + dx, y + dy))
        return out


# ==========================================================================
# painting
# ==========================================================================
def _shade(col, k):
    """Scale a colour toward light (k>1) or shadow (k<1), keeping it in gamut
    and drifting shadows cool rather than muddy grey."""
    r, g, b = col
    if k >= 1.0:
        t = min(1.0, k - 1.0)
        r = r + (255 - r) * t * 0.9
        g = g + (255 - g) * t * 0.9
        b = b + (255 - b) * t * 0.75
    else:
        r, g, b = r * k, g * k, b * (k * 0.92 + 0.14)  # shadows keep blue
    return (int(max(0, min(255, r))), int(max(0, min(255, g))), int(max(0, min(255, b))))


class Painter(object):
    """Renders a posed skeleton into an RGBA frame.

    The look, fixed once here so every character shares it:
      * key light from upper-left -> a soft light-to-shadow ramp across each
        piece, done as a masked linear gradient (not a flat fill, not a
        posterized ramp).
      * a cool teal rim on the upper-left silhouette edge, so figures separate
        from near-black ground -- the readability requirement of §11.1.
      * an optional additive emissive pass for anything that should glow.
      * a soft dark halo hugging the silhouette (`ao`). This is the single
        thing that lets one sprite read on BOTH the Fold's pale silt and the
        Keep's near-black stone: on dark ground it is invisible, on light
        ground it becomes the figure's contour. A rim light alone cannot do
        this -- it disappears the moment the ground is brighter than the rim.
      * a faint painterly grain so large flats do not read as vector.
    """

    def __init__(self, size, light=(-0.72, -0.70), rim_col=(104, 178, 176), grain=6,
                 ao=(2.0, 0.82)):
        self.w, self.h = size
        self.light = light
        self.rim_col = rim_col
        self.grain = grain
        self.ao = ao  # (radius in figure px, strength) or None

    def render(self, skeleton, shapes, pose, root=(0.0, 0.0), scale=1.0, flip=False):
        W, H = self.w * SS, self.h * SS
        frame = skeleton.solve(pose)

        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        emissive = Image.new("RGB", (W, H), (0, 0, 0))
        rx, ry = root

        # `scale` may be a scalar or (sx, sy). Non-uniform scale is how a
        # boneless creature gets real squash-and-stretch: a slime's telegraph
        # has to flip its silhouette class from wide-dome to tall-column, and
        # a uniform scale cannot do that. See foes.Slime.
        try:
            sx_, sy_ = scale
        except TypeError:
            sx_ = sy_ = scale

        def to_px(p):
            x, y = p
            x = (x + rx) * sx_
            y = (y + ry) * sy_
            if flip:
                x = -x
            # figure space: origin at feet-centre, +y up -> image space
            return ((self.w * 0.5 + x) * SS, (self.h - 1.0 - y) * SS)

        for sh in sorted(shapes, key=lambda s: s.z):
            poly = [to_px(p) for p in sh.polygon(frame)]
            if len(poly) < 3:
                continue
            piece = self._paint_piece(poly, sh, (W, H))
            base.alpha_composite(piece)
            if sh.glow > 0:
                g = Image.new("RGB", (W, H), (0, 0, 0))
                ImageDraw.Draw(g).polygon(poly, fill=_shade(sh.col, 1.5))
                g = g.filter(ImageFilter.GaussianBlur(9 * SS * sh.glow))
                emissive = ImageChops.add(emissive, g)

        if self.ao:
            base = self._halo(base)

        out = base
        if self.grain:
            out = self._grain(out)
        out = out.resize((self.w, self.h), Image.LANCZOS)

        if emissive.getbbox():
            em = emissive.resize((self.w, self.h), Image.LANCZOS)
            rgb = out.convert("RGB")
            lit = ImageChops.add(rgb, em)
            # emissive spills a little past the silhouette, so composite it
            # over the whole frame using the glow's own luminance as alpha
            spill = em.convert("L").point(lambda v: min(255, int(v * 1.5)))
            out = Image.composite(lit.convert("RGBA"), out, spill).convert("RGBA")
            a = out.split()[3]
            out.putalpha(ImageChops.lighter(a, spill))
        return out

    # ---- internals -------------------------------------------------------
    def _halo(self, base):
        """A soft dark contour behind the figure -- see the `ao` note above."""
        rad, strength = self.ao
        sil = base.split()[3].point(lambda v: 255 if v > 40 else 0)
        grown = sil
        for _ in range(max(1, int(rad * SS) // 2)):
            grown = grown.filter(ImageFilter.MaxFilter(3))
        grown = grown.filter(ImageFilter.GaussianBlur(rad * SS * 0.55))
        plate = Image.new("RGBA", base.size, (4, 6, 11, 0))
        plate.putalpha(grown.point(lambda v: int(v * strength)))
        plate.alpha_composite(base)
        return plate

    def _paint_piece(self, poly, sh, size):
        W, H = size
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).polygon(poly, fill=255)
        box = mask.getbbox()
        if not box:
            return Image.new("RGBA", (W, H), (0, 0, 0, 0))

        # form shading: a linear ramp along the light vector across the piece
        x0, y0, x1, y1 = box
        grad = Image.new("L", (max(1, x1 - x0), max(1, y1 - y0)))
        gp = grad.load()
        lx, ly = self.light
        n = math.hypot(lx, ly) or 1.0
        lx, ly = lx / n, ly / n
        gw, gh = grad.size
        for yy in range(gh):
            fy = (yy / float(max(1, gh - 1))) - 0.5
            for xx in range(gw):
                fx = (xx / float(max(1, gw - 1))) - 0.5
                d = fx * lx + fy * ly  # -0.7 (lit) .. +0.7 (shadow)
                gp[xx, yy] = int(max(0, min(255, 128 - d * 300)))
        full = Image.new("L", (W, H), 0)
        full.paste(grad, (x0, y0))

        lit = Image.new("RGBA", (W, H), _shade(sh.col, 1.16) + (255,))
        shadow = Image.new("RGBA", (W, H), _shade(sh.col, 0.46) + (255,))
        body = Image.composite(lit, shadow, full)

        # rim light along the lit silhouette edge
        if sh.rim > 0:
            inner = mask.filter(ImageFilter.MinFilter(3))
            for _ in range(max(1, int(1.6 * SS)) // 2):
                inner = inner.filter(ImageFilter.MinFilter(3))
            edge = ImageChops.subtract(mask, inner)
            edge = ImageChops.multiply(edge, full.point(lambda v: 255 if v > 150 else int(v * 0.35)))
            rim = Image.new("RGBA", (W, H), tuple(self.rim_col) + (255,))
            body = Image.composite(rim, body, edge.point(lambda v: int(v * sh.rim)))

        body.putalpha(mask)
        return body

    def _grain(self, img):
        """A faint high-frequency wobble so flats read as painted, not vector.
        Deterministic (hash-based), so builds stay reproducible."""
        w, h = img.size
        step = max(2, self.grain * SS // 2)
        noise = Image.new("L", (max(1, w // step), max(1, h // step)))
        np_ = noise.load()
        for y in range(noise.height):
            for x in range(noise.width):
                v = (x * 73856093) ^ (y * 19349663)
                np_[x, y] = 118 + (v % 21)
        noise = noise.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2 * SS))
        rgb = img.convert("RGB")
        overlay = ImageChops.multiply(rgb, Image.merge("RGB", (noise, noise, noise)).point(lambda v: 128 + (v - 128) // 3))
        out = Image.blend(rgb, ImageChops.add(overlay, overlay), 0.0)  # keep values, cheap no-op guard
        out = Image.blend(rgb, overlay.point(lambda v: min(255, int(v * 2.0))), 0.35)
        out = out.convert("RGBA")
        out.putalpha(img.split()[3])
        return out


# ==========================================================================
# animation
# ==========================================================================
def ease(t, kind="smooth"):
    if kind == "linear":
        return t
    if kind == "in":
        return t * t
    if kind == "out":
        return 1.0 - (1.0 - t) ** 2
    if kind == "snap":  # fast out, hard stop -- impacts
        return 1.0 - (1.0 - t) ** 4
    return t * t * (3.0 - 2.0 * t)


def mul_scale(k, s):
    """Combine a figure-height scalar with a per-frame squash (scalar or pair)."""
    try:
        a, b = s
    except TypeError:
        a = b = s
    return (k * a, k * b)


def blend(a, b, t):
    keys = set(a) | set(b)
    return dict((k, a.get(k, 0.0) * (1 - t) + b.get(k, 0.0) * t) for k in keys)


class Clip(object):
    """Keyframed animation. Each key is (pose, root_offset, scale, easing)."""

    def __init__(self, keys):
        self.keys = keys

    @staticmethod
    def _lerp_scale(s0, s1, t):
        """Scales may be scalars or (sx, sy); blend either, componentwise."""
        try:
            a0, b0 = s0
        except TypeError:
            a0 = b0 = s0
        try:
            a1, b1 = s1
        except TypeError:
            a1 = b1 = s1
        return (a0 * (1 - t) + a1 * t, b0 * (1 - t) + b1 * t)

    def sample(self, n):
        """Evenly sample n frames across the clip's keys."""
        out = []
        segs = len(self.keys) - 1
        if segs <= 0:
            p, r, s, _ = self.keys[0]
            return [(p, r, s)] * n
        for i in range(n):
            t = (float(i) / n) * segs  # n frames, looping
            k = min(segs - 1, int(t))
            local = ease(t - k, self.keys[k + 1][3])
            p0, r0, s0, _ = self.keys[k]
            p1, r1, s1, _ = self.keys[k + 1]
            out.append(
                (
                    blend(p0, p1, local),
                    (r0[0] * (1 - local) + r1[0] * local, r0[1] * (1 - local) + r1[1] * local),
                    self._lerp_scale(s0, s1, local),
                )
            )
        return out
