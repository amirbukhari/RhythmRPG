#!/usr/bin/env python3
"""Regenerate every committed art asset from source, in one command:

    python3 tools/pixelart/generate_all.py

Deterministic -- byte-identical output unless the sprite/tile definitions
change. See docs/design/art-bible.md for the direction behind it all.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import cohesion_lint
import tiles
import enemies
import props
import ui
import fx
from skatopia import save

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "overworld"))
import generate_overworld_map  # noqa: E402  -- the world's map-layout owner (§8.8)


def main() -> None:
    # The overworld tileset (20 tiles: 4 base x 5 region-tinted variants,
    # PRD §8.8) is owned here; the map layout/echoes/markers are owned by
    # generate_overworld_map.py, invoked right after so one command
    # regenerates the whole explorable world consistently.
    save(tiles.build_multi_region(), "tilemaps/overworld_tileset.png")
    generate_overworld_map.main()
    # Foes are AI-generated (newfoes.py, committed); the procedural sheets are
    # a fallback that must not clobber the shipped art (same rule as landmarks).
    if os.environ.get("REGEN_FOES") == "1":
        enemies.build_all()
    save(props.build_sheet(), "sprites/overworld/props.png")
    save(ui.panel(False), "ui/panel.png")
    save(ui.panel(True), "ui/panel_boss.png")
    save(fx.radial(), "fx/glow.png")
    save(fx.spark(), "fx/spark.png")
    save(fx.haze(), "fx/haze.png")
    save(fx.godray(), "fx/godray.png")
    # The old ink landmark sheet is retired (art cohesion audit C1/C6): region
    # set-pieces are the painterly gate landforms + authored dressing now.
    # The playable character (Mir) is AI-generated + committed (newband.py ->
    # bake_cast.py -> requantize_cast.py -> outline_pass.py); nothing to
    # regenerate procedurally here since the v10.0 solo pivot.
    print("all art regenerated")
    # the art cohesion audit's checks, as a permanent gate (exit 1 on findings)
    if cohesion_lint.main() != 0:
        raise SystemExit("cohesion lint failed -- see findings above")


if __name__ == "__main__":
    main()
