"""Additive glow/bloom textures for the Hyper Light Drifter register (PRD
§11.1). White radial sprites tinted + additively blended in-engine to fake
emission: glowing enemy eyes, weapon arcs, attack telegraphs, on-beat
flashes. Kept white so a single texture serves every colour via tinting.
"""

from __future__ import annotations

import math
from PIL import Image
from skatopia import save


def radial(size: int = 64, falloff: float = 2.4) -> Image.Image:
    """Soft white radial gradient (opaque core → transparent edge)."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / c
            a = max(0.0, 1.0 - d) ** falloff
            px[x, y] = (255, 255, 255, int(255 * a))
    return im


def haze(w: int = 128, h: int = 128) -> Image.Image:
    """A soft, seamlessly-tiling fog/haze cloud (white, low alpha). Built from
    a few superimposed periodic sine layers so it tiles with no seam in either
    axis -- scrolled slowly in-engine for drifting atmosphere over the world."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    layers = [(1, 2, 0.0), (2, 1, 1.3), (3, 3, 2.1), (5, 2, 0.7)]
    for y in range(h):
        for x in range(w):
            v = 0.0
            for fx_, fy_, ph in layers:
                v += math.sin(2 * math.pi * (fx_ * x / w) + ph) * math.cos(2 * math.pi * (fy_ * y / h) + ph)
            v = (v / len(layers) + 1) / 2  # -> 0..1
            a = max(0.0, (v - 0.45)) ** 1.6 * 0.75
            px[x, y] = (255, 255, 255, int(255 * min(1.0, a)))
    return im


def godray(w: int = 256, h: int = 144) -> Image.Image:
    """Soft diagonal light shafts, brightest at the top and fading down --
    tiles horizontally so it can scroll. White; tinted warm/cold in-engine."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    bands = [(0.08, 6.0), (0.26, 3.5), (0.42, 7.0), (0.61, 4.0), (0.79, 5.5), (0.93, 3.0)]
    for y in range(h):
        fade = max(0.0, 1.0 - y / h) ** 1.7  # bright top, gone by the floor
        for x in range(w):
            u = x / w
            a = 0.0
            for center, width in bands:
                # shear the band position with depth for a raking-light look
                c = (center + 0.10 * (y / h)) % 1.0
                d = min(abs(u - c), 1 - abs(u - c))  # wrap distance -> seamless
                a += max(0.0, 1.0 - d * width)
            a = min(1.0, a) * fade * 0.5
            if a > 0.01:
                px[x, y] = (255, 255, 255, int(255 * a))
    return im


def spark(size: int = 24) -> Image.Image:
    """A 4-point impact star for hit flashes."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            dx, dy = abs(x - c), abs(y - c)
            arm = min(dx, dy)
            reach = max(dx, dy)
            a = max(0.0, 1.0 - reach / c) ** 1.6 * max(0.0, 1.0 - arm / 2.5)
            core = max(0.0, 1.0 - math.hypot(dx, dy) / (c * 0.5)) ** 2
            v = min(1.0, a + core)
            if v > 0.02:
                px[x, y] = (255, 255, 255, int(255 * v))
    return im


if __name__ == "__main__":
    save(radial(), "fx/glow.png")
    save(spark(), "fx/spark.png")
    save(haze(), "fx/haze.png")
    save(godray(), "fx/godray.png")
    print("fx written")
