# The Drowned Chorus — Art Generation Prompt Catalog (AAA manifest)

> **PARTLY SUPERSEDED — read with the current canon.** Two things below no
> longer match the shipped game and should be reinterpreted, not taken literally:
> **(1) Cast (PRD v10.0 solo pivot).** There is no playable *band*. The cast is
> solo **Mir** — the former **Amir** guitarist slot, renamed — plus his toddler
> son **Nari** (a follower), the huntress **Lunal**, and the Conductor. The
> Bassist / Vocalist / Drummer slots in §1 are **retired fiction** (the "band"
> is now the in-universe soundtrack act *Inhalants*, §11.2). Generate Mir where
> this doc says "Amir"; skip the other three bandmates. See
> [`world-bible.md`](world-bible.md) §4 and PRD §8.4.
> **(2) Aesthetic (PRD v11.0 beauty pivot).** The game is **painterly HD, not
> pixel art** — ignore "pixel-art title," the quantize/slice pixel pipeline, and
> per-frame pixel budgets here; the current pipeline imports art at native
> painterly fidelity (PRD §11.1/§11.1.2). The slot list and per-asset *content*
> prompts below remain a useful inventory; the *style* wrapper does not.

Every art asset the game needs to be a real AAA pixel-art title — **~575 named
slots, thousands of frames** — each with a generation prompt. This is the 1:1
companion to **PRD §11.5 (AAA art asset manifest)**. The engine loads PNGs
directly, so you generate the art (any AI image tool or an artist), drop the PNG
into the slot, and I quantize → slice → wire → deploy it — the path proven by the
provided **Amir** guitarist.

> This is a production checklist, not a sample. "Enough art" = every row here
> filled with real art. Work top-to-bottom, or cherry-pick a biome/character and
> finish its whole set so the game grows in complete, shippable chunks.

## Contents
1. [Global style block](#global-style-block) · [Master palette](#master-palette) · [Delivery spec](#delivery-spec)
2. [Playable band — full animation sets](#1-playable-band--full-animation-sets)
3. [Enemies — full state sets](#2-enemies--full-state-sets)
4. [Boss — The Conductor](#3-boss--the-conductor-multi-phase)
5. [Tilesets — 5 biomes × autotile sheets](#4-tilesets--5-biomes)
6. [Environment props & destructibles](#5-environment-props--destructibles)
7. [Landmarks](#6-landmarks)
8. [Parallax backgrounds & weather](#7-parallax-backgrounds--weather)
9. [VFX library](#8-vfx-library)
10. [UI kit](#9-ui-kit)
11. [NPCs](#10-npcs)
12. [Items & pickups](#11-items--pickups)
13. [Tips & hand-back](#tips-for-ai-pixel-art-generation)

---

## Where to generate these (tools & workflow)

You generate the art; I wire it. Pick a tool by the job — the ones below are
**pixel-art-native** (they output real pixel grids, spritesheet frames, and
transparent PNGs, which general art generators don't):

| Job | Best tools | Why |
|---|---|---|
| **Characters w/ animation states** (the ≥22 band states, enemy states) | **PixelLab** (`pixellab.ai`), **Sprite-AI** (`sprite-ai.art`) | animate a base sprite into walk/run/attack cycles + 4/8-direction; built for game characters |
| **Spritesheets at exact frame size** | **Spritesheets.AI** (`spritesheets.ai`), **PixelBox** (`llamagen.ai/ai-pixel-art-generator`) | pixel-perfect frames on a grid, transparent PNG w/ premultiplied alpha |
| **Tilesets (seamless / autotile)** | **PixelLab** (tileset mode), **Spritesheets.AI** | generates tiles that fit together seamlessly |
| **Backgrounds / arena scenes / key art** | a strong general model — ChatGPT·DALL·E (`chatgpt.com`), Google Gemini (`gemini.google.com`), Midjourney (`midjourney.com`) | not pixel-native, so run the result through the importer to quantize/clean |
| **Style consistency across all ~575 slots** | **Scenario** (`scenario.com`) — train a small style model on Amir + your first assets | keeps the whole game one cohesive look |

**Workflow that fits this game:**
1. **Anchor the style once.** Generate/settle one hero (or reuse **Amir**) and 2–3
   tiles you love. Feed them back as a *style reference image* (most tools support
   it) on every later prompt so the set stays cohesive. Optionally train a Scenario
   model on them.
2. **Paste the [Global Style Block](#global-style-block) + [palette](#master-palette)** into every prompt.
3. **Transparency:** if the tool exports transparent PNGs, great. If not, generate the
   sprite on a **solid flat green (`#00ff00`) or magenta (`#ff00ff`) background** — my
   importer keys it out (`--key '#00ff00'`).
4. **Don't sweat exact pixel size or exact palette** at generation time — generate big
   and colorful; the importer downscales to the target frame size and snaps colors to
   the master palette.
5. **Send me the file** (attach or commit) and say the slot; I run one importer command
   and wire it in.

> Free tiers exist on most of these (e.g. Sprite-AI ~15 free gens, PixelLab/Scenario
> trials); pricing/URLs shift, so confirm current terms on each site. You don't need a
> paid plan to start — do one asset, hand it to me, and we prove the whole loop before
> you scale up.

---

## Global Style Block

> Paste before **every** prompt below.

```
Pixel art in the style of Hyper Light Drifter and Blasphemous — beautiful, moody,
gothic. Setting: "The Drowned Chorus", a surreal drowned/gothic world of ocean-floor
abyss, salt and rust, melting black clocks, bone and pearl, blood, rot-green, and a
looming Conductor. Dark, desaturated near-black base values with a few searing accent
hues: abyssal teal, plum/magenta, ember-gold, blood red. Strong readable silhouettes,
consistent top-left light source, clean limited palette, subtle dithering for shading
(no gradients, no anti-aliased blur, no photo-realism, no text, no watermark). Crisp
pixels, high contrast, deliberate — not noisy.
```

## Master palette

Keep every asset within these hues (hex):

```
Ink/void:   #05060a #0f111a #1c1f2b #2b2f3e
Bone/pearl: #f4efe2 #d8ceb6 #a89d84 #6f6754
Rust/ember: #e07030 #a8431c #f0a648 #f4d27a #6e3316
Blood:      #c22f34 #7d1b20 #4a1013
Ocean/teal: #49c6bd #1f6f77 #153a52 #0b2233 #2f5f86
Rot/moss:   #79b855 #426e33 #9aa843 #566a20
Plum:       #8a52a0 #4b2a57 #b98fca
Flesh:      #dcae86 #ad7552 #c4bbb0 #877d70
Metal:      #97a2ae #586470 #ccd4dc #3a434f
```

## Delivery spec

Generate **large and crisp** (≥1024px); I downscale + quantize to target. Transparent
background for all cutouts (characters, enemies, props, landmarks, UI, items, VFX);
opaque for tilesets and backgrounds. Multi-frame = a **horizontal strip** in the frame
order given, or send individual poses and I'll pack them.

| Asset | Path pattern | Frame size | BG |
|---|---|---|---|
| Band state | `assets/sprites/band/<member>/<state>.png` | 48×48 | transparent |
| Band portrait | `assets/ui/portraits/<member>.png` | 64×64 | transparent |
| Enemy state | `assets/sprites/enemies/<id>/<state>.png` | 48×48 (elites 64×64) | transparent |
| Boss state | `assets/sprites/enemies/conductor/<state>.png` | 96×128 | transparent |
| Tile sheet | `assets/tilemaps/<biome>_<sheet>.png` | 16×16 tiles | opaque, tileable |
| Prop | `assets/sprites/overworld/props/<name>.png` | ~32×40 | transparent |
| Landmark | `assets/sprites/overworld/landmarks/<name>.png` | ~64×80 | transparent |
| Parallax layer | `assets/backgrounds/<biome>_<layer>.png` | 320×180 (wide for near) | opaque/transparent |
| VFX | `assets/fx/<name>.png` | strip, ~32–64px | transparent |
| UI piece | `assets/ui/<name>.png` | varies | transparent |
| NPC | `assets/sprites/npcs/<id>/<state>.png` | 20×24–48×48 | transparent |
| Item icon | `assets/ui/icons/<name>.png` | 16×16 | transparent |

**Animation-state legend** (frame counts are targets; send what you get):
`idle` 4 · `idle_combat` 4 · `walk` 6 · `run` 6 · `dash` 3 · `jump` 2 · `fall` 2 ·
`land` 2 · `attack_1/2/3` 3 each · `heavy` 4 · `special` 5 · `ultimate` 6 · `parry` 3 ·
`block` 2 · `hurt` 2 · `death` 5 · `downed` 1 · `revive` 3 · `victory` 4 · `interact` 3.
Enemies: `idle` 2 · `move` 4 · `attack` 4 · `telegraph` 3 · `hurt` 2 · `death` 4
(+ `projectile`/`special` where noted).

---

## 1. Playable band — full animation sets

Side-view, facing right, punk/gothic rock band, one cohesive design language (attach
`assets/sprites/heroes/placeholder/Amir Stand.png` as a style reference). For each
member, generate all 22 states (48×48) + a 64×64 portrait. Base look first, then run
each state as "same character, now <motion>."

Motion cues (apply to every member): `idle` relaxed sway · `idle_combat` weapon ready,
tense · `walk` steady · `run` leaning sprint · `dash` blurred lunge with trail · `jump`
launch, legs tucked · `fall` reaching down · `land` crouch absorb · `attack_1/2/3`
three-hit instrument combo · `heavy` big wind-up overhead swing · `special` a
signature move (below) · `ultimate` an explosive full-body finisher · `parry` a
quick braced deflect flash · `block` guard raised · `hurt` recoil, head snap · `death`
stagger → collapse · `downed` slumped on the ground · `revive` rising, gasping ·
`victory` triumphant instrument raise · `interact` reaching/kneeling to touch.

**1.1 Amir — lead guitarist** — `band/amir/*` + `ui/portraits/amir.png`
```
Lean dark-skinned punk, spiked grey mohawk-ish cut, black sleeveless top over a white
tank, black jeans, electric guitar slung across the body. Special = a shrieking guitar
power-chord shockwave; ultimate = a whirling guitar-windmill unleashing a teal blast.
```

**1.2 Bassist — second guitarist / bass** — `band/bassist/*` + portrait
```
Broader build, tall red-dyed mohawk, sleeveless black vest, heavy low-slung bass.
Special = a ground-thumping bass drop (shock ring); ultimate = swinging the bass like
a wrecking club with an ember arc.
```

**1.3 Vocalist** — `band/vocalist/*` + portrait
```
Lithe front-person, high spiked hair, torn white shirt under a black jacket, microphone
with trailing cable. Special = a directional scream cone; ultimate = a sustained note
that rings the whole arena teal (support/heal-flavored ult).
```

**1.4 Drummer** — `band/drummer/*` + portrait
```
Sturdy build, shaggy hair under a bandana, black tank, a drumstick in each hand.
Special = a rapid double-stick flurry; ultimate = a colossal downbeat that quakes the
floor (ember impact).
```

---

## 2. Enemies — full state sets

~18 types across the 5 biomes. Each: `idle, move, attack, telegraph, hurt, death`
(48×48; elites 64×64). Ranged/elites add `projectile` or `special` as noted. All face
left (toward the player). Faint additive glow on eyes.

### Shallows (teal, drowned coast) — `enemies/<id>/*`
- **brinemound_slime** `slime` — `A gelatinous rot-green mound with pearl spots and two dim eyes, dripping brine.`
- **kelp_drifter** `drifter` — `A hooded abyssal wraith gliding above the floor, tattered teal-black cloak, one glowing eye-slit.`
- **drowned_fisher** — `A waterlogged villager, slack face, oilskin coat, swinging a rusted gaff hook.`
- **tidecaller** *(ranged, +`projectile`)* — `A barnacled priest-thing that hurls orbs of black water; projectile = a teal water bolt.`

### Salt Mines (ember-gold) — `enemies/<id>/*`
- **salt_grub** — `A pale segmented cave grub crusted in salt, burrows up from the ground to bite.`
- **calcified_miner** *(elite 64×64)* — `A miner turned to salt mid-swing, pick raised, cracks glowing ember; slow, heavy.`
- **ember_grunt** `luchador_grunt` — `A drowned masked wrestler in a cracked ember-gold mask, barrel chest, bandaged fists.`
- **slag_hound** — `A fast lean beast of cooled slag and bone, ember seams, lunging bite.`

### Pit Below (plum, drowned carnival) — `enemies/<id>/*`
- **rot_clown** — `A sagging carnival jester, greasepaint over rot, oversized gloves, a lurching giggle-attack.`
- **lantern_wisp** *(ranged, +`projectile`)* — `A floating dead-lantern spirit; projectile = a drifting plum ember.`
- **big_top_brute** *(elite 64×64)* — `A hulking strongman in a torn singlet, chained kettlebell, ground-slam.`
- **masked_luchador** `luchador_mask` *(elite 64×64)* — `A gleaming blood-red and bone mask with too many eye holes, kelp cape, glowing seams.`

### Attic of Teeth (rust) — `enemies/<id>/*`
- **gnawling** — `A small hunched biter, all teeth and knuckles, skitters and lunges.`
- **wall_crawler** — `A flattened spider-limbed thing that drops from the ceiling to ambush.`
- **pen_wraith** *(ranged, +`projectile`)* — `A spectral scribe trailing ink; projectile = a flung steel pen-nib dart.`
- **elite_wraith** `elite_wraith` *(elite 64×64)* — `Tall spectral wraith, feathered hair, wide pearl-toothed grin, tattered plum shroud, magenta eyes.`

### Conductor's Hall (deep plum, flooded) — `enemies/<id>/*`
- **page_revenant** — `A ghost made of blank sheet-music pages, faceless, drifting and slashing with paper edges.`
- **metronome_sentinel** *(elite 64×64)* — `A clockwork guardian, brass pendulum torso ticking side to side, arms that swing on the beat.`

---

## 3. Boss — The Conductor (multi-phase)

`assets/sprites/enemies/conductor/*`, 96×128 (screen-filling, authored at size, never
upscaled), faces left.

```
Base: a colossal gaunt maestro in a vast black melting tailcoat, a great cracked
clock-face heart dripping molten gold, two long baton-arms, blank pages swirling,
faceless void under a wide hat with two burning amber pinpoints.
```
States (each its own strip):
- `intro` — rises from the flooded podium, coat unfurling. (6)
- `idle_p1` / `idle_p2` / `idle_p3` — per-phase idle sway, more frantic each phase. (2 each)
- `attack_baton_sweep` — a wide horizontal baton slash. (4)
- `attack_page_storm` — flings a fan of razor pages. (4, +`projectile` page)
- `attack_clock_slam` — brings the clock-heart down, shockwave. (5)
- `attack_gold_rain` — molten-gold droplets rain from above. (4, +`projectile` droplet)
- `attack_tempo_pulse` — a radial beat shockwave (phase 3). (5)
- `phase_transition` — clock cracks further, screen-wide amber flash. (5)
- `stagger` — reels, heart exposed (the punish window). (3)
- `hurt` — flinch. (2)
- `death` — coat collapses, clock stops, gold sets solid. (8)

*(Optional mid-boss per biome, `enemies/<id>/*`, ~10 states each: a Shallows Tide-Warden
and a Pit Ringmaster are the two strongest candidates.)*

---

## 4. Tilesets — 5 biomes

Per biome, **9 sheets**, all 16×16, seamlessly tileable. Autotile sheets should include
the standard edge/corner set (a 3×3 minimum: center, 4 edges, 4 outer corners; ideally
a full 47-tile blob). One dominant accent hue per biome.

For each biome `<b>` in {`shallows`, `saltmines`, `pit`, `attic`, `hall`}, generate:
- `<b>_terrain.png` — ground autotile (center + edges + corners) of the biome's turf/floor.
- `<b>_path.png` — road/walkway autotile.
- `<b>_water.png` — water + **shoreline transition** autotile (water-to-land edges, foam).
- `<b>_cliff.png` — cliff faces / walls with top rim + drop shadow + side variants.
- `<b>_transition.png` — a blend strip to the **next** biome's palette (for region seams).
- `<b>_decal.png` — non-blocking overlay decals: cracks, moss, puddles, stains, rubble (8+).
- `<b>_fg.png` — foreground occluders drawn over the player (overhangs, fronds, arches).
- `<b>_anim.png` — animated tiles (2–4 frames): water surface shimmer / torch / drip.
- `<b>_interactive.png` — door, chest, lever, save-shrine, breakable crate/urn (as tiles).

Biome flavor for the prompts (combine with the sheet type):
- **shallows** — drowned coastal turf, bone-salt cobbles, teal seawater w/ pearl foam, barnacled shoreline rock; accent `#49c6bd`.
- **saltmines** — salt-crusted ochre ground, ember-lit mine road, brackish shaft water, rusted ore rock; accent `#f0a648`.
- **pit** — trampled violet fairground grass, cracked plum midway, deep pit water, amethyst rubble; accent `#8a52a0`.
- **attic** — rust-brown rotted floorboards, plank path, black leak-water, crumbling brick/plaster; accent `#a8431c`.
- **hall** — drowned deep-plum plaza stone, bone-tile processional path, still black flood water, obsidian statue-stone; accent `#4b2a57`.

---

## 5. Environment props & destructibles

~12 per biome + shared interactables. `assets/sprites/overworld/props/<name>.png`,
~32×40 (larger for big pieces), transparent, feet at bottom, top-left light.

**Shared interactables (animated where noted):** `chest` (closed/opening/open),
`save_shrine` (a glowing tuning-fork shrine, idle pulse), `door` (shut/opening),
`sign` (a leaning notice board), `lever` (up/down), `campfire` (flicker), `barrel`,
`crate`, `urn` (each with an intact + shatter frame), `lore_stele` (a readable slab).

**Shallows:** dead reeds, drowned rowboat, fishing net on a post, crab-shell pile, mooring bollard, broken jetty plank, kelp clump, buoy, salt-crusted anchor, tide pool, driftwood, gull skeleton.
**Salt Mines:** ore cart, pickaxe in a wall, salt stalagmite, lantern hook, support timber, coiled cable, slag heap, cracked bell, ore vein cluster, water pump, dust pile, calcified glove.
**Pit Below:** dead carousel horse, ticket booth, popcorn cart, striped tent pole, snapped rope coil, funhouse mirror, ring-toss stand, deflated balloon cluster, clown shoe, prize shelf, cage, bunting string.
**Attic of Teeth:** rocking chair, boarded window, chest of drawers, hanging coats, birdcage, cracked mirror, stacked crates, oil lamp, torn wallpaper strip, mouse hole, spilled pen jar, music-box.
**Conductor's Hall:** music stand, stacked blank pages, broken chandelier, velvet rope post, melting clock (small), podium step, statue plinth, pipe-organ fragment, candelabra, drowned chair row, banner, hourglass.

*(One-line prompt each = the item name + "matching drowned-gothic pixel-art prop,
transparent, ~32×40, top-left light".)*

---

## 6. Landmarks

`assets/sprites/overworld/landmarks/<name>.png`, ~64×80 (primary up to 96×112),
silhouette-first, transparent, feet at bottom.

**Primary (1 per biome):** `drowned_ship` (Shallows — a sloop run aground, broken-backed,
one snapped mast), `salt_headframe` (Salt Mines — rusted mine winding-tower over a black
shaft), `carnival_wheel` (Pit — a half-submerged tilted Ferris wheel), `leaning_tenement`
(Attic — a condemned tenement leaning over the street, one lit attic window),
`conductor_spire` (Hall — a black obelisk-spire with a fused melting clock-face).

**Secondary (~2 per biome):** shallows: `lighthouse_stump`, `sunken_chapel`; saltmines:
`collapsed_gantry`, `salt_pillar_giant`; pit: `big_top_ruin`, `drowned_carousel`; attic:
`clocktower_lean`, `gallows_frame`; hall: `great_organ`, `throne_of_pages`.

---

## 7. Parallax backgrounds & weather

Per biome, **4 layers** for depth scrolling + the composite arena scene. Layers:
`<biome>_sky.png` (far gradient/sky, static), `<biome>_far.png` (distant silhouettes,
slow), `<biome>_mid.png` (mid structures), `<biome>_near.png` (foreground band, fast).
320×180 (near can be wider), opaque sky / transparent overlays.

Plus the 5 **arena composite scenes** (the fight backdrops, each with its untold-story
set pieces — see PRD §11.1.1):
- `arena_shallows` — drowned village green, one boat straining at its rope.
- `arena_saltmines` — gallery of miners calcified mid-listen.
- `arena_pit` — sunken carnival ring, ropes snapped outward.
- `arena_attic` — clawed door from the inside, scrawled staves.
- `arena_hall` — blank pages (last row filled), melting stopped clocks.

**Weather overlays** (`assets/fx/weather_<name>.png`, tiling, scrolled in-engine):
`rain`, `mist`, `ash_fall`, `bubbles_rise`, `dust_motes`, `falling_pages`.

---

## 8. VFX library

`assets/fx/<name>.png`, transparent strips, additive-blended in-engine. Keep white/bright
so a single texture tints to any accent.

`hit_spark` (4) · `slash_light` (arc, 3) · `slash_heavy` (big arc, 4) · `parry_burst` (4) ·
`dash_trail` (3) · `dust_run` (3) · `dust_land` (3) · `splash_water` (4) · `blood_hit` (3) ·
`heal_bloom` (4) · `buff_ring` (4) · `proj_teal` / `proj_ember` / `proj_plum` (spin, 3 each) ·
`muzzle_flash` (2) · `impact_ring` (4) · `explosion` (6) · `death_dissolve` (5) ·
`status_poison` / `status_burn` / `status_stun` / `status_slow` / `status_shock` (aura, 3 each) ·
`chorus_light` (a soft descending god-ray shaft, 4) · `beat_pulse` (a ring on the beat, 3) ·
`groove_flare` (ultimate charge burst, 5).

---

## 9. UI kit

`assets/ui/...`, transparent. A complete, cohesive gothic-HUD kit.

**Frames & HUD:** `panel` (nine-slice window, bone-and-iron w/ rivets) · `panel_boss`
(blood-red trim + clock motif) · `hud_frame` (combat HUD housing) · `bar_hp`,
`bar_focus`, `bar_groove` (each: empty track + fill + cap, blood/teal/ember) ·
`tooltip` (small nine-slice).

**Icons — abilities** (`ui/icons/ability_<member>_<n>.png`, 16×16): 4 per member
(attack, special, ultimate, passive) = 16 icons, each a tiny emblem of that move.

**Icons — relics/items** (`ui/icons/<name>.png`, 16×16, ~20): metronome-charm,
salt-heart, drowned-locket, cracked-baton, pearl-tooth, ember-string, tide-glass,
rope-coil, page-quill, clock-gear, blood-vial, kelp-wreath, mask-shard, lantern-ember,
bone-pick, feather-plume, plum-sapphire, foghorn, tuning-fork, chorus-shell.

**Icons — stats/system** (16×16): `heart`, `focus_eye`, `groove_wave`, `coin`, `key`,
`potion`, `map_pin`, `echo`, `settings_gear`, `volume`, `motion`, `contrast`.

**Screens:** `title_logo` (wordmark "THE DROWNED CHORUS", bone letters half-submerged
in teal) · `menu_illustration` (a moody key-art scene of the band before the drowned
skyline) · `map_screen` (a stylized parchment world map frame) · `pause_panel` ·
`results_panel` · `dialogue_box` + `nameplate` · `cursor` (a small baton/pointer) ·
`button` (3 states: normal/hover/press) · `portrait_frame`.

**Font:** `font_body` and `font_display` — bitmap pixel fonts (uppercase + lowercase +
digits + punctuation), display weight more ornate/gothic. Deliver as a glyph sheet.

---

## 10. NPCs

`assets/sprites/npcs/<id>/*` — each `idle` (2) + `talk` (2) + a 64×64 portrait.

**Old band-era heroes, now townsfolk (4):** `ex_warrior`, `ex_tank`, `ex_mage`,
`ex_healer` — the four generated adventurers, weathered, loitering by the shore.
**New NPCs (~6):** `luthier` (instrument-mender vendor), `saltwife` (a Salt Mines
widow), `barker` (a defeated carnival barker), `archivist` (keeper of the blank pages),
`ferryman` (a hooded boat-poler), `child_of_the_choir` (a small masked chorister).

---

## 11. Items & pickups

`assets/sprites/pickups/<name>.png` (world) + reuse the 16×16 icon for UI. Transparent.

`health_orb` (teal, bob+glow) · `coin_small` / `coin_large` (ember, spin) · `key` ·
`echo_mote` (a drifting lore fleck) · `map_fragment` · the **15 relics** (world-pickup
versions of the relic icons in §9) · `chorus_shard` (a story collectible) ·
`tuning_fork` (save token) · `bandage` (heal consumable) · `ember_vial` (buff consumable).

---

## Tips for AI pixel-art generation

- Say **"pixel art", a resolution feel** ("32×32 pixel art", "16-bit", "crisp pixels,
  limited palette, no anti-aliasing"); generate large, I downscale.
- **Lock the palette** — paste the hex list and/or attach a swatch. Cohesion across the
  ~575 slots matters more than any single image.
- **Spritesheets are the hard part.** Generate one strong reference pose per character,
  then "same character, same outfit, now <state>", and send poses separately — I pack
  the strips. Feed each new prompt your last good asset as a **style reference**.
- **Transparent backgrounds:** "isolated sprite, transparent background, no scene." If a
  tool bakes a background, send it anyway — I can key it out.
- **Tiles must tile & autotile:** "seamless tileable texture, edges wrap"; for autotile,
  ask for "edge and corner pieces on a grid." I verify seams and fix artifacts on import.

## How to hand assets back

1. **Commit** PNGs into the paths above and tell me they're in, **or**
2. **Attach** them here and say which slot(s), **or**
3. Drop a **folder/zip** and I'll sort it.

Per asset I run it through the **importer** (`tools/pixelart/import_asset.py`), which
palette-quantizes to the master palette, keys out a flat background, downscales, and
slices/repacks frames to the engine's exact size — then I drop it into the right
`assets/` slot, wire it (new enemies/animation states get their loaders + state
machines), verify in-browser, and deploy. Example:

```bash
# a 6-frame 48x48 run cycle, green-screen background keyed out:
python3 tools/pixelart/import_asset.py --input raw_run.png \
    --out assets/sprites/band/vocalist/run.png --frame 48x48 --frames 6 --key '#00ff00'
# a 4-tile 16x16 tileset row (opaque, no keying):
python3 tools/pixelart/import_asset.py --input raw_tiles.png \
    --out assets/tilemaps/shallows_terrain.png --frame 16x16 --grid 4x1 --opaque
```

The manifest fills row by row — the game climbs to real AAA one asset at a time,
starting from the one that already is: **Amir**.
