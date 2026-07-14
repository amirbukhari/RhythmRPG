"""Hand-lettered wordmark for THE DROWNED CHORUS (AAA audit M1, PRD v7.12:
"AI image models render text unreliably, needs a lettered-by-hand approach").

Every glyph below is literally lettered by hand as a 7x9 bitmap -- heavy
2px stems with a drowned-gothic weight -- then composed with a per-letter
sway and drip pixels falling off the baseline (the title is sinking).
Deterministic; regenerate with:  python3 tools/pixelart/wordmark.py
Output: assets/ui/wordmark.png (two stacked lines, 2x chunky pixels).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "ui" / "wordmark.png"

G = {
    "T": ["#######", "#######", "..###..", "..###..", "..###..", "..###..", "..###..", "..###..", "..###.."],
    "H": ["##...##", "##...##", "##...##", "#######", "#######", "##...##", "##...##", "##...##", "##...##"],
    "E": ["######.", "######.", "##.....", "#####..", "#####..", "##.....", "##.....", "######.", "######."],
    "D": ["#####..", "######.", "##...##", "##...##", "##...##", "##...##", "##...##", "######.", "#####.."],
    "R": ["######.", "######.", "##...##", "##...##", "######.", "#####..", "##..##.", "##...##", "##...##"],
    "O": [".#####.", "#######", "##...##", "##...##", "##...##", "##...##", "##...##", "#######", ".#####."],
    "W": ["##...##", "##...##", "##...##", "##.#.##", "##.#.##", "##.#.##", "#######", "###.###", "##...##"],
    "N": ["##...##", "###..##", "###..##", "####.##", "##.####", "##..###", "##..###", "##...##", "##...##"],
    "C": [".#####.", "#######", "##....#", "##.....", "##.....", "##.....", "##....#", "#######", ".#####."],
    "U": ["##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "#######", ".#####."],
    "S": [".######", "#######", "##.....", "######.", ".######", ".....##", ".....##", "#######", "######."],
    " ": [".......", ".......", ".......", ".......", ".......", ".......", ".......", ".......", "......."],
}
GW, GH = 7, 9

BONE = (244, 239, 226, 255)
TEAL = (73, 198, 189, 255)
DEEP = (20, 56, 79, 255)
INK = (5, 6, 10, 255)

# hand-placed drips: (letter index in the composed line, column, length)
DRIPS_1 = [(0, 3, 3), (5, 1, 2), (7, 5, 4), (9, 2, 2)]  # THE DROWNED
DRIPS_2 = [(1, 4, 3), (3, 1, 2), (5, 5, 4)]  # CHORUS
SWAY_1 = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0]
SWAY_2 = [1, 0, 0, 1, 0, 1]


def draw_line(text: str, fill: tuple[int, int, int, int], sway: list[int], drips: list[tuple[int, int, int]]) -> Image.Image:
    n = len(text)
    w = n * GW + (n - 1)
    h = GH + 6  # room for drips
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for i, ch in enumerate(text):
        gx = i * (GW + 1)
        gy = sway[i % len(sway)]
        for r, rowbits in enumerate(G[ch]):
            for c, bit in enumerate(rowbits):
                if bit == "#":
                    px[gx + c, gy + r] = fill
        # deep-teal underlight on each letter's bottom row of set pixels
        for c in range(GW):
            for r in range(GH - 1, -1, -1):
                if G[ch][r][c] == "#":
                    px[gx + c, gy + r] = DEEP if r == GH - 1 or G[ch][min(GH - 1, r + 1)][c] == "." else px[gx + c, gy + r]
                    break
    for li, col, length in drips:
        if li >= n or text[li] == " ":
            continue
        gx = li * (GW + 1) + col
        base = sway[li % len(sway)] + GH
        for d in range(length):
            a = max(70, 255 - d * 60)
            px[gx, min(h - 1, base + d)] = (fill[0], fill[1], fill[2], a)
    return im


def outline(im: Image.Image) -> Image.Image:
    w, h = im.size
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    src = im.load()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] > 60:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        dst[x + 1 + dx, y + 1 + dy] = INK
    out.alpha_composite(im, (1, 1))
    return out


def main() -> None:
    line1 = outline(draw_line("THE DROWNED", BONE, SWAY_1, DRIPS_1))
    line2 = outline(draw_line("CHORUS", TEAL, SWAY_2, DRIPS_2))
    w = max(line1.width, line2.width)
    gap = 2
    sheet = Image.new("RGBA", (w, line1.height + gap + line2.height), (0, 0, 0, 0))
    sheet.alpha_composite(line1, ((w - line1.width) // 2, 0))
    sheet.alpha_composite(line2, ((w - line2.width) // 2, line1.height + gap))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    main()
