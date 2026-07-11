#!/usr/bin/env python3
"""Generates the overworld's committed art/data assets:

  assets/tilemaps/overworld_tileset.png  (4 16x16 tiles: grass, path, water, rock)
  assets/tilemaps/overworld.json         (Tiled-JSON map: `ground` tile layer +
                                          `markers` object layer)

Run from anywhere; paths are resolved relative to the repo root. Deterministic
(fixed RNG seed), so re-running produces byte-identical output unless the
authored layout below changes. The script BFS-validates that every campaign
node marker is reachable on foot from the spawn point before writing anything,
so a bad layout edit fails loudly here instead of soft-locking the game.

The tileset is programmatically generated placeholder art (PRD §11.4/§20.2:
no image-generation tooling is available in this environment); the *map
layout and marker data* are the real authored content.
"""

from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "assets" / "tilemaps"

TILE_SIZE = 16
MAP_W, MAP_H = 40, 24  # 640x384 px -- larger than the 320x180 viewport so camera-follow matters

# Tile ids (0-based within the tileset; Tiled layer data uses id+1 as the GID).
GRASS, PATH, WATER, ROCK = 0, 1, 2, 3
WALKABLE = {GRASS, PATH}

# Campaign node markers: nodeId -> (col, row). Kept in sync with
# src/data/content/campaign/opening_biome.json by the content-registry
# cross-check in OverworldScene (it warns on unknown nodeIds at runtime) and
# by the e2e suite walking the real map.
NODE_MARKERS: dict[str, tuple[int, int]] = {
    "opening_1": (8, 19),
    "mid_1": (16, 15),
    "mid_2": (24, 11),
    "mid_3": (30, 7),
    "boss_1": (35, 3),
}
SPAWN: tuple[int, int] = (4, 20)


def build_tileset(path: Path) -> None:
    rng = random.Random(20260710)
    img = Image.new("RGBA", (TILE_SIZE * 4, TILE_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def speckle(tile_x: int, base: tuple[int, int, int], dots: tuple[int, int, int], n: int) -> None:
        draw.rectangle([tile_x, 0, tile_x + TILE_SIZE - 1, TILE_SIZE - 1], fill=base + (255,))
        for _ in range(n):
            x = tile_x + rng.randrange(TILE_SIZE)
            y = rng.randrange(TILE_SIZE)
            draw.point((x, y), fill=dots + (255,))

    speckle(GRASS * TILE_SIZE, (58, 125, 68), (44, 98, 52), 26)  # grass: green, darker flecks
    speckle(PATH * TILE_SIZE, (194, 163, 107), (166, 136, 82), 18)  # path: packed dirt
    speckle(WATER * TILE_SIZE, (43, 108, 176), (96, 165, 220), 10)  # water: blue, light glints
    speckle(ROCK * TILE_SIZE, (107, 114, 128), (75, 82, 94), 22)  # rock: gray, cracks

    # A subtle edge shade on obstacle tiles so they read as solid at a glance.
    for tile in (WATER, ROCK):
        x0 = tile * TILE_SIZE
        draw.rectangle([x0, 0, x0 + TILE_SIZE - 1, 0], fill=(30, 36, 48, 255))
        draw.rectangle([x0, TILE_SIZE - 1, x0 + TILE_SIZE - 1, TILE_SIZE - 1], fill=(30, 36, 48, 255))

    img.save(path)


def build_grid() -> list[list[int]]:
    rng = random.Random(20260710)
    grid = [[GRASS] * MAP_W for _ in range(MAP_H)]

    # Solid rock border so the world reads as bounded (movement also clamps).
    for c in range(MAP_W):
        grid[0][c] = ROCK
        grid[MAP_H - 1][c] = ROCK
    for r in range(MAP_H):
        grid[r][0] = ROCK
        grid[r][MAP_W - 1] = ROCK

    # Authored obstacle features.
    for r in range(2, 8):  # north-west lake
        for c in range(3, 11):
            grid[r][c] = WATER
    for r in range(16, 21):  # south-east pond
        for c in range(30, 37):
            grid[r][c] = WATER
    for c in range(14, 23):  # central rock ridge
        grid[8][c] = ROCK
        grid[9][c] = ROCK
    for r in range(12, 18):  # western rock spur
        grid[r][6] = ROCK
        grid[r][7] = ROCK

    # Scattered rocks/water for texture. Placed before the path is carved, so
    # the path always wins and connectivity is preserved by construction.
    for _ in range(30):
        c, r = rng.randrange(2, MAP_W - 2), rng.randrange(2, MAP_H - 2)
        grid[r][c] = ROCK if rng.random() < 0.7 else WATER

    # Carve the road: L-shaped (horizontal, then vertical) segments through
    # spawn and every node, in campaign order.
    waypoints = [SPAWN, *NODE_MARKERS.values()]
    for (c0, r0), (c1, r1) in zip(waypoints, waypoints[1:]):
        step = 1 if c1 >= c0 else -1
        for c in range(c0, c1 + step, step):
            grid[r0][c] = PATH
        step = 1 if r1 >= r0 else -1
        for r in range(r0, r1 + step, step):
            grid[r][c1] = PATH

    return grid


def validate(grid: list[list[int]]) -> None:
    seen = {SPAWN}
    queue = deque([SPAWN])
    while queue:
        c, r = queue.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc, nr = c + dc, r + dr
            if 0 <= nc < MAP_W and 0 <= nr < MAP_H and (nc, nr) not in seen and grid[nr][nc] in WALKABLE:
                seen.add((nc, nr))
                queue.append((nc, nr))
    unreachable = [nid for nid, pos in NODE_MARKERS.items() if pos not in seen]
    if unreachable:
        raise SystemExit(f"Layout bug: markers unreachable from spawn: {unreachable}")


def build_map_json(grid: list[list[int]]) -> dict:
    def point_object(obj_id: int, name: str, col: int, row: int, properties: list[dict]) -> dict:
        return {
            "id": obj_id,
            "name": name,
            "type": "",
            "point": True,
            "x": col * TILE_SIZE + TILE_SIZE / 2,
            "y": row * TILE_SIZE + TILE_SIZE / 2,
            "width": 0,
            "height": 0,
            "rotation": 0,
            "visible": True,
            "properties": properties,
        }

    objects = [point_object(1, "spawn", *SPAWN, [])]
    objects += [
        point_object(i + 2, node_id, col, row, [{"name": "nodeId", "type": "string", "value": node_id}])
        for i, (node_id, (col, row)) in enumerate(NODE_MARKERS.items())
    ]

    return {
        "type": "map",
        "version": "1.10",
        "tiledversion": "1.10.2",
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "infinite": False,
        "width": MAP_W,
        "height": MAP_H,
        "tilewidth": TILE_SIZE,
        "tileheight": TILE_SIZE,
        "nextlayerid": 3,
        "nextobjectid": len(objects) + 1,
        "layers": [
            {
                "id": 1,
                "name": "ground",
                "type": "tilelayer",
                "width": MAP_W,
                "height": MAP_H,
                "x": 0,
                "y": 0,
                "opacity": 1,
                "visible": True,
                "data": [tile + 1 for row in grid for tile in row],
            },
            {
                "id": 2,
                "name": "markers",
                "type": "objectgroup",
                "x": 0,
                "y": 0,
                "opacity": 1,
                "visible": True,
                "objects": objects,
            },
        ],
        "tilesets": [
            {
                "firstgid": 1,
                "name": "overworld_tileset",
                "image": "overworld_tileset.png",
                "imagewidth": TILE_SIZE * 4,
                "imageheight": TILE_SIZE,
                "tilewidth": TILE_SIZE,
                "tileheight": TILE_SIZE,
                "tilecount": 4,
                "columns": 4,
                "margin": 0,
                "spacing": 0,
                "tiles": [
                    {"id": WATER, "properties": [{"name": "collides", "type": "bool", "value": True}]},
                    {"id": ROCK, "properties": [{"name": "collides", "type": "bool", "value": True}]},
                ],
            }
        ],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid = build_grid()
    validate(grid)
    build_tileset(OUT_DIR / "overworld_tileset.png")
    (OUT_DIR / "overworld.json").write_text(json.dumps(build_map_json(grid), indent=2) + "\n")
    print(f"Wrote {OUT_DIR / 'overworld_tileset.png'} and {OUT_DIR / 'overworld.json'}")


if __name__ == "__main__":
    main()
