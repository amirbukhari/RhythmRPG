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

# v15.0 THE GREAT EXPANSION: the world is ~10x bigger. 112x64 -> 356x200
# (10.0x area). The five biomes stay, but each is now a huge territory with
# painted sub-variation, a ~20-fight campaign tours the whole map, and ~40
# echoes are strewn through it. The painted ground is baked as CHUNKS
# (paint_ground.py) and camera-culled at runtime so a world this size fits in
# GPU memory. Every absolute coordinate below is authored at this scale.
MAP_W, MAP_H = 356, 200

# (col, row, weight) -- a lower weight claims a LARGER territory. Rescaled from
# the original 112x64 anchors (x3.18, x3.13) so the ascent still flows
# SW-Fold -> NW-Shelf -> centre-Breach -> the huge Scar -> NE-Stage.
REGION_ANCHORS = [
    (28, 168, 1.7),    # the Fold: a CONTAINED drowned sanctuary, deep SW
    (50, 78, 1.15),    # the Kelp Shelf: the drowned north-west climb
    (116, 120, 1.25),  # the Breach: the crossing band, centre-west
    (225, 128, 0.5),   # the Scar: the HUGE open surface (up, down, and right)
    (322, 40, 1.5),    # the Stage: a contained far point in the NE
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


# Mir wakes deep in the Fold (SW); the town obelisk sits three tiles north.
SPAWN: tuple[int, int] = (26, 172)
TOWN_OBELISK: tuple[int, int] = (SPAWN[0], SPAWN[1] - 3)

# --- the campaign tour: ~20 fight nodes winding through the whole world ------
# Authored waypoints in visiting ORDER (the road is carved through them in
# sequence). The tour climbs out of the Fold's mouth, up the Shelf, across the
# Breach, then a long sweep back and forth through the huge Scar, and finally
# north-east to the Stage where the Conductor waits. Each node's biome (and so
# its foe/track) is read from the region it lands in. No fight lands in the
# Fold (region 0) -- combat begins only once Mir leaves the sanctuary.
_TOUR: list[tuple[int, int]] = [
    (46, 120), (54, 92), (44, 64), (66, 52), (88, 70),     # opening_1, mid_1, up the Shelf
    (104, 98), (122, 128), (98, 150),                       # into the Breach band + south
    (142, 170), (184, 180), (218, 158), (190, 120),         # south Scar sweep
    (156, 98), (210, 86), (252, 110), (286, 152),           # mid/east Scar
    (318, 128), (300, 84), (264, 58),                       # climbing toward the Stage
    (308, 41),                                              # boss_1: the Conductor's Stage
]
# Regular-fight foe per region (the Conductor is reserved for the boss node).
_BIOME_FOE = ["slime", "drifter", "drifter", "elite_wraith", "elite_wraith"]
_BIOME_TRACK = ["opening_biome_01", "mid_biome_1_01", "pit_below_01", "mid_biome_3_syncopated_01", "boss_conductor_p1"]


def _node_id(i: int, n: int) -> str:
    # Keep the ids the engine/tests/e2e reference (opening_1, mid_1, boss_1).
    if i == 0:
        return "opening_1"
    if i == 1:
        return "mid_1"
    if i == n - 1:
        return "boss_1"
    return f"node_{i + 1:02d}"


def _build_nodes() -> tuple[dict[str, tuple[int, int]], list[dict]]:
    n = len(_TOUR)
    ids = [_node_id(i, n) for i in range(n)]
    markers: dict[str, tuple[int, int]] = {}
    meta: list[dict] = []
    for i, (c, r) in enumerate(_TOUR):
        ri = region_of(c, r)
        last = i == n - 1
        ntype = "boss" if last else ("elite" if (i + 1) % 4 == 0 else "battle")
        markers[ids[i]] = (c, r)
        # opening_1 is the gentle intro: a slime, whatever biome it lands in.
        foe = "the_conductor" if last else ("slime" if i == 0 else _BIOME_FOE[ri])
        pool_biome = "shallows" if i == 0 else REGIONS[ri]
        meta.append({
            "id": ids[i], "type": ntype, "region": ri, "biome": REGIONS[ri],
            "foe": foe, "pool_biome": pool_biome,
            "next": [] if last else [ids[i + 1]],
        })
    # No fight in the Fold (region 0): it's the sanctuary. Fail loudly so a bad
    # tour edit is caught here, not shipped.
    inside = [m["id"] for m in meta if m["region"] == 0]
    if inside:
        raise SystemExit(f"Tour bug: fight node(s) inside the Fold sanctuary: {inside}")
    return markers, meta


NODE_MARKERS, NODE_META = _build_nodes()

# --- echoes: ~40 lore fragments strewn through the world (8 per biome) -------
# A curated pool per biome; each is hand-placed off the road within its region.
_ECHO_POOL: dict[str, list[tuple[str, str]]] = {
    "shallows": [
        ("The First Prayer", "We didn't raise the obelisk. We woke on the floor and it was already listening."),
        ("The Unlit Lamp", "Nobody leaves the Fold. It isn't a rule. It's just that nobody ever has."),
        ("The Baker's Ledger", "Everyone's boat but mine -- I'll follow once the last one's free."),
        ("The Empty Cradle", "She untied every line but her own."),
        ("The Drowned Bell", "It still rings on the tide. Nobody is left to pull the rope."),
        ("The Last Harvest", "The water came with the first verse, gently. Most of us didn't run."),
        ("Salt for the Doorways", "We marked the lintels so the sea would pass us over. It read the marks as an invitation."),
        ("The Floor That Hums", "Press your ear to the silt. That is the sound we were born owing."),
    ],
    "saltmines": [
        ("The Climber's Knot", "Rope enough to reach the light -- if you don't weigh anything anymore."),
        ("The First Wreck", "Every ship that ever sank points the same way. Up."),
        ("The Foreman's Ledger", "Everyone's shift but mine ends at the sound. I keep counting anyway."),
        ("Listening Stones", "If you stack them right, they listen back."),
        ("The Mast Forest", "Dead ships stand like trees down here. We climb them to feel tall."),
        ("Pillar of Salt", "When you're turning to salt, it's when you're staring ahead too long."),
        ("Three Steps From the Lift", "The foreman covered his ears and ran. He calcified mid-stride, facing away."),
        ("The Cold Cargo", "Whatever the hold was carrying, it is still carrying it, and still cold."),
    ],
    "pit": [
        ("The Broken Foam", "The line between worlds is thinner than a footstep. His fit inside mine."),
        ("Salt in the Lungs", "The first breath burns. The second one is his name."),
        ("Two Ticket Stubs", "Front row, both of us. He said don't blink."),
        ("The Fortune Wheel", "It never lands anywhere else now. I've checked."),
        ("The Waterline", "Cross here and the sky remembers you have a face. It does not approve."),
        ("The Champion's Last Bout", "Something came up through the ring floor. The ropes snapped outward when it left with him."),
        ("The Tipped Chairs", "In the end no one could watch. The crowd is still down there, in a sense."),
        ("The Ferryman's Coin", "He'll take you across for what you love most. Everyone finds they can pay."),
    ],
    "attic": [
        ("The Small Prints", "They walk IN. Toward the den. Why would he walk toward it?"),
        ("What the Claws Keep", "It doesn't eat what it takes. It collects."),
        ("The Boarded Window", "Nailed from the inside. Whatever they feared, they feared it more than the dark."),
        ("Pens for a Bed", "Someone locked themselves in to transcribe the sound before it finished transcribing them."),
        ("The Den's Mouth", "The tracks all lead one way and none lead back. That is the only welcome it offers."),
        ("Scorch and Claw", "The surface does not want you. It has left instructions, in gouges."),
        ("The Collector's Shelf", "Little things, arranged by size. A shoe. A comb. A tooth too small to be yours."),
        ("Tracks That Walk In", "Learn his gait or lose him: paired stride, a heel dot, the faint right-foot drag."),
    ],
    "hall": [
        ("The Rehearsal", "The music stops every time the small one cries. Then it starts again, angrier."),
        ("The Huntress's Mark", "She doesn't hunt to kill. She hunts to keep."),
        ("The Blank Pages", "He erases every attempt except the last row's -- the only players who ever got it right."),
        ("Melting Clocks", "Each stopped at the moment a player gave up. He keeps re-conducting those moments."),
        ("The Cage of Small Bones", "It is exactly the size of a boy who stopped growing when the water came."),
        ("The Ending He Rehearses", "He's been trying to describe a sound again. When he finds it, it ends."),
        ("The Last Row", "Play it right and he will never, ever let you leave."),
        ("What the Baton Remembers", "Every downbeat since the world drowned. It has not missed one. Neither can you."),
    ],
}


def _build_echoes() -> list[tuple[str, str, str, int, tuple[int, int]]]:
    region_tiles: dict[int, list[tuple[int, int]]] = {i: [] for i in range(len(REGIONS))}
    for r in range(4, MAP_H - 4):
        for c in range(4, MAP_W - 4):
            region_tiles[REGION_MAP[r][c]].append((c, r))
    er = random.Random(20260722)
    out: list[tuple[str, str, str, int, tuple[int, int]]] = []
    for ri, name in enumerate(REGIONS):
        pool = _ECHO_POOL[name]
        tiles = region_tiles[ri]
        picks: list[tuple[int, int]] = []
        for _ in range(len(pool)):
            best = None
            for _try in range(60):
                cand = tiles[er.randrange(len(tiles))]
                if all((cand[0] - p[0]) ** 2 + (cand[1] - p[1]) ** 2 > 144 for p in picks):
                    best = cand
                    break
            picks.append(best or tiles[er.randrange(len(tiles))])
        for (title, text), pos in zip(pool, picks):
            out.append((title, text, name, ri, pos))
    return out


ECHOES = _build_echoes()


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

    # the Fold: open silt seafloor with rock knots. NO water pools -- the Fold
    # is UNDERWATER (v14.1); a discrete puddle on the ocean floor reads wrong,
    # so the drowned regions carry rock and silt, never standing water. The
    # town stays clear near the spawn.
    for c, r in spots(0, 34):
        if (c - SPAWN[0]) ** 2 + (r - SPAWN[1]) ** 2 > 64:
            blob(c, r, 2, 2, ROCK, 0)
    # the Kelp Shelf: worked terrace ridges climbing the drowned slope (also
    # underwater -- rock terraces only, no pools).
    for c, r in spots(1, 72):
        blob(c, r, rng.randrange(3, 8), rng.choice((1, 2)), ROCK, 1)
    # the Breach: tide pools along the crossing
    for c, r in spots(2, 34):
        blob(c, r, rng.randrange(2, 5), rng.randrange(2, 4), WATER, 2)
    # the Scar: outcrop knots + dark pits, sprawling every direction
    for c, r in spots(3, 150):
        blob(c, r, rng.randrange(2, 5), rng.randrange(2, 4), ROCK, 3)
    for c, r in spots(3, 34):
        blob(c, r, rng.randrange(3, 7), rng.randrange(2, 5), WATER, 3)
    # the Stage: the boss lake (its island is carved after) + broken colonnade
    bc, br = NODE_MARKERS["boss_1"]
    for r in range(br - 9, br + 10):
        for c in range(bc - 11, bc + 12):
            if 2 <= c < MAP_W - 2 and 2 <= r < MAP_H - 2 and (c - bc) ** 2 + ((r - br) * 1.3) ** 2 <= 100 and REGION_MAP[r][c] == 4:
                grid[r][c] = tid(4, WATER)
    for c, r in spots(4, 34):
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
    for t100 in range(0, 201):
        t = t100 / 200.0
        cc = int(150 + t * 40 + 10.0 * __import__("math").sin(t * 6.0))
        rr = int(40 + t * 140)
        for side in (-7, 7):
            wc = cc + side
            if t100 % 23 < 4:  # gap windows through the walls
                continue
            if 2 <= wc < MAP_W - 2 and 2 <= rr < MAP_H - 2 and REGION_MAP[rr][wc] == 3:
                grid[rr][wc] = tid(3, ROCK)
                for dd in (1, 2):
                    ec = wc + (dd if side > 0 else -dd)
                    if 2 <= ec < MAP_W - 2:
                        grid[rr][ec] = tid(3, ROCK)
    # The CRATER: a broken rock ring with a dark pit at its heart (east Scar)
    crc, crr = 268, 96
    for r in range(crr - 24, crr + 25):
        for c in range(crc - 24, crc + 25):
            if not (2 <= c < MAP_W - 2 and 2 <= r < MAP_H - 2) or REGION_MAP[r][c] != 3:
                continue
            d2 = (c - crc) ** 2 + (r - crr) ** 2
            if 260 <= d2 <= 430 and (c + r * 3) % 9 != 0:  # ring, with breaches
                grid[r][c] = tid(3, ROCK)
            elif d2 <= 42:
                grid[r][c] = tid(3, WATER)  # the pit

    # THE RIVER (v13.2): a winding channel spilling out of the drowned west,
    # snaking across the Scar to the Stage lake -- a real water feature with
    # FORDS (stone crossings) so it divides the surface into banks without
    # sealing anything. Two tiles wide, banked by reeds-turned-rock.
    import math as _m
    river_pts = []
    for t100 in range(0, 301):
        t = t100 / 300.0
        rc = int(95 + t * 200)
        rr = int(78 + 56 * _m.sin(t * 5.5) + t * 20)
        river_pts.append((rc, rr))
    for i, (rc, rr) in enumerate(river_pts):
        ford = (i % 34) < 4  # a stone ford every ~34 steps
        for dw in (-1, 0, 1):
            wr = rr + dw
            if not (2 <= rc < MAP_W - 2 and 2 <= wr < MAP_H - 2):
                continue
            reg = REGION_MAP[wr][rc]
            grid[wr][rc] = tid(reg, PATH if ford else WATER)

    # A SANDBAR REEF field in the Breach shallows: scattered single rocks in
    # the crossing water -- an archipelago read, not a solid mass
    for _i in range(90):
        rc = 92 + (_i * 37) % 40
        rr = 62 + (_i * 53) % 90
        if 2 <= rc < MAP_W - 2 and 2 <= rr < MAP_H - 2 and REGION_MAP[rr][rc] == 2:
            grid[rr][rc] = tid(2, ROCK if _i % 2 else WATER)

    # scattered texture obstacles, placed before carving so the road always wins.
    # In the drowned regions (Fold/Shelf) a scattered water tile is a puddle on
    # the seafloor -- illogical underwater (v14.1), so those get rock only.
    for _ in range(1500):
        c, r = rng.randrange(2, MAP_W - 2), rng.randrange(2, MAP_H - 2)
        underwater = REGION_MAP[r][c] in (0, 1)
        local = ROCK if (underwater or rng.random() < 0.6) else WATER
        grid[r][c] = tid(REGION_MAP[r][c], local)

    # secret spurs: each echo is reachable only by branching off the main
    # road at its region's node marker, then walking an L-bend corridor away
    # from it into a hidden pocket (PRD §8.8.3). Carved BEFORE the main road
    # (below) so the road always has final say if a pocket's ring happens to
    # cross its route -- the road must never be the thing that gets sealed.
    node_pts = list(NODE_MARKERS.values())
    for _title, _text, _region, ri, anchor in ECHOES:
        # branch each echo's hidden spur off the NEAREST fight node (all nodes
        # sit on the carved road), so the pocket is always reachable.
        jump_off = min(node_pts, key=lambda p: (p[0] - anchor[0]) ** 2 + (p[1] - anchor[1]) ** 2)
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

    marker_objects = [
        point_object(1, "spawn", *SPAWN, []),
        # The Fold's town obelisk (v14.0): not a campaign node -- OverworldScene
        # filters it out of the fight markers (like "spawn") and reads it to
        # place the massive monolith + its worshippers at the plaza heart.
        point_object(90, "town_obelisk", *TOWN_OBELISK, []),
    ]
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


# --- content emission: campaign graph + encounter pools (v15.0) -------------
# Co-generated with the map so node ids, biomes, foes and pools never drift.
# Reuses the 4 shipped enemies + the 4 combat beatmaps; encounters vary by
# wave composition and rewards so the ~20-fight tour never feels copy-pasted.
CONTENT_DIR = REPO_ROOT / "src" / "data" / "content"

# (suffix, enemyWave, trackId, xp, currency, relicChoices)
_BIOME_ENCOUNTERS: dict[str, list[tuple]] = {
    "shallows": [
        ("slime_a", ["slime"], "opening_biome_01", 40, 20, []),
        ("slime_b", ["slime", "slime"], "opening_biome_01", 55, 25, ["focus_loop"]),
    ],
    "saltmines": [
        ("drifter_a", ["drifter"], "mid_biome_1_01", 80, 35, []),
        ("drifter_b", ["drifter", "drifter"], "mid_biome_1_01", 100, 45, ["counter_charm"]),
        ("drifter_c", ["drifter", "slime"], "mid_biome_1_01", 90, 40, []),
    ],
    # pit uses the DRIFTER beatmap (mid_biome_1_01), heavier packs than saltmines.
    "pit": [
        ("pack_a", ["drifter", "drifter"], "mid_biome_1_01", 120, 55, ["counter_charm"]),
        ("pack_b", ["drifter", "drifter", "slime"], "mid_biome_1_01", 135, 60, []),
        ("pack_c", ["drifter", "slime", "slime"], "mid_biome_1_01", 125, 55, ["focus_loop"]),
    ],
    # attic uses BOTH wraith beatmaps (mid_biome_3_syncopated_01 + pit_below_01)
    # for track variety; every wave includes a wraith so its telegraphs are met.
    "attic": [
        ("wraith_a", ["elite_wraith"], "mid_biome_3_syncopated_01", 160, 80, ["groove_amp"]),
        ("wraith_b", ["elite_wraith", "drifter"], "mid_biome_3_syncopated_01", 190, 95, ["focus_loop"]),
        ("wraith_c", ["elite_wraith", "elite_wraith"], "pit_below_01", 220, 110, ["groove_amp"]),
        ("wraith_d", ["elite_wraith", "drifter", "drifter"], "pit_below_01", 205, 100, ["counter_charm"]),
    ],
    "hall": [
        ("wraith_hall_a", ["elite_wraith", "elite_wraith"], "mid_biome_3_syncopated_01", 240, 120, ["groove_amp"]),
    ],
}


def _encounter_id(biome: str, suffix: str) -> str:
    return f"biome_{biome}_{suffix}"


def emit_content() -> None:
    enc_dir = CONTENT_DIR / "encounters"
    enc_dir.mkdir(parents=True, exist_ok=True)
    # write one encounter file per (biome, variant)
    written = 0
    for biome, variants in _BIOME_ENCOUNTERS.items():
        for suffix, wave, track, xp, currency, relics in variants:
            eid = _encounter_id(biome, suffix)
            rewards: dict = {"xp": xp, "currency": currency}
            if relics:
                rewards["relicChoices"] = relics
            (enc_dir / f"{eid}.json").write_text(json.dumps({
                "encounterId": eid,
                "trackId": track,
                "enemyWave": wave,
                "accentProfile": None,
                "victoryRewards": rewards,
            }, indent=2) + "\n")
            written += 1
    # campaign graph: each node draws from its biome's pool; boss is fixed.
    nodes = []
    for m in NODE_META:
        if m["type"] == "boss":
            nodes.append({"nodeId": m["id"], "type": "boss", "encounterId": "boss_conductor_01", "next": m["next"]})
        else:
            pool = [_encounter_id(m["pool_biome"], s[0]) for s in _BIOME_ENCOUNTERS[m["pool_biome"]]]
            nodes.append({"nodeId": m["id"], "type": m["type"], "encounterPool": pool, "next": m["next"]})
    campaign = {"startNodeId": NODE_META[0]["id"], "nodes": nodes}
    (CONTENT_DIR / "campaign" / "opening_biome.json").write_text(json.dumps(campaign, indent=2) + "\n")
    print(f"Wrote campaign ({len(nodes)} nodes) + {written} biome encounters")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid = build_grid()
    validate(grid)
    (OUT_DIR / "overworld.json").write_text(json.dumps(build_map_json(grid), indent=2) + "\n")
    print(f"Wrote {OUT_DIR / 'overworld.json'} ({MAP_W}x{MAP_H}, {len(REGIONS)} regions, {len(ECHOES)} echoes)")
    emit_content()


if __name__ == "__main__":
    main()
