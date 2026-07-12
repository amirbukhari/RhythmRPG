# Art Bible — Meterfall / *the drowned chorus*

Status: **living document**, current as of 2026-07-10. This is the real
art-direction doc PRD §11.1 asked for. Unlike earlier cycles, the art it
describes is **built and in the game**, not aspirational.

## 1. Where the direction comes from

The visual direction is derived directly from the uploaded **Skatopia
setlist lyrics** — a dark, surreal, gothic body-horror songbook (drowning
and ocean floors, obelisks of belief, rust and ambition, melting black
clocks, meat hooks and freezer grates, ghosts singing misery songs, wraiths
with "teeth like pearls and hair like feathers," and a boss who is literally
**The Conductor**, "trying to describe a sound"). The pitch: render that
world as *beautiful* moody pixel art — the melancholy-gorgeous register of
Hollow Knight / Blasphemous / Death's Door, not gore for its own sake.

Tagline, used on the title screen: **"the drowned chorus."**

## 2. How the art is actually made (the pipeline)

Every sprite, tile, and backdrop in the game is **authored in code** as a
palette-indexed pixel grid and rendered deterministically to PNG. There is
no external art and no image generation anywhere in this project — the "just
pixels / an RGB-JSON thing" approach, taken literally. This makes all art:

- **real and committed** (the PNGs live in `assets/`),
- **regenerable** with one command: `python3 tools/pixelart/generate_all.py`,
- **reviewable as source** (`tools/pixelart/*.py` are the master files).

Pipeline modules (`tools/pixelart/`):

| File | Produces |
|---|---|
| `skatopia.py` | The master palette + the render/outline/frame/pack/save primitives every other module uses. |
| `tiles.py` | `assets/tilemaps/overworld_tileset.png` — 4 seamlessly-tiling 16×16 tiles. |
| `heroes.py` | `assets/sprites/heroes/{role}/{down,side,up}.png` — 4 classes × 3 facings, each a 4-frame walk strip. |
| `enemies.py` | `assets/sprites/enemies/{id}.png` — 6 enemies, 48×48, 2-frame idle. |
| `backgrounds.py` | `assets/backgrounds/arena_{shallows,saltmines,pit,attic,hall}.png` — five distinct story-staged arenas (PRD §11.1.1, lore in world-bible §5a), plus the legacy `battle_{abyss,conductor}` pair (menus/turn-based) and a tiling `caustics` overlay. Each arena carries a beat-pulsing story light wired in `ActionBattleScene`. |
| `props.py` | `assets/sprites/overworld/props.png` — gothic overworld decorations (dead tree, tombstone, bone pile, fungus, reeds, obelisk shard). |
| `ui.py` | `assets/ui/` — a nine-slice window frame (+ boss variant) and stat icons. |
| `fx.py` | `assets/fx/` — white radial glow + impact-spark textures, tinted and additively blended in-engine for the HLD emissive look. |
| `generate_all.py` | Runs all of the above deterministically. |

**HLD register (v6.0+).** The real-time action arena leans into *Hyper Light Drifter*: enemies are scaled **colossal** and silhouette-first (the Conductor towers ~2.9× over the small player), and emission is faked with additive glow (`fx.py`) — accent-tinted auras and glowing eyes that pulse on the beat, red windup telegraphs, an on-beat player flash, bright attack arcs, and impact sparks. All emissive fx are reduced-motion aware.

Core technique: a sprite is a list of equal-length strings; each character is
a key into the palette (`" "`/`"."` = transparent). A 1px outline pass and a
consistent framing convention (bottom-centre, feet on the floor line) give
everything the same solid, readable, "real pixel art" feel.

## 3. The master palette

One curated ~34-colour palette (`PALETTE` in `skatopia.py`) is shared by
*everything* so nothing clashes and the whole game reads as one world. Each
hue carries 3–4 value steps so sprites are shaded, not flat.

- **Ink / void** — night, ghosts, outlines.
- **Bone / pearl** — teeth, obelisks, salt, the party's cleric.
- **Rust / ember / gold** — ambition's rust, black plumes of fire, saltmines.
- **Blood** — the staircase that turns red, the bath that turns red.
- **Ocean** — the abyss the party would rather live in than die on land.
- **Rot / moss / sick-olive** — rot spots, calcification, anthrax highs.
- **Plum / amethyst** — sapphire purses, twilight, the esoteric.
- **Flesh** — the doomed party, pallid and corpse-touched.
- **Metal** — nooses, meat hooks, steel, the melting clocks.

## 4. The cast

**The party** (four *distinct* silhouettes — never one tinted sprite):

| Role | Character | Read |
|---|---|---|
| warrior | **the Deereater** | antlered blood-rust reaver, iron-gauntleted, a cleaver |
| tank | **the Saltminer** | hunched steel miner behind a slab shield |
| mage | **the Esoterophobe** | tall plum-robed figure, a melting-clock lantern |
| healer | **Sunshine Sally** | pale bone-robed keeper with a teal stole and a censer |

**The enemies** (each straight from a lyric):

| Id | Creature | Lyric hook |
|---|---|---|
| `slime` | rot-ooze with a pearl-tooth grin | "rot spots", "teeth like pearls" |
| `drifter` | hooded ghost wanderer | "the ghosts in my house" |
| `luchador_grunt` / `luchador_mask` | masked reavers | "cannibals so eager" |
| `elite_wraith` | feather-haired, wide-mouthed wraith | "teeth like pearls, and hair like feathers" |
| `the_conductor` | **the boss**: gaunt conductor of the misery song, a clock in his chest, baton raised | "trying to describe a sound", "black clocks line the walls", the melting clocks |

## 5. Environments

- **Overworld**: dark rot-moss turf, pale bone-brick roads ("turning to
  salt"), abyssal water pools, wet faceted rock. A camera-locked vignette +
  cold overcast set the mood (disabled under photosensitivity-safe mode).
- **Battle**: an abyssal hall of bone obelisks over a wet stone floor; the
  boss gets a plum, clock-lined variant. The party stands lower-left facing
  the wave on the floor to the right, each on a soft ground shadow, with
  breathing/idle motion.
- **Menus**: share the abyss backdrop (dimmed) so the whole game — from the
  audio gate and title screen through results — lives in one world.

## 6. Known limitations / next passes

- Heroes reuse the side strip flipped for left, and up/down reuse the down
  frames' silhouette; true 4-directional per-frame art is a future pass.
- Enemy "idle" is a 2-frame bob/float; attack/hurt animations are not yet
  authored (combat still reads clearly via the HUD and sprite alpha).
- The palette and pipeline are deliberately built to make those next passes
  cheap: add frames/grids in `tools/pixelart/`, rerun `generate_all.py`.
