# The Style Contract — *The Drowned Chorus*

**Status: FROZEN at v17.0 (M3).** This document is the authority on how every
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
- **There is no purple in this world, and the UI did not know that.** The master
  palette in `tools/pixelart/skatopia.py` still carries the previous art
  direction's plum family (`P`/`p`/`u`, captioned "sapphire purses, twilight,
  esoteric"), and two of the most-looked-at pieces of interface in the game were
  keyed to it: the nine-slice panel frame — which draws round the player's HP in
  **every fight** — and the groove meter's fill. An 0x8a52a0 orchid border in a
  world of teal, stone, salt and lamp-amber does not read as a choice, it reads
  as a leftover from another game, which is exactly what it was. The frames are
  ocean and rust now, and groove is bone (it has to be legible against HP's teal
  and focus's amber without inventing a fourth hue). **A shared palette module
  is not a palette: an unused hue family sitting in the table is a loaded gun,
  and the check is to grep the game's own hex literals, not the table.**

- **The gun was still loaded, and it went off twice more.** The bullet above was
  written after the panel frame and the groove bar; it turned out to be the
  *third* time those three keys had been picked up, not the last. Grepping the
  game's own literals is necessary and it is not sufficient — it only sees code.
  Two more purple surfaces were shipping where no hex literal named them:

  - `tools/pixelart/tiles.py` carried its own five-entry region-accent table,
    keyed to the retired cosmology's region names, reaching for `PALETTE["P"]`
    (orchid) and `PALETTE["p"]` (plum) for the last two. That tinted **20 of the
    20 region ground tiles**, two whole regions of them.
  - `tools/art/palette.py` defined `KEEP = (142, 123, 181)  # storm violet`,
    cited to PRD §8.8.1, and `paint_ground.py` tinted region 4's terrain and
    marble from it. `ground_plate_0_5.png` measured **86.6% purple pixels**.

  So the audit that actually works is on the **shipped bytes**: walk every PNG in
  `assets/`, convert to HLS, and count pixels in the forbidden hue band. It found
  twelve files in seconds and needed no knowledge of which tool wrote them. Run
  it before shipping — *the palette a game has is the one in its pixels.*

  The keys are now **deleted** from `_HEX` rather than left unreferenced.
  `render()` raises `KeyError` on an undefined key, so the next reach for purple
  fails at build time. An unused hue family is not dormant, it is available.

- **A retired cosmology leaves its colours behind after its nouns are gone.**
  `KEEP` was violet because the fifth region used to be a *carnival* — `docs/design/art-prompts.md`
  still describes "trampled violet fairground grass, cracked plum midway,
  amethyst rubble; accent `#8a52a0`". The **nouns** were retired (`pit`,
  `attic`, `hall`), and everyone could see those were stale. The **hue** survived
  the rename, because a colour constant does not say what it is for. Nothing in
  the PRD ever asked for violet: §8.8.1 asks only that each region own an accent.
  When a world is re-cut, re-derive its colours from the new world, not from
  which constants still resolve.

  What replaced it is the point. World-bible §6.5: the Keep is "warm, lit,
  stocked, comfortable. Padded bars, and no door on the inside." It is the **last**
  region and it has to be the **warmest place in the game**, or Lunal's offer is
  not tempting and the ending is not a choice. So the fifth accent is the game's
  own brass lamplight — the same value as the prayer-lamps and Mir's tool. The
  trap is lit like everything the player spent four regions learning to trust.
  Region 4's ambient particle changed with it: violet *spores* became **dust in
  lamplight**, because a spore is something growing and this room is the opposite,
  and because motes turning over in warm light is the most domestic image there is.

- **Two tables that must agree, and are edited separately, do not agree.** The
  tile accents and the ground-plate accents tint art that is composited *in the
  same pixel* — tiles are laid on the painted plate. They were two hand-kept
  copies (and `tools/art/palette.py` was a third), so of course they had drifted:
  `tiles.py` had salt-mine **orange** where the plate underneath had kelp
  **green**. Purple was the defect that got them looked at; the divergence was
  the bug. `tiles.py` now imports `paint_ground.ACCENTS` — one accent per region
  in the whole pipeline, and a tile can no longer disagree with the dirt it sits on.

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

### 4.6 Placeholder art does not announce itself, and effects are not states

**A file called `placeholder` will ship.** `assets/sprites/env/shared/save_obelisk.png`
came out of `tools/pixelart/placeholder_cast.py` — the word is in the filename —
and it was a 29x38 flat rounded rectangle with a cyan lozenge down the middle. It
is the **save point**, placed beside every fight node in all five regions: after
Mir himself it is the most-touched interactive object in the game, and it had
survived every review pass because it was in the frame of none of them. It was
also drawn at `setScale(1)`, bypassing `worldScaleFor` — the one unit the whole
world shares — while `WorldScale` had carried its 2.4 m entry the entire time.
The lesson is procedural, not artistic: **grep the tree for placeholder
provenance, do not wait to notice it.**

Two things the replacement had to be told, because it got both wrong first:

* **A waystone is not a small obelisk.** The monolith is dressed, tapered and
  plumb; a menhir that has stood in silt for centuries has a broken crown, a
  footing of rough stones, and — the detail that does all the work — a **lean of
  two or three degrees**. Nothing else in the vocabulary says "old and
  unmaintained" at 36 world pixels, and a stone standing perfectly upright in
  mud says the opposite. A taper that flares hard at the base with a point on top
  is a bell, a hood, or a nose cone; it is never stone.
* **A glyph carries meaning whether or not you meant it to.** An upright with a
  crossbar is a Latin cross, and the first cut stamped one on the object the
  player touches most in the game — a wholly foreign cosmology, at the exact spot
  the world's own has to be legible. The mark is a **ring** now, which is canon
  (the Rite kneels in concentric rings, world-bible §6.1) and cannot be mistaken
  for anyone else's sign.

**AN EFFECT KEYED TO A SIM STATE LASTS AS LONG AS THE STATE, WHICH IS NEVER WHAT
YOU WANTED.** The hit flash was `if (state === "hitstun") setTintFill(0xffffff)`.
Hitstun is 150–250 ms; a full white silhouette for that long does not read as an
impact, it reads as the sprite having broken — and it erased the one frame of
animation the hit existed to show off. It is keyed to `GameFeel`'s hold now, so it
lasts 24 ms on an off-beat swing and 82 ms on a Perfect, and a Perfect flashes
*harder and longer* for free, off the same one number as the shove, the sparks
and the shake.

Two more from the same frame:

* **A telegraph goes on the FLOOR.** A 2 px ring stroked round the creature is 8
  screen pixels of hard red at the 4x zoom, sitting on top of the silhouette: it
  read as a debug gizmo, and it hid the telegraph *pose*, which is the animation
  state §11.5 ships six of per foe for exactly this purpose. Two thin ground
  ellipses instead, the inner one closing as the wind-up completes, so the tell
  is a countdown and the creature stays visible.
* **An accessibility caption is for something the player cannot HEAR.** §9.3
  captions exist so a player without audio still gets "♪ THE MUSIC SHIFTS" and
  "GROOVE FULL"; they are on by default, and they should be. An incoming attack
  is not audio — it is a visual tell — and duplicating it as text put a
  centre-screen all-caps warning banner in the middle of every fight, several
  times per fight, in the default configuration. That cue is a combat *forecast*,
  so it belongs to `sightreadEnabled` (§8.4), whose own doc comment already
  claimed it. **Never fix a default-on accessibility feature by turning it off;
  fix it by putting the cue behind the setting that actually describes it.**

### 4.7 Eight laws from the Breach, the Scar and the painted ground

Every one of these was paid for. Where a count is given it is a count of times
the same mistake shipped before the law got written down.

**AUTHOR AT 32 PX PER INTENDED TILE.** `worldScaleFor` floors world scale at
0.5, so a piece's height in tiles is fixed by its source canvas and no metre
declaration can shrink it below `src_h / 2`. At 32 px per tile, `metres == tiles`
lands on that floor every time — which means the metre value in `WorldScale.ts`
and the tile count you drew are the same number, and a mismatch is arithmetic
rather than taste. Verified mechanically for all 12 Breach and all 17 Scar
pieces; a piece that does not land on 0.5 is drawn at the wrong size, not
declared at the wrong size.

**THE EMISSIVE BLUR LAW.** `rig.Painter` blurs a glowing shape by `9 * SS *
glow`. So `glow=1.0` on a two-pixel blob spreads that blob's entire energy over
a thirty-six-pixel radius and disappears — which is how the Breach's festoon
bulbs, the only warm light in the region, shipped as a row of grey **pearls**.
Over-correcting the other way (a bright wide bloom) gave white kidney beans that
merged two adjacent lamps into one. A light is **three discs**: a *dark* ember
bloom at `glow=1.0` (the bloom source must be dim, not white), a tight envelope
at ~0.2, and an opaque filament at ~0.1. `_bulb` and `_flame` are both built
this way and neither may be simplified.

**A SMOOTH TAPER OR A MONOTONIC SHRINK IS A MANUFACTURED SILHOUETTE.** Nothing
in this world is machined, and nothing that grew and then broke has a smooth
outline. Instances, all caught in-frame: the Shelf's hull as a *fishbone*, then
a *leaf*; `burnt_spar` as a *missile*, then a *cactus*, then a *ladder*, then a
*sword*; `burnt_stand` as *bollards*; `den_mouth` as an *igloo*, then a
*chapel*, then a *tomb*; `cairn` as a *pebble cone*, then a *wedding cake*;
`spoil_heap` as a *pyramid*; `oasis_fern` as a *spider*; `oasis_rill` as a
*millipede*. Two rules fall out. A stack built by hand never has a monotonic
width sequence — the cairn needed a *wide* slab high up and two thin ones low
before it stopped being a cake. And a vertical shaft of constant width carries
no information at all, so whatever detail you hang on it supplies the reading:
arms that rise make a cactus, a nose cone makes a missile, three evenly-spaced
bars down one side make a ladder. Fix the shaft, not the details.

**REPETITION IS SOLVED BY DIFFERENT SILHOUETTES, NOT FEWER INSTANCES.** The
Oasis shipped as three pieces over eight placements and read as four copies of
one green mound; the fix was two new *shapes*, not less moss. The inverse also
holds and is load-bearing: `spoil_heap` is repeated thirty-one times **because
the point is a count** — "picked-over" is a number, not a texture. Ask whether
the repetition is saying something before you break it.

**TEMPERATURE CONTRAST POPS HARDER THAN VALUE CONTRAST.** `den_mouth` measures
*darker* than the ground it stands on (mean luminance 42 against 61) and still
read as the brightest thing in the frame, because twenty-two thousand pixels of
cool neutral grey on warm earth reads as poured concrete no matter what its
value is. §3 constrains brightness; this is the other axis, and it is not
covered by a luminance check. A large piece must belong to its region's
temperature. Same failure one scale down: the Scar's `IRON` was authored cold,
and the barrow and windlass came back as *aluminium*.

**YOU CANNOT FIX A BASE BY TINTING IT.** Mixing complementaries always lands in
the middle of the wheel. `GROUND_BASES[2]` was a warm tan and no amount of cold
accent could pull region 2 off a beach; `GROUND_BASES[3]` was warm and the
accent lerp at 0.22 made the Scar the only 67%-saturation surface in the world
(everything else measures 10–46%); `rock_top_bases` was one cool blue-grey for
all five regions, and blue-grey lerped a third of the way toward the Scar's
red-orange ember is **mauve** — the exact hue the palette gate exists to keep
out, arriving through the back door because nobody lerps toward purple on
purpose. Per-region bases, then a *small* accent. An accent is a small hot thing;
it must not be smeared across forty-three thousand tiles.

**A HARD THRESHOLD ON A NOISE FIELD IS A CAMOUFLAGE GENERATOR.** `img[n_low <
0.36] *= 0.86` paints flat blobs with hard edges — binary in, binary out — and
wherever two districts of different hue overlapped one of those blobs the frame
came back as military camo: flat patches of olive, tan and brown meeting along
crisp curves. Any pass that hard-selects a region of the canvas owes it a
gradient at the boundary. (Same family as §4.3's flat-patch law: any pass that
fully *replaces* the canvas owes it the grain back.)

**A SPECULAR IS WHAT MAKES A SURFACE READ AS LIQUID.** Not colour, not
transparency, not a soft gradient — a *hard-edged bright streak* where the sky
lands on it. `oasis_spring` was a desaturated grey-teal pool with visible
bottom stones and no specular, and it read as a concrete slab; three hard
streaks covering ~4% of the pool turned the same shape into water. Two
corollaries found in the same piece: things seen *through* water are darker than
it, not lighter (the bottom stones had been lerped toward `STONE_LIT` and sat
*on* the shape), and a bright vertical bar with nothing behind it is a straw,
not a fall.

### 4.8 Three things only the browser will tell you

`tools/capture.mjs` is a gate (§4.5). These are the failures that survived a
clean contact sheet, a passing palette gate, a passing plate check, and a green
`tsc`.

**THE CAMERA SHOWS 20×11 TILES.** That is the hard constraint on composition and
it has broken a layout three times: the Shelf's hull (14 tiles tall in an 11-tile
viewport), the Breach's wheel (the overworld depth-sorts on base row, so a booth
tucked among its legs draws *behind* it and reads as deleted, not as depth), and
the Scar's den camp (spread over twelve rows, so the den and the equipment that
explains it could never share a frame). A vignette that does not fit one camera
is not a vignette, it is two.

**A SILENT `continue` IS INDISTINGUISHABLE FROM AN EMPTY REGION.** Both the
dressing loader and `ArenaComposer.composeWorldVenue` guard with `if
(!this.textures.exists(p.key)) continue;`. A whole kit's worth of missing keys
renders as bare ground with no error, no warning, and a green test suite. Count
what you placed and print it — the capture harness reports `envSpritesPlaced` and
a per-kit breakdown for exactly this reason, and a placement file that was never
written looks *identical* to one that was.

**SMOOTH SCALING NEEDS ONE PIXEL OF BLEED AT EVERY CHUNK EDGE.** The world
renders at `RENDER_SCALE 4`, so the camera scrolls to fractional world positions
and every ground-chunk edge gets bilinearly sampled past its own last texel.
Outside the texture the sampler clamps, so two chunks laid exactly edge-to-edge
each contribute a half-weighted edge column: measured on the shipped build as a
1 px lighter rule straight across the frame at world y=1024, which reads as a
horizon that is not there. Stretch each chunk by a single world pixel.

**A COLOUR CONSTANT DOES NOT SAY WHAT IT IS FOR, AND THIS PROJECT HAS PAID FOR
THAT THREE TIMES.** `BREACH` was `(216, 206, 182)` commented `"sand / foam"` —
two different colours in one comment, and the implementation silently picked
sand. Fixing it meant touching three files that must agree (`palette.py`,
`paint_ground`'s `ACCENTS`, `OverworldScene`'s `REGION_ACCENTS`) plus a district
table, and a second in-browser capture *still* came back olive because the real
culprit was a fourth copy. Name the intent in the comment, name the files that
must agree, and verify in the browser.

### 4.9 Six laws from the Keep, all of them found by looking at the room

The Keep's kit is sixteen pieces and six of them failed their first render. Every
failure was a shape law rather than a colour law, which is a change from the
earlier regions — the palette lessons had landed, the geometry ones had not.

**AN ISOCONTOUR OF A COARSE NOISE FIELD IS A DOODLE GENERATOR.** Three instances,
all of them shipped: the Scar's mud cracks at `value_noise(cell=30)`, the dried
lakebed at 22, the Keep's marble veining at **55**. `abs(n - 0.5) < eps` on a
field whose cell is tens of metres traces a handful of enormous sweeping curves
that dip in and out of the band, i.e. **dashed lines**, and the shipped result
looks like dressmaker's chalk, a topographic overlay, or worm trails. Two things
fix it and you need both: a **fine** cell, so the features are the size of the
real feature (a sun crack is a hand's width, a marble vein is a finger's), and a
**second coarse field deciding WHERE**, because a texture that covers everything
uniformly is not a texture. Sibling of the camo law in §4.7: *a noise field does
not become a texture until something says where it applies.*

**AN ARCH IS TWO SPRINGINGS.** The proscenium took five goes. A single pier with
a curve leaving the top of it is not half an arch — it is a **cantilever**, and a
cantilever is machinery. It rendered, in order, as a crane, a boom, a
level-crossing barrier, a street lamp and a shepherd's crook, and no amount of
thickening, gilding, breaking, or reparameterising the curve helped, because the
missing information was never in the curve. The fix was to give up on "a fragment
reads as a ruin" and draw the **complete** arch on two piers, putting all the
ruin in the entablature above it. Generalises: some objects are defined by a
relationship between two parts, and you cannot draw one of those parts.

**STACKED POLYGONS ARE A STAIRCASE, NOT A GRADIENT.** Shading a hemisphere with
horizontal slices gave a **barrel** at five bands (visible steps read as staves)
and **corrugation** at twelve (a 62px piece means 3px bands, and a 3px step at
fifteen levels of contrast is a stripe). Removing the per-band rim light did not
help, because the banding was the fill, not the outline. If a surface needs a
smooth ramp it needs **one shape whose alpha ramps** — here, one polygon for the
bowl plus a single soft `blob` for the shoulder.

**WHEN AN OBJECT KEEPS RESOLVING INTO FURNITURE, THE PROBLEM IS THE SILHOUETTE
COUNT, NOT THE SHADING.** The timpani read as a side table, then a birdcage, then
a wheelbarrow, then a trough — four objects, one cause: *a single large
flat-topped mass on legs is furniture no matter what you paint on it.* It was
fixed by drawing **two** drums instead of one. Two overlapping masses at different
sizes and heights have no single top surface for the eye to sit a tabletop on, and
the occlusion states depth for free.

**A CLOSED LOOP HANDED TO A POLYGON RASTERISER IS A FILLED DISC.** The
chandelier's corona was written with the comment *"the ring as a BAND, not a
filled disc"* directly above `poly(ring)` — the most literal possible version of
the mistake — and shipped as a flying saucer. An annulus is **two** arcs: the
outer sweep, then the inner sweep reversed, so the winding leaves the middle out.
The hole is the entire difference between a ring lying on a floor and a saucer
landing on one.

**AT HALF SCALE, TEMPERATURE IS THE LAST LEVER YOU HAVE.** Two pieces failed on
this in the same capture. `sheet_drift`'s lit edges were mixed toward `GLASS_LIT`
— picked for its value without looking at its hue — and pale **cool** slivers on
dark ground are broken glass; warmed to `CANDLE` they are paper. The chair's seat
pad was `VELVET` at 4px, which halves to 2px of nothing, and four chairs in a row
read as croquet hoops; the fix was not a redder red but a **lighter** block with a
dark line under its front edge. Everything in this world renders at `worldScale
0.5`, so **the eye needs a value block, not a hue** — and where value is spoken
for, temperature is what is left.

### 4.10 Two more things only the browser will tell you

**A DEAD TEXTURE KEY RENDERS AS NOTHING AND EVERY GATE STAYS GREEN.** Region 4
had 44 `env_hall_*` placements in `dressing.json` and 14 more in
`ArenaComposer.arena_keep`, and there is no `assets/sprites/env/hall/` directory
in this build. The last region of the game — and the boss arena, the room the
entire campaign walks toward — had been shipping **empty**. `tsc` cannot see it
(they are strings), the palette gate cannot see it (it audits shipped PNGs, and
there were none to audit), the plate check cannot see it, and the scene does not
throw. The only thing that catches this class of bug is walking the region in
`tools/capture.mjs`. Worth a gate of its own: every key in `dressing.json` and
`ArenaComposer` should be checked against the files on disk.

**THE PLATE AND THE TILEMAP DISAGREE ABOUT WHAT IS FLOOR.** `paint_ground.py`
paints a `marble` district centred on (308,46) and a `foyer` district on
(292,62); `overworld.json` says (308,46) is open water and (292,62) is 24% dry
land. Two scripts describe the same ground and nothing reconciles them. The
tilemap wins — it is what the player collides with and what `place_kit` checks —
so authored dressing sits at the dry EDGE of a painted patch rather than its
centre, and that is a compromise, not a fix. Know it before adding a district.

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
  a pale billboard. `CAP_WINDOW=col,row,radius` dumps every textured display
  object near a tile — a thing in the frame can come from `dressing.json`, a
  scatter pass or the venue composer, and only the live display list knows
  which. (It sees textures, so `Graphics` objects are invisible to it. That is
  how a placeholder save point survived four review passes: see §4.6.)
* `node tools/fight.mjs` — the same idea for **feel**, which the other three
  cannot see at all. Impact is 82 ms long at its longest, and `ActionCombat` is
  pure and knows nothing about any of it, so a green suite and a fight that
  reads as two sprites overlapping are completely compatible states. It drives
  real input, closes the distance off the sim's own positions, and **sleeps the
  game loop two frames after a hit lands** so the impact frame can be
  photographed. `LIST=1` adds the arena's display list, depth-sorted.

The rule behind all four: **anything the eye cannot audit at the size and speed
it ships at gets a number instead.**
