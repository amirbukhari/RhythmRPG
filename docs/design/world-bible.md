# World & Story Bible — *The Drowned Chorus*

Status: **canonical** as of 2026-07-23 (rewritten for the v10.0 solo pivot and
the v12.0 Ascent). This is the narrative and world foundation the game's tone,
content, and UX are built on. It supersedes the placeholder "Project Meterfall"
codename (PRD §18's open naming question is resolved here: the game is **The
Drowned Chorus**).

The world is built from the recorded setlist of the band **Inhalants** — the
game's world *is* those songs, sunk and given a place. (History: an earlier
draft of this bible cast four song-title heroes descending together; v10.0
retired that fiction. The protagonist is now solo, the journey is an **ascent**,
and those four old names survive only as the soundtrack's songs, §8. This
document reflects the shipped story.)

## 1. Logline

A drowned guitarist climbs up through a black ocean of bone and rusted
clockwork toward the surface, chasing the one thing louder than the misery song
that fills it — his lost son — and the only way up is to sing back on the beat.

## 2. Premise — the Ascent

At the bottom of a lightless sea lies a gothic world that refused to end. Time
broke here long ago — *"black clocks line the walls," "melting the clocks like
waterfalls"* — so nothing rots away and nothing rests. The whole drowned realm
hums one endless composition, **the drowned chorus**, and the chorus is what
keeps everything sinking, feeding, and awake. At the far end of it, up where the
water thins, stands its composer: **the Conductor**, forever *trying to describe
a sound* that will not resolve — and the drowning is only the side effect of a
piece that will not end.

**Mir** wakes lying on the ocean floor, in the **Fold**: a town whose people
pray to a massive obelisk they did not raise and cannot leave. He can hear the
chorus more clearly than the things that live down here — and hearing it, he can
*answer* it. To sing back *on the beat* is to push against the song; to miss is
to be pulled under.

Mir leaves the Fold and climbs — up the drowned Shelf, across the Breach where
the world crosses the waterline, out onto the hostile Scar of the surface, and
on toward the Stage. His toddler son **Nari** follows him out of the town. On the
surface, Nari is taken. From that moment the whole game is one thing: the fight
to climb the rest of the way and get him back.

## 3. The rhythm is diegetic

The combat mechanic is the story. A battle is a passage of the drowned chorus;
every ability is a phrase sung into it. Hitting the beat (§8.3) is **singing
back** — countering the misery song; missing lets it take the phrase. This is
why the timing model is the game's spine, not a minigame:

- **Focus** — a breath held for a difficult line, spent on specials.
- **Groove** (the swelling meter) — the chorus turning in *Mir's* favour; spent
  in full on an **ultimate**, a verse loud enough to break the song.
- **Sightread** — literally *seeing the music*: a forecast of the next bars of
  the chorus and the strikes riding them (PRD §8.4's forecast assist).

## 4. The cast

The band cast is retired; the story is four figures on one road up.

| Role | Name | Who they are |
|---|---|---|
| protagonist | **Mir** | A drowned guitarist and a father. He wakes on the ocean floor with no memory of drowning and one certainty — his son is with him. His whole kit (light / heavy / special / ultimate / dash / parry) is verses sung against the chorus. |
| the followed | **Nari** | Mir's toddler son. He trails Mir out of the Fold — a small figure at his heel — until the surface takes him. He is never an escort objective or a fail state; he is the *reason*, told entirely through the world: a footprint trail that ends at a scuffle, then sparse clues, then a cage. |
| the huntress | **Lunal** | The masked huntress who holds the Conductor's strings — she *conducts the Conductor*. She is the one who took Nari, and she does not hunt to kill. She hunts to **keep**. She is revealed through staging at the finale (a Lunal fight is a v2 candidate, §18). |
| the composer | **the Conductor** | The world's composer and final boss — gaunt, black-coated, a clock where a heart should tick, a baton raised over a drowned orchestra. Not evil so much as *unfinished*. Lunal's instrument, and Nari's jailer. |

## 5. The ascent — regions as movements

The campaign graph (`opening_biome.json`) is one continuous climb from the
seafloor to the Stage. Each region is a movement of the chorus, dressed in the
visual language of a specific drowned place so approaching it foreshadows it.
Combat begins only once Mir leaves the Fold — the generator *asserts* no fight
lands inside the sanctuary.

| Region | Movement | Staged as | Foe |
|---|---|---|---|
| **The Fold** | *waking on the floor* — the obelisk town, silt and prayer rings | the drowned harvest village | *none — Nari still follows* |
| **The Kelp Shelf** | *the climb* — ship skeletons standing like a dead forest | the drowned salt mine | salt-wracked drifters |
| **The Breach** | *crossing the waterline* — where the sky remembers you have a face | the drowned carnival | drifter packs |
| **The Scar** | *the hostile surface* — claw gouges, scorch, dens; **Nari is taken here** | the collector's den | elite wraiths |
| **The Conductor's Stage** | *the ending he rehearses* — where Nari is kept | the drowned concert hall | **the Conductor** (Lunal behind him) |

### 5a. The untold stories (canonical arena staging)

Each movement is fought inside a specific place staged to imply a past the game
never narrates (PRD §11.1.1). This is the canon behind each staging — **never
surfaced as text in-game**; it exists so the art stays coherent.

- **The Fold (the drowned village).** The village drowned during its harvest
  festival — the ring of boats was a blessing rite for the fleet. The rising
  water came *with* the first verse of the chorus, gently, and most didn't run.
  One boat still strains at its mooring above the green: the baker's daughter
  cut everyone else's boats loose first, and hers ran out of rope. Now the
  survivors pray to the obelisk they woke to, and nobody ever leaves. Mir is
  the first who does.
- **The Kelp Shelf (the salt mine).** The miners broke into a gallery that sang
  back. They gathered at the tunnel mouth to listen — pillar of salt is what
  listening too long *is*, down here (*"when you're turning to salt, it's when
  you're staring ahead"*). The one statue facing away is the foreman, who
  covered his ears and ran, and calcified anyway, mid-stride, three steps from
  the lift. Every wreck on the climb points the same way: up.
- **The Breach (the carnival).** The carnival kept performing after the water
  came — *"cannibals so eager we'll eat each other on dates."* The champion's
  final match was against something that came up through the ring floor; the
  ropes snapped outward when it left with him. This is the waterline, the seam
  between the drowned world and the air — thin enough that a small thing can
  slip through it. The tipped chairs face away because in the end no one could
  watch.
- **The Scar (the collector's den).** The hostile surface. The tracks all lead
  one way — *in*, toward the den — and none lead back. Whatever keeps this
  place does not eat what it takes; it **collects**, arranged by size: a shoe,
  a comb, a tooth too small to be yours. This is where Nari's footprint trail
  ends at a scuffle mark, and where a colder truth waits — the surface has left
  its instructions in gouges, and something has been walking a small pair of
  prints *toward* the den. (An older tenant is staged here too: a room whose
  door is boarded from the inside, where someone locked themselves in to
  transcribe the sound in the walls before it finished transcribing them.)
- **The Conductor's Stage (the concert hall).** The orchestra drowned
  rehearsing the ending. The Conductor kept conducting; the stands' pages are
  blank because he erases every attempt except the last row's — the only
  players who ever got it right, and whom he therefore could never let leave.
  The clocks each stopped at the moment a player gave up; they melt because he
  keeps re-conducting those moments. The music falters every time the small one
  in the cage cries — then starts again, angrier. Behind the baton, Lunal
  watches, and keeps.

### 5b. The explorable world (PRD §8.8) — regions and echoes

The walkable world is five joined regions, one continuous ascent, each dressed
in its arena's visual language so approaching a place foreshadows it. Strewn off
the critical path are **~40 echoes** (8 per region) — hand-placed lore
fragments, each surfacing exactly one line when found (PRD §8.8.2). No echo text
is ever shown automatically; the player must walk to it and interact. Re-voiced
to the ascent (v12.0), they carry three braided threads: the drowned place's own
grief, the cult's fear of the surface, and — from the Breach up — the trail of
Nari.

- **The Fold** grieves and warns: *"We didn't raise the obelisk. We woke on the
  floor and it was already listening."* — *"Nobody leaves the Fold. It isn't a
  rule. It's just that nobody ever has."* — *"She untied every line but her own."*
- **The Kelp Shelf** is the climb: *"Every ship that ever sank points the same
  way. Up."* — *"Rope enough to reach the light — if you don't weigh anything
  anymore."* — *"The foreman covered his ears and ran. He calcified mid-stride,
  facing away."*
- **The Breach** is the crossing, and the first note of the loss: *"The line
  between worlds is thinner than a footstep. His fit inside mine."* — *"The first
  breath burns. The second one is his name."*
- **The Scar** is the search turning to dread: *"They walk IN. Toward the den.
  Why would he walk toward it?"* — *"It doesn't eat what it takes. It collects."*
  — *"Learn his gait or lose him: paired stride, a heel dot, the faint right-foot
  drag."*
- **The Stage** is the truth of who holds him: *"The music stops every time the
  small one cries. Then it starts again, angrier."* — *"She doesn't hunt to
  kill. She hunts to keep."* — *"The cage is exactly the size of a boy who
  stopped growing when the water came."*

**Secrets (PRD §8.8.3).** Each region hides at least one non-obvious traversal
element — a rock gap that only reads as passable up close, a path behind a wreck
or waterfall, a route visible only from one vantage — gating a relic or an echo,
never critical-path content. Hand-placed, not procedural: a discoverable secret
has to be a decision someone made.

## 6. The Conductor and Lunal

The Conductor is the world's composer and final boss (PRD §8.7). Gaunt,
black-coated, a clock where a heart should tick, a baton raised over a drowned
orchestra of the things Mir fought to get here. He is not evil so much as
*unfinished* — forever *"trying to describe a sound,"* and the drowning is a
side effect of a piece that will not resolve. His three phases are three
attempts at the ending: stable 4/4 that fractures into 3/4, then a desperate
cycle of 5/4→7/8→4/4→3/4 as the composition comes apart.

But the baton is not his own. Behind him stands **Lunal**, the masked huntress
who holds his strings — *she conducts the Conductor.* She took Nari off the
Scar and keeps him caged at the Stage; the music answers to the child's crying,
and so, through the child, to her. She is revealed in the finale through
staging, not exposition — the mask clatters where she stood, and only then is it
clear who the whole drowned song was really for. (A playable Lunal confrontation
after the Conductor is a v2 candidate, §18.)

Beat the Conductor and the chorus finally lands its last chord. The hall falls
silent; the huntress is unmasked; and above the water, at last, there is rain,
and under it, small, a laugh. **Nari, found.** The water is quiet. The world
stays open afterward — the echoes remain findable — so the ending returns Mir to
the drowned world rather than hard-stopping.

## 7. Tone

Beautiful-grim. Surreal, poetic, melancholy dread — Blasphemous / Hollow-Knight
register, not splatter. The horror is in the *images* (drowned clocks, a maw
too wide, a cage the size of a child, a trail of small prints walking the wrong
way) — rendered as gorgeous moody painterly 2D. Minimal text; the world speaks
through place, sprite, and song.

## 8. Naming

- **Title:** *The Drowned Chorus*
- **Tagline:** *a rhythm of rust and tide*
- **Soundtrack:** six real recorded tracks by the band **Inhalants** (§11.2) —
  *Sunshine Sally*, *Deereater*, *Glassriff*, *John's Anus*, *Truckers for
  Christ*, *Quotience*. (These song titles were briefly used as hero names in a
  retired draft; they are songs, not characters.)
- Prior codename "Project Meterfall" is retired (kept only in git history and
  older PRD revision entries).
