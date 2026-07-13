"""Colossal overworld landmarks (PRD §8.8.1 / §11.1.1) -- one silhouette-first
set-piece per region that gives the explorable world scale and tells its
untold story wordlessly (world-bible §5b). These are far bigger than the
scattered decoration props (props.py): a wrecked ship listing in the
shallows, a salt-crusted headframe over the mine, a drowned carnival wheel,
a leaning tenement over the attic, and the Conductor's obelisk-spire before
the hall. Rendered outlined + rim-lit + drop-shadowed like every other
sprite, packed into one fixed-frame sheet the OverworldScene places at
authored positions (one per region, well off the critical path).

Frame order matches tiles.REGIONS: shallows, saltmines, pit, attic, hall.
"""

from __future__ import annotations

from PIL import Image
from skatopia import render, outline, rim_light, drop_shadow, save

# 5 palette-key grids, bottom-anchored, ~40-56px tall so they tower over the
# 16px tiles and the 24px hero. "." / " " = transparent.

# Shallows: a fishing sloop run aground and broken-backed, one mast snapped,
# hull staved in -- "everyone's boat but mine" (Baker's Ledger echo).
DROWNED_SHIP = [
    "...........k............",
    "..........kMk...........",
    "..........kMk...........",
    ".........kkMkk..........",
    "..........kMk...........",
    "..........vMv...........",
    "..........vMv...........",
    ".....v....vMv....v......",
    ".....vv...vMv...vv......",
    "....vwwv..vMv..vwwv.....",
    "....vwwv..vMv..vwwv.....",
    "...vwwwwv.vMv.vwwwwv....",
    "...dwwwwd.dMd.dwwwwd....",
    "..dfffffddddddffffffd...",
    "..dfffffffffffffffffd...",
    "..hffffffffffffffffhd...",
    "...hffffffffffffffh.....",
    "....hhffffffffffhh......",
    "......hhhffffhhh........",
    ".eEeEeEeEeEeEeEeEeEeEeE.",
    "eEeEeEeEeEeEeEeEeEeEeEeE",
]

# Salt Mines: a mine headframe / winding tower over a black shaft, cabling
# slack -- "everyone's shift but mine ends at the sound" (Foreman's Ledger).
SALT_HEADFRAME = [
    ".......rMMMMr.......",
    "......rMoooMr.......",
    ".....rMo...oMr......",
    "....rMo.....oMr.....",
    "...rMo..ooo..oMr....",
    "..rMo..oyyyo..oMr...",
    ".rMo..oy...yo..oMr..",
    "rMo..oy.....yo..oMr.",
    "rM..oy...M...yo..Mr.",
    "rM.wwwwwwMwwwwww.Mr.",
    "rM.wVVVVVMVVVVVw.Mr.",
    "rM..v...vMv...v..Mr.",
    "rM..v..dddddd.v..Mr.",
    "rM..v..dKKKKd.v..Mr.",
    "rM..v..dKKKKd.v..Mr.",
    "vv..v..dKKKKd.v..vv.",
    "SS.SS..dKKKKd.SS.SS.",
    "SSSSSSSSSSSSSSSSSSSS",
]

# Pit Below: a drowned carnival wheel, half-submerged and tilted, cars hanging
# -- ropes snapped outward from something that got loose in the ring.
CARNIVAL_WHEEL = [
    ".........PPPPP.........",
    "......PPPuuuuuPPP......",
    ".....PuP...P...PuP.....",
    "...PuP..P..P..P..PuP...",
    "..Pu..P...uPu...P..uP..",
    "..P..P...Pu.uP...P..P..",
    ".Pu.P...Pu...uP...P.uP.",
    ".P.uP..Pu..P..uP..Pu.P.",
    "Pu.P..Pu.PPuPP.uP..P.uP",
    "P..P.Pu.Pu.u.uP.uP.P..P",
    "Pu.P..Pu.PPuPP.uP..P.uP",
    ".P.uP..Pu..P..uP..Pu.P.",
    ".Pu.P...Pu...uP...P.uP.",
    "..P..P...Pu.uP...P..P..",
    "..Pu..P...uPu...P..uP..",
    "...PuP..P..P..P..PuP...",
    ".rBr.uP...P...Pu.rBr...",
    "rBBBr..PPPuPPP..rBBBr..",
    "dBBBd....ppp....dBBBd..",
    ".ddd....ppppp....ddd...",
    "eEeEeEeEeEeEeEeEeEeEeEe",
]

# Attic of Teeth: a condemned tenement leaning over the street, boarded
# windows, one attic light still lit -- clawed door is inside (world-bible).
LEANING_TENEMENT = [
    "....dddddddddd..",
    "...drrrrrrrrrrd.",
    "..drrrrrrrrrrrrd",
    "..drVVdrrdVVdrrd",
    "..drVVdrrdVVdrrd",
    "..drrrrrrrrrrrrd",
    "..drWWdrrdVVdrrd",
    "..drWWdrrdVVdrrd",
    "..drrrrrrrrrrrrd",
    "..drVVdrrdVVdrrd",
    "..drVVdrrdVVdrrd",
    "..drrrrrrrrrrrrd",
    "..drVVdrrdVVdrrd",
    "..drVVdrrdVVdrrd",
    "..drrrrrrrrrrrrd",
    "..ddKKddddKKdddd",
    "..ddKKddddKKdddd",
    "..dddddddddddddd",
]

# Conductor's Hall approach: a black obelisk-spire, faces blank, a single
# stopped-clock face melting on it -- the boss's monument.
CONDUCTOR_SPIRE = [
    ".......ww.......",
    "......wWWw......",
    "......wWWw......",
    ".....wWppWw.....",
    ".....wpPPpw.....",
    ".....wpPPpw.....",
    "....wpPuuPpw....",
    "....wpPuuPpw....",
    "....wpPuuPpw....",
    "...wpPuLLuPpw...",
    "...wpPuLoLuPpw..",
    "...wpPuLLLuPpw..",
    "...wpPuuLuuPpw..",
    "...wpPuuuuuPpw..",
    "..wpPPuuuuuPPpw.",
    "..wpPPPPPPPPPpw.",
    "..wpPPPPPPPPPpw.",
    "..vpPPPPPPPPPpv.",
    "..dpPPPPPPPPPpd.",
    ".ddvpPPPPPPPpvdd",
    "dddddddddddddddd",
]

LANDMARKS = {
    "shallows": DROWNED_SHIP,
    "saltmines": SALT_HEADFRAME,
    "pit": CARNIVAL_WHEEL,
    "attic": LEANING_TENEMENT,
    "hall": CONDUCTOR_SPIRE,
}
ORDER = ["shallows", "saltmines", "pit", "attic", "hall"]
FRAME_W, FRAME_H = 30, 40


def build_landmark(name: str) -> Image.Image:
    img = render(LANDMARKS[name])
    img = rim_light(img, strength=0.30)
    img = outline(img)
    img = drop_shadow(img, 1, 2, 90)
    frame = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    frame.alpha_composite(img, ((FRAME_W - img.width) // 2, FRAME_H - img.height - 1))
    return frame


def build_sheet() -> Image.Image:
    sheet = Image.new("RGBA", (FRAME_W * len(ORDER), FRAME_H), (0, 0, 0, 0))
    for i, name in enumerate(ORDER):
        sheet.alpha_composite(build_landmark(name), (i * FRAME_W, 0))
    return sheet


def contact() -> Image.Image:
    s = build_sheet()
    bg = Image.new("RGBA", s.size, (24, 28, 34, 255))
    bg.alpha_composite(s)
    return bg


if __name__ == "__main__":
    save(build_sheet(), "sprites/overworld/landmarks.png")
    print("landmarks written; order =", ORDER)
