# Art Cohesion Audit — why the game doesn't read as one world

**Date:** 2026-07-16 · **Owner directive:** "do a visual audit of the art in
this game — it doesn't feel cohesive at all."

**Method:** full-screen capture sweep of every scene (`tests/e2e/audit.spec.ts`:
gate → menu → save → calibration → overworld → walk → fight → boss), contact
sheets of all 221 committed PNGs at 3–4× nearest-neighbour, zoom crops of the
composed overworld, plus a quantitative pass over every asset (dimensions,
opaque-colour count, semi-transparency, upscale blockiness). Findings are
ordered by how much each one contributes to the "not cohesive" feel.

## The one-line diagnosis

The game is currently showing **four different art generations at once** —
AI-painterly sprites, old code-drawn flat pixel art, smooth-gradient
procedural backgrounds, and a soft watercolour ground plate — and the
pipeline's cohesion passes (outline, quantize) are applied unevenly across
them. Any single register would read fine; the mix is what the eye flags.

## Findings

### C1 — Four art generations are live on screen simultaneously · **High**

| Generation | Where the player sees it | Register |
|---|---|---|
| AI-painterly (current bar, v7.9+) | band, enemies, all `env/` kits, landforms | soft-shaded, detailed, 1px forced outline |
| Code-drawn flat pixel art (pre-v7.9) | `overworld/props.png` (echo runes, candles), `npcs.png`, `landmarks.png`, the 16px tileset, `ui/panel*.png` | flat fills, minimal shading, chunky |
| Procedural smooth-gradient | `backgrounds/battle_abyss.png` — the **audio gate (first screen of the game)** and every menu via `Backdrop.ts` | 1,632 colours, vector-flat tents, no outlines, not pixel art at all |
| Raw unstyled | `CalibrationScene` (pure black + white circle), parts of SaveScene | no palette, no framing |

Concrete sting: **two shipwrecks in two styles near the same node** — the
painterly wreck-on-sand (`env/shallows/landform_outcrop2.png`) and the old
ink-and-white-sails ship (`landmarks.png` frame 0) are both visible around
`opening_1`. Same object, two art generations, one screen apart.

The player's first three screens (gate → menu → calibration) contain **none**
of the current-bar art: oldest background, then raw black. The world art only
starts at the overworld, so the game *opens* incoherent.

### C2 — "Stickers on a watercolour": ground vs sprite register clash · **High**

The ground plate (`ground_plate.png`, 764 colours) is soft, anti-aliased and
unoutlined; every sprite standing on it gets a forced hard 1px near-black
outline (`outline_pass.py`). Each object therefore reads as a die-cut sticker
pasted onto a painting rather than a thing standing in the world. Three
amplifiers:

- **Outlined ground aprons.** Many AI pieces carry baked-in ground context —
  the shallows wreck's sand island, dockpost/piling water puddles, the
  saltmines `landform_outcrop2` entire lantern-lit plaza, hall
  `landform_outcrop2` a whole cathedral interior. `grow_outline()` then draws
  a black ring *around the patch of sand/water*, which no real object has.
- **Inconsistent policy.** Venue floor patches and region tint transitions are
  soft-edged and unoutlined; every piece on them is hard-outlined; the two
  conductor sheets are hand-outlined and skipped. Three treatments, one shot.
- **Baked shadow platters.** Band frames carry hard black outlined shadow
  ovals of differing shapes ("action-figure base"), while foes/NPCs get soft
  runtime shadows.

### C3 — The band doesn't read as one band · **High**

Zoom crop of the four members walking together (`audit-6`):

| Member | Opaque colours | Read |
|---|---|---|
| amir | 35–44 | dark charcoal/olive, teal-cyan skin, red guitar — good anchor |
| bassist | **11** | near-black featureless blob; no face, instrument illegible; **reads closer to the `drifter` enemy than to a bandmate** |
| drummer | 41–51 | pale grey-white skin, light plum shirt — brightest skin on the team |
| vocalist | **61–80** | blazing saturated ember-orange full robe — the hottest colour mass in *any* captured scene |

Three different skin keys (teal / pale-grey / amber-shadow), a 7× spread in
colour budget, one member under-lit to illegibility and one over-saturated
against the "cold overcast, ember as accent" palette rule. Individually
plausible sprites; together they look sourced from four different games —
and they walk in a line, so the comparison is forced constantly.

### C4 — Quantization/bloom escapees in the env kits · **Medium**

Median env piece: ~12 opaque colours, hard alpha. Escapees:

| Asset | Colours | Problem |
|---|---|---|
| `saltmines/landform_canopy2.png` | **265** | giant crystal flower with smooth gradients **and baked soft bloom halo** |
| `saltmines/salt_crystal.png` | 136 | baked glow |
| `saltmines/scatter_crystal.png` | 112 | baked glow |
| `pit/scatter_pennant.png` | 86 | smooth pink gradient flag, also the most saturated pit piece |
| `pit/ticket_booth.png` | 85 | smooth shading |

The baked-bloom crystals sit in the same shot as candles/braziers whose glow
is done with the runtime additive `fx.py` pass — **two visibly different
bloom systems side by side** (clearly visible in the `audit-7` fight capture,
crystal flower right of frame vs candle glow left). Everything else in the
game says "emission = additive runtime glow"; the crystals disagree.

### C5 — Pipeline QA misses shipped into `assets/` · **Medium**

- `saltmines/scatter_sign.png`: the background flood-key failed — the piece
  still carries its **rectangular grey AI-generation backdrop**, shipped as-is.
- `attic/scatter_umbrellas.png`: an orphan 1px island floats disconnected
  below the umbrella (largest-island filter kept two islands).

Small, but each one is an obvious "generated art glitch" tell when spotted.

### C6 — Texel-density mixing from non-integer render scales · **Medium**

The cast was explicitly baked for integer texels (`bake_cast.py`, drawn at
`setScale(0.5)` — the code comments call this out), but other draw sites
break the grid: venue kit pieces `×0.55`, echo runes and props `×0.72`,
landmarks **upscaled** `×1.15`. At the 4× display zoom this yields fat, thin
and uneven pixels on the same screen — a classic subconscious incohesion
signal even for players who can't name it.

### C7 — Region hue transitions are hard seams · **Low**

The plate's per-region tint (teal → olive at shallows/saltmines) changes
across a near-vertical soft wipe visible mid-screen in `audit-7`. The two
biomes' *dressing* transitions gradually, the *ground colour* doesn't.

### C8 — Minor composition notes · **Low**

- Boss bar overlaps the "ESC: settings" controls hint (`audit-9`).
- The plate's ordered-dither texture is uniform across turf, stone and water;
  on large calm water it reads as faint static rather than material.

## What is already working (don't touch)

The conductor pair (world + colossal), `bg_title`, the pit tent/wheel/booth
set, the hall and attic landforms, the scatter kits' internal consistency,
palette temperature of the world as a whole, and the plate on its own terms.
The direction (moody painterly-pixel HLD register) is right; the problem is
enforcement, not taste.

## Recommended fixes, in order of leverage

1. **Kill the legacy surfaces** (C1). Restyle the gate/menu backdrop in the
   current register (the `bg_title` treatment already qualifies — reuse it or
   generate a sibling), dress CalibrationScene/SaveScene with the panel kit +
   palette, and regenerate `props.png`, `npcs.png`, `landmarks.png` through
   the same AI pipeline as the env kits (they're the last pre-v7.9 art in the
   world). Retire one of the two shipwrecks.
2. **One outline + one ground policy** (C2). Strip baked ground aprons at
   import (extend the flood-key/mist-scrub to sand/water pedestals) so
   outlines hug true silhouettes; pick one shadow treatment (runtime soft
   shadow) and delete baked platters from the band frames.
3. **Band unification pass** (C3). Re-key the vocalist's robe to a muted
   rust/plum with ember kept as trim accent, relight the bassist to amir's
   value range with a readable face + bass silhouette, and settle one skin
   key for all four. Budget target: every member within ~30–60 colours.
4. **Requantize the escapees and lint for it** (C4, C5). Re-run the C4 table
   through `requantize_cast.py`-style discipline with bloom removed (runtime
   glow markers instead), fix the sign/umbrella glitches, then add a cheap
   cohesion lint to `generate_all.py`/CI: max opaque colours per class,
   single-island silhouette, no rectangular-backdrop corners, outline ring
   present. That turns this audit's checks into a permanent gate.
5. **Snap render scales to the texel grid** (C6): kit 0.55→0.5, props/echo
   0.72→0.5 (author 1.5× larger if they get too small), landmarks 1.15→1.0.
6. **Blend region tints** (C7) over a wider dithered band in `paint_ground.py`.

## Verification

Re-run `npx playwright test tests/e2e/audit.spec.ts` after each pass and
compare against this sweep's captures; the acceptance bar is that a stranger
cannot sort any single screenshot's elements into "which pipeline drew this".
