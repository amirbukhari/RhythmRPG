"""Lunal at the Keep -- the ending's boss (world-bible v16.0, §8-§9).

She replaces the retired Conductor. He was a COLOSSUS: ~52x72 native, displayed
at ~72px, buying dread with sheer scale (a towering coat over a 22px Mir). Lunal
does the opposite on purpose. She is human -- the same height class as Mir --
and the menace has to come from stillness, not size (PRD Open Question 3b). A
mother doing something monstrous without ever raising her voice.

So she is authored small and quiet: a worn hunter's coat, her head bowed and
turned three-quarters AWAY from us -- we never quite get her face -- one pale
hand resting on the top of a low cage at her feet. Inside the cage a small
huddled shape, and one amber lamp hooked to the bars throwing warm light on the
saddest thing in the room. The two frames are barely a motion: in the second her
head turns a little further down and the resting hand CLOSES on a bar. She hunts
to keep. She will not let go.

Same deterministic skatopia discipline as the rest of the authored cast (no image
generation, no purple -- teal, stone, bone, rust, lamp-amber). Painted at native
resolution, outlined, then upscaled 4x NEAREST so the engine downscales crisp
instead of blurring an upscale -- the HD-density contract BootScene loads against.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from skatopia import PALETTE, outline, save  # noqa: E402

BW, BH = 52, 56  # native painting size (figure ~44px tall; cage at her feet)
UPSCALE = 4      # HD density: engine downscales, never upscales


def _paint(frame: int) -> Image.Image:
    im = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    px = im.load()
    K, k, d, D = PALETTE["K"], PALETTE["k"], PALETTE["d"], PALETTE["D"]
    W_, w, v, V = PALETTE["W"], PALETTE["w"], PALETTE["v"], PALETTE["V"]
    C, c, e, E, a = PALETTE["C"], PALETTE["c"], PALETTE["e"], PALETTE["E"], PALETTE["a"]
    H_, h = PALETTE["H"], PALETTE["h"]
    M, m, L, N = PALETTE["M"], PALETTE["m"], PALETTE["L"], PALETTE["N"]
    o, y, r, R = PALETTE["o"], PALETTE["y"], PALETTE["r"], PALETTE["R"]

    def put(x, yy, col):
        if 0 <= x < BW and 0 <= yy < BH:
            px[x, yy] = col

    def vline(x, y0, y1, col):
        for yy in range(y0, y1 + 1):
            put(x, yy, col)

    # In the second frame her head bows a touch further and the hand grips.
    bow = 1 if frame else 0
    cx = 19  # figure centre (left of frame; the cage sits to her right)

    # --- the coat: a worn hunter's coat, floor-length, slightly hunched ------
    # She is turned three-quarters away, so the coat's near edge (our left) takes
    # the top-left light as a thin teal rim; the far side falls to deep shade.
    for yy in range(20, 51):
        t = (yy - 20) / 30.0
        half = round(6 + 5 * t)          # tapers a little toward the shoulders
        lean = round(1.5 * t)            # hem drifts toward the cage
        x0 = cx - half + lean
        x1 = cx + half + lean
        for x in range(x0, x1 + 1):
            put(x, yy, e)                # coat body: dark teal
        for x in range(x0 + 1, cx + lean):
            put(x, yy, c)                # midtone where light catches the back
        put(x0, yy, c)                   # near-edge rim (light side)
        put(x0 - 1, yy, C) if yy % 3 else None  # faint bright rim, broken
        put(x1, yy, K)                   # far edge falls to void
        put(x1 - 1, yy, E)
    # vertical fold shadows down the back
    for fx in (cx - 3, cx + 2, cx + 6):
        for yy in range(24, 49):
            put(fx + round((yy - 24) * 0.10), yy, E)
    # ragged wet hem
    for x in range(cx - 9, cx + 13):
        if (x * 5) % 3 == 0:
            put(x, 50, K)
            put(x, 51, K if (x % 2) else (0, 0, 0, 0))

    # --- a shawl/collar heaped at the shoulders (bone-grey, rain-heavy) ------
    for yy in range(17 + bow, 23 + bow):
        half = 7 - (yy - (17 + bow))
        for x in range(cx - half, cx + half + 2):
            put(x, yy, V)
        put(cx - half, yy, v)            # light rim on the shawl
        put(cx + half + 1, yy, N)

    # --- neck: a short pale column so the head sits on her, not above her ----
    for yy in range(15 + bow, 18 + bow):
        put(cx - 1, yy, h); put(cx, yy, H_); put(cx + 1, yy, h)

    # --- head: bowed and turned AWAY; we get the back and a sliver of cheek --
    # A little smaller and taller-than-round so it never reads as a plain ball,
    # with a tied-back knot breaking the silhouette at the back.
    hx, hy = cx + 1, 8 + bow             # head centre, dips with the bow
    for yy in range(hy - 5, hy + 6):     # hair mass (dark, tied back), ovoid
        rad = 4 - (abs(yy - hy) + 1) // 3
        for x in range(hx - rad, hx + rad + 1):
            put(x, yy, k)
    for yy in range(hy - 4, hy + 4):     # crown highlight, top-left source
        put(hx - (3 - abs(yy - hy) // 3), yy, d)
    put(hx - 3, hy - 2, D)
    # tied-back knot at the back of the skull + a strand fallen toward the cage
    put(hx + 4, hy - 1, k); put(hx + 5, hy, k); put(hx + 4, hy + 1, d)
    put(hx + 3, hy + 4, k); put(hx + 4, hy + 5, d)
    # the one sliver of face we are allowed: a lit cheek/jaw, turned down-away
    put(hx - 3, hy, h); put(hx - 4, hy + 1, H_); put(hx - 4, hy + 2, H_)
    put(hx - 3, hy + 3, h); put(hx - 3, hy + 4, h)  # jawline into the neck

    # --- arms ----------------------------------------------------------------
    # near arm (our side) hangs slack down the coat -- doing nothing, at rest.
    for i in range(11):
        put(cx - 6, 23 + i, d)
        put(cx - 5, 23 + i, e)
    put(cx - 6, 34, h); put(cx - 6, 35, H_)   # slack pale hand at her side

    # far arm reaches DOWN-RIGHT to the top of the cage. In frame 1 it closes.
    arm = [(cx + 4, 24), (cx + 6, 27), (cx + 8, 30), (cx + 10, 33), (cx + 12, 36)]
    for (ax, ay) in arm:
        put(ax, ay, d); put(ax + 1, ay, e); put(ax, ay + 1, K)
    # the hand on the bars -- the whole beat is here
    hxr, hyr = 33, 37
    if frame == 0:
        for x in range(hxr - 1, hxr + 3):   # resting, open, fingers spread
            put(x, hyr, H_)
        put(hxr, hyr + 1, h); put(hxr + 2, hyr + 1, h)
    else:
        for x in range(hxr - 1, hxr + 3):   # closed around the bar, knuckles
            put(x, hyr, h)
        put(hxr, hyr - 1, H_); put(hxr + 1, hyr, H_)
        put(hxr, hyr + 1, h); put(hxr + 1, hyr + 1, h)

    # --- the cage at her feet (metal), a small huddled shape inside ----------
    cgx0, cgx1, cgy0, cgy1 = 30, 47, 38, 50
    for x in range(cgx0, cgx1 + 1):      # top + bottom rails
        put(x, cgy0, M); put(x, cgy0 - 1, m)
        put(x, cgy1, m); put(x, cgy1 + 1, N)
    for bx in range(cgx0, cgx1 + 1, 3):  # vertical bars
        vline(bx, cgy0, cgy1, M)
        vline(bx, cgy0 + 1, cgy1 - 1, L) if bx == cgx0 else None  # near bar catches light
    put(cgx0, cgy0, L); put(cgx1, cgy0, N)
    # interior gloom, then the huddled form -- a small rounded back, knees up
    for yy in range(cgy0 + 2, cgy1):
        for x in range(cgx0 + 1, cgx1):
            if px[x, yy] == (0, 0, 0, 0):
                put(x, yy, K)
    for x in range(cgx0 + 4, cgx0 + 12):    # the curl of a small back
        arc = cgy1 - 1 - int(2.2 * (1 - ((x - (cgx0 + 8)) / 4.0) ** 2))
        for yy in range(arc, cgy1):
            put(x, yy, d)
        put(x, arc, k)
    put(cgx0 + 6, cgy1 - 3, w); put(cgx0 + 7, cgy1 - 3, W_)  # a pale small head
    put(cgx0 + 6, cgy1 - 2, v); put(cgx0 + 8, cgy1 - 2, v)   # rounded shoulders

    # --- one lamp hooked to the cage corner: the warmth that makes it sad ----
    lx, ly = cgx1, cgy0 - 3
    put(lx, ly - 1, m)                   # hook
    for yy in range(ly, ly + 3):         # little lamp body
        for x in range(lx - 1, lx + 2):
            put(x, yy, N)
    put(lx, ly, o); put(lx, ly + 1, y)   # the flame
    # a soft amber wash falling left across the bars and her grieving hand
    glow = [(lx - 2, ly + 1, o), (lx - 3, ly + 2, y), (lx - 4, ly + 3, o),
            (lx - 5, ly + 4, y), (hxr + 3, hyr, o), (hxr + 2, hyr - 1, y)]
    for (gx, gy, gc) in glow:
        if px[gx, gy] != (0, 0, 0, 0) or (gx, gy) in ((lx - 2, ly + 1),):
            put(gx, gy, gc)
        else:
            put(gx, gy, gc)
    # faint warm catch on the near coat edge from the lamp (low, right side)
    for yy in range(40, 49):
        put(cx + round(6 + (yy - 40) * 0.16), yy, r if yy % 2 else R)

    return im


def build_sheet() -> Image.Image:
    frames = [outline(_paint(0)), outline(_paint(1))]
    fw = max(f.width for f in frames)
    fh = max(f.height for f in frames)
    up = []
    for f in frames:
        canvas = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        canvas.alpha_composite(f, ((fw - f.width) // 2, fh - f.height))
        up.append(canvas.resize((fw * UPSCALE, fh * UPSCALE), Image.NEAREST))
    sheet = Image.new("RGBA", (up[0].width * 2, up[0].height), (0, 0, 0, 0))
    for i, f in enumerate(up):
        sheet.alpha_composite(f, (i * f.width, 0))
    return sheet, up[0].size


if __name__ == "__main__":
    sheet, (fw, fh) = build_sheet()
    save(sheet, "sprites/enemies/lunal.png")
    print(f"lunal written -- 2 frames {fw}x{fh} (native {BW}x{BH} x{UPSCALE})")
