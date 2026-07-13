"""The Conductor at native colossal resolution (PRD §11.1: bosses 96-180px,
authored at size -- NOT a small sprite scaled up). ~46x66 native painting;
displayed at ~1.6x it stands ~105px, towering over the 24px player with
crisp, intentional pixels instead of upscale blur.

Hybrid authored painting (same discipline as backgrounds.py): the coat is a
shaped, fold-shaded silhouette; the face, collar, chest clock, hands and
baton are placed deliberately. Two frames: beat-down (baton high) and
beat-up (baton swept, coat hem sways) -- a real conducting motion, not a
position nudge.
"""

from __future__ import annotations

import math
from PIL import Image
from skatopia import PALETTE, outline, save

BW, BH = 46, 66  # native painting size


def _paint(frame: int) -> Image.Image:
    im = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    px = im.load()
    K, k, d, D = PALETTE["K"], PALETTE["k"], PALETTE["d"], PALETTE["D"]
    H_, h = PALETTE["H"], PALETTE["h"]
    W_, w, v = PALETTE["W"], PALETTE["w"], PALETTE["v"]
    o, y, r, B = PALETTE["o"], PALETTE["y"], PALETTE["r"], PALETTE["B"]

    def put(x, yy, c):
        if 0 <= x < BW and 0 <= yy < BH:
            px[x, yy] = c

    cx = 22
    # --- coat: flaring silhouette with ragged, swaying hem ---------------
    sway = 1 if frame else -1
    for yy in range(16, BH):
        t = (yy - 16) / (BH - 16)
        half = round(9 + 14 * t)
        wob = round(math.sin(yy * 0.5) * (1 + t * 1.5)) if yy > BH - 10 else 0
        for x in range(cx - half + min(0, wob * sway), cx + half + max(0, wob * sway)):
            put(x, yy, k)
        # left rim light + right deep shadow (consistent top-left source)
        put(cx - half + min(0, wob * sway), yy, D)
        put(cx - half + 1 + min(0, wob * sway), yy, d)
        put(cx + half - 1 + max(0, wob * sway), yy, K)
    # ragged hem bite-outs
    for x0 in (cx - 16, cx - 7, cx + 3, cx + 12):
        for i in range(3):
            for x in range(x0, x0 + 3 - i):
                put(x + i, BH - 1 - i, (0, 0, 0, 0))
    # vertical fold shading
    for fx in (cx - 6, cx + 1, cx + 7):
        for yy in range(20, BH - 2):
            put(fx + round((yy - 20) * 0.12), yy, K)
    # lapels: bone-pale V from the collar
    for i in range(9):
        put(cx - 2 - i // 2, 17 + i, v)
        put(cx + 2 + i // 2, 17 + i, v)

    # --- chest clock (his heart) ------------------------------------------
    ccy = 30
    for a in range(0, 360, 4):
        put(cx + round(7 * math.cos(math.radians(a))), ccy + round(7 * math.sin(math.radians(a))), w)
        put(cx + round(6 * math.cos(math.radians(a))), ccy + round(6 * math.sin(math.radians(a))), v)
    for yy in range(ccy - 5, ccy + 6):  # face
        for x in range(cx - 5, cx + 6):
            if (x - cx) ** 2 + (yy - ccy) ** 2 <= 27:
                put(x, yy, W_)
    put(cx, ccy - 4, K); put(cx + 4, ccy, K); put(cx, ccy + 4, K); put(cx - 4, ccy, K)
    # hands: stopped just short of the hour
    for i in range(4):
        put(cx + i, ccy - i, r)
    for i in range(3):
        put(cx - i, ccy - i // 2, B)
    for dseg in range(4):  # the melt: clock dripping down the coat
        put(cx + 3, ccy + 7 + dseg, w if dseg < 2 else v)

    # --- head: gaunt, wild-haired, ember-eyed ------------------------------
    for yy in range(0, 9):  # wild hair mass
        half = 7 - abs(4 - yy) // 2
        for x in range(cx - half, cx + half + 1):
            if (x * 7 + yy * 13) % 5:
                put(x, yy, K if (x + yy) % 3 else k)
    for spike in ((cx - 8, 2), (cx + 8, 3), (cx - 6, 0), (cx + 6, 0)):
        put(spike[0], spike[1], k)
    for yy in range(6, 15):  # face
        half = 5 if yy < 12 else 4 - (yy - 12)
        for x in range(cx - half, cx + half + 1):
            put(x, yy, H_ if yy < 12 else h)
    put(cx - 3, 9, o); put(cx - 2, 9, y)  # ember eyes
    put(cx + 2, 9, o); put(cx + 3, 9, y)
    for x in range(cx - 2, cx + 3):  # grim mouth
        put(x, 13, K)
    for yy in range(7, 12):  # hollow cheeks
        put(cx - 4, yy, h); put(cx + 4, yy, h)
    for yy in range(15, 18):  # high collar swallowing the jaw
        for x in range(cx - 7, cx + 8):
            put(x, yy, D if yy == 15 else d)

    # --- arms ---------------------------------------------------------------
    # left arm: crooked in, pale hand holding the score against the coat
    for i in range(7):
        put(cx - 9 - i // 2, 20 + i, d)
        put(cx - 10 - i // 2, 20 + i, k)
    for x in range(cx - 14, cx - 10):
        put(x, 27, H_); put(x, 28, h)
    # right arm + baton: frame 0 raised high, frame 1 swept to the side
    if frame == 0:
        pts = [(i, -i) for i in range(10)]  # up-right diagonal
        bat = [(10 + i, -10 - i) for i in range(7)]
    else:
        pts = [(i, -i // 3) for i in range(11)]  # swept outward
        bat = [(11 + i, -4 - i // 2) for i in range(8)]
    for ddx, ddy in pts:
        put(cx + 8 + ddx, 22 + ddy, k)
        put(cx + 8 + ddx, 23 + ddy, d)
    hx, hy = cx + 8 + pts[-1][0], 22 + pts[-1][1]
    put(hx, hy, H_); put(hx + 1, hy, H_)  # hand
    for i, (ddx, ddy) in enumerate(bat):
        put(cx + 8 + ddx, 22 + ddy, w if i < 5 else W_)  # bone baton, bright tip
    return im


def build_sheet() -> Image.Image:
    frames = [outline(_paint(0)), outline(_paint(1))]
    fw, fh = 52, 72
    sheet = Image.new("RGBA", (fw * 2, fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * fw + (fw - f.width) // 2, fh - f.height - 1))
    return sheet


if __name__ == "__main__":
    save(build_sheet(), "sprites/enemies/conductor_colossal.png")
    print("colossal conductor written (frames 52x72)")
