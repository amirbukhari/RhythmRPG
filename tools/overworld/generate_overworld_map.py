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

# --- world layout: the Ascent as an OPEN world (v13.0), not a strip --------
# Owner: "we start on the left but it's like you ascend to a world that's
# extensive to the up down and right and the story takes you through a
# specific path around the map to a specific point for the ending."
# Mir starts drowned in the WEST (the Fold, the Kelp Shelf climbing above
# it); crossing the Breach surfaces into a Scar that sprawls north, south,
# and east; the Stage waits at one specific far point. Regions are organic
# TERRITORIES (weighted Voronoi with jitter), not columns.
REGIONS = ["shallows", "saltmines", "pit", "attic", "hall"]  # ids: fold, shelf, breach, scar, stage
MAP_W, MAP_H = 112, 64

# (col, row, weight) -- a lower weight claims a LARGER territory
REGION_ANCHORS = [
    (11, 50, 0.9),   # the Fold: the drowned south-west, where Mir wakes
    (17, 18, 1.0),   # the Kelp Shelf: the drowned north-west climb
    (34, 34, 1.5),   # the Breach: the narrow crossing band
    (66, 38, 0.55),  # the Scar: the huge open surface (up, down, and right)
    (97, 13, 1.05),  # the Stage: the specific far point where it ends
]

_JR = random.Random(20260717)
_JIT = [[_JR.uniform(-2.5, 2.5) for _ in range(MAP_W)] for _ in range(MAP_H)]


def _region_at(c: int, r: int) -> int:
    best, bd = 0, 1e18
    for i, (ac, ar, w) in enumerate(REGION_ANCHORS):
        d = w * (((c - ac + _JIT[r][c]) ** 2 + (r - ar + _JIT[r][(c * 7 + 3) % MAP_W]) ** 2) ** 0.5)
        if d < bd:
            best, bd = i, d
    return best


REGION_MAP: list[list[int]] = [[_region_at(c, r) for c in range(MAP_W)] for r in range(MAP_H)]

# Local tile ids within a region's own 4-tile block (see tiles.py).
GRASS, PATH, WATER, ROCK = 0, 1, 2, 3
WALKABLE_LOCAL = {GRASS, PATH}


def region_of(col: int, row: int = 0) -> int:
    """Region territory at a tile (2D since v13.0; row defaults 0 for edges)."""
    return REGION_MAP[min(MAP_H - 1, max(0, row))][min(MAP_W - 1, max(0, col))]


def tid(region_index: int, local: int) -> int:
    """The raw (0-based) tile id for `local` (GRASS/PATH/WATER/ROCK) in a given region."""
    return region_index * 4 + local


def is_walkable_id(raw_id: int) -> bool:
    return (raw_id % 4) in WALKABLE_LOCAL


# Campaign node markers (ABSOLUTE coords since v13.0), kept in sync with
# src/data/content/campaign/opening_biome.json. The road tours the open
# world: out of the Fold, north up the Shelf, east across the Breach, a long
# south-east swing through the Scar, then north-east to the Stage -- the
# specific point where it ends.
NODE_MARKERS: dict[str, tuple[int, int]] = {
    "opening_1": (20, 45),
    "mid_1": (22, 17),
    "mid_2": (36, 31),
    "mid_3": (66, 52),
    "boss_1": (96, 14),
}
SPAWN: tuple[int, int] = (8, 54)

# Two echoes per region territory (10 total), anchors ABSOLUTE. The echo
# voice carries the Ascent premise -- the Fold's faith, the climb, the
# crossing, the hostile surface, and what waits on the Stage.
ECHOES: list[tuple[str, str, str, int, tuple[int, int]]] = [
    ("The First Prayer", "We didn't raise the obelisk. We woke on the floor and it was already listening.", "shallows", 0, (6, 40)),
    ("The Unlit Lamp", "Nobody leaves the Fold. It isn't a rule. It's just that nobody ever has.", "shallows", 0, (16, 59)),
    ("The Climber's Knot", "Rope enough to reach the light -- if you don't weigh anything anymore.", "saltmines", 1, (9, 9)),
    ("The First Wreck", "Every ship that ever sank points the same way. Up.", "saltmines", 1, (28, 8)),
    ("The Broken Foam", "The line between worlds is thinner than a footstep. His fit inside mine.", "pit", 2, (33, 22)),
    ("Salt in the Lungs", "The first breath burns. The second one is his name.", "pit", 2, (39, 43)),
    ("The Small Prints", "They walk IN. Toward the den. Why would he walk toward it?", "attic", 3, (54, 28)),
    ("What the Claws Keep", "It doesn't eat what it takes. It collects.", "attic", 3, (75, 58)),
    ("The Rehearsal", "The music stops every time the small one cries. Then it starts again, angrier.", "hall", 4, (88, 6)),
    ("The Huntress's Mark", "She doesn't hunt to kill. She hunts to keep.", "hall", 4, (104, 24)),
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
        grid[r][c] = tid(region_of(c, r), PATH)
        since_jog += 1
        if rng is not None and since_jog >= 3 and c != c1 and abs(c - c1) > 2 and rng.random() < 0.38:
            drift = rng.choice((-1, 1))
            nr = r + drift
            if 2 <= nr < MAP_H - 2:
                r = nr
                grid[r][c] = tid(region_of(c, r), PATH)  # keep the corridor connected
                since_jog = 0
    cc = c1
    step = 1 if r1 >= r else -1
    since_jog = 0
    for rr in range(r, r1 + step, step):
        grid[rr][cc] = tid(region_of(cc, rr), PATH)
        since_jog += 1
        if rng is not None and since_jog >= 3 and rr != r1 and abs(rr - r1) > 2 and rng.random() < 0.38:
            drift = rng.choice((-1, 1))
            nc = cc + drift
            if 2 <= nc < MAP_W - 2:
                cc = nc
                grid[rr][cc] = tid(region_of(cc, rr), PATH)
                since_jog = 0
    # land the endpoint exactly (the meander may end a column off)
    step = 1 if c1 >= cc else -1
    for c in range(cc, c1 + step, step):
        grid[r1][c] = tid(region_of(c, r1), PATH)


def _carve_secret_spur(grid: list[list[int]], rng: random.Random, from_pt: tuple[int, int], to_pt: tuple[int, int]) -> None:
    """A 1-wide corridor from a point near the main road to a hidden pocket,
    with an L-bend so the pocket isn't visible from the junction -- PRD
    §8.8.3's 'reads as passable only up close' hidden path. The pocket
    itself is carved as a small walkable clearing ringed by rock, entered
    only through this spur."""
    c0, r0 = from_pt
    c1, r1 = to_pt
    region = region_of(c1, r1)
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


def _dress_zones(grid: list[list[int]], rng: random.Random) -> None:
    """Territory dressing (v13.0): each region's obstacles are seeded inside
    its own organic zone, so the layout language follows the territory shape
    instead of a 26-column strip."""

    def blob(c0: int, r0: int, w_: int, h_: int, local: int, ri: int) -> None:
        for r in range(r0, r0 + h_):
            for c in range(c0, c0 + w_):
                if 2 <= c < MAP_W - 2 and 2 <= r < MAP_H - 2 and REGION_MAP[r][c] == ri:
                    grid[r][c] = tid(ri, local)

    zone: dict[int, list[tuple[int, int]]] = {i: [] for i in range(5)}
    for r in range(2, MAP_H - 2):
        for c in range(2, MAP_W - 2):
            zone[REGION_MAP[r][c]].append((c, r))

    def spots(ri: int, n: int) -> list[tuple[int, int]]:
        tiles = zone[ri]
        return [tiles[rng.randrange(len(tiles))] for _ in range(n)]

    # the Fold: open silt with pools and rock knots; the town stays clear
    for c, r in spots(0, 4):
        if (c - SPAWN[0]) ** 2 + (r - SPAWN[1]) ** 2 > 64:
            blob(c, r, rng.randrange(3, 6), rng.randrange(2, 5), WATER, 0)
    for c, r in spots(0, 5):
        if (c - SPAWN[0]) ** 2 + (r - SPAWN[1]) ** 2 > 49:
            blob(c, r, 2, 2, ROCK, 0)
    # the Kelp Shelf: worked terrace ridges climbing the drowned slope
    for c, r in spots(1, 14):
        blob(c, r, rng.randrange(3, 8), rng.choice((1, 2)), ROCK, 1)
    for c, r in spots(1, 3):
        blob(c, r, rng.randrange(3, 5), rng.randrange(2, 4), WATER, 1)
    # the Breach: tide pools along the crossing
    for c, r in spots(2, 6):
        blob(c, r, rng.randrange(2, 5), rng.randrange(2, 4), WATER, 2)
    # the Scar: outcrop knots + dark pits, sprawling every direction
    for c, r in spots(3, 26):
        blob(c, r, rng.randrange(2, 5), rng.randrange(2, 4), ROCK, 3)
    for c, r in spots(3, 6):
        blob(c, r, rng.randrange(3, 7), rng.randrange(2, 5), WATER, 3)
    # the Stage: the boss lake (its island is carved after) + broken colonnade
    bc, br = NODE_MARKERS["boss_1"]
    for r in range(br - 9, br + 10):
        for c in range(bc - 11, bc + 12):
            if 2 <= c < MAP_W - 2 and 2 <= r < MAP_H - 2 and (c - bc) ** 2 + ((r - br) * 1.3) ** 2 <= 100 and REGION_MAP[r][c] == 4:
                grid[r][c] = tid(4, WATER)
    for c, r in spots(4, 6):
        blob(c, r, 1, rng.randrange(2, 4), ROCK, 4)


def build_grid() -> list[list[int]]:
    rng = random.Random(20260711)
    grid = [[tid(REGION_MAP[r][c], GRASS) for c in range(MAP_W)] for r in range(MAP_H)]

    # solid rock border
    for c in range(MAP_W):
        grid[0][c] = tid(REGION_MAP[0][c], ROCK)
        grid[MAP_H - 1][c] = tid(REGION_MAP[MAP_H - 1][c], ROCK)
    for r in range(MAP_H):
        grid[r][0] = tid(REGION_MAP[r][0], ROCK)
        grid[r][MAP_W - 1] = tid(REGION_MAP[r][MAP_W - 1], ROCK)

    _dress_zones(grid, rng)

    # --- macro landforms (v13.1: map-structure variation) --------------------
    # The CANYON: two curved rock walls running down through the mid-Scar,
    # with gap windows -- the surface gets corridors and chokepoints instead
    # of open sprawl (the touring road punches its own gate through later).
    for t100 in range(0, 101):
        t = t100 / 100.0
        cc = int(48 + t * 12 + 3.0 * __import__("math").sin(t * 6.0))
        rr = int(14 + t * 44)
        for side in (-4, 4):
            wc = cc + side
            if t100 % 23 < 3:  # gap windows through the walls
                continue
            if 2 <= wc < MAP_W - 2 and 2 <= rr < MAP_H - 2 and REGION_MAP[rr][wc] == 3:
                grid[rr][wc] = tid(3, ROCK)
                if 2 <= wc + (1 if side > 0 else -1) < MAP_W - 2:
                    grid[rr][wc + (1 if side > 0 else -1)] = tid(3, ROCK)
    # The CRATER: a broken rock ring with a dark pit at its heart (NE Scar)
    crc, crr = 86, 44
    for r in range(crr - 8, crr + 9):
        for c in range(crc - 8, crc + 9):
            if not (2 <= c < MAP_W - 2 and 2 <= r < MAP_H - 2) or REGION_MAP[r][c] != 3:
                continue
            d2 = (c - crc) ** 2 + (r - crr) ** 2
            if 25 <= d2 <= 42 and (c + r * 3) % 9 != 0:  # ring, with breaches
                grid[r][c] = tid(3, ROCK)
            elif d2 <= 4:
                grid[r][c] = tid(3, WATER)  # the pit

    # scattered texture obstacles, placed before carving so the road always wins
    for _ in range(160):
        c, r = rng.randrange(2, MAP_W - 2), rng.randrange(2, MAP_H - 2)
        grid[r][c] = tid(REGION_MAP[r][c], ROCK if rng.random() < 0.6 else WATER)

    # secret spurs: each echo is reachable only by branching off the main
    # road at its region's node marker, then walking an L-bend corridor away
    # from it into a hidden pocket (PRD §8.8.3). Carved BEFORE the main road
    # (below) so the road always has final say if a pocket's ring happens to
    # cross its route -- the road must never be the thing that gets sealed.
    for _title, _text, _region, ri, anchor in ECHOES:
        node_id = list(NODE_MARKERS.keys())[ri]
        jump_off = NODE_MARKERS[node_id]
        _carve_secret_spur(grid, rng, jump_off, anchor)

    # the Conductor's stage is an ISLAND (v11.5). The boss node sits in the
    # hall lake, previously reachable only by its causeway while the "arena"
    # was painted over open water (owner: "it's over the water though....").
    # Carve a real grass island around the node: the fight gets true walkable
    # ground and the painted marble stage ends at a real shoreline.
    bc, br = NODE_MARKERS["boss_1"]
    for r in range(br - 5, br + 6):
        for c in range(bc - 5, bc + 6):
            if 0 <= c < MAP_W and 0 <= r < MAP_H and (c - bc) ** 2 + (r - br) ** 2 <= 20:
                if grid[r][c] % 4 != PATH:
                    grid[r][c] = tid(REGION_MAP[r][c], GRASS)

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
