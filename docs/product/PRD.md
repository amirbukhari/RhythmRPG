# Product Requirements Document — *The Drowned Chorus*

## Document Control

| Field | Value |
|---|---|
| Document title | *The Drowned Chorus* — Browser Rhythm-Action RPG PRD |
| Working codename | Project Meterfall (historical; the game is titled *The Drowned Chorus*) |
| Status | **Active v8.9** — v8.0: enterprise rewrite per the [PRD audit](./prd-audit-2026-07-14.md); v8.1: P1 beat truth; v8.2: P2+P3 (four-tier judgment, ultimate, phased boss, Sightread, §9.3 parity) + mobile hardening; v8.3: SFX/relics/hygiene/retired-code deletion; v8.4: landforms; v8.5: the ending (FinaleScene) + wordmark + VFX; v8.6: §8.6 curriculum as authored data + enemy state motion; v8.7: balance harness + measured balance pass; v8.8: onset-snapped grids + elevation shading; v8.9: P5 soak spec (caught + fixed a real Results softlock) + vendor bundle splitting. |
| Owner | Amir Bukhari |
| Author | Amir Bukhari (compiled from concept notes, deep research, and live-play feedback) |
| Created | 2026-07-08 |
| Last updated | 2026-07-14 |
| Source material | Concept screenshots + [Deep Research Report](../research/deep-research-report.md) + Skatopia setlist lyrics + six recorded Inhalants tracks + [world bible](../design/world-bible.md) |
| Distribution | Product, Engineering, Art, Audio, QA, Accessibility |
| Approval required from | Product sponsor, Engineering lead, Art lead, Audio lead, QA lead *(names TBD)* |

### Revision history

Entries are one-line summaries in chronological order. Full narratives for every
revision — including the direct owner feedback that drove each pivot — are preserved
verbatim in this file's git history (`git log --follow -p docs/product/PRD.md`) and,
for the v7.x cycle, in [`docs/product/prd-audit-2026-07-14.md`](./prd-audit-2026-07-14.md)
and [`docs/design/aaa-audit.md`](../design/aaa-audit.md).

| Version | Date | Change |
|---|---|---|
| 0.1–1.4 | 2026-07-08 | Initial synthesis → enterprise PRD structure; music tooling (`gbmusic`) and demo-master slicing decisions. |
| 2.0–4.4 | 2026-07-08 | Turn-based engine built end-to-end vs. spec; campaign, boss, relics, accessibility, e2e/CI; multiple root-caused input/CI fixes. |
| 5.0–5.3 | 2026-07-10 | Walkable overworld replaces node menu; Groove-spend + full stat wiring; analytics consent UI; first full lyric-derived art pass. |
| 6.0–6.3 | 2026-07-11 | **Pivot: real-time rhythm-action combat** (frame data, hitstun, knockback, DI, parry, cancels) + HLD-register art; action sim + scene shipped; story-staged arena spec. |
| 7.0–7.5 | 2026-07-11→13 | **Pivot: exploration is a second game loop** — five-region world, echoes, secrets; band cast (Inhalants) playable; AI art pipeline replaces code-only constraint; AAA asset manifest; kitbash environments; top-down combat framing; touch controls. |
| 7.6–7.9 | 2026-07-13→14 | Lyric-only foe roster (luchadors culled); **real six-track Inhalants soundtrack** replaces synth placeholder; foes stand in the world; save-obelisks; fresh AI band cast + follower conga. |
| 7.10–7.15 | 2026-07-14 | Honest AAA art audit + P0–P2 burn-down (designed floors, coherent kits, real HUD, water/ground/value); **fights happen in the world** (`WorldFight`, separate battle scenes retired from the trigger path); de-pixelation; arena venues composed into the world; landform direction logged. |
| **8.0** | **2026-07-14** | **Enterprise rewrite of this document** per the PRD audit. Decisions made: judged beat must derive from the audible track via authored beat maps (§8.3/§10.3); four judgment tiers reaffirmed as spec; ultimate/Groove-spend reaffirmed v1-mandatory; cast re-specified as the band (leader-playable v1, switching v2); boss re-specified as a phased in-world fight keyed to authored song sections (§8.7); §9.3 accessibility reaffirmed with shipped-path gaps tracked; touch input brought in scope with platform tiering (§7.1/§9.2); §8.6 curriculum rewritten post-luchador; analytics/KPIs re-based on measurable events; §11 rewritten to the AI-art + recorded-soundtrack reality; §20 re-cut as of 2026-07-14. |
| **8.9** | **2026-07-14** | **P5 soak — and it caught a real softlock on its first run.** New `soak.spec.ts`: minutes of continuous play (boot → wander all directions → settings churn → a LOST fight → a WON fight with relic pick → reload) asserting **zero uncaught errors** and no fatal overlay. Its first run found a genuine player-facing bug: *losing any fight and then finishing another crashed the Results screen mid-create* (ResultsScene reused a `TextMenu` whose Texts Phaser had destroyed — the v4.2 scene-reuse bug class, still latent). Fixed with the create-reset pattern; the soak now passes clean and gates every push. Also: **vendor bundle splitting** (phaser 340k gz / tone 62k gz cached separately from the 163k game chunk — returning phones re-download only game code). 115 unit / 17 e2e green. |
| **8.8** | **2026-07-14** | **Onset-snapped beat grids + elevation shading + portrait hint.** **(1)** `measure_beats.py` now snaps each tracked beat to the strongest onset-envelope peak within ±50 ms (only when it clearly beats the tracker's smoothed position) — the judged grid lands on the transients the ear actually locks onto, raising fidelity beyond plain beat-tracking (the algorithmic half of the §8.3 listening pass; the human tap-along stays owed). All six grids regenerated; Quotience's phase sections re-snapped to the same boundaries. **(2)** Elevation read for the v7.15 "hills" clause: rock is high ground — lit crowns, hard terrace lips with cast shadows where it drops, darkened flanks. **(3)** Portrait phones get a non-blocking "rotate for the full stage" hint. 115 unit / 16 e2e green. |
| **8.7** | **2026-07-14** | **P5 begins: the balance harness + the first measured balance pass.** New `tests/unit/balance.test.ts`: a scripted bot (approach, strike on a 120bpm beat, dash out of telegraphs) plays **every authored encounter in the pure sim** — every fight must be winnable and the §8.6 curve must ascend, enforced on every push. The first census caught a real inversion: the Conductor fell in 17.6s (turn-based-era HP pools) while the pit pack took 34s. Retuned as content: drifter 70→95 HP, wraith 140→150 (aggression 1.2→1.1), **Conductor 260→620 HP** (+dmg 13→15). Post-tune curve: 5.1s → 7.1s → 29.6s (elite pack, spiciest at 44 player HP) → 11.6s → **boss 37.6s** before phase escalation. 115 unit / 16 e2e green. |
| **8.6** | **2026-07-14** | **The §8.6 curriculum is authored data + enemies got animation-state motion.** Per-foe `action` tuning on the Enemy schema (validated): the slime lumbers (0.75× tempo, 7 dmg) → drifter (0.95×, 9) → elite wraith (1.2×, 11) → the Conductor (1.1×, 13, before phase escalation) — the difficulty curve is now content, not a shared constant, multiplying with §8.7's phase aggression in the sim (unit-pinned). And per §11.5's state standard where per-frame art is absent: enemies now **move through their states** — windup crouches (anticipation squash), the strike's active frames stretch and lunge toward the player (impact), startup coils — squash-and-stretch over the base scale, alongside the existing telegraph aura/hurt flash/death dissolve. 105 unit / 16 e2e green. |
| **8.5** | **2026-07-14** | **The game has an ending — plus the hand-lettered wordmark and a combat-VFX batch.** **(1) Finale:** felling the Conductor now routes Results → the new `FinaleScene` — three staged lines in the echo voice ("The hall falls silent. / Then — not silence. Rain, far above. / The chorus rests. The band plays on."), the wordmark, band + song credits over *Sunshine Sally*, and a choice of returning to the still-open world or the menu; completion stamps `campaignCompletedAt` on the save; covered by `finale.spec.ts`. **(2) Wordmark (AAA audit M1 closed):** `tools/pixelart/wordmark.py` — every glyph hand-lettered as a 7×9 bitmap (heavy 2px stems, per-letter sway, drip pixels off the baseline, deep-teal underlight), deterministic PNG; replaces the monospace headline on the menu and anchors the finale. **(3) VFX batch (§11.5):** parry burst ring, dash after-images, per-foe accent-colored death dissolve (burst + sink-and-fade) — all reduced-motion aware. 103 unit / 16 e2e / typecheck / build green; menu + finale screenshot-verified. |
| **8.4** | **2026-07-14** | **The landform pass (v7.15 direction realized).** New AI-generated landform kit (`tools/pixelart/landformkit.py`, pinned-camera + cleanup pipeline, retry-hardened): per region one **colossal outcrop** (sea stack, amber-lit salt cliff, plum spire cluster, weathered crag, black marble shard) and one **canopy tree** (drowned cypress, petrified crown, pennant oak, twisted dead tree, kelp willow), 10 pieces in `assets/sprites/env/<biome>/` (auto-loaded by the env glob). `OverworldScene.placeLandforms()`: deterministic low-frequency cell scatter (multi-candidate jitter; clear of markers/echoes/spawn/roadside grass rules), ~19 forms across the map. **Canopies draw ABOVE the player layer (depth 6.5) and alpha-fade to 0.35 while the player walks beneath** — footprint-sized trigger, verified programmatically + screenshot. Three off-brief generations (attic pieces drew buildings; hall willow shredded by the island filter) were re-prompted — the review-and-reroll discipline the v7.10 audit established. 103 unit / 15 e2e / typecheck / build green. |
| **8.3** | **2026-07-14** | **P4 first pass — feel, hygiene, and the retired code is gone.** **(1) Battle SFX** (procedural first fill of §11.2's SFX pack, `SfxPlayer.ts`): hits (brighter on-beat), player hurt, parry ring, dash whoosh, ultimate boom — all from sim state transitions, volume on the SFX slider. **(2) Relics regression fixed:** post-pivot, relics were selectable/persisted but mechanically inert (`applyRelics` only ran in the retired path — the §12 "pivot regression" risk, caught in cleanup); re-targeted to the action arena (focus_loop: +2 opening Focus; counter_charm: opening guard i-frames; groove_amp: +20 banked Groove) and applied at fight start. **(3) Content hygiene:** `mid_biome_2_luchadores_*` → `pit_pack_*`, track `mid_biome_2_clave_01` → `pit_below_01` (son-clave accent *data* kept — it's a rhythm term, §3). **(4) Retired code deleted** (gate #7 permanently satisfied; §18 Q5 answered: deleted outright, git history is the archive): `BattleScene`, `ActionBattleScene`, `CombatController`, `JudgmentSystem`, `PhraseTiming`, `MeterSequence`, `Forecast`, `BeatmapSonifier`, their 65 unit tests and 7 legacy e2e cases; scene stack is 8 scenes, all shipped. Suite now 103 unit / 15 e2e — every remaining test covers the product. |
| **8.2** | **2026-07-14** | **Roadmaps P2 + P3 shipped — combat completion & accessibility parity — plus mobile-boot hardening.** **P2:** the four §8.3 judgment tiers are live in the shipped fight (graded windows vs the playing song's grid, tier popups in the HUD, per-tier analytics; multipliers/Groove/i-frames/parry windows all tier-scaled in the sim); the **ultimate** (§8.5) spends the full Groove meter (player-centred burst, armored startup, screen shake, `ultimate_used`); the **in-world Conductor fight is phased** (§8.7): HP thresholds advance movements, playback jumps to the bound beat-aligned *Quotience* section (28.19s / 74.30s, segmentation-derived + grid-snapped), enemy aggression escalates, phase markers on the boss bar — covered by a new `boss-phases-world.spec.ts` on the product path; **Sightread** (§8.4) ships as a settings-toggled forecast lane (upcoming grid beats + telegraphed strikes vs a now-line). **P3 (§9.3):** practice mode floors HP at 1 in the sim (no fail state), in-fight captions for musically meaningful events (telegraph direction, phase shifts, groove full, ultimate), and **all six combat bindings are remappable** (new two-page settings with an Audio & Controls page). **Mobile:** owner report "doesn't start on mobile" → gate hardened (DOM-level tap fallback, `Tone.start()` race/try-catch), production fatal-error overlay (black screens become readable reports), `es2019/safari13` build target for older WebKit, an ULT touch button, and a Pixel-5-emulation boot e2e. 168 unit tests, 22 e2e cases, typecheck/build green; fight visuals screenshot-verified. |
| **8.1** | **2026-07-14** | **Roadmap P1 shipped — beat truth (§8.3, release gate #1a).** All six tracks measured (`tools/audio/measure_beats.py`, librosa beat tracking) into authored beat-grid maps (`src/data/content/songs/`, validated `SongMap` schema — full per-beat grids, since real recordings drift 8–16% off a constant BPM line); in-world fight judgment now reads the **playing element's position** through the live song's grid (`SongBeat.ts`, loop-aware, calibration/assist preserved), with the transport grid as fallback only when nothing is audible; game speed sets the song's `playbackRate` and scales the sim together (grids live in file-time, so heard and judged beat cannot diverge); the always-on sonifier click is retired from the fight and replaced by the opt-in §9.3 **Beat Tick** setting; `judgment_onbeat`/`judgment_offbeat` events fire on every attempted action, making the §5 on-beat-rate KPI live. New `beat-truth.spec.ts` e2e proves the audible path end-to-end (song map = playing song; judgment flips with audio; rate coupling at 70%). 157 unit tests (12 new), 20 e2e cases, typecheck/build green. Remaining §8.3 caveat: grids are algorithmically measured — the human listening pass is still owed. |

---

## 1. Executive Summary

*The Drowned Chorus* is a **single-player, browser-based, top-down rhythm-action RPG**.
The player leads Inhalants — a four-piece band (Amir on lead guitar, plus Bassist,
Vocalist, and Drummer) — through one continuous, hand-authored drowned world of five
joined regions. Exploration is a first-class game loop: hidden paths, secret pockets,
and discoverable "echo" lore fragments reward leaving the road. Combat happens **in the
world**: walking into a foe locks the camera to a room of the actual overworld and runs
a real-time action fight there — 8-directional momentum movement, dashes with i-frames,
frame-data attacks, hitstun and damage-scaled knockback, on-beat parries — with the
rhythm woven in as **on-beat power**: actions timed to the beat of the *actually
playing* music are empowered. The soundtrack is six real recorded Inhalants tracks; the
art direction is the *Hyper Light Drifter* register (colossal silhouette-first enemies,
vivid limited palette, additive glow on near-black depths), produced through an
AI-generation + deterministic-import pipeline.

The product began (v1.0, 2026-07-08) as a turn-based rhythm RPG derived from concept
screenshots; two owner-driven direction changes (v6.0 real-time action combat, v7.0
first-class exploration) produced the current shape. This document specifies the
**current target**: it is the single source of truth for requirements, and §20 is the
single source of truth for build status against them. Where a legacy system still
exists in the repository (the turn-based `BattleScene` and its subsystems), it is
explicitly marked *retired* here and is not part of the shipped product path.

Three commitments define the product bar:

1. **The beat the game judges is the beat the player hears** (§8.3, §10.3). A rhythm
   game whose judged beat diverges from its audible music is broken by definition; this
   is a hard requirement and release gate — shipped in v8.1 and held by the
   `beat-truth.spec.ts` e2e gate.
2. **Accessibility is a day-one requirement** (§9.3), applying to the shipped combat
   path — not to a retired one.
3. **Timing is audio-clock-authoritative** (§10.2). No gameplay judgment ever derives
   from UI timers.

---

## 2. Background and Problem Statement

The product originates from three concept screenshots (2026-07-08) that established a
rhythm-combat hook, a four-role party, meter-change boss design, a "see the music"
forecast concept, and a browser/pixel-art delivery target — but left every
production-critical decision undefined. The initial PRD (v1.0) fixed those decisions
for a turn-based design, and the game was built against it.

Live play then falsified two core framing assumptions, and the owner redirected:

- **v6.0 (2026-07-11):** menu-driven turn-based combat was replaced by a real-time
  action arena in the *Super Smash Bros. Melee* depth register, with the rhythm layer
  re-expressed as on-beat empowerment.
- **v7.0 (2026-07-11):** the "overworld as hub between fights" framing was identified
  as the root cause of a flat game; exploration became a first-class second loop with a
  five-region world, hidden paths, and environmental lore.

Subsequent v7.x cycles delivered the real soundtrack, the band cast, in-world fights,
and an honest AAA art audit and burn-down. This v8.0 document is the consolidation:
one spec describing the current target, with history preserved but no longer
masquerading as current requirements.

### Why this document matters now

The 2026-07-14 audit found the PRD body ~15 revisions behind its own history, spec'ing
retired systems as current and missing decisions the build had already forced. An
out-of-date PRD is worse than none: it re-litigates settled decisions and hides real
gaps (several v1-mandatory features existed only in the retired combat path). v8.0
restores the contract: **§1–§19 are authoritative for what is required; §20 is
authoritative for what exists.**

---

## 3. Research Findings That Shape the Design

| Finding | Source basis | Design consequence |
|---|---|---|
| Rhythm-combat hybrids succeed when timing is legible, not hidden | Product descriptions of *Crypt of the NecroDancer*, *Cadence of Hyrule*, *Hi-Fi RUSH* | Baseline-readable beat UI for all players; on-beat windows judged against the audible track (§8.3); telegraphs land on the beat |
| Browser JS timers drift tens of ms under main-thread load | web.dev audio scheduling guidance | All judgment computed against the audio clock (§10.2), never `setTimeout`/`rAF` |
| Web Audio must start from a user gesture | MDN Web Audio documentation | Mandatory audio gate before any menu is interactive (§10.4); first music `play()` is called inside the gate's gesture handler |
| IndexedDB is the correct client-side store for structured offline data | MDN storage documentation | Local save profiles use IndexedDB (§10.7) |
| Precise timing must not be the only path to success; cues need multi-sensory representation | Xbox Accessibility Guidelines (XAG 103/104/110), Game Accessibility Guidelines, W3C | Assist windows, captions, speed options, practice mode are mandatory v1 features on the shipped combat path (§9.3) |
| *Historical:* son clave is a rhythmic pattern, not a time signature | Berklee / Open Music Theory references | Shaped the retired turn-based clave-accent design (v1–v5). The luchador/clave content was culled at v7.6 as off-theme; the finding remains valid guidance for any future accent-pattern design. |

Full citations in the [deep research report](../research/deep-research-report.md),
which this PRD supersedes as product spec.

---

## 4. Goals and Objectives

### 4.1 Business / project goals

1. Ship a complete, polished, playable rhythm-action RPG that realizes the current
   direction (real-time on-beat combat inside an explorable authored world).
2. Prove browser-delivered, audio-clock-driven action combat at production quality.
3. Be accessible by default — on the shipped path, verified per release (§16).

### 4.2 Product goals

1. Deliver a 2–3 hour campaign across five regions, each with one boss encountered
   in-place, with exploration content (echoes, secrets) beyond the critical path.
2. Make on-beat play *feel* powerful and *be* powerful: the audible music, the judged
   beat, enemy telegraphs, and player empowerment are one coherent system (§8.3).
3. Keep the content pipeline data-driven (§10.5): fights, beat maps, and rewards
   authored as data, not scene code.

### 4.3 Non-goals (v1)

Multiplayer, monetization, user-generated content, imported-song gameplay, live beat
detection, voice acting, dialogue trees/quest-givers (§8.8.4), loot-driven progression,
controller haptics as a required channel, band-member switching mid-fight (v2 target,
§8.4), native/store distribution.

---

## 5. Success Metrics / KPIs

Every KPI below is measurable from events that fire on the **shipped** game path
(§14). KPIs that depended on retired-path events were removed or re-based at v8.0.

| Category | Metric | Source events | Target |
|---|---|---|---|
| Core loop health | % of players clearing the first fight (Shallows) | `battle_started`, `encounter_cleared` | ≥ 80% |
| Retention | % of players reaching the Conductor after clearing region 1 | `encounter_cleared` per node | ≥ 50% |
| Rhythm engagement | On-beat rate (on-beat actions / judged actions) in region 1 | `judgment_onbeat`, `judgment_offbeat` (§14) | ≥ 40% average, trending up across a session |
| Exploration loop | % of completing players who found ≥ 3 echoes | `echo_found` | ≥ 50% (validates the second loop is discovered) |
| Accessibility adoption | % of sessions using ≥ 1 assist setting | `assist_mode_enabled` | Tracked, no target — informs discoverability |
| Boss difficulty | % of Conductor attempts reaching phase 3 | `boss_phase_reached` (§8.7, pending build) | Tracked to tune the curve |
| Technical stability | Judged-beat vs. audible-beat drift in QA soak | QA instrumentation (§16.1) | ≤ 30 ms sustained; 0 desync incidents at release |
| Browser compatibility | Tier-1 matrix pass rate (§9.2) | Release-gate test matrix | 100% Tier 1; Tier 2 tracked, non-blocking |

---

## 6. Target Users and Personas

| Persona | Profile | What they need |
|---|---|---|
| **Rhythm-action fan** | Plays *Hi-Fi RUSH*, *Crypt of the NecroDancer*, character-action games | On-beat play that is audibly and mechanically real; frame-data depth (spacing, cancels, parries) that rewards mastery |
| **Exploration-first player** | Plays *Hyper Light Drifter*, *Tunic*, *Hollow Knight* | A dense, secret-bearing world where curiosity pays off in found story, not filler collectibles |
| **Action-curious, rhythm-wary player** | Enjoys action RPGs; anxious about timing tests | Off-beat actions still work (weaker, never punished into unplayability); assist windows, speed options, practice mode |
| **Player with disabilities relevant to timing/audio** | Needs alternatives to precise input or audio-only cues | Visual beat UI, captions for musically meaningful events, remappable controls, reduced-motion/photosensitivity-safe modes — all on the shipped path |
| **Content/production team member (internal)** | Authors fights, beat maps, art slots | Data-driven schemas (§10.5), the asset manifest + prompt catalog (§11.5), deterministic regeneration |

---

## 7. Scope

### 7.1 Fixed product decisions (v1)

| Area | Decision |
|---|---|
| Platform | Browser web app. **Tier 1 (release-gating):** Chrome and Edge, current stable, desktop. **Tier 2 (supported, best-effort, non-gating):** Firefox and Safari desktop; Chrome/Safari on mobile via the shipped touch controls. See §9.2. *(v8.0: supersedes "desktop only / no touch" — touch controls shipped at v7.x and are retained.)* |
| Delivery | Static web app (GitHub Pages). No launcher, no native wrapper. |
| Mode | Single-player only. |
| Business model | None. No ads, IAP, login, or accounts. |
| Save model | Local saves only, in IndexedDB (§10.7). |
| Scope shape | One continuous, hand-authored five-region world (§8.8) with the critical path (five fights, one per region, each region's boss met in-place) and a substantially larger exploration layer around it. |
| Combat | Real-time rhythm-action, fought **in the world** (§8.2): the camera locks to a room of the actual overworld around the foe. No separate battle scenes on the shipped path. |
| Camera / layout | Top-down, HLD-style, everywhere — one camera model for exploration and combat. |
| Aesthetic | Pixel-art in the *Hyper Light Drifter* register (§11.1) at 320×180 logical resolution; art sourced via the AI-generation + import pipeline (§11.1). |
| Music | Six recorded Inhalants tracks are the soundtrack (§11.2). Each shipped track carries an authored beat map; combat judgment derives from the audible track (§8.3). |
| Narrative | Environmental only. World-bible canon (§5a/§5b) surfaces through staged scenes and echoes (§8.8.2) — never dialogue trees or lore dumps. |
| Session target | 10–20 minute sessions; 2–3 hour first completion. |

### 7.2 Out of scope (v1)

Online multiplayer, user-generated beat maps, live beat detection from arbitrary
audio, voice acting, NPCs with dialogue trees or quest-givers, controller rumble as a
required channel, monetization plumbing, band-member switching mid-fight (v2, §8.4),
loot/gear-grind progression (§8.5).

### 7.3 Product pillars

1. **The world is the second game.** Exploration is authored content with its own
   pacing, secrets, and payoff — never connective tissue. A player who only walks the
   critical path sees a fraction of what's there.
2. **Movement is the game (in battle too).** Combat is run, dash, space, and read —
   *Hyper Light Drifter* kinetics with *Melee*-register frame-data depth. Mastery is
   spacing, timing, cancels, and reads, not menu selection.
3. **The chorus drives the fight — audibly.** The beat the game judges **is the beat
   of the playing track** (§8.3). On-beat actions are empowered; enemy attacks
   telegraph and land on the beat. Reading the music is reading the fight.
4. **The untold stories are found, not told.** Every backstory is discoverable by
   walking somewhere and looking (§8.8, §11.1.1). No dialogue, no lore dumps.
5. **Rhythm clarity before difficulty.** Every mechanic must make the beat more
   legible, never less. Off-beat actions always still execute (weaker) — precise
   timing is never the only path (§9.3).
6. **Colossal, readable art.** Silhouette-first enemies that dwarf a small player;
   vivid limited accents on desaturated darks; emissive telegraphs that keep the
   real-time fight legible at a glance.
7. **Accessible depth.** Assist windows, speed options, practice mode, captions, and
   remapping — on the shipped combat path — without removing the ceiling for players
   who want it.

---

## 8. Functional Requirements

### 8.1 Core loop — two interleaved layers

Boot → audio-gesture gate → save slot → optional AV calibration → the drowned world.

1. **The critical path:** five fight nodes (battle/elite/boss), one per region, in
   campaign order. Each node's foe **stands in the world** at its place (v7.8) — the
   player walks up to the actual enemy, not an abstract marker. A save-obelisk stands
   near each fight (§8.8.5). Contact starts the in-world fight (§8.2); victory grants
   rewards (§8.5) and the world continues from that spot. This alone finishes the game.
2. **The world:** around the path is the five-region explorable map (§8.8) — hidden
   paths, secret pockets, and echoes. None of it is required; all of it is findable.

### 8.2 Battle model — real-time action, fought in the world

**In-world fights (v7.13/v7.14, shipped).** Walking into a foe does not load a battle
scene. The camera locks to a screen-sized room of the actual overworld around the foe;
the Phaser-free action sim (`src/systems/action/ActionCombat.ts`) runs mapped onto that
world-space rectangle. Impassable world tiles inside the room become sim obstacles;
each fight node's authored biome venue (floor patch + kitbash set pieces, composed into
the map — `ArenaComposer.composeWorldVenue`) guarantees a fightable circle around the
foe. Victory/defeat runs the rewards → results flow and returns control in-place. The
legacy `ActionBattleScene` and turn-based `BattleScene` remain registered for
regression coverage only and are **retired from the product path**.

**Movement.**
- 8-directional run with acceleration/friction (momentum) and max speed.
- **Dash/dodge:** startup i-frames, committed recovery, short cooldown. An *on-beat*
  dash extends i-frames and refunds cooldown.
- Facing follows movement; attacks are directional.

**Attacks (kit).**
- **Light** — fast startup, low commitment, gatlings into a short combo in a cancel window.
- **Heavy** — slow startup, high knockback/damage.
- **Special** — costs Focus; the kit's defining tool.
- **Ultimate** — costs the full Groove meter (100); a screen-shaking verse. **v1-mandatory:**
  Groove must be spendable, not merely accumulable (§8.5). *(Shipped v8.2: player-centred
  burst hitting everything in a wide radius, armored through startup+active, tier-scaled.)*
- Every attack is a hitbox with frame data (startup/active/recovery), damage, a
  knockback vector, and hitstun.

**Hit reactions.**
- **Hitstun** scaled by damage, enabling true combos.
- **Knockback** magnitude scales with the hit and the victim's accumulated **damage %**
  (*Melee*-style). **DI:** the defender's held direction nudges the knockback vector.
- **Parry / perfect-guard:** an on-beat guard that negates the hit and staggers the
  attacker; off-beat guard is a punishable whiff.

**Cancels & tech.** Attack→dash cancel on the beat; light-gatling chains inside cancel
windows; on-beat recovery-cancel into the next attack. Everything cancellable is
cancellable only inside a few-frame window.

**Encounter flow.** Contact → real-time fight (defeat the wave / survive the boss's
phases, §8.7) → rewards (§8.5) → the world, in place. No turns, no mid-fight menus.

### 8.3 Timing model — the beat is the audible track (v8.0 decision)

**Hard requirement (release gate #1a, §16.2):** the beat against which actions are
judged **must be the beat of the music currently playing.** Implementation contract:

1. Every shipped track carries an **authored beat map**: measured BPM, first-beat
   offset (ms into the file), and named sections (bar-aligned timestamp ranges — verse,
   chorus, breakdown) — hand-verified against the recording, stored per §10.5.
2. Combat judgment derives from the **playing audio element's position**
   (`currentTime`) mapped through that beat map — not from an independent metronome.
   The Web Audio / transport clock remains the scheduling authority (§10.2); it is
   synchronized to the track, never free-running against it.
3. **Game speed** (§9.3) scales the track's `playbackRate` and the judgment clock
   together — heard music and judged beat may never diverge under any setting.
4. The beat-tick sonifier becomes an optional accessibility layer ("audible beat
   tick"), defaulting off once beat maps land.

*Status: **shipped (v8.1)** — all six tracks carry measured beat-grid maps
(`src/data/content/songs/`), the in-world fight judges from the playing element's
position through the live song's grid, game speed couples `playbackRate` + sim, and
the `beat-truth.spec.ts` e2e gates it. The grids are algorithmically measured
(librosa); the hand-verification listening pass is the remaining caveat (§20.2).*

**Judgment tiers.** Four tiers grade each real-time action against the nearest beat.
Off-beat actions always execute, weaker — never a whiff-by-timing:

| Tier | Window | Effect |
|---|---:|---|
| Perfect | ±45 ms | Full empowerment: max bonus damage/knockback, extended dash i-frames, parry active, +Groove (large) |
| Great | ±90 ms | Strong bonus, +Groove |
| Good | ±140 ms | Small bonus |
| Off | outside Good | Base action, no bonus, no Groove |

Assist mode multiplies all windows ×1.5; the calibration offset (§10.3) applies
globally before judgment. Enemy attacks telegraph and land on the beat.
*(Status: **shipped v8.2** — the four tiers grade every action against the playing
song's grid; damage/knockback/Groove/dash-i-frames/parry windows scale per tier;
HUD tier popups + per-tier analytics live.)*

### 8.4 The cast — Inhalants, the band

The playable cast is the band (v7.9): **Amir** (lead guitar), **Bassist**,
**Vocalist**, **Drummer**. The band walks the world together (followers in a conga
line, decorative in v1).

- **v1 (this spec):** the player controls the leader (Amir) with one complete kit —
  light / heavy / special / ultimate / dash / parry per §8.2.
- **v2 (target, out of v1 scope):** each member is a distinct playable kit with a
  signature special and trait (guitar burst zoning, bass shockwave space control,
  vocal sustain/heal pulse, drum-roll gap-close), switchable between fights.

*(v8.0 note: v6.0's song-title hero names — Deereater, Saltminer, Esoterophobe,
Sunshine Sally — are retired as cast names; the songs are the soundtrack, not the
characters. The four legacy role definitions (warrior/tank/mage/healer JSON) back the
retired turn-based path only.)*

**Sightread** — the realization of the concept art's "see the music" — is re-specified
for action combat as a **forecast assist**: a HUD lane previewing the next bars' beats
and any incoming telegraphed enemy attack. v1: available as an accessibility/HUD
setting; v2: also an in-fiction Vocalist kit ability. *(v1 shipped v8.2: the
"Sightread Forecast" setting renders the lane — upcoming grid beats + red strike
markers against a now-line — from the same beat grid judgment uses.)*

### 8.5 Resources and progression

- **HP** (bar) and accumulating **damage %** scaling incoming knockback.
- **Focus** — built by on-beat aggression, spent on specials.
- **Groove** (0–100) — built by on-beat play, clean combos, and parries; **spent in
  full on the ultimate** (§8.2). A Groove meter that cannot be spent is out of spec.
- Progression is deterministic, not loot-driven: boss clears unlock kit tools; one
  relic slot per member plus one shared party charm; relics grant real mechanical
  effects chosen on the results screen.

### 8.6 Encounter design progression (v8.0 — post-luchador curriculum)

One fight per region, ascending in rhythmic and mechanical intensity. Difficulty is
expressed through **track feel (BPM/energy), enemy count, telegraph density, and
frame-data strictness** — not meter-signature changes (retired with the turn-based
model; see §8.7 for how the boss escalates).

| Region (node) | Foe(s) | Track (combat rotation/boss) | Curriculum |
|---|---|---|---|
| The Shallows (`opening_1`) | rot slime | combat rotation | Movement, light/heavy, first on-beat rewards; generous telegraphs |
| The Salt Mines (`mid_1`) | drowned drifter | combat rotation | Dash timing, whiff punishment, first special |
| The Pit Below (`mid_2`) | wraith + drifter pack | combat rotation | Multi-enemy spacing, target priority, crowd DI |
| The Attic of Teeth (`mid_3`) | elite wraith | combat rotation | Parry as offense; cancel-window pressure; tighter telegraphs |
| The Conductor's Hall (`boss_1`) | **the Conductor** | *Quotience* | Full system: phases, section changes, ultimate economy (§8.7) |

Foe roster is **lyric-canon only** (v7.6): slime, drifter, elite wraith, the Conductor.
*(Content-hygiene item: encounter/track file IDs still carry legacy names —
`mid_biome_2_luchadores_*`, `*_clave_*` — around correct contents; rename tracked in
§20.2.)*

### 8.7 Final boss — "The Conductor" (v8.0 re-spec for in-world action combat)

The Conductor is fought in his hall **in the world** (§8.2), rendered at native
colossal resolution. The fight has **three authored phases keyed to HP thresholds**,
and phase escalation is expressed through the *actual song*:

- Each phase binds to an **authored section of *Quotience*** via the track's beat map
  (§8.3): on phase transition, playback jumps to that section's bar-aligned start, and
  the judged beat follows — tempo/feel changes come from the recording itself, not
  from synthetic meter arithmetic.
- Per phase: escalating AI (attack frequency, new telegraphed patterns), tighter
  frame data, and one arena change in the hall (story light, hazard ring).
- All phase data is authored content (§10.5 `BossPhaseConfig` + beat-map sections) —
  never improvised or inferred from audio at runtime.

**Release gate #3 (§16.2, re-scoped):** phase transitions execute on bar boundaries of
the audible track without desync between heard music and judged beat.

*(Status: **shipped v8.2** — the in-world Conductor fight advances phases on the
authored HP thresholds, jumps playback to the bound *Quotience* sections
(`movement_2` @ 28.19s, `movement_3` @ 74.30s — segmentation-derived, grid-snapped,
pending the human listening pass), escalates enemy aggression per phase, and marks
thresholds on the boss bar; `boss-phases-world.spec.ts` covers it on the product path.)*

### 8.8 Exploration — the second game

**8.8.1 World structure.** One continuous hand-authored map (currently 130×34 tiles)
of **five joined regions**, one per movement of the campaign, in order: the drowned
coastal Shallows, the salt-crusted mine road, the carnival approach to the Pit, the
claustrophobic exterior of the Attic, and the flooded plaza before the Conductor's
hall. Regions are visually and structurally distinct (own dressing, obstacle logic,
and accent hue — "one palette, five moods," §11.1.1) but seamlessly connected. The map
is deliberately larger than its critical path so it can hold secrets.

**8.8.2 Echoes — the found backstory.** An **echo** is a discoverable, hand-placed
environmental-story beat off the critical path: a staged prop arrangement with a
context-prompt interaction revealing **one evocative line** of world-bible §5a/§5b
canon — found, never told. Echoes are collectible (persisted per save, §10.7),
optional, and surfaced only as a found/total HUD counter — no map markers. Ten ship in
the current world.

**8.8.3 Secrets and hidden paths.** At least one non-obvious traversal element per
region (a gap readable only up close, a route behind a wreck/structure). Secrets gate
optional rewards (relic, echo, or both) — never critical-path content. Hand-authored,
never procedural.

**8.8.4 What this explicitly is not.** Not loot/inventory management; not NPCs or
dialogue; not a second combat layer (no overworld enemies beyond the standing node
foes); not procedural generation.

**8.8.5 Save-obelisks.** A save-obelisk stands near each fight node (two tiles out, on
walkable ground). Standing beside it prompts rest; resting persists the save in-world
("THE CHORUS RESTS") without touching the fight trigger. Obelisks complement — not
replace — autosave on progression.

---

## 9. Non-Functional Requirements

### 9.1 Performance

- 60 FPS target on Tier-1 browsers at integer-scaled 320×180.
- Audio scheduling stays stable under render stutter: **audio is authoritative, not
  video** — the fight stays rhythm-correct through frame drops.
- Boot stays light: audio is lazy-loaded per scene (`preload="none"`; only the live
  track is fetched — ~45 MB on disk never loads up front).

### 9.2 Platform / compatibility tiers (v8.0)

| Tier | Targets | Bar |
|---|---|---|
| **Tier 1 — release-gating** | Chrome, Edge (current stable, desktop) | Full QA matrix (§16.1) passes; automated e2e gate (Chromium) green |
| **Tier 2 — supported, best-effort** | Firefox, Safari (desktop); Chrome/Safari (mobile, via touch controls) | Boot + core loop verified manually per release; known issues documented, non-blocking. Firefox automated coverage is disabled pending root-cause (§20.2). |

Touch input (on-screen thumbstick + action buttons incl. ultimate,
`src/ui/TouchControls.ts`) ships and is maintained; mobile performance/layout polish is
Tier-2 best-effort in v1. **Mobile-boot hardening (v8.2,** after an owner report of a
phone failing at the gate**):** the audio gate has DOM-level tap fallbacks and a
timeout-guarded `Tone.start()` (it can never hang the front door); production builds
paint uncaught errors into a visible overlay (a phone black-screen becomes a readable
report); the JS build target is `es2019/safari13` for older WebKit; and a
Pixel-5-emulation e2e (`mobile-boot.spec.ts`) pins boot + tap-through + touch-layer
mount. Real-device iOS Safari verification remains the Tier-2 manual bar.

### 9.3 Accessibility (mandatory, day-one, on the shipped combat path)

| Setting | Requirement |
|---|---|
| Remappable controls | Required — including the in-world fight's combat bindings *(shipped v8.2: all six combat actions remappable via Settings → Audio & Controls; fight reads the bindings with sane defaults)* |
| Keyboard-only play, no required simultaneous presses | Required |
| Separate volume sliders (music / SFX / UI) | Required |
| Captions for musically meaningful events ("attack incoming left," "the music shifts," "groove full") | Required — in the in-world fight *(shipped v8.2: telegraph direction, boss phase shifts, groove/ultimate events)* |
| Reduced motion mode | Required *(shipped, verified in-fight)* |
| Photosensitivity-safe VFX mode | Required — no flashing above seizure-risk thresholds |
| Game speed 70% / 85% / 100% | Required — must scale music playback and judgment together (§8.3.3) |
| Assisted timing windows | Required — precise timing is never the only viable path *(shipped, ×1.5 in-fight)* |
| Practice mode with no fail state | Required — in the in-world fight *(shipped v8.2: the sim floors player HP at 1; entering a fight announces it)* |
| AV calibration screen | Required *(shipped; offset verified applied in-fight)* |
| Optional audible beat tick | Required *(shipped v8.1: "Beat Tick (combat)" toggle, off by default; the old always-on sonifier click is retired from the fight)* |

Haptics remain additive-only for any future controller pass.

### 9.4 Security / privacy

- No accounts, no PII, no server-side storage.
- Telemetry (§14) is local-only and consent-gated via an in-game toggle; consent state
  lives in the save profile. No network transmission of any player data in v1.

---

## 10. Technical Architecture

### 10.1 Required stack

**TypeScript + Phaser + Tone.js + Web Audio API**, built with Vite; unit tests in
Vitest; e2e in Playwright; deployed as a static site via GitHub Actions → GitHub Pages.

### 10.2 Authoritative timing rule (hard constraint)

**No gameplay judgment may be derived from `setTimeout`, `setInterval`, or
`requestAnimationFrame` alone.** These drive visuals only. The source of truth for
musical/combat state is the audio clock — and per §8.3, that clock must be
synchronized to the audible track's beat map, never free-running against it. This is
non-negotiable and a release gate (§16.2).

### 10.3 Audio subsystem requirements

| Requirement | Implementation |
|---|---|
| Soundtrack playback | `SongPlayer` (`src/systems/audio/SongPlayer.ts`): six MP3s, lazy-loaded, crossfaded per scene mode (menu/explore/combat/boss), combat rotation |
| Beat authority | Per-track **beat-grid maps** (`SongMap`: fitted BPM, first-beat offset, full per-beat grid, sections) — judgment reads the playing element's position through the live song's grid (`SongBeat.ts`, loop-aware) *(shipped v8.1)* |
| Scheduling clock | `TransportClock` (Tone.Transport) — fallback judgment grid only when nothing is audible (blocked autoplay/headless); never free-running against an audible song |
| Mobile/autoplay compliance | First `play()` fired inside the audio-gate gesture handler; rejections never break a scene |
| Game speed | Song `playbackRate` and sim scaled together; grids are file-time so heard/judged beat cannot diverge (§8.3.3) *(shipped v8.1)* |
| Calibration | User-adjustable global AV offset, persisted, applied before judgment *(shipped)* |
| Optional beat tick | `BeatTick` synth, opt-in via §9.3 setting, triggered from the live song grid *(shipped v8.1; `BeatmapSonifier` retired from the fight, serves the retired path only)* |

### 10.4 Audio startup requirement

The first screen after boot is a mandatory **"press any key or click/tap to continue"**
gate whose sole job is to create/resume the `AudioContext` and prime the first track
from a user gesture. No autoplay is attempted before it.

### 10.5 Data-driven content architecture

All gameplay content is data, validated at load, never hardcoded in scenes. Canonical
JSON Schemas in [`docs/technical/schemas/`](../technical/schemas/), mirrored as
TypeScript types in `src/data/schemas/`, ajv-validated via `ContentLoader.ts`:

- `beatmap.schema.json` — per-track timing data. **v8.0: extends to the authored
  beat map of §8.3** (measured BPM, first-beat offset, named bar-aligned sections)
  binding to a real audio file; the legacy synthetic meter-sequence/event fields
  remain for the retired path and the sonifier.
- `encounter.schema.json` — enemy wave, track binding, rewards.
- `ability.schema.json` — **legacy (retired path)**: phrase-based ability definitions
  for the turn-based model. Action-combat kits are frame-data definitions in
  `ActionCombat.ts` today; extracting them to a validated `moveset` schema is the
  intended follow-on once per-member kits (v2, §8.4) begin.

Internal runtime-validated schemas (hand-written shape validators, fail-loudly at
load): `Enemy.ts`, `HeroClass.ts` (legacy roles + band display data), `CampaignNode.ts`
(node graph; `encounterPool` per non-boss node), `BossPhaseConfig.ts` (HP-threshold
phases — re-targeted at §8.7's section-based phases when built).

### 10.6 Rendering and scene architecture

- Fixed logical resolution **320×180**, 16:9, integer scaling, `image-rendering:
  pixelated`. Generated art is authored at up to ~1.5× logical density (v7.13) with
  engine scales compensating — more detail per screen pixel, same on-screen sizes.
- Scene stack (`src/main.ts`):

| Scene | Status | Purpose |
|---|---|---|
| BootScene | shipped | Manifest load, browser support check |
| AudioGateScene | shipped | Gesture gate; audio context + first-track priming |
| MainMenuScene | shipped | Start, continue, settings; title key-art |
| SaveScene | shipped | Slot create/load/delete |
| CalibrationScene | shipped | AV sync test + offset save (keyboard and pointer) |
| OverworldScene (+ `overworld/WorldFight.ts`, `env/ArenaComposer.ts`) | shipped — **the product path** | The five-region world: movement, foes standing in-world, venues, obelisks, echoes, and the in-world fight controller |
| ResultsScene | shipped | Rewards, relic choice, unlocks; routes the final boss's victory into the finale |
| FinaleScene | shipped (v8.5) | The ending: staged closing lines, wordmark, credits; the world stays open after |
| SettingsOverlay | shipped | Always-available two-page settings modal |

*(v8.3: the retired `BattleScene`/`ActionBattleScene` and their orphaned combat
systems were deleted outright once boss-phase coverage migrated to the product path —
release gate #7 is satisfied structurally. Git history is the archive.)*

### 10.7 Storage and persistence

All save data in **IndexedDB**: settings, calibration offset, campaign progress,
unlocks, relics, analytics consent, found echo ids. Verified across reload and
browser restart (release gate #6).

---

## 11. Content and UX Requirements

### 11.1 Art direction — *Hyper Light Drifter* register

**Target feel:** colossal, imposing, silhouette-first enemies dwarfing a small nimble
player; a vivid, ruthlessly limited palette (abyssal teal, plum/magenta, ember-gold,
blood on desaturated near-black); additive glow on eyes, arcs, telegraphs, and the
chorus's light. Emissive readability is a hard requirement: every telegraph and
hitbox-active frame glows so the real-time fight reads at a glance.

**Sourcing (v8.0 — supersedes all "no image generation" language):** production art is
**AI-generated through the in-repo pipeline** and deterministically imported —
`tools/pixelart/generate_ai.py` (keyless Flux via Pollinations) → cleanup passes
(background flood-key, largest-island filtering, mist-scrub) → `smooth_downscale()`
(clean LANCZOS, hard alpha, **no palette quantization** since v7.14) → committed PNGs
in `assets/` slots. Prompts are cataloged 1:1 with the manifest in
[`docs/design/art-prompts.md`](../design/art-prompts.md); style coherence comes from
shared per-biome/per-cast style clauses and a **pinned top-down camera clause** in
every environment prompt (the v7.10 audit's root-cause fix). Hand-drawn or
commissioned art drops into the same slots and always wins over generated art.
Procedural code-drawn art (`tools/pixelart/`) remains the fallback for not-yet-generated
slots and all deterministic regeneration plumbing.

| Asset type | Spec |
|---|---|
| Base resolution | 320×180 logical; art authored up to ~1.5× density (§10.6) |
| Tile size | 16×16 |
| Player sprite | small, silhouette-readable band members (individually recognizable at world scale) |
| Standard enemy | 48×48+; elites/bosses colossal (the Conductor ~2.9× player height, native-resolution) |
| Glow/bloom | additive emissive layer on eyes, edges, telegraphs, hazards; beat-pulsing accents |
| Environments | designed floors and venues (§11.1.1) — no noise fills, no void centres |
| Animation | low frame count, high pose contrast (anticipation → impact → recovery), 8–12 fps; strips derived from one base pose per character for identity stability |
| Palette policy | master palette discipline; per-region dominant hue ("one palette, five moods") |

**Acceptance criteria** (judged, not vibes): (1) no tint-swaps or upscales — bosses at
native colossal resolution; (2) animation states, not static sprites (§11.5 standard);
(3) every arena/venue a distinct authored place (§11.1.1); (4) consistent light source
+ emissive pass; (5) master-palette discipline; (6) deterministic regeneration
(`generate_all.py` + committed generator scripts); (7) designed surfaces — every tile
reads as *grass/stone/water*, never RNG static; (8)–(10) per the §11.5 manifest: every
row filled with real art, every character/enemy carrying its full state set, every
biome a full tileset + props. Gaps tracked in §20.4 only — never implied shipped.

### 11.1.1 Environments — every fight happens in a specific place

**No generic battlefields.** Each region's fight happens at a **venue composed into
the world itself** (v7.14): the biome's authored floor is painted as an edge-faded
patch blended into the surrounding map, its kitbash set pieces stand around the spot
in world space, and the fight locks its room onto that exact dressed ground. Each venue
stages an untold story (canon in [world-bible](../design/world-bible.md) §5a) readable
without text:

| Node | The place | Hue | The untold story its set pieces stage |
|---|---|---|---|
| `opening_1` | **The Shallows** — a drowned village green | teal | A ring of boats moored around a sunken maypole; one empty boat still straining at its rope toward the surface. The village went under mid-festival — and somebody almost got away. |
| `mid_1` | **The Salt Mines** — a gallery of the calcified | ember/gold | Miners turned to salt mid-swing, all facing one faintly glowing tunnel mouth; one statue faces the other way — mid-run. |
| `mid_2` | **The Pit Below** — a sunken carnival ring | plum/magenta | A ring with ropes snapped **outward**, dead lantern strings overhead — two still burning — and every chair tipped over *away* from the ring. |
| `mid_3` | **The Attic of Teeth** — a room that should not fit indoors | blood/rust | A bolted door with claw-gouges on the *inside*, walls black with scrawl — staves and bars scratched among it — and a small bed made of pens. |
| `boss_1` | **The Conductor's Hall** — an orchestra with no orchestra | ink + ember | Empty stands holding blank pages (the last row's are full), melting clocks each stopped at a different time. He rehearses an unfinished ending with players who drowned rehearsing it. |

Design rules: a specific place, not a theme (postcard test); story staged physically
in 2–4 set pieces; fight-readable (story in dressing, play-space high-contrast; story
accents never telegraph-red); a beat-pulsing story light in every venue; one palette,
five moods. The overworld region *approaching* each venue foreshadows it in its own
visual language (§8.8.1).

**Landforms (v7.15 direction, shipped v8.4):** landscape-scale forms over the scene —
per-region colossal outcrops that break the map silhouette (scenery layer) and canopy
trees whose crowns overhang the play space, drawn **above the player layer** and
alpha-fading while the player walks beneath (the HLD height trick). Deterministic
cell-hash scatter, kept clear of markers/echoes/spawn. Elevation shading/terracing
remains a future polish item.

### 11.2 Music and audio content spec (v8.0 — the recorded soundtrack)

**The soundtrack is six recorded Inhalants tracks** (owner-supplied, committed in
`assets/audio/`), streamed lazily and crossfaded by scene mode (§10.3):

| Mode | Track |
|---|---|
| Menu | *Sunshine Sally* |
| Explore | *Deereater* |
| Combat (rotates per fight) | *Glassriff* / *John's Anus* / *Truckers for Christ* |
| Boss | *Quotience* |

**Per-track deliverables (v1):** the audio file plus an **authored beat map** —
measured BPM, first-beat offset, the full beat grid, and named bar-aligned sections
(§8.3) — hand-verified against the recording. The boss track additionally requires
per-phase section bindings (§8.7). A battle SFX pack (hits, parry, dash, UI) completes
the audio content set. *(Status v8.1: all six beat-grid maps shipped and validated
(`tools/audio/measure_beats.py` → `src/data/content/songs/`); the human listening pass
over the measured grids and the §8.7 boss sections remain — §20.2.)*

**Explicitly retired:** the DAW-stem/tempo-map pipeline spec and the
`tools/gbmusic/` chiptune production path (demo-master slicing, `.lsdsng` drafts,
LSDJ hand-tuning) are **historical** — superseded by the real recorded soundtrack at
v7.7. The tooling and drafts remain in-repo as archived direction work
([`docs/design/music-direction.md`](../design/music-direction.md)); they are not v1
deliverables and nothing ships from them.

### 11.3 UX rules — the fight HUD

The in-world fight must always show: the framed band plate (HP bar, Focus pips, Groove
bar, damage %), a **beat indicator** pulsing with the judged beat, enemy HP hugging
each sprite, a screen-space named boss bar in boss fights, and a controls hint that
auto-fades. On-beat feedback must be legible (hit flash / scaled arcs). Critical
information never relies on color alone. Once §8.3 tiers land, judgment feedback
(Perfect/Great/Good) joins the HUD; once Sightread lands (§8.4), its forecast lane does.

### 11.4 Current asset inventory (as of 2026-07-14)

| Asset | Location | Status |
|---|---|---|
| Playable band (4 members × idle/run/attack strips, derived from one base pose each) | `assets/sprites/band/{amir,bassist,vocalist,drummer}/` | Shipped (v7.9 AI-generated cast; prior hand-drawn originals archived in `assets/reference/band-original/`) |
| Foes (slime, drifter, elite wraith) + the colossal Conductor | `assets/sprites/enemies/` | Shipped (v7.11 resprite in the band's register; Conductor native-resolution) |
| Six-track soundtrack + beat-grid maps | `assets/audio/*.mp3` (~45 MB, lazy-loaded) + `src/data/content/songs/*.json` | Shipped (v7.7 audio; v8.1 measured beat grids via `tools/audio/measure_beats.py`). Listening-pass verification owed (§20.2) |
| Five-region overworld (130×34 Tiled JSON, BFS-validated reachability) + 20-tile sheet | `assets/tilemaps/`, `tools/overworld/generate_overworld_map.py` | Shipped (v7.0; ground/water/clustering/value pass v7.12; de-pixelation v7.14) |
| Environment kits (5 biomes + shared, 28 pieces) + venue composition | `assets/sprites/env/`, `tools/pixelart/envkit.py`, `ArenaComposer.ts` | Shipped (v7.11 coherent top-down kits; v7.14 world venues) |
| Region landmarks (5 colossal set-pieces) | `assets/sprites/overworld/landmarks.png` | Shipped (v7.1/v7.3) |
| Overworld NPCs (ambient figures), props, obelisks, echo runes | `assets/sprites/` | Shipped |
| Title key-art + framed UI kit (plates, boss bar) | `assets/`, `tools/pixelart/ui.py` | Shipped (v7.11 HUD). Authored wordmark deferred (v7.12 — needs lettered-by-hand approach) |
| SFX | `src/systems/audio/SfxPlayer.ts` (procedural; `assets/audio/sfx/` empty) | First fill shipped v8.3 (hits/hurt/parry/dash/ultimate, synthesized). Real recorded SFX remain a §11.5 manifest row (§20.2) |
| Legacy/reference: pre-band hero art, animation GIFs, gbmusic `.lsdsng` drafts, demo master (gitignored) | `assets/reference/`, `tools/gbmusic/output/` | Archived — historical direction material, no v1 deliverables |

### 11.5 Production art asset manifest

The checklist the game's art is built and judged against; per-slot generation prompts
live in [`docs/design/art-prompts.md`](../design/art-prompts.md) (kept 1:1).

**Animation-state standard.** Playable band members target **≥22 states** (idle,
idle_combat, walk, run, dash, jump, fall, land, attack_1/2/3, heavy, special,
ultimate, parry, block, hurt, death, downed, revive, victory, interact + portrait).
Enemies target **≥6 states** (idle, move, attack, telegraph, hurt, death; ranged/elite
add projectile/special). The boss is authored per-phase (intro, idles, attack set,
transitions, stagger, death).

| Category | Scope | Approx. slots |
|---|---|---|
| Playable band | 4 members × ~22 states + portraits | ~92 |
| Enemies | ~18 types across 5 biomes × 6 states | ~114 |
| Boss(es) | The Conductor (3 phases) + 1–2 mid-bosses | ~36 |
| Tilesets | 5 biomes × ~9 sheets (autotile, cliffs, transitions, decals, occluders, animated) | ~45 |
| Props & destructibles | ~12/biome + ~10 shared interactables | ~70 |
| Landmarks | 5 primary + ~2 secondary per biome | ~15 |
| Parallax/venue backgrounds | 5 biomes × ~4 layers + weather | ~30 |
| VFX library | hit sparks, arcs, parry burst, dash trail, dust, splash, blooms, projectiles, dissolves, status auras, chorus light | ~30 |
| UI kit | wordmark, menu illustration, HUD, icons, cursor, panels, results, settings, bitmap font | ~90 |
| **Ambient figures** (v8.0: re-scoped from "questgivers" — §8.8.4 forbids dialogue NPCs; these are silent world-dressing characters) | 4 old-hero figures + ~6 townsfolk × (idle + portrait-less) | ~20 |
| Items & pickups | health orb, currency, ~15 relics, keys | ~25 |
| **Total** | | **~567 named slots** (thousands of frames) |

Slots are filled by the §11.1 pipeline (AI-generated per catalog, or real art dropped
into the same slots). Procedural stand-ins fill slots temporarily and never count as
shipped. Progress tracked in §20.4.

---

## 12. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Judged beat and audible music drift back into two clocks** (§8.3 regression — e.g. a new scene bypassing `SongBeat`, or beat maps not re-measured after a track swap) | Low (shipped v8.1) | Critical | `beat-truth.spec.ts` e2e gates #1a on every push; `measure_beats.py` re-run is part of any track change; QA soak measures heard-vs-judged drift (§16.1) |
| **Pivot regressions:** features that existed in a retired path read as "done" while missing from the shipped path (already happened twice: Groove-spend, practice mode) | High | High | v8.0 rule: §20 tracks status **per the shipped path only**; retired scenes scheduled for deletion (§10.6); every §9.3 item re-verified in-fight each release |
| Beat maps authored inaccurately (wrong BPM/offset) make on-beat play feel arbitrary | Medium | High | Hand-verification protocol per track (tap-test + waveform check); calibration screen absorbs residual device latency; drift instrumentation in QA |
| Visual-timer judgment code creeps in under pressure | Medium | High | Hard rule §10.2 + lint/test flagging timer APIs in judgment paths; QA soak under forced render load |
| Accessibility slips to post-launch | Medium | High | §9.3 items are release gates (§16.2 #5), tested per pass on the shipped path |
| AI art pipeline produces off-register or perspective-broken assets | Medium | Medium | Pinned camera/style clauses in every prompt (v7.10 root-cause fix); import cleanup passes; screenshot review against §11.1 criteria before merge |
| Scope creep (multiplayer, switching, procedural content) mid-production | Medium | High | §7.2 is a standing reference; changes require a PRD revision row, not ad hoc addition (the v7.x touch-controls lesson — shipped without a PRD row, caught by audit) |
| Firefox/Safari timing or boot incompatibilities discovered late | Medium | Medium | Tier-2 manual verification per release (§9.2); Firefox e2e root-cause tracked (§20.2); calibration absorbs residual latency |
| Single-owner bus factor (one person is Product/Eng/Art/Audio/QA) | High | Medium | This PRD + §20 + the audit docs are the durable record; deterministic pipelines mean any competent contributor can regenerate and continue |

---

## 13. Dependencies and Assumptions

- The six recorded tracks are cleared by the owner (band) for inclusion; no third-party
  licensing in v1.
- The AI image-generation endpoint (keyless Pollinations/Flux) remains reachable from
  the build environment for asset regeneration; committed PNGs insulate players and CI
  from any outage.
- No regulatory/platform requirement for accounts or age-rating compliance in v1
  (no storefront distribution yet — §18).
- Desktop-first remains acceptable; mobile is Tier-2 best-effort (§9.2), not rejected
  long-term.

---

## 14. Analytics and Telemetry

Local-only, consent-gated (in-game toggle, off by default, §9.4). The v8.0 event set
is re-based on the **shipped path**:

**Live today:** `audio_gate_completed`, `calibration_completed`, `battle_started`,
`encounter_cleared`, `encounter_failed`, `assist_mode_enabled`, `save_loaded`,
`echo_found`, `obelisk_rest`, and (v8.1) `judgment_onbeat` / `judgment_offbeat` —
fired for every attempted fight action, judged against the playing song's grid.

**Required with pending features (§20.2):** per-tier
`judgment_perfect|great|good|off` (upgrades the binary pair when §8.3 tiers land),
`ultimate_used` (with §8.5 spend), `boss_phase_reached` (with §8.7),
`sightread_enabled` (with §8.4 forecast).

**Retired-path events removed from spec:** `ability_used`, `sightread_used` (phrase-model
semantics).

This set makes every §5 KPI computable from real play.

---

## 15. Delivery Plan and Roadmap (re-cut 2026-07-14)

Phases are sequential from v8.0 adoption; each exit condition is verifiable against
§20. Durations assume the current single-owner + agent-assisted cadence.

| Phase | Focus | Exit condition |
|---|---|---|
| **P1 — Beat truth** (~1 week) | §8.3: author beat maps for all six tracks; sync judgment to the playing track; game speed scales both; sonifier → opt-in setting | Heard-vs-judged drift ≤ 30 ms sustained in QA soak; gate #1a passes |
| **P2 — Combat completion** (~2 weeks) | §8.3 four tiers; §8.5 ultimate spend; §8.7 phased in-world boss on song sections; §8.4 Sightread forecast lane | Boss reaches phase 3 in live play; all §8 combat requirements demonstrable in the in-world fight |
| **P3 — Accessibility parity** (~1 week) | §9.3 gaps: practice mode, in-fight captions, combat remap | Every §9.3 row verified on the shipped path |
| **P4 — Content & art depth** (~3 weeks) | §11.5 manifest burn-down (states, VFX, wordmark, SFX pack); §11.1.1 landforms (v7.15 direction); encounter/track ID hygiene (§8.6); retired-scene deletion | §11.1 criteria (1)–(7) pass screenshot review across all screens; no retired scenes in the build |
| **P5 — Hardening & release** (~2 weeks) | §16.1 QA matrix on real Tier-1/Tier-2 browsers + devices; Firefox root-cause; balance; soak | All §16.2 gates green; Tier-1 matrix 100% |

Explicitly deferred past v1: band-member switching (§8.4 v2), moveset schema
extraction (§10.5), additional biome content beyond the five regions, storefront
distribution.

---

## 16. QA, Acceptance Criteria, and Release Gates

### 16.1 QA matrix

| Area | Mandatory test |
|---|---|
| **Beat truth** | Instrumented heard-vs-judged beat drift on every track and speed setting, under forced render load |
| Timing | Judgment stays audio-authoritative under stutter; calibration offset applies after refresh |
| Browser support | Tier 1 full matrix; Tier 2 boot + core loop, incl. touch controls on a real mobile device |
| Saves | Create, overwrite, delete, corruption recovery; obelisk rest persists; echoes persist |
| Content | Invalid beat maps/encounters fail validation before runtime; campaign reachability check green |
| Boss | Phase transitions land on bar boundaries of the audible track (§8.7) |
| Accessibility | Every §9.3 row exercised **in the in-world fight** |
| Photosensitivity | No banned flash patterns in default or boss VFX |

### 16.2 Release gates (all must be true)

1. All combat timing is audio-authoritative (§10.2) — never visual timers.
   **1a (v8.0):** the judged beat is derived from the audible track via its authored
   beat map, on every track and every speed setting (§8.3).
2. The game boots into a user-gesture audio gate; no prohibited autoplay.
3. The Conductor's phase transitions execute on bar boundaries of the audible track
   without desync (§8.7).
4. Pixel art remains crisp at supported resolutions (integer-scaled 320×180).
5. Every §9.3 accessibility feature is present, discoverable, and functional **on the
   shipped combat path**.
6. Save data persists in IndexedDB across refresh and browser restart.
7. No retired scene is reachable by a player.

---

## 17. Stakeholders and RACI

All discipline roles are currently held by the owner (with agent-assisted execution);
the matrix defines the intended hand-off shape as the team grows.

| Activity | Product | Engineering | Art | Audio | QA | Accessibility |
|---|---|---|---|---|---|---|
| PRD approval | A/R | C | C | C | C | C |
| Combat/timing architecture | C | A/R | I | C | C | I |
| Beat-map authoring & verification (§8.3) | C | R | I | A/R | C | I |
| Content schemas | C | A/R | I | C | I | I |
| Art pipeline & manifest (§11.1/§11.5) | C | I | A/R | I | I | C |
| Accessibility feature set | C | R | C | C | C | A |
| QA matrix & release gates | C | C | I | I | A/R | C |

---

## 18. Open Questions

1. Distribution channel post-v1 (itch.io, standalone site, storefront) — affects
   whether accounts/monetization stay permanently out of scope.
2. Mobile as a Tier-1 target in v2 (touch controls exist; performance/layout polish
   and touch-latency window tuning would be the work).
3. Band-member switching design (v2, §8.4): between-fight selection vs. mid-fight
   tag — and whether followers gain combat presence in v1.5.
4. Wordmark production path (v7.12: AI text rendering unreliable; needs hand-lettering).
5. ~~Whether the retired turn-based systems are deleted outright or archived~~ —
   **answered v8.3: deleted outright; git history is the archive** (consistent with
   how this repo has always treated superseded work).

*(Resolved since v7.x: title — **The Drowned Chorus**; narrative — the world bible;
music sourcing — the six recorded tracks.)*

---

## 19. Appendix

- Research: [`docs/research/deep-research-report.md`](../research/deep-research-report.md)
- Schemas: [`docs/technical/schemas/`](../technical/schemas/)
- Design docs: [art bible](../design/art-bible.md) · [art prompts](../design/art-prompts.md) ·
  [world bible](../design/world-bible.md) · [AAA art audit](../design/aaa-audit.md) ·
  [music direction (historical)](../design/music-direction.md)
- Audits: [PRD audit 2026-07-14](./prd-audit-2026-07-14.md)
- Glossary:
  - **Beat map** — per-track authored timing data: measured BPM, first-beat offset,
    named bar-aligned sections (§8.3).
  - **On-beat** — a real-time action whose timestamp falls within a judgment window of
    the audible track's nearest beat.
  - **Groove** — the 0–100 shared meter built by on-beat play, spent in full on the
    ultimate.
  - **Focus** — the per-fight resource built by on-beat aggression, spent on specials.
  - **Sightread** — the forecast assist previewing upcoming beats and telegraphed
    attacks (the concept art's "see the music").
  - **Echo** — a hand-placed, collectible environmental-story beat (§8.8.2).
  - **Venue** — a fight node's authored biome ground + set pieces composed into the
    world map, on which its in-world fight room locks (§11.1.1).
  - **DI (directional influence)** — defender's held direction nudging knockback.
  - **Phrase** *(legacy)* — the retired turn-based model's authored input sequence.

---

## 20. Implementation Status (as of 2026-07-14, v8.0 re-cut)

Factual snapshot of the repository against this PRD. **Status is tracked against the
shipped product path only** — a feature that exists solely in a retired scene is a gap
here, not a checkmark (the v8.0 rule; see the audit for why). Where this section and
§1–§19 disagree about reality, this section wins; §1–§19 win about requirements.

Verified this cut (v8.7): `npm test` — **115/115 unit tests** (15 files, incl. the balance harness); **17 e2e
test cases in 10 Playwright spec files** (Chromium gate, incl. `beat-truth.spec.ts`
(gate 1a), `boss-phases-world.spec.ts` (gate 3, product path), and
`mobile-boot.spec.ts`); typecheck and production build green. *(Counts dropped from
v8.2's 168/22 because the retired turn-based path and its tests were deleted — every
remaining test covers shipped code, which is the honest number.)*

### 20.1 Built, tested, and verified on the shipped path

| Area | Status |
|---|---|
| Five-region explorable world (§8.8) | 130×34 seamless map, five regions in campaign order, region-authored dressing/obstacles/tints, BFS-validated reachability at generation time; secret spurs per region |
| Echoes (§8.8.2) | 10 hand-placed, E-to-interact, one-line world-bible fragments; persisted per save; HUD counter; `echo_found` fires |
| Foes stand in the world (§8.1) | Node foes idle at their places (locked = dark silhouettes, cleared = ember); the Conductor colossal in-world |
| Save-obelisks (§8.8.5) | Beside every fight node; rest persists through the real IndexedDB save (e2e-proven, no fight trigger) |
| **In-world fights (§8.2)** | `WorldFight`: camera-locked room of the actual overworld; sim obstacles from impassable tiles (`resolveObstacles`, unit-tested); venues (biome floor + set pieces) composed into the map with a guaranteed fightable circle; rewards → results → in-place return; e2e asserts no battle scene loads |
| Action sim (§8.2) | 8-dir momentum, dash i-frames + on-beat extension, light/heavy frame data with active hitboxes, hitstun, damage-%-scaled knockback, player DI, on-beat parry (off-beat = punishable), rhythm-gated cancel combos, Focus special, enemy telegraph AI — 13+ dedicated unit tests |
| **Beat truth (§8.3, gate #1a — v8.1)** | All six tracks measured into validated beat-grid maps (`SongMap`, full per-beat grids — real recordings drift 8–16% off a constant BPM line, so the grid judges, not a line); fight judgment reads the **playing element's position** through the live song's grid (loop-aware, calibration + assist preserved); transport grid is fallback only when nothing is audible; game speed couples song `playbackRate` + sim; opt-in Beat Tick replaces the retired always-on sonifier click; `judgment_onbeat/offbeat` fire per attempted action. E2e-proven on the audible path (`beat-truth.spec.ts`): song map = playing song, judgment flips with the audio, rate coupling at 70%. |
| **Four-tier judgment (§8.3 — v8.2)** | Perfect/Great/Good/Off windows (±45/90/140 ms ×assist) graded against the playing song's grid; damage, knockback, Groove gain, dash i-frames, and parry windows all tier-scaled in the sim; HUD tier popups; per-tier + binary analytics |
| **Ultimate (§8.5 — v8.2)** | Full-Groove (100) spend: player-centred burst (radius 64) hitting every foe once, armored through startup+active, tier-scaled; groove bar pulses when ready; screen shake (reduced-motion/photosensitivity aware); `ultimate_used` fires |
| **Phased in-world boss (§8.7 — v8.2)** | HP thresholds advance movements; playback jumps to bound *Quotience* sections; enemy aggression escalates (shorter telegraphs/recovers, faster approach); boss-bar phase markers; `boss_phase_reached` fires; e2e-covered on the product path |
| **Sightread forecast (§8.4 v1 — v8.2)** | Settings toggle renders the forecast lane: upcoming beats from the judged grid + red markers for telegraphed strikes vs a now-line |
| **§9.3 parity in the shipped fight (v8.2)** | Practice mode (sim HP floor at 1), captions (telegraph direction, phase shifts, groove/ultimate), remappable combat bindings (all six actions, two-page settings UI) |
| **Battle SFX (v8.3)** | Procedural hits (on-beat brighter)/hurt/parry/dash/ultimate from sim state transitions; SFX volume slider honored |
| **Relics live again (§8.5 — v8.3)** | `applyRelics` re-targeted to the action arena and applied at fight start (opening Focus / opening guard / banked Groove); the post-pivot inert-relics regression is closed and unit-pinned |
| Timing plumbing (§8.3) | Judgment never touches UI timers; calibration offset applied before judgment; assist ×1.5 applied |
| Soundtrack playback (§11.2) | Six real tracks, lazy-loaded (`preload="none"`), scene-mode crossfade, combat rotation, gesture-primed for mobile autoplay |
| Band cast (§8.4) | Four AI-generated members in one register, per-member idle/run/attack derived from a base pose; the band walks the world as a conga; leader fights with their real sprite |
| Art (§11.1) | AI-pipeline backdrops/foes/band/landmarks/props/kits; designed floors + coherent pinned-camera kits + menacing resprites + framed HUD (v7.11); ground/water/clustering/value pass (v7.12); 1.5× legibility re-render (v7.13); quantization-free downscale + world venues (v7.14) — all screenshot-verified |
| Venues & story staging (§11.1.1) | All five places built and composed into the world with beat-pulsing story lights |
| Persistence (§10.7) | Full save lifecycle incl. echoes, consent, calibration; verified across reload |
| Analytics (§14) | Consent toggle + the eight "live today" events fire on the shipped path |
| Accessibility (§9.3, partial) | Assist windows, reduced motion, photosensitivity-aware FX, volume, speed (judgment-side), calibration, keyboard+pointer gates — verified in the shipped fight. **Gaps below.** |
| Touch controls (§9.2) | On-screen thumbstick + action buttons shipped |
| CI/deploy | Build + typecheck + unit + Chromium e2e gate → GitHub Pages on every master push; subpath boot verified |

### 20.2 Open gaps (ranked; per the shipped path)

1. **Beat-map listening pass (§8.3/§11.2):** the six grids and the two Quotience
   section boundaries are algorithmically measured (librosa; 84–92% constant-tempo
   stability, hence grid-based judgment); a human tap-along verification per track is
   still owed (cheap, needs ears).
2. **Real-device mobile verification (§9.2):** the emulatable floor is e2e-pinned
   (`mobile-boot.spec.ts`) and the boot path hardened (v8.2), but the owner-reported
   iOS failure needs a real-device check against the next deploy — the new fatal-error
   overlay will make any remaining crash readable.
3. **Asset manifest depth (§11.5):** character animation-state sets and real recorded
   SFX remain (procedural `SfxPlayer` fills the slots); wordmark shipped v8.5,
   landforms v8.4, core combat VFX (parry ring, dash ghosts, death dissolve,
   sparks, arcs, telegraphs) v6.2–v8.5 — elevation shading/terracing is the
   remaining terrain polish.
4. **QA matrix on real browsers/devices (§16.1)** and the Firefox e2e root-cause
   (excluded from the gate since v4.1) (P5).
5. **Legacy ability/role content** (`src/data/content/abilities|heroes`) remains as
   validated data with no runtime consumer — earmarked as the seed of the v2
   per-member moveset schema (§10.5), not deleted.

*(Closed by v8.2–v8.3: four-tier judgment, ultimate, phased boss, §9.3 parity,
Sightread v1, analytics parity, battle SFX first fill, the relics regression,
content-ID hygiene, and retired-code deletion.)*

### 20.2a Release-gate status (§16.2, verified this cut)

| Gate | Status |
|---|---|
| 1. Audio-authoritative timing | ✅ Judgment never touches UI timers |
| 1a. Beat truth — judged beat = audible track | ✅ Shipped v8.1; held by `beat-truth.spec.ts` on every push |
| 2. Gesture-driven audio gate, no autoplay | ✅ Hardened v8.2 (DOM fallbacks, timeout-guarded resume) |
| 3. Boss phase transitions on the audible track | ✅ Shipped v8.2; held by `boss-phases-world.spec.ts` |
| 4. Crisp pixel scaling | ✅ Integer-scaled 320×180 |
| 5. Every §9.3 feature on the shipped path | ✅ All rows shipped as of v8.2 (see §9.3 table) |
| 6. IndexedDB persistence across restarts | ✅ Held by boot-flow + obelisk specs |
| 7. No retired scene reachable | ✅ Satisfied structurally (deleted, v8.3) |

All seven gates hold and the verifiable ones are enforced by CI on every push. The
remaining §20.2 items are **owner-gated** (beat-map listening pass, real-device iOS
check, real recorded SFX, real-browser QA matrix, Firefox root-cause environment) or
**art-depth polish** (authored per-frame enemy states, elevation shading) — none block
the gates above.

### 20.3 Next increment

P1–P3 shipped; P4's hygiene/feel pass shipped (v8.3). Remaining P4 is the **§11.5
manifest burn-down**: the v7.15 landform art pass (colossal outcrops, canopy
overhangs above the player layer), character animation-state depth, the VFX library,
the hand-lettered wordmark, and real recorded SFX into the `SfxPlayer` slots. Then
P5 hardening (real-device QA matrix, Firefox root-cause, balance, soak).

### 20.4 Asset-manifest progress

Tracked slot-by-slot against §11.5 in [`docs/design/art-prompts.md`](../design/art-prompts.md)
and the [AAA audit](../design/aaa-audit.md) burn-down (P0–P2 shipped; P3 wordmark and
landform pass open). Filled as real (AI-pipeline or provided) art: band (4), foes (4),
venue kits (28 pieces), landmarks (5), backdrops (5, now venue-superseded), title
key-art, NPCs/props/obelisks. Open rows: full animation-state sets, VFX library, SFX,
parallax layers, wordmark, remaining enemy types beyond the lyric-canon four.
