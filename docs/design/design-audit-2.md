# Design Audit 2 — cohesion (2026-07-14, PRD v9.0)

Owner: "the art is so terrible and not cohesive. you tried to get the HLD detail I
want on rocks and shit but left chunky blocks everywhere."

Correct, and the audit confirms it screen by screen (captures reproduced with the
same teleport set as `audit.spec.ts`). The failure is **structural, not per-asset**:
the world now contains TWO fidelity registers at once — painterly AI-generated
pieces (band, foes, landforms, venue kits, all ~1.5× texel density) standing on a
**hand-stamped 16px tile carpet**. Every complaint below is a symptom of that split.

## Findings (ranked)

| # | Finding | Evidence |
|---|---|---|
| **G1** | **Rock = chunky blocks.** Impassable rock renders as rows of one repeated 16px bubble-blob tile. Next to the 96px painted sea-stack landform the clash is maximal — the exact "HLD rocks vs chunky blocks" complaint. Terrace-lip shading (v8.8) polished the blocks instead of removing them. | Shallows capture: repeated blob rows left edge, painterly outcrop beside them |
| **G2** | **Roads are copy-paste strips.** The cobble tile repeats identically; two parallel roads read as duplicated bitmap strips with hard grid seams. The plank road tiles likewise. | Saltmines capture |
| **G3** | **Water reads as a UI panel (regression of audit-1 O2).** Rectangular pools with razor-straight edges, a uniform dot-grid fill, and the region tint lift it into a translucent teal "window". Deep-water rows tile visibly. | Both captures, top-left |
| **G4** | **Grass is wallpaper.** One tuft stamp at even density; the v7.12 calming pass reduced contrast but the repetition is still legible at one glance. | Saltmines capture |
| **G5** | Prop rows along road edges read as mechanically placed (straight graveyard lines at constant offset). | Saltmines capture, bottom |

What already lands (do NOT churn): the band and foes, the landform pieces
themselves, venue floors in fights, the framed HUD, the wordmark, fog/vignette.

## Root cause & the fix

A tile-stamp ground can never match painted sprites. Stop stamping: **bake one
painted ground plate** offline at 2× texel density (`tools/overworld/paint_ground.py`
→ `assets/tilemaps/ground_plate.png`, 32px per tile cell, deterministic), where
terrain is drawn as coherent MASSES, not tiles:

- **Rock (G1):** connected rock clusters become single mesa landforms — organic
  silhouette (no grid edges), lit top surface with cracks, a striated cliff face on
  the south edge, cast shadow onto the ground. The HLD cliff read.
- **Roads (G2):** one continuous worn-earth ribbon — distance-field edges, darkened
  rims, centerline wear, hash-scattered stones. No repetition anywhere.
- **Water (G3):** unified bodies — shore-distance depth bands to near-black,
  organic (rounded, jittered) shorelines with foam + dark bank, sparse hashed
  swells. The "panel" dies with the straight edges.
- **Grass (G4):** a value-noise field with region-blended bases (bakes the seam
  cross-fade) and hash-placed individual motifs — variation at every scale.
- The tile LAYER stays for collision/terrain queries; only its rendering is
  replaced by the plate. Fights, venues, props, landforms sit on top unchanged.
- (G5) prop scatter keeps the cluster hash but adds jitter + road-offset variance.

Burn-down: G1–G4 in the plate (one pass), G5 in scene scatter. Acceptance: re-run
the audit captures — no repeated stamp is identifiable anywhere on any screen; rock
reads as landform; water reads as depth; the plate sits in one register with the
AI pieces.
