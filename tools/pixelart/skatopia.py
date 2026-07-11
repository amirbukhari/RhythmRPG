"""Skatopia pixel-art pipeline.

Sprites are authored as palette-indexed pixel grids: a list of equal-length
strings where each character is a key into a colour palette (space / "." are
transparent). This is deliberately the "just pixels / an RGB-JSON thing" the
brief asked for -- every sprite in this game is hand-placed here, in code,
and rendered deterministically to PNG. No external art, no image generation.

Art direction is derived from the Skatopia setlist lyrics (see
docs/design/art-bible.md): dark, surreal, gothic body-horror rendered as
*beautiful* moody pixel art -- ocean-floor abyss, rust and ember, melting
black clocks, bone/pearl, blood, rot green. A single curated master palette
(PALETTE) keeps every asset in the same world.
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS = REPO_ROOT / "assets"

Rgba = tuple[int, int, int, int]

# --- The Skatopia master palette ------------------------------------------
# One curated palette for the whole game so nothing clashes. Each hue carries
# 3-4 value steps so sprites can be shaded, not flat. Keys are single chars
# used in the grids below; " " and "." are always transparent.
_HEX: dict[str, str] = {
    # ink / void  (night, ghosts, outlines)
    "K": "05060a", "k": "0f111a", "d": "1c1f2b", "D": "2b2f3e",
    # bone / pearl (teeth, obelisk, salt, "teeth like pearls")
    "W": "f4efe2", "w": "d8ceb6", "v": "a89d84", "V": "6f6754",
    # rust / ember / gold ("rust of ambition", black plumes of fire, saltmines)
    "R": "e07030", "r": "a8431c", "o": "f0a648", "y": "f4d27a", "Y": "6e3316",
    # blood ("staircase red", "the bath turns red")
    "B": "c22f34", "b": "7d1b20", "X": "4a1013",
    # ocean ("live in the ocean", abyss, obelisk beneath)
    "C": "49c6bd", "c": "1f6f77", "e": "153a52", "E": "0b2233", "a": "2f5f86",
    # rot / moss / sick ("rot spots", "calcify", anthrax)
    "G": "79b855", "g": "426e33", "s": "9aa843", "S": "566a20",
    # plum / amethyst ("sapphire purses", twilight, esoteric)
    "P": "8a52a0", "p": "4b2a57", "u": "b98fca",
    # flesh (the doomed party -- pallid, corpse-touched, varied)
    "F": "dcae86", "f": "ad7552", "H": "c4bbb0", "h": "877d70",
    # metal (nooses, meat hooks, steel, clocks)
    "M": "97a2ae", "m": "586470", "L": "ccd4dc", "N": "3a434f",
}
# fix truncated hexes defensively (any short value -> pad)
def _rgba(hexs: str) -> Rgba:
    hexs = (hexs + "000000")[:6]
    return (int(hexs[0:2], 16), int(hexs[2:4], 16), int(hexs[4:6], 16), 255)

PALETTE: dict[str, Rgba] = {k: _rgba(v) for k, v in _HEX.items()}
TRANSPARENT: Rgba = (0, 0, 0, 0)


def render(rows: list[str], palette: dict[str, Rgba] | None = None) -> Image.Image:
    """A grid of palette-key strings -> an RGBA image (1px per char)."""
    pal = {**PALETTE, **(palette or {})}
    h = len(rows)
    w = max((len(r) for r in rows), default=0)
    img = Image.new("RGBA", (w, h), TRANSPARENT)
    px = img.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in (" ", ".", ""):
                continue
            col = pal.get(ch)
            if col is None:
                raise KeyError(f"palette key {ch!r} at ({x},{y}) is not defined")
            px[x, y] = col
    return img


def outline(img: Image.Image, color: Rgba = PALETTE["K"], diagonal: bool = True) -> Image.Image:
    """Add a 1px outline around every opaque cluster -- the single biggest
    'reads as real pixel art' win. Grows the canvas by 1px on every side."""
    w, h = img.size
    src = img.load()
    out = Image.new("RGBA", (w + 2, h + 2), TRANSPARENT)
    dst = out.load()
    neigh = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        neigh += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    # copy original shifted by (1,1)
    for y in range(h):
        for x in range(w):
            if src[x, y][3] > 0:
                dst[x + 1, y + 1] = src[x, y]
    # paint outline where a transparent pixel touches an opaque one
    for y in range(h + 2):
        for x in range(w + 2):
            if dst[x, y][3] > 0:
                continue
            for dx, dy in neigh:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w + 2 and 0 <= ny < h + 2 and dst[nx, ny][3] == 255 and dst[nx, ny] != color:
                    dst[x, y] = color
                    break
    return out


def pad_to(img: Image.Image, w: int, h: int, ax: float = 0.5, ay: float = 1.0) -> Image.Image:
    """Center a sprite in a fixed frame (ax/ay = 0..1 anchor; default bottom-center)."""
    out = Image.new("RGBA", (w, h), TRANSPARENT)
    ox = round((w - img.width) * ax)
    oy = round((h - img.height) * ay)
    out.alpha_composite(img, (ox, oy))
    return out


def hsheet(frames: list[Image.Image]) -> Image.Image:
    """Pack equal-size frames left-to-right into one spritesheet row."""
    fw = max(f.width for f in frames)
    fh = max(f.height for f in frames)
    sheet = Image.new("RGBA", (fw * len(frames), fh), TRANSPARENT)
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * fw + (fw - f.width) // 2, fh - f.height))
    return sheet


def save(img: Image.Image, rel_path: str) -> Path:
    p = ASSETS / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p)
    return p
