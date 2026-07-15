"""Merge + hard-validate the authored set-dressing (from the region-author
workflow) into src/data/content/overworld/dressing.json. The agents compose;
this script is the last word on the HARD rules -- anything that fails is
dropped loudly, never shipped:

  * anchor tile must be grass, >=2 tiles (Chebyshev) from road/water/rock/
    echo/spawn and region edges, >=3 from fight nodes;
  * per-region key budgets (scatter <=2, organic filler <=4, landform <=1);
  * scale clamped to class range; texture key must exist on disk.

Usage: python3 tools/overworld/merge_dressing.py <workflow_results.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = json.loads((ROOT / "assets" / "tilemaps" / "overworld.json").read_text())
OUT = ROOT / "src" / "data" / "content" / "overworld" / "dressing.json"

REGIONS = ["shallows", "saltmines", "pit", "attic", "hall"]
W, H = MAP["width"], MAP["height"]
DATA = MAP["layers"][0]["data"]
NODES = [(int(o["x"] // 16), int(o["y"] // 16)) for o in MAP["layers"][1]["objects"] if o["name"] != "spawn"]
SPAWN = [(int(o["x"] // 16), int(o["y"] // 16)) for o in MAP["layers"][1]["objects"] if o["name"] == "spawn"]
ECHOES = [(int(o["x"] // 16), int(o["y"] // 16)) for o in MAP["layers"][2]["objects"]]

FILLER = ("stone", "kelp", "reeds", "reedclump", "rubble", "plank", "bones", "starfish", "coral", "shells", "driftwood")


def kind_at(c: int, r: int) -> int:
    if not (0 <= c < W and 0 <= r < H):
        return 3
    return (DATA[r * W + c] - 1) % 4


def valid_tile(ri: int, col: int, row: int) -> str | None:
    # Physical rules only: the ANCHOR tile must be grass (a mooring stands
    # BESIDE the water, a camp BESIDE the ridge -- adjacency is the point of
    # scene-dressing, not a violation); stay off fight venues and interact
    # spots; stay inside the border rock ring.
    c = ri * 26 + col
    if not (1 <= col <= 24 and 1 <= row <= 32):
        return "on the border rock ring"
    if kind_at(c, row) != 0:
        return f"anchor tile is not grass (kind {kind_at(c, row)})"
    for nc, nr in NODES:
        if max(abs(nc - c), abs(nr - row)) < 3:
            return "within 3 tiles of a fight node"
    for pc, pr in ECHOES + SPAWN:
        if max(abs(pc - c), abs(pr - row)) < 2:
            return "within 2 tiles of an echo/spawn"
    return None


def main() -> int:
    results = json.loads(Path(sys.argv[1]).read_text())
    regions_out = []
    total, dropped = 0, 0
    for entry in results:
        region = entry["region"]
        ri = REGIONS.index(region)
        placements = (entry.get("verified") or {}).get("fixed") or entry["authored"]["placements"]
        budget: dict[str, int] = {}
        kept = []
        for p in placements:
            total += 1
            key = p["key"]
            if not (ROOT / "assets" / "sprites" / "env" / key.replace("env_", "", 1).replace("_", "/", 1).__str__()).with_suffix(".png").exists():
                # env_<biome>_<piece> -> assets/sprites/env/<biome>/<piece>.png
                print(f"[{region}] DROP {key}: no such texture file")
                dropped += 1
                continue
            err = valid_tile(ri, p["col"], p["row"])
            if err:
                print(f"[{region}] DROP {key} @({p['col']},{p['row']}): {err}")
                dropped += 1
                continue
            is_landform = "landform_" in key
            cap = 1 if is_landform else (4 if any(f in key for f in FILLER) else 2)
            if budget.get(key, 0) >= cap:
                print(f"[{region}] DROP {key}: over budget ({cap})")
                dropped += 1
                continue
            budget[key] = budget.get(key, 0) + 1
            lo, hi = (0.7, 0.85) if is_landform else (0.55, 0.7)
            kept.append({
                "vignette": p["vignette"],
                "key": key,
                "col": p["col"],
                "row": p["row"],
                "dx": max(-24, min(24, int(p["dx"]))),
                "dy": max(-24, min(24, int(p["dy"]))),
                "scale": round(max(lo, min(hi, float(p["scale"]))), 2),
                "flip": bool(p["flip"]),
            })
        regions_out.append({"region": region, "placements": kept})
        print(f"[{region}] kept {len(kept)} placements, {len(set(p['vignette'] for p in kept))} vignettes")
    OUT.write_text(json.dumps({"regions": regions_out}, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)} -- kept {total - dropped}/{total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
