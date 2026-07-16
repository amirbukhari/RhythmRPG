"""Paint the overworld ground as ONE plate (design-audit-2 G1-G4).

The world mixed two registers: painterly AI sprites over a hand-stamped 16px
tile carpet -- repeated rock blobs ("chunky blocks"), copy-paste road strips,
panel-edged water, wallpaper grass. This tool retires tile STAMPING: it reads
the authored tile DATA (which stays authoritative for collision/terrain) and
paints the whole ground at 32px-per-tile density as coherent masses:

  * rock clusters -> single mesa landforms: organic silhouette, lit cracked
    top, striated south cliff face, cast shadow (the HLD cliff read);
  * roads -> one continuous worn ribbon: distance-field edges, centerline
    wear, hash-scattered stones -- zero repetition;
  * water -> unified bodies: shore-distance depth ramp to near-black,
    jittered organic shorelines with foam + dark bank, sparse swells;
  * grass -> a multi-scale value-noise field with region-blended bases
    (bakes the seam cross-fade) and hash-placed individual motifs.

Deterministic (fixed seed). Regenerate:  python3 tools/overworld/paint_ground.py
Output: assets/tilemaps/ground_plate.png (map_w*32 x map_h*32), drawn by
OverworldScene at 0.5 scale in place of the (now hidden) tile layer render.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "assets" / "tilemaps" / "overworld.json"
OUT = ROOT / "assets" / "tilemaps" / "ground_plate.png"

S = 32  # px per tile cell (2x the runtime 16px -> denser texels, HLD register)
RNG = np.random.default_rng(20260714)

# HLD-grade accents: one hot signature hue per region, chroma pushed so the
# blend passes read as COLOUR, not grey (goal: the HLD comparison)
ACCENTS = [(0x49, 0xC6, 0xBD), (0xF0, 0xA6, 0x48), (0x9A, 0x5C, 0xBD), (0xC2, 0x54, 0x24), (0x7A, 0x4E, 0xB4)]


def tint(base: tuple[int, int, int], accent: tuple[int, int, int], amt: float) -> np.ndarray:
    return np.array([b + (a - b) * amt for b, a in zip(base, accent)], dtype=np.float32)


def value_noise(h: int, w: int, cell: int) -> np.ndarray:
    """Smooth [0,1] noise: white noise at coarse res, bilinear upsample."""
    gh, gw = max(2, h // cell + 2), max(2, w // cell + 2)
    coarse = RNG.random((gh, gw), dtype=np.float32)
    img = Image.fromarray((coarse * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255.0


def organic_mask(tile_mask: np.ndarray, jitter: float = 0.22, blur: int = 9, warp: float = 0.0) -> np.ndarray:
    """Upscale a tile-res boolean mask to pixels with soft, noise-jittered,
    rounded edges -- the anti-'razor grid edge' operator. `warp` adds a
    COARSE low-frequency term that swings the whole boundary in and out by
    several pixels (scale/placement audit: fine jitter alone left big
    map-rectangular ponds reading as rounded rectangles)."""
    h, w = tile_mask.shape
    img = Image.fromarray((tile_mask * 255).astype(np.uint8)).resize((w * S, h * S), Image.NEAREST)
    img = img.filter(ImageFilter.BoxBlur(blur))
    field = np.asarray(img, dtype=np.float32) / 255.0
    n = value_noise(h * S, w * S, 14)
    field = field + (n - 0.5) * jitter
    if warp > 0:
        field = field + (value_noise(h * S, w * S, 30) - 0.5) * warp
    return field > 0.5


def erode(mask: np.ndarray, steps: int) -> list[np.ndarray]:
    """mask, eroded once, eroded twice ... (4-neighbour), for distance bands."""
    out = [mask]
    m = mask
    for _ in range(steps):
        m = m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
        out.append(m)
    return out


def distance_bands(mask: np.ndarray, steps: int, cell: int = 4) -> np.ndarray:
    """Approximate interior distance (in px) via erosion at reduced res."""
    h, w = mask.shape
    small = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize((w // cell, h // cell), Image.NEAREST)) > 127
    dist = np.zeros_like(small, dtype=np.float32)
    for i, m in enumerate(erode(small, steps)):
        dist[m] = (i + 1) * cell
    img = Image.fromarray((dist / dist.max().clip(1) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255.0 * dist.max()


def main() -> None:
    data = json.loads(MAP.read_text())
    W, H = data["width"], data["height"]
    gids = np.array([l for l in data["layers"] if l.get("name") == "ground"][0]["data"], dtype=np.int32).reshape(H, W)
    kind = (gids - 1) % 4  # 0 grass 1 path 2 water 3 rock
    region = np.clip((gids - 1) // 4, 0, 4)

    PW, PH = W * S, H * S
    # --- region weight blend (bakes the seam cross-fade) -------------------
    region_px = np.asarray(Image.fromarray(region.astype(np.uint8)).resize((PW, PH), Image.NEAREST))
    weights = []
    for r in range(5):
        m = Image.fromarray(((region_px == r) * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(48))
        weights.append(np.asarray(m, dtype=np.float32) / 255.0)
    wsum = np.stack(weights).sum(0).clip(1e-3)

    def blended(bases: list[np.ndarray]) -> np.ndarray:
        acc = np.zeros((PH, PW, 3), dtype=np.float32)
        for r in range(5):
            acc += weights[r][..., None] * bases[r][None, None, :]
        return acc / wsum[..., None]

    # --- grass field --------------------------------------------------------
    grass_bases = [tint((0x2C, 0x40, 0x26), a, 0.36) for a in ACCENTS]
    img = blended(grass_bases)
    n_low = value_noise(PH, PW, 160)
    n_mid = value_noise(PH, PW, 36)
    n_hi = value_noise(PH, PW, 7)
    img *= (1 + (n_low - 0.5) * 0.30 + (n_mid - 0.5) * 0.18 + (n_hi - 0.5) * 0.10)[..., None]
    img[n_low < 0.36] *= 0.86  # pooled dark patches
    grain = RNG.random((PH, PW), dtype=np.float32)
    img *= (1 + (grain - 0.5) * 0.12)[..., None]  # per-pixel grain (HLD crunch)

    canvas = img  # float32 HxWx3

    def stamp_tufts() -> None:
        """Individually hash-placed grass marks -- variation, not wallpaper."""
        ys, xs = np.where(kind == 0)
        for ty, tx in zip(ys, xs):
            h = (tx * 73856093 ^ ty * 19349663) & 0xFFFFFFFF
            if h % 100 >= 55:
                continue
            cx, cy = tx * S + (h >> 8) % S, ty * S + (h >> 16) % S
            dark = canvas[cy % PH, cx % PW] * 0.72
            lite = canvas[cy % PH, cx % PW] * 1.35
            for k in range((h >> 4) % 3 + 1):
                px = (cx + ((h >> (k * 5)) % 9) - 4) % PW
                py = (cy + ((h >> (k * 3)) % 5) - 2) % PH
                ln = 3 + (h >> k) % 4
                for d in range(ln):
                    yy = (py - d) % PH
                    canvas[yy, px] = dark if d < ln - 1 else lite
            if h % 977 == 0:  # rare accent fleck
                canvas[cy % PH, cx % PW] = np.array(ACCENTS[region[ty, tx]], dtype=np.float32) * 0.8

    stamp_tufts()

    # --- region micro-motifs (v11.3 ground-variation pass) -------------------
    # Each biome stamps its own faint marks into the turf so the five regions
    # read as five PLACES even with zero set dressing (the purge: the ground
    # is the game). All marks are subtle mixes, never full overwrites.
    grass_px = np.asarray(Image.fromarray(((kind == 0) * 255).astype(np.uint8)).resize((PW, PH), Image.NEAREST)) > 127

    def mix(mask: np.ndarray, colour: tuple[int, int, int], amt: float) -> None:
        c = np.array(colour, dtype=np.float32)
        canvas[mask] = canvas[mask] * (1 - amt) + c[None, :] * amt

    # r0 shallows: tide lines -- long wavy pale horizontals left by the water
    r_mask = grass_px & (region_px == 0)
    tide_wave = (value_noise(PH, PW, 90) - 0.5) * 26
    tide_rows = (np.abs(((yy_r := np.arange(PH, dtype=np.float32)[:, None]) + tide_wave) % 96) < 1.2)
    mix(r_mask & tide_rows & (value_noise(PH, PW, 40) > 0.35), (0xB9, 0xC8, 0xBB), 0.28)

    # r1 saltmines: crusted salt veins -- bright random-walk crackle
    r_mask = grass_px & (region_px == 1)
    ys_v, xs_v = np.where(r_mask[::64, ::64])
    for vy, vx in zip(ys_v * 64, xs_v * 64):
        h = (int(vx) * 73856093 ^ int(vy) * 83492791) & 0xFFFFFFFF
        if h % 100 >= 22:
            continue
        y, x = int(vy), int(vx)
        for _ in range(18 + h % 30):
            if 0 <= y < PH and 0 <= x < PW and r_mask[y, x]:
                canvas[y, x] = canvas[y, x] * 0.4 + np.array((0xD9, 0xE2, 0xDE), dtype=np.float32) * 0.6
            y += int(RNG.integers(-1, 2))
            x += int(RNG.integers(-1, 2))

    # r2 pit: ash smudges + fallen carnival confetti flecks
    r_mask = grass_px & (region_px == 2)
    canvas[r_mask & (value_noise(PH, PW, 30) > 0.68)] *= 0.86  # ash
    fleck_h = (np.arange(PH)[:, None] * 19349663 + np.arange(PW)[None, :] * 73856093) & 0xFFFF
    festival = [(0x9A, 0x5C, 0xBD), (0xC9, 0x9A, 0x3F), (0x49, 0xC6, 0xBD)]
    for i, fc in enumerate(festival):
        mix(r_mask & (fleck_h == 77 + i * 331), fc, 0.75)

    # r3 attic: ghostly floorboard seams showing through the turf
    r_mask = grass_px & (region_px == 3)
    yy_b = np.arange(PH)[:, None].repeat(PW, 1)
    xx_b = np.arange(PW)[None, :].repeat(PH, 0)
    board_row = yy_b // 26
    seam_h = (yy_b % 26) == 0
    joint = ((xx_b + board_row * 67) % 150) < 2
    canvas[r_mask & seam_h] *= 0.8
    canvas[r_mask & joint & ((yy_b % 26) < 24)] *= 0.9
    canvas[r_mask & (board_row % 2 == 0) & ~seam_h] *= 0.97  # alternating board tone

    # r4 hall: faint marble veining -- pale contour filaments
    r_mask = grass_px & (region_px == 4)
    vein_n = value_noise(PH, PW, 55)
    mix(r_mask & (np.abs(vein_n - 0.5) < 0.006), (0xC9, 0xC4, 0xD4), 0.30)

    # --- path hierarchy: the main road vs desire-path spurs ------------------
    # BFS the road graph from spawn to the boss: that corridor (+1 tile of
    # slack) is the MAIN road; every other path tile is a side spur, painted
    # as a narrower, broken desire path. The route also gives Nari's trail
    # its direction (stamped after the fight grounds below).
    markers = [l for l in data["layers"] if l.get("name") == "markers"][0]["objects"]

    def nearest_path_tile(px_x: float, px_y: float) -> tuple[int, int] | None:
        t0 = (int(px_y // 16), int(px_x // 16))
        best, bd = None, 1e9
        ys_p, xs_p = np.where(kind == 1)
        for py, px in zip(ys_p, xs_p):
            d = (py - t0[0]) ** 2 + (px - t0[1]) ** 2
            if d < bd:
                best, bd = (int(py), int(px)), d
        return best

    spawn_obj = next(o for o in markers if o["name"] == "spawn")
    boss_obj = next((o for o in markers if o["name"] == "boss_1"), None)
    route: list[tuple[int, int]] = []
    if boss_obj is not None:
        start = nearest_path_tile(spawn_obj["x"], spawn_obj["y"])
        goal = nearest_path_tile(boss_obj["x"], boss_obj["y"])
        if start and goal:
            from collections import deque
            parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
            q = deque([start])
            while q:
                cur = q.popleft()
                if cur == goal:
                    break
                cy_t, cx_t = cur
                for ny, nx in ((cy_t + 1, cx_t), (cy_t - 1, cx_t), (cy_t, cx_t + 1), (cy_t, cx_t - 1)):
                    if 0 <= ny < H and 0 <= nx < W and kind[ny, nx] == 1 and (ny, nx) not in parent:
                        parent[(ny, nx)] = cur
                        q.append((ny, nx))
            if goal in parent:
                cur2: tuple[int, int] | None = goal
                while cur2 is not None:
                    route.append(cur2)
                    cur2 = parent[cur2]
                route.reverse()

    main_tiles = np.zeros_like(kind, dtype=bool)
    if route:
        for ty, tx in route:
            main_tiles[max(0, ty - 1) : ty + 2, max(0, tx - 1) : tx + 2] |= kind[max(0, ty - 1) : ty + 2, max(0, tx - 1) : tx + 2] == 1
    else:
        main_tiles = kind == 1  # fallback: no route found, everything is main
    spur_tiles = (kind == 1) & ~main_tiles

    # --- path ribbon ---------------------------------------------------------
    # blur 7 -> 11: the meandering road's single-tile jogs painted as hard
    # stair-steps; the wider falloff melts each corner into a curve while a
    # 1-tile spur (32px wide) still holds together comfortably
    path_mask = organic_mask(main_tiles, jitter=0.18, blur=11)
    d_path = distance_bands(path_mask, 6)
    path_bases = [tint((0x8E, 0x83, 0x68), a, 0.18) for a in ACCENTS]
    path_col = blended(path_bases) * (1 + (n_mid - 0.5) * 0.12)[..., None]
    edge = path_mask & (d_path < 3)
    wear = path_mask & (d_path > 7)
    canvas[path_mask] = path_col[path_mask]
    canvas[edge] *= 0.68
    canvas[wear] *= 1.10
    # hash-scattered stones (individual, lit top-left)
    ys, xs = np.where(kind == 1)
    for ty, tx in zip(ys, xs):
        h = (tx * 2654435761 ^ ty * 40503) & 0xFFFFFFFF
        if h % 100 >= 26:
            continue
        cx, cy = tx * S + (h >> 7) % (S - 8) + 4, ty * S + (h >> 13) % (S - 8) + 4
        rx, ry = 2 + (h >> 3) % 3, 2 + (h >> 9) % 2
        yy, xx = np.ogrid[-ry : ry + 1, -rx : rx + 1]
        blob = (xx / rx) ** 2 + (yy / ry) ** 2 <= 1
        sl = canvas[cy - ry : cy + ry + 1, cx - rx : cx + rx + 1]
        if sl.shape[:2] != blob.shape:
            continue
        base = path_col[cy, cx] * 1.12
        sl[blob] = base
        sl[: ry + 1][blob[: ry + 1]] = base * 1.18  # top-light
        sl[-1:][blob[-1:]] = base * 0.62  # base shadow

    # --- desire-path spurs ----------------------------------------------------
    # Side trails are half-swallowed by the turf: narrower, paler, and BROKEN
    # into worn patches -- you learn to read them, they never compete with the
    # main road. (Secret-pocket approaches stay findable but subtle.)
    spur_px = np.zeros((PH, PW), dtype=bool)
    if spur_tiles.any():
        spur_band = organic_mask(spur_tiles, jitter=0.26, blur=7)
        spur_px = spur_band & (value_noise(PH, PW, 12) > 0.34) & ~path_mask
        worn = canvas[spur_px] * 0.35 + path_col[spur_px] * 0.65
        canvas[spur_px] = canvas[spur_px] * 0.45 + worn * 0.55

    # --- water bodies --------------------------------------------------------
    # jitter raised 0.2 -> 0.34 (scale/placement audit: map-rectangular ponds
    # kept reading as rounded RECTANGLES through the gentler wobble)
    water_mask = organic_mask(kind == 2, jitter=0.3, blur=13, warp=0.6)
    d_w = distance_bands(water_mask, 12)
    shore_bases = [tint((0x17, 0x42, 0x58), a, 0.20) for a in ACCENTS]
    deep = np.array((0x08, 0x0D, 0x24), dtype=np.float32)
    t = np.clip(d_w / 26.0, 0, 1)[..., None]
    water_col = blended(shore_bases) * (1 - t) + deep[None, None, :] * t
    water_col *= (1 + (n_mid - 0.5) * 0.08)[..., None]
    canvas[water_mask] = water_col[water_mask]
    # sparse swell strokes (hashed, never a repeating row pattern)
    ys, xs = np.where(kind == 2)
    for ty, tx in zip(ys, xs):
        h = (tx * 83492791 ^ ty * 297121507) & 0xFFFFFFFF
        if h % 100 >= 7:
            continue
        cy, cx = ty * S + (h >> 6) % S, tx * S + (h >> 12) % S
        ln = 6 + (h >> 4) % 14
        yy = cy % PH
        seg = slice(cx % PW, min(PW, cx % PW + ln))
        row = canvas[yy, seg]
        m = water_mask[yy, seg]
        row[m] = row[m] * 1.25
        if h % 13 == 0:
            canvas[yy, seg][m] = np.minimum(row[m] * 1.5, 255)
    # shoreline: foam on the water side, dark bank on the land side
    dil = ~(erode(~water_mask, 2)[2])
    foam_ring = water_mask & ~erode(water_mask, 2)[2]
    bank_ring = dil & ~water_mask
    canvas[foam_ring] = canvas[foam_ring] * 0.45 + np.array((0x8F, 0xD8, 0xD0), dtype=np.float32) * 0.55 * 0.7
    canvas[bank_ring] *= 0.55

    # --- drowned shapes under the surface (v11.3) -----------------------------
    # The village went under mid-festival: pale rooftops, chimneys, and a hull
    # ghost beneath the shallows, told entirely through the depth ramp. Shapes
    # sit in mid-depth water, blurred a touch, and fade with depth.
    overlay = np.zeros((PH, PW), dtype=np.float32)
    placed: list[tuple[int, int]] = []
    ys_w, xs_w = np.where(kind == 2)
    for ty, tx in zip(ys_w, xs_w):
        h = (tx * 40503 ^ ty * 2654435761) & 0xFFFFFFFF
        if h % 100 >= 4:
            continue
        cx, cy = tx * S + S // 2, ty * S + S // 2
        reg = region[ty, tx]
        if reg not in (0, 4) and h % 5 != 0:
            continue  # cluster in the shallows + the hall lake
        if d_w[cy, cx] < 7 or any((cx - px) ** 2 + (cy - py) ** 2 < 70**2 for px, py in placed):
            continue
        placed.append((cx, cy))
        kindh = h % 3
        if kindh < 2:  # gabled roof + chimney
            rw, rh = 30 + (h >> 5) % 14, 16 + (h >> 9) % 8
            for dy in range(rh):
                half = int(rw / 2 * (dy / rh))
                overlay[cy - rh // 2 + dy, cx - half : cx + half + 1] = 1.0
            overlay[cy - rh // 2 - 4 : cy - rh // 2, cx + rw // 4 : cx + rw // 4 + 3] = 1.0  # chimney
            overlay[cy - rh // 2 : cy + rh // 2, cx - 1 : cx + 1] *= 1.0  # ridge stays
        else:  # boat hull
            rw, rh = 26 + (h >> 5) % 10, 8
            yy_o, xx_o = np.ogrid[-rh : rh + 1, -rw // 2 : rw // 2 + 1]
            hull = ((xx_o / (rw / 2)) ** 2 + (yy_o / rh) ** 2 <= 1) & (yy_o >= 0)
            sl = overlay[cy : cy + 2 * rh + 1, cx - rw // 2 : cx + rw // 2 + 1]
            if sl.shape == hull.shape:
                sl[hull] = 1.0
    if placed:
        overlay = np.asarray(Image.fromarray((overlay * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(2)), dtype=np.float32) / 255.0
        depth_fade = np.clip(1.0 - d_w / 34.0, 0.45, 1.0)
        a = (overlay * 0.52 * depth_fade)[..., None] * water_mask[..., None]
        ghost = blended(shore_bases) * 1.8
        canvas = canvas * (1 - a) + ghost * a

    # --- causeways (scale/placement audit) -----------------------------------
    # The map routes some paths THROUGH lakes; painted as bare grass-road they
    # read as glowing squiggles floating on water. Where a path runs beside or
    # through water, restate it as a BUILT stone causeway: cooler masonry tone
    # + a hard dark edging where it meets the water.
    # water dilated ~26px: a full road crossing is ~40px wide, so every pixel
    # of a crossing sits within reach (6px only re-toned the crossing's edges,
    # leaving a tan stripe down the middle of the lake)
    near_water = ~(erode(~water_mask, 26)[26])
    causeway = (path_mask | spur_px) & near_water
    if causeway.any():
        stone = np.array((0x4E, 0x50, 0x58), dtype=np.float32)
        canvas[causeway] = canvas[causeway] * 0.35 + stone[None, :] * 0.65 * (
            1 + (n_mid[causeway, None] - 0.5) * 0.18
        )
        cw_dil = ~(erode(~causeway, 2)[2])
        cw_edge = cw_dil & water_mask & ~causeway
        canvas[cw_edge] *= 0.4

    # --- rock mesas (G1: the chunky-block killer) ----------------------------
    rock_tiles = kind == 3
    labels = np.zeros_like(rock_tiles, dtype=np.int32)
    nxt = 0
    for ty in range(H):
        for tx in range(W):
            if rock_tiles[ty, tx] and labels[ty, tx] == 0:
                nxt += 1
                stack = [(ty, tx)]
                while stack:
                    y, x = stack.pop()
                    if 0 <= y < H and 0 <= x < W and rock_tiles[y, x] and labels[y, x] == 0:
                        labels[y, x] = nxt
                        stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]

    rock_top_bases = [tint((0x4A, 0x51, 0x5E), a, 0.30) for a in ACCENTS]
    rock_top = blended(rock_top_bases)
    crack_col = 0.5
    for comp in range(1, nxt + 1):
        cm = organic_mask(labels == comp, jitter=0.34, blur=8)
        if not cm.any():
            continue
        below_out = cm & ~np.roll(cm, -1, 0)  # south rim of the mesa
        # cast shadow on the ground south of the mesa
        sh = np.roll(cm, 7, 0) & ~cm
        canvas[sh] *= 0.66
        # cliff face: a band above the south rim, striated and dark
        face = np.zeros_like(cm)
        acc = below_out.copy()
        for _ in range(13):
            acc = np.roll(acc, -1, 0) & cm
            face |= acc
        top = cm & ~face
        col = rock_top * (1 + (n_mid - 0.5) * 0.16 + (n_hi - 0.5) * 0.14)[..., None]
        col *= (1 + (value_noise(PH, PW, 2) - 0.5) * 0.10)[..., None]
        canvas[top] = col[top]
        stria = (value_noise(PH, PW, 3) > 0.55) & face
        canvas[face] = col[face] * 0.52
        canvas[stria] = col[stria] * 0.35
        # lit north rim + darker west/east flanks
        rim = cm & ~np.roll(cm, 1, 0)
        canvas[rim] = col[rim] * 1.28 + 10
        wflank = cm & ~np.roll(cm, 1, 1)
        eflank = cm & ~np.roll(cm, -1, 1)
        canvas[wflank] *= 1.12
        canvas[eflank] *= 0.7
        # cracks on the top surface: dark random walks
        ys, xs = np.where(top)
        if len(ys) > 200:
            for k in range(min(10, len(ys) // 400 + 2)):
                i = int(RNG.integers(0, len(ys)))
                y, x = int(ys[i]), int(xs[i])
                for _ in range(int(RNG.integers(12, 42))):
                    if 0 <= y < PH and 0 <= x < PW and top[y, x]:
                        canvas[y, x] *= crack_col
                    y += int(RNG.integers(-1, 2))
                    x += int(RNG.integers(-1, 2))
            # SP10: plateau dressing -- big pale tops read bare/flat. Tonal
            # patches (lichen-dark blotches) + hashed pebbles with a lit top
            # edge give the plateau the same material density as the grass.
            patches = (value_noise(PH, PW, 18) > 0.72) & top
            canvas[patches] *= 0.88
            for k in range(max(2, len(ys) // 260)):
                i = int(RNG.integers(0, len(ys)))
                py_, px_ = int(ys[i]), int(xs[i])
                pr = int(RNG.integers(1, 3))
                sl = (slice(max(0, py_ - pr), py_ + pr + 1), slice(max(0, px_ - pr), px_ + pr + 1))
                if top[sl].all():
                    canvas[sl] *= 0.8
                    canvas[sl][0] = np.minimum(canvas[sl][0] * 1.45, 255)  # lit top edge

    # --- fight grounds (venue floors BAKED into the world) -------------------
    # The old runtime venue floor was a translucent 320x180 rect overlaid on
    # the map (owner: "straight up squares... you can see through them").
    # Instead each fight node gets an organic trampled-earth clearing painted
    # INTO the plate: ragged noise edge, packed-earth tone tinted by region,
    # wear rings. WorldFight's always-walkable r=64 circle (128 plate px)
    # stays inside the r~130px disc, so every fight still has a real room --
    # now indistinguishable from the painted world because it IS the world.
    markers = [l for l in data["layers"] if l.get("name") == "markers"][0]["objects"]
    yy_g, xx_g = np.mgrid[0:PH, 0:PW].astype(np.float32)
    disc_noise = value_noise(PH, PW, 22)
    for obj in markers:
        if obj["name"] == "spawn":
            continue
        cx, cy = float(obj["x"]) * 2, float(obj["y"]) * 2
        reg = min(4, int(cx // (26 * S)))
        # the finale gets a GRAND ring -- its venue pieces stand wide and the
        # clearing bridges the hall lake as one deliberate stage
        radius = 230.0 if obj["name"] == "boss_1" else 132.0
        rr = np.sqrt((xx_g - cx) ** 2 + (yy_g - cy) ** 2) + (disc_noise - 0.5) * 56
        disc = rr < radius
        edge = disc & (rr > radius - 16)
        base = tint((0x6E, 0x61, 0x4A), ACCENTS[reg], 0.28)
        col = base[None, None, :] * (1 + (n_mid - 0.5) * 0.14)[..., None]
        canvas[disc] = col[disc]
        canvas[edge] *= 0.62
        rings = disc & (np.abs((rr % 44) - 22.0) < 1.1) & (rr > 26)
        canvas[rings] *= 0.85

    # --- Nari's trail (v11.3): the search, told in the ground -----------------
    # Tiny toddler footprints march along the critical-path route toward the
    # boss -- Mir is tracking his son through ground paint alone. A short run
    # every ~14 route tiles, prints stepping in the route's true direction.
    def stamp_print(py: int, px: int) -> None:
        if 1 <= py < PH - 2 and 1 <= px < PW - 1 and not water_mask[py, px]:
            canvas[py : py + 2, px : px + 2] *= 0.62  # sole
            canvas[py + 2, px] *= 0.7  # heel
    for i in range(3, len(route) - 1, 14):
        ty, tx = route[i]
        ny, nx = route[i + 1]
        dy, dx = ny - ty, nx - tx  # unit tile step = the walk direction
        cx, cy = tx * S + S // 2, ty * S + S // 2
        h = (tx * 19349663 ^ ty * 73856093) & 0xFFFFFFFF
        for step in range(5):
            along = step * 8 - 16
            side = 3 if step % 2 else -3
            px_ = cx + dx * along + (dy * side)  # lateral offset perpendicular
            py_ = cy + dy * along + (dx * side)
            stamp_print(py_ + (h >> step) % 2, px_ + (h >> (step + 3)) % 2)

    # --- value composition (v11.3): the road carries the light ---------------
    # A soft macro pool of light hugs the main road so the critical path sits
    # a half-step brighter than off-path ground -- the eye is guided without
    # a single UI element. Fight clearings are already pale and stay so.
    road_small = np.asarray(Image.fromarray((path_mask * 255).astype(np.uint8)).resize((PW // 8, PH // 8), Image.BILINEAR))
    road_light = np.asarray(Image.fromarray(road_small).filter(ImageFilter.BoxBlur(22)).resize((PW, PH), Image.BILINEAR), dtype=np.float32) / 255.0
    road_light = road_light / max(1e-3, road_light.max())
    canvas *= (0.95 + road_light * 0.11)[..., None]

    # --- the world's dark frame (HLD value structure) -------------------------
    # HLD's playfield GLOWS because its unwalkable surround sits near black.
    # Sink the outer map edge into darkness with an organic falloff so the
    # world reads as a lit place inside a void, not a plate that just stops.
    edge_d = np.minimum.reduce([
        np.arange(PW, dtype=np.float32)[None, :].repeat(PH, 0),
        np.arange(PW, dtype=np.float32)[::-1][None, :].repeat(PH, 0),
        np.arange(PH, dtype=np.float32)[:, None].repeat(PW, 1),
        np.arange(PH, dtype=np.float32)[::-1][:, None].repeat(PW, 1),
    ])
    frame_t = np.clip((64.0 - edge_d - (value_noise(PH, PW, 26) - 0.5) * 40) / 64.0, 0, 1)
    canvas *= (1 - frame_t * 0.72)[..., None]

    # v11.0 beauty pivot: the quantized-ramp + ordered-dither "HLD floor
    # signature" is retired -- the plate ships its painted gradients at full
    # fidelity (smooth renderer, no chunky register to match anymore).
    out = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGB")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({out.width}x{out.height})")


if __name__ == "__main__":
    main()
