"""The shared placement checker for every region's hand-authored dressing.

    from place_kit import Kit, place
    KIT = Kit(region_index=2, biome="breach", meters={...}, road_ok={...})
    ... KIT.main(sys.argv, PLACEMENTS, preview_window=(60, 150, 66, 174))

WHY THIS IS ONE FILE AND NOT FIVE
`place_fold.py` and `place_shelf.py` were written a week apart and the second was
a copy of the first: same `_map`, same `_sizes`, same `_box`, same road/water
sweep, same ground-contact test, same `--write`, same preview. Four more regions
were coming, which meant six copies of a checker whose whole purpose is to be
the single thing that cannot be wrong.

This project has already paid for that mistake once and written it up: the
overworld tileset's region accents lived in TWO tables edited separately
(`tiles.py` and `paint_ground.py`) and they disagreed -- salt-mine orange in one,
kelp green in the other -- and nobody noticed for months, because a colour
constant does not say what it is for. The fix there was to make one table import
the other. This is the same fix applied before the divergence instead of after.

WHAT STAYS PER-REGION: the placements themselves, the metres table, and the
prose explaining why each vignette is where it is. That is authorship and it
should be duplicated, because it is different every time. The arithmetic is not.

THE RULES, in one place:
  * no piece may cover a PATH tile -- a stall drawn over the road makes the road
    look like a mistake. Per-region exemptions go in `road_ok`, and they are for
    pieces that ARE crossings or gates: a bridge that does not span the road it
    bridges is a decoration in a field.
  * no piece may cover a WATER tile, with the same kind of per-region exemption
    in `water_ok` -- and the Breach needs it, because duckboards over standing
    water is the entire reason duckboards exist. A blanket water ban would have
    forced the one piece whose job is "people crossed here on purpose" to stand
    everywhere except where it makes sense.
  * pieces may stand on ROCK, and mostly should: rock already blocks movement,
    so a building on rock is a building the player cannot walk through, and the
    collision layer and the picture finally agree.
  * two pieces collide when their GROUND CONTACT overlaps, not their bounding
    boxes. Boxes were the first rule and it was wrong -- a lamp standing in
    FRONT of a house is inside the house's box by definition, and the engine
    already sorts by base Y so the lamp simply occludes it. The real fault is
    two things standing on the same ground, so the test is: x-ranges overlap AND
    bases within FOOT_DEPTH pixels.
  * every base must be inside its own region, which catches the whole class of
    bug where a vignette is authored against the wrong coordinate space.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "assets" / "tilemaps" / "overworld.json"
DRESSING = ROOT / "src" / "data" / "content" / "overworld" / "dressing.json"
PREVIEW = ROOT / "tools" / "overworld" / ".preview"

TILE = 16
PX_PER_METER = 15  # src/scenes/env/WorldScale.ts
MIN_SCALE, MAX_SCALE = 0.28, 1.6
FOOT_DEPTH = 10
FOOT_TOL = 0.3
KIND_COL = {0: (34, 44, 46), 1: (72, 66, 56), 2: (14, 30, 40), 3: (52, 58, 62), None: (8, 9, 12)}


def place(vignette, piece, col, row, flip=False, dx=0, dy=0):
    return {"vignette": vignette, "piece": piece, "col": col, "row": row,
            "flip": flip, "dx": dx, "dy": dy}


class Kit:
    def __init__(self, region_index, biome, meters, road_ok=frozenset(), water_ok=frozenset()):
        self.ri = region_index
        self.biome = biome
        self.meters = meters
        self.road_ok = set(road_ok)
        self.water_ok = set(water_ok)
        self.dir = ROOT / "assets" / "sprites" / "env" / biome

    # -- the map ---------------------------------------------------------
    def _map(self):
        doc = json.loads(MAP.read_text())
        data = next(l for l in doc["layers"] if l["name"] == "ground")["data"]
        return doc, doc["width"], data

    def _sizes(self):
        """Rendered pixel size per piece, using the ENGINE's scale.

        `worldScaleFor()` clamps and then snaps to the nearest half step with a
        0.5 FLOOR, and the floor is the part that matters: it means a piece's
        height in tiles is set by its source canvas, and no metres value can
        shrink it below `src_h / 2`. Reproducing the snap here rather than the
        raw ratio is what makes the footprint maths agree with what ships.
        """
        out = {}
        for name, m in self.meters.items():
            with Image.open(self.dir / ("%s.png" % name)) as im:
                sw, sh = im.size
            s = max(MIN_SCALE, min(MAX_SCALE, (m * PX_PER_METER) / sh))
            s = max(0.5, round(s * 2) / 2)
            out[name] = (sw * s, sh * s)
        return out

    def _box(self, sizes, p):
        """Pixel bounds, origin bottom-centre (matches setOrigin(0.5, 1))."""
        w, h = sizes[p["piece"]]
        x = p["col"] * TILE + TILE / 2 + p["dx"]
        y = p["row"] * TILE + TILE + p["dy"]
        return (x - w / 2, y - h, x + w / 2, y)

    # -- the checks ------------------------------------------------------
    def check(self, items):
        doc, mw, data = self._map()
        sizes = self._sizes()
        problems = []

        def kind(c, r):
            if not (0 <= c < mw and 0 <= r < doc["height"]):
                return None
            gid = data[r * mw + c]
            return None if gid == 0 else (gid - 1) % 4

        def region(c, r):
            if not (0 <= c < mw and 0 <= r < doc["height"]):
                return None
            gid = data[r * mw + c]
            return None if gid == 0 else min(4, max(0, (gid - 1) // 4))

        for p in items:
            vig, piece, col, row = p["vignette"], p["piece"], p["col"], p["row"]
            if piece not in sizes:
                problems.append("%s %s (%d,%d): no metres declared" % (vig, piece, col, row))
                continue
            x0, y0, x1, y1 = self._box(sizes, p)
            if region(col, row) != self.ri:
                problems.append("%s %s (%d,%d): base is in region %s, not %s"
                                % (vig, piece, col, row, region(col, row), self.biome))
            for c in range(int(x0 // TILE), int((x1 - 1) // TILE) + 1):
                for r in range(int(y0 // TILE), int((y1 - 1) // TILE) + 1):
                    k = kind(c, r)
                    if k == 1 and piece not in self.road_ok:
                        problems.append("%s %s (%d,%d): covers ROAD tile (%d,%d)"
                                        % (vig, piece, col, row, c, r))
                    if k == 2 and piece not in self.water_ok:
                        problems.append("%s %s (%d,%d): covers WATER tile (%d,%d)"
                                        % (vig, piece, col, row, c, r))

        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if a["piece"] not in sizes or b["piece"] not in sizes:
                    continue
                ax0, _ay0, ax1, ay1 = self._box(sizes, a)
                bx0, _by0, bx1, by1 = self._box(sizes, b)
                if abs(ay1 - by1) > FOOT_DEPTH:
                    continue
                ow = min(ax1, bx1) - max(ax0, bx0)
                if ow <= 0:
                    continue
                frac = ow / min(ax1 - ax0, bx1 - bx0)
                if frac > FOOT_TOL:
                    problems.append(
                        "%s %s (%d,%d) shares ground with %s %s (%d,%d) -- %.0f%% of its width"
                        % (a["vignette"], a["piece"], a["col"], a["row"],
                           b["vignette"], b["piece"], b["col"], b["row"], frac * 100))
        return problems

    # -- authoring aid ----------------------------------------------------
    def resolve(self, items, radius=3, verbose=True):
        """Nudge each base to the nearest legal tile within `radius`, and SAY SO.

        WHY THIS EXISTS. The Shelf and the Breach were placed by enumerating
        every legal base in a window and picking from the list by hand. That
        works at 47 and 81 placements in regions of a few thousand tiles. Region
        3 is FORTY-THREE THOUSAND tiles with eleven nodes in it, and hand-picking
        at that scale stops being authorship and becomes data entry -- the Breach
        already lost two passes to a road that a two-row sample had hidden.

        So this resolves LEGALITY while leaving COMPOSITION to the author: you
        write where the piece should be, and it moves to the nearest tile that
        works. Two rules make that safe rather than a rubber stamp:

          * THE RADIUS IS SMALL. Three tiles. A piece that cannot be placed
            within three tiles of where it was authored is not a snapping
            problem, it is a composition problem -- the author put a five-tile
            frame on a cliff -- and it stays a hard failure so somebody looks at
            it.
          * IT REPORTS EVERY MOVE. A silent resolver is indistinguishable from a
            placement file that was never checked, which is the same failure mode
            as `dressing.json` naming 132 textures that had never existed while
            looking authored because it had counts.

        Ties break toward the SMALLEST move, then north, then west, so the result
        is deterministic -- two runs of the same file must produce the same
        dressing or the diff is noise.
        """
        doc, mw, data = self._map()
        sizes = self._sizes()
        H = doc["height"]

        def kind(c, r):
            if not (0 <= c < mw and 0 <= r < H):
                return None
            gid = data[r * mw + c]
            return None if gid == 0 else (gid - 1) % 4

        def region(c, r):
            if not (0 <= c < mw and 0 <= r < H):
                return None
            gid = data[r * mw + c]
            return None if gid == 0 else min(4, max(0, (gid - 1) // 4))

        def ok(p):
            if region(p["col"], p["row"]) != self.ri:
                return False
            x0, y0, x1, y1 = self._box(sizes, p)
            for c in range(int(x0 // TILE), int((x1 - 1) // TILE) + 1):
                for r in range(int(y0 // TILE), int((y1 - 1) // TILE) + 1):
                    k = kind(c, r)
                    if k is None:
                        return False
                    if k == 1 and p["piece"] not in self.road_ok:
                        return False
                    if k == 2 and p["piece"] not in self.water_ok:
                        return False
            return True

        # candidate offsets, sorted by distance then north then west
        offs = sorted(((dc, dr) for dc in range(-radius, radius + 1)
                       for dr in range(-radius, radius + 1)),
                      key=lambda o: (abs(o[0]) + abs(o[1]), o[1], o[0]))
        out, moved, stuck = [], 0, []
        for p in items:
            if p["piece"] not in sizes:
                out.append(p)
                continue
            found = None
            for dc, dr in offs:
                q = dict(p, col=p["col"] + dc, row=p["row"] + dr)
                if ok(q):
                    found = (q, dc, dr)
                    break
            if found is None:
                stuck.append(p)
                out.append(p)
                continue
            q, dc, dr = found
            if dc or dr:
                moved += 1
                if verbose:
                    print("  moved %-14s %s (%d,%d) -> (%d,%d)"
                          % (p["piece"], p["vignette"], p["col"], p["row"], q["col"], q["row"]))
            out.append(q)
        if verbose:
            print("resolved %d placements: %d already legal, %d nudged, %d STUCK"
                  % (len(items), len(items) - moved - len(stuck), moved, len(stuck)))
        for p in stuck:
            print("  STUCK  %-14s %s (%d,%d) -- no legal base within %d tiles"
                  % (p["piece"], p["vignette"], p["col"], p["row"], radius))
        return out

    # -- output ----------------------------------------------------------
    def placements(self, items):
        return [
            {"vignette": p["vignette"], "key": "env_%s_%s" % (self.biome, p["piece"]),
             "col": p["col"], "row": p["row"], "dx": p["dx"], "dy": p["dy"],
             "scale": 1.0,  # the engine's world scale wins; see WorldScale.ts
             "flip": p["flip"]}
            for p in items
        ]

    def write(self, items):
        doc = json.loads(DRESSING.read_text())
        out = self.placements(items)
        for region in doc["regions"]:
            if region["region"] == self.biome:
                region["placements"] = out
                break
        else:
            doc["regions"].append({"region": self.biome, "placements": out})
        DRESSING.write_text(json.dumps(doc, indent=1) + "\n")
        return len(out)

    def preview(self, items, window, zoom=3):
        """Draw the layout over a flat map of terrain kinds, at true world scale,
        in the engine's own draw order (by base Y, so a nearer piece occludes a
        farther one).

        PADDED, THEN CROPPED. A tall piece based on the top row of the window has
        its head above the window and `alpha_composite` refuses a negative
        destination. Clipping the window instead would hide exactly the pieces
        whose height is the thing under review.
        """
        c0, c1, r0, r1 = window
        doc, mw, data = self._map()
        sizes = self._sizes()
        pad = int(max(h for _w, h in sizes.values())) + TILE
        W, H = (c1 - c0) * TILE, (r1 - r0) * TILE
        img = Image.new("RGBA", (W + pad * 2, H + pad * 2))
        px = img.load()
        for c in range(c0, c1):
            for r in range(r0, r1):
                gid = data[r * mw + c] if (0 <= c < mw and 0 <= r < doc["height"]) else 0
                col = KIND_COL[None if gid == 0 else (gid - 1) % 4] + (255,)
                for i in range(TILE):
                    for j in range(TILE):
                        px[pad + (c - c0) * TILE + i, pad + (r - r0) * TILE + j] = col
        outside = 0
        for p in sorted(items, key=lambda t: t["row"]):
            with Image.open(self.dir / ("%s.png" % p["piece"])) as src:
                src = src.convert("RGBA")
                w, h = sizes[p["piece"]]
                sp = src.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
                if p["flip"]:
                    sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            x0, y0, x1, y1 = self._box(sizes, p)
            dx, dy = pad + int(x0) - c0 * TILE, pad + int(y0) - r0 * TILE
            # OUTSIDE THE WINDOW IS SKIPPED, AND COUNTED. The pad covers a piece
            # whose head sticks out above the top row; it does NOT cover a piece
            # that is simply somewhere else in the region, and `alpha_composite`
            # refuses a negative destination. The Shelf and the Breach never hit
            # this because every placement in those files happened to fall inside
            # the preview window; region 3 spans 289 columns and most of it does
            # not. Skipping silently would make a preview of a half-empty window
            # indistinguishable from a preview of a half-empty region, so the
            # count is printed.
            if dx + (x1 - x0) <= 0 or dy + (y1 - y0) <= 0 \
               or dx >= W + pad * 2 or dy >= H + pad * 2:
                outside += 1
                continue
            if dx < 0 or dy < 0:
                sp = sp.crop((max(0, -dx), max(0, -dy), sp.width, sp.height))
                dx, dy = max(0, dx), max(0, dy)
            img.alpha_composite(sp, (dx, dy))
        PREVIEW.mkdir(parents=True, exist_ok=True)
        out = PREVIEW / ("%s.png" % self.biome)
        img.crop((pad, pad, pad + W, pad + H)).convert("RGB") \
           .resize((W * zoom, H * zoom), Image.NEAREST).save(out)
        if outside:
            print("  (%d of %d placements are outside the preview window)"
                  % (outside, len(items)))
        return out

    def main(self, argv, items, preview_window, snap=0):
        # `snap` > 0 runs `resolve` first (see its docstring for why region 3
        # needs it and regions 0-2 did not). It still goes through `check`
        # afterwards -- resolve fixes terrain legality, check also enforces the
        # shared-footprint rule between pieces, and nothing skips the gate.
        if snap:
            items = self.resolve(items, radius=snap)
        problems = self.check(items)
        for p in problems:
            print("FAIL  %s" % p)
        if problems:
            print("\n%d problem(s) -- nothing written." % len(problems))
            return 1
        print("%d placements, all clear of roads and water." % len(items))
        if "--preview" in argv or "--write" in argv:
            print("preview -> %s" % self.preview(items, preview_window).relative_to(ROOT))
        if "--write" in argv:
            print("wrote %d placements -> %s" % (self.write(items), DRESSING.relative_to(ROOT)))
        return 0
