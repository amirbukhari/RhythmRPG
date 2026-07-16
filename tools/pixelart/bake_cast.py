"""Bake the CAST into the world's pixel register (the last fractional-texel
elements after bake_world_scale.py). Characters rendered at 0.33-0.62 had
finer, non-integer pixels than the chunky environment. Resample each sheet so
its runtime scale is a clean half-multiple (integer texels on the 2x canvas):

  * band strips: 72px frames -> 50px; player/followers render at 0.5
    (25px world -- the 1.7m anchor, unchanged size, clean texels);
  * foe sheets: each to its FIGHT size (slime 32, drifter 35, wraith 45);
    fight and standing foes both render at 1.0.

Frame boundaries survive whole-strip resizing because frame widths scale by
the same factor. Alpha is hardened and silhouette edges despilled (same
discipline as fidelity_pass.py) but WITHOUT palette quantization -- faces
survive.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BAND = ROOT / "assets" / "sprites" / "band"
ENEMIES = ROOT / "assets" / "sprites" / "enemies"

# sheet -> (old_frame_h, new_frame_h)
FOE_TARGETS = {"slime.png": 32, "drifter.png": 35, "elite_wraith.png": 45}
BAND_FRAME = (72, 50)


def harden(im: Image.Image) -> Image.Image:
    a = np.array(im)
    alpha = a[..., 3]
    mask = alpha >= 96
    n = np.zeros_like(mask, dtype=np.int16)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                n += np.roll(np.roll(mask, dy, 0), dx, 1)
    mask &= n >= 2
    interior = mask & np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1)
    ring = mask & ~interior
    if interior.any() and ring.any():
        iys, ixs = np.where(interior)
        for y, x in zip(*np.where(ring)):
            d = (iys - y) ** 2 + (ixs - x) ** 2
            j = int(np.argmin(d))
            if d[j] <= 16:
                px = a[y, x, :3].astype(int)
                nb = a[iys[j], ixs[j], :3].astype(int)
                if int(px.max() - px.min()) < 30 and int(np.abs(px - nb).sum()) > 90:
                    a[y, x, :3] = nb
    a[..., 3] = np.where(mask, 255, 0).astype(np.uint8)
    return Image.fromarray(a)


def resample(path: Path, old_h: int, new_h: int) -> None:
    im = Image.open(path).convert("RGBA")
    if im.height != old_h:
        print(f"skip {path.name}: height {im.height} != {old_h}")
        return
    w = round(im.width * new_h / old_h)
    small = im.resize((w, new_h), Image.LANCZOS)
    harden(small).save(path)
    print(f"{path.parent.name}/{path.name}: {im.width}x{im.height} -> {w}x{new_h}")


def main() -> int:
    for member_dir in sorted(BAND.iterdir()):
        if not member_dir.is_dir():
            continue
        for strip in sorted(member_dir.glob("*.png")):
            resample(strip, *BAND_FRAME)
    for name, target in FOE_TARGETS.items():
        p = ENEMIES / name
        if p.exists():
            resample(p, 72, target)
    return 0


if __name__ == "__main__":
    return_code = main()
    raise SystemExit(return_code)
