# Scale & Placement Audit — the entire landscape

**Date:** 2026-07-15 · **Owner directive:** "do an audit of all the art in the
game where you just focus on scale and placement.... audit the entire
landscape."

**Method:** systematic 5×3 camera sweep of the whole overworld (every region
at three latitudes, retina scale), plus live-fight and venue captures. Every
finding below was observed in a screenshot, fixed, and re-verified with the
same sweep.

## Findings & fixes

| # | Finding | Severity | Fix | Status |
|---|---|---|---|---|
| SP1 | **Roads squiggle through open water.** The map routes some paths through lakes (they are walkable causeways), but they were painted as bare grass-road: glowing tan worms floating on the hall lake. | High | `paint_ground.py` causeway pass: path pixels near/inside water repaint as cool stone masonry with a hard dark edging where they meet water. | ✅ fixed |
| SP2 | **Venue set pieces float on water.** `composeWorldVenue` placed kit pieces at fixed offsets from the node centre with no terrain check — a harp and a marble bust stood on the boss lake. | High | `composeWorldVenue` takes a `canPlace(x,y)` predicate; the overworld passes a tile check (grass/path only). Offsets that land in water or rock skip the piece. | ✅ fixed |
| SP3 | **Colossal outcrops squat on roads.** Landform placement validated only the anchor tile, but an outcrop's solid base spans ~5 tiles — a giant grandfather clock sat overlapping the road. | High | Outcrops now require their whole ±2-tile footprint row to be open grass; canopies (which only overhang) keep the anchor-only check. | ✅ fixed |
| SP4 | **Scatter pieces pile up inside clusters.** Pieces are 20–30 px on a 16 px grid; orthogonally-adjacent placements collided into overlapping heaps (anchors on top of kelp on top of chests). | Medium | Checkerboard eligibility inside clusters (no two orthogonal neighbours) with per-tile chance raised 32→52 to keep the cluster feel. | ✅ fixed |
| SP5 | **Toy-scale errors.** The attic doll and rocking horse rendered at 24 px — the size of the 25 px hero. They read as a seated person and a live horse. | Medium | Resized to genuine toy scale (14 px); birdcage trimmed 26→18 px. | ✅ fixed |
| SP6 | **Ponds read as rounded rectangles.** Fine shoreline jitter (±3 px) could not disguise map-rectangular water bodies at 380 px scale. | Medium | `organic_mask` gained a coarse low-frequency `warp` term that swings the whole boundary several px in/out; water uses `warp=0.6, blur=13`. | ✅ fixed |
| SP7 | **Scatter invades dressed places.** Decorative scatter could land inside node venues and on echo spots, fighting the deliberate dressing. | Medium | Scatter now clears a ±2-tile zone around every marker and echo. | ✅ fixed |
| SP8 | **NPC scale inconsistency.** Townsfolk at 0.72 (~29 px) towered over the 25 px hero. | Low | Normalized to 0.58 (~23 px) — a hair shorter than the hero. | ✅ fixed |
| SP9 | **Attic mesa pillars repeat one silhouette.** The attic mid-band paints five near-identical rounded-rect pillar mesas in one screen. Shape comes from map data (same-size rock clusters), not the painter. | Low | Deferred: needs map-data variance in `generate_overworld_map.py` (vary rock cluster sizes), or per-component width jitter in the painter. | ⏳ follow-up |
| SP10 | **Mesa top plateaus read bare.** Large pale tops carry only sparse cracks/glyphs; at retina scale they read flat. | Low | Deferred: add tonal patching + occasional scatter ON mesa tops (needs a "rock-top" placement class). | ⏳ follow-up |
| SP11 | **Straight parallel road ribbons** in saltmines mid-band read artificial (two N-S roads ~200 px apart, dead straight). | Low | Deferred: map-data routing change; painting alone can't bend them. | ⏳ follow-up |

## Scale reference (verified consistent)

At world scale the hero is ~25 px tall (72 px art × 0.35). Verified against:
band followers (same), townsfolk 23 px, standing foes ~29 px (72 × 0.4 —
deliberately imposing), the colossal Conductor ~58 px, scatter props 12–30 px
by object class (toys < furniture < posts), venue kit pieces × 0.55 in-world,
landforms 60–96 px, canopy trees overhang the player layer. No remaining
same-class outliers observed in the sweep.

## Verification

Full 5×3 sweep re-captured after fixes: causeways read as built stone, no
floating venue pieces, no outcrop on a road in any capture, clusters no
longer overlap, ponds organic. 115 unit / 17 e2e green; deployed.
