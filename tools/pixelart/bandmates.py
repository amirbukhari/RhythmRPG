"""The band -- Inhalants -- the playable party (PRD §11.4 carry-forward).

The provided guitarist ("Amir") spritesheets in
assets/sprites/heroes/placeholder/ are the visual basis for the lead
character, per assets/reference/README.md. They ship as large, heavily
padded frames (64px stand / 128px movement) with the character occupying
~32-37px. This module conforms them to spec -- slice, autocrop, and
re-anchor every frame bottom-centre into one uniform 48x48 frame so the
engine can load clean idle/run/attack strips -- and authors the three
remaining band members (a bassist, a vocalist, a drummer) in the same
proportion/palette so the four read as one band.

Amir is the real, hand-drawn art; the other three are authored here in the
Skatopia pipeline to match him -- same silhouette height, same dark-punk
palette, each with a distinct instrument and an idle/run/attack move set.

Output (via generate_all.py):
    assets/sprites/band/{member}/{idle,run,attack}.png   -- 48x48 frames
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from skatopia import PALETTE, render, outline, rim_light, drop_shadow, save

FRAME = 48  # uniform band-sprite frame (bottom-centre anchor)
PLACEHOLDER = Path(__file__).resolve().parents[2] / "assets" / "sprites" / "heroes" / "placeholder"


# --- Amir: conform the provided sheets -------------------------------------

def _slice(sheet_name: str, frame_w: int) -> list[Image.Image]:
    """Cut a provided Amir sheet into its frames (all provided sheets are one
    row, frame_w wide, full-height)."""
    im = Image.open(PLACEHOLDER / sheet_name).convert("RGBA")
    n = im.width // frame_w
    return [im.crop((i * frame_w, 0, (i + 1) * frame_w, im.height)) for i in range(n)]


def _reanchor(frame: Image.Image) -> Image.Image:
    """Autocrop a padded source frame to the character and re-place it
    bottom-centre in a uniform FRAME x FRAME canvas, so a strip of frames
    animates in place with no jitter."""
    bbox = frame.getbbox()
    out = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    if bbox is None:
        return out
    char = frame.crop(bbox)
    # scale down if a source frame is taller than the target (keeps aspect)
    if char.height > FRAME - 2:
        s = (FRAME - 2) / char.height
        char = char.resize((max(1, round(char.width * s)), FRAME - 2), Image.NEAREST)
    ox = (FRAME - char.width) // 2
    oy = FRAME - char.height - 1
    out.alpha_composite(char, (ox, oy))
    return out


def _strip(frames: list[Image.Image]) -> Image.Image:
    sheet = Image.new("RGBA", (FRAME * len(frames), FRAME), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * FRAME, 0))
    return sheet


def amir_idle() -> Image.Image:
    # 21 stand frames -> a smooth 6-frame loop (evenly sampled).
    src = _slice("Amir Stand.png", 64)
    pick = [round(i * (len(src) - 1) / 5) for i in range(6)]
    return _strip([_reanchor(src[i]) for i in pick])


def amir_run() -> Image.Image:
    # 8 run frames, used as-is (already a clean cycle).
    return _strip([_reanchor(f) for f in _slice("Amir Run.png", 128)])


def amir_attack() -> Image.Image:
    # A 3-frame guitar swing pulled from the dash sheet's most dynamic poses
    # (windup -> swing -> follow-through).
    src = _slice("Amir DashToWait.png", 128)
    pick = [2, 6, 10]
    return _strip([_reanchor(src[i]) for i in pick])


# --- Authored bandmates (match Amir's proportions + palette) ----------------
# Amir's own palette, sampled from the provided art, so the four read as one
# band: dark-brown skin, grey spiked hair, black clothing, a white tank, plus
# one instrument accent per member. Figures are side-facing like Amir, built
# as a per-member TORSO (head/hair/body/arms/instrument) stacked over a set of
# SHARED leg poses, so every member runs on the same hand-drawn cycle and the
# band moves cohesively -- only the instrument silhouette differs.
BAND_PAL = {
    "K": (0x00, 0x00, 0x00, 255),   # black clothing (darkest)
    "k": (0x0d, 0x0d, 0x0d, 255),   # black clothing
    "d": (0x28, 0x28, 0x28, 255),   # clothing fold highlight
    "m": (0x1d, 0x1d, 0x1d, 255),   # hair shadow
    "M": (0x33, 0x33, 0x33, 255),   # hair mid
    "L": (0xb5, 0xb4, 0xb4, 255),   # hair / metal highlight
    "s": (0x41, 0x21, 0x01, 255),   # skin shadow
    "S": (0x73, 0x3a, 0x00, 255),   # skin mid
    "F": (0xe2, 0xa8, 0x6d, 255),   # skin highlight
    "W": (0xf4, 0xef, 0xe2, 255),   # white tank
    "w": (0xd8, 0xce, 0xb6, 255),   # tank shadow
    "o": (0xf0, 0xa6, 0x48, 255),   # warm instrument accent (wood/amber)
    "r": (0xa8, 0x43, 0x1c, 255),   # rust accent
    "b": (0x49, 0xc6, 0xbd, 255),   # cold accent (mic/cymbal glint)
    "R": (0xc2, 0x2f, 0x34, 255),   # red accent (mohawk dye / drum shell)
}

W = 22  # shared grid width for torsos and legs

# Shared side-facing (facing right) leg poses, 12 rows each. Feet on the last
# row. Same for every member so the band shares one gait.
_LEGS_STAND = [
    ".......kkkk...........",
    ".......kkkk...........",
    "......kkkkkk..........",
    ".....dkk..kkd.........",
    ".....kk....kk.........",
    ".....kk....kk.........",
    ".....kk....kk.........",
    ".....kk....kk.........",
    ".....kk....kk.........",
    "....dkk....kkd........",
    "...MMMk....kMMM.......",
    "...LMMM....MMML.......",
]
_LEGS_RUN_A = [  # forward reach
    ".......kkkk...........",
    ".......kkkk...........",
    "......kkkkkk..........",
    ".....dkkkkkkd.........",
    "....kkk...kkkk........",
    "...kk.......kkk.......",
    "..kk.........kkk......",
    ".kk...........kk......",
    "dk.............kk.....",
    "MMk.......dk...kk.....",
    "LMM.......MMk..dk.....",
    "..........MMM..MMM....",
]
_LEGS_RUN_B = [  # passing / gather
    ".......kkkk...........",
    ".......kkkk...........",
    "......kkkkkk..........",
    ".....dkkkkkkd.........",
    "......kkkkkk.........",
    ".....kkk.kkk.........",
    ".....kk...kkk........",
    "....dk.....kkk.......",
    "...MMk......dkk......",
    "...LMM......MMk......",
    "............MMM......",
    ".....................",
]
_LEGS_RUN_C = [  # rear extend
    ".......kkkk...........",
    ".......kkkk...........",
    "......kkkkkk..........",
    "....dkkkkkkkkd.......",
    "...kkkk...kkkk.......",
    "..kkk.......kk.......",
    ".kk..........kk......",
    "dk............dkk....",
    "MMk............kkk...",
    "LMM.........dk..MMk..",
    "............MMk..LMM..",
    "............MMM.......",
]


def _stack(torso: list[str], legs: list[str]) -> list[str]:
    """Left-align torso over legs into one grid (pad to width W)."""
    return [r.ljust(W, ".")[:W] for r in (torso + legs)]


def _finish(rows: list[str]) -> Image.Image:
    img = render(rows, BAND_PAL)
    img = rim_light(img, strength=0.30)
    img = outline(img)
    img = drop_shadow(img, 1, 2, 85)
    return _reanchor(img)


# ---- Per-member torsos (24 rows) ------------------------------------------
# Bassist: tall red-dyed mohawk, sleeveless, a heavy bass held low across the
# body with a long neck raked up to the right (the widest silhouette).
_BASS_TORSO = [
    "........RR............",
    ".......RRR............",
    "......mRRRm...........",
    "......mMRMm...........",
    ".....FFsFsF...........",
    ".....FSssSF..........L",
    ".....FSFFSF.........LL",
    "......sSSs.........Lo.",
    ".....WWWWWW.......Loo.",
    "....SWWWWWWS.....Loo..",
    "...SSWWWWWWSS...Loo...",
    "..SS.WWWWWW.SSoooo....",
    ".SS..kkkkkk..oooo.....",
    "SS...kdddkk.rroor.....",
    ".....kkddkk.rroor.....",
    ".....kkkkkk..rrr......",
    ".....kkkkkk...........",
]
# Vocalist: high spiked hair, throwing back, a mic on a cord in the near hand
# raised toward the mouth (leanest silhouette, arm up).
_VOX_TORSO = [
    "....m..mm.m...........",
    "...mMmMMmMm...........",
    "....mMMMMm......b.....",
    "....FFsFsF.....Lb.....",
    "....FSssSF....Lb......",
    "....FSFFSF...Lb.......",
    ".....sSSs...Fb........",
    "....WWWWWW..sF........",
    "...WWkkkkWW.s.........",
    "..SWWkkkkWWS..........",
    ".SS.WkkkkW.SS.........",
    "SS..WkkkkW..SS........",
    ".S..kkkkkk...S........",
    "....kdddkk............",
    "....kkddkk............",
    "....kkkkkk............",
    "....kkkkkk............",
]
# Drummer: shaggy hair under a bandana, both arms up holding sticks crossed
# overhead (the "sticks up" silhouette), broad shoulders.
_DRUM_TORSO = [
    ".L........L..........",
    "..Lo....oL...........",
    "...Lo..oL............",
    "..mMLooLMm...........",
    "..mMMMMMMm...........",
    "...FFsFsF............",
    "...FSssSF............",
    "...FSFFSF............",
    "....sSSs.............",
    "..WWWWWWWW...........",
    ".WWWkkkkWWW..........",
    "SWWWkkkkWWWS.........",
    "SS.WkkkkW.SS.........",
    ".S.kkkkkkk.S.........",
    "...kdddkkk...........",
    "...kkddkkk...........",
    "...kkkkkkk...........",
    "...kkkkkkk...........",
]

# ---- Per-member attack torsos (instrument swung -- "different move sets") ---
_BASS_ATTACK = [  # bass swung down like a club
    "........RR............",
    ".......RRR............",
    "......mRRRm...........",
    "......mMRMm...........",
    ".....FFsFsF...........",
    ".....FSssSF...........",
    ".....FSFFSF...........",
    "......sSSs............",
    ".....WWWWWW...........",
    "....SWWWWWWS..........",
    "...SSWWWWWWSS.........",
    "..SS.WWWWWW.SS........",
    ".SS..kkkkkk..S........",
    "SS...kdddkk..ooo......",
    ".....kkddkk.ooooo.....",
    ".....kkkkkk.orrro.....",
    ".....kkkkkk..ooo......",
]
_VOX_ATTACK = [  # mic thrust forward, scream
    "....m..mm.m...........",
    "...mMmMMmMm...........",
    "....mMMMMm...........",
    "....FFsFsF...........",
    "....FSssSF...........",
    "....FSFFSF...........",
    ".....sSSs............",
    "....WWWWWW...........",
    "...WWkkkkWW..........",
    "..SWWkkkkWWSSSb......",
    ".SS.WkkkkW..FFFLb....",
    "SS..WkkkkW...sF.b....",
    ".S..kkkkkk...........",
    "....kdddkk...........",
    "....kkddkk...........",
    "....kkkkkk...........",
    "....kkkkkk...........",
]
_DRUM_ATTACK = [  # both sticks crashing down
    "..mMMMMMMm...........",
    "..mMMMMMMm...........",
    "...FFsFsF............",
    "...FSssSF...........L",
    "...FSFFSF..........Lo",
    "....sSSs.........Loo.",
    "..WWWWWWWW......Loo..",
    ".WWWkkkkWWW...ooo....",
    "SWWWkkkkWWWSooo......",
    "SS.WkkkkW.Soo........",
    ".S.kkkkkkk.S.........",
    "...kdddkkk...........",
    "...kkddkkk...........",
    "...kkkkkkk...........",
    "...kkkkkkk...........",
    ".....................",
    ".....................",
]

MEMBERS = {
    "bassist": (_BASS_TORSO, _BASS_ATTACK),
    "vocalist": (_VOX_TORSO, _VOX_ATTACK),
    "drummer": (_DRUM_TORSO, _DRUM_ATTACK),
}


def _member_idle(torso: list[str]) -> Image.Image:
    """2-frame breathing idle: standing, then a 1px settle."""
    base = _finish(_stack(torso, _LEGS_STAND))
    settled = _finish(_stack(torso[1:] + [torso[-1]], _LEGS_STAND))  # torso drops 1px
    return _strip([base, settled])


def _member_run(torso: list[str]) -> Image.Image:
    return _strip([
        _finish(_stack(torso, _LEGS_RUN_A)),
        _finish(_stack(torso, _LEGS_RUN_B)),
        _finish(_stack(torso, _LEGS_STAND)),
        _finish(_stack(torso, _LEGS_RUN_C)),
    ])


def _member_attack(torso: list[str], attack_torso: list[str]) -> Image.Image:
    """3-frame swing: settle -> windup(idle torso, wide stance) -> strike."""
    return _strip([
        _finish(_stack(torso, _LEGS_STAND)),
        _finish(_stack(attack_torso, _LEGS_RUN_A)),
        _finish(_stack(attack_torso, _LEGS_STAND)),
    ])


def build_all() -> None:
    # Amir -- from the provided art.
    save(amir_idle(), "sprites/band/amir/idle.png")
    save(amir_run(), "sprites/band/amir/run.png")
    save(amir_attack(), "sprites/band/amir/attack.png")
    # Authored bandmates, matched to Amir.
    for name, (torso, attack_torso) in MEMBERS.items():
        save(_member_idle(torso), f"sprites/band/{name}/idle.png")
        save(_member_run(torso), f"sprites/band/{name}/run.png")
        save(_member_attack(torso, attack_torso), f"sprites/band/{name}/attack.png")
    print("band written:", ["amir", *MEMBERS.keys()])


if __name__ == "__main__":
    build_all()
