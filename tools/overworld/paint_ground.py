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

# v12.0 Ascent accents: the Fold (deep teal), the Kelp Shelf (kelp green),
# the Breach (sand/foam), the Scar (blood rust), the Stage (storm violet)
ACCENTS = [(0x49, 0xC6, 0xBD), (0x58, 0xC0, 0x7A), (0xE8, 0xD9, 0xA8), (0xC2, 0x54, 0x24), (0x7A, 0x4E, 0xB4)]



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

    # v13.0 open world: "under the sea" is the Fold+Shelf TERRITORY, so the
    # waterline is the organic contour of their blurred weight field.
    w01 = (weights[0] + weights[1]) / wsum

    def blended(bases: list[np.ndarray]) -> np.ndarray:
        acc = np.zeros((PH, PW, 3), dtype=np.float32)
        for r in range(5):
            acc += weights[r][..., None] * bases[r][None, None, :]
        return acc / wsum[..., None]

    # --- ground field (v12.0: each region's "grass" is its own material) ----
    # silt streets / kelp turf / wet sand / ashen scrub / stone moor
    GROUND_BASES = [(0x2E, 0x46, 0x44), (0x24, 0x44, 0x2F), (0x86, 0x76, 0x54), (0x40, 0x30, 0x28), (0x3A, 0x34, 0x46)]
    grass_bases = [tint(b, a, 0.22) for b, a in zip(GROUND_BASES, ACCENTS)]
    img = blended(grass_bases)
    n_low = value_noise(PH, PW, 160)
    n_mid = value_noise(PH, PW, 36)
    n_hi = value_noise(PH, PW, 7)
    img *= (1 + (n_low - 0.5) * 0.30 + (n_mid - 0.5) * 0.18 + (n_hi - 0.5) * 0.10)[..., None]
    img[n_low < 0.36] *= 0.86  # pooled dark patches
    grain = RNG.random((PH, PW), dtype=np.float32)
    img *= (1 + (grain - 0.5) * 0.12)[..., None]  # per-pixel grain (HLD crunch)

    canvas = img  # float32 HxWx3
    yy_g, xx_g = np.mgrid[0:PH, 0:PW].astype(np.float32)

    # --- the OCEAN FLOOR (v12.2 -- owner: "where's the ocean floor
    # environment?"). The Fold's ground is not a lawn: it is rippled
    # silt-sand with beds of dark eelgrass -- the material itself says
    # seafloor. Cross-faded by the region weight so the Shelf inherits its
    # fringe naturally.
    w0 = weights[0] / wsum
    sand = tint((0x67, 0x6F, 0x64), ACCENTS[0], 0.18)
    sea = sand[None, None, :] * (1 + (n_low - 0.5) * 0.22 + (n_mid - 0.5) * 0.12 + (n_hi - 0.5) * 0.08)[..., None]
    sea = sea * (1 + (grain - 0.5) * 0.10)[..., None]
    # dune ripples: broad combed sand-waves, warped so they never read ruled
    dune_wob = (value_noise(PH, PW, 90) - 0.5) * 34
    dune = (yy_g + dune_wob) % 22
    sea[dune < 2.2] *= 0.88
    sea[(dune >= 2.2) & (dune < 3.6)] *= 1.08
    # eelgrass beds: coarse patches of dark sea-green growth in the sand
    bed_n = value_noise(PH, PW, 110)
    bed = np.clip((bed_n - 0.55) / 0.12, 0, 1)[..., None]
    grassy = tint((0x1F, 0x3B, 0x30), ACCENTS[0], 0.25)[None, None, :] * (1 + (n_mid - 0.5) * 0.16)[..., None]
    sea = sea * (1 - bed) + grassy * bed
    canvas = canvas * (1 - w0[..., None]) + sea * w0[..., None]

    # --- Scar sub-biomes (v13.1: "not sure our map has enough variation") ----
    # The huge surface splits into three districts by coarse noise: pale ash
    # wastes, the rust flats, and the deep-red thorn barrens -- one region,
    # three moods, no seams (same noise stack, different keys).
    district = value_noise(PH, PW, 260)
    scar_px = region_px == 3
    ashen = scar_px & (district < 0.4)
    thorn = scar_px & (district > 0.66)
    ash_c = np.array((0x54, 0x4C, 0x46), dtype=np.float32)
    thorn_c = np.array((0x4E, 0x24, 0x1C), dtype=np.float32)
    a_m = (np.clip((0.4 - district) / 0.08, 0, 1) * 0.5)[..., None]
    t_m = (np.clip((district - 0.66) / 0.08, 0, 1) * 0.45)[..., None]
    canvas = np.where(ashen[..., None], canvas * (1 - a_m) + ash_c[None, None, :] * a_m, canvas)
    canvas = np.where(thorn[..., None], canvas * (1 - t_m) + thorn_c[None, None, :] * t_m, canvas)

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

    # r0 the Fold: current lines -- the silt combed by the water above
    r_mask = grass_px & (region_px == 0)
    tide_wave = (value_noise(PH, PW, 90) - 0.5) * 26
    tide_rows = (np.abs(((yy_r := np.arange(PH, dtype=np.float32)[:, None]) + tide_wave) % 96) < 1.2)
    mix(r_mask & tide_rows & (value_noise(PH, PW, 40) > 0.35), (0xB9, 0xC8, 0xBB), 0.28)

    # r1 the Kelp Shelf: kelp wisps -- long dark strands swaying up-slope
    r_mask = grass_px & (region_px == 1)
    ys_v, xs_v = np.where(r_mask[::48, ::48])
    kelp_dark = np.array((0x14, 0x30, 0x1E), dtype=np.float32)
    for vy, vx in zip(ys_v * 48, xs_v * 48):
        h = (int(vx) * 73856093 ^ int(vy) * 83492791) & 0xFFFFFFFF
        if h % 100 >= 30:
            continue
        x = int(vx) + (h >> 5) % 40
        ln = 10 + h % 14
        for d in range(ln):
            y = int(vy) - d
            xw = x + int(2.2 * np.sin(d * 0.5 + h % 7))
            if 0 <= y < PH and 0 <= xw < PW and r_mask[y, xw]:
                canvas[y, xw] = canvas[y, xw] * 0.45 + kelp_dark * 0.55
                if d == ln - 1:
                    canvas[y, xw] = canvas[y, xw] * 0.5 + np.array(ACCENTS[1], dtype=np.float32) * 0.5
    # wreck ribs: the skeletons of dead ships stitched up the shelf, every
    # bow pointing UP the climb -- pale bone arcs with a sunken shadow
    bone = np.array((0xC9, 0xC2, 0xA8), dtype=np.float32)
    shelf_open = list(zip(*np.where((region == 1) & (kind == 0))))
    for wi in range(6):
        h = (wi * 83492791 + 331) & 0xFFFFFFFF
        if not shelf_open:
            break
        wr, wc = shelf_open[(h >> 4) % len(shelf_open)]
        wx, wy = wc * S, wr * S
        nrib = 5 + h % 3
        for ri in range(nrib):
            ry = wy + ri * 7
            half = int((14 - abs(ri - nrib / 2) * 3))
            for dx in range(-half, half + 1):
                bow = int((dx * dx) / max(1, half * 2.2))
                y, x = ry - bow, wx + dx
                if 0 <= y < PH - 1 and 0 <= x < PW and grass_px[y, x]:
                    canvas[y, x] = canvas[y, x] * 0.4 + bone[None, :] * 0.6
                    canvas[y + 1, x] *= 0.7

    # r2 the Breach: shell flecks + tidal ripple combing near the waterline
    r_mask = grass_px & (region_px == 2)
    fleck_h = (np.arange(PH)[:, None] * 19349663 + np.arange(PW)[None, :] * 73856093) & 0xFFFF
    for i, fc in enumerate([(0xD8, 0xD0, 0xB4), (0xB9, 0xC8, 0xBB)]):
        mix(r_mask & (fleck_h == 77 + i * 331), fc, 0.7)
    xx_r = np.arange(PW)[None, :].repeat(PH, 0)
    rip_wob = (value_noise(PH, PW, 70) - 0.5) * 22
    near_wl = (w01 > 0.22) & (w01 < 0.62)
    ridges = r_mask & near_wl & (((xx_r + rip_wob).astype(np.int32) % 16) < 2)
    canvas[ridges] *= 0.86
    crests = r_mask & near_wl & (((xx_r + rip_wob).astype(np.int32) % 16) == 2)
    canvas[crests] *= 1.12

    # r3 the Scar: sun-cracked earth -- a dark mud-crack web, plus claw
    # gouges, scorch patches, and monster-den rings (the hostile surface)
    r_mask = grass_px & (region_px == 3)
    crack_n = value_noise(PH, PW, 30)
    canvas[r_mask & (np.abs(crack_n - 0.5) < 0.005)] *= 0.66
    ys_v, xs_v = np.where(r_mask[::56, ::56])
    ember = np.array(ACCENTS[3], dtype=np.float32)
    for vy, vx in zip(ys_v * 56, xs_v * 56):
        h = (int(vx) * 40503 ^ int(vy) * 19349663) & 0xFFFFFFFF
        cy0, cx0 = int(vy) + (h >> 9) % 40, int(vx) + (h >> 4) % 40
        if h % 100 < 10:  # claw gouge: three parallel slashes
            for k in range(3):
                for d in range(10 + h % 7):
                    y, x = cy0 + d + k * 4, cx0 + d - k * 2
                    if 0 <= y < PH and 0 <= x < PW and r_mask[y, x]:
                        canvas[y, x] *= 0.55
        elif h % 100 < 16:  # scorch patch with ember rim flecks
            rr_s = 8 + h % 8
            yy_o, xx_o = np.ogrid[-rr_s : rr_s + 1, -rr_s : rr_s + 1]
            dd = np.sqrt(yy_o**2 + xx_o**2)
            sl_y, sl_x = slice(max(0, cy0 - rr_s), cy0 + rr_s + 1), slice(max(0, cx0 - rr_s), cx0 + rr_s + 1)
            sub = canvas[sl_y, sl_x]
            subm = r_mask[sl_y, sl_x]
            if sub.shape[:2] == dd.shape:
                sub[(dd <= rr_s) & subm] *= 0.6
                rim = (np.abs(dd - rr_s) < 1.2) & subm & ((yy_o * 3 + xx_o * 7) % 5 == 0)
                sub[rim] = sub[rim] * 0.3 + ember[None, :] * 0.7
        elif h % 100 < 20:  # den ring: trampled circle, bone flecks
            rr_s = 16 + h % 10
            yy_o, xx_o = np.ogrid[-rr_s : rr_s + 1, -rr_s : rr_s + 1]
            dd = np.sqrt(yy_o**2 + xx_o**2)
            sl_y, sl_x = slice(max(0, cy0 - rr_s), cy0 + rr_s + 1), slice(max(0, cx0 - rr_s), cx0 + rr_s + 1)
            sub = canvas[sl_y, sl_x]
            subm = r_mask[sl_y, sl_x]
            if sub.shape[:2] == dd.shape:
                sub[(dd <= rr_s * 0.8) & subm] *= 0.85
                bone = (dd <= rr_s * 0.7) & subm & ((yy_o * 5 + xx_o * 11) % 23 == 0)
                sub[bone] = sub[bone] * 0.35 + np.array((0xCE, 0xC8, 0xB2), dtype=np.float32)[None, :] * 0.65

    # --- one-off ground vignettes (v13.1): places that exist exactly once ----
    bone_c = np.array((0xC9, 0xC2, 0xA8), dtype=np.float32)

    def clip_ok(y: int, x: int) -> bool:
        return 1 <= y < PH - 1 and 1 <= x < PW - 1 and grass_px[y, x]

    # THE LEVIATHAN: a whale skeleton bleaching in the south-east Scar
    wvx, wvy = 84 * S, 55 * S
    for d in range(150):  # the spine
        y, x = wvy + int(10 * np.sin(d / 26.0)), wvx - 60 + d
        if clip_ok(y, x) and region_px[y, x] == 3:
            canvas[y, x] = canvas[y, x] * 0.35 + bone_c * 0.65
            canvas[y + 1, x] *= 0.72
    for ri_ in range(9):  # the ribs, tallest amidships
        rx = wvx - 42 + ri_ * 11
        rh = int(26 - abs(ri_ - 4) * 4)
        for d in range(rh):
            bow = int((d * d) / max(1, rh * 1.6))
            for sx_ in (-1, 1):
                y, x = wvy + int(10 * np.sin((rx - wvx + 60) / 26.0)) - d, rx + sx_ * bow
                if clip_ok(y, x) and region_px[y, x] == 3:
                    canvas[y, x] = canvas[y, x] * 0.4 + bone_c * 0.6
    # the skull: a pale mass at the head
    for dy in range(-8, 9):
        for dx in range(-11, 12):
            if (dx / 11.0) ** 2 + (dy / 8.0) ** 2 <= 1:
                y, x = wvy + int(10 * np.sin(90 / 26.0)) + dy, wvx + 90 + dx
                if clip_ok(y, x) and region_px[y, x] == 3:
                    canvas[y, x] = canvas[y, x] * 0.45 + bone_c * 0.55

    # THE FALLEN OBELISK: shattered segments in a line, west Scar -- the cult's
    # stone, face-down on the surface, a gouge trailing where it fell
    fox, foy = 46 * S, 42 * S
    for d in range(70):  # the impact gouge
        y, x = foy + d // 5, fox - 30 - d
        if clip_ok(y, x) and region_px[y, x] == 3:
            canvas[y : y + 3, x] *= 0.74
    seg_x = fox
    for si, seg_len in enumerate((34, 26, 18, 12)):
        for dy in range(-6, 7):
            for dx in range(seg_len):
                y, x = foy + dy + si * 2, seg_x + dx
                if abs(dy) <= 6 - (1 if dx in (0, seg_len - 1) else 0) and clip_ok(y, x) and region_px[y, x] == 3:
                    edge = abs(dy) >= 5 or dx in (0, seg_len - 1)
                    tone = 0.55 if edge else 0.8
                    canvas[y, x] = canvas[y, x] * (1 - tone) + np.array((0x8E, 0x92, 0x9E), dtype=np.float32) * tone
        seg_x += seg_len + 6  # the breaks between shattered segments

    # THE SILENT RING: ancient standing stones on the north Scar rise
    srx, sry = 78 * S, 20 * S
    ring_r = np.sqrt((xx_g - srx) ** 2 + ((yy_g - sry) * 1.4) ** 2)
    worn = (np.abs(ring_r - 52) < 3) & grass_px & (region_px == 3)
    canvas[worn] *= 0.85
    for k in range(9):
        ang = k * 0.698
        px_, py_ = int(srx + 52 * np.cos(ang)), int(sry + 37 * np.sin(ang))
        for dy in range(-5, 6):
            for dx in range(-2, 3):
                y, x = py_ + dy, px_ + dx
                if clip_ok(y, x) and region_px[y, x] == 3:
                    t_ = 0.75 if abs(dy) < 5 and abs(dx) < 2 else 0.5
                    canvas[y, x] = canvas[y, x] * (1 - t_) + np.array((0x9A, 0x96, 0x8A), dtype=np.float32) * t_
        # each stone leans its shadow the same way -- something passed here
        for dsh in range(6):
            y, x = py_ + 6 + dsh // 3, px_ + 3 + dsh
            if clip_ok(y, x):
                canvas[y, x] *= 0.8

    # THE DRIED LAKEBED: a pale cracked pan in the east Scar
    dlx, dly = 94 * S, 40 * S
    pan = (((xx_g - dlx) / 90.0) ** 2 + ((yy_g - dly) / 55.0) ** 2 <= 1) & grass_px & (region_px == 3)
    pan_c = np.array((0x9A, 0x8C, 0x74), dtype=np.float32)
    canvas[pan] = canvas[pan] * 0.4 + pan_c[None, :] * 0.6
    pan_crack = pan & (np.abs(value_noise(PH, PW, 22) - 0.5) < 0.012)
    canvas[pan_crack] *= 0.6
    rim = (np.abs(((xx_g - dlx) / 90.0) ** 2 + ((yy_g - dly) / 55.0) ** 2 - 1) < 0.06) & grass_px & (region_px == 3)
    canvas[rim] *= 0.78

    # r4 hall: faint marble veining -- pale contour filaments
    r_mask = grass_px & (region_px == 4)
    vein_n = value_noise(PH, PW, 55)
    mix(r_mask & (np.abs(vein_n - 0.5) < 0.006), (0xC9, 0xC4, 0xD4), 0.30)

    # --- the Conductor's ground (v11.5): UNIQUE TERRAIN, not an overlay ------
    # Owner: "I don't like that we are layering shit just make it so that
    # area has unique terrain." The boss island (carved as real land by the
    # map generator) is painted as its OWN material -- the hall's drowned
    # marble-stone floor -- with the exact same treatment grass gets (noise
    # stack, grain, organic tile-mask edge). The road, shoreline, mesas, and
    # light passes then treat it like any other ground. No discs, no rims.
    _markers0 = [l for l in data["layers"] if l.get("name") == "markers"][0]["objects"]
    _boss0 = next((o for o in _markers0 if o["name"] == "boss_1"), None)
    stage_px = np.zeros((PH, PW), dtype=bool)
    if _boss0 is not None:
        btc, btr = int(_boss0["x"] // 16), int(_boss0["y"] // 16)
        island_tiles = np.zeros_like(kind, dtype=bool)
        for _r in range(max(0, btr - 6), min(H, btr + 7)):
            for _c in range(max(0, btc - 6), min(W, btc + 7)):
                if (_c - btc) ** 2 + (_r - btr) ** 2 <= 22 and kind[_r, _c] in (0, 1):
                    island_tiles[_r, _c] = True
        stage_px = organic_mask(island_tiles, jitter=0.24, blur=9)
        stone = tint((0x6A, 0x64, 0x78), ACCENTS[4], 0.18)
        scol = stone[None, None, :] * (1 + (n_low - 0.5) * 0.18 + (n_mid - 0.5) * 0.12 + (n_hi - 0.5) * 0.08)[..., None]
        scol = scol * (1 + (grain - 0.5) * 0.10)[..., None]
        canvas[stage_px] = scol[stage_px]
        # the hall's marble veining, a little denser on the stone itself
        vein_s = value_noise(PH, PW, 48)
        vm = stage_px & (np.abs(vein_s - 0.5) < 0.007)
        canvas[vm] = canvas[vm] * 0.6 + np.array((0xC9, 0xC4, 0xD4), dtype=np.float32)[None, :] * 0.4

    # --- the Fold: the obelisk town (v12.0) ----------------------------------
    # Mir wakes here. The town is told in ground alone: a trodden prayer
    # plaza (its own material) around the spawn, ring furrows worn by
    # generations of circling worshippers, and the rectangular silt
    # foundations of huts around the streets.
    _spawn0 = next(o for o in _markers0 if o["name"] == "spawn")
    stc, str_ = int(_spawn0["x"] // 16), int(_spawn0["y"] // 16)
    town_tiles = np.zeros_like(kind, dtype=bool)
    for _r in range(max(0, str_ - 4), min(H, str_ + 5)):
        for _c in range(max(0, stc - 4), min(W, stc + 5)):
            if (_c - stc) ** 2 + (_r - str_) ** 2 <= 13 and kind[_r, _c] in (0, 1):
                town_tiles[_r, _c] = True
    plaza_px = organic_mask(town_tiles, jitter=0.22, blur=9)
    silt = tint((0x7E, 0x78, 0x62), ACCENTS[0], 0.16)
    pcol = silt[None, None, :] * (1 + (n_low - 0.5) * 0.14 + (n_mid - 0.5) * 0.10 + (n_hi - 0.5) * 0.06)[..., None]
    pcol = pcol * (1 + (grain - 0.5) * 0.10)[..., None]
    canvas[plaza_px] = pcol[plaza_px]
    # worn prayer-ring furrows, circling the plaza's heart
    scx, scy = stc * S + S // 2, str_ * S + S // 2
    rr_p = np.sqrt((xx_g - scx) ** 2 + (yy_g - scy) ** 2)
    furrow = plaza_px & (np.abs((rr_p % 30) - 15.0) < 1.1) & (rr_p > 18) & (rr_p < 120)
    canvas[furrow] *= 0.82
    # hut foundations: rectangular silt outlines in the streets around the plaza
    for fi in range(14):
        h = (fi * 2654435761 + 977) & 0xFFFFFFFF
        fc = stc + ((h >> 4) % 21) - 10
        fr = str_ + ((h >> 9) % 15) - 7
        if not (0 <= fc < W and 0 <= fr < H) or kind[fr, fc] != 0 or region[fr, fc] != 0:
            continue
        if (fc - stc) ** 2 + (fr - str_) ** 2 <= 13:
            continue  # not inside the plaza itself
        fx, fy = fc * S + (h >> 13) % 16, fr * S + (h >> 17) % 16
        fw_, fh_ = 26 + (h >> 5) % 18, 20 + (h >> 7) % 14
        if fx + fw_ >= PW - 2 or fy + fh_ >= PH - 2:
            continue
        # a filled, slightly sunken silt floor -- ground that was once a
        # hut's, not an outline drawn over the turf
        floor_m = np.zeros((PH, PW), dtype=bool)
        floor_m[fy : fy + fh_, fx : fx + fw_] = True
        floor_m &= grass_px
        fcol = silt[None, None, :] * (1 + (n_mid - 0.5) * 0.10)[..., None] * 0.9
        canvas[floor_m] = canvas[floor_m] * 0.25 + fcol[floor_m] * 0.75
        edge_m = np.zeros((PH, PW), dtype=bool)
        edge_m[fy : fy + fh_, fx : fx + fw_] = True
        edge_m[fy + 1 : fy + fh_ - 1, fx + 1 : fx + fw_ - 1] = False
        edge_m &= grass_px
        canvas[edge_m] *= 0.8

    # --- prayer rings at every save-obelisk (v12.0) --------------------------
    # The Fold's faith marks the whole ascent. Mirrors OverworldScene's
    # deterministic obelisk placement (first walkable of fixed candidates).
    def _walk(c, r):
        return 0 <= c < W and 0 <= r < H and kind[r, c] in (0, 1)
    node_names = {o["name"] for o in _markers0 if o["name"] != "spawn"}
    for o in _markers0:
        if o["name"] == "spawn":
            continue
        mc, mr = int(o["x"] // 16), int(o["y"] // 16)
        cand = [(mc - 2, mr), (mc + 2, mr), (mc, mr + 2), (mc, mr - 2), (mc - 2, mr + 1), (mc + 2, mr + 1)]
        spot = next(((c, r) for c, r in cand if _walk(c, r)), None)
        if spot is None:
            continue
        ocx, ocy = spot[0] * S + S // 2, spot[1] * S + S // 2
        rr_o = np.sqrt((xx_g - ocx) ** 2 + (yy_g - ocy) ** 2)
        ring = (np.abs(rr_o - 22.0) < 1.6) & grass_px
        canvas[ring] *= 0.78
        knee = (np.abs(rr_o - 22.0) < 5.0) & (rr_o >= 23.6) & grass_px & (value_noise(PH, PW, 9) > 0.6)
        canvas[knee] *= 0.9

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
    # the road dissolves into the island's stone -- one material there, no
    # tan ribbon crossing the unique terrain (v11.5)
    path_mask &= ~stage_px
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

    # v13.1 road materials: silt lanes under the sea, packed dirt across the
    # Scar, pale worn paving on the Stage approach -- one road, three makings
    silt_road = path_mask & (w01 > 0.5)
    canvas[silt_road] = canvas[silt_road] * 0.7 + np.array((0xA8, 0xA4, 0x8E), dtype=np.float32)[None, :] * 0.3
    dirt_road = path_mask & (region_px == 3) & (w01 <= 0.5)
    canvas[dirt_road] = canvas[dirt_road] * 0.65 + np.array((0x74, 0x58, 0x40), dtype=np.float32)[None, :] * 0.35
    paved_road = path_mask & (region_px == 4)
    canvas[paved_road] = canvas[paved_road] * 0.7 + np.array((0xA9, 0xA2, 0xB8), dtype=np.float32)[None, :] * 0.3

    # --- desire-path spurs ----------------------------------------------------
    # Side trails are half-swallowed by the turf: narrower, paler, and BROKEN
    # into worn patches -- you learn to read them, they never compete with the
    # main road. (Secret-pocket approaches stay findable but subtle.)
    spur_px = np.zeros((PH, PW), dtype=bool)
    if spur_tiles.any():
        spur_band = organic_mask(spur_tiles, jitter=0.26, blur=7)
        spur_px = spur_band & (value_noise(PH, PW, 12) > 0.34) & ~path_mask & ~stage_px
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
    # v13.1 water types: the Scar's pits are TAR (black-warm, no foam), the
    # Stage's lake is deep ink-violet; the drowned pools keep their teal
    tar = water_mask & (region_px == 3)
    canvas[tar] = canvas[tar] * 0.45 + np.array((0x16, 0x0E, 0x0A), dtype=np.float32)[None, :] * 0.55
    ink = water_mask & (region_px == 4)
    canvas[ink] = canvas[ink] * 0.6 + np.array((0x0C, 0x08, 0x1E), dtype=np.float32)[None, :] * 0.4
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
    foam_ring = water_mask & ~erode(water_mask, 2)[2] & (region_px != 3)  # tar doesn't foam
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
        if reg not in (0, 1, 4) and h % 5 != 0:
            continue  # cluster under the sea (Fold/Shelf) + the hall lake
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
    mesa_px = np.zeros((PH, PW), dtype=bool)  # union, so later passes respect the mesas
    for comp in range(1, nxt + 1):
        cm = organic_mask(labels == comp, jitter=0.34, blur=8)
        if not cm.any():
            continue
        mesa_px |= cm
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
    disc_noise = value_noise(PH, PW, 22)
    # v11.5 (owner: "I don't like that we are layering shit"): fight wear is
    # for REGULAR arenas only -- turf blending toward packed earth, patchy,
    # clipped from mesas/water. The boss island needs nothing here: its
    # ground IS the unique hall-stone terrain painted with the grass pass.
    for obj in markers:
        if obj["name"] == "spawn" or obj["name"] == "boss_1":
            continue
        cx, cy = float(obj["x"]) * 2, float(obj["y"]) * 2
        reg = int(region[min(H - 1, int(cy // S)), min(W - 1, int(cx // S))])
        radius = 132.0
        rr = np.sqrt((xx_g - cx) ** 2 + (yy_g - cy) ** 2) + (disc_noise - 0.5) * 56
        t = np.clip((radius - rr) / radius, 0.0, 1.0)  # 0 at rim -> 1 at centre
        # patchy trampled wear: strongest at centre, ground grinding through
        wear = (t**0.65) * (0.45 + 0.55 * n_mid) * 0.8
        land = ~water_mask & ~mesa_px & (wear > 0.02)
        base = tint((0x6E, 0x61, 0x4A), ACCENTS[reg], 0.28)
        earth = base[None, None, :] * (1 + (n_mid - 0.5) * 0.14 + (n_hi - 0.5) * 0.08)[..., None]
        a = wear[..., None] * land[..., None]
        canvas = canvas * (1 - a) + earth * a
        # faded, BROKEN wear arcs (circling feet), never full stamped rings
        arcs = land & (rr < radius - 10) & (np.abs((rr % 44) - 22.0) < 1.0) & (rr > 30) & (value_noise(PH, PW, 16) > 0.5)
        canvas[arcs] *= 0.9

    # --- under the sea + the waterline (v12.0) --------------------------------
    # The Fold and the Shelf are on the ocean floor; the western Breach still
    # wades. West of the wobbling waterline the world renders UNDERWATER:
    # a cool depth grade, caustic light webs playing over the ground, and
    # drifting sediment. The line itself is a broken foam seam; the surface
    # side dries out of it, wet sand darkening right at the crossing.
    depth_u = np.clip((w01 - 0.35) / 0.3, 0.0, 1.0)
    deep_sea = np.array((0x10, 0x2E, 0x36), dtype=np.float32)
    canvas = canvas * (1 - (depth_u * 0.22)[..., None]) + deep_sea[None, None, :] * (depth_u * 0.22)[..., None]
    # (v12.1 -- owner: "why are we still placing shit on-top of everything":
    # the caustic-web + sediment overlay crossed every material at uniform
    # strength and read as a decal layer; deleted. The depth grade, the
    # region materials, the drowned shapes, and the waterline say
    # "underwater" without painting a pattern over the world.)
    # the foam seam, broken (never a solid rule) -- and the wet band beyond it
    seam_d = np.abs(w01 - 0.5)
    foam_line = (seam_d < 0.012) & ~water_mask & (value_noise(PH, PW, 12) > 0.28)
    canvas[foam_line] = canvas[foam_line] * 0.35 + np.array((0xD9, 0xF2, 0xEA), dtype=np.float32)[None, :] * 0.65
    wet_band = (w01 < 0.5) & (w01 > 0.36) & ~water_mask
    canvas[wet_band] *= (1 - 0.14 * np.clip((w01[wet_band] - 0.36) / 0.14, 0, 1))[..., None]

    # --- Nari's trail (v12.0): he FOLLOWED -- until the Scar ------------------
    # Tiny toddler footprints trail the route from the Fold: Nari walking
    # behind his father. At the first route tile on the surface (the Scar,
    # region index 3) the trail ends in a scuffle -- prints circling, a drag
    # mark -- and beyond it only sparse single prints remain: clues.
    def stamp_print(py: int, px: int, drag: bool = False) -> None:
        """Nari's print: a paired 2x2 sole WITH a heel dot -- and on every
        other step, a faint drag tail (his right foot drags). This is his
        learnable signature; decoy prints elsewhere carry none of it."""
        if 1 <= py < PH - 3 and 1 <= px < PW - 4 and not water_mask[py, px]:
            canvas[py : py + 2, px : px + 2] *= 0.62  # sole
            canvas[py + 2, px] *= 0.7  # heel
            if drag:
                canvas[py + 1, px + 2 : px + 4] *= 0.8  # the drag tail
    loss_idx = next((i for i, (ty, tx) in enumerate(route) if region[ty, tx] >= 3), len(route))
    for i in range(3, min(loss_idx, len(route) - 1), 10):
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
            stamp_print(py_ + (h >> step) % 2, px_ + (h >> (step + 3)) % 2, drag=step % 2 == 0)
    if loss_idx < len(route):
        ty, tx = route[loss_idx]
        cx, cy = tx * S + S // 2, ty * S + S // 2
        h = 0x5EED
        # the scuffle: prints circling in panic
        for k in range(12):
            ang = k * 0.55 + (h >> k) % 3 * 0.2
            stamp_print(int(cy + 10 * np.sin(ang)), int(cx + 12 * np.cos(ang)))
        # the drag mark, leading away from the road
        for d in range(26):
            y, x = cy + d // 3, cx + d
            if 0 <= y < PH and 0 <= x < PW and not water_mask[y, x]:
                canvas[y : y + 2, x] *= 0.6
        # beyond: sparse single prints -- the clues Mir hunts
        for i in range(loss_idx + 6, len(route) - 1, 24):
            ty, tx = route[i]
            h2 = (tx * 40503 ^ ty * 2654435761) & 0xFFFFFFFF
            stamp_print(ty * S + (h2 >> 5) % S, tx * S + (h2 >> 11) % S, drag=h2 % 2 == 0)

    # --- other tracks (v12.2): WHICH prints are his? -------------------------
    # Owner: "along with naris footsteps there's tracks of other people, we
    # have to understand and distinguish which ones are actually naris."
    # The world is walked. Pilgrims' adult prints pace the road margins;
    # three-toed den creatures cross the Scar; and -- cruelest -- other
    # SMALL prints wander regions beyond the Breach. Nari's signature is
    # learnable while he walks behind you in the Fold: paired gait, heel
    # dot, faint right-foot drag. Decoys are single-file, heel-less,
    # drag-less. Reading the difference IS the tracking game.
    def adult_print(py: int, px: int) -> None:
        if 1 <= py < PH - 4 and 1 <= px < PW - 2 and not water_mask[py, px]:
            canvas[py : py + 3, px : px + 2] *= 0.6  # long sole
            canvas[py + 3, px] *= 0.66  # heavy heel
    def small_decoy_print(py: int, px: int) -> None:
        if 1 <= py < PH - 2 and 1 <= px < PW - 2 and not water_mask[py, px]:
            canvas[py : py + 2, px : px + 2] *= 0.62  # sole only: no heel, no drag
    def critter_print(py: int, px: int) -> None:
        for dy, dx in ((0, 0), (2, -2), (2, 2)):  # three toes
            y, x = py + dy, px + dx
            if 1 <= y < PH and 1 <= x < PW and not water_mask[y, x]:
                canvas[y, x] *= 0.5
    # pilgrims: paired adult strides along the road margins, map-wide
    if route:
        for ti in range(26):
            h = (ti * 2654435761 + 13) & 0xFFFFFFFF
            i = (h >> 4) % max(1, len(route) - 1)
            ty, tx = route[i]
            ny, nx = route[min(i + 1, len(route) - 1)]
            dy, dx = ny - ty, nx - tx
            side = 1 if h % 2 else -1
            cy0 = ty * S + S // 2 + dx * side * ((h >> 7) % 8 + 10)
            cx0 = tx * S + S // 2 + dy * side * ((h >> 7) % 8 + 10)
            for k in range(7 + (h >> 5) % 9):
                lat = 3 if k % 2 else -3
                adult_print(cy0 + dy * k * 11 + dx * lat, cx0 + dx * k * 11 + dy * lat)
    # the decoys: single-file small prints wandering beyond the Breach
    surface_open = list(zip(*np.where((region >= 2) & (kind == 0))))
    for ti in range(14):
        h = (ti * 83492791 + 401) & 0xFFFFFFFF
        if not surface_open:
            break
        tr, tc = surface_open[(h >> 4) % len(surface_open)]
        ang = ((h >> 11) % 628) / 100.0
        sx, sy = np.cos(ang), np.sin(ang) * 0.5
        for k in range(6 + (h >> 6) % 9):
            small_decoy_print(int(tr * S + 16 + sy * k * 9), int(tc * S + 16 + sx * k * 9))
    # den creatures: three-toed crossings on the Scar
    scar_open = list(zip(*np.where((region == 3) & (kind == 0))))
    for ti in range(10):
        h = (ti * 40503 + 77) & 0xFFFFFFFF
        if not scar_open:
            break
        tr, tc = scar_open[(h >> 4) % len(scar_open)]
        ang = ((h >> 11) % 628) / 100.0
        sx, sy = np.cos(ang), np.sin(ang) * 0.6
        for k in range(5 + (h >> 6) % 7):
            critter_print(int(tr * S + 16 + sy * k * 8), int(tc * S + 16 + sx * k * 8))

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
