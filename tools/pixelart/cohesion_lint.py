"""Cohesion lint -- the art cohesion audit's checks, made permanent.

The 2026-07-16 audit (docs/design/art-cohesion-audit.md) found the "not
cohesive" feel came from assets that individually escaped the pipeline's
register: unquantized colour blooms (C4), an unkeyed rectangular generation
backdrop and an orphan pixel island shipped as-is (C5). Each escape was a
one-off review miss; this lint turns those reviews into a gate.

Checks, per committed sprite PNG (v11.0: re-scoped to STRUCTURAL checks --
the colour-budget and hard-alpha rules were pixel-register rules and retired
with it):
  * no orphan specks -- every alpha island is either >= 9 px or >= 3% of the
                        largest island (composed groups like a candle cluster
                        pass; a stray keying speck fails);
  * no backdrop card -- a piece whose tight bounding box is nearly fully
                        opaque with a bright border is an unkeyed
                        generation backdrop.

Exempt by design: fx/ (soft additive gradients), ui/panel* (9-slice soft
edges), the painted ground plate + tileset (own the many-colour register),
and reference/ art.

Run it standalone or via generate_all.py:
    python3 tools/pixelart/cohesion_lint.py
Exit code 1 on any finding, so CI/regeneration can gate on it.
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"

EXEMPT_PARTS = ("reference", "fx", "audio", "tilemaps")
EXEMPT_FILES = {"panel.png", "panel_boss.png"}
# soft-alpha allowance only where the design calls for it (none today beyond
# the exemptions above)
OUTLINE_MAX = 40  # channel value at/below which a colour reads as "outline dark"


def islands(mask: np.ndarray) -> list[int]:
    lab = np.zeros(mask.shape, dtype=int)
    sizes: list[int] = []
    cur = 0
    for y, x in zip(*np.where(mask)):
        if lab[y, x]:
            continue
        cur += 1
        size = 0
        q = deque([(y, x)])
        lab[y, x] = cur
        while q:
            cy, cx = q.popleft()
            size += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = cur
                        q.append((ny, nx))
        sizes.append(size)
    return sizes


def lint(path: Path) -> list[str]:
    findings: list[str] = []
    a = np.array(Image.open(path).convert("RGBA"))
    alpha = a[..., 3]
    mask = alpha > 128  # soft HD edges: judge structure by the solid core

    if not mask.any():
        return [f"{path}: fully transparent"]

    # orphan specks (multi-frame sheets excluded: frames are separate islands)
    rel = path.relative_to(ASSETS).as_posix()
    multi_frame = rel.startswith(("sprites/band/", "sprites/enemies/", "sprites/overworld/"))
    if not multi_frame:
        sizes = sorted(islands(mask), reverse=True)
        for s in sizes[1:]:
            if s < 9 and s < 0.03 * sizes[0]:
                findings.append(f"{path}: orphan {s}px island (keying speck)")
                break

    # backdrop card: near-full bbox coverage with a non-outline border ring
    # (backgrounds are full-canvas key-art by design)
    if rel.startswith("backgrounds/"):
        return findings
    ys, xs = np.where(mask)
    bh, bw = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
    fill = mask.sum() / float(bh * bw)
    if fill > 0.95 and bh >= 8 and bw >= 8:
        box = a[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
        ring = np.concatenate([box[0, :, :3], box[-1, :, :3], box[:, 0, :3], box[:, -1, :3]])
        if int(np.median(ring.max(axis=1))) > OUTLINE_MAX:
            findings.append(f"{path}: bbox {fill:.0%} opaque with bright border -- unkeyed backdrop card?")

    return findings


def main() -> int:
    failures: list[str] = []
    n = 0
    for path in sorted(ASSETS.rglob("*.png")):
        rel = path.relative_to(ASSETS)
        if any(part in EXEMPT_PARTS for part in rel.parts) or path.name in EXEMPT_FILES:
            continue
        failures += lint(path)
        n += 1
    print(f"cohesion lint over {n} assets: {len(failures)} finding(s)")
    for f in failures:
        print("  " + f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
