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
    print("fx written")
