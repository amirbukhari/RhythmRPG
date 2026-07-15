"""The hand-pixeled fidelity pass (the last HLD axis): AI-generated pieces
read soft next to Hyper Light Drifter's hand-placed pixels -- anti-aliased
gradients, muddy edges, hundreds of near-duplicate colours per sprite. HLD's
look is FLAT: a tight palette, hard cel transitions, crisp silhouettes.

This pass rewrites every environment piece into that register:
  * median-cut palette quantization to a small colour count (scaled by
    sprite area -- a 14px prop gets ~8 colours, a 96px landform ~24);
  * hard alpha (0 or 255) -- no soft fringes;
  * quantized values snap to the same /9 ramp the painted ground uses,
    so pieces and plate share one colour register.

Idempotent; run after any generation batch.
  python3 tools/pixelart/fidelity_pass.py            # all env pieces
  python3 tools/pixelart/fidelity_pass.py <dir...>   # specific dirs
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIRS = [ROOT / "assets" / "sprites" / "env"]


def fidelity(path: Path) -> None:
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    alpha = a[..., 3]
    # --- green-screen despill (owner: "green screen style removal") --------
    # The generation background bleeds into the silhouette's outermost pixels
    # (grey/black halos); hardening alpha alone locks the halo in. So:
    # 1. hard silhouette (96: strict enough to drop glow fringes, loose
    #    enough to keep 1px features like harp strings);
    mask = alpha >= 96
    if not mask.any():
        return
    # 2. kill truly isolated specks only (<=1 opaque neighbour) -- a 1px
    #    line (harp string, cello neck) has 2 neighbours and must survive;
    n = np.zeros_like(mask, dtype=np.int16)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                n += np.roll(np.roll(mask, dy, 0), dx, 1)
    mask &= n >= 2
    # 3. decontaminate the outer ring: every boundary pixel takes the colour
    #    of its nearest interior neighbour, so no background tint survives.
    interior = mask & np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1)
    ring = mask & ~interior
    if interior.any() and ring.any():
        ys, xs = np.where(ring)
        iys, ixs = np.where(interior)
        for y, x in zip(ys, xs):
            d = (iys - y) ** 2 + (ixs - x) ** 2
            j = int(np.argmin(d))
            if d[j] > 16:  # no interior within 4px (thin feature): keep
                continue
            px = a[y, x, :3].astype(int)
            nb = a[iys[j], ixs[j], :3].astype(int)
            # only replace genuinely CONTAMINATED pixels: neutral (greyish)
            # and far from the interior colour -- deliberate dark outlines
            # and coloured rims stay untouched
            if int(px.max() - px.min()) < 30 and int(np.abs(px - nb).sum()) > 90:
                a[y, x, :3] = nb
    hard = np.where(mask, 255, 0).astype(np.uint8)
    # palette size by area: tiny props stay chunky, colossi keep range
    area = int((hard > 0).sum())
    colors = int(np.clip(6 + area ** 0.5 / 3.2, 8, 24))
    rgb = Image.fromarray(a[..., :3], "RGB")
    q = rgb.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    qa = np.array(q)
    # emissive cores are tiny clusters of hot pixels -- median cut discards
    # them (a lit lantern went dark). Re-stamp the original wherever it burns.
    lum = a[..., :3].astype(np.float32).max(axis=2)
    hot = lum > 190
    qa[hot] = a[..., :3][hot]
    out = np.dstack([qa, hard])
    # shared value ramp with the painted plate (crunch, not airbrush)
    out[..., :3] = (np.round(out[..., :3].astype(np.float32) / 9.0) * 9.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(path)


def main() -> int:
    dirs = [Path(d) for d in sys.argv[1:]] or DEFAULT_DIRS
    n = 0
    for d in dirs:
        for p in sorted(d.rglob("*.png")):
            fidelity(p)
            n += 1
    print(f"fidelity pass over {n} pieces")
    return 0


if __name__ == "__main__":
    sys.exit(main())
