"""Six battle enemies, each drawn straight from a Skatopia lyric. Hand-authored
palette-indexed grids, outlined, given a 2-frame idle (bob / float / sway) and
saved as per-enemy spritesheets the BattleScene draws.

  slime        -> a rot-ooze with a pearl-tooth grin ('rot spots', 'teeth like pearls')
  drifter      -> a hooded ghost wanderer ('the ghosts in my house')
  luchador_grunt / luchador_mask -> masked reavers ('cannibals so eager')
  elite_wraith -> feather-haired, wide-mouthed wraith ('teeth like pearls, hair like feathers')
  the_conductor-> the boss: a gaunt conductor of the misery song, clock in his chest
                  ('trying to describe a sound', 'black clocks line the walls', melting clocks)
"""

from __future__ import annotations

from PIL import Image
from skatopia import render, outline, save

# --- grids -----------------------------------------------------------------

SLIME = [
    "......GGGGGGGG......",
    "....GGGCGGGGCGGG....",
    "...GGGGGGGGGGGGGG...",
    "..GGGGGGGGGGGGGGGG..",
    ".GGGGGGGGGGGGGGGGGG.",
    ".GGGKKGGGGGGGGKKGGG.",
    ".GGGKKGGGGGGGGKKGGG.",
    "GGGGGGGGGGGGGGGGGGGG",
    "GGGGGWGWGWGWGWGWGGGG",
    "GGgGGGGGGGGGGGGGGgGG",
    ".GgGGGGGGGGGGGGGGgG.",
    ".SgggGGGGGGGGGGgggS.",
    "..SggggggggggggggS..",
    "...SSggggggggggSS...",
    ".....SSSSSSSSSS.....",
]

DRIFTER = [
    ".....dddddd.....",
    "...ddDDDDDDdd...",
    "..dDDDDDDDDDDd..",
    "..dDDkkkkkkDDd..",
    "..dDkKKKKKKkDd..",
    "..dDkKCKKCKkDd..",  # cold pinpoint eyes
    "..dDkKKKKKKkDd..",
    "..dDDkkkkkkDDd..",
    ".dDDHHHHHHHHDDd.",
    ".dDHHHhhhhHHHDd.",
    ".dDHHhhhhhhHHDd.",
    ".dDHHHhhhhHHHDd.",
    "..DHHHhhhhHHHD..",
    "..dHHhh..hhHHd..",
    "..dHh......hHd..",
    "...h..d..d..h...",
    "...d..d..d..d...",
]

LUCHADOR_GRUNT = [
    ".....bBBBBb.....",
    "...bBBBBBBBBb...",
    "..bBWWBBBBWWBb..",  # mask eye-holes
    "..bBWWBBBBWWBb..",
    "..bBBBBrrBBBBb..",
    "..bBBBBBBBBBBb..",
    "..bBBBWWWWBBBb..",  # mask mouth-lace
    "...ffFFFFFFff...",
    "..fFFFFFFFFFFf..",
    ".fFFFfFFFFfFFFf.",  # muscled torso
    ".FFFFFFFFFFFFFF.",
    ".fFFFFFFFFFFFFf.",
    "..pFFpppppFFp...",
    "..pppppppppppp..",  # trunks
    "..ppp......ppp..",
    "..fFf......fFf..",
    "..dd........dd..",
]

LUCHADOR_MASK = [
    "....oyYYYYyo....",
    "..oyYPPPPPPYyo..",
    ".oYPWWPPPPWWPYo.",
    ".oYPWWPPPPWWPYo.",
    ".oYPPPPooPPPPYo.",
    ".oYPPPPPPPPPPYo.",
    ".oYPPWWWWWWPPYo.",
    "..PuFFFFFFFFuP..",  # cape shoulders
    ".PuFFFFFFFFFFuP.",
    "PuFFFfFFFFfFFFuP",
    "PuFFFFFFFFFFFFuP",
    ".PFFFFFFFFFFFFP.",
    "..PPBBBBBBBBPP..",  # championship belt
    "..pFFpppppFFp...",
    "..ppp......ppp..",
    "..fFf......fFf..",
    "..dd........dd..",
]

ELITE_WRAITH = [
    "..M..MLM..LM..M..",
    ".MLM.MLM.MLM.MLM.",  # feather hair streaming up
    "..MLLMMLMMLLM....",
    "...MLHHHHHHLM....",
    "...LHHHHHHHHL....",
    "..LHHCCHHCCHHL...",  # hollow cold eyes
    "..LHHHHHHHHHHL...",
    "..HHWWWWWWWWWHH..",  # wide grinning maw
    "..HWKWKWKWKWKWH..",  # pearl teeth over black
    "..HHWWWWWWWWWHH..",
    "...eHHHHHHHHe....",
    "..eeCcHHHHcCee...",  # tattered ocean shroud
    ".eecc cccc ccee..",
    ".ec c  cc  c ce..",
    "..e   c  c   e...",
    "...c        c...",
]

CONDUCTOR = [
    "........kkkkkk........",
    ".......kkkkkkkk.......",  # wild dark hair
    "......kkHHHHHHkk......",
    "......kHHHHHHHHk......",
    "......HHoHHHHoHH......",  # ember eyes
    "......HHHHHHHHHH......",
    "......HHHWWWWHHH......",  # gaunt grimace
    ".......dHHHHHHd.......",
    ".....DDddddddddDD.....",  # high collar
    "....DDkkkkkkkkkkDD..W.",  # baton raised in right hand
    "...DkkkkwwwwkkkkkD.WW.",
    "...Dkkkw WW wkkkkDWW..",  # clock face in chest
    "...Dkkw WrW wkkkkD....",  # clock hands (rust)
    "...Dkkw WWW wkkkkD....",
    "...Dkkkw    wkkkkD....",
    "...DkkkkwwwwkkkkkD....",
    "...DkkkkkkkkkkkkkD....",
    "....DkkkkkkkkkkkD.....",
    "....Dkkkk..kkkkkD.....",  # coat tails
    ".....kkd....dkkk.....",
    ".....dd......ddd.....",
]

ENEMIES = {
    "slime": (SLIME, "squash"),
    "drifter": (DRIFTER, "float"),
    "elite_wraith": (ELITE_WRAITH, "float"),
    "the_conductor": (CONDUCTOR, "sway"),
}


def _idle_frames(base: Image.Image, style: str) -> list[Image.Image]:
    """2-frame idle. Pad by 2px all round, then produce a resting frame and a
    motion frame (bob down / float up / sway sideways / squash)."""
    w, h = base.size
    pw, ph = w + 4, h + 4

    def framed(dx: int, dy: int, squash: int = 0) -> Image.Image:
        f = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        img = base
        if squash:
            img = base.resize((w + squash, max(1, h - squash)), Image.NEAREST)
        f.alpha_composite(img, (2 + dx + (w - img.width) // 2, 2 + dy + (h - img.height)))
        return f

    if style == "float":
        return [framed(0, 0), framed(0, -1)]
    if style == "sway":
        return [framed(-1, 0), framed(1, 0)]
    if style == "squash":
        return [framed(0, 0), framed(0, 1, squash=2)]
    return [framed(0, 0), framed(0, -1)]  # bob


# Every enemy is packed into a uniform 48x48 frame (bottom-centred) so the
# BattleScene can load them all with one frameWidth/Height and stand them on
# the same floor line regardless of their authored size.
FRAME = 48


def build_enemy(name: str) -> Image.Image:
    grid, style = ENEMIES[name]
    base = outline(render(grid))
    frames = _idle_frames(base, style)
    sheet = Image.new("RGBA", (FRAME * len(frames), FRAME), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        ox = i * FRAME + (FRAME - f.width) // 2
        oy = FRAME - f.height - 2  # feet 2px off the bottom
        sheet.alpha_composite(f, (ox, oy))
    return sheet


def build_all() -> None:
    for name in ENEMIES:
        save(build_enemy(name), f"sprites/enemies/{name}.png")
    print("enemies written")


def contact_sheet() -> Image.Image:
    imgs = [build_enemy(n).crop((0, 0, FRAME, FRAME)) for n in ENEMIES]
    gap = 6
    W = sum(im.width + gap for im in imgs) + gap
    H = max(im.height for im in imgs) + 8
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = gap
    for im in imgs:
        out.alpha_composite(im, (x, H - im.height - 2))
        x += im.width + gap
    return out


if __name__ == "__main__":
    build_all()
