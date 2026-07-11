# World & Story Bible — *The Drowned Chorus*

Status: **canonical** as of 2026-07-11. This is the narrative and world
foundation the game's tone, content, and UX are built on. It supersedes the
placeholder "Project Meterfall" codename (PRD §18's open naming question is
resolved here: the game is **The Drowned Chorus**).

Everything below is derived from the uploaded Skatopia setlist lyrics — the
game's world *is* those songs, sunk and given a place.

## 1. Logline

Four of the drowned descend through a black ocean of bone and rusted
clockwork toward a sound they can't stop hearing — the misery song of **The
Conductor** — and the only way to reach him is to sing back on the beat.

## 2. Premise

At the bottom of a lightless sea lies a gothic world that refused to end.
Time broke here long ago — *"black clocks line the walls," "melting the
clocks like waterfalls"* — so nothing rots away and nothing rests. The whole
drowned realm hums one endless composition, **the drowned chorus**, and the
chorus is what keeps everything sinking, feeding, and awake.

A party washes in on the shallows with no memory of drowning: the
**Deereater**, the **Saltminer**, the **Esoterophobe**, and **Sunshine
Sally**. They can hear the chorus more clearly than the things that live
here — and hearing it, they can answer it. To sing back *on the beat* is to
push against the song; to miss is to be pulled under. Following the loudest
strand of the music, they descend toward its composer.

## 3. The rhythm is diegetic

The combat mechanic is the story. A battle is a passage of the drowned
chorus; every ability is a phrase sung into it. Hitting the beat (§8.3) is
**singing back** — countering the misery song; missing lets it take the
phrase. This is why the timing model is the game's spine, not a minigame:

- **Focus** — a hero's breath held for a difficult line.
- **Groove** (the party's shared meter) — the chorus swelling in *their*
  favour; spent on an **ultimate**, a verse loud enough to break the song.
- **Sightread** (Sunshine Sally) — literally *seeing the music*: the two
  measures of the chorus about to arrive (PRD §8.4's forecast).

## 4. The party — the four who answer

| Role | Name | Who they are |
|---|---|---|
| warrior | **the Deereater** | An antlered reaver who ate what it should have mourned. Burst damage; long, greedy phrases. |
| tank | **the Saltminer** | A hunched figure in a 17th-century saltminer's kilt, shield hewn from a slab of the mine. Mitigation, guard, taunts the song onto itself. |
| mage | **the Esoterophobe** | Robed and clock-lanterned, terrified of the meanings it keeps uncovering. Debuffs, pattern disruption — unpicking the chorus's threads. |
| healer | **Sunshine Sally** | Pale keeper of a censer, named for a warmth this place has never had. Sustains the party and reads the music ahead. |

## 5. The descent — biomes as movements

The campaign graph (`opening_biome.json`) is one descent; each node is a
movement of the chorus, reframed from a placeholder biome to a lyric.

| Node | Movement | The song it sings | Foe |
|---|---|---|---|
| `opening_1` | **The Shallows** | washing in; the water's first cold teeth | drowned rot-oozes (`slime`) |
| `mid_1` | **The Salt Mines** | *"17th-century saltminer kilts… every cast-iron piece"* | salt-wracked drifters |
| `mid_2` | **The Pit Below** | *"cannibals so eager we'll eat each other on dates"* — a drowned carnival, clave-accented | masked luchador reavers |
| `mid_3` | **The Attic of Teeth** | *"have you ever seen a mouth this wide?"* — rats, bones, teeth | the elite wraith |
| `boss_1` | **The Conductor's Hall** | *"he's been trying to describe a sound again"* | **The Conductor** |

## 6. The Conductor

The world's composer and final boss (PRD §8.7). Gaunt, black-coated, a clock
where a heart should tick, a baton raised over a drowned orchestra of the
things the party fought to get here. He is not evil so much as *unfinished* —
forever *"trying to describe a sound,"* and the drowning is a side effect of
a piece that will not resolve. His three phases are three attempts at the
ending: stable 4/4 that fractures into 3/4, then a desperate cycle of
5/4→7/8→4/4→3/4 as the composition comes apart. Beat him and the chorus
finally lands its last chord — and the water, at last, is quiet.

## 7. Tone

Beautiful-grim. Surreal, poetic, melancholy dread — Blasphemous/Hollow-Knight
register, not splatter. The horror is in the *images* (drowned clocks, a maw
too wide, a party eating what it loved), rendered as gorgeous moody pixel
art. Minimal text; the world speaks through place, sprite, and song.

## 8. Naming

- **Title:** *The Drowned Chorus*
- **Tagline:** *a rhythm of rust and tide*
- Prior codename "Project Meterfall" is retired (kept only in git history and
  older PRD revision entries).
