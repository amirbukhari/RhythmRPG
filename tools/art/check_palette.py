"""Audit the SHIPPED BYTES for hues this world does not have.

    python3 tools/art/check_palette.py [--all] [--top N]

exit 0 = clean, 1 = a forbidden hue is shipping.

WHY THIS EXISTS, AND WHY GREPPING WAS NOT ENOUGH
The previous art direction's plum family (`8a52a0` / `4b2a57` / `b98fca`) shipped
into *The Drowned Chorus* three separate times, months apart, and each one was
caught by a human looking at a frame:

  1. the nine-slice panel frame -- drawn round the player's HP in EVERY fight;
  2. the groove meter's fill;
  3. `tools/pixelart/tiles.py`'s own region-accent table, which tinted 20 of the
     20 region ground tiles, and `tools/art/palette.py`'s `KEEP = storm violet`,
     which tinted a whole region's terrain -- `ground_plate_0_5.png` measured
     86.6% purple pixels.

After (1) and (2) the style contract said to "grep the game's own hex literals".
That is necessary and it is NOT sufficient: it only sees code. (3) shipped
through a palette-KEY lookup and a named constant, so no literal spelled the
colour anywhere near the art it produced.

The audit that works does not care which tool wrote a pixel. It walks the PNGs
and counts. THE PALETTE A GAME HAS IS THE ONE IN ITS PIXELS.

THE BAND, AND WHY IT IS NOT "ANY PURPLE PIXEL"
Hue alone flags things that are not purple in any useful sense: a near-black at
`(12, 10, 16)` is hue 260 and is simply cool black. So a pixel counts only if it
is purple ENOUGH TO SEE -- inside the hue band, and above a saturation and a
lightness floor. And a FILE is only reported over a small area fraction, because
a handful of antialiasing pixels on a boundary between a warm and a cool region
will always land in the band and mean nothing.
"""

from __future__ import annotations

import colorsys
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

# violet .. magenta. Deliberately open on the blue side at 258 rather than 270:
# `7a4eb4` (hue 266) and `b18cf0` (hue 262) both shipped, and both are plainly
# purple to the eye. Below ~255 the band would start eating the game's real
# slate-blues (`2b2f3e` is hue 227), which are canon.
HUE_LO, HUE_HI = 258.0, 342.0
SAT_MIN = 0.14  # below this it is a grey with a bias, not a hue
LUM_MIN = 0.10  # below this it is black, whatever its hue says
AREA_MAX = 0.004  # 0.4% of opaque pixels -- above this it is not antialiasing

# Known and accepted. Each needs a reason, not just a path.
ALLOW = {
    # world-bible/style-contract §"foe colour family": the wraith is the one
    # supernatural foe and its family is specified as oxidised copper AND
    # violet -- an off-world hue on an off-world thing is information. This is
    # the only place in the game where purple is a CHOICE.
    "assets/sprites/enemies/elite_wraith",
    # not shipped: a snapshot of the pre-authored cast, kept for comparison
    "assets/reference/",
}


def offending(path: Path, step: int):
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    bad = tot = 0
    worst = (0.0, None)
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            tot += 1
            hue, lum, sat = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            deg = hue * 360.0
            if HUE_LO <= deg <= HUE_HI and sat >= SAT_MIN and lum >= LUM_MIN:
                bad += 1
                if sat > worst[0]:
                    worst = (sat, (r, g, b, round(deg)))
    return bad, tot, worst[1]


def main(argv):
    show_all = "--all" in argv
    top = 25
    if "--top" in argv:
        top = int(argv[argv.index("--top") + 1])

    hits = []
    scanned = 0
    for p in sorted((ROOT / "assets").rglob("*.png")):
        rel = str(p.relative_to(ROOT))
        if not show_all and any(rel.startswith(a) for a in ALLOW):
            continue
        # big plates are subsampled -- a 512x512 region of purple is not going
        # to hide between two sampled pixels
        w, h = Image.open(p).size
        bad, tot, worst = offending(p, 1 if w * h < 200_000 else 2)
        scanned += 1
        if tot and bad / float(tot) > AREA_MAX:
            hits.append((bad / float(tot), rel, bad, tot, worst))

    hits.sort(reverse=True)
    print("scanned %d png(s) under assets/ (%d path(s) allow-listed)"
          % (scanned, len(ALLOW)))
    if not hits:
        print("PASS -- no forbidden hue is shipping")
        return 0
    print("FAIL -- %d file(s) ship hue %g-%g (sat>=%.2f, lum>=%.2f) over %.1f%% of area:"
          % (len(hits), HUE_LO, HUE_HI, SAT_MIN, LUM_MIN, 100 * AREA_MAX))
    for frac, rel, bad, tot, worst in hits[:top]:
        print("  %6.2f%%  %-58s %7d/%-8d worst rgb%s" % (100 * frac, rel, bad, tot, worst))
    if len(hits) > top:
        print("  ... and %d more" % (len(hits) - top))
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
