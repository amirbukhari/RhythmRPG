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
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "assets" / "tilemaps" / "overworld.json"
OUT = ROOT / "assets" / "tilemaps" / "ground_plate.png"

S = 16  # px per tile cell. v15.0: dropped from 32 (2x) to 16 (1x) so the ~10x
# world's chunked ground stays a sane RAM/bake/repo weight; the runtime draws
# chunks at scale 1.0 (S == TILE_SIZE).
RNG = np.random.default_rng(20260714)

# v12.0 Ascent accents: the Fold (deep teal), the Kelp Shelf (kelp green),
# the Breach (sand/foam), the Scar (blood rust), the Stage (storm violet)
# The fifth was 0x7A4EB4, storm violet, inherited from the retired cosmology's
# carnival -- see KEEP in tools/art/palette.py. The Keep is a drowned concert
# hall and its accent is the game's own brass lamplight.
# The third was 0xE8D9A8, warm sand -- see BREACH in tools/art/palette.py for
# why it is foam now. The accent feeds `grass_bases`, `path_bases`,
# `shore_bases`, `rock_top_bases` and the arena wear base, so region 2's
# grass, road, shoreline, rock and trampled ground all turn cold together.
ACCENTS = [(0x49, 0xC6, 0xBD), (0x58, 0xC0, 0x7A), (0xB6, 0xCA, 0xC4), (0xC2, 0x54, 0x24), (0xC6, 0x98, 0x4E)]



def tint(base: tuple[int, int, int], accent: tuple[int, int, int], amt: float) -> np.ndarray:
    return np.array([b + (a - b) * amt for b, a in zip(base, accent)], dtype=np.float32)


def value_noise(h: int, w: int, cell: int) -> np.ndarray:
    """Smooth [0,1] noise: white noise at coarse res, bilinear upsample."""
    gh, gw = max(2, h // cell + 2), max(2, w // cell + 2)
    coarse = RNG.random((gh, gw), dtype=np.float32)
    img = Image.fromarray((coarse * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255.0


def crack_net(
    h: int,
    w: int,
    spacing: int,
    thick: float = 0.75,
    density: float = 1.0,
    aspect: float = 1.0,
    warp: float = 0.0,
) -> np.ndarray:
    """A real mud-crack web: the shared EDGES of a jittered Voronoi tessellation.

    THIS REPLACES AN ISOCONTOUR, WHICH IS A DOODLE GENERATOR. Three separate
    passes in this file used `abs(value_noise(...) - 0.5) < eps` for cracks and
    all three shipped wrong, in two different ways depending on the cell size: a
    coarse cell gave long sweeping curves that dip in and out of the band, i.e.
    DASHED LINES (dressmaker's chalk), and a fine cell gave a confetti of
    disconnected hooks and ticks (scattered glyphs). Neither is a crack, because
    a level set of a smooth field has no reason to close, meet, or branch.

    Dried mud does not crack along a level set. It shrinks, and shrinkage tears
    it along the boundaries between cells, so the pattern is a CONNECTED
    POLYGON NETWORK: every cell closed, every junction a Y, every segment
    ending at another segment. That is exactly a Voronoi diagram's edge set, so
    build it as one -- mark the pixels whose two nearest seeds are nearly
    equidistant -- and the topology is right by construction rather than by
    luck. `spacing` is the polygon size in PLATE pixels (the camera shows 320 of
    them across, so 40 gives about eight cells per screen); `thick` is a hair
    under a pixel because the plate draws 1:1 into a 4x-scaled camera and a
    2px plate line arrives eight screen pixels wide.

    WHY A PLAIN JITTERED GRID READ AS BURLAP. Seeds jittered WITHIN their own
    cell stay a Poisson-disc lattice: every plate ends up ~`spacing` across, so
    the whole net has ONE pitch on both axes and tiles the eye as woven canvas
    -- which is exactly what the Scar shipped looking like. Dried earth does not
    do this: its plates range from a thumbnail to a dinner plate. Three levers
    break the single pitch, all defaulting OFF so the salt-pan hex is untouched:
      * `density` (<1) drops that fraction of seeds, so their neighbours' cells
        MERGE into larger irregular plates -- the cell SIZE now varies, which is
        the thing a jittered grid cannot do.
      * `aspect` (!=1) stretches the lattice on one axis, so plates are not
        square -- earth cracks are rarely isotropic.
      * `warp` (>0) bends the query space through a coarse noise flow before the
        Voronoi is read, so the rows and columns are no longer straight.

    Banded over rows so the intermediate distance fields never all exist at
    once -- the plate is 18M pixels and this needs three float32 planes.
    """
    sp_x = float(spacing)
    sp_y = float(spacing) * aspect
    gh, gw = int(h / sp_y) + 3, int(w / sp_x) + 3
    jy = RNG.random((gh, gw), dtype=np.float32)
    jx = RNG.random((gh, gw), dtype=np.float32)
    sy = (np.arange(gh, dtype=np.float32)[:, None] - 1.0 + jy * 0.88 + 0.06) * sp_y
    sx = (np.arange(gw, dtype=np.float32)[None, :] - 1.0 + jx * 0.88 + 0.06) * sp_x
    sy = np.ascontiguousarray(np.broadcast_to(sy, (gh, gw)))
    sx = np.ascontiguousarray(np.broadcast_to(sx, (gh, gw)))
    if density < 1.0:
        # push the dropped seeds out of reach; their cells fold into neighbours
        keep = RNG.random((gh, gw), dtype=np.float32) < density
        sy = np.where(keep, sy, 1e9)
        sx = np.where(keep, sx, 1e9)
    # domain warp: a coarse smooth flow that displaces the query point, so the
    # lattice bends on both axes instead of ruling straight rows and columns
    wx = wy = None
    if warp > 0.0:
        amp = warp * spacing
        wx = (value_noise(h, w, spacing * 5) - 0.5) * (2.0 * amp)
        wy = (value_noise(h, w, spacing * 5) - 0.5) * (2.0 * amp)
    out = np.zeros((h, w), dtype=bool)
    xx_base = np.arange(w, dtype=np.float32)[None, :]
    for y0 in range(0, h, 512):
        y1 = min(h, y0 + 512)
        yy = np.arange(y0, y1, dtype=np.float32)[:, None] + np.zeros((1, w), dtype=np.float32)
        xx = xx_base + np.zeros((y1 - y0, 1), dtype=np.float32)
        if warp > 0.0:
            xx = xx + wx[y0:y1]
            yy = yy + wy[y0:y1]
        gx = np.clip((xx / sp_x).astype(np.int32) + 1, 0, gw - 1)
        gy = np.clip((yy / sp_y).astype(np.int32) + 1, 0, gh - 1)
        d1 = np.full((y1 - y0, w), 1e9, dtype=np.float32)
        d2 = np.full((y1 - y0, w), 1e9, dtype=np.float32)
        for dy in (-1, 0, 1):
            iy = np.clip(gy + dy, 0, gh - 1)
            for dx in (-1, 0, 1):
                ix = np.clip(gx + dx, 0, gw - 1)
                d = np.hypot(sy[iy, ix] - yy, sx[iy, ix] - xx)
                lower = d < d1
                d2 = np.where(lower, d1, np.minimum(d2, d))
                d1 = np.where(lower, d, d1)
        out[y0:y1] = (d2 - d1) < thick
    return out


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
    # Fold + Shelf are BOTH underwater (the waterline is at the Breach), so both
    # are cool/submerged -- but distinct: the Fold is a bluer silt town-floor,
    # the Shelf a greener drowned KELP slope. Not a sunlit meadow (owner: "the
    # transition from the fold straight to grass doesn't make sense").
    # THE THIRD ONE WAS 0x867654, "wet sand", and it was the whole reason region 2
    # arrived as a desert. Look at the family: every other base sits between 0x22
    # and 0x4A, and that one was 0x86 -- more than double the value of any of the
    # others, and the only warm one. It was not a tint problem, it was a BASE
    # problem: no accent applied at 0.22 can pull a 0x86 warm tan back into a
    # region whose kit is authored as cold neutral slate, and the frame came back
    # khaki with the carnival sitting on a beach in it.
    #
    # The Breach is a FORESHORE at the moment the tide is out: cool grey-green
    # wet shingle. It is still the lightest of the five, because it is the one
    # region with sky over it (§6.3, the first breath of surface air) -- but
    # lightest of a family, not an outlier from a different game.
    #
    # AND THEN REGION 3 ARRIVED AS ARIZONA. Same failure, one region east.
    # Measured off the shipped plate, the ground under the den camp was
    # #623720 -- hue 21, SATURATION 67%. Every other ground in the game
    # measures between 10% and 45%, so the Scar was not "warm", it was the
    # only saturated surface in the world, and the only one whose hue reads
    # as sunlight. §6.4 asks for "gouged, burned, pitted, picked-over"; what
    # rendered was an oxide desert with mining equipment standing on it, and
    # the equipment -- authored in char and ash and iron -- read as grey
    # CUT-OUTS pasted onto orange. It also broke §3 twice over: the ground
    # was the brightest large field in the frame, so the three dig lamps,
    # which are the only real light in the region, had to compete with it.
    #
    # It was the tint, not the base: 0.22 of a 0xC25424 ember over a dark
    # brown lands at 58% saturation before the noise pass touches it. An
    # ACCENT is a small hot thing (§3) and must not be smeared across
    # forty-three thousand tiles at a fifth strength -- so the strength is
    # per-region now, and the Scar takes an EIGHTH of its ember. What is left
    # is a bruise: dark, warm, and desaturated to 40%, which is where the
    # Shelf and the Fold already sit. The ember still burns at full strength
    # where it belongs, in the ember motifs and the lamps.
    GROUND_BASES = [(0x26, 0x40, 0x4A), (0x22, 0x44, 0x3C), (0x54, 0x5C, 0x56), (0x44, 0x34, 0x30), (0x33, 0x33, 0x3B)]
    # AND THEN REGION 4 CAME BACK AS MUD, which is the third time this exact
    # line has shipped a region in the wrong colour. `ACCENTS[4]` is a warm gilt
    # (0xC698 4E) -- correct as an accent, it is candlelight on brass -- and 0.22
    # of it over the cool grey-violet base lands at hue 28, saturation 29%: a
    # concert hall the colour of a ploughed field. Measured on the shipped plate
    # at (336,26), the "deepest darkest place in the hall", it was #3a322a.
    #
    # The Keep gets a SIXTEENTH of its accent, which is less than the Scar's
    # eighth, and for a reason already written down in tools/art/env_keep.py's
    # header as rule 3: THE WARMTH IN THIS REGION IS IN THE MATERIALS, NOT IN
    # THE LIGHT. Mahogany, gilt, brass and velvet are all warm and all of them
    # are OBJECTS; the floor they stand on is cold marble in an unlit room, and
    # if the floor is warm too then §7's warm room is not an arrival, it is more
    # of the same. The one region whose accent belongs on the ground is the Fold,
    # because its accent IS its water.
    GRASS_TINTS = [0.22, 0.22, 0.22, 0.08, 0.06]
    grass_bases = [tint(b, a, t) for b, a, t in zip(GROUND_BASES, ACCENTS, GRASS_TINTS)]
    img = blended(grass_bases)
    n_low = value_noise(PH, PW, 160)
    n_mid = value_noise(PH, PW, 36)
    n_hi = value_noise(PH, PW, 7)
    img *= (1 + (n_low - 0.5) * 0.30 + (n_mid - 0.5) * 0.18 + (n_hi - 0.5) * 0.10)[..., None]
    # POOLED DARK PATCHES, and this line was a camouflage generator. A hard
    # threshold on a cell-160 noise field paints flat blobs with HARD EDGES --
    # binary in, binary out -- and wherever two districts of different hue
    # overlapped one of these blobs (the Oasis's green against the sulfur
    # barrens' olive) the result was military camo: three or four flat patches
    # of different colour meeting along crisp curves. It is the same shape as
    # the flat-patch law noted further down: any pass that hard-selects a
    # region of the canvas owes it a gradient at the boundary.
    pool = np.clip((0.36 - n_low) / 0.11, 0, 1)
    img *= (1 - 0.15 * pool)[..., None]
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
    # THE FLAT-PATCH LAW (v16.6). `bed` SATURATES at 1.0 over most of a bed --
    # there, `sea` is discarded entirely and the bed colour is all that is left.
    # So the bed colour must carry the SAME high-frequency terms the ground
    # field does (`grain`, `n_hi`), not just the cell-36 swell: a cell-36 term
    # moves by ~1/200 of a step across 8 pixels, and the elevation pass then
    # multiplies by a QUANTIZED terrace tone that is constant inside a terrace.
    # Constant x constant = a mathematically flat block, and the plate had 136
    # of them in the Fold alone -- hard-edged untextured patches on the most
    # visible surface in the game. Any pass that fully REPLACES the canvas owes
    # it the grain back. (Measured: zero-variance 8x8 blocks, `bed_n > 0.67`.)
    grassy = tint((0x1F, 0x3B, 0x30), ACCENTS[0], 0.25)[None, None, :] * (
        1 + (n_mid - 0.5) * 0.16 + (n_hi - 0.5) * 0.12 + (grain - 0.5) * 0.11
    )[..., None]
    # and the bed is a BED, not a paint spill: dark blades comb through it in
    # the same direction the dune ripples run, so the patch reads as growth.
    blades = ((yy_g * 0.7 + dune_wob * 0.5 + value_noise(PH, PW, 9) * 9).astype(np.int32) % 5) < 1
    grassy = grassy * np.where(blades, 0.86, 1.0)[..., None]
    sea = sea * (1 - bed) + grassy * bed
    canvas = canvas * (1 - w0[..., None]) + sea * w0[..., None]

    # --- ELEVATION: the world has RELIEF now (v13.2) -------------------------
    # The single biggest variation lever the map was missing: it was dead
    # flat. A smooth height field (low in the drowned SW, rising toward the
    # Stage in the NE -- the ascent is literally uphill) is quantized into
    # terraces; each step down toward the south casts a shadow cliff and the
    # high side catches a lit rim. Applied globally so the WHOLE map rolls,
    # not just isolated mesas. Water sits in the lows; the pass skips it.
    grade = (xx_g / PW) * 0.35 + (1.0 - yy_g / PH) * 0.35  # NE is high
    elev = np.clip(grade + (value_noise(PH, PW, 150) - 0.5) * 0.9 + (value_noise(PH, PW, 60) - 0.5) * 0.35, 0, 1)
    LEVELS = 7
    terr = np.floor(elev * LEVELS)
    land_e = ~( (region_px >= 0) & False )  # all true; water masked out later
    # tonal lift with height (high ground is lit, hollows pool dark)
    canvas *= (0.82 + terr / LEVELS * 0.34)[..., None]
    # step edges: where the terrace drops to the south (row+), a cast-shadow
    # band; where it rises to the north, a bright lip
    drop = (terr < np.roll(terr, 8, 0))   # lower than the tile 8px north => a south-facing face
    rise = (terr > np.roll(terr, 8, 0))
    face = np.zeros_like(terr, dtype=bool)
    acc = drop.copy()
    for _ in range(9):  # thicken the cliff face downward
        acc = np.roll(acc, 1, 0) & (terr < np.roll(terr, 9, 0) + 1)
        face |= acc
    face |= drop
    # softer cliff-shadow (was *0.6): the hard terrace bands read as abstract
    # topo-map contour lines. Gentler now -- relief without the drafting look.
    canvas[face] *= 0.76
    stria = face & (value_noise(PH, PW, 3) > 0.5)
    canvas[stria] *= 0.88
    canvas[rise] = np.minimum(canvas[rise] * 1.22 + 8, 255)
    # a WHISPER of terrace contour off the steps -- subtle, not a topo map
    slope = np.abs(terr - np.roll(terr, 10, 0)) + np.abs(terr - np.roll(terr, 10, 1))
    contour = (np.abs((elev * LEVELS) % 1.0) < 0.02) & (slope > 0)
    canvas[contour] *= 0.96

    # --- AUTHORED DISTRICTS (owner: "biomes are all one colour ... no unique
    # sections within any of the biomes ... everything should feel
    # intentional"). NOT noise bands: each sub-zone is a HAND-PLACED place with
    # its own bold palette + signature texture, positioned deliberately and
    # lined up with the landmark that sits on it -- bone-pale earth under the
    # Boneyard, salt crust under the Salt Flats, mineral teal under the Geysers,
    # charcoal under the scorch. The world reads as a MAP OF PLACES, not five
    # flat fields. A low-freq noise only WARPS each blob's border so a placed
    # place never reads as a stamped clean ellipse.
    _warp = value_noise(PH, PW, 40)
    _gp = np.asarray(Image.fromarray(((kind == 0) * 255).astype(np.uint8)).resize((PW, PH), Image.NEAREST)) > 127

    def district(cx_t, cy_t, rx_t, ry_t, reg, rgb, amt, feather=0.62):
        cx, cy, rx, ry = cx_t * S, cy_t * S, rx_t * S, ry_t * S
        dd = np.sqrt(((xx_g - cx) / rx) ** 2 + ((yy_g - cy) / ry) ** 2) + (_warp - 0.5) * 0.30
        m = dd <= 1.0
        if not m.any():
            return m & (region_px == reg)
        # Gate the colour by SOFT region membership (the blurred weight field),
        # NOT a hard region cut -- so a district that reaches a region seam
        # fades out across it instead of showing a blocky 16px-stepped edge
        # (this was the jagged rust-vs-Stage seam). Bounded by the radius too.
        memb = (weights[reg] / wsum)[m]
        soft = (np.clip((1.0 - dd[m]) / feather, 0, 1) * amt * memb)[:, None]
        canvas[m] = canvas[m] * (1 - soft) + np.array(rgb, dtype=np.float32)[None, :] * soft
        return m & (region_px == reg)  # hard-clipped disc for the texture pass

    # name / cx(tile) / cy / rx / ry / region / rgb / strength
    AUTHORED = [
        # THE SCAR (region 3) -- the 60% surface, now ~10 NAMED places. Dark
        # districts get bold amt + high-contrast palettes so they read against
        # the dark-brown base; the whole east is filled so nothing stays blank.
        # BLEACHED IS A SATURATION, NOT A VALUE. This was 0xB8B29A at 0.60 and
        # measured 48% value on the plate -- the brightest large field in the
        # Scar, so the frame at (190,100) came back as an empty warm haze with
        # the bone piles sitting on it barely darker than the dirt. Bone reads
        # as bone because it is DRIER than the earth, not lighter than it.
        ("boneyard",  178, 106, 26, 20, 3, (0x94, 0x8E, 0x7C), 0.46),  # bleached bone earth (under the bones)
        ("geyserpan", 203,  42, 22, 16, 3, (0x8C, 0xA6, 0x9C), 0.52),  # mineral teal-grey crust (under the geysers)
        ("ashwaste",  146,  54, 26, 20, 3, (0x7C, 0x78, 0x72), 0.56),  # pale cool ash grey, NW Scar
        # THE DEN STANDS ON THE BASALT, and it did not. `basalt` was centred
        # (268,84) r30x23, which misses (290,67) by four percent of its own
        # radius, and `rustdunes` -- the loudest district in the game -- caught
        # it instead. So §6.4's ending, the den and the man in it, was staged
        # on a bright orange dune field. The bleakest ground in the region now
        # reaches the one place in it that has to land.
        ("basalt",    280,  80, 34, 26, 3, (0x52, 0x54, 0x50), 0.64),  # neutral slate basalt flats, central-E (breaks the brown, not Stage-purple)
        # THE GREEN WAS NOT UNDER THE PLANTS. This disc was centred (236,120)
        # r15x13, so it covered rows 107-133 -- and `place_scar`'s Oasis is laid
        # out over rows 125-136, which means the bottom third of the clearing sat
        # on bare brown and the top two thirds of the green field had nothing
        # growing on it. Centred on the spring now, and TIGHTER, so the green is
        # exactly as big as the place it belongs to. `feather` is opened up as
        # well: at 0.62 the falloff was steep enough to show an edge, and a
        # clearing does not have an edge, it has an outskirt.
        # A POCKET NEEDS ITS EDGE IN THE FRAME. At r12x10 the green filled the
        # whole 20x11 camera and the Oasis read as a MEADOW -- §6.4 asks for "one
        # pocket of living green", and a pocket is defined by the dead ground you
        # can see around it. Nine by seven puts brown in the corners of the frame
        # from wherever you stand in the clearing, and the amount comes down too
        # so the ground green stays a step under the plants growing on it.
        ("oasis",     237, 130, 5, 4, 3, (0x4E, 0x70, 0x36), 0.46, 0.85),  # a POCKET, and the camera is 20x11 tiles: r9x7 filled the frame edge to edge and read as a meadow. Half the screen has to stay dead or the green means nothing
        # ...and it is a POCKET now, not a province. A vivid oxide field is a
        # fine thing to find off the road; it is not a fine thing to hold the
        # region's climax. Moved to the far NE corner and cut to a third of
        # its old area, so it stays a discovery.
        ("rustdunes", 322,  32, 26, 20, 3, (0xC4, 0x60, 0x22), 0.52),  # VIVID burnt-orange oxide dunes, NE Scar
        ("verdigris", 342,  98, 21, 21, 3, (0x4C, 0x60, 0x52), 0.50),  # muted oxidised-copper seep (mineral, not meadow), far-E Scar
        ("scorch",    334, 132, 26, 24, 3, (0x1C, 0x16, 0x16), 0.72),  # near-black scorchreach, E Scar
        # ...and it is moved off the Oasis. At (252,152) r25x21 the barrens
        # reached rows 131-173, straight through the clearing, so the one place
        # in the region that is meant to read as ALIVE had a sickly olive laid
        # under half of it. Green and yellow-green fighting over the same tiles
        # is also the single worst pairing available for the camo failure noted
        # at the pooled-patch line above.
        ("sulfur",    262, 164, 24, 19, 3, (0x7C, 0x78, 0x38), 0.56),  # sickly sulfur barrens, SE Scar
        ("tarpit",    300, 172, 22, 18, 3, (0x22, 0x1C, 0x1A), 0.62),  # black tar seeps, far SE Scar
        ("bloodmire", 114, 152, 24, 20, 3, (0x54, 0x22, 0x26), 0.64),  # dark blood-maroon bog, SW Scar
        ("saltpan",   216, 186, 32, 12, 3, (0xC0, 0xBA, 0xAC), 0.54),  # pale salt crust (under the Salt Flats)
        # THE KELP SHELF (region 1) -- all SUBMERGED tones (drowned, not a meadow)
        ("kelpforest", 34,  44, 22, 26, 1, (0x18, 0x40, 0x30), 0.52),  # dense dark kelp beds (bluer green)
        ("mastsilt",   57,  63, 18, 16, 1, (0x38, 0x4A, 0x46), 0.44),  # cool grey seafloor silt (mast forest)
        ("paleshoal",  74,  22, 22, 16, 1, (0x44, 0x60, 0x5A), 0.42),  # pale teal shoal (shallow submerged sand)
        # THE FOLD (region 0) -- keep it deep + blue, distinct from Shelf green
        ("eelgrass",   20, 185, 17, 14, 0, (0x14, 0x30, 0x2E), 0.46),  # near-black eelgrass deeps
        ("praysilt",   33, 162, 15, 12, 0, (0x40, 0x5C, 0x5E), 0.36),  # pale teal silt clearing (the town)
        # THE BREACH (region 2) -- FOUR districts now, and it had two.
        #
        # Two was thin for the region the story turns on (the Keep's note below
        # makes the same complaint about itself), and one of the two was wrong:
        # `drysand` at 0xC6B68A, "warm dry crossing sand", sat centred on (126,92)
        # -- which is exactly where the midway stands -- and painted the carnival
        # a holiday-beach tan. See ACCENTS above.
        #
        # Read west to east, which is the way he crosses: he is still wading, then
        # he is over the old high-water mark, then he is on hard wet shingle with
        # the fair on it, then the ground is drying out toward the Scar. The
        # wrackline is the one that matters -- a band of stranded weed and litter
        # marking how far the water came, running north-south across his path, so
        # the crossing has a THRESHOLD in it and is not just a gradient.
        ("tidepool",   85, 138, 18, 16, 2, (0x62, 0x82, 0x82), 0.44),  # bluer tidal shallows -- still wading
        ("wrackline",  99, 116, 13, 30, 2, (0x3C, 0x44, 0x36), 0.50),  # stranded weed + litter: the high-water mark
        ("foreshore", 114,  88, 21, 19, 2, (0x7E, 0x8E, 0x88), 0.46),  # hard wet shingle -- the midway stands here
        ("saltcrust", 132, 141, 18, 18, 2, (0xAC, 0xB2, 0xA6), 0.44),  # cold pale crust, drying toward the Scar
        # THE KEEP (region 4) -- a drowned concert hall, "taken and repurposed"
        # (world-bible §6.5). It had TWO districts, both violet: `inkreach`
        # (0x201A30, "deep violet-black") and a `marble` at 0xB0AAC2. Both were
        # the retired cosmology's Stage, and both slipped the palette gate by a
        # hair -- hue 256 and 255 against a 258 floor. Two districts is also
        # thin for the last region in the game: the Fold has three and the Scar
        # has twelve, and the Keep is where the story ENDS.
        #
        # So it is a hall now, read west-to-east the way you walk into one:
        # the way in, the seats, the pit where the players drowned, and the
        # marble the room is built on. §6.5: "an orchestra that drowned
        # mid-performance, stands and chairs and stopped clocks. Beautiful, and
        # nobody's story." Nothing here is cold or strange -- that is the whole
        # trap (see KEEP in tools/art/palette.py).
        # THE FOUR KEEP DISTRICTS ALL OVERLAPPED EACH OTHER, and the one with
        # a hard repeat in its texture won every argument: `stalls` reached
        # cols 302-342, so the FOYER -- twenty tiles west of any seat -- came
        # back ruled with seat rows and read as corduroy. Four districts in one
        # region have to be laid out like four ROOMS, i.e. mostly disjoint, and
        # each has to sit under the vignette `place_keep.py` authors on it:
        # the-foyer (305,62), the-stalls (322,60), the-orchestra-pit (336,26),
        # the-marble-approach (320,40) -- and the boss himself at (308,41).
        ("foyer",     300,  64, 13, 11, 4, (0x4A, 0x3C, 0x30), 0.50),  # sodden carpet gone to brown silt -- the way in
        ("stalls",    326,  62, 14, 12, 4, (0x38, 0x33, 0x2E), 0.46),  # rows of seats under a century of silt
        ("orchpit",   336,  26, 15, 13, 4, (0x1C, 0x18, 0x14), 0.54),  # the orchestra pit: the deepest, darkest place in the hall
        ("marble",    314,  42, 12,  9, 4, (0xB6, 0xAE, 0x9E), 0.44),  # pale NEUTRAL marble, warmed by the lamps -- and it is the BOSS APPROACH, so it is centred between the boss (308,41) and the vignette (320,40)
    ]
    dmask = {}
    for row in AUTHORED:
        # an 8th field is an optional per-district `feather` (see `district`);
        # most places want the default, the Oasis wants a wider outskirt.
        name, cx, cy, rx, ry, reg, rgb, amt = row[:8]
        dmask[name] = district(cx, cy, rx, ry, reg, rgb, amt, *row[8:])

    # district signature TEXTURES -- each place reads distinct by MATERIAL, not
    # only tint. Keyed to the placed masks above (grass tiles only).
    def dtex(name):
        m = dmask.get(name)
        return (m & _gp) if m is not None and m.any() else None
    m = dtex("scorch")            # pale ASH cracks in the char (darkening a
    if m is not None:             # near-black zone is invisible -- lighten them)
        crk = (value_noise(PH, PW, 3) > 0.70) & m
        canvas[crk] = canvas[crk] * 0.55 + np.array((0x6E, 0x66, 0x5E), dtype=np.float32)[None, :] * 0.45
    m = dtex("tarpit")            # oily near-black seeps with a faint sheen
    if m is not None:
        seep = (value_noise(PH, PW, 20) > 0.6) & m
        canvas[seep] *= 0.55
        sheen = (value_noise(PH, PW, 20) > 0.82) & m
        canvas[sheen] = canvas[sheen] * 0.7 + np.array((0x3A, 0x40, 0x44), dtype=np.float32)[None, :] * 0.3
    m = dtex("basalt")            # angular columnar fracture (cool dark seams)
    if m is not None:
        seam = (np.abs(value_noise(PH, PW, 16) - 0.5) < 0.03) & m
        canvas[seam] = canvas[seam] * 0.6 + np.array((0x2A, 0x30, 0x38), dtype=np.float32)[None, :] * 0.4
    m = dtex("verdigris")         # mottled oxidised copper-green blotches
    if m is not None:
        blot_v = (value_noise(PH, PW, 12) > 0.62) & m
        canvas[blot_v] = canvas[blot_v] * 0.7 + np.array((0x58, 0x88, 0x68), dtype=np.float32)[None, :] * 0.3
    m = dtex("rustdunes")         # streaked oxide banding
    if m is not None:
        streak = (((yy_g * 0.5 + value_noise(PH, PW, 60) * 40) % 26) < 4) & m
        canvas[streak] = canvas[streak] * 0.82 + np.array((0xA8, 0x5C, 0x30), dtype=np.float32)[None, :] * 0.18
    m = dtex("sulfur")            # crusted yellow granules
    if m is not None:
        gr = (value_noise(PH, PW, 9) > 0.72) & m
        canvas[gr] = canvas[gr] * 0.7 + np.array((0x9E, 0x96, 0x40), dtype=np.float32)[None, :] * 0.3
    m = dtex("bloodmire")         # pooled dark water blots
    if m is not None:
        pool = (value_noise(PH, PW, 22) > 0.64) & m
        canvas[pool] = canvas[pool] * 0.5 + np.array((0x20, 0x10, 0x14), dtype=np.float32)[None, :] * 0.5
    m = dtex("boneyard")          # pale bone flecks in the bleached earth
    if m is not None:
        # ONE PERCENT OF PIXELS IS A SNOWFIELD. 1% of 256 pixels is two and a
        # half flecks per TILE, so the frame at (190,110) -- dead centre of this
        # district -- came back with about five hundred white dots in it, each
        # one clipped up to 232 on ground whose median is 81. That is the fourth
        # time a speck pass has shipped as snow (see the tuft densities in
        # `stamp_tufts` and the style contract's §4.4). Two things were wrong
        # and the district's own comment already said both: bone reads as bone
        # because it is DRIER than the earth, not brighter -- so the lift comes
        # down to a sixth of what it was -- and bone fragments lie in DRIFTS,
        # washed into hollows, so a coarse field decides where any of them are.
        drift = value_noise(PH, PW, 30)
        fleck = (RNG.random((PH, PW), dtype=np.float32) > 0.9975) & m & (drift > 0.58)
        canvas[fleck] = np.minimum(canvas[fleck] * 1.16 + 9, 186)
    m = dtex("saltpan")           # polygonal salt hex cracks
    if m is not None:
        canvas[crack_net(PH, PW, 34, 0.75) & m] *= 0.84
    m = dtex("geyserpan")         # pale mineral speckle
    if m is not None:
        spk = (value_noise(PH, PW, 8) > 0.74) & m
        canvas[spk] = np.minimum(canvas[spk] * 1.3 + 18, 225)
    m = dtex("kelpforest")        # dark frond mottle
    if m is not None:
        canvas[(value_noise(PH, PW, 18) > 0.66) & m] *= 0.78
    m = dtex("foyer")             # a sodden carpet's nap: soft directional mottle
    if m is not None:
        nap = value_noise(PH, PW, 26)
        canvas[m] = canvas[m] * (0.90 + nap[m][:, None] * 0.20)
    m = dtex("stalls")            # THE SEATS. Rows, because a theatre IS built --
    if m is not None:             # this is the one place a hard repeat is the
        # subject rather than a mistake (§4.5). It is still broken on two axes:
        # the row pitch wobbles with a low-frequency noise term, and a CENTRE
        # AISLE runs through, because a hall with no way to your seat is a grid.
        rowp = 7.0
        wob = (value_noise(PH, PW, 40) - 0.5) * 2.4
        phase = np.mod(yy_g + wob, rowp)
        seats = (phase < 2.6) & m
        aisle = np.abs(np.mod(xx_g + (value_noise(PH, PW, 60) - 0.5) * 9.0, 46.0) - 23.0) < 3.4
        canvas[seats & ~aisle] *= 0.74
        # a thin pale top-edge on each row: the light catches the seat backs
        lip = (phase >= 2.6) & (phase < 3.3) & m & ~aisle
        canvas[lip] = canvas[lip] * 0.82 + np.array((0x8E, 0x82, 0x6C), dtype=np.float32)[None, :] * 0.18
    m = dtex("orchpit")           # BRASS, glinting where the players drowned.
    if m is not None:             # Darkening a near-black district is invisible,
        # so the signature has to be light -- and the light that belongs here is
        # the one warm accent in the game, on instruments nobody came back for.
        glint = (value_noise(PH, PW, 2) > 0.938) & m
        canvas[glint] = canvas[glint] * 0.35 + np.array((0xC6, 0x98, 0x4E), dtype=np.float32)[None, :] * 0.65
        stand = (value_noise(PH, PW, 9) > 0.86) & m   # music stands, still up
        canvas[stand] = canvas[stand] * 0.72 + np.array((0x4C, 0x46, 0x3C), dtype=np.float32)[None, :] * 0.28
    m = dtex("marble")            # veining, warm-white, sparse and long
    if m is not None:
        vein = (np.abs(value_noise(PH, PW, 52) - 0.5) < 0.010) & m
        canvas[vein] = canvas[vein] * 0.62 + np.array((0xD0, 0xC9, 0xBC), dtype=np.float32)[None, :] * 0.38
    m = dtex("oasis")             # THE OASIS: living moss + a bright spring pool
    if m is not None:
        # bright living-green tufts (warm, unlike the cold drowned kelp).
        # A HARD THRESHOLD ON ONE NOISE FIELD IS CAMO. `noise(20) > 0.55` is a
        # binary mask, so 0.45 of a vivid chartreuse landed as SOLID PATCHES
        # with stepped edges -- a paint spill, and the last thing the one living
        # place in the region should look like. Moss is a COVERAGE, not a
        # region: it thickens and thins continuously, it is patchiest at its
        # own edge, and it is never one colour. So the alpha ramps through the
        # threshold instead of switching at it, a finer field breaks the fill
        # up so it stays mottled at reading distance, and the hue rides the
        # same fields -- thick moss greener, thin moss yellow and dying.
        tn = value_noise(PH, PW, 22)
        tf = value_noise(PH, PW, 6)
        cover = np.clip((tn - 0.44) / 0.30, 0.0, 1.0) * (0.42 + tf * 0.58)
        a = (cover[m] * 0.52)[:, None]
        wet = np.array((0x6A, 0x92, 0x3A), dtype=np.float32)[None, :]
        dry = np.array((0x84, 0x8C, 0x46), dtype=np.float32)[None, :]
        col_t = dry + (wet - dry) * (cover[m])[:, None]
        canvas[m] = canvas[m] * (1 - a) + col_t * a
        # a spring pool at its heart: clear water, the one place still alive.
        # WARPED, like every other water body in this file. The plain ellipse
        # this used to be was a clean geometric edge around a near-flat fill --
        # the same failure the pond pass was warped to fix ("map-rectangular
        # ponds kept reading as rounded RECTANGLES"), and it survived here
        # because the oasis is one hand-placed disc rather than a tile mask.
        # It also stacked three blends (district 0.66, tufts 0.45, pool 0.70)
        # which multiply the ground's variance down by ~18x, so the fill needs
        # its own grain back -- see THE FLAT-PATCH LAW (style-contract §4.3).
        # ...AND THE POOL DID NOT MOVE WITH THE DISTRICT. The clearing was
        # recentred on the spring at (237,130) and this stayed at (236,120):
        # eleven rows north, which on an 11-tile-tall camera is entirely
        # off-screen from the spring, so the painted pool sat on bare brown
        # outside the green and the sprite pool sat on unpainted ground. It is
        # under `oasis_spring` (238,131) now, and SMALLER than the sprite that
        # stands on it -- the paint is the wet ground around the water, not a
        # second pool competing with the first.
        ox, oy = 238 * S, 131 * S
        pd = ((xx_g - ox) / (3.4 * S)) ** 2 + ((yy_g - oy) / (2.2 * S)) ** 2 + (_warp - 0.5) * 0.42
        pool = (pd <= 1) & (region_px == 3)
        spring = np.array((0x2E, 0x6A, 0x74), dtype=np.float32)[None, None, :] * (
            1 + (n_hi - 0.5) * 0.14 + (grain - 0.5) * 0.10
        )[..., None]
        canvas[pool] = canvas[pool] * 0.3 + spring[pool] * 0.7
        # the pool DEEPENS toward the middle instead of being one flat sheet
        canvas[pool] *= (0.80 + 0.20 * np.clip(pd, 0, 1))[pool][:, None]
        rim = (np.abs(pd - 1) < 0.10) & (region_px == 3)
        reeds = np.array((0x8A, 0xA8, 0x54), dtype=np.float32)[None, None, :] * (
            1 + (n_hi - 0.5) * 0.20 + (grain - 0.5) * 0.14
        )[..., None]
        canvas[rim] = canvas[rim] * 0.5 + reeds[rim] * 0.5

    def stamp_tufts() -> None:
        """Individually hash-placed grass marks -- variation, not wallpaper."""
        ys, xs = np.where(kind == 0)
        # THE TUFT TIP WAS A SNOWFIELD. `lite = canvas * 1.35` on a plate whose
        # median is 79 lands at 154, and 154 next to 79 is not a highlight, it
        # is a WHITE DOT -- forty-three of them per ten tiles, which in a 20x11
        # camera is ninety-five specks of lens dust over the whole world. Worse
        # in the Scar, where the ground is meant to be dead earth and a tuft of
        # grass is a lie: region 3 now keeps a twentieth of them, the Keep a
        # third (a flooded marble floor grows very little), and the Fold keeps
        # all of them because a water-meadow is the one place turf belongs.
        TUFT_DENSITY = (55, 44, 40, 4, 16)
        for ty, tx in zip(ys, xs):
            h = (tx * 73856093 ^ ty * 19349663) & 0xFFFFFFFF
            if h % 100 >= TUFT_DENSITY[region[ty, tx]]:
                continue
            cx, cy = tx * S + (h >> 8) % S, ty * S + (h >> 16) % S
            dark = canvas[cy % PH, cx % PW] * 0.72
            lite = canvas[cy % PH, cx % PW] * 1.12 + 6.0
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
    # The mud-crack web -- see `crack_net`, which explains why this is a
    # Voronoi edge set and not the `abs(noise - 0.5)` isocontour it was twice.
    # Two scales, because a dried pan cracks large first and then the plates
    # craze inside themselves, and the coarse net is darker than the fine one.
    # A second COARSE field still decides WHERE: mud only cracks where mud
    # pooled, and a texture that covers everything uniformly is not a texture.
    #
    # THE FINE NET SHIPPED AS BURLAP. Both scales were plain jittered grids, so
    # every plate came out ~one size and the whole Scar tiled as woven canvas
    # (measured: the fine net blanketed ~38% of the region at a single 15px
    # pitch). Earth does not have one pitch. So both nets now break their grid
    # -- `density` merges a third of the plates into bigger irregular ones,
    # `aspect` stretches them off square, `warp` bends the rows -- and the fine
    # craze is pulled back to genuine PATCHES: gated by two independent coarse
    # fields multiplied together, it lands only where a plate actually dried and
    # crazed inside itself, not as an all-over weave.
    crack_where = value_noise(PH, PW, 26)
    crack_patch = value_noise(PH, PW, 19)
    canvas[r_mask & crack_net(PH, PW, 44, 0.80, density=0.7, aspect=1.35, warp=0.5)
           & (crack_where > 0.42)] *= 0.72
    canvas[r_mask & crack_net(PH, PW, 17, 0.55, density=0.62, aspect=0.72, warp=0.7)
           & (crack_where > 0.60) & (crack_patch > 0.60)] *= 0.88
    ys_v, xs_v = np.where(r_mask[::56, ::56])
    ember = np.array(ACCENTS[3], dtype=np.float32)
    for vy, vx in zip(ys_v * 56, xs_v * 56):
        h = (int(vx) * 40503 ^ int(vy) * 19349663) & 0xFFFFFFFF
        cy0, cx0 = int(vy) + (h >> 9) % 40, int(vx) + (h >> 4) % 40
        if h % 100 < 6:  # claw gouge
            # THREE RULER-STRAIGHT PARALLEL DIAGONALS AT 45 DEGREES IS
            # HATCHING, not a claw mark -- the Scar shipped looking pencilled.
            # A claw drags: the strokes SPLAY (a paw is not a comb), they curve
            # with the pull, and they taper out at the end because the animal
            # lifted. Deepest at the start, gone by the tip.
            ang = (h >> 11) % 360 * math.pi / 180.0
            ln = 13 + h % 9
            for k in (-1, 0, 1):
                spread = 0.34 * k
                for d in range(ln):
                    t = d / float(ln)
                    a = ang + spread * (0.35 + t * 0.9)
                    y = cy0 + int(math.sin(a) * d) + int(k * 3 * math.cos(ang))
                    x = cx0 + int(math.cos(a) * d) - int(k * 3 * math.sin(ang))
                    if 0 <= y < PH and 0 <= x < PW and r_mask[y, x]:
                        canvas[y, x] *= 0.55 + 0.42 * t * t
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
    wvx, wvy = 267 * S, 172 * S
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
    fox, foy = 146 * S, 131 * S
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
    srx, sry = 248 * S, 63 * S
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
    dlx, dly = 299 * S, 125 * S
    pan = (((xx_g - dlx) / 90.0) ** 2 + ((yy_g - dly) / 55.0) ** 2 <= 1) & grass_px & (region_px == 3)
    pan_c = np.array((0x9A, 0x8C, 0x74), dtype=np.float32)
    canvas[pan] = canvas[pan] * 0.4 + pan_c[None, :] * 0.6
    pan_crack = pan & crack_net(PH, PW, 38, 0.80)
    canvas[pan_crack] *= 0.70
    rim = (np.abs(((xx_g - dlx) / 90.0) ** 2 + ((yy_g - dly) / 55.0) ** 2 - 1) < 0.06) & grass_px & (region_px == 3)
    canvas[rim] *= 0.78

    # --- v13.2: MANY more one-offs -- the map earns places you remember ------
    def blot(cx: int, cy: int, rx: int, ry: int, col: tuple, amt: float, only_reg=None) -> None:
        sl_y, sl_x = slice(max(0, cy - ry), cy + ry + 1), slice(max(0, cx - rx), cx + rx + 1)
        sub = canvas[sl_y, sl_x]
        yy_o, xx_o = np.ogrid[-ry : ry + 1, -rx : rx + 1]
        m = (xx_o / max(1, rx)) ** 2 + (yy_o / max(1, ry)) ** 2 <= 1
        gm = grass_px[sl_y, sl_x]
        if m.shape != sub.shape[:2]:
            return
        keep = m & gm
        if only_reg is not None:
            keep &= region_px[sl_y, sl_x] == only_reg
        c = np.array(col, dtype=np.float32)
        sub[keep] = sub[keep] * (1 - amt) + c[None, :] * amt

    # THE GREAT WRECK: a colossal ship's hull run aground on the Breach shore
    gwx, gwy = 127 * S, 63 * S
    for d in range(200):  # the keel
        y, x = gwy + int(24 * np.sin(d / 120.0)), gwx - 100 + d
        if clip_ok(y, x):
            canvas[y : y + 3, x] = canvas[y : y + 3, x] * 0.4 + np.array((0x3A, 0x2C, 0x22), dtype=np.float32) * 0.6
    for hb in range(-90, 91, 6):  # hull ribs curving up from the keel
        rh = int(30 * (1 - (hb / 90.0) ** 2))
        for d in range(rh):
            y, x = gwy + int(24 * np.sin(hb / 120.0)) - d, gwx + hb + int(d * hb / 200.0)
            if clip_ok(y, x):
                canvas[y, x] = canvas[y, x] * 0.45 + np.array((0x52, 0x3E, 0x30), dtype=np.float32) * 0.55
    for m in range(3):  # broken masts fallen forward
        mx = gwx - 40 + m * 40
        for d in range(40):
            y, x = gwy - 30 - d // 2, mx + d
            if clip_ok(y, x):
                canvas[y, x] *= 0.6

    # THE BONEYARD: a battlefield of the fallen, west-central Scar
    for k in range(60):
        h = (k * 2654435761) & 0xFFFFFFFF
        bx, by = 178 * S + ((h >> 3) % 400 - 200), 106 * S + ((h >> 13) % 260 - 130)
        if not clip_ok(by, bx) or region_px[by, bx] != 3:
            continue
        if h % 3 == 0:  # a ribcage
            for rib in range(-3, 4):
                for d in range(5):
                    y, x = by - d, bx + rib * 3 + int(d * 0.4 * (1 if rib > 0 else -1))
                    if clip_ok(y, x):
                        canvas[y, x] = canvas[y, x] * 0.4 + np.array((0xC4, 0xBD, 0xA4), dtype=np.float32) * 0.6
        else:  # scattered long bones
            ln = 4 + h % 6
            ang = (h % 628) / 100.0
            for d in range(ln):
                y, x = by + int(d * np.sin(ang)), bx + int(d * np.cos(ang))
                if clip_ok(y, x):
                    canvas[y, x] = canvas[y, x] * 0.45 + np.array((0xC4, 0xBD, 0xA4), dtype=np.float32) * 0.55

    # THE GEYSER FIELD: pale mineral pools ringed with crust, north Scar
    for k in range(7):
        gx, gy = 203 * S + (k * 47 % 240 - 120), 38 * S + (k * 71 % 130 - 65)
        if clip_ok(gy, gx) and region_px[gy, gx] == 3:
            blot(gx, gy, 9 + k % 5, 7 + k % 4, (0x8C, 0x9A, 0x86), 0.55, only_reg=3)
            blot(gx, gy, 4 + k % 3, 3 + k % 2, (0x6C, 0xA8, 0x9E), 0.6, only_reg=3)  # the hot centre
            ring = (np.abs(np.sqrt((xx_g - gx) ** 2 + (yy_g - gy) ** 2) - (11 + k % 4)) < 1.4) & grass_px & (region_px == 3)
            canvas[ring] = canvas[ring] * 0.4 + np.array((0xD2, 0xCE, 0xBE), dtype=np.float32)[None, :] * 0.6

    # THE MAST FOREST: dead ships' masts standing in the drowned Shelf like trees
    for k in range(16):
        h = (k * 40503 + 991) & 0xFFFFFFFF
        mx, my = 57 * S + ((h >> 4) % 360 - 180), 63 * S + ((h >> 12) % 360 - 180)
        if not clip_ok(my, mx) or region_px[my, mx] != 1:
            continue
        mh = 20 + h % 26
        lean = ((h >> 3) % 5) - 2
        for d in range(mh):
            y, x = my - d, mx + int(d * lean / mh)
            if clip_ok(y, x):
                canvas[y, x] = canvas[y, x] * 0.5 + np.array((0x2A, 0x22, 0x1C), dtype=np.float32) * 0.5
        for yard in (int(mh * 0.6), int(mh * 0.85)):  # cross-spars
            for dx in range(-5, 6):
                y, x = my - yard, mx + dx + int(yard * lean / mh)
                if clip_ok(y, x):
                    canvas[y, x] = canvas[y, x] * 0.55 + np.array((0x2A, 0x22, 0x1C), dtype=np.float32) * 0.45

    # THE GIANT FOOTPRINT: one vast three-toed track pressed into the east Scar
    fpx, fpy = 318 * S, 156 * S
    heel = (((xx_g - fpx) / 28.0) ** 2 + ((yy_g - fpy) / 34.0) ** 2 <= 1) & grass_px & (region_px == 3)
    canvas[heel] *= 0.62
    for toe_a in (-0.6, 0.0, 0.6):
        tx, ty = int(fpx + 40 * np.sin(toe_a)), int(fpy - 40 * np.cos(toe_a))
        blot(tx, ty, 10, 14, (0x2E, 0x1C, 0x16), 0.45, only_reg=3)

    # THE SALT FLATS: a blinding pale crust plain, far south Scar
    sfx, sfy = 216 * S, 188 * S
    flat = (((xx_g - sfx) / 130.0) ** 2 + ((yy_g - sfy) / 34.0) ** 2 <= 1) & grass_px & (region_px == 3)
    canvas[flat] = canvas[flat] * 0.35 + np.array((0xC6, 0xC2, 0xB4), dtype=np.float32)[None, :] * 0.65
    hexc = flat & crack_net(PH, PW, 30, 0.70)  # polygonal salt cracks -- a real tessellation
    canvas[hexc] *= 0.82

    # THE SPIRE RUIN: a toppled lighthouse's round base + shadow, NE Scar edge
    spx, spy = 286 * S, 94 * S
    base = (np.sqrt((xx_g - spx) ** 2 + (yy_g - spy) ** 2) < 16) & grass_px & (region_px == 3)
    canvas[base] = canvas[base] * 0.5 + np.array((0x6E, 0x66, 0x5E), dtype=np.float32)[None, :] * 0.5
    inner = (np.sqrt((xx_g - spx) ** 2 + (yy_g - spy) ** 2) < 8) & grass_px & (region_px == 3)
    canvas[inner] *= 0.7  # the hollow shaft
    for d in range(70):  # the fallen tower lying east
        y, x = spy + d // 6, spx + 16 + d
        if clip_ok(y, x) and region_px[y, x] == 3:
            canvas[y : y + 5, x] = canvas[y : y + 5, x] * 0.55 + np.array((0x6E, 0x66, 0x5E), dtype=np.float32) * 0.45

    # r4 hall: marble veining -- AND IT WAS A CONTOUR DOODLE, at cell 55, which
    # is a seventy-metre cell on a 5696px plate. What shipped was three or four
    # pale lavender ribbons wandering across the entire region like chalk on a
    # blackboard, and in a browser capture of the orchestra pit they read as worm
    # trails. Third instance of the same mistake (the Scar's mud cracks at cell
    # 30, the dried pan at 22), and it is now a law in the style contract: AN
    # ISOCONTOUR OF A COARSE NOISE FIELD IS A DOODLE GENERATOR.
    #
    # Real marble veining is FINE, BRANCHING and UNEVENLY DISTRIBUTED -- some
    # slabs are almost clean and the one next to it is a thunderstorm. So: a fine
    # field for the vein shape, a coarse one to decide which stretches of floor
    # are veined at all, and a third of the old strength, because 0.30 of a
    # near-white over a lum-58 floor is not a vein, it is a paint stripe.
    # ...and then the isocontour came back a THIRD time, at cell 4 and cell 7,
    # which is fine enough that it stops being dashes and becomes 1px CONFETTI:
    # not veining, just pale speckle. Marble veining is a healed FRACTURE
    # NETWORK -- calcite filling cracks -- so it is the same object as the
    # Scar's dried mud, only far larger and lighter. `crack_net` builds it as a
    # tessellation edge set, which branches and closes; two scales, and a
    # coarse field still deciding which stretches of floor are veined at all,
    # because some slabs are almost clean and the one beside it is a storm.
    r_mask = grass_px & (region_px == 4)
    vein_where = value_noise(PH, PW, 30)
    mix(r_mask & crack_net(PH, PW, 96, 0.60) & (vein_where > 0.44),
        (0xC9, 0xC4, 0xD4), 0.13)
    mix(r_mask & crack_net(PH, PW, 34, 0.45) & (vein_where > 0.60),
        (0x9A, 0x9E, 0xB2), 0.10)

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
        # ...and the island's OWN edge was the tell. `island_tiles` is a disc
        # of radius 4.7 tiles clipped to walkable ground, so it is nearly
        # rectangular after the clip, and jitter 0.24 at blur 9 moves the
        # boundary about four pixels -- which rounds the corners of a 150px
        # mass and leaves its four flat sides. Worse, the island is surrounded
        # by water, so the shoreline's distance bands trace that outline again
        # one ring further out: a browser capture at (320,40) came back with a
        # grey rounded RECTANGLE inside a second grey rounded rectangle, which
        # is the last thing the approach to the game's final room should be.
        # A big warp on the source mask chews the outline and every band that
        # follows it inherits the chew for free.
        stage_px = organic_mask(island_tiles, jitter=0.24, blur=9, warp=0.90)
        stone = tint((0x6C, 0x67, 0x6A), ACCENTS[4], 0.18)  # neutral marble, warmed by the accent
        scol = stone[None, None, :] * (1 + (n_low - 0.5) * 0.18 + (n_mid - 0.5) * 0.12 + (n_hi - 0.5) * 0.08)[..., None]
        scol = scol * (1 + (grain - 0.5) * 0.10)[..., None]
        canvas[stage_px] = scol[stage_px]
        # the hall's marble veining, a little denser on the stone itself
        vein_s = value_noise(PH, PW, 48)
        vm = stage_px & (np.abs(vein_s - 0.5) < 0.007)
        canvas[vm] = canvas[vm] * 0.6 + np.array((0xD0, 0xC9, 0xBC), dtype=np.float32)[None, :] * 0.4

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
    # --- the Fold's WALLED YARDS get floors (v16.6) --------------------------
    # What was here: 14 hash-placed "hut foundations", each a hard axis-aligned
    # rectangle of pale silt with a 1px dark outline. Two things were wrong with
    # them. They read as literal BOXES -- the one shape this file warps every
    # other border to avoid -- and they predated the Fold having any
    # architecture, so once the town kit landed (M2) a ghost foundation could
    # sit squarely under a standing house. A ruin among houses that are lit and
    # occupied is not a story, it is a mistake.
    #
    # What is here instead: the map ALREADY contains walled yards. The
    # generator laid hollow rectangles of rock around the Fold -- (17-21,
    # 166-170), (30-34, 162-166), (26-30, 177-181) -- and nothing had ever been
    # drawn inside them. So find every enclosed pocket of open ground in the
    # Fold and floor it: packed silt, worn toward the middle where people
    # actually walk, with a warped organic border like everything else. The
    # walls were always there; now they contain somewhere.
    #
    # The pockets are DERIVED, not listed: flood-fill the open tiles inward from
    # the Fold's border, and anything the fill cannot reach is enclosed. That
    # way a yard the generator adds later gets a floor for free, and one it
    # removes stops being painted.
    r0 = region == 0
    if r0.any():
        rs, cs = np.where(r0)
        r_lo, r_hi, c_lo, c_hi = rs.min(), rs.max(), cs.min(), cs.max()
        open_t = (kind != 3) & r0
        seen = np.zeros_like(open_t)
        stack = []
        for _r in range(r_lo, r_hi + 1):
            for _c in (c_lo, c_hi):
                if open_t[_r, _c]:
                    stack.append((_r, _c))
        for _c in range(c_lo, c_hi + 1):
            for _r in (r_lo, r_hi):
                if open_t[_r, _c]:
                    stack.append((_r, _c))
        for _r, _c in stack:
            seen[_r, _c] = True
        while stack:
            _r, _c = stack.pop()
            for _nr, _nc in ((_r - 1, _c), (_r + 1, _c), (_r, _c - 1), (_r, _c + 1)):
                if r_lo <= _nr <= r_hi and c_lo <= _nc <= c_hi and open_t[_nr, _nc] and not seen[_nr, _nc]:
                    seen[_nr, _nc] = True
                    stack.append((_nr, _nc))
        yards = open_t & ~seen & (kind == 0)
        if yards.any():
            yard_px = organic_mask(yards, jitter=0.20, blur=7, warp=0.35)
            yard_px &= grass_px & ~plaza_px
            # packed silt, a touch darker than the plaza: a yard is private
            # ground, swept but not walked by a whole town
            ycol = silt[None, None, :] * 0.86
            ycol = ycol * (1 + (n_mid - 0.5) * 0.12 + (n_hi - 0.5) * 0.10 + (grain - 0.5) * 0.10)[..., None]
            canvas[yard_px] = canvas[yard_px] * 0.22 + ycol[yard_px] * 0.78
            # wear toward the middle of each yard -- feet, not a texture
            d_y = distance_bands(yard_px, 5)
            canvas[yard_px & (d_y > 6)] *= 1.06
            canvas[yard_px & (d_y < 2)] *= 0.9
            print("  fold yards: %d enclosed tiles floored" % int(yards.sum()))

    # --- the town obelisk's dais + cast shadow + focus rings (v14.0) ---------
    # The massive monolith (drawn at runtime by OverworldScene.placeTownObelisk)
    # stands on worked stone at the plaza heart; the town circles IT. Painted
    # here so the ground under the structure reads as a real prayer platform,
    # not turf. Kept in sync with the "town_obelisk" marker.
    _tob = next((o for o in _markers0 if o["name"] == "town_obelisk"), None)
    if _tob is not None:
        obx, oby = int(_tob["x"] // 16) * S + S // 2, int(_tob["y"] // 16) * S + S // 2
        rr_ob = np.sqrt((xx_g - obx) ** 2 + (yy_g - oby) ** 2)
        # a long shadow cast SE across the plaza, as if from the tall stone
        shadow = (((xx_g - obx - 30) / 46.0) ** 2 + ((yy_g - oby - 16) / 20.0) ** 2 <= 1) & grass_px
        canvas[shadow] *= 0.7
        # the worked stone dais: a bluer, darker platform under the base
        dais_stone = tint((0x28, 0x34, 0x3E), ACCENTS[0], 0.10)
        dcol = dais_stone[None, None, :] * (1 + (n_mid - 0.5) * 0.12 + (grain - 0.5) * 0.10)[..., None]
        dais = (rr_ob < 30) & grass_px
        canvas[dais] = dcol[dais]
        rim = (np.abs(rr_ob - 29.0) < 2.0) & grass_px
        canvas[rim] *= 0.72  # a stepped edge to the platform
        # worn prayer-focus rings the worshippers have circled for generations
        for radius in (46.0, 66.0, 88.0):
            focus = (np.abs(rr_ob - radius) < 1.3) & grass_px & (rr_ob > 30)
            canvas[focus] *= 0.8

    # --- prayer rings at every save-obelisk (v12.0) --------------------------
    # The Fold's faith marks the whole ascent. Mirrors OverworldScene's
    # deterministic obelisk placement (first walkable of fixed candidates).
    def _walk(c, r):
        return 0 <= c < W and 0 <= r < H and kind[r, c] in (0, 1)
    node_names = {o["name"] for o in _markers0 if o["name"] not in ("spawn", "town_obelisk")}
    for o in _markers0:
        if o["name"] in ("spawn", "town_obelisk"):
            continue  # the town obelisk gets its own dais + focus rings above
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
    # THE ROAD IS THE SAME MATERIAL EVERYWHERE and that is why it kept being
    # the warmest thing in whatever frame it crossed -- a 0x8E837 tan at only
    # 0.18 of the region accent stayed tan in the Breach, where it read as a
    # strip of holiday beach laid through a cold foreshore. Packed earth still,
    # but cooler and pulled harder toward whatever region it runs through: the
    # Breach's road is grey-green shingle, the Scar's is rust.
    # ...AND IT WAS STILL THE BRIGHTEST LARGE FIELD IN EVERY FRAME IT CROSSED.
    # Cooling it fixed the Breach's holiday-beach problem and left the other
    # half: measured, the road ran ~33 luminance over the ground beside it,
    # which on a 20-tile-wide camera is a pale band down the middle of the shot
    # competing with the festoon bulbs and the dig lamps -- the two things §3
    # reserves brightness for. A road needs to be READABLE, not bright. Twelve
    # luminance over the ground plus its own texture is plenty; a path in a
    # drowned world is packed dirt, and packed dirt is darker than loose.
    path_bases = [tint((0x6A, 0x66, 0x5A), a, 0.24) for a in ACCENTS]
    # full overwrite below (`canvas[path_mask] = path_col[...]`), so the road
    # owes the grain back too -- see THE FLAT-PATCH LAW above.
    path_col = blended(path_bases) * (
        1 + (n_mid - 0.5) * 0.12 + (n_hi - 0.5) * 0.10 + (grain - 0.5) * 0.09
    )[..., None]
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
    # THE KEEP'S ROAD IS AN AISLE, AND AN AISLE IS NOT PACKED DIRT. `path_col`
    # is a khaki (0x6A665A pulled a quarter toward the gilt accent), and mixing
    # 0.3 of lavender into khaki leaves khaki -- so the hall's two processional
    # runs arrived as wide olive bands ruled dead straight across the frame, the
    # warmest and second-brightest thing in the only cool region in the game.
    # Overwrite instead of mixing, keep it barely above the floor in value, and
    # let it stay STRAIGHT: this is the one region built by people with money,
    # and a straight axis is the thing their money bought.
    paved_road = path_mask & (region_px == 4)
    aisle_col = np.array((0x4C, 0x4A, 0x56), dtype=np.float32)[None, None, :] * (
        1 + (n_mid - 0.5) * 0.10 + (grain - 0.5) * 0.09
    )[..., None]
    canvas[paved_road] = aisle_col[paved_road]
    canvas[paved_road & (d_path < 3)] *= 0.80

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
    # water is smoother than ground, but not FLAT (THE FLAT-PATCH LAW): this is
    # a full overwrite as well, and a still pool with zero variance reads as a
    # hole cut in the plate.
    water_col *= (1 + (n_mid - 0.5) * 0.08 + (n_hi - 0.5) * 0.05 + (grain - 0.5) * 0.05)[..., None]
    canvas[water_mask] = water_col[water_mask]

    # v13.2 river current: a flowing sheen streaking along Scar/Breach water
    flow = value_noise(PH, PW, 40)
    river_w = water_mask & (region_px == 3)
    streak = river_w & (((xx_g * 0.6 + yy_g + flow * 30).astype(np.int32) % 14) < 2)
    canvas[streak] = np.minimum(canvas[streak] * 1.4, 255)
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
        # THE VILLAGE WENT UNDER; THE SCAR NEVER HAD ONE. This used to leak into
        # regions 2 and 3 at one tile in five (`and h % 5 != 0`), which put a
        # pale gabled ROOFTOP WITH A CHIMNEY in the middle of the exposed
        # seabed -- and blurred by two pixels at 52% over a bright ghost tone,
        # what the shipped frame at (190,110) actually contained was a
        # three-pointed pale apparition with a face in it, sitting in a puddle
        # a hundred and fifty tiles from the nearest building. §6.3 is explicit
        # that the waterline is at the Breach: everything WEST of it drowned and
        # everything east of it was never wet. A house under water east of the
        # waterline is not atmosphere, it is a contradiction.
        if reg not in (0, 1, 4):
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
        # A two-pixel blur at 52% is a DECAL, not a drowned thing. These shapes
        # are hard-edged filled triangles and rectangles; the world then renders
        # them smooth-scaled at 4x, so two pixels of softening buys nothing and
        # the rooftops read as pale stencils laid on the water rather than
        # objects underneath it. Five pixels and a third less opacity: still
        # legible as a roof once you look, and no longer the first thing you see.
        overlay = np.asarray(Image.fromarray((overlay * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(5)), dtype=np.float32) / 255.0
        depth_fade = np.clip(1.0 - d_w / 34.0, 0.45, 1.0)
        a = (overlay * 0.34 * depth_fade)[..., None] * water_mask[..., None]
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

    # THE SCAR'S MESAS CAME BACK PINK. One base for all five regions -- a cool
    # blue-grey 0x4A515E -- pulled 30% toward each region's accent. That works
    # for four of them, because four accents are cold or warm-neutral. Region
    # 3's accent is a red-orange ember, and blue-grey lerped a third of the way
    # to red-orange is MAUVE: measured (110,80,77) on the shipped plate, which
    # is the exact hue this project's palette gate exists to keep out, arriving
    # through the back door because nobody lerps toward purple on purpose.
    #
    # The lesson is the one the ground bases already learned twice (the Breach's
    # sand, the Scar's orange): you cannot fix a base by tinting it. Mixing
    # complementaries always lands in the middle of the wheel. So the rock has a
    # base PER REGION -- the four cold regions keep the blue-grey they were
    # already resolving to, and the Scar gets warm dark stone that does not need
    # dragging anywhere -- and it takes the same eighth-strength accent the
    # Scar's ground does.
    ROCK_BASES = [(0x4A, 0x51, 0x5E), (0x46, 0x51, 0x5A), (0x50, 0x58, 0x5C),
                  (0x4C, 0x44, 0x40), (0x4A, 0x4C, 0x54)]
    ROCK_TINTS = [0.30, 0.30, 0.30, 0.08, 0.07]
    rock_top_bases = [tint(b, a, t) for b, a, t in zip(ROCK_BASES, ACCENTS, ROCK_TINTS)]
    rock_top = blended(rock_top_bases)
    crack_col = 0.5
    mesa_px = np.zeros((PH, PW), dtype=bool)  # union, so later passes respect the mesas
    # v15.0 perf: skip tiny rock specks CHEAPLY (one bincount) before the
    # per-component full-canvas organic_mask. On the ~10x map the thousands of
    # single-tile scattered rocks were each triggering an 18M-px blur -> a
    # ~20-minute bake. Only real clusters (>=4 tiles) become mesas.
    comp_sizes = np.bincount(labels.ravel(), minlength=nxt + 1)
    for comp in range(1, nxt + 1):
        if comp_sizes[comp] < 4:
            continue
        # A SMALL RECTANGLE NEEDS PROPORTIONALLY MORE CHEW THAN A BIG ONE.
        # The tilemap really does contain rectangular rubble blobs -- there is
        # a solid 5x3 of them at (230,127) -- and `blur=8, jitter=0.34` moves
        # the boundary about five pixels, which on an 80px-wide mass rounds the
        # corners and leaves the four flat sides intact: a rounded rectangle of
        # grey stone sitting in the Oasis. Amplitude has to scale against the
        # component's own size, so small clusters get warped until they break.
        cm = organic_mask(labels == comp, jitter=0.34, blur=8,
                          warp=1.05 if comp_sizes[comp] < 14 else 0.62)
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
    # A FLOOR cool-wash covers the WHOLE drowned territory the moment you're
    # west of the waterline (w01 > 0.5) -- so the Shelf reads submerged, not a
    # sunlit meadow -- PLUS a depth ramp that keeps deepening toward the Fold
    # core. The two together make the Fold->Shelf seam a gradual seafloor slope
    # instead of an underwater->grass jump.
    submerged = np.clip((w01 - 0.5) / 0.05, 0.0, 1.0)      # 0 at the waterline -> 1 just inside
    depth_u = np.clip((w01 - 0.5) / 0.24, 0.0, 1.0)        # continues deepening to the Fold
    deep_sea = np.array((0x12, 0x30, 0x3A), dtype=np.float32)
    wash = (submerged * 0.18 + depth_u * 0.14)[..., None]
    canvas = canvas * (1 - wash) + deep_sea[None, None, :] * wash
    # (v12.1 -- owner: "why are we still placing shit on-top of everything":
    # the caustic-web + sediment overlay crossed every material at uniform
    # strength and read as a decal layer; deleted. The depth grade, the
    # region materials, the drowned shapes, and the waterline say
    # "underwater" without painting a pattern over the world.)
    # the foam seam, broken (never a solid rule) -- and the wet band beyond it
    # A ONE-PIXEL SEAM IS A SCRATCH, NOT A WATERLINE. This was
    # `seam_d < 0.012` composited at 65% toward 0xD9F2EA -- a near-solid
    # one-pixel stroke, and the world renders at RENDER_SCALE 4, so what
    # crossed the frame was a four-pixel hard white ribbon that read as a
    # scratch on the film. It is the most important line in the geography
    # (§6.3: Mir crosses it and takes his first breath of surface air), so it
    # gets to be surf: a band two and a half times wider, falling off from the
    # seam, torn open by a finer noise, and never brighter than 62%.
    seam_d = np.abs(w01 - 0.5)
    FOAM_W = 0.030
    foam_n = value_noise(PH, PW, 9)
    foam_m = (seam_d < FOAM_W) & ~water_mask
    fs = (np.clip(1.0 - seam_d[foam_m] / FOAM_W, 0, 1) ** 1.6
          * np.clip((foam_n[foam_m] - 0.34) / 0.30, 0, 1) * 0.62)[:, None]
    canvas[foam_m] = (canvas[foam_m] * (1 - fs)
                      + np.array((0xD2, 0xE6, 0xE0), dtype=np.float32)[None, :] * fs)
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

    # The gaits Nari's signature has to be READ AGAINST. Defined here rather
    # than beside the pilgrim/decoy placement below, because the three-stretch
    # pass in the taking block needs them and Python does not hoist a nested def.
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
    # --- HER STRIDE, and why the ground has to contradict Mir ----------------
    # world-bible §6.3, the taking: "No blood. No struggle worth the name. Nari
    # did not cry out." Mir reads AMBUSH; "the ground reads otherwise, and the
    # player gets every piece." §6.4: "beside the small ones always a woman's
    # stride -- NOT CHASING. LEADING." And: "The player should be ahead of him
    # and should hate it."
    #
    # WHAT WAS HERE BEFORE, AND WHY IT BROKE THE STORY. The taking was staged as
    # twelve prints circling in panic plus a 26px DRAG MARK hauling off the road.
    # A drag mark says the boy was taken by force. Circling says he struggled.
    # So the most important piece of evidence in the game was corroborating the
    # WRONG THEORY -- the ground was agreeing with Mir, and the entire reversal
    # at the Den depends on it having quietly disagreed with him the whole time.
    # No woman's stride existed anywhere on the map at all.
    #
    # HER PRINTS ARE THE OPPOSITE OF VIOLENCE, and that is what makes them
    # unbearable: narrow, evenly spaced, LIGHT (0.78 against Nari's 0.62 -- she
    # barely presses), no heel gouge, no scuff, no skid. Nobody who is dragging
    # a child walks like this. She is not in a hurry, because she does not think
    # she is doing anything wrong.
    def woman_print(py: int, px: int, lead: bool = False) -> None:
        """A narrow adult sole, set down gently. `lead` marks the prints that
        sit AHEAD of the small ones in the direction of travel -- the tell. A
        pursuer's prints fall behind the child's. Hers are in front, the whole
        way, because he was following her."""
        if 1 <= py < PH - 4 and 1 <= px < PW - 2 and not water_mask[py, px]:
            canvas[py : py + 3, px] *= 0.78          # narrow sole, light pressure
            canvas[py : py + 2, px + 1] *= 0.86      # the ball of the foot only
            if lead:
                canvas[py + 3, px] *= 0.90           # a whisper of a heel

    if loss_idx < len(route):
        ty, tx = route[loss_idx]
        nyi = min(loss_idx + 1, len(route) - 1)
        dy, dx = route[nyi][0] - ty, route[nyi][1] - tx
        cx, cy = tx * S + S // 2, ty * S + S // 2

        # SHE WAS ALREADY UP HERE. §6.3: "a second adult set of prints reaches
        # the surface AHEAD of theirs." Her trail runs BACKWARD from the taking
        # for a stretch, so a player who turns around finds she arrived first --
        # the clue is available before the loss, not only after it.
        for k in range(14):
            back = -k * 13 - 8
            lat = 4 if k % 2 else -4
            woman_print(cy + dy * back + dx * lat, cx + dx * back + dy * lat, lead=True)

        # THE TAKING: "two feet, then one, then none."
        # Rendered literally, because the line is already the picture. Nari's
        # paired gait arrives, closes to both feet together where he stopped and
        # waited, then one last single print, then bare ground. Nothing is
        # dragged and nothing circles.
        stamp_print(cy - dy * 8 - dx * 3, cx - dx * 8 + dy * 3, drag=True)   # ...still walking
        stamp_print(cy - dy * 8 + dx * 3, cx - dx * 8 - dy * 3)              # two feet: he stops
        stamp_print(cy - dy * 2 + dx * 2, cx - dx * 2 - dy * 2)              # then one
        # then none. The absence is the event.

        # and hers, turning here and leaving with him. Evenly spaced: she walked.
        for k in range(9):
            ahead = k * 12 + 6
            lat = 4 if k % 2 else -4
            woman_print(cy + dy * ahead + dx * lat, cx + dx * ahead + dy * lat, lead=True)

        # --- the three stretches (§6.4) --------------------------------------
        # "the fresh trail (clear prints, hope with teeth), the false trails
        # (pilgrim strides, den-thing gaits, decoys that double back), and the
        # den's mouth (all tracks lead one way, none lead back)."
        #
        # The trail used to be one uniform sparse dribble of single prints every
        # 24 route steps, all the way to the boss. A search that reads the same
        # at the start, the middle and the end is not a progression -- and the
        # walk back out of the Scar is supposed to feel different from the walk
        # in. So the density, the pairing and the decoy load all change with
        # distance, and HER stride is beside the small ones in every stretch.
        tail = len(route) - 1
        span = max(1, tail - loss_idx)
        for i in range(loss_idx + 4, tail, 4):
            t = (i - loss_idx) / float(span)          # 0 at the taking, 1 at the den
            ty2, tx2 = route[i]
            n2 = route[min(i + 1, tail)]
            dy2, dx2 = n2[0] - ty2, n2[1] - tx2
            h2 = (tx2 * 40503 ^ ty2 * 2654435761) & 0xFFFFFFFF
            cy2, cx2 = ty2 * S + S // 2, tx2 * S + S // 2

            if t < 0.34:
                # STRETCH 1 -- the fresh trail. Clear, close-spaced, paired, and
                # her stride right alongside. This is the stretch that gives the
                # player the gait to learn, so it has to be unambiguous.
                for k in range(4):
                    lat = 3 if k % 2 else -3
                    stamp_print(cy2 + dy2 * k * 7 + dx2 * lat, cx2 + dx2 * k * 7 + dy2 * lat,
                                drag=k % 2 == 0)
                if h2 % 3:
                    woman_print(cy2 + dx2 * 7, cx2 + dy2 * 7, lead=True)
            elif t < 0.72:
                # STRETCH 2 -- the false trails. His prints thin out and the
                # ground fills with OTHER gaits. The decoys DOUBLE BACK, which
                # is the cruel part: a doubling-back trail is what a lost child
                # would leave, so it is the one Mir most wants to believe.
                if h2 % 4 == 0:
                    for k in range(3):
                        lat = 3 if k % 2 else -3
                        stamp_print(cy2 + dy2 * k * 8 + dx2 * lat, cx2 + dx2 * k * 8 + dy2 * lat,
                                    drag=k == 0)
                    woman_print(cy2 + dx2 * 8, cx2 + dy2 * 8, lead=True)
                else:
                    out = 1 if h2 % 2 else -1
                    for k in range(5):                     # away...
                        small_decoy_print(cy2 + dy2 * k * 9 * out + 5, cx2 + dx2 * k * 9 * out)
                    for k in range(4):                     # ...and back, offset
                        small_decoy_print(cy2 + dy2 * k * 9 * out - 4, cx2 + dx2 * k * 9 * out + 6)
                    if h2 % 5 == 0:
                        for k in range(4):
                            critter_print(cy2 + dx2 * k * 8 + 6, cx2 + dy2 * k * 8)
            else:
                # STRETCH 3 -- the den's mouth. "All tracks lead one way, none
                # lead back." EVERY gait here points inward and nothing returns:
                # his, hers, the pilgrims', the den-things'. That is the whole
                # dread of the approach, and it is also the last lie the ground
                # tells -- because what is in the den is a man, and the reason
                # nothing leads back is that nobody who came here wanted to.
                for k in range(3):
                    lat = 3 if k % 2 else -3
                    stamp_print(cy2 + dy2 * k * 9 + dx2 * lat, cx2 + dx2 * k * 9 + dy2 * lat,
                                drag=k % 2 == 0)
                woman_print(cy2 + dx2 * 6, cx2 + dy2 * 6, lead=True)
                if h2 % 3 == 0:
                    for k in range(3):
                        adult_print(cy2 + dy2 * k * 11 - 7, cx2 + dx2 * k * 11 - 5)
                if h2 % 4 == 1:
                    for k in range(3):
                        critter_print(cy2 + dy2 * k * 9 + 8, cx2 + dx2 * k * 9 + 4)

    # --- other tracks (v12.2): WHICH prints are his? -------------------------
    # Owner: "along with naris footsteps there's tracks of other people, we
    # have to understand and distinguish which ones are actually naris."
    # The world is walked. Pilgrims' adult prints pace the road margins;
    # three-toed den creatures cross the Scar; and -- cruelest -- other
    # SMALL prints wander regions beyond the Breach. Nari's signature is
    # learnable while he walks behind you in the Fold: paired gait, heel
    # dot, faint right-foot drag. Decoys are single-file, heel-less,
    # drag-less. Reading the difference IS the tracking game.
    # (adult_print / small_decoy_print / critter_print are defined ABOVE, with
    # stamp_print -- the three-stretch pass in the taking block calls them, and
    # a nested def is not hoisted: they have to exist before that code runs.)
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

    # --- the ABSOLUTE grain floor (v16.6) ------------------------------------
    # THE FLAT-PATCH LAW's second half. Every noise term in this file is
    # MULTIPLICATIVE -- `col * (1 + (grain - 0.5) * 0.11)` -- and a relative
    # term underflows in the dark: on deep water at (8, 13, 36) an 11% swing is
    # +/- 0.44 of a red level, which rounds to a single constant byte. Measured:
    # after fixing the three full-overwrite passes, every flat cluster LEFT on
    # the plate was near-black -- deep water (9, 10, 32), the map's dark frame
    # (21, 15, 12) -- i.e. exactly where relative grain cannot reach.
    #
    # So the last thing that touches the canvas is an absolute one: a +/-1.8
    # level dither from the SAME deterministic grain the ground field used (so
    # rebuilds stay byte-identical). 0.7% of the range -- invisible as texture,
    # decisive as a floor. It is not a cover-up for the real bug above; it is
    # the statement that nothing in this world is a solid colour, enforced in
    # the units the file actually ships in.
    canvas = canvas + ((grain - 0.5) * 3.6)[..., None]
    canvas_u8 = np.clip(canvas, 0, 255).astype(np.uint8)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # v15.0: the world is ~10x bigger, so the painted ground exceeds WebGL's
    # max texture size and must ship as a GRID of chunk PNGs that the runtime
    # loads and CAMERA-CULLS. Delete any stale single/legacy chunk files first.
    for old in OUT.parent.glob("ground_plate*.png"):
        old.unlink()
    CHUNK = 1024
    rows = (PH + CHUNK - 1) // CHUNK
    cols = (PW + CHUNK - 1) // CHUNK
    for r in range(rows):
        for c in range(cols):
            sub = canvas_u8[r * CHUNK:(r + 1) * CHUNK, c * CHUNK:(c + 1) * CHUNK]
            Image.fromarray(sub, "RGB").save(OUT.parent / f"ground_plate_{r}_{c}.png", optimize=True)
    (OUT.parent / "ground_plate_manifest.json").write_text(json.dumps(
        {"chunk": CHUNK, "rows": rows, "cols": cols, "full_w": PW, "full_h": PH, "s": S}) + "\n")
    print(f"wrote {rows}x{cols} ground chunks ({PW}x{PH}, chunk {CHUNK}px, S={S})")


if __name__ == "__main__":
    main()
