"""UI skin art for *The Drowned Chorus*: an ornate nine-slice window frame for
panels/menus, and small stat icons (heart / focus / groove / target). Same
palette and pipeline as the rest of the art so the interface belongs to the
same world instead of being raw text on flat rectangles.
"""

from __future__ import annotations

from PIL import Image
from skatopia import PALETTE, render, outline, save

# --- nine-slice panel (24x24, 8px border corners) --------------------------
# Center is a flat fill so Phaser's NineSlice can stretch it cleanly; the
# border carries the ornament. Drawn directly for pixel-exact control.


def panel(boss: bool = False) -> Image.Image:
    S = 24
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = im.load()
    ink = PALETTE["K"]
    fill = (13, 15, 24, 235)  # translucent ink interior
    frame = PALETTE["p"] if not boss else PALETTE["b"]
    frame_hi = PALETTE["P"] if not boss else PALETTE["B"]
    bone = PALETTE["w"]

    for y in range(S):
        for x in range(S):
            edge = min(x, y, S - 1 - x, S - 1 - y)
            if edge == 0:
                px[x, y] = ink
            elif edge == 1:
                px[x, y] = bone  # bright rim
            elif edge == 2:
                px[x, y] = frame_hi
            elif edge == 3:
                px[x, y] = frame
            elif edge == 4:
                px[x, y] = ink
            else:
                px[x, y] = fill

    # corner flourishes: little bone studs
    for cx, cy in [(3, 3), (S - 4, 3), (3, S - 4), (S - 4, S - 4)]:
        px[cx, cy] = PALETTE["W"]
    return im


# --- 8x8 stat icons --------------------------------------------------------

HEART = [
    "........",
    ".BB..BB.",
    "BBBBBBBB",
    "BBBBBBBB",
    ".BBBBBB.",
    "..BBBB..",
    "...BB...",
    "........",
]
FOCUS = [  # a struck bell / droplet of breath
    "...WW...",
    "..WCCW..",
    "..WCCW..",
    ".WCCCCW.",
    ".WCCCCW.",
    "WCCCCCCW",
    ".W.WW.W.",
    "...WW...",
]
GROOVE = [  # a swelling star
    "...o....",
    "...y....",
    "o.oyo.o.",
    ".oyyyo..",
    "..oyo...",
    ".oyyyo..",
    "o.oyo.o.",
    "...y....",
]
TARGET = [
    "...B....",
    ".B.B.B..",
    "...B....",
    "BBB.BBB.",
    "...B....",
    ".B.B.B..",
    "...B....",
    "........",
]

ICONS = {"heart": HEART, "focus": FOCUS, "groove": GROOVE, "target": TARGET}
ICON_ORDER = list(ICONS.keys())


def icon(name: str) -> Image.Image:
    return outline(render(ICONS[name]))


def icon_sheet() -> Image.Image:
    imgs = [icon(n) for n in ICON_ORDER]
    w = max(i.width for i in imgs)
    h = max(i.height for i in imgs)
    sheet = Image.new("RGBA", (w * len(imgs), h), (0, 0, 0, 0))
    for i, im in enumerate(imgs):
        sheet.alpha_composite(im, (i * w, 0))
    return sheet, w, h  # type: ignore[return-value]


if __name__ == "__main__":
    save(panel(False), "ui/panel.png")
    save(panel(True), "ui/panel_boss.png")
    sheet, w, h = icon_sheet()
    save(sheet, "ui/icons.png")
    print(f"ui written; icon frame = {w}x{h}; order = {ICON_ORDER}")
