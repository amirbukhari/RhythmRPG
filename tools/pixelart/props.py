"""Overworld decoration props -- scattered on the map at runtime to break the
tile grid and dress the drowned gothic world. Hand-authored, outlined,
drop-shadowed, packed into one uniform-frame sheet the OverworldScene places
deterministically. Each is themed to the Skatopia lyrics (bone, rot, rust,
drowned relics).
"""

from __future__ import annotations

from PIL import Image
from skatopia import render, outline, drop_shadow, rim_light, save

# 16-wide grids, bottom-anchored. "." = transparent.
DEAD_TREE = [
    "....k.......",
    "..k.k.k.....",
    "...kkk..k...",
    "kk..k..kk...",
    "..k.k.k.....",
    "....kk......",
    "....dk......",
    "....dd......",
    "....dd......",
    "...kdd......",
    "....dd.k....",
    "....ddk.....",
    "...kddd.....",
]

TOMBSTONE = [
    "...vvvv...",
    "..vwwwwv..",
    ".vwwwwwwv.",
    ".vwWvvwwv.",
    ".vwvXXvwv.",
    ".vwwvvwwv.",
    ".vwwwwwwv.",
    ".vwwwwwwv.",
    ".vwwvvwwv.",
    ".vwwwwwwv.",
    "gvwwwwwwvg",
    "gGvwwwwvGg",
]

BONE_PILE = [
    ".....W......",
    "..W.WWW..W..",
    ".WWWvvWWWW..",
    "WvWWWWWvvWW.",
    ".WvKKvWWvW..",
    "WWvWWWvWWvW.",
    ".vWvvWWvvW..",
    "..vWWvvWv...",
]

FUNGUS = [
    "..C....C....",
    ".CcC..CcC...",
    "CCcCC.CcCC..",
    ".cCc.CCcC...",
    "..v...vc....",
    "..v...v.....",
    ".gvg.gvg....",
]

REEDS = [
    "..g..g...g..",
    "g.G.g.G.g.G.",
    ".g.G.g.G.g..",
    "g.g.G.g.G.g.",
    ".G.g.g.G.g..",
    "g.g.G.g.g.G.",
    ".SgSgSgSgS..",
]

OBELISK_SHARD = [
    "...vw...",
    "... vw..",
    "..vwWv..",
    "..vwWv..",
    ".vwWWv..",
    ".vwWCv..",
    ".vwWWv..",
    "vwWWWvg.",
    "gvwWvgG.",
]

# A found-lore marker (PRD §8.8.2): a small carved rune stone, distinct from
# the purely decorative props above so it reads as interactive. The scene
# layers an additive glow pulse over this at runtime (tools/pixelart/fx.py),
# so the base art itself just needs a clean, readable silhouette + a carved
# glyph socket for that glow to sit in.
ECHO_RUNE = [
    "..vvvv..",
    ".vwwwwv.",
    "vwWWWWwv",
    "vwWCCCWv",
    "vwWCoCWv",
    "vwWCCCWv",
    "vwWWWWwv",
    ".vwwwwv.",
    "..vvvv..",
    "...vv...",
    "...gg...",
]

PROPS = {
    "dead_tree": DEAD_TREE,
    "tombstone": TOMBSTONE,
    "bone_pile": BONE_PILE,
    "fungus": FUNGUS,
    "reeds": REEDS,
    "obelisk_shard": OBELISK_SHARD,
    "echo_rune": ECHO_RUNE,
}
ORDER = list(PROPS.keys())
FRAME_W, FRAME_H = 20, 24


def build_prop(name: str) -> Image.Image:
    img = render(PROPS[name])
    img = rim_light(img, strength=0.35)
    img = outline(img)
    img = drop_shadow(img, 1, 1, 70)
    frame = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    frame.alpha_composite(img, ((FRAME_W - img.width) // 2, FRAME_H - img.height - 1))
    return frame


def build_sheet() -> Image.Image:
    sheet = Image.new("RGBA", (FRAME_W * len(ORDER), FRAME_H), (0, 0, 0, 0))
    for i, name in enumerate(ORDER):
        sheet.alpha_composite(build_prop(name), (i * FRAME_W, 0))
    return sheet


def contact() -> Image.Image:
    s = build_sheet()
    bg = Image.new("RGBA", s.size, (30, 40, 30, 255))
    bg.alpha_composite(s)
    return bg


if __name__ == "__main__":
    save(build_sheet(), "sprites/overworld/props.png")
    print("props written; order =", ORDER)
