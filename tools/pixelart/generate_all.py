#!/usr/bin/env python3
"""Regenerate every committed art asset from source, in one command:

    python3 tools/pixelart/generate_all.py

Deterministic -- byte-identical output unless the sprite/tile definitions
change. See docs/design/art-bible.md for the direction behind it all.
"""

from __future__ import annotations

import sys
from pathlib import Path

import tiles
import heroes
import enemies
import backgrounds
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
    heroes.build_all()
    enemies.build_all()
    save(backgrounds.build(False), "backgrounds/battle_abyss.png")
    save(backgrounds.build(True), "backgrounds/battle_conductor.png")
    save(backgrounds.caustics(), "backgrounds/caustics.png")
    save(props.build_sheet(), "sprites/overworld/props.png")
    save(ui.panel(False), "ui/panel.png")
    save(ui.panel(True), "ui/panel_boss.png")
    save(ui.icon_sheet()[0], "ui/icons.png")
    save(fx.radial(), "fx/glow.png")
    save(fx.spark(), "fx/spark.png")
    print("all art regenerated")


if __name__ == "__main__":
    main()
