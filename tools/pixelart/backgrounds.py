"""Battle backdrops (320x180, the game's internal resolution). Painted
deterministically in the Skatopia palette: the drowned world the party fights
through -- an abyssal hall of bone obelisks under a cold current, with a
ground plane the sprites stand on. One general backdrop plus a redder,
clock-lined boss variant ('black clocks line the walls').
"""

from __future__ import annotations

import random
from PIL import Image
from skatopia import PALETTE, save

W, H = 320, 180
HORIZON = 116  # sprites stand around here; ground below


def _vgrad(px, top, bot, y0, y1) -> None:
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0 - 1))
        c = tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
        for x in range(W):
            px[x, y] = c


def _obelisk(px, cx, base_y, h, w, body, edge, glow) -> None:
    top = base_y - h
    for y in range(top, base_y):
        t = (y - top) / max(1, h)
        half = max(1, round(w * (0.4 + 0.6 * t)))
        for x in range(cx - half, cx + half):
            if 0 <= x < W:
                px[x, y] = body
        if cx - half >= 0:
            px[cx - half, y] = edge
        if cx + half - 1 < W:
            px[cx + half - 1, y] = edge
    # a faint carved glyph glow near the top
    for i in range(3):
        yy = top + 4 + i * 3
        if 0 <= yy < H:
            px[cx, yy] = glow


def build(boss: bool = False) -> Image.Image:
    rng = random.Random(7 if not boss else 99)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    px = im.load()

    # water column: teal current up top fading to abyssal black at the floor
    top = PALETTE["c"] if not boss else PALETTE["p"]
    mid = PALETTE["e"] if not boss else PALETTE["X"]
    _vgrad(px, top, mid, 0, HORIZON)
    _vgrad(px, mid, PALETTE["K"], HORIZON, H)

    # drifting motes / bubbles in the water
    for _ in range(90):
        x, y = rng.randrange(W), rng.randrange(0, HORIZON)
        px[x, y] = PALETTE["C"] if rng.random() < 0.5 else PALETTE["a"]

    # a row of bone obelisks receding across the back
    body = PALETTE["V"]
    edge = PALETTE["w"]
    glow = PALETTE["B"] if boss else PALETTE["C"]
    for cx, h, w in [(40, 70, 7), (95, 92, 9), (160, 78, 8), (225, 96, 10), (285, 68, 7)]:
        _obelisk(px, cx, HORIZON + 6, h, w, body, edge, glow)

    if boss:
        # black clocks line the walls
        for cx, cy in [(60, 40), (255, 46), (150, 30)]:
            for a in range(-4, 5):
                px[cx + a, cy - 4] = PALETTE["k"]
                px[cx + a, cy + 4] = PALETTE["k"]
                px[cx - 4, cy + a] = PALETTE["k"]
                px[cx + 4, cy + a] = PALETTE["k"]
            px[cx, cy] = PALETTE["W"]
            px[cx, cy - 2] = PALETTE["r"]
            px[cx + 2, cy] = PALETTE["r"]

    # ground plane: wet dark stone with scattered rubble + a soft near edge
    _vgrad(px, PALETTE["N"], PALETTE["k"], HORIZON, H)
    for _ in range(240):
        x, y = rng.randrange(W), rng.randrange(HORIZON, H)
        r = rng.random()
        px[x, y] = PALETTE["m"] if r < 0.5 else PALETTE["d"] if r < 0.8 else PALETTE["g"]
    # a lighter contact line where floor meets the water
    for x in range(W):
        px[x, HORIZON] = PALETTE["m"]
        px[x, HORIZON + 1] = PALETTE["N"]

    # vignette
    for y in range(H):
        for x in range(W):
            edge_d = min(x, W - 1 - x, y, H - 1 - y)
            if edge_d < 24:
                c = px[x, y]
                f = edge_d / 24
                px[x, y] = tuple(round(c[i] * (0.45 + 0.55 * f)) for i in range(3)) + (255,)
    return im


if __name__ == "__main__":
    save(build(False), "backgrounds/battle_abyss.png")
    save(build(True), "backgrounds/battle_conductor.png")
    print("backgrounds written")
