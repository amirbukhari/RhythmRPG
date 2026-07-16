"""Force a crisp dark outline onto every AI-generated sprite (owner's HLD
bar; skatopia.py's own comment calls this "the single biggest 'reads as
real pixel art' win" -- every hand-authored piece in this game already gets
it via skatopia.outline(), but the AI pipeline (env/band/enemies) never did).

Two techniques, chosen per asset shape:

  * grow_outline() -- for STANDALONE single-object PNGs (env/*): grows the
    canvas by 1px on every side and stamps a dedicated near-black ring
    around the true silhouette, exactly like skatopia.outline() but
    vectorized. Safe here because OverworldScene reads render scale from
    the LIVE texture height (WorldScale.ts), so a 2px-taller PNG is
    self-correcting -- no config to update.

  * inplace_outline() -- for multi-frame SHEETS (band/*, enemies/*): BootScene
    hardcodes frameWidth/frameHeight, so growing the canvas would desync
    every frame boundary. Instead this recolors the EXISTING outer ring of
    each opaque island to near-black, in place, same dimensions -- no
    config changes, no origin/scale drift across the many draw sites that
    use a fixed literal scale for these sheets.

Both are idempotent: grow_outline() skips a piece whose border ring is
already the outline colour; inplace_outline() recolouring dark to the same
dark is a no-op on a second run.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ENV = ROOT / "assets" / "sprites" / "env"
BAND = ROOT / "assets" / "sprites" / "band"
ENEMIES = ROOT / "assets" / "sprites" / "enemies"
SKIP_ENEMY = {"conductor_colossal.png", "the_conductor.png"}  # already hand-outlined

OUTLINE = np.array([10, 10, 14, 255], dtype=np.uint8)


def _silhouette_ring(mask: np.ndarray) -> np.ndarray:
    interior = mask & np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1)
    return mask & ~interior


def grow_outline(path: Path) -> None:
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    mask = a[..., 3] > 0
    if not mask.any():
        return
    # idempotency: if the CURRENT border ring's opaque pixels are already
    # all outline-coloured, this piece was already grown -- skip.
    border = np.zeros_like(mask)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    touched = mask & border
    if touched.any() and np.all(a[touched] == OUTLINE):
        return
    h, w = mask.shape
    canvas = np.zeros((h + 2, w + 2, 4), dtype=np.uint8)
    canvas[1:-1, 1:-1] = a
    cmask = canvas[..., 3] > 0
    ring = np.zeros_like(cmask)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                ring |= np.roll(np.roll(cmask, dy, 0), dx, 1)
    ring &= ~cmask
    canvas[ring] = OUTLINE
    Image.fromarray(canvas, "RGBA").save(path)
    print(f"grew {path.relative_to(ROOT)}: {w}x{h} -> {w + 2}x{h + 2}")


def inplace_outline(path: Path) -> None:
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    mask = a[..., 3] > 0
    if not mask.any():
        return
    ring = _silhouette_ring(mask)
    if not ring.any():
        return
    if np.all(a[ring][..., :3] == OUTLINE[:3]):
        return  # already darkened -- no-op
    a[ring, :3] = OUTLINE[:3]
    Image.fromarray(a, "RGBA").save(path)
    print(f"outlined {path.relative_to(ROOT)}")


def main() -> int:
    for p in sorted(ENV.rglob("*.png")):
        grow_outline(p)
    for p in sorted(BAND.rglob("*.png")):
        inplace_outline(p)
    for p in sorted(ENEMIES.glob("*.png")):
        if p.name not in SKIP_ENEMY:
            inplace_outline(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
