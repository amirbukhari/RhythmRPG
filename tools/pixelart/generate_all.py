#!/usr/bin/env python3
"""Regenerate every committed art asset from source, in one command:

    python3 tools/pixelart/generate_all.py

Deterministic -- byte-identical output unless the sprite/tile definitions
change. See docs/design/art-bible.md for the direction behind it all.
"""

from __future__ import annotations

import tiles
import heroes
import enemies
import backgrounds
import props
import ui
import fx
from skatopia import save


def main() -> None:
    save(tiles.build(), "tilemaps/overworld_tileset.png")
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
