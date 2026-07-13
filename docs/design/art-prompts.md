# The Drowned Chorus — Art Generation Prompts

Everything you need to generate the game's art with any AI image tool (or hand
to an artist), then drop the results back for me to wire in. The engine loads
PNGs directly — **there is no pixel-for-pixel transcription step.** You generate
the image, put the PNG in the repo (or send it to me), and I quantize it to the
palette, slice it into frames, and wire it into the game — exactly how the
provided **Amir** guitarist already works.

---

## How to use this file

1. **Prepend the [Global Style Block](#global-style-block) to every prompt.** It carries
   the world, register, palette, and pixel-art constraints so all assets match.
2. Generate the asset from its section below. Generate **large and crisp**
   (1024×1024 is fine) — I downscale + palette-quantize to the target size, so
   don't try to hand-generate tiny 16px images.
3. **Transparent background** for anything marked *(cutout)* — characters,
   enemies, props, landmarks, UI pieces. Backgrounds/tilesets are opaque.
4. Save with the **exact filename** shown and drop it under the shown path, or
   just send it to me and say which slot it is.
5. For multi-frame sprites, either generate a **horizontal strip** in the frame
   order listed, or send me the individual poses and I'll pack the strip.

**Consistency tip:** most generators let you attach a *reference image*. Use the
existing `assets/sprites/heroes/placeholder/Amir Stand.png` as the style anchor
for the band, and re-use your first good tile/enemy as a reference for the rest
so the set stays cohesive.

---

## Global Style Block

> Paste this before every prompt below.

```
Pixel art in the style of Hyper Light Drifter and Blasphemous — beautiful, moody,
gothic. Setting: "The Drowned Chorus", a surreal drowned/gothic world of ocean-floor
abyss, salt and rust, melting black clocks, bone and pearl, blood, rot-green, and a
looming Conductor. Dark, desaturated near-black base values with a few searing
accent hues: abyssal teal, plum/magenta, ember-gold, blood red. Strong readable
silhouettes, a consistent top-left light source, clean limited palette, subtle
dithering for shading (no gradients, no anti-aliased blur, no photo-realism, no
text, no watermark). Crisp pixels, high contrast, deliberate — not noisy.
```

**Master palette** (keep every asset within these hues; hex):

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

---

## Delivery spec (what each PNG must be)

| Asset | File / path | Display size | Frames | BG |
|---|---|---|---|---|
| Region tilesets | `assets/tilemaps/region_<name>.png` | 16×16 per tile, 4 in a row (grass, path, water, rock) | 4 | opaque, **seamlessly tileable** |
| Band: idle | `assets/sprites/band/<member>/idle.png` | 48×48 per frame, horizontal strip | 4 | transparent |
| Band: run | `assets/sprites/band/<member>/run.png` | 48×48 per frame | 6 | transparent |
| Band: attack | `assets/sprites/band/<member>/attack.png` | 48×48 per frame | 3 | transparent |
| Enemies | `assets/sprites/enemies/<id>.png` | 48×48 per frame | 2 (idle) | transparent |
| Boss (Conductor) | `assets/sprites/enemies/conductor_colossal.png` | 96×128 per frame | 2 | transparent |
| Arena backgrounds | `assets/backgrounds/arena_<name>.png` | 320×180 (whole scene) | 1 | opaque |
| Overworld props | one PNG per prop, I'll pack them | ~32×40, feet at bottom | 1 | transparent |
| Region landmarks | one PNG per landmark | ~64×80, feet at bottom | 1 | transparent |
| UI panel | `assets/ui/panel.png` | 48×48 nine-slice frame | 1 | transparent center |
| Stat icons | `assets/ui/icons.png` | 16×16 each, 3 in a row (heart, focus, groove) | 3 | transparent |

> Generate bigger than these sizes; I downscale. "Frames" = distinct poses I'll
> slice into a strip. If a tool can't do exact frame counts, send me whatever
> poses you get and I'll assemble them.

---

## 1. Overworld tilesets — 5 regions

Top-down tiles for the walkable world. Each region is one image with **4 tiles in
a row: grass, path, water, rock**, all 16×16, **seamlessly tileable** (edges wrap).
One dominant accent hue per region so the biomes read as distinct moods.

**1.1 Shallows** — `region_shallows.png`
```
Top-down 16x16 game tileset, 4 seamlessly-tiling tiles in a row: (1) drowned coastal
turf — dark teal-green moss with wet grass tufts; (2) a pale bone/salt cobblestone
path; (3) shallow abyssal seawater with gentle teal wave crests and pearl foam;
(4) wet dark barnacled shoreline rock. Dominant accent: abyssal teal (#49c6bd).
```

**1.2 Salt Mines** — `region_saltmines.png`
```
Top-down 16x16 game tileset, 4 seamlessly-tiling tiles: (1) salt-crusted ochre ground
with dried moss; (2) a worn ember-lit mine road of pale stone; (3) brackish flooded
shaft water; (4) rusted ore-veined rock. Dominant accent: ember-gold (#f0a648).
```

**1.3 Pit Below (drowned carnival)** — `region_pit.png`
```
Top-down 16x16 game tileset, 4 seamlessly-tiling tiles: (1) trampled violet-tinged
fairground grass; (2) a cracked plum-stone midway path; (3) deep sunken pit water;
(4) dark amethyst rubble rock. Dominant accent: plum/magenta (#8a52a0).
```

**1.4 Attic of Teeth** — `region_attic.png`
```
Top-down 16x16 game tileset, 4 seamlessly-tiling tiles: (1) rust-brown rotted-wood
floorboards with grime; (2) a narrow rust-stained plank path; (3) black leak-water;
(4) crumbling brick/plaster rock. Dominant accent: rust (#a8431c).
```

**1.5 Conductor's Hall (flooded plaza)** — `region_hall.png`
```
Top-down 16x16 game tileset, 4 seamlessly-tiling tiles: (1) drowned deep-plum plaza
stone; (2) a processional bone-tile path; (3) still black flood water with faint
reflections; (4) dark obsidian statue-stone. Dominant accent: deep plum (#4b2a57).
```

---

## 2. The band — Inhalants (playable party)

Side-view, facing right, punk/gothic rock band. **Keep them consistent with Amir**
(dark-brown skin, spiked grey hair, black clothes, white tank — attach his sheet as
a style reference). Each member: **idle (4 frames), run (6 frames), attack (3
frames)**, 48×48, transparent, feet on the bottom line.

**2.1 Amir — lead guitarist** — `band/amir/{idle,run,attack}.png`
```
Side-view pixel-art character sprite sheet, facing right: a lean dark-skinned punk
rocker with a spiked grey mohawk-ish cut, black sleeveless top over a white tank,
black jeans, carrying an electric guitar slung across his body. Frames: 4-frame
breathing idle, 6-frame dynamic run (guitar bouncing), 3-frame guitar-swing attack
(windup, downward swing, follow-through). 48x48 per frame, transparent background.
```
*(You already provided Amir; only regenerate if you want the whole band in one
new unified style.)*

**2.2 Bassist — second guitarist / bass** — `band/bassist/{idle,run,attack}.png`
```
Same style/scale as Amir, a different band member facing right: broader build, tall
red-dyed mohawk, sleeveless black vest, a heavy bass guitar held low. 4-frame idle,
6-frame run, 3-frame attack swinging the bass headstock like a club. 48x48, transparent.
```

**2.3 Vocalist** — `band/vocalist/{idle,run,attack}.png`
```
Same style/scale as Amir, facing right: lithe front-person, high spiked hair, torn
white shirt under a black jacket, gripping a microphone with a trailing cable.
4-frame idle, 6-frame run, 3-frame attack thrusting the mic forward mid-scream (a
faint teal shock at the mic). 48x48, transparent.
```

**2.4 Drummer** — `band/drummer/{idle,run,attack}.png`
```
Same style/scale as Amir, facing right: sturdy build, shaggy hair under a bandana,
black tank, a drumstick in each hand. 4-frame idle, 6-frame run, 3-frame attack
crashing both sticks down. 48x48, transparent.
```

---

## 3. Enemies

Side/front, generally facing left (toward the player). Colossal, silhouette-first,
with faint additive glow on eyes. **2-frame idle** unless noted. 48×48, transparent.

**3.1 Slime** — `enemies/slime.png`
```
A drowned rot-slime: a gelatinous mound of dark rot-green and moss with bubbling
pearl-white spots and two dim glowing eyes, dripping brine. 2-frame idle (squash and
settle). 48x48, transparent, faces left.
```

**3.2 Drifter** — `enemies/drifter.png`
```
A hooded abyssal wraith-drifter gliding above the floor, tattered teal-black cloak,
a single glowing teal eye-slit, skeletal hands. Hyper Light Drifter register.
2-frame idle (cloak sway). 48x48, transparent, faces left.
```

**3.3 Luchador grunt** — `enemies/luchador_grunt.png`
```
A drowned masked wrestler ("clave" motif): waterlogged luchador in a cracked
ember-gold mask, barrel chest, bandaged fists, rope belt. Menacing, gothic. 2-frame
idle (breathing). 48x48, transparent, faces left.
```

**3.4 Luchador mask (elite)** — `enemies/luchador_mask.png`
```
An elite luchador: taller, a gleaming blood-red and bone mask with too many eye
holes, cape of kelp, glowing red seams. 2-frame idle. 48x48, transparent, faces left.
```

**3.5 Elite wraith** — `enemies/elite_wraith.png`
```
"Teeth like pearls and hair like feathers": a tall spectral wraith, gaunt, feathered
hair, a wide pearl-toothed grin, trailing tattered plum shroud, glowing magenta eyes.
Beautiful and unsettling. 2-frame idle (drift). 48x48, transparent, faces left.
```

**3.6 The Conductor (standard)** — `enemies/the_conductor.png`
```
The Conductor: a gaunt towering figure in a dripping black tailcoat, a melting clock
for a heart, baton raised, faceless under a wide hat, glowing amber clock-light.
2-frame idle (baton sway). 48x48, transparent, faces left.
```

**3.7 The Conductor — COLOSSAL boss** — `enemies/conductor_colossal.png`
```
The Conductor as a screen-filling boss, authored at full size (not upscaled): a
colossal gaunt maestro in a vast black melting tailcoat, a great cracked clock-face
heart dripping molten gold, two long baton-arms, blank pages swirling, faceless void
under the hat with two burning amber pinpoints. Awe and dread, HLD scale contrast.
2 frames (conducting up, conducting down). 96x128 per frame, transparent, faces left.
```

---

## 4. Battle arena backgrounds — 5 regions

Full 320×180 side-view scenes the fight plays over. Each is a specific place with an
**untold story told through set pieces** (no text). Opaque. Layered depth (fog,
atmospheric perspective), one beat-pulsing focal light per scene.

**4.1 Shallows** — `arena_shallows.png`
```
Side-view pixel-art battlefield, 320x180: a drowned village green under shallow teal
water at dusk. Set pieces: sunken cottage foundations, a single fishing boat still
straining upward against a taut mooring rope (everyone left but one). Soft god-rays
through teal water, atmospheric fog, a lantern glow focal point. Moody, beautiful.
```

**4.2 Salt Mines** — `arena_saltmines.png`
```
Side-view battlefield, 320x180: a salt-mine gallery, walls glittering with ember-lit
salt. Set piece: a row of miners calcified mid-listen, one caught mid-stride, faces
turned toward an unseen sound. Warm ember-gold rim light, dust motes, deep shadow.
```

**4.3 Pit Below** — `arena_pit.png`
```
Side-view battlefield, 320x180: a sunken carnival ring half-underwater, dead lantern
strings, a tilted ticket booth. Set piece: circus ropes snapped and flung OUTWARD, as
if something broke loose from the center. Plum/magenta glow, drifting bubbles, unease.
```

**4.4 Attic of Teeth** — `arena_attic.png`
```
Side-view battlefield, 320x180: a claustrophobic attic interior, rust and rotted
timber, boarded window leaking grey light. Set piece: deep claw marks gouged on the
INSIDE of the shut door, scattered pens, a scrawled musical staff. Rust palette, dread.
```

**4.5 Conductor's Hall** — `arena_hall.png`
```
Side-view battlefield, 320x180: a flooded grand hall / plaza before the Conductor.
Set pieces: rows of blank sheet-music pages (only the last row filled), melting clocks
stopped at the same moment, a raised podium. Deep-plum flood water, cold amber focal
light, vast and solemn.
```

---

## 5. Overworld props (scatter decoration)

Small top-down-ish cutouts placed on the map, drawn with a little face so they read
at an angle (like a JRPG overworld). ~32×40, transparent, feet at bottom, top-left
light, soft drop shadow baked in is fine. Send each as its own PNG; I'll pack them.

```
Set of gothic overworld decoration props, matching pixel-art style, transparent
background, small (~32x40), consistent top-left light, each its own image:
1. dead_tree   — a bare black twisted dead tree
2. tombstone   — a weathered bone-pale leaning headstone
3. bone_pile   — a small heap of pale bones and a skull
4. fungus      — a cluster of teal-capped glowing mushrooms
5. reeds       — a tuft of drowned marsh reeds
6. obelisk_shard — a broken shard of a teal-glowing stone obelisk
7. echo_rune   — a carved standing rune-stone with a glowing teal glyph socket
                 (this one is interactive — keep the glyph clean for an added glow)
```

---

## 6. Region landmarks (colossal set-pieces)

One big silhouette landmark per region for scale + story. ~64×80, transparent, feet
at bottom, silhouette-first. Send each as its own PNG.

```
1. drowned_ship  (Shallows) — a fishing sloop run aground, broken-backed, one mast
   snapped, hull staved in, kelp-draped.
2. salt_headframe (Salt Mines) — a rusted mine winding-tower / headframe over a black
   shaft, slack cabling.
3. carnival_wheel (Pit) — a drowned Ferris/fortune wheel, half-submerged and tilted,
   cars hanging, plum-lit.
4. leaning_tenement (Attic) — a condemned tenement leaning over the street, boarded
   windows, one attic light still lit.
5. conductor_spire (Hall) — a black obelisk-spire, faces blank, a single melting
   stopped-clock face fused to it.
```

---

## 7. UI

**7.1 Panel frame** — `panel.png`
```
A nine-slice UI window frame, gothic pixel-art: dark bone-and-iron border with corner
rivets, ornate but readable, transparent center (I stretch the middle). ~48x48 source.
Also a boss variant (panel_boss.png) with blood-red trim and a small clock motif.
```

**7.2 Stat icons** — `icons.png`
```
Three 16x16 pixel-art stat icons in a row, transparent, matching palette:
(1) heart — a blood-red heart (HP); (2) focus — a teal eye/tuning-fork (Focus);
(3) groove — an ember-gold pulse/waveform (Groove). Bold, readable at tiny size.
```

**7.3 Title logo** *(optional, nice-to-have)* — `title_logo.png`
```
A pixel-art wordmark reading "THE DROWNED CHORUS", drowned-gothic, bone letters
half-submerged in teal water with dripping ink and a faint melting-clock flourish.
Transparent background, ~240x80.
```

---

## Tips for AI pixel-art generation

- **Say "pixel art" and a resolution feel** ("32x32 pixel art", "16-bit", "crisp
  pixels, limited palette, no anti-aliasing"). Then generate large; I downscale.
- **Lock the palette** by pasting the hex list into the prompt and/or attaching a
  reference swatch. Consistency across assets matters more than any single image.
- **Spritesheets are the hard part.** Many tools won't nail a clean 6-frame strip.
  Easiest workflow: generate one strong reference pose per character, then generate
  the other poses "same character, same outfit, now running / now swinging",
  and **send me the poses separately** — I pack them into the strip.
- **Transparent backgrounds:** ask for "transparent background, isolated sprite, no
  scene". If a tool bakes a background, send it anyway — I can key it out.
- **Tiles must tile:** ask for "seamless tileable texture, edges wrap". I verify the
  seams and fix small artifacts when I import.
- **Reference image = consistency.** Feed each new prompt your last good asset as a
  style reference so the whole game reads as one world.

---

## How to hand assets back

Any of these works:

1. **Commit** the PNGs into the repo under the paths above and tell me they're in.
2. **Attach** them to me in chat and say which slot each is ("this is the shallows
   tileset", "this is the vocalist run").
3. Drop a **folder/zip** of everything and I'll sort, quantize, slice, and wire it.

For each asset I'll: quantize to the master palette, downscale to the target size,
slice multi-frame strips into the engine's frames, drop it into the right `assets/`
slot, regenerate anything derived, verify it in-browser, and deploy. You watch the
game climb to real AAA one asset at a time — starting from the one that already is:
Amir.
