# The Style Contract — *The Drowned Chorus*

**Status: FROZEN at v16.8 (M2).** This document is the authority on how every
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

The reason is the size the game actually renders at: **Mir is 22 world pixels
tall.** Facial detail is worth nothing there. Silhouette, value structure,
palette and animation are worth everything — and all four are exactly what a rig
gives you and a generator cannot, at any prompt length. Identity that has to hold
across 22 states and animate is not something you can prompt for twice and get
the same character.

### 1.1 The dilution law

**The single most important measured fact about the endpoint**
(`tools/art/probe_dilution.py`). One fixed subject clause at the end of a prompt,
one seed, padded only with bland non-contradicting filler:

| prompt length | is the subject in the picture? |
|---|---|
| 162 chars | **yes** |
| 587 chars | no |
| 1012 chars | no |
| 1522 chars | no |

There is no truncation cliff to sit under. The signal just thins until the clause
stops arriving, and it starts early. Therefore:

- **A long style preamble does not add style. It deletes subject matter.** The
  ~1000-character `RENDER + LIGHT + PALETTE + WORLD` stack is precisely the
  filler measured above.
- **Every prompt gets a hard character budget, asserted at build time**, with the
  canon-critical fact first (`plates.py`, `BUDGET = 340`). If a prompt needs
  something more, cut something else — never append.
- **Negations barely register.** "NO SKY, NO CLOUDS, NO HORIZON" as a tail
  returned a grey sky with a horizon in it. Say positively what occupies that
  region instead: *"black water is what is overhead"*. The first version of the
  dilution probe was invalid for this exact reason — it asked for "BRIGHT GREEN,
  not red" after establishing a red chair, and the chair stayed red at every
  length including 131 characters.

### 1.2 Probes that the dilution law corrects

Four probes against a canon-accurate description of Mir were previously recorded
here as evidence of hard model limits. Three still stand; two do not, and are
kept with their correction rather than deleted, because a retired finding that
looks like a live one gets re-derived:

1. Forcing a 55° overhead camera produces isometric *dioramas*, not characters.
   The reference games (Hyper Light Drifter, Death's Door, Hades) use a
   **slightly** elevated three-quarter view; the contract was corrected to match
   what they actually do rather than what the camera spec said. **Stands.**
2. The endpoint has a hard prior toward lean handsome heroes. "Sedentary, unfit,
   forty" is silently overridden, and pushing hard enough to land the body type
   swings the render to photorealism. **Stands** — this is a prior, not a
   dilution artifact.
3. ~~"Full body" is ignored roughly half the time.~~ **Corrected:** those prompts
   were over 1500 characters. The instruction was being diluted, not refused.
4. ~~The combination full-body + painterly + unheroic body + isolation cannot
   hold at once.~~ **Corrected:** untested at a sane prompt length. It may well
   hold under budget.

Neither correction reopens the decision. The split rests on §1's first paragraph
— identity, animation, 22-pixel readability — not on these two probes.

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

### 4.1 Environment: four laws measured on the Fold's town kit

The scale contract above governs *figures*. Building the Fold's town
(`tools/art/env_fold.py`, `tools/overworld/place_fold.py`) measured four more
that govern *architecture*, each of which cost a visibly wrong build first.

**1. A facade is as wide as it is tall.** The first houses were 30 rig units
wide and 196 tall. At the canonical world scale that is 9m tall and 2.8m wide,
and the town previewed as six **lighthouses** standing in a field. Bodies are
now 1:1 to 1:2, never 1:3. Corollary: **keep the frame tight to the art**, since
`worldScaleFor` scales by source *height* — empty pixels above a roof silently
shrink the building.

**2. Architecture is authored ~30% darker than it reads right in isolation.**
The overworld lays additive haze and god-rays over everything, and a tall sprite
collects more of both than a low one — so a building is lifted toward the light
far harder than a prop is. Stone that previewed correctly against dark silt came
back from the game as a pale grey-blue billboard. `STONE` went 58,70,76 →
40,49,55, which is what leaves the lit windows as the brightest thing on the
street. The inverse also holds: the kneeling stones sit on *pale* paving and are
too low to collect haze, so they had to go the other way to stop reading as a
ring of black tyres. **Author for the frame the piece will actually sit in.**

**3. Density is what separates a town from some buildings.** At world scale,
individually-placed houses must sit ~4 tiles apart to avoid overlapping, and a
street of 4-tile gaps reads as a hamlet. Real towns are terraces: `house_row` is
three houses sharing two party walls as ONE piece, with bay heights, doors and
lit windows jittered off `_h`. One placement, a whole street front. The empty
middles then need small props (`well`, `crate_stack`, `cart`) — a plaza with
nothing in the middle of it is a field.

**4. A prop is legible from a fixed short list of features, and it needs all of
them.** The handcart drew as a tilted bed, one wheel and a single raised shaft,
and read unmistakably as a **cannon**. A cart needs a level bed, two wheels at
different depths, and two shafts running to the ground. When a piece reads as the
wrong object, the fix is never more detail — it is the missing structural
feature.

Two smaller rules from the same build:

* **`Blob` defaults to the figure rim (1.0), and on architecture it shows.**
  Every wheel, kneeling stone and salt heap came back wearing a bright teal
  outline — a neon decal, not a rim light. Stone, iron and timber go through
  `blob()` at `STONE_RIM = 0.22`; only emissive flames want the full treatment.
* **One window in four is dark** (`DARK_RATE`). With every window in every house
  lit, the Fold read as a gingerbread village. Some windows being out is truer,
  quieter, and it matters later, because the story is about somebody leaving.

### 4.2 Placement is checked, not eyeballed

Props in this world are placed by hand, and by hand is right — but a hand cannot
see a **footprint**. A 7m house is 3.3 x 6.6 tiles and covers the seven tiles
*north* of the one it stands on, because sprites are drawn from their base.
Eyeballing coordinates off a map puts buildings on roads.

So `tools/overworld/place_fold.py` holds the authored placements *next to a
checker*, and validates every one against `assets/tilemaps/overworld.json`:
no piece may cover a path tile (the arch and the kneeling stones are exempt — a
gate that does not straddle its road is a decoration in a field) or a water
tile; pieces **should** stand on rock, which already blocks movement, so that
the collision layer and the picture finally agree; and nothing may share ground
with anything else. `--preview` renders the result at true world scale before it
is written, because a layout is not shipped unlooked-at (§9).

Two findings worth keeping from writing it:

* **The map already had architecture in it.** `generate_overworld_map.py` laid
  hollow rectangles of rock around the Fold — (17-21, 166-170), (30-34,
  162-166), (26-30, 177-181). Those are walled yards, and nothing had ever been
  drawn on them.
* **Ground contact, not bounding boxes, is the overlap test.** A lamp standing in
  front of a house is inside the house's box by definition, and the engine
  already sorts by base Y. What is actually broken is two pieces standing on the
  same ground.

### 4.3 The flat-patch law (the painted ground)

The ground plate (`tools/overworld/paint_ground.py`) is 5696 x 3200 px of
procedural painting composited in ~25 passes, and it shipped with **136
mathematically flat blocks** in the Fold alone — hard-edged untextured patches,
about 96 x 72 px each, on the most-looked-at surface in the game. They were
found by measurement, not by eye: scan every 8x8 block of each chunk PNG and
flag the ones whose per-channel standard deviation is under 0.6.

The cause is one mistake made three times:

> A pass that **fully replaces** the canvas owes it the grain back.

The base ground field carries four noise terms — cell-160, cell-36, cell-7, and
per-pixel `grain`. The eelgrass beds, the path ribbon, and the water fill all
*overwrite* it (`canvas[mask] = col[mask]`, or a blend weight that saturates at
1.0) with a colour carrying only the **cell-36** term. A cell-36 term moves by
about 1/200 of its range across eight pixels. The elevation pass then multiplies
by a **quantized** terrace tone, which is constant inside a terrace. Constant
times constant is flat, exactly, and 8-bit output rounds the last of it away.

Two rules follow, and both are cheap:

* Any full overwrite re-supplies `n_hi` and `grain` at the same order as the
  field it replaced. Smoother materials get smaller amplitudes (water 0.05,
  road 0.09, eelgrass 0.11) — never zero.
* A saturating mask is a full overwrite. `np.clip((n - 0.55) / 0.12, 0, 1)` is
  1.0 across most of its blob, not a soft blend, and the thing it blends *to* is
  therefore the only thing on screen there.

The generalisable part is the method. Flatness is invisible to a reviewer
looking at a 5696px image scaled to fit a window, and obvious to four lines of
numpy. Anything the eye cannot audit at the size it ships at gets a measured
gate instead (§9).

### 4.4 Engine primitives are a placeholder, including for landmarks

§0 says an abstraction is not an image. The Fold shipped with the rule broken on
the single most-looked-at object in the game: the town obelisk — the landmark
the town is built around (world-bible §2), the save point the player returns to
all game, and the object the premise hangs off — was drawn by
`OverworldScene.placeTownObelisk` as five `Graphics` polygons and five identical
cyan rectangles. In the build it read as a grey gradient **wedge with tick
marks**.

It is authored art now (`tools/art/env_fold.py` → `obelisk`), and the four
things that turned a wedge into stone are reusable:

1. **Volume in five stepped bands, not two.** A two-tone split puts its whole
   value jump on one hard line down the middle and reads as folded paper. Five
   bands following the taper read as a quarried shaft — and the fourth band is
   the *shadow turn*, which has to start before the silhouette edge or the dark
   side looks pasted on.
2. **It was built.** Seams, kept faint and only on the lit side. Eleven
   full-width courses with lit lips turned it into a stack of floors, which
   together with boxed glyph panels read as an **office tower**.
3. **Damage.** Chips off both edges, a corner off the plinth. An undamaged
   monolith at the bottom of the sea is a render, not a place.
4. **An old waterline.** Salt crust at the plinth and again a third of the way
   up, where the sea used to stand — the game's whole geography in one detail.

Three failures worth keeping, because each was a plausible choice:

* **A spire plus a wide plinth is a rocket.** A real obelisk is nearly a slab —
  31 units at the foot to 17 at the shoulder over 372 of height. The first cut
  ran 34 → 13 on a 124-wide two-tier pad and read as a launch vehicle.
* **Boxed glyph panels are lit windows**, and a tower of lit windows is the one
  thing this must not be. The fix for that — one continuous recessed channel of
  worn marks, running the shaft's full height — previewed as a weathered text
  and then failed **worse** in the browser, twice over, which is why §4.5 exists:
  a centred column of regularly-spaced marks is a **ladder**, and the channel's
  own lit lip put a hard highlight up the middle of the slab so the shaft came
  apart into a **bundle of pipes**. A ladder up a tall shaft with a lit tip is a
  launch gantry — the exact read the taper fix above had just bought off.
  The inscription now sits in a shallow panel in the **bottom third only**, with
  no lit lip, several marks per line at a varied left margin, and the odd
  upright stroke. See §4.5.
* **The lighting was hiding the art.** The old teal body-glow was a scale-1.0
  wash tuned to give a flat polygon presence; over the sprite it bleached out
  the courses, the chips and the waterline. When art replaces an abstraction,
  the effects that were propping the abstraction up have to come off with it.

The §4.1 haze law bites twice as hard here: with the lit band at 20% of the
shaft the monolith arrived **paler than the houses**. The lit band is a 7%
sliver now.

And one scale-clamp rule fell out of the same pass. `ring_stone` ships at
`MIN_SCALE` — **12 × 6 pixels**. Its three-blob build rendered the polished
highlight sub-pixel while the wide dark contact blob survived, so the kneeling
rings came back as black beans on pale paving. A piece that clamps at
`MIN_SCALE` gets two tones and no baked contact shadow: the placement pass
already draws a proportional one, so a second darkens the average for nothing.

### 4.5 Two laws about geometry, both found in the browser

Both of these shipped past an offline contact-sheet review and were obvious in
the first in-game frame. They are the reason `tools/capture.mjs` is a gate and
not a convenience.

**REGULAR REPETITION IS A MACHINE.** Evenly-spaced marks are the strongest
pattern the eye has, and it will name the machine before it names the material.
Measured, in this kit: a centred column of dashes became a *ladder*; eleven
full-width courses became *storeys*; one vertical strap per crate became a
*xylophone*; two dark discs under a cart became a *table*. Nothing in this world
is machined, so every repeat has to be broken on at least two axes — count,
spacing, length, **and** offset. Breaking one is not enough: the obelisk's marks
already varied in length and were a third worn blank, and they still read as
rungs, because they were all horizontal and all on the centreline.

**AN ATTACHMENT'S BASE COMES FROM THE SURFACE IT ATTACHES TO.** Derive it, never
take it from a nearby landmark value. `house_row` measured its chimney base off
`apex` — the ridge — and then placed the stack two-thirds of the way *down* the
slope, so it hung ~20 px clear of the tiles: two chimneys floating in open water
above the terrace, and the same bug sat in `house_tall`. The fix is a `roof_y(x)`
closure and the stack's **downhill** corner (the lowest point of its footprint),
buried a few units under it — which then holds at every roof height the `_h`
jitter can pick, instead of at the one that was eyeballed.

A corollary for figures: **light direction is information, and it is free.** The
shrine's stone child was a 9-unit `SALT` head over a 13×20 `SALT` ellipse in a
22×42 black niche — one pale egg in a phone booth, and the largest object in the
piece was also its brightest, which §3 forbids. The votive sits *below* it, so
carving the value gradient upward-dark turns the same lump into a thing being lit
by a candle. Stone tones, a shoulder taper, a ledge to stand on, and the candle's
shadow thrown up the back wall as proof of the direction.

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

### 7.1 Cutscene plates

The seven stage plates (`tools/art/plates.py`) are the game's told beats — the
only moments it says something outright, and the first thing a new player sees.
They used to be a handful of procedural rectangles; the stone child the whole
premise hangs on was two grey circles with two dots for eyes, against
world-bible §0's *"an abstraction is not an image."*

**The split runs through the plates too.** Five are generated; two are drawn:

| plate | how | why |
|---|---|---|
| fold, litho, house, waterline, scar | generated | organic, material-rich — a wet street, a bench of brass tools, a slope of sunken hulls |
| **obelisk, rain** | **authored** (`tools/art/authored.py`) | geometric and particulate |

The authored two are not a preference either. Six batches could not get one flat
vertical slab out of the endpoint — it returned a mountain, a canyon, a *framed
painting of* a canyon, and a pair of brutalist office blocks — and none produced
a single visible falling raindrop, offering a waterfall and a mossy gorge
instead. Both images are a few dozen lines of PIL, exactly on canon when drawn,
and deterministic. **Fighting a prior you can simply draw is a waste.**

Three rules the plates cost real batches to learn, beyond §1.1's dilution law:

1. **Frame the shot so the contradiction cannot fit.** "A town on the deep-sea
   floor, no sky" returned a moonlit canal town under clouds. Shot up a narrow
   street, there is no room in the frame for a sky. Composition enforces canon;
   adjectives do not.
2. **Lead with the load-bearing noun.** As a trailing clause, the sunken hulls
   vanished and left bare seabed, the trenches left a flat empty plain, and the
   rain left a handsome dry street. Whatever the beat *is*, it goes first.
3. **Name the material twice when the subject could be alive.** "An idol with an
   infant's face" gave an adult relief carving; "swaddled infant" fixed the age
   and summoned newborn *photography* — a real, living, pink baby. "Stone
   carving … colourless stone … deep shadow" is what has no breath behind it.

Plates are 1280×720, native 1:1 on the 320×180-at-4× canvas, placed at scale
0.25, and the scene enforces its own text scrim rather than trusting the art to
stay dark where the words go.

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

And a third look that is not a look at all. Some defects are invisible to *both*
of the above — a 96 x 72 patch of dead colour in a 5696 x 3200 plate is one pixel
of a window-fit review and unmissable under the camera. Those get a **measured**
gate:

* `npm run art:check` — `tools/overworld/check_plate.py`. Flags every cluster of
  8x8 blocks whose per-channel σ is under 0.6 and fails the build on any cluster
  of four or more. Exit code, not an opinion.
* `npm run art:ground` — repaints the plate and runs that gate immediately, so a
  new pass cannot land a flat patch without saying so.
* `node tools/capture.mjs` — boots the real game through the audio gate and
  frames named tiles, because no offline preview shows what the overworld
  actually composites: haze, god-rays, region grade, painted ground, and
  `worldScaleFor`. The Fold's houses previewed correctly and arrived in-game as
  a pale billboard.

The rule behind all three: **anything the eye cannot audit at the size it ships
at gets a number instead.**
