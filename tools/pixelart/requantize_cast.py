"""Re-quantize the CAST (band + enemies) to a tighter, per-FRAME colour
budget. fidelity_pass.py sizes its palette off the whole sheet's opaque
area; for a multi-frame strip that inflates the budget (a 2-4 frame sheet
reads as one huge sprite), so characters kept soft gradient banding instead
of HLD's flat cel blocks. This computes the budget from area-PER-FRAME
(known frame counts below) and re-quantizes on top of the already-despilled
art from fidelity_pass.py.

Run AFTER fidelity_pass.py has already despilled/hardened these sheets.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

# path (relative to assets/sprites) -> frame count
TARGETS: dict[str, int] = {
    "band/mir/idle.png": 2, "band/mir/run.png": 4, "band/mir/attack.png": 3,
    "enemies/slime.png": 2, "enemies/drifter.png": 2, "enemies/elite_wraith.png": 2,
}

MAX_COLORS = 16  # characters read flatter with a tighter cap than props


def requantize(path: Path, frames: int) -> None:
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    alpha = a[..., 3]
    opaque = alpha >= 128
    if not opaque.any():
        return
    per_frame_area = int(opaque.sum()) / max(1, frames)
    colors = int(np.clip(5 + per_frame_area**0.5 / 2.6, 6, MAX_COLORS))
    rgb = Image.fromarray(a[..., :3], "RGB")
    q = rgb.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    qa = np.array(q)
    lum = a[..., :3].astype(np.float32).max(axis=2)
    hot = lum > 190  # keep emissive highlights (eyes, embers) from flattening out
    qa[hot] = a[..., :3][hot]
    out = np.dstack([qa, alpha])
    out[..., :3] = (np.round(out[..., :3].astype(np.float32) / 11.0) * 11.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(path)
    print(f"{path.relative_to(ROOT)}: {colors} colours ({frames} frames, {per_frame_area:.0f}px/frame)")


def main() -> int:
    for rel, frames in TARGETS.items():
        p = ROOT / "assets" / "sprites" / rel
        if p.exists():
            requantize(p, frames)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
