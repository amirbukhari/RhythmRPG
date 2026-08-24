"""Build the whole authored cast into `assets/sprites/`.

    python3 tools/art/build_cast.py [mir] [nari] [slime] [drifter] [elite_wraith]

with no arguments it builds everything. Output layout, which is also the
engine's texture-key contract (BootScene):

    assets/sprites/band/mir/<state>.png        -> band_mir      (state "idle")
                                                  band_mir_<state>
    assets/sprites/band/nari/<state>.png       -> band_nari / band_nari_<state>
    assets/sprites/enemies/<foe>/<state>.png   -> enemy_<foe> / enemy_<foe>_<state>

Every strip is a horizontal run of equal cells at the frame size fixed in
`contract.SCALE`, so a re-author can never desync the engine's frame ranges
(BootScene reads frame counts off the loaded texture).

Determinism: the renderer has no randomness -- the painterly grain is a hash of
pixel coordinates -- so the same source produces byte-identical PNGs and a
rebuild is a no-op in git unless the art actually changed.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image  # noqa: E402

import contract  # noqa: E402
import foes  # noqa: E402
import mir as mir_mod  # noqa: E402
import nari as nari_mod  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SPRITES = ROOT / "assets" / "sprites"


def _strip(frames):
    fw, fh = frames[0].size
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * fw, 0))
    return sheet


def _write(sets, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for state, frames in sorted(sets.items()):
        path = out_dir / ("%s.png" % state)
        _strip(frames).save(path)
        written.append("%s (%d)" % (state, len(frames)))
    return written


def build_mir():
    frame, figure_h, _ = contract.SCALE["mir"]
    return _write(mir_mod.build(frame=frame, figure_h=figure_h), SPRITES / "band" / "mir")


def build_nari():
    frame, figure_h, _ = contract.SCALE["nari"]
    return _write(nari_mod.build(frame=frame, figure_h=figure_h), SPRITES / "band" / "nari")


def build_foe(name):
    frame, figure_h, _ = contract.SCALE[name]
    cls = foes.FOES[name]
    return _write(cls.build(frame=frame, figure_h=figure_h), SPRITES / "enemies" / name)


TARGETS = {
    "mir": build_mir,
    "nari": build_nari,
    "slime": lambda: build_foe("slime"),
    "drifter": lambda: build_foe("drifter"),
    "elite_wraith": lambda: build_foe("elite_wraith"),
}


def main(argv):
    want = argv[1:] or list(TARGETS)
    for name in want:
        fn = TARGETS.get(name)
        if not fn:
            print("unknown target: %s (have: %s)" % (name, ", ".join(TARGETS)))
            return 2
        t = time.time()
        states = fn()
        print("%-13s %5.1fs  %s" % (name, time.time() - t, ", ".join(states)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
