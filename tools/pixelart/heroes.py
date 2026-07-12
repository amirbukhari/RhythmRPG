"""The doomed party -- four distinct gothic characters drawn from the
Skatopia lyrics: a party that walks the ocean-floor road toward The
Conductor. Each is a hand-authored pixel grid (down/side/up facings), given
a 4-frame walk cycle procedurally (leg swing + body bob), outlined, and
packed into per-class spritesheets used by BOTH the overworld and battle.

Classes map to roles, each with its own silhouette, palette and prop:
  warrior -> Deereater: antlered blood-rust reaver with a cleaver
  tank    -> Saltminer: hunched iron miner behind a slab-shield
  mage    -> Esoterophobe: tall plum-robed figure, melting-clock lantern
  healer  -> Sunshine Sally: pale bone-robed keeper with a censer
"""

from __future__ import annotations

from PIL import Image
from skatopia import render, outline, pad_to, save

FRAME_W, FRAME_H = 20, 24  # generous frame; sprites sit bottom-centre

# --- down-facing standing grids (16 wide). "." = transparent. --------------

WARRIOR_DOWN = [
    "...o......o...",
    "...o.rrrr.o...",
    "...oorRRRroo..",
    "....rRRRRr....",
    "....RFFFFR....",
    "....FKFFKF....",
    "....FFffFF....",
    "....bFFFFb....",
    "...bBBRRBBb...",
    "..MBBBBBBBBM..",
    "..MBbBBBBbBM..",
    "..MBBBBBBBBM..",
    "...BBBBBBBB...",
    "...rBBBBBBr...",
    "...bBBBBBBb...",
    "....NNNNNN....",
    "....NN..NN....",
    "....NN..NN....",
    "....dd..dd....",
    "...kdd..ddk...",
]

TANK_DOWN = [
    ".............",
    "....mMMMm....",
    "...mMMMMMm...",
    "...MMLLMMM...",
    "...MFFFFM....",
    "...FfKKfF....",
    "...FFffFF....",
    "..NmMMMMmN...",
    ".NMMMMMMMMN..",
    ".NMLLLLLLMN..",  # slab shield front
    ".NMLwwwwLMN..",
    ".NMLwvvwLMN..",
    ".NMLwwwwLMN..",
    ".NMLLLLLLMN..",
    ".NmMMMMMMmN..",
    "..NNNNNNNN...",
    "...NN..NN....",
    "...mN..Nm....",
    "...dd..dd....",
    "..kdd..ddk...",
]

MAGE_DOWN = [
    ".....pp......",
    "....pPPp.....",
    "...pPPPPp....",
    "...pPuuPp....",
    "....PFFP.....",
    "....FKKF.....",
    "....FffF.....",
    "...pPPPPp....",
    "..pPPPPPPp..o",
    "..pPPuuPPp.oM",  # right hand holds a lantern pole
    "..pPPPPPPp.oy",  # lantern glow
    "..pPuPPuPp.oy",
    "..pPPPPPPp.oo",
    "...pPPPPp....",
    "...pPPPPp....",
    "...pPPPPp....",
    "...pPPPPp....",
    "...ppPPpp....",
    "....p..p.....",
    "...kd..dk....",
]

HEALER_DOWN = [
    "....wwww.....",
    "...wWWWWw....",
    "..wWWWWWWw...",
    "..wWvvvvWw...",
    "...WFFFFW....",
    "...FKffKF....",
    "...FFffFF....",
    "..CwWWWWwC...",  # teal stole
    ".wWWWWWWWWw..",
    ".wWWCCCCWWw..",
    ".wWWWWWWWWw.C",  # left hand swings a censer
    ".wWvWWWWvWw.c",
    ".wWWWWWWWWw.C",
    "..wWWWWWWw...",
    "..wWWWWWWw...",
    "..wWWWWWWw...",
    "..wWWvvWWw...",
    "..wwW..Www...",
    "...w....w....",
    "..kd....dk...",
]

# --- side-facing (walking right) standing grids ----------------------------

WARRIOR_SIDE = [
    "....oo....",
    "...rRRr...",
    "..rRRRRo..",
    "..RFFFr...",
    "..FKfF....",
    "..FFff....",
    ".bBBRb....",
    "MBBBBBb...",
    "MBBBBBBr..",  # cleaver arm forward
    "MBBBBBBR..",
    ".BBBBBb...",
    ".rBBBb....",
    ".bBBBb....",
    ".NNNN.....",
    ".NN.N.....",
    ".NN.NN....",
    ".dd.dd....",
    "kdd.ddk...",
]

TANK_SIDE = [
    "..........",
    "..mMMMm...",
    ".mMMMMMm..",
    ".MMLLMM...",
    ".MFFfM....",
    ".FfKfF....",
    "NmMMMmN...",
    "LLLLLLMN..",  # shield leads
    "wwwwLLMN..",
    "wvvwLLMN..",
    "wwwwLLMN..",
    "LLLLLmN...",
    "mMMMMmN...",
    ".NNNNN....",
    ".NN.N.....",
    ".mN.Nm....",
    ".dd.dd....",
    "kdd.ddk...",
]

MAGE_SIDE = [
    "..pp......",
    ".pPPp.....",
    ".pPuPp....",
    "..PFP.....",
    "..FKf.....",
    "..Fff.....",
    ".pPPPp..o.",
    "pPPPPp.oy.",  # lantern out front
    "pPPuPp.oy.",
    "pPPPPp.oo.",
    ".pPPPp....",
    ".pPPPp....",
    ".pPPPp....",
    ".pPPPp....",
    ".pPPp.....",
    ".ppPp.....",
    "..p.p.....",
    ".kd.dk....",
]

HEALER_SIDE = [
    "..wwww....",
    ".wWWWWw...",
    ".wWvvWw...",
    "..WFFW....",
    "..FKfF....",
    "..FffF....",
    ".CwWWwC...",
    "cWWWWWWC..",  # censer swings ahead
    "CWWCCWWc..",
    ".WWWWWW...",
    ".wWWWWw...",
    ".wWWWWw...",
    ".wWWWWw...",
    ".wWWWWw...",
    ".wWWWw....",
    ".wwWw.....",
    "..w.w.....",
    ".kd.dk....",
]

# up-facing: reuse the down silhouette but hide the face (back of head/hood).
def _back(grid: list[str]) -> list[str]:
    out = []
    for i, row in enumerate(grid):
        # rows 3-6 are the face band in the down grids; overpaint skin with hair/hood
        if 3 <= i <= 6:
            row = (row.replace("F", "#").replace("K", "#").replace("f", "#")
                      .replace("u", "#").replace("C", "#"))
        out.append(row)
    return out

BACK_FILL = {"warrior": "R", "tank": "M", "mage": "P", "healer": "W"}


def _grid_up(grid: list[str], role: str) -> list[str]:
    fill = BACK_FILL[role]
    return [r.replace("#", fill) for r in _back(grid)]


def _walk(base: Image.Image, facing: str) -> list[Image.Image]:
    """4-frame cycle: contact-L, passing (bob up), contact-R, passing (bob up).
    Legs are the last 5 rows; nudge them left/right and bob the torso 1px."""
    w, h = base.size
    px = base.load()
    leg_top = h - 5

    def shifted(dx_left: int, dx_right: int, bob: int) -> Image.Image:
        f = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        fp = f.load()
        for y in range(h):
            for x in range(w):
                c = px[x, y]
                if c[3] == 0:
                    continue
                if y >= leg_top:
                    dx = dx_left if x < w // 2 else dx_right
                    nx, ny = x + dx, y
                else:
                    nx, ny = x, y - bob  # torso bobs up on passing frames
                if 0 <= nx < w and 0 <= ny < h:
                    fp[nx, ny] = c
        return f

    if facing == "side":
        return [shifted(1, -1, 0), shifted(0, 0, 1), shifted(-1, 1, 0), shifted(0, 0, 1)]
    return [shifted(-1, 1, 0), shifted(0, 0, 1), shifted(1, -1, 0), shifted(0, 0, 1)]


HEROES = {
    "warrior": (WARRIOR_DOWN, WARRIOR_SIDE),
    "tank": (TANK_DOWN, TANK_SIDE),
    "mage": (MAGE_DOWN, MAGE_SIDE),
    "healer": (HEALER_DOWN, HEALER_SIDE),
}


def build_hero(role: str) -> dict[str, Image.Image]:
    down_g, side_g = HEROES[role]
    facings = {
        "down": render(down_g),
        "side": render(side_g),
        "up": render(_grid_up(down_g, role)),
    }
    sheets = {}
    for facing, base in facings.items():
        base = outline(base)
        base = pad_to(base, FRAME_W, FRAME_H)
        frames = _walk(base, "side" if facing == "side" else "down")
        sheet = Image.new("RGBA", (FRAME_W * 4, FRAME_H), (0, 0, 0, 0))
        for i, fr in enumerate(frames):
            sheet.alpha_composite(fr, (i * FRAME_W, 0))
        sheets[facing] = sheet
    return sheets


def build_all() -> None:
    for role in HEROES:
        sheets = build_hero(role)
        for facing, sheet in sheets.items():
            save(sheet, f"sprites/heroes/{role}/{facing}.png")
    print("heroes written")


def contact_sheet() -> Image.Image:
    """One standing (frame 0, down) of each hero side by side, for review."""
    imgs = []
    for role in HEROES:
        s = build_hero(role)["down"]
        imgs.append(s.crop((0, 0, FRAME_W, FRAME_H)))
    out = Image.new("RGBA", (FRAME_W * len(imgs), FRAME_H), (0, 0, 0, 0))
    for i, im in enumerate(imgs):
        out.alpha_composite(im, (i * FRAME_W, 0))
    return out


if __name__ == "__main__":
    build_all()


# --- battle attack frames (side-facing): windup + swing ---------------------
# Authored action poses for the playable lead in the real-time arena (PRD
# §11.1 "anticipation -> impact"): frame 0 coils with the cleaver drawn back
# high; frame 1 swings it fully forward with a motion arc.

WARRIOR_ATTACK_WINDUP = [
    "....oo........",
    "...rRRr..b....",
    "..rRRRRo.Bb...",
    "..RFFFr..Bb...",
    "..FKfF..bB....",
    "..FFff.bB.....",
    ".bBBRbBB......",
    "MBBBBBb.......",
    "MBBBBBB.......",
    "MBBBBBB.......",
    ".BBBBBb.......",
    ".rBBBb........",
    ".bBBBb........",
    ".NNNN.........",
    ".NN.N.........",
    ".NN.NN........",
    ".dd.dd........",
    "kdd.ddk.......",
]

WARRIOR_ATTACK_SWING = [
    "....oo........",
    "...rRRr.......",
    "..rRRRRo......",
    "..RFFFr.......",
    "..FKfF....w...",
    "..FFff...ww...",
    ".bBBRb..wW....",
    "MBBBBBbwWBb...",
    "MBBBBBBWBBb...",
    "MBBBBBBbBb....",
    ".BBBBBb.b.....",
    ".rBBBb........",
    ".bBBBb........",
    ".NNNN.........",
    ".NN.NN........",
    ".NN..N........",
    ".dd..dd.......",
    "kdd..ddk......",
]


def build_warrior_attack() -> "Image.Image":
    from PIL import Image as _I
    fw, fh = 24, 24
    frames = []
    for grid in (WARRIOR_ATTACK_WINDUP, WARRIOR_ATTACK_SWING):
        img = outline(render(grid))
        frames.append(img)
    sheet = _I.new("RGBA", (fw * 2, fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * fw, fh - f.height))
    return sheet
