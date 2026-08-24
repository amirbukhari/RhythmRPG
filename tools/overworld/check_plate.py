"""Measured gate on the painted ground plate -- see style-contract §4.3.

    python3 tools/overworld/check_plate.py [--top N]

WHY THIS EXISTS
The plate is 5696x3200. A reviewer looking at it scaled to fit a window cannot
see that a 96x72 patch of it has ZERO texture, and the plate shipped with 136
such patches in the Fold alone: the eelgrass, road and water passes fully
overwrote the ground field with a colour carrying only low-frequency noise, and
the quantized terrace tone then made the product exactly constant.

So flatness is measured. Every 8x8 block of every chunk gets a per-channel
standard deviation; anything under FLAT_STD is a placeholder patch by
definition, because nothing in this world is a solid colour. Isolated blocks are
tolerated (a genuinely still pool, the transparent padding past the map edge);
CLUSTERS are not, because a cluster is a shape, and a hard-edged flat shape is
the thing a player sees.

Exit code is 1 if any cluster is at least MIN_CLUSTER blocks, so this can sit in
the art build the same way `tsc --noEmit` sits in the code build.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PLATES = ROOT / "assets" / "tilemaps"

BLOCK = 8
FLAT_STD = 0.6
# 4 blocks = a 16x16 patch = one map tile of dead colour. Below that it is a
# rounding artefact at the bottom of a value range, not a visible shape.
MIN_CLUSTER = 4
CHUNK = 1024
S = 16  # plate px per map tile


def _label(mask):
    """Connected components (4-neighbour), so scipy is not a dependency."""
    lab = np.zeros(mask.shape, dtype=np.int32)
    cur = 0
    h, w = mask.shape
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or lab[sy, sx]:
                continue
            cur += 1
            stack = [(sy, sx)]
            lab[sy, sx] = cur
            while stack:
                y, x = stack.pop()
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = cur
                        stack.append((ny, nx))
    return lab, cur


def scan(path):
    """[(blocks, tile_row, tile_col, tile_h, tile_w, rgb)] for one chunk."""
    r, c = (int(v) for v in path.stem.split("_")[-2:])
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    hh, ww = a.shape[0] // BLOCK, a.shape[1] // BLOCK
    blk = a[: hh * BLOCK, : ww * BLOCK].reshape(hh, BLOCK, ww, BLOCK, 3)
    flat = blk.std(axis=(1, 3)).max(axis=2) < FLAT_STD
    mean = blk.mean(axis=(1, 3))
    lab, n = _label(flat)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < MIN_CLUSTER:
            continue
        y0 = (r * CHUNK + ys.min() * BLOCK) // S
        x0 = (c * CHUNK + xs.min() * BLOCK) // S
        y1 = (r * CHUNK + ys.max() * BLOCK + BLOCK) // S
        x1 = (c * CHUNK + xs.max() * BLOCK + BLOCK) // S
        out.append((len(ys), y0, x0, y1 - y0, x1 - x0, tuple(mean[ys[0], xs[0]].astype(int))))
    return out


def main(argv):
    top = 12
    if "--top" in argv:
        top = int(argv[argv.index("--top") + 1])
    paths = sorted(PLATES.glob("ground_plate_*_*.png"))
    if not paths:
        print("no ground plates -- run tools/overworld/paint_ground.py first")
        return 2
    hits = []
    for p in paths:
        hits.extend(scan(p))
    hits.sort(reverse=True)
    total = sum(h[0] for h in hits)
    print("%d chunks scanned, %d flat clusters >= %d blocks (%d blocks total)"
          % (len(paths), len(hits), MIN_CLUSTER, total))
    for blocks, tr, tc, th, tw, rgb in hits[:top]:
        print("  %4d blocks  tile (r%d, c%d) %dx%d tiles  rgb%s" % (blocks, tr, tc, th, tw, rgb))
    if len(hits) > top:
        print("  ... %d more" % (len(hits) - top))
    if hits:
        by_col = Counter(h[5] for h in hits)
        print("commonest flat colours: %s" % ", ".join("%s x%d" % kv for kv in by_col.most_common(4)))
        print("FAIL: the ground is painted, not filled (style-contract §4.3)")
        return 1
    print("PASS: no flat patches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
