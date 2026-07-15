#!/usr/bin/env python3
"""Generates the overworld's map data:

  assets/tilemaps/overworld.json  (Tiled-JSON map: `ground` tile layer +
                                   `markers` object layer + `echoes` object layer)

Run from anywhere; paths are resolved relative to the repo root. Deterministic
(fixed RNG seed), so re-running produces byte-identical output unless the
authored layout below changes. The script BFS-validates that every campaign
node marker AND every echo/secret pocket is reachable on foot from the spawn
point before writing anything, so a bad layout edit fails loudly here
instead of soft-locking or stranding content in the shipped game.

PRD §8.8 (v7.0): this is no longer a single-road "hub" between battles --
it's a large, five-region explorable world (one region per movement, joined
left-to-right in campaign order), substantially bigger than the walkable
area alone requires, specifically so it has room to hold secrets. The
tileset image itself (20 tiles: 4 base tiles x 5 region-tinted variants) is
owned by tools/pixelart/tiles.py (region_tiles/build_multi_region) -- this
script only lays out which tile id goes where and where the markers/echoes
sit. See tools/pixelart/generate_all.py, which runs both in the right order.
"""

from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "assets" / "tilemaps"

TILE_SIZE = 16

# --- world layout: five regions joined left-to-right, campaign order -------
REGIONS = ["shallows", "saltmines", "pit", "attic", "hall"]
REGION_W, REGION_H = 26, 34
MAP_W, MAP_H = REGION_W * len(REGIONS), REGION_H

# Local tile ids within a region's own 4-tile block (see tiles.py).
GRASS, PATH, WATER, ROCK = 0, 1, 2, 3
WALKABLE_LOCAL = {GRASS, PATH}


def region_of(col: int) -> int:
    return min(len(REGIONS) - 1, col // REGION_W)


def tid(region_index: int, local: int) -> int:
    """The raw (0-based) tile id for `local` (GRASS/PATH/WATER/ROCK) in a given region."""
    return region_index * 4 + local


def is_walkable_id(raw_id: int) -> bool:
    return (raw_id % 4) in WALKABLE_LOCAL


def wp(region_index: int, local_col: int, local_row: int) -> tuple[int, int]:
    """A waypoint expressed in a region's own local coordinates."""
    return (region_index * REGION_W + local_col, local_row)


# Campaign node markers, kept in sync with src/data/content/campaign/opening_biome.json.
# Placed in a loose zigzag across the five regions -- not just a straight
# road -- so the world reads as a real winding descent, not a corridor.
NODE_MARKERS: dict[str, tuple[int, int]] = {
    "opening_1": wp(0, 21, 8),
    "mid_1": wp(1, 20, 26),
    "mid_2": wp(2, 21, 9),
    "mid_3": wp(3, 20, 25),
    "boss_1": wp(4, 20, 17),
}
SPAWN: tuple[int, int] = wp(0, 3, 27)

# Two echoes per region (10 total) -- lore text mirrors world-bible §5b
# verbatim so the map data and the design doc never drift apart. Each is
# (title, one-line found-text, region, local anchor near where its spur/pocket lands).
ECHOES: list[tuple[str, str, str, int, tuple[int, int]]] = [
    ("Baker's Ledger", "Everyone's boat but mine -- I'll follow once the last one's free.", "shallows", 0, wp(0, 9, 6)),
    ("The Empty Cradle", "She untied every line but her own.", "shallows", 0, wp(0, 18, 30)),
    ("The Foreman's Ledger", "Everyone's shift but mine ends at the sound. I keep counting anyway.", "saltmines", 1, wp(1, 8, 30)),
    ("Listening Stones", "If you stack them right, they listen back.", "saltmines", 1, wp(1, 17, 5)),
    ("Two Ticket Stubs", "Front row, both of us. He said don't blink.", "pit", 2, wp(2, 8, 27)),
    ("The Fortune Wheel", "It never lands anywhere else now. I've checked.", "pit", 2, wp(2, 18, 6)),
    ("The Boarded Window", "We didn't lock her in. We tried to keep it out.", "attic", 3, wp(3, 9, 6)),
    ("The Handprint", "Not for help. For quiet.", "attic", 3, wp(3, 17, 28)),
    ("The Program", "He wrote his own name in last, every time, like it might come out different.", "hall", 4, wp(4, 9, 25)),
    ("The Standing Ovation", "They clapped until the water was over their heads. He never once turned around.", "hall", 4, wp(4, 15, 6)),
]


def _rect(grid: list[list[int]], c0: int, r0: int, c1: int, r1: int, val: int) -> None:
    for r in range(max(0, r0), min(MAP_H, r1)):
        for c in range(max(0, c0), min(MAP_W, c1)):
            grid[r][c] = val


def _carve_path(grid: list[list[int]], a: tuple[int, int], b: tuple[int, int], rng: random.Random | None = None) -> None:
    """Corridor from a to b, PATH tile per-region. With an rng the corridor
    MEANDERS: while walking each leg it drifts a tile sideways every few
    steps (scale/placement audit SP11 -- dead-straight parallel roads read
    artificial). Without an rng it stays the plain L (used by secret spurs,
    whose pockets need the predictable punch-through)."""
    c0, r0 = a
    c1, r1 = b
    r = r0
    step = 1 if c1 >= c0 else -1
    since_jog = 0
    for c in range(c0, c1 + step, step):
        grid[r][c] = tid(region_of(c), PATH)
        since_jog += 1
        if rng is not None and since_jog >= 3 and c != c1 and abs(c - c1) > 2 and rng.random() < 0.38:
            drift = rng.choice((-1, 1))
            nr = r + drift
            if 2 <= nr < MAP_H - 2:
                r = nr
                grid[r][c] = tid(region_of(c), PATH)  # keep the corridor connected
                since_jog = 0
    cc = c1
    step = 1 if r1 >= r else -1
    since_jog = 0
    for rr in range(r, r1 + step, step):
        grid[rr][cc] = tid(region_of(cc), PATH)
        since_jog += 1
        if rng is not None and since_jog >= 3 and rr != r1 and abs(rr - r1) > 2 and rng.random() < 0.38:
            drift = rng.choice((-1, 1))
            nc = cc + drift
            if 2 <= nc < MAP_W - 2:
                cc = nc
                grid[rr][cc] = tid(region_of(cc), PATH)
                since_jog = 0
    # land the endpoint exactly (the meander may end a column off)
    step = 1 if c1 >= cc else -1
    for c in range(cc, c1 + step, step):
        grid[r1][c] = tid(region_of(c), PATH)


def _carve_secret_spur(grid: list[list[int]], rng: random.Random, from_pt: tuple[int, int], to_pt: tuple[int, int]) -> None:
    """A 1-wide corridor from a point near the main road to a hidden pocket,
    with an L-bend so the pocket isn't visible from the junction -- PRD
    §8.8.3's 'reads as passable only up close' hidden path. The pocket
    itself is carved as a small walkable clearing ringed by rock, entered
    only through this spur."""
    c0, r0 = from_pt
    c1, r1 = to_pt
    region = region_of(c1)
    # the pocket FIRST: a small walkable clearing ringed by rock so it reads
    # as enclosed... then the spur carved SECOND, punching the one opening
    # through the ring the corridor actually needs. Order matters: carving
    # the ring after the corridor would reseal it.
    _rect(grid, c1 - 2, r1 - 2, c1 + 3, r1 + 3, tid(region, ROCK))
    _rect(grid, c1 - 1, r1 - 1, c1 + 2, r1 + 2, tid(region, GRASS))
    grid[r1][c1] = tid(region, PATH)
    bend_col = c0 if rng.random() < 0.5 else c1
    _carve_path(grid, (c0, r0), (bend_col, r0))
    _carve_path(grid, (bend_col, r0), (bend_col, r1))
    _carve_path(grid, (bend_col, r1), (c1, r1))


def _dress_region(grid: list[list[int]], rng: random.Random, ri: int) -> None:
    """Region-specific obstacle placement so each of the five feels distinct
    in layout, not just tint (PRD §11.1.1 'one palette, five moods',
    extended to the walkable world by §8.8.1)."""
    base = ri * REGION_W
    name = REGIONS[ri]
    w = lambda local: tid(ri, local)  # noqa: E731

    if name == "shallows":  # coastal: bay inlets top and bottom
        _rect(grid, base + 2, 2, base + 12, 9, w(WATER))
        _rect(grid, base + 14, REGION_H - 10, base + 24, REGION_H - 3, w(WATER))
        for _ in range(3):  # sunken foundation stubs
            c, r = base + rng.randrange(4, REGION_W - 4), rng.randrange(12, REGION_H - 12)
            _rect(grid, c, r, c + 3, r + 3, w(ROCK))
    elif name == "saltmines":  # mine road: worked rock ridges (SP11: segmented
        # with jittered rows and gaps, not four dead-straight full-width bars)
        for ridge_r in (6, 9, 20, 23):
            c = base + 3
            while c < base + REGION_W - 3:
                seg = rng.randrange(4, 9)
                rr = ridge_r + rng.choice((-1, 0, 0, 1))
                _rect(grid, c, rr, min(base + REGION_W - 3, c + seg), rr + 1, w(ROCK))
                c += seg + rng.randrange(1, 4)  # gap between worked sections
        _rect(grid, base + 4, 14, base + 10, 18, w(WATER))  # flooded shaft
    elif name == "pit":  # sunken carnival ring: a big circular flooded pit, centered
        cx, cy, rad = base + REGION_W // 2, REGION_H // 2, 7
        for r in range(REGION_H):
            for c in range(base, base + REGION_W):
                if (c - cx) ** 2 + (r - cy) ** 2 <= rad * rad:
                    grid[r][c] = w(WATER)
        for _ in range(4):  # toppled seating debris
            c, r = base + rng.randrange(3, REGION_W - 3), rng.randrange(3, REGION_H - 3)
            if (c - cx) ** 2 + (r - cy) ** 2 > (rad + 2) ** 2:
                _rect(grid, c, r, c + 2, r + 2, w(ROCK))
    elif name == "attic":  # building exterior: tight rock-partitioned alleys.
        # SP9: the four partitions vary -- jittered x, staggered ends, widths
        # 1-2, and segmented runs -- so the region stops reading as five
        # copies of one rounded-rect pillar.
        for i in range(4):
            c = base + 5 + i * 5 + rng.choice((-1, 0, 1))
            width = rng.choice((1, 1, 2))
            r = 3 + rng.randrange(0, 4)
            end = REGION_H - 6 - rng.randrange(0, 4)
            while r < end:
                seg = rng.randrange(5, 11)
                _rect(grid, c, r, c + width, min(end, r + seg), w(ROCK))
                r += seg + rng.randrange(2, 4)  # alley break
        # punch cross-corridors so it's a maze, not solid walls
        for gap_r in (9, 17, 26):
            for c in range(base + 4, base + 23):
                if grid[gap_r][c] == w(ROCK):
                    grid[gap_r][c] = w(GRASS)
    elif name == "hall":  # flooded plaza: open water with statue columns
        _rect(grid, base + 2, 2, base + REGION_W - 2, REGION_H - 2, w(WATER))
        for cx, cy in [(8, 10), (18, 8), (6, 22), (20, 24), (13, 16)]:
            _rect(grid, base + cx, cy, base + cx + 2, cy + 3, w(ROCK))


def build_grid() -> list[list[int]]:
    rng = random.Random(20260711)
    grid = [[tid(region_of(c), GRASS) for c in range(MAP_W)] for _ in range(MAP_H)]

    # solid rock border
    for c in range(MAP_W):
        grid[0][c] = tid(region_of(c), ROCK)
        grid[MAP_H - 1][c] = tid(region_of(c), ROCK)
    for r in range(MAP_H):
        grid[r][0] = tid(region_of(0), ROCK)
        grid[r][MAP_W - 1] = tid(region_of(MAP_W - 1), ROCK)

    for ri in range(len(REGIONS)):
        _dress_region(grid, rng, ri)

    # scattered texture obstacles, placed before carving so the road always wins
    for _ in range(90):
        c, r = rng.randrange(2, MAP_W - 2), rng.randrange(2, MAP_H - 2)
        grid[r][c] = tid(region_of(c), ROCK if rng.random() < 0.6 else WATER)

    # secret spurs: each echo is reachable only by branching off the main
    # road at its region's node marker, then walking an L-bend corridor away
    # from it into a hidden pocket (PRD §8.8.3). Carved BEFORE the main road
    # (below) so the road always has final say if a pocket's ring happens to
    # cross its route -- the road must never be the thing that gets sealed.
    for _title, _text, _region, ri, anchor in ECHOES:
        node_id = list(NODE_MARKERS.keys())[ri]
        jump_off = NODE_MARKERS[node_id]
        _carve_secret_spur(grid, rng, jump_off, anchor)

    # the main road: waypoint chain through spawn, every node, in campaign
    # order. Carved LAST so it's never accidentally resealed by a pocket ring.
    # Meandering (rng passed): a worn trail drifts, it doesn't run on rails.
    waypoints = [SPAWN, *NODE_MARKERS.values()]
    for a, b in zip(waypoints, waypoints[1:]):
        _carve_path(grid, a, b, rng)

    return grid


def validate(grid: list[list[int]]) -> None:
    seen = {SPAWN}
    queue = deque([SPAWN])
    while queue:
        c, r = queue.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc, nr = c + dc, r + dr
            if 0 <= nc < MAP_W and 0 <= nr < MAP_H and (nc, nr) not in seen and is_walkable_id(grid[nr][nc]):
                seen.add((nc, nr))
                queue.append((nc, nr))
    unreachable_nodes = [nid for nid, pos in NODE_MARKERS.items() if pos not in seen]
    unreachable_echoes = [title for title, _, _, _, pos in ECHOES if pos not in seen]
    if unreachable_nodes or unreachable_echoes:
        raise SystemExit(f"Layout bug: unreachable from spawn -- nodes={unreachable_nodes} echoes={unreachable_echoes}")


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

    marker_objects = [point_object(1, "spawn", *SPAWN, [])]
    marker_objects += [
        point_object(i + 2, node_id, col, row, [{"name": "nodeId", "type": "string", "value": node_id}])
        for i, (node_id, (col, row)) in enumerate(NODE_MARKERS.items())
    ]

    echo_objects = [
        point_object(
            100 + i,
            f"echo_{i}",
            pos[0],
            pos[1],
            [
                {"name": "title", "type": "string", "value": title},
                {"name": "text", "type": "string", "value": text},
                {"name": "region", "type": "string", "value": region},
            ],
        )
        for i, (title, text, region, _ri, pos) in enumerate(ECHOES)
    ]

    tileset_tiles = []
    for ri in range(len(REGIONS)):
        tileset_tiles.append({"id": tid(ri, WATER), "properties": [{"name": "collides", "type": "bool", "value": True}]})
        tileset_tiles.append({"id": tid(ri, ROCK), "properties": [{"name": "collides", "type": "bool", "value": True}]})

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
        "nextlayerid": 4,
        "nextobjectid": len(marker_objects) + len(echo_objects) + 1,
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
                "objects": marker_objects,
            },
            {
                "id": 3,
                "name": "echoes",
                "type": "objectgroup",
                "x": 0,
                "y": 0,
                "opacity": 1,
                "visible": True,
                "objects": echo_objects,
            },
        ],
        "tilesets": [
            {
                "firstgid": 1,
                "name": "overworld_tileset",
                "image": "overworld_tileset.png",
                "imagewidth": TILE_SIZE * 4 * len(REGIONS),
                "imageheight": TILE_SIZE,
                "tilewidth": TILE_SIZE,
                "tileheight": TILE_SIZE,
                "tilecount": 4 * len(REGIONS),
                "columns": 4 * len(REGIONS),
                "margin": 0,
                "spacing": 0,
                "tiles": tileset_tiles,
            }
        ],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid = build_grid()
    validate(grid)
    (OUT_DIR / "overworld.json").write_text(json.dumps(build_map_json(grid), indent=2) + "\n")
    print(f"Wrote {OUT_DIR / 'overworld.json'} ({MAP_W}x{MAP_H}, {len(REGIONS)} regions, {len(ECHOES)} echoes)")


if __name__ == "__main__":
    main()
