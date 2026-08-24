# The Style Contract — *The Drowned Chorus*

**Status: FROZEN at v16.3 (M1).** This document is the authority on how every
pixel in this game is made. PRD §11.1.2 step 2 says "freeze the rules
immediately; never prompt each asset from scratch" — this is that freeze,
extended to cover the authored half of the pipeline too.

Change this document and the whole game moves together. That is the point. If
an asset does not comply, the asset is wrong, not the contract.

---

## 0. The bar

> A stranger shown any screenshot says *"that's a beautiful painting."*
> A stranger shown any two seconds of motion can tell you who is who.

Both halves are load-bearing. The first is why nothing here quantizes, dithers,
outlines or pixelates. The second is why the cast is authored rather than
generated, and it is the harder of the two — a beautiful frame in which the
player cannot find their own character is a failure, not a compromise.

## 1. The split, and why

**Characters are authored. Environments are generated.**

| | tool | why |
|---|---|---|
| Mir, Nari, Lunal, the Harrow, every foe | `tools/art/rig.py` + one module per character | identity across 22 states, exact silhouettes, real animation |
| ground, venues, props, set pieces, cutscene plates | `tools/art/gen.py` (Flux via Pollinations) | painterly depth and material variety at a scale no one can hand-paint |

This is not a preference. It is the result of five generation probes against a
canon-accurate description of Mir, recorded here so nobody re-runs them:

1. A long style block placed *before* the subject makes the style the subject —
   "steep / overhead / isolated" produced a mountain, not a man. **Subject
   first, short style tail.**
2. "Full body" is ignored roughly half the time. Even
   `ENTIRE BODY HEAD TO TOE INCLUDING BOTH FEET` crops at the thighs when the
   prompt also asks for a painterly render.
3. Forcing a 55° overhead camera produces isometric *dioramas*, not characters.
   The reference games (Hyper Light Drifter, Death's Door, Hades) use a
   **slightly** elevated three-quarter view; the contract was corrected to match
   what they actually do rather than what the camera spec said.
4. The endpoint has a hard prior toward lean handsome heroes. "Sedentary,
   unfit, forty" is silently overridden. Pushing hard enough to land the body
   type ("fat, balding, big round belly, double chin") swings the render to
   photorealism and breaks the style.
5. The combination is the real wall: **full-body + painterly + a specific
   unheroic body + an isolated background** cannot all hold at once, and
   nothing about prompt order fixes it.

Against that, note the size the game actually renders at: **Mir is 22 world
pixels tall.** Facial detail is worth nothing there. Silhouette, value
structure, palette and animation are worth everything — and all four are
exactly what a rig gives you and a generator cannot.

The old pipeline's answer to animation was to generate one pose and shift halves
of the bitmap around. That is why the cast used to animate like a jiggling blob.

## 2. The rig (`tools/art/rig.py`)

Figure space: origin between the feet, **+y up**, **+x forward (screen-left)**.
Every character faces screen-left natively and is flipped for the other
direction, because the game's sprites are side-facing and one run cycle serves
every direction.

- `Skeleton` — a tree of `Joint`s (offset, rest angle, length), solved to
  absolute positions and angles.
- `Shape`s hang off joints and carry **one** authored colour each:
  `Limb` (tapered capsule, optional `bow`), `Blob` (28-gon ellipse), `Poly`
  (authored polygon in joint-local space).
- `Painter` fixes the look for the whole game:
  - one key light from the **upper left**, as a masked linear gradient across
    each piece — never a flat fill, never a posterized ramp;
  - shadows keep blue (`_shade`), so darks read as cold air rather than mud;
  - a cool **rim light** on the lit silhouette edge (morphological erosion of
    the piece mask, subtracted);
  - a soft dark **halo** hugging the silhouette (`ao`). This is the single thing
    that lets one sprite read on both the Fold's pale silt and the Keep's
    near-black stone. A rim light alone cannot: it vanishes the moment the
    ground is brighter than the rim;
  - an additive **emissive** pass with spill, for the one warm accent per
    figure;
  - a faint deterministic grain, so large flats do not read as vector.
- Everything renders at **4× supersample** and downsamples with LANCZOS only.
- `Clip` keyframes `(pose, root_offset, scale, easing)`. `scale` may be a scalar
  or `(sx, sy)`; non-uniform scale is how a boneless creature gets real
  squash-and-stretch.

**Determinism.** There is no randomness anywhere — the grain is a hash of pixel
coordinates. The same source produces byte-identical PNGs, so a rebuild is a
no-op in git unless the art actually changed.

## 3. The palette (`tools/art/palette.py`)

"One palette, five moods" (PRD §11.1.1) only holds if the palette is a shared
object rather than a note in a doc, so that module **is** the discipline: every
authored colour is a named import, and each region pulls one dominant hue that
tints its own dressing (`tint()`).

Ground values `ABYSS / INK / SLATE / STONE`; five region hues
`FOLD / KELP / BREACH / SCAR / KEEP`; one warm accent family
`EMBER / BRASS / PARCHMENT`.

Two rules that took real iteration to learn, recorded so they are not undone:

- **The brightest thing on a figure must be small.** Mir's shirt at luma 132
  across his whole upper arm and chest made him a pale smudge with no
  silhouette. The shirt is now a dim mid-dark and only the *collar* keeps the
  clean linen value — one small bright note at the throat, where the eye already
  goes to read the head.
- **Foes separate by VALUE, not hue.** The rot slime was originally the same
  value and nearly the same hue as the Fold's silt, so it was invisible until it
  moved. It is now a lighter, yellower bile green.

## 4. The scale contract (`tools/art/contract.py` → `SCALE`)

One ground line, one set of sizes. Mir is the yardstick at **22 world px**, and
everything else is sized *in relation to him*, because the story is about the
difference between a man, his small son, and what is bigger than both.

| slot | frame | figure | render | world px |
|---|---|---|---|---|
| mir | 200 | 176 | 0.125 | 22.0 — the yardstick |
| nari | 200 | 104 | 0.125 | 13.0 — chest-high to his father |
| lunal | 200 | 180 | 0.125 | 22.5 — human-scaled on purpose (§8.7.1 #6) |
| harrow | 200 | 168 | 0.125 | 21.0 — **smaller** than Mir; his *work* is what is huge |
| slime | 128 | 104 | 0.25 | 26.0 |
| drifter | 140 | 122 | 0.25 | 30.5 |
| elite_wraith | 180 | 158 | 0.25 | 39.5 |

Frames are seated on a shared baseline (`gen.fit_frame`), so every character in
the game stands on one floor.

## 5. Readability — the three levers

Applied deliberately, per foe, and checked at true game scale on real ground
plates before anything ships:

1. **Silhouette class.** Mir is a narrow upright rectangle. No foe shares his
   proportions. The slime is a wide low dome (aspect inverted). The drifter is
   taller and thinner than Mir with a trailing hem. The wraith is a triangle
   that widens downward.
2. **Colour family.** Mir is cold slate-teal with one ember accent. Slime: bile
   green. Drifter: drowned brown-grey with a cold void where a face should be.
   Wraith: oxidised copper and violet.
3. **Telegraph pose.** A windup is *not* a scale tween. It is an authored pose
   that changes the silhouette class for the duration — the slime rears from a
   wide dome into a tall column, the drifter throws its arms wide, the wraith
   rises. This is what makes an attack readable in peripheral vision, on the
   beat, without reading a HUD.

**A state is only a state if the shape changes.** Every foe ships all six
(`idle, move, telegraph, attack, hurt, dead`).

## 6. The hands

world-bible §11 names one visual arc that runs the whole game: **the hands.**
Clean and precise at the Fold, ruined by the Keep. The hands are therefore
separate shapes with their own colour, and `mir.hands_wear(stage)` lerps
`MIR_SKIN → HARROW_HAND` and widens them 1.0 → 1.22, so an act can be
re-rendered without touching the rest of the figure.

The brass turning tool is on his belt, emissive, in **every** frame — including
the ones where nothing is happening — because it is what opens the cage in the
ending and the player has to have been looking at it for three hours.

## 7. Generation clauses (`tools/art/contract.py`)

Every generated slot is `STYLE + one per-slot subject line`. Nothing prompts
from scratch, so the whole set reads as one game. The clauses are `RENDER`,
`CAMERA` (pinned — every figure seen from the same height or the cast does not
stand on the same floor), `LIGHT` (one key for the whole game), `PALETTE`,
`ISOLATION`, `WORLD`.

Retired from the previous contract, and not to be reintroduced:

- "Pixel art / ordered dithering / crisp pixels" — PRD v11.0 retired deliberate
  pixelation as a style.
- "full body SIDE VIEW facing LEFT" — the game's camera looks down.
- "a looming Conductor" — world-bible v16.0 replaced him with the Harrow.
- "VIVID saturated neon" everywhere — the register is a vivid *limited* palette
  on desaturated near-black; the accent has to be the emissive, or nothing reads
  as emissive.

## 8. Build

```
python3 tools/art/build_cast.py                    # everything
python3 tools/art/build_cast.py mir slime          # just these
```

Output layout is also the engine's texture-key contract (`BootScene`):

```
assets/sprites/band/mir/<state>.png      -> band_mir | band_mir_<state>
assets/sprites/band/nari/<state>.png     -> band_nari | band_nari_<state>
assets/sprites/enemies/<foe>/<state>.png -> enemy_<foe> | enemy_<foe>_<state>
```

Frame counts are read off the loaded texture at runtime, so re-authoring a strip
can never desync the engine's animation ranges.

## 9. Review gate

PRD §11.1.2 step 5: a batch is not shipped until it has been *looked at*. Two
looks are required, and the second is the one that matters:

1. the contact sheet at source size, for craft;
2. **the sprite at true game scale, composited on the real ground plates it will
   fight on.** Every readability bug in this project has been invisible at
   source size and obvious at 22 pixels.
