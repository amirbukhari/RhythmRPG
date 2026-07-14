# AAA Gap Audit — 2026-07-14

Owner verdict on the current build: **"there's so much wrong. this is not AAA
standard."** Correct. This document is the candid, screen-by-screen audit of
what specifically falls short, captured by playing the deployed build end to
end (`tests/e2e/audit.spec.ts` reproduces every capture), and the prioritized
plan to close the gaps. It exists so iteration stops being whack-a-mole and
starts burning down a ranked list.

## Method

`audit.spec.ts` boots the real game and screenshots every screen: audio gate,
main menu, save, calibration, overworld (idle + walking), the Shallows fight
(idle + attacking), and the Conductor boss fight. Findings below are ordered
by how much of the play time the screen occupies.

## Findings

### 1. Action battle (the most-played screen) — worst offender

| # | Problem | Detail |
|---|---|---|
| B1 | **Empty void arena** | The fightable centre is a flat dark-teal fill. The procedural "dapple" is invisible at final contrast; the light-pool is too subtle. ~70% of the screen is dead space. HLD arenas are *floors* — textured, patterned, readable. |
| B2 | **Incoherent piece kit** | The Shallows edge pieces mix perspectives and biomes: mossy *grass-topped islands* in an underwater ruin, a *side-view* rowboat on a top-down floor, red coral at inconsistent scales. Reads as clipart scatter, not a place. Root cause: pieces were generated without pinning the camera ("viewed from above / top-down game asset") or a shared scale reference. |
| B3 | **Goofy enemies** | The rot-slime is a beige mound with white googly eyes — comic, not dreadful. Enemy sprites predate the current generation pipeline and don't share the new band's style register. (Exception: the colossal Conductor reads genuinely imposing — keep.) |
| B4 | **Floating HP bars** | Bars hover in space above heads, disconnected from anything. Player HP should live in a real HUD; enemy bars should hug the sprite or appear as a boss bar. |
| B5 | **Raw-text HUD** | Bottom line is unframed monospace text over the arena; the top strip is a bare purple band with "Beat 1/4" clipping. Needs a designed HUD: framed player plate (HP/Focus/Groove), top-centre boss bar with the foe's name, beat indicator integrated. |

### 2. Overworld

| # | Problem | Detail |
|---|---|---|
| O1 | **Wallpaper ground** | One leaf-motif grass tile repeats unbroken over whole regions — uniform noise, green-on-green. Needs variant tiles (2–3 grass variations, bare-dirt patches), clustering, and value contrast so the road/props pop. |
| O2 | **Water reads as UI panel** | The bright cyan ripple texture is flat, saturated, and hard-edged — it looks like a panel, not water. Needs darker value, desaturation, animated caustics/foam edge (the shoreline foam already exists but the body of water betrays it). |
| O3 | **Prop confetti** | Gothic props are distributed near-evenly. Real places cluster: graveyards, camps, reed banks. The deterministic scatter should weight into clusters with clearings between. |
| O4 | **Everything is the same value** | Player, followers, NPCs, props are all near-black silhouettes on a dark field; only the red guitar pops. Characters need rim/value separation from scenery (scenery darker, characters lighter + accent). |

### 3. Menu / meta screens

| # | Problem | Detail |
|---|---|---|
| M1 | **Monospace wordmark** | The title is system monospace with a thick stroke — not a logo. Needs authored pixel wordmark art (generate via the sprite pipeline). |
| M2 | **Plain menu/save/calibration panels** | Functional but generic: default font, plain boxes. Lower priority than in-game screens. |

### 4. What already lands (keep, don't churn)

- The Conductor boss silhouette + scale contrast.
- The new band cast's style register (drowned-gothic, teal/rust).
- The real-song soundtrack + per-scene crossfade.
- Foes standing in the world / save-obelisks / band conga line (systems are
  right; the *art feeding them* is what lags).

## Prioritized plan

1. **P0 — Arena floors** (B1): per-biome designed ground in `ArenaComposer` —
   layered tones, biome motif (wet-sand ripples / mine planks / circus dust /
   attic boards / marble), strong central light, readable vignette.
2. **P0 — Coherent piece kits** (B2): regenerate every biome kit with camera
   pinned top-down ("game asset viewed from above"), one shared scale
   reference per kit, mist-scrub + island cleanup (the `newband.py` passes,
   now shared); cull off-biome pieces from layouts.
3. **P1 — Enemy resprite** (B3): slime/drifter/wraith through the same
   pipeline + style clause as the band so cast and foes share one register.
4. **P1 — Battle HUD** (B4, B5): framed player plate bottom-left, boss bar
   top-centre with name, beat pip integrated; enemy bars hug sprites.
5. **P2 — Overworld ground/water** (O1, O2): grass variants + dirt patches +
   clustered scatter; darker desaturated water with animated caustics.
6. **P2 — Value separation** (O4): darken scenery props ~15%, add 1px rim
   highlight to characters.
7. **P3 — Wordmark** (M1): authored pixel logo via the sprite pipeline.

Each item ships behind the usual gate: typecheck + 142 unit + full chromium
e2e + screenshot verification, then deploy.
