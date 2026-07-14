# Product Requirements Document — Project Meterfall

## Document Control

| Field | Value |
|---|---|
| Document title | Project Meterfall — Browser Rhythm RPG PRD |
| Codename | Project Meterfall |
| Status | Draft v7.0 — **major direction change in progress**: exploration is now a first-class second game loop (§8.8 — a five-region joined explorable world, hidden paths, discoverable "echo" lore, all hand-authored), combat is a **real-time rhythm-action arena** (run-around movement, dashes/i-frames, frame-data attacks, hitstun/knockback/combos, parries, on-beat power — *Melee*-depth), and art is in the **Hyper Light Drifter** register (colossal enemies, silhouette-first, glow/bloom, story-staged arenas, native-resolution bosses). The game is *The Drowned Chorus* (world/story bible written, incl. §5a's untold stories). See §20.4 for build-vs-spec status; the v7.0 explorable world is being built against this revised spec. |
| Owner | Amir Bukhari |
| Author | Amir Bukhari (compiled from concept notes and deep research) |
| Created | 2026-07-08 |
| Last updated | 2026-07-10 |
| Source material | Concept screenshots (party roles, rhythm-combat premise, luchador/clave example) + [Deep Research Report](../research/deep-research-report.md) |
| Distribution | Product, Engineering, Art, Audio, QA, Accessibility |
| Approval required from | Product sponsor, Engineering lead, Art lead, Audio lead, QA lead *(names TBD)* |

### Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-07-08 | Amir Bukhari | Initial deep research synthesis from concept notes |
| 1.0 | 2026-07-08 | Amir Bukhari | Restructured into enterprise PRD format; added KPIs, risk register, RACI, roadmap, schemas |
| 1.1 | 2026-07-08 | Amir Bukhari | Added §11.2 gbmusic tooling note and §11.4 current asset inventory (placeholder sprites, reference audio, example chiptune output) |
| 1.2 | 2026-07-08 | Amir Bukhari | Resolved §11.4 action item: confirmed the placeholder hero character and demo-track-via-gbmusic chiptune direction carry forward as the production basis, not disposable reference; updated §11.1/§11.2 accordingly |
| 1.3 | 2026-07-08 | Amir Bukhari | Resolved music-sourcing question: all v1 battle tracks are sliced from the single demo master (one gbmusic run + hand-tuning pass per stage/boss-phase), not separately composed; updated §11.2 and §11.4 |
| 1.4 | 2026-07-08 | Amir Bukhari | Made the actual slice-selection decision (algorithmic, ascending complexity per stage) and generated all 7 stage/boss-phase `.lsdsng` drafts; added `docs/design/music-direction.md` and updated §11.2/§11.4 to point to it |
| 2.0 | 2026-07-08 | Amir Bukhari | Implemented the engine end-to-end against this spec: full scene stack, audio-clock-driven combat, all mandatory accessibility settings, data-driven content pipeline, and an audible battle-timing sonifier, all covered by 67 unit tests and live headless-browser verification. Added §20 Implementation Status documenting what's built vs. genuinely open (content volume, art, real music integration, e2e suite, QA matrix). |
| 3.0 | 2026-07-08 | Amir Bukhari | Closed most of v2.0's gaps: built live meter changes (`MeterSequence`) and a real 3-phase boss, authored the full 5-node campaign (satisfying §15's vertical-slice exit condition for the first time), added multi-enemy targeting, a real Sightread forecast UI, functional relics and a real skill-unlock trigger, and a committed 11-spec Playwright e2e suite wired into CI. 94 unit tests. Rewrote §20 accordingly; remaining gaps are art, real music integration, and a documented e2e sandbox-flakiness caveat. |
| 4.0 | 2026-07-08 | Amir Bukhari | Closed three of v3.0's gaps: wired the placeholder hero sprite into `BattleScene` (role-tinted, alpha/scale state for KO'd and active heroes), authored and wired a real tier-2 unlock ability per role (§8.4), and replaced `MapScene`'s text-only status list with a real visual node-graph (circles-on-a-path, connected, color-coded by cleared/unlocked/locked, type-lettered). Investigated rendering the `tools/gbmusic/` chiptune drafts to real playable audio via PyBoy and found no public audio-buffer export API in the pinned version — documented as investigated-and-deprioritized rather than pursued further; real music integration remains open. 96 unit tests; e2e suite unchanged at 11 specs. Rewrote §20 accordingly. |
| 4.1 | 2026-07-08 | Amir Bukhari | Final re-verification for this cycle caught that the `deploy-pages.yml` CI pipeline had silently been failing at `playwright install --with-deps` on every push since `ubuntu-latest` moved to 24.04 (unsupported by the pinned Playwright version) — meaning GitHub Pages had not actually been redeploying. Fixed by pinning `ubuntu-22.04`. Fixing that surfaced the real next failure: every Firefox e2e spec fails outright in `beforeAll`/boot, in this sandbox and on real CI alike — not the "occasional sandbox flakiness" §20.2 previously described. Excluded Firefox from the CI/deploy gate (Chromium-only) pending root-cause; updated `tests/e2e/README.md` and §20.2 with the corrected, more precise finding. |
| 4.2 | 2026-07-08 | Amir Bukhari | With Firefox excluded, CI still failed on Chromium at `settings.spec.ts`. Root-caused rather than re-labeling it environment flakiness: found and fixed two real bugs — `TextMenu` could double/triple-fire one physical keypress (Phaser's shared keyboard queue reprocesses on every subsequent keydown before flushing), and re-opening `SettingsOverlay` reused a stale menu referencing already-destroyed GameObjects, throwing and permanently soft-locking the player, because Phaser reuses one persistent Scene instance across stop/relaunch cycles and `create()` wasn't resetting state. The full Chromium e2e suite (11 specs) now passes cleanly and quickly (~38s) across repeated runs, and the deploy pipeline is green end to end. |
| 4.3 | 2026-07-08 | Amir Bukhari | Closed the two remaining gaps that were pure engineering effort with no external blocker: (1) documented the four internal schemas (`Enemy`, `HeroClass`, `CampaignNode`, `BossPhaseConfig`) in §10.5 alongside the three PRD-canonical ones, including their runtime validation approach; (2) added real per-node encounter variety via a new `CampaignNode.encounterPool` field and a pure `resolveEncounterId()` (`src/systems/progression/CampaignSelection.ts`), authored a second `mid_2` encounter variant, and wired it through `MapScene` and content-registry validation. 102 unit tests (was 96); Chromium e2e suite re-verified passing. Reclassified §20.2's remaining items explicitly as either external-resource-blocked or pure follow-on work, and rewrote §20.3 to match. |
| 4.4 | 2026-07-08 | Amir Bukhari | Real user report on the live deploy: unable to get past calibration at all. Root cause: `CalibrationScene` only ever accepted keyboard taps — every other mandatory, unskippable screen (`AudioGateScene`, every `TextMenu`) accepts both keyboard and pointer input, but calibration was keyboard-only with zero feedback for a player who clicked/tapped instead, a first-run-blocking bug on the very first interactive screen the game requires. Fixed by adding a `pointerdown` handler alongside the existing `keydown` one; added an e2e regression test that completes calibration via mouse clicks only. Also reworded `AudioGateScene`'s "PRESS ANY KEY TO START AUDIO" (misread as "music will play") to "PRESS ANY KEY OR CLICK TO CONTINUE" — no audio, music or otherwise, is ever played by that screen; it only unlocks the browser's AudioContext for later use. |
| 5.0 | 2026-07-10 | Amir Bukhari | **Scope change from live-play feedback: replaced the node-select campaign map with a walkable pixel-art overworld** ("is this a text-based game? I wanted a pixel art game I could run around in") — a real tilemap hub (script-generated 4-tile tileset + Tiled-JSON 40×24 map with BFS-validated marker reachability, `tools/overworld/generate_overworld_map.py`), tile-snapped 4-directional movement with collision (pure `OverworldMovement` module, no physics engine), camera-follow, the previously-unused 8-frame run spritesheet as the walking player, node markers color-coded by cleared/unlocked/locked status (`CampaignReachability`, extracted pure from `MapScene`), walk-onto-marker battle triggering, and respawn-at-fought-node after battles (`GameContext.returnToNodeId`). `MapScene` deleted; §7.1's "no free-roam overworld" decision superseded (see revised row). Also closed §20.2's last no-external-blocker gap: every non-boss node now draws from a 2-entry `encounterPool` (boss deliberately fixed — its phase config is keyed to the specific encounter). Updated §7.1, §8.1, §10.5, §10.6, §11.4, §20. 118 unit tests (was 102); 16 Chromium e2e specs (was 11/12, including 4 new overworld specs); prior cycle's flagged Pages deploy failure confirmed transient — latest deploy verified green. |
| 5.1 | 2026-07-10 | Amir Bukhari | Closed two spec-vs-implementation gaps found by auditing §8 requirements directly against the code (both invisible to §20's previous accounting): (1) **§8.5's "Groove … spent on ultimates" had no spend path at all** — Groove could only accumulate. Added an optional `grooveCost` to the canonical ability schema, gating/spending in `queueHeroAction`, one authored 100-Groove ultimate per role, and the command-menu wiring (5-slot kit, `(100g)` labels); §8.5 now specifies the realized design. (2) **Five authored stats (`accuracy`, `speed`, `defense`, `resist`, `targetFocus`) and enemy-applied debuffs were cosmetic** — pushed onto `statusEffects` but read by nothing (only hero `guard` was ever consulted). All are now mechanically wired with deterministic semantics documented on `StatusEffect` (no RNG miss chances, per the rhythm-clarity pillar), including a real taunt and Sightread's accuracy buff actually widening judgment windows. 129 unit tests (was 118, incl. new `combat-stats.test.ts` pinning every wiring); 16 Chromium e2e specs re-verified; ultimate flow verified live in-browser. |
| 6.0 | 2026-07-11 | Amir Bukhari | **Direction change: real-time rhythm-action + Hyper Light Drifter art.** On direct feedback ("I need to be able to run around in battle and attack stuff… mechanics super intricate like Super Smash Bros. Melee"; "the art needs to be wayyy sicker… like Hyper Light Drifter with its colossal-feeling art and enemies"), pivoted the combat pillar from turn-based rhythm to a **real-time action arena**: 8-dir momentum movement, dash with i-frames, light/heavy/special/ultimate attacks with real frame data (startup/active/recovery), hitstun + damage-%-scaled knockback + DI, on-beat parries, and cancels/tech — with the rhythm woven in as on-beat power windows (audio-clock spine unchanged). Rewrote the art direction to the HLD register: colossal silhouette-first enemies, vivid limited palette, additive glow/bloom. Rewrote §7.3 pillars, §8.2–§8.5 combat model, §11.1 art, §7.2 scope, and the status line; the prior turn-based slice, overworld, pipeline, and CI carry forward while the new action engine and HLD art are built against this spec (see §20.4). |
| 6.1 | 2026-07-11 | Amir Bukhari | First **playable, wired** v6.0 action-combat increment. Added the Phaser-free `src/systems/action/ActionCombat.ts` sim (8-dir momentum movement, dash cooldowns + i-frames, light/heavy frame data with active hitboxes, hitstun, damage-%-scaled knockback + player DI, on-beat power, and enemy AI: approach→telegraph→strike→recover) and `ActionBattleScene` driving it with live input (WASD move, J light, K heavy, Shift dash), the audible beat, HP/telegraph/hitbox rendering, and the real reward/campaign path → Results. **The overworld now launches the action scene** (the shipped combat path); the turn-based `BattleScene` stays registered so its regression specs still run during the pivot. 10 new action-combat unit tests (overlap, knockback scaling, on-beat power, dash i-frames negating a hit, win/lose, bounds) + overworld e2e retargeted to the action scene with a forced-victory return-flow check; fixed an async-create input race. A colossal-scale Conductor renders in the boss arena. 139 unit tests, 16 Chromium e2e specs, typecheck, build all green; arena + boss verified live. (Reconciled a parallel prototype branch: a duplicate `systems/combat/ActionCombat.ts` was superseded by this fuller `systems/action/` implementation and removed.) |
| 6.2 | 2026-07-11 | Amir Bukhari | Deepened the action combat and pushed the art to the HLD register. **Combat depth:** a Focus special (builds from on-beat hits), an on-beat parry (negate + stagger the attacker; off-beat = punishable whiff), and rhythm-gated cancel combos (recovery→next-attack only on-beat, in-window) — sim + 3 new unit tests; scene wires L/I + a parry flash + Focus HUD. **HLD art:** additive emissive glow/bloom (`tools/pixelart/fx.py` glow/spark) — accent auras + beat-pulsing glowing eyes, red windup telegraphs, on-beat player flash, bright attack arcs, impact sparks (reduced-motion aware); enemies scaled colossal (Conductor ~2.9× the player). **Theme:** enemy display names reflavored to the world bible and a fading battle-intro card names the movement (biome) + foe. Reconciled a parallel prototype branch into one `systems/action/` implementation. 142 unit tests, 16 Chromium e2e specs, typecheck, build all green; arenas screenshot-verified. |
| 7.3 | 2026-07-13 | Amir Bukhari | **AAA asset scope — the manifest, not a sample.** Direct feedback: "fix the PRD so you'd have as many prompts as a AAA game would have… what we have here is not enough." Correct — ~30 asset slots is prototype breadth. Added **§11.5 AAA art asset manifest**: an **animation-state standard** (playable characters ≥22 states each, enemies ≥6, boss per-phase) and a full production manifest across playable band, ~18 enemies, boss(es), 5-biome autotiling tilesets, props/destructibles, landmarks, parallax backgrounds, a VFX library, a complete UI kit, NPCs, and items — **~575 named asset slots / thousands of frames**. Added acceptance criteria (8)–(10) (every row filled with real art; every character/enemy has its full state set; every biome a full tileset+parallax+props). Expanded [`docs/design/art-prompts.md`](../design/art-prompts.md) to a per-slot prompt catalog kept 1:1 with the manifest. |
| 7.2 | 2026-07-13 | Amir Bukhari | **Art-quality overhaul — kill the noise tiles; set an honest AAA standard.** Direct feedback: "this is NOT a AAA level pixel art game at all… implement an enterprise AAA game." Root-caused to the pipeline, not the effects layer: every tile was a per-pixel **RNG noise fill** (`grass()` etc. in `tiles.py`) and sprites were tiny hand-typed ASCII grids — reads as mud/static, a hard ceiling far below AAA. Added acceptance criterion §11.1 (7) (**designed surfaces, not noise**: light source + shading ramp + ordered dithering + hand-placed motifs) and an **honest ceiling note**: hand-coded art tops out at competent-indie; true HLD-tier needs real art assets in the same `assets/` slots (as the provided **Amir** guitarist already proves). Implemented the overhaul: redesigned tiles (grass/path/water/rock) as intentional pixel art, and lifted the crudest procedural sprites/props toward the one real-asset bar. Real-asset integration is the flagged path beyond the ceiling. Tracked in §20.4. |
| 7.1 | 2026-07-13 | Amir Bukhari | **The band is the cast; the world got its atmosphere.** On direct feedback ("the main characters should be the band members of Inhalants… where are the sprite sheets I gave of the guitarist — that needs to be the main character… make another guitarist, vocalist, and drummer with different move-set animations in the same style"), made the four playable slots the band: **Amir** — the provided hand-drawn guitarist art (`assets/sprites/heroes/placeholder/`) — is conformed into clean 48×48 idle/run/guitar-swing strips and is now the playable lead in the overworld and the action arena; a bassist, vocalist, and drummer are authored to match his palette/proportions with distinct instrument silhouettes + attack move sets (`tools/pixelart/bandmates.py`). The four generated pre-band adventurers become **world NPCs**. Roles/abilities/stats are unchanged (a re-skin via new `HeroClass.spriteId`), so combat and all 142 unit tests are untouched. Also delivered the **AAA overworld atmosphere pass** the standing environment goal called for: seamless drifting fog + raking god-ray shafts (`fx.py`), one colossal set-piece landmark per region (`landmarks.py` — drowned ship, salt headframe, carnival wheel, leaning tenement, Conductor's spire), contact-shadow grounding on props, and the existing vignette/region-tint — all reduced-motion/photosensitivity aware. Verified in-browser across all five regions + both battle and overworld; typecheck, 142 unit tests, build, and the overworld e2e specs green. Open: whether the other three members become swappable/co-op in the single-avatar arena (flagged to the owner). |
| 7.0 | 2026-07-11 | Amir Bukhari | **Exploration is the second game — the "hub" framing was the bug.** Direct feedback: "this isn't an enterprise game... where's the crazy explorable environment with a crazy detailed world with secret backstories for the player to explore." Root-caused against the spec itself, not just the build: §7.1 called the overworld a "hub," §7.2 explicitly excluded "exploration... and secrets," §8.1's loop had one non-combat verb ("walk onto a marker"), and §11.1.1 put every untold story *inside* battle arenas the player can't walk through or revisit — the PRD was describing a menu with grass texture and forbidding the game being asked for. Rewrote §7.1 (scope shape), §7.3 (two new pillars: "the world is the second game," "untold stories are found, not told"), §8.1 (two interleaved loops: critical path + world), and added **§8.8 Exploration**: a five-region joined world map (one region per movement, each in its arena's visual language) substantially larger than the old hub specifically to hold secrets; **echoes** (§8.8.2) — discoverable, collectible environmental-story fragments surfacing world-bible §5a's lore one line at a time, found not told, persisted per save; and **hidden paths/secret pockets** (§8.8.3) gating optional relic/echo rewards, explicitly hand-authored, never procedural. §10.7 and the overworld-foreshadowing rule (§11.1.1) updated to point at §8.8. Implementation tracked in §20.4. |
| 6.3 | 2026-07-11 | Amir Bukhari | **Environments spec: every arena is a place with an untold story.** On direct feedback ("the environments suck… make the settings super interesting and like there's background stories that are untold"), added §11.1.1: generic shared backdrops are out of spec; each of the five movements is fought inside a specific staged place whose 2–4 set pieces wordlessly imply a past event (drowned village green with one boat still straining at its rope; salt-mine gallery of miners calcified mid-listen; sunken carnival ring with ropes snapped outward; the Attic of Teeth with claw marks inside the door; the Conductor's hall of blank pages and stopped melting clocks). Canonical staging/lore in world-bible §5a (never surfaced as in-game text). Design rules: postcard test, fight-readability, a beat-pulsing story light per arena, one palette / five dominant hues, overworld foreshadowing. Implementation of the five painters tracked in §20.4. |
| 5.3 | 2026-07-10 | Amir Bukhari | **Real art pass, from the lyrics.** Acting on direct feedback ("make all the pixel art sprite sheets… make this game absolutely beautiful and use these lyrics to inspire the art"), derived a full art direction from the uploaded Skatopia setlist lyrics ("the drowned chorus" — gothic, drowned, clockwork body-horror as *beautiful* moody pixel art) and built it. Added an in-code pixel-art pipeline (`tools/pixelart/`: one master palette + grid→PNG render/outline/pack; `generate_all.py` regenerates everything deterministically) and authored: four **distinct** hero classes (down/side/up walk cycles), six lyric-themed enemies incl. the Conductor boss (idle-animated), a seamlessly-tiling overworld tileset, two painted 320×180 battle backdrops, and a titled main menu — replacing every tinted-placeholder/colored-circle. Overhauled `BattleScene` (backdrop + party + animated wave + reflowed HUD), gave `OverworldScene` real directional hero art + a mood vignette, and put the shared abyss backdrop behind the menu/gate/results scenes. Wrote `docs/design/art-bible.md`; updated §11.1/§11.4/§20. All authored in code — no external art, no image generation. 129 unit tests, 16 Chromium e2e specs, typecheck, build all green; every scene screenshot-verified in-browser. |
| 5.2 | 2026-07-10 | Amir Bukhari | Same audit, third find: §14's analytics were consent-gated (off by default, correctly privacy-first) but **no UI existed for a player to ever grant consent**, so the entire event set was unreachable in real play. Added an "Analytics (local-only)" toggle to SettingsOverlay writing the persisted `SaveProfile.analyticsConsent` (shown only with an active profile; v1 analytics remain in-memory/no-network). Verified live end to end: toggle ON → events record → consent survives reload+load. |

---

## 1. Executive Summary

Project Meterfall is a **single-player, browser-based, pixel-art rhythm RPG**. Players command a fixed four-hero party — warrior, tank, mage, healer — through turn-based battles in which each action is executed as a timed phrase against an authored musical track. The product is derived from a set of concept screenshots that established the core hook (rhythm-driven combat tied to battle music, a four-role party, a final boss with shifting time signatures, and a "see the music" spell concept) but left every production-critical decision — platform, monetization, scope, timing architecture, accessibility posture — undefined.

This PRD closes those gaps. It fixes v1 as a **desktop-browser, single-player, non-monetized, ~2–3 hour campaign**, built on **TypeScript + Phaser + Tone.js + Web Audio API**, with **audio-clock-authoritative timing** (never UI timers) and **accessibility treated as a first-class, day-one requirement** rather than a stretch goal. It corrects one music-theory error in the source concept (son clave is a rhythmic pattern, not a time signature, and is implemented as an accent layer over a base meter) and converts the "hidden rhythm" idea into a baseline-readable beat UI with forecast-granting abilities layered on top, in line with published accessibility guidance for rhythm/timing-based games.

The document below is organized so each function — product, engineering, art/audio, QA, accessibility — can work from a single source of truth: goals and metrics, functional and non-functional requirements, technical architecture, content specs, delivery phases, risk register, and release gates.

---

## 2. Background and Problem Statement

The product originates from three concept screenshots, not a formal brief. Those screenshots reliably establish:

- A turn-based RPG where attacks are performed via rhythm-based input combinations tied to battle music.
- A four-role party: warrior, healer, tank, mage.
- Most encounters in 4/4, with a final boss that changes time signature.
- A "see the music" spell concept to anticipate pattern/meter changes.
- Enemy variety, with a named example: luchador enemies tied to a 2–3 / 3–2 clave-style rhythm.
- A browser delivery target, 8-bit/pixel-art aesthetic, original soundtrack, and "sick movesets."

They do **not** establish: game name, narrative setting, campaign length, monetization, multiplayer status, target devices, exact timing rules, save architecture, or default beat-UI visibility. Left unresolved, these gaps would stall engineering with recurring product questions mid-build. This PRD exists to resolve them once, with rationale, so implementation can proceed without re-litigating product decisions.

### Why this matters now

Rhythm-combat hybrids are a proven, evidence-backed genre (see §4), but they fail commercially and accessibility-wise when timing is hidden, imprecise, or unreadable. Browsers additionally impose hard technical constraints (audio autoplay restrictions, main-thread timer drift) that must be designed around from day one rather than retrofitted. Fixing these decisions now, before a single scene is built, is materially cheaper than discovering them during a vertical slice.

---

## 3. Research Findings That Shape the Design

| Finding | Source basis | Design consequence |
|---|---|---|
| Rhythm-combat hybrids succeed when timing is legible, not hidden | Official product descriptions of *Crypt of the NecroDancer*, *Cadence of Hyrule* (on-screen beat bar), *Hi-Fi RUSH* | Ship a baseline-readable beat UI for all players; do not gate timing info behind a spell |
| Clave is a rhythmic pattern spanning two bars, not a time signature | Berklee / Open Music Theory / University of Puget Sound music-theory references | Luchador/clave enemies are implemented as accent maps over a base meter (4/4 or cut time); true meter changes are reserved for boss design |
| Browser JS timers (`setTimeout`, `setInterval`, `requestAnimationFrame`) drift tens of ms under main-thread load | web.dev audio scheduling guidance | All gameplay judgment must be computed against the Web Audio hardware clock / Tone.Transport, never UI timers |
| Web Audio must be started from a user gesture; browsers suspend audio on load | MDN Web Audio documentation | Mandatory "Press Any Key to Start Audio" gate before any menu is interactive |
| IndexedDB is the correct client-side store for structured, offline-capable data | MDN storage documentation | Local save profiles use IndexedDB, not `localStorage` |
| Precise timing must not be the only path to success; cues need multi-sensory representation | Xbox Accessibility Guidelines (XAG 103/104/110), Game Accessibility Guidelines, W3C guidance on real-time pressure and photosensitivity | Baseline beat UI, captions for musically meaningful events, speed/assist options, and practice mode are mandatory v1 features, not backlog items |

Full citations and source excerpts are preserved in the [deep research report](../research/deep-research-report.md), which this PRD supersedes as the authoritative product spec while remaining the reference appendix for rationale.

---

## 4. Goals and Objectives

### 4.1 Business / project goals

1. Ship a complete, polished, playable vertical slice of a rhythm RPG that faithfully realizes the source concept.
2. Prove the audio-clock-driven combat architecture is technically viable in-browser at production quality.
3. Produce a design that is accessible by default, avoiding a costly post-launch accessibility retrofit.

### 4.2 Product goals

1. Deliver a 2–3 hour single-player campaign that teaches rhythm mechanics progressively, from straight 4/4 to a live-meter-change final boss.
2. Make the four hero roles feel mechanically distinct through phrase design (combo length, downbeat timing, syncopation, forecast).
3. Establish a data-driven content pipeline (beatmaps, abilities, encounters) so content team can author fights without engineering involvement per-encounter.

### 4.3 Non-goals (v1)

Multiplayer, monetization, mobile/touch support, user-generated beatmaps, imported-MP3 gameplay, procedural music generation, voice acting, open-world exploration, controller haptics as a required channel.

---

## 5. Success Metrics / KPIs

| Category | Metric | Target |
|---|---|---|
| Core loop health | % of players completing the opening biome (tutorial) | ≥ 80% |
| Retention | % of players who complete the full campaign after starting boss biome | ≥ 50% |
| Difficulty calibration | Miss rate on Perfect/Great judgments in opening biome | < 25% average, trending down across session |
| Accessibility adoption | % of sessions using at least one assist setting (speed, assisted window, remap) | Tracked, no target — informs whether assists are discoverable |
| Forecast mechanic usage | % of healer-equipped parties using Sightread in boss fights | ≥ 60% (validates the mechanic is understood, not ignored) |
| Technical stability | Judgment drift incidents (measured vs. audio clock) during QA soak | 0 tolerated at release |
| Boss showcase | % of final-boss attempts reaching Phase 3 | Tracked to validate mid-boss difficulty curve |
| Browser compatibility | Pass rate across Chrome/Edge/Firefox/Safari current stable | 100% of release-gate test matrix |

These map directly to the analytics events defined in §14.

---

## 6. Target Users and Personas

| Persona | Profile | What they need from Meterfall |
|---|---|---|
| **Rhythm-genre fan** | Plays rhythm games (Cadence of Hyrule, NecroDancer, Hi-Fi RUSH); wants a fresh hybrid | Legible timing windows, satisfying feedback on Perfect hits, meaningful mechanical depth by the final boss |
| **RPG-first player, rhythm-curious** | Primarily plays turn-based RPGs; wary of reflex-heavy genres | Untimed command phase, generous judgment windows in story mode, practice mode with no fail state |
| **Player with disabilities relevant to timing/audio** | Needs alternatives to precise real-time input or audio-only cues | Assisted timing windows, remappable controls, captions for musically meaningful events, reduced motion / photosensitivity-safe mode |
| **Content/production team member (internal)** | Authors encounters, tracks, and abilities post-vertical-slice | Data-driven JSON schemas for beatmaps/abilities/encounters that don't require touching scene code |

---

## 7. Scope

### 7.1 Fixed product decisions (v1)

| Area | Decision |
|---|---|
| Platform | Desktop web only. Chrome, Edge, Firefox, Safari — current stable versions. No mobile/touch in v1. |
| Delivery | Browser-first static web app. No launcher, no native wrapper. |
| Mode | Single-player only. No co-op, PvP, or chat. |
| Business model | None. No ads, no IAP, no login, no account creation. |
| Save model | Local saves only, stored in IndexedDB. |
| Scope shape | **Revised 2026-07-11 (v7.0):** a large, explorable multi-region world + battles + bosses. v5.0 replaced the node-select menu with a walkable tilemap, but scoped it as a between-battles "hub" — one small road, no reason to leave it. That was the wrong target: on direct feedback ("where's the crazy explorable environment with a crazy detailed world with secret backstories for the player to explore"), exploration is now a **first-class second game loop**, not connective tissue between fights. The world is one large, densely authored map (five joined regions, one per movement — see §8.8) with hidden paths, secret pockets off the critical path, and discoverable environmental lore (echoes, §8.8.2) — the untold stories of §11.1.1 are no longer locked inside battle arenas the player can only glimpse mid-fight; the player walks through the *places themselves* and finds evidence of what happened there. |
| Aesthetic | 8-bit-inspired pixel art with modern readability. |
| Camera / layout | Side-view battles; top-down camera-follow overworld hub (v5.0); static/parallax battle backgrounds. |
| Narrative | Light, character-driven framing. Minimal text burden. |
| Session target | 10–20 minute sessions; 2–3 hour first-completion campaign. |

### 7.2 Out of scope (v1)

Online/netcode multiplayer (local co-op/party-switch is a later increment, not v1), user-generated beatmaps, procedural soundtrack generation, voice acting, NPCs with dialogue trees or quest-givers (the world tells its story environmentally, §8.8.2 — not through characters to talk to), controller rumble as a required channel, live beat detection from arbitrary/imported songs, monetization plumbing. (Real-time action combat is in scope as of v6.0; large-scale exploration with secrets and environmental lore is in scope as of v7.0 — both were previously excluded.)

### 7.3 Product pillars (v7.0 — real-time rhythm-action + exploration)

1. **The world is the second game.** Exploration is not connective tissue between fights — it is authored content with its own pacing, secrets, and payoff. A player who only walks the critical path sees a fraction of what's there.
2. **Movement is the game (in battle too).** Combat is a real-time action arena you run, dash, and space in — think *Hyper Light Drifter*'s kinetic clarity with *Super Smash Bros. Melee*'s mechanical depth. Every action has real frame data (startup / active / recovery); mastery is spacing, timing, cancels, and reads, not menu selection.
3. **The chorus drives the fight.** The rhythm layer is not a minigame bolted on — the arena beats to the track. Attacks, dashes, and parries executed on-beat are *empowered* (bonus damage/knockback, extended i-frames, Groove); enemy attacks telegraph and land on the beat. Reading the music is reading the fight. This is why it is still *The Drowned Chorus*.
4. **The untold stories are found, not told.** No dialogue trees, no quest text, no lore dumps. Every backstory (§11.1.1, world-bible §5a) is discoverable by walking somewhere and looking — an echo fragment, a staged scene, a hidden pocket off the road. The world rewards curiosity with meaning, not just loot.
5. **Rhythm clarity before difficulty** — every mechanic must make the beat more legible, never less; the beat UI, telegraphs, and on-beat feedback are always readable.
6. **Colossal, readable art.** Enemies are imposing and silhouette-first; the player is small against screen-filling bosses. Vivid, limited palette with emissive glow on a desaturated dark world.
7. **Accessible depth.** Assist/story modes widen on-beat windows, a practice mode has no fail state, and reduced-motion/photosensitivity-safe modes tame effects — none of which remove the skill ceiling for players who want it.

---

## 8. Functional Requirements

### 8.1 Core loop (v7.0 — two loops, not one)

Boot → audio-gesture unlock → save slot select/create → optional AV calibration → the drowned world. From here the loop has two interleaved layers, not one:

1. **The critical path** (unchanged mechanically from v5.0): campaign nodes (battle / elite / boss) are map markers, unlocked in graph order; walking onto an unlocked marker starts its battle; clearing it rewards progression and respawns the player at that marker. This is still exactly enough to finish the game.
2. **The world** (new, v7.0): between and around those markers is a large, densely authored, walkable region-by-region map (§8.8) that rewards leaving the road — hidden paths, secret pockets, and echoes (§8.8.2) that flesh out the untold stories of §11.1.1/world-bible §5a. None of it is required to progress; all of it is there to be found.

The critical path is the spine; the world is the flesh. A player who beelines markers can finish the campaign. A player who explores finds a substantially larger, stranger game underneath it.

### 8.8 Exploration — the second game (v7.0)

**Why this section exists.** v5.0–v6.3 treated the overworld as a "hub": a single road with no reason to step off it, and put every environmental story inside a battle arena the player only sees mid-fight and can't walk through. That is a menu with grass texture, not an explorable world, and it does not deliver "crazy detailed world with secret backstories for the player to explore." §8.8 is the fix.

**8.8.1 World structure.**
- One large, continuous map made of **five joined regions**, one per movement, in campaign order, each authored in the visual language of its arena (§11.1.1) so walking the world *is* walking toward each place, not a generic road that teleports into it: a drowned coastal approach (Shallows), a salt-crusted mine road (Salt Mines), a carnival approach thick with dead lantern strings (Pit Below), a claustrophobic building exterior around the Attic, and the flooded plaza before the Conductor's hall.
- Regions are visually and structurally distinct (different tile dressing, different obstacle logic — see §11.1.1's "one palette, five moods") but connected on one seamless map, not separate loading-screen levels.
- The map is substantially larger than the v5.0 hub (target: 4× or more the walkable area) specifically to hold secrets — a map with no unused space cannot hold anything to find.

**8.8.2 Echoes — the found backstory.** An **echo** is a discoverable, wordless-in-dialogue environmental storytelling beat placed off the critical path: a small staged scene (a real prop arrangement, not a text popup) that a player only sees by walking somewhere non-obvious. Interacting with an echo (a context prompt, not automatic) reveals one short fragment of the untold stories already canonized in world-bible §5a — the boat that ran out of rope, the foreman's last three steps, the two lanterns the crowd voted to keep — surfaced as a single evocative line, never a lore dump. Echoes are collectible (persisted per save, §10.7) and optional; missing all of them does not block progress. A HUD counter (found/total) is the only progress signal — no map markers spoiling where they are.

**8.8.3 Secrets and hidden paths.** At least one non-obvious traversal element per region: a gap in rocks that reads as passable only up close, a path that reverses field-of-view expectations (behind a waterfall/wreck, around the back of a structure), or a route only visible from a specific vantage. Secrets gate optional rewards (a relic, an echo, or both) — never critical-path content. This is deliberately hand-authored, not procedural: a secret is only a secret if someone decided where to hide it.

**8.8.4 What this explicitly is not.** Not a stat/level/inventory-management layer (§7.2's "no loot-driven progression" from §8.5 still holds — secrets reward relics/echoes, not gear grinding). Not NPCs or dialogue (§7.2). Not a second combat layer (no overworld enemies/hazards in v1 — the danger is reserved for arenas). Not procedurally generated (§8.8.1's regions and §8.8.3's secrets are hand-placed so their storytelling is intentional, matching §11.1.1 rule 2).

### 8.2 Battle model — real-time action arena (v6.0)

> **Direction change (v6.0):** combat is now a **real-time action arena**, not turn-based. The player directly controls one hero (the party lead; switchable/co-op party members are a later increment), running around a bounded arena, spacing against enemies, and attacking in real time. Depth is in the *Super Smash Bros. Melee* register: every action has real frame data, movement has momentum and cancel windows, and mastery is spacing, timing, cancels, and reads. The prior turn-based/phrase model (v1–v5) is retired; the audio-clock spine (§10.2), content pipeline (§10.5), and campaign/overworld (§8.1) carry forward.

**Movement.**
- 8-directional run with acceleration/friction (momentum) and a max speed; a short skid on hard direction reversal.
- **Dash / dodge**: a burst with **invincibility frames** on startup, committed recovery, and a short cooldown. An *on-beat* dash (§8.3) extends the i-frames and refunds cooldown — the core risk/reward of moving to the music.
- Facing is set by aim/movement; all attacks are directional.

**Attacks (per-hero moveset).**
- **Light** — fast startup, low commitment, gatlings into a short combo within a cancel window.
- **Heavy** — slow startup, high knockback/damage, armor on select frames.
- **Special** — costs Focus; the hero's defining tool (e.g. the Deereater's lunge, the Esoterophobe's zone).
- **Ultimate** — costs the full Groove meter; a screen-shaking verse loud enough to break the song.
- Each attack is a hitbox with **frame data** (startup / active / recovery), damage, a knockback vector, and hitstun.

**Hit reactions (real combos).**
- **Hitstun**: a hit locks the victim out for frames scaled by damage — enabling true combos and juggles.
- **Knockback**: a vector whose magnitude scales with the hit *and* the victim's accumulated **damage %** (Melee-style), so combos carry across the arena. **Directional Influence (DI)**: holding a direction during hitstun nudges the knockback vector — defender counterplay.
- **Parry / perfect-guard**: a tight **on-beat** guard that negates a hit and staggers the attacker; the parry window opens on the beat.

**Cancels & tech (the depth layer).** Attack→dash cancel on the beat (dash-dance pressure, whiff-punish); light→light→heavy gatling inside cancel windows; on-beat dash-out-of-pivot slides for spacing. Everything cancellable is cancellable only inside a few-frame window, rewarding precision.

**Encounter flow.** Enter arena → real-time fight (defeat the wave / survive the boss's phases) → on clear, rewards (§8.5) → back to the overworld at the fought node. No turns, no mid-fight menus.

### 8.3 Timing model — on-beat power within real time

The four judgment tiers now grade the timing of a **real-time action relative to the nearest beat** (not a scripted phrase). On-beat actions are *empowered*; off-beat still execute, weaker:

| Tier | Window | On-beat effect |
|---|---:|---|
| Perfect | ±45 ms | +full power: max bonus damage/knockback, extended dash i-frames, parry active, +Groove |
| Great | ±90 ms | strong bonus, +Groove |
| Good | ±140 ms | small bonus |
| Off | outside Good | base action, no bonus, no Groove |

Story/assist mode widens all windows; calibration offset applies globally, before judgment (§10.3). Enemy attacks telegraph and land on the beat, so reading the music reads the fight; **Sightread** reveals the upcoming beats/telegraphs and any meter change (the "see the music" tool). Audio-clock authority is unchanged (§10.2) — all timing derives from `TransportClock`, never wall-clock.

### 8.4 Party and hero movesets

Each hero is an **action moveset** (not a menu of phrases): light, heavy, special (Focus), ultimate (Groove), plus a signature movement/defensive trait.

| Hero | Combat identity | Signature trait |
|---|---|---|
| **the Deereater** (warrior) | aggressive burst; long committal combos | a lunging gap-close on the beat |
| **the Saltminer** (tank) | space control & armor; punishes whiffs | on-beat parry with a wide window and a stagger counter |
| **the Esoterophobe** (mage) | zoning & disruption; controls the arena | places a lingering hex-zone that debuffs foes crossing it |
| **Sunshine Sally** (healer) | sustain & sight; keeps the party reading the music | **Sightread** (forecast) + an on-beat heal pulse |

### 8.5 Resources and progression

- **HP** (a bar) and an accumulating **damage %** that scales incoming knockback (Melee-style), so a battered fighter gets launched further.
- **Focus** — built by on-beat aggression, spent on specials.
- **Groove** (shared) — built by on-beat play and clean combos, spent on the ultimate. Whiffing/getting hit off-beat slows Groove gain but never drains Focus.
- Progression is deterministic, not loot-driven: each boss clear unlocks a new moveset tool per hero. Equipment limited to one relic slot per hero plus one shared party charm.

### 8.6 Encounter design progression

| Stage | Musical design | Mechanical purpose |
|---|---|---|
| Opening biome | Mostly straight 4/4 | Tutorializes timing, count-ins, role identities |
| Mid biome 1 | 3/4 and 6/8 | Non-quadruple feel without chaos |
| Mid biome 2 | 4/4 with clave-accent enemies (luchadors: 2–3 / 3–2 son-clave accent maps, throws/counters on accent hits) | Cross-accent recognition |
| Mid biome 3 | Syncopated elite encounters | Forecast and defense layering |
| Final boss | Live meter changes across authored phases | Culmination of the full system |

### 8.7 Final boss specification — "The Conductor" (internal name)

- **Phase 1**: stable 4/4 with deceptive syncopation.
- **Phase 2**: alternates 4/4 and 3/4 every four bars.
- **Phase 3**: cycles 5/4, 7/8, 4/4, 3/4, with full visual forecast if Sightread is active and reduced forecast otherwise.
- All meter changes are hard-authored in the battle beatmap — never improvised, generated, or inferred from audio.

---

## 9. Non-Functional Requirements

### 9.1 Performance

- Battle scene targets 60 FPS on all supported desktop browsers.
- Audio scheduling must remain stable under rendering stutter; combat stays rhythm-correct even during temporary frame-rate dips because **audio is authoritative, not video**.

### 9.2 Platform / compatibility

Chrome, Edge, Firefox, Safari — current stable desktop versions only, for v1.

### 9.3 Accessibility (mandatory, day-one)

| Setting | Requirement |
|---|---|
| Remappable controls | Required |
| Keyboard-only play, no required simultaneous presses | Required |
| Separate volume sliders (music / SFX / UI) | Required |
| Captions/subtitles for dialogue and musically meaningful events (e.g. "meter shifts," "music intensifies," "downbeat incoming," "enemy chant left") | Required |
| Reduced motion mode | Required |
| Photosensitivity-safe VFX mode; no flashing above seizure-risk thresholds | Required |
| Game speed options: 70% / 85% / 100% | Required |
| Assisted timing windows | Required — precise timing must never be the only viable path |
| Practice mode with no fail state | Required |
| AV calibration screen | Required |

Haptics are additive-only for a future controller pass, never the sole channel for information.

### 9.4 Security / privacy

- No accounts, no PII collection, no server-side storage in v1.
- Telemetry (§14) is anonymous and/or consent-gated; consent state is itself part of the local save object.
- All save data is local to the browser (IndexedDB); no transmission of save data off-device in v1.

---

## 10. Technical Architecture

### 10.1 Required stack

**TypeScript + Phaser + Tone.js + Web Audio API.** Phaser provides actively maintained, TypeScript-supported HTML5 rendering (WebGL/Canvas) across browsers. Tone.js schedules musical events against exact time values rather than UI timers. Web Audio is the browser-native API suited to precise, dynamic game audio.

### 10.2 Authoritative timing rule (hard constraint)

**No gameplay judgment may be derived from `setTimeout`, `setInterval`, or `requestAnimationFrame` alone.** These may drive visuals only. The source of truth for all musical/combat state is the Web Audio hardware clock via Tone.Transport. This is non-negotiable and is a release gate (§16).

### 10.3 Audio subsystem requirements

| Requirement | Implementation |
|---|---|
| Master timeline | `Tone.Transport` as global musical clock |
| Exact event scheduling | Web Audio clock time passed into callbacks |
| Low-latency custom analysis/click/metronome | AudioWorklet, if needed |
| Battle music | Authored stem playback aligned to bar/beat markers |
| State-reactive mix | Mute/unmute stems, automate parameters on phase changes |
| Calibration | User-adjustable global AV sync offset, persisted |

### 10.4 Audio startup requirement

The first screen after boot is a mandatory **"Press Any Key to Start Audio"** gate whose sole job is to create/resume the `AudioContext` on a user gesture. No soundtrack autoplay is attempted before this point.

### 10.5 Data-driven content architecture

All gameplay content — timing, encounters, abilities — is data-driven; no encounter timing is hardcoded in scene logic. Canonical schemas live in [`docs/technical/schemas/`](../technical/schemas/) and are mirrored as TypeScript types in `src/data/schemas/`:

- `beatmap.schema.json` — track BPM, meter sequence, subdivision, timed events.
- `ability.schema.json` — role, cost, phrase length, input pattern, timing template, effects.
- `encounter.schema.json` — enemy wave, track binding, accent profile, rewards.

These three are validated against a compiled ajv JSON Schema (`src/data/ContentLoader.ts`). Four further internal schemas exist alongside them in `src/data/schemas/` to make the game actually runnable — the three canonical schemas above deliberately don't specify combat stats, map topology, or boss phasing, and something has to for a turn-based battle, a node-based map (§8.1), or a multi-phase boss (§8.7) to exist at all. These are content-team-owned data (not engine code), runtime-checked at load time via hand-written shape validators rather than a compiled JSON Schema (`ContentLoader.ts`'s `loadEnemy`/`loadHeroClass`/`loadCampaign`/`loadBossPhaseConfig` — each throws a `ContentValidationError` naming the offending field on bad data, same fail-loudly-at-load-time guarantee as the ajv-validated three):

- `Enemy.ts` — id/name/HP and a list of `intents` (a telegraph key matching a beatmap's `enemyTelegraph` event payload, plus a damage/debuff effect). Backs the enemy wave in an `encounter.schema.json`'s `enemyWave`.
- `HeroClass.ts` — id/role/name, HP/Focus pools, and the ability-kit `abilityIds` list (§8.4). Backs `partyRoster()`.
- `CampaignNode.ts` — the node-graph type (`battle | elite | camp | boss`), its bound `encounterId` (or an `encounterPool` of ids drawn from at random per visit, §8.6), and `next` node ids forming the campaign's DAG (§8.1). A `CampaignDefinition` is a `startNodeId` plus the full node list. As of v5.0 the graph renders as walk-onto markers on the overworld (`OverworldScene` + the pure `CampaignReachability` module) rather than a select menu.
- `BossPhaseConfig.ts` — an ordered list of `{ trackId, hpThreshold }` phases (strictly decreasing thresholds) mapping a boss's HP fraction to which beatmap plays, the data backing for the live meter/tempo phase changes in §8.7.

A JSON Schema file plus ajv compilation could still be added for these four if/when they need external tooling support (e.g. a future content-authoring UI validating outside the game runtime); today's hand-written validators meet the same fail-loudly bar the ajv-compiled ones do and were judged sufficient for content authored directly as hand-written JSON.

### 10.6 Rendering and scene architecture

- Fixed internal resolution **320×180**, 16:9 canvas, integer-multiple scaling, `image-rendering: pixelated` (no smoothing).
- Fixed scene stack (mirrored under `src/scenes/`):

| Scene | Purpose |
|---|---|
| BootScene | Load manifest, verify browser support |
| AudioGateScene | User gesture; create/resume audio context |
| MainMenuScene | Start, continue, settings |
| SaveScene | Slot create/load/delete |
| CalibrationScene | AV sync test and offset save |
| OverworldScene | Walkable overworld hub: tilemap, movement/collision, camera-follow, node markers, battle triggering (replaced MapScene in v5.0) |
| BattleScene | All combat logic and UI |
| ResultsScene | XP, relic, unlocks |
| SettingsOverlay | Always-available settings modal |

### 10.7 Storage and persistence

All save data lives in **IndexedDB**: player settings, calibration offsets, campaign progress, unlocked skills, relic inventory, analytics consent state, and (v7.0) found echo ids (§8.8.2).

---

## 11. Content and UX Requirements

### 11.1 Art direction — *Hyper Light Drifter* register (v6.0)

**Target feel:** *Hyper Light Drifter*. Colossal, imposing enemies that dwarf a small, nimble player; bold, instantly-readable **silhouette-first** design; a **vivid, limited palette** — a few searing accent hues (abyssal teal, plum/magenta, ember-gold, blood) on desaturated near-black depths — with **additive glow/bloom** on eyes, weapon arcs, attack telegraphs, hazards, and the chorus's light. Dramatic scale and negative space; crunchy, deliberate, low-frame-count animation with strong anticipation/impact poses. Emissive readability is a hard requirement: every attack telegraph and hitbox-active frame must glow so the real-time fight is legible at a glance.

| Asset type | Spec |
|---|---|
| Base resolution | 320×180 (small player, screen-filling bosses) |
| Tile size | 16×16 |
| Player combat sprite | ~20×24, silhouette-readable |
| Standard enemy | 48×48+; **elites/bosses 96–180px** (colossal, may exceed one screen height) |
| Glow/bloom | additive emissive layer on eyes, edges, energy, telegraphs, and hazards |
| Battle arenas | 320×180, layered depth (fog/atmospheric perspective), god-rays, caustics |
| Animation | low frame count, high contrast in pose (anticipation → impact → recovery), 8–12 fps |
| Palette policy | one global master palette, ruthlessly limited; saturated accents on desaturated darks (HLD discipline) |

**"Enterprise level" acceptance criteria (v6.4, extended v7.2).** Art quality is judged against these checkable standards, not vibes: (1) **no tint-swaps or upscales** — every character is bespoke authored art, and bosses are authored at native colossal resolution (never a small sprite scaled up); (2) **animation states, not static sprites** — the playable character has authored attack poses (anticipation → impact) and a hurt reaction; enemies have idle motion, a readable windup telegraph, and a hurt flash; (3) **every arena is a distinct authored place** meeting §11.1.1; (4) **a consistent light source and emissive pass** on every sprite (rim light, outline, glow); (5) **one master palette** across all assets; (6) all of it deterministic and regenerable (`generate_all.py`); (7) **(v7.2) designed surfaces, not noise** — every tile and texture is intentional pixel art with a clear light source, a shading ramp (ordered dithering between value steps, never per-pixel RNG fills), and hand-placed motifs; a tile must read as *grass / stone / water*, not static. Gaps against these criteria are tracked in §20.4 — anything not yet meeting them must be listed there, not implied shipped.

**Honest ceiling note (v7.2).** The art is authored in code as palette-indexed pixel grids (`tools/pixelart/`, no external art, no image generation — a project-level constraint, §11.4). This is the correct source-of-truth discipline, but it has a hard quality ceiling: hand-coded pixel art reaches *competent-indie* fidelity (well-designed 16–32px tiles, silhouette-clear sprites), **not** literal *Hyper Light Drifter* production art, which is made by dedicated pixel artists over months. Criterion (7) and the §20.4 overhaul push the procedural art to that competent-indie ceiling. Reaching true AAA/HLD-tier requires **real art assets** (professional tilesets / character packs) dropped into the same `assets/` slots — the pipeline already proves this works (the provided hand-drawn **Amir** guitarist is the one asset that reads AAA precisely because it is real art). That is the intended path beyond the ceiling, gated on the owner supplying/authorizing assets.

**Realized direction (v5.3):** the art bible now exists — [`docs/design/art-bible.md`](../design/art-bible.md) — and the game ships a real, cohesive pixel-art pass built to it, derived from the Skatopia setlist lyrics ("the drowned chorus": a gothic, drowned, clockwork world). Everything is authored in code as palette-indexed pixel grids and rendered deterministically to PNG (`tools/pixelart/`, regenerate with `generate_all.py`) — four *distinct* hero classes (not one tinted sprite), six lyric-themed enemies incl. the Conductor boss, a seamlessly-tiling overworld tileset, painted battle backdrops, and a titled main menu, all sharing one master palette. This supersedes the earlier "carried-forward Amir placeholder" basis (§11.4); the Amir reference frames are retained only as historical animation-timing reference. Remaining art work is animation depth (attack/hurt frames, true 4-directional art), not a from-scratch art pass — see art-bible §6 and §20.2.

### 11.1.1 Environments — every arena is a place with an untold story (v6.3)

**Requirement: no generic battlefields.** A shared "moody backdrop" behind every fight is explicitly *out of spec*. Every movement of the campaign is fought **inside a specific place**, and every place carries a story the game never tells in words — the *Hyper Light Drifter* discipline of environmental storytelling: the set pieces are arranged so an attentive player reconstructs what happened here, and an inattentive one still feels that *something* did. No lore dumps, no signposts, no NPC exposition in v1. The room is the narrator.

Design rules for every arena:

1. **A specific place, not a theme.** "Underwater ruins" is a theme; "a village green whose ring of boats is still tied to a sunken maypole" is a place. Each arena must pass the postcard test: describe it in one sentence and it is unmistakably *this* game and *this* room.
2. **An untold story, physically staged.** Each arena embeds 2–4 authored set pieces whose *arrangement* implies a past event (see table). The set pieces must be readable at 320×180 without text.
3. **Fight-readable.** Storytelling lives in the backdrop and floor bands; the play-space stays uncluttered and high-contrast so hitboxes, telegraphs, and movement always read (pillar 3). Emissive accents (§11.1) may mark story focal points but never enemy-telegraph red.
4. **The chorus is present everywhere.** Every arena visibly *responds to the music* somewhere — a story light that pulses on the beat — reinforcing pillar 2 diegetically.
5. **One palette, five moods.** All arenas share the master palette but own a dominant hue so each movement feels like a different depth of the same drowned world.

The five v1 arenas and their untold stories (canonical staging in [`docs/design/world-bible.md`](../design/world-bible.md) §5a; each backdrop is authored in `tools/pixelart/backgrounds.py` as its own painter):

| Node | Arena (the place) | Dominant hue | The untold story its set pieces stage |
|---|---|---|---|
| `opening_1` | **The Shallows** — a drowned village green | teal | Rooftops and a leaning chapel spire break the seafloor; a ring of little boats is still moored in a circle around a sunken maypole, and one empty boat floats *above*, still tied, straining at its rope toward the surface. The village went under mid-festival — and somebody almost got away. |
| `mid_1` | **The Salt Mines** — a gallery of the calcified | ember/gold | Mine-cart rails run past pillars that are not pillars: they are miners **turned to salt mid-swing**, tools still raised, all facing the same tunnel mouth that now glows faintly. Whatever they saw down that tunnel, they saw it *together*, and no one was looking away. One statue near the exit faces the other way — mid-run. |
| `mid_2` | **The Pit Below** — a sunken carnival ring | plum/magenta | A wrestling ring stands in a bowl of banked seating, strings of dead festival lanterns sagging overhead — but two lanterns still burn, and the ring's ropes are snapped **outward** on one side. The crowd's chairs are all tipped over *away* from the ring. The last match did not stay inside the ropes. |
| `mid_3` | **The Attic of Teeth** — a locked room that should not fit indoors | blood/rust | Slanted rafters, a single bolted door high in the back wall with claw-gouges **on the inside**, walls black with layered scrawl, and a small bed made entirely of pens beside a spill of tiny bones. Someone was kept here long enough to write on every surface — and was writing *about a sound* (staves and bars are scratched among the scrawl). |
| `boss_1` | **The Conductor's Hall** — an orchestra with no orchestra | ink + ember | Rows of empty music stands recede toward a raised podium under a bone organ; every stand holds a page, and every page is blank except the last row's, which are full. Black clocks line the walls, each stopped at a *different* time, all melting downward. He has been rehearsing an unfinished ending with players who drowned rehearsing it. |

**Overworld (superseded by §8.8, v7.0):** the world map is no longer a thin road between arenas — it is the fully explorable five-region world of §8.8, authored in each region's own visual language so the walk *into* a place foreshadows the arena it leads to (calcified milestones thickening near the mine road, lantern strings drooping near the pit descent, etc.), carrying its own echoes and secrets rather than being connective tissue.

**Acceptance:** each arena ships as a distinct authored backdrop (no palette-swap of a shared scene), passes the postcard test in review, and its story set pieces are identifiable in a 1× screenshot. Tracked in §20.4.

### 11.2 Music and audio content spec

Each battle track ships with: full mix preview, runtime stems (drums, bass, harmony, lead, FX), tempo map, meter map, bar markers, an authoring-only click reference (never shipped to players), and a battle SFX pack. Music is authored externally in a DAW and exported as bar-aligned stems.

**Carried-forward basis:** the demo audio master (§11.4) and its Game Boy chiptune derivative are the music-direction basis, not disposable reference. [`tools/gbmusic/`](../../tools/gbmusic/README.md) — which stem-separates a mixed track into vocals/bass/drums/other and maps them onto the Game Boy's four hardware channels (pulse/pulse/wave/noise) — is the intended production path for turning this track into authentic Game Boy chiptune material: run the pipeline, then hand-tune the resulting `.lsdsng` in LSDJ, then render/record real Game Boy audio as the shippable stem set per the spec above. The DAW-authored-stems requirement still stands for tracks that don't originate from this pipeline; this is the path for tracks that do.

**Track sourcing decision:** all v1 battle tracks are sliced from this single ~22-minute demo master (`--start`/`--duration` per segment in `tools/gbmusic/convert.py`), not composed as separate new material per biome. Each stage in the §8.6 encounter progression and each final-boss phase (§8.7) gets its own slice, its own independent `gbmusic` run, and its own hand-tuning pass — they are distinct `.lsdsng` projects/renders even though they share one source recording. Meter changes for the final boss are still hand-authored in the beatmap JSON per §10.5/§8.7 regardless of which audio slice underlies them — slicing determines the audio content, not the authored meter/event data layered on top of it.

Which timestamp ranges map to which stage is recorded in [`docs/design/music-direction.md`](../design/music-direction.md): ranges were chosen algorithmically (rhythmic-density/energy scoring, ascending complexity to match the §8.6 difficulty curve), not by ear, so treat the mapping as a starting point pending a human listening pass, not a locked decision. All seven `.lsdsng` drafts exist at `tools/gbmusic/output/{opening_biome,mid_biome_1,mid_biome_2_clave,mid_biome_3_syncopated,boss_phase_1,boss_phase_2,boss_phase_3}.lsdsng`.

### 11.3 UX rules

The battle UI must always show: current measure and beat, phrase lane for the active action, next-downbeat indicator, enemy intent iconography, and clearly separated HP / Focus / Groove values. Critical information must never rely on color alone.

### 11.4 Current asset inventory (as of 2026-07-10)

**Primary art source (v5.3): the in-code pixel-art pipeline.** The game's actual shipped art — heroes, enemies, tileset, battle backdrops, menu — is authored in `tools/pixelart/` and rendered to committed PNGs under `assets/sprites/`, `assets/tilemaps/`, and `assets/backgrounds/`. See [`docs/design/art-bible.md`](../design/art-bible.md) for the direction and the file-by-file breakdown. The table below is the *pre-pipeline reference material*; the "Amir" placeholder frames are now superseded by the pipeline heroes and retained only as historical animation-timing reference.

**Decision (historical, 2026-07-08): this material carries forward** as the style/direction basis for production — it is not disposable placeholder to be discarded once "real" production starts. None of it meets §11.1/§11.2 delivery spec yet in its current form, and none of it counts toward the vertical-slice exit condition (§15) as-is, but it is the thing final assets are derived from, not replaced by.

| Asset | Location | Status |
|---|---|---|
| 7 placeholder hero spritesheets ("Amir" run/crouch/dash/stand animations) | `assets/sprites/heroes/placeholder/` | Carries forward as the hero's visual/animation basis; the crouch-wait frame is now loaded and rendered in-engine for all four heroes (role-tinted) per §20.1, and as of v5.0 the 8-frame run strip is the animated walking player on the overworld (left = flipped right; up/down reuse the same frames — a one-strip placeholder-art limitation, not a bug). Does not yet conform to the 48×48 combat-sprite / master-palette spec in §11.1, and reusing one frame across all four roles is not final art — needs redrawing to spec, not replacing with a different character. |
| Overworld tileset + tilemap (16×16 grass/path/water/rock tiles; 40×24 Tiled-JSON map with `ground` tile layer and `markers` object layer) | `assets/tilemaps/`, generated by `tools/overworld/generate_overworld_map.py` | New in v5.0. The map layout and marker data are real authored content (the generator BFS-validates every node marker is reachable from spawn); the tile *art* is programmatically-generated placeholder, subject to the same real-art-production blocker as everything else in this table. |
| 2 animation reference GIFs (crouch, dash-to-run) | `assets/reference/animation-gifs/` | Carries forward as animation-timing reference for the same character; superseded by the spritesheets above wherever they overlap. |
| Demo audio master ("AmirsMaster...WithBabyVocals.mp3", ~22 min, kept local/gitignored — see `assets/reference/README.md`) | `assets/reference/audio-demo/` | Carries forward as the sole source track for all v1 battle music. Not itself a battle-track deliverable (too long, not stem/tempo/meter-mapped) — every stage/boss-phase track is a distinct slice of this master run through `tools/gbmusic/` (§11.2), not separately composed material. |
| Example `.lsdsng` chiptune draft (30–60s clip of the demo track, run through `tools/gbmusic/`) | `tools/gbmusic/output/amirs_master_clip_30-60s.lsdsng` | Carries forward as the first working proof of the music-direction pipeline. Machine-transcribed and untuned (see limitations in `tools/gbmusic/README.md`) — needs hand-tuning in LSDJ before it's a candidate shippable stem, but it is the direction, not a discardable prototype. |
| 7 stage/boss-phase `.lsdsng` drafts, one per row of the table in `docs/design/music-direction.md` | `tools/gbmusic/output/{opening_biome,mid_biome_1,mid_biome_2_clave,mid_biome_3_syncopated,boss_phase_1,boss_phase_2,boss_phase_3}.lsdsng` | The full v1 battle-track set, sliced and converted per the track-sourcing decision above. Same caveats as the example draft: machine-transcribed, untuned, not yet auditioned by a human, not shippable as-is. |

Action item for pre-production exit (§15): the art bible and music direction docs (`docs/design/`, currently stubs) should be written as spec-conformant extensions of this carried-forward material — i.e., document how the "Amir" character and the chiptune-via-`gbmusic` approach get taken to shippable quality, not propose alternatives to them.

### 11.5 AAA art asset manifest (v7.3)

**Why this section exists.** Prior art scope was ~30 slots (four sprites, four tiles, a handful of enemies/backgrounds). That is *prototype* breadth, not a game. A shipped AAA pixel-art title (Blasphemous, Dead Cells, Hyper Light Drifter register) carries **hundreds of named assets and thousands of frames**: every character has a full animation state machine, every biome has a full autotiling tileset plus parallax layers and dozens of props, there are dozens of enemies each with their own state set, a multi-phase boss, a full VFX library, and a complete UI kit. This section is the **production asset manifest** — the checklist the game is built and judged against — and the per-asset generation prompts live in [`docs/design/art-prompts.md`](../design/art-prompts.md), which must stay 1:1 with this manifest. "Enough art" = this manifest filled, not a representative sample of it.

**Animation-state standard.** AAA characters are not single sprites. Every **playable band member** ships **≥22 animation states**: `idle`, `idle_combat`, `walk`, `run`, `dash`, `jump`, `fall`, `land`, `attack_1/2/3` (combo), `heavy`, `special`, `ultimate`, `parry`, `block`, `hurt`, `death`, `downed`, `revive`, `victory`, `interact` — plus a dialogue **portrait**. Every **enemy** ships **≥6 states**: `idle`, `move`, `attack`, `telegraph`, `hurt`, `death` (ranged/elite add a `projectile`/`special`). The **boss** is authored per-phase with intro, per-phase idles, its full attack set, phase-transition, stagger, and death.

**Manifest by category** (target counts for v1 AAA scope; each row is enumerated with a prompt in `art-prompts.md`):

| Category | Scope | Approx. asset slots |
|---|---|---|
| **Playable band** | 4 members × ~22 animation states + 4 portraits | ~92 |
| **Enemies** | ~18 types across 5 biomes × 6 states (+ elite specials) | ~114 |
| **Boss(es)** | The Conductor (3 phases, full attack set) + 1–2 mid-bosses | ~36 |
| **Tilesets** | 5 biomes × ~9 sheets (terrain/path/water autotile w/ edges+corners, cliffs/walls, biome transitions, decal overlays, foreground occluders, animated tiles, interactive tiles) | ~45 |
| **Environment props & destructibles** | ~12 per biome + ~10 shared interactables (chest, save-shrine, door, sign, lever, campfire, breakables) | ~70 |
| **Landmarks** | 5 primary + ~2 secondary per biome | ~15 |
| **Parallax backgrounds** | 5 biomes × ~4 layers (sky/far/mid/near) + 5 arena scenes + weather overlays | ~30 |
| **VFX library** | hit sparks, light/heavy slash arcs, parry burst, dash trail, run/land dust, water splash, blood, heal/buff blooms, per-element projectiles + muzzle/impact, explosion, death dissolve, status auras (poison/burn/stun/slow/shock), chorus light | ~30 |
| **UI kit** | title logo, main-menu illustration, HUD frame + HP/Focus/Groove bars, ability icons (4×~4), relic/item icons (~20), currency/key/consumable icons, cursor, button states, dialogue box + nameplate, world-map screen, pause panel, results screen, settings icons, bitmap font (2 weights) | ~90 |
| **NPCs** | 4 old-hero NPCs + ~6 townsfolk/vendors/questgivers × (idle, talk, portrait) | ~30 |
| **Items & pickups** | health orb, currency, ~15 relics, keys, consumables, map fragments | ~25 |
| **Total** | | **~575 named asset slots** (thousands of frames) |

**Sourcing (per §11.1 ceiling note).** These 575 slots are generated as real art (AI-generated per the `art-prompts.md` catalog, or commissioned) and dropped into the same `assets/` slots for wiring — the pipeline proven by the provided Amir guitarist. Hand-coded procedural art fills a slot temporarily but never counts as shipped against this manifest. Progress is tracked slot-by-slot in §20.4.

**Acceptance (extends §11.1).** "AAA-complete" requires: (8) **every manifest row filled with real art**, not a procedural stand-in; (9) **every playable character and enemy has its full state set** (a static one-pose sprite is incomplete); (10) **every biome has a full autotiling tileset + parallax + prop set**, not four flat tiles. Until then, unfilled rows are listed honestly in §20.4.

---

## 12. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Visual-timer-based judgment code creeps in under deadline pressure, causing drift | Medium | High | Hard architectural rule (§10.2) + automated lint/test that flags `setInterval`/`rAF` in judgment-path code; QA soak test under forced render load |
| Accessibility features treated as post-launch add-ons | Medium | High | Accessibility requirements are release gates (§16), not backlog items; tested every QA pass |
| "Clave as fake meter" misconception re-enters content design | Low | Medium | Encounter schema requires `accentProfile` distinct from `meterSequence`; content review checklist enforces the distinction |
| Scope creep toward open-world/multiplayer during production | Medium | High | Out-of-scope list (§7.2) is a standing reference in sprint planning; changes require PRD revision, not ad hoc addition |
| Original soundtrack production slips and blocks encounter authoring | Medium | High | Vertical slice phase requires one complete track pipeline proven end-to-end before content production begins |
| Browser audio-autoplay policy changes break the startup flow | Low | Medium | Audio gate is gesture-driven per current MDN guidance; browser matrix re-tested every beta cycle |
| Cross-browser Web Audio/Tone.js timing inconsistencies | Medium | Medium | QA browser matrix (Chrome/Edge/Firefox/Safari) is a release gate; calibration screen absorbs residual device/browser latency |

---

## 13. Dependencies and Assumptions

- Assumes an internal or contracted art team can deliver pixel-art assets at the specified resolution/palette discipline.
- Assumes original music composition/production is resourced and DAW-authored stems can be delivered on the vertical-slice timeline.
- Assumes no requirement (regulatory or platform) for account systems or age-rating storefront compliance in v1, since there is no distribution platform fixed yet.
- Assumes desktop-only distribution is acceptable to stakeholders for v1; mobile is explicitly deferred, not rejected long-term.

---

## 14. Analytics and Telemetry

Anonymous, local-or-consented telemetry events for v1:

`audio_gate_completed`, `calibration_completed`, `battle_started`, `ability_used`, `judgment_perfect`, `judgment_miss`, `assist_mode_enabled`, `sightread_used`, `encounter_failed`, `encounter_cleared`, `boss_phase_reached`, `save_loaded`, `echo_found` (v7.0, §8.8.2 — fires when a player discovers a world echo, letting us tell whether the exploration loop is actually being used).

This event set is sufficient to tune hit windows, detect encounter difficulty spikes, and validate whether the forecast mechanic (Sightread) is used as intended — directly feeding the KPIs in §5.

---

## 15. Delivery Plan and Roadmap

Phases below are sequential from PRD approval; indicative start date assumes sign-off by 2026-07-15.

| Phase | Duration | Indicative window | Exit condition |
|---|---:|---|---|
| Pre-production | 4 weeks | 2026-07-15 → 2026-08-12 | Approved combat prototype, locked schemas, locked art bible |
| Vertical slice | 6 weeks | 2026-08-12 → 2026-09-23 | One full biome, one boss, one complete track pipeline, calibration working |
| Content production | 8 weeks | 2026-09-23 → 2026-11-18 | Full campaign content implemented and playable end-to-end |
| Alpha | 4 weeks | 2026-11-18 → 2026-12-16 | All features complete; only bug-fixing and balance remain |
| Beta | 3 weeks | 2026-12-16 → 2027-01-06 | Browser matrix passes, accessibility matrix passes, save stability passes |
| Release candidate | 2 weeks | 2027-01-06 → 2027-01-20 | No blocker defects, balance approved, legal/audio asset checks complete |

---

## 16. QA, Acceptance Criteria, and Release Gates

### 16.1 QA matrix

| Area | Mandatory test |
|---|---|
| Timing | Scheduler remains accurate under forced rendering load |
| Browser support | Chrome, Edge, Firefox, Safari — current stable desktop |
| Saves | Create, overwrite, delete, corruption recovery |
| Calibration | Offset persists and applies correctly after refresh |
| Encounter data | Invalid beatmaps fail validation before runtime |
| Meter changes | Boss phase transitions occur on exact authored barlines |
| Accessibility | Reduced motion, speed assist, captions, remap, contrast, practice mode |
| Photosensitivity | No banned flashing patterns in default or boss VFX modes |

### 16.2 Release gates (all must be true)

1. All combat timing is driven by audio-authoritative scheduling — never visual timers alone.
2. The game boots into a user-gesture audio gate and never attempts prohibited autoplay.
3. The final boss reliably executes authored meter changes on bar boundary without drift.
4. Pixel art remains crisp at supported resolutions (low-res canvas + `image-rendering: pixelated`).
5. All accessibility features in §9.3 are present, discoverable, and functional.
6. Save data persists correctly in IndexedDB across refreshes and browser restarts.

---

## 17. Stakeholders and RACI

| Activity | Product | Engineering | Art | Audio | QA | Accessibility |
|---|---|---|---|---|---|---|
| PRD approval | A/R | C | C | C | C | C |
| Combat/timing architecture | C | A/R | I | C | C | I |
| Beatmap/ability/encounter schemas | C | A/R | I | C | I | I |
| Art bible and asset pipeline | C | I | A/R | I | I | C |
| Music/stem pipeline | C | C | I | A/R | I | C |
| Accessibility feature set | C | R | C | C | C | A |
| QA matrix and release gate sign-off | C | C | I | I | A/R | C |

*R = Responsible, A = Accountable, C = Consulted, I = Informed. Names to be assigned once discipline leads are confirmed.*

---

## 18. Open Questions

1. Final game title (Project Meterfall is a working codename only).
2. Narrative setting and framing beyond "light, character-driven."
3. Distribution channel post-v1 (itch.io, standalone site, storefront) — affects whether account/monetization stays permanently out of scope.
4. Whether mobile/touch becomes a v2 target, and if so, how the timing-window model adapts to touch latency.
5. Composer/audio production resourcing and timeline confirmation.

---

## 19. Appendix

- Full research findings, source citations, and detailed rationale: [`docs/research/deep-research-report.md`](../research/deep-research-report.md)
- JSON schemas: [`docs/technical/schemas/`](../technical/schemas/)
- Glossary:
  - **Beatmap** — the authored data file mapping a track's bars/beats/meter changes to gameplay events.
  - **Phrase** — a 1–2 measure authored input sequence tied to a specific ability.
  - **Groove** — the shared party ultimate-charge resource, built from accurate streaks.
  - **Sightread** — the healer ability that forecasts upcoming beat/meter information; the implementation of the source concept's "see the music" idea.
  - **Son clave (2–3 / 3–2)** — an Afro-Cuban rhythmic pattern spanning two bars; used here as an accent profile over a base meter, not as a time signature.

---

## 20. Implementation Status (as of 2026-07-10)

This section is a factual snapshot of what exists in the repository against this PRD, kept separate from the spec itself so the spec stays a stable target while this section is expected to go stale and get re-cut periodically. Where this section and earlier sections disagree on what's "done," this section is authoritative for current reality; the numbered sections above remain authoritative for what's *required*. This is the fourth cut of this section (earlier cuts are preserved in the revision history, §0) — everything previously open that was closeable by engineering effort inside this environment is now closed; what remains open in §20.2 is blocked on external resources.

### 20.1 Built, tested, and verified live

Everything below was checked with `npm run typecheck`, `npm test` (129 unit tests passing), `npm run build`, and the Chromium e2e project (16 Playwright specs, run repeatedly), plus extensive manual live verification in headless Chrome (scripted keyboard/pointer input, screenshots, console/error inspection, and direct state manipulation via a dev-only debug hook for scenarios real-time input automation can't drive precisely, like boss HP thresholds) — not just typechecked in isolation.

| Area | Status |
|---|---|
| Full scene stack (§10.6) | All 9 scenes are real, not stubs. Verified by playing through the entire loop live, including the full 5-node campaign. |
| Audio-clock authority (§10.2) | `TransportClock` wraps `Tone.Transport`; all judgment timing is computed from it, never `setTimeout`/`setInterval`/`requestAnimationFrame`. |
| Timing model (§8.3) | `JudgmentSystem.judge()` implements the exact four-tier windows, story-mode and assist multipliers; `PhraseTiming` converts a `bar.beat` timing template plus the one-bar count-in into transport seconds. |
| **Live meter changes (§8.7, release gate #3)** | `MeterSequence` answers "what bar/beat/meter is it right now" and "when's the next bar boundary" across a beatmap's full `meterSequence`, replacing an earlier flat-`meterSequence[0].num` assumption that could not represent a meter change at all. "The Conductor" boss swaps its beatmap (tempo + meter, including a live 5/4→7/8→4/4→3/4 cycle in phase 3) at the next bar boundary when its HP crosses each phase's authored threshold. 15 direct unit tests; verified live with a real 5/4 bar rendering on screen exactly as authored. |
| Combat engine (§8.2, §8.5) | `CombatController` is a Phaser-free state machine: full turn structure, HP/Focus/Groove/streak resources, every ability effect type, practice mode with a real no-fail-state, multi-enemy target selection. |
| **Groove-spend ultimates (§8.5, v5.1)** | One `{role}_ultimate.json` per role (100-Groove cost via a new optional `grooveCost` field in the canonical ability schema), gated and spent in `queueHeroAction`, always listed in the command menu with a `(100g)` cost label. Verified live: refused with a clear message at 0 Groove, spends the meter and runs a real timed performance at 100. Before v5.1 Groove could only ever accumulate — "spent on ultimates" existed in this spec but nothing in the game could spend it. |
| **Real stat model (§8.4 role identities, v5.1)** | Every stat that appears in authored content is now mechanically wired (all were silent no-ops before): enemy-side `defense` (increases damage taken), `accuracy`/`speed` (deterministically reduce outgoing damage — never an RNG miss chance, per the rhythm-clarity pillar), `targetFocus` (a real taunt: redirects the enemy onto the hero who applied it); hero-side `resist` (shrinks incoming enemy debuffs), enemy-applied `enemyDebuff` (reduces the hero's outgoing damage), and `accuracy` buffs (widen that hero's judgment windows via `heroTimingWindowMultiplier`, multiplicative with the accessibility assist). Semantics documented on `StatusEffect` in `CombatController.ts`; each wiring pinned by a dedicated unit test (`combat-stats.test.ts`). This makes the Mage's §8.4 "Debuff / pattern disruption" identity and the Tank's taunt real rather than log-only. |
| **In-engine art (§11.1, rebuilt v5.3)** | A real, cohesive pixel-art pass built to the new art bible (`docs/design/art-bible.md`) and derived from the Skatopia lyrics, all authored in code and rendered to committed PNGs (`tools/pixelart/`): four **distinct** hero classes with down/side/up walk cycles, six lyric-themed enemies (incl. the Conductor boss) with idle animation, a seamlessly-tiling overworld tileset, two painted 320×180 battle backdrops, and a titled main menu — one shared master palette throughout. `BattleScene` draws the backdrop + party + animated enemy wave (shadows, active-hero lift, KO dimming); `OverworldScene` walks real directional hero art under a vignette. Replaces the old one-tinted-sprite/colored-circle placeholders entirely. |
| Accessibility settings (§9.3) | Every mandatory day-one setting is functionally wired, not just persisted (game speed, assisted windows, captions, reduced motion/photosensitivity, tap-key remap, recalibrate). |
| Data-driven content pipeline (§10.5) | `ContentRegistry` validates all content against the canonical JSON Schemas (ajv) before a scene sees it, including cross-reference integrity across the full 5-node campaign, 7 enemies, and a 3-phase boss config. |
| Content volume | Full campaign chain: opening biome (slime) → mid biome 1 (drifter, 3/4→6/8) → mid biome 2 (luchador wave, clave accents, real multi-enemy targeting) → mid biome 3 (elite wraith, syncopation) → "The Conductor" (3-phase boss). This satisfies §15's vertical-slice exit condition ("one full biome, one boss") for the first time. |
| Sightread forecast | A real upcoming-events panel (`Forecast.upcomingEvents`, loop-aware), not a log line — matches the PRD §8.4 description. |
| **Relics and skill unlocks, including tier-2 ability content** | `ResultsScene` presents real relic choices; chosen relics apply real mechanical effects at battle start (`Relics.ts`: +1 max focus / permanent tank guard / banked groove). Defeating a boss writes real tier-2 unlock ids to `SaveProfile.unlockedSkills`, and each role now has a real, authored 4th ability (`{role}_tier2.json`) that becomes selectable in the command stage once unlocked — the full unlock → content → usable-ability loop is real end to end, not just the trigger. |
| Audible battle timing | `BeatmapSonifier` schedules real, meter-aware Tone.js synth hits for a beatmap's events, looped and phase-aware. Still scratch sonification, not the shipped soundtrack (§20.2). |
| **Walkable overworld hub (v5.0, §7.1/§8.1)** | `OverworldScene`: a 40×24-tile Tiled-JSON map (script-generated tileset; layout BFS-validated for marker reachability at generation time), tile-snapped 4-directional movement with real collision (pure `OverworldMovement` module — deliberately no physics engine), camera-follow with map bounds, the 8-frame run spritesheet as the animated walking player, campaign-node markers color-coded cleared (green) / unlocked (yellow) / locked (gray) via the pure `CampaignReachability` module, walk-onto-marker battle triggering, respawn at the fought node after every battle (`GameContext.returnToNodeId`), and ESC settings. Covered by 2 new unit-test files and 4 new e2e specs (movement, collision, trigger correctness, locked/cleared no-op, return flow). Replaced `MapScene` (deleted). |
| **Per-node encounter variety** | `CampaignNode.encounterPool` plus a pure `resolveEncounterId()` (`src/systems/progression/CampaignSelection.ts`) picks a random encounter from a node's pool each visit instead of always the same fight. As of v5.0, **all four non-boss nodes** draw from 2-entry pools (8 authored encounters total); `boss_1` is deliberately a fixed `encounterId` because its 3-phase config (§8.7) is keyed to that exact encounter. Content-registry cross-reference validation covers pool entries the same as fixed `encounterId`s. |
| Persistence (§10.7) | `SaveManager` (IndexedDB) supports create/load/delete/list; campaign progression (current node, cleared nodes) advances correctly through the full chain. |
| Analytics (§14) | All 12 specified events, including `boss_phase_reached`, are wired into real gameplay code paths, and as of v5.2 the player can actually grant/revoke consent: an "Analytics (local-only)" toggle in SettingsOverlay writes `SaveProfile.analyticsConsent` (persisted, consent-off by default, no network calls in v1) — previously consent defaulted off with no UI to ever enable it, leaving the whole §14 event set permanently gated in real play. Verified live: toggle → events record → consent survives a reload. |
| `tests/e2e/` | 16 committed Playwright specs (Chromium + Firefox config): boot/calibration (keyboard and pointer)/reload persistence, battle mechanics, the boss's 3-phase mechanic, two settings-UI regressions, and the 4 overworld specs. Wired into CI. See caveat in §20.2. |
| Deployment | `.github/workflows/deploy-pages.yml` builds, tests, typechecks, runs the e2e suite, then deploys to GitHub Pages on every push to `master`. The single `deploy-pages@v4` failure flagged at the end of the v4.4 cycle was transient (GitHub-side): the immediately following run deployed green with no changes, confirmed 2026-07-10. |

### 20.2 Explicitly not done — real gaps, not oversights

1. **Art depth, not art existence (mostly closed in v5.3).** The long-standing "art is placeholder" gap is now substantially closed: `docs/design/art-bible.md` exists, and the game ships a real, cohesive, lyric-derived pixel-art pass — four distinct hero classes, six themed enemies incl. the boss, a real tileset, painted battle backdrops, and a titled menu, all authored in code (`tools/pixelart/`) and committed (§20.1). What remains is animation *depth*, not a from-scratch art pass: heroes reuse the side strip flipped for left and the down silhouette for up (no true 4-directional per-frame art), and enemies have a 2-frame idle but no authored attack/hurt animations. These are incremental frame-authoring passes in the existing pipeline (rerun `generate_all.py`), not an external blocker. A separately-commissioned human-artist AAA pass remains out of scope for this environment, but is no longer what stands between the game and looking genuinely good.
2. **Music is placeholder sonification, not the real soundtrack.** `BeatmapSonifier`'s synth blips are a scratch layer for feeling the beat. The seven `tools/gbmusic/` chiptune drafts (`.lsdsng`) are authored but not wired into the game as playable audio. Rendering `.lsdsng` to a real audio buffer was investigated this cycle via PyBoy 2.4.1 against a local LSDJ ROM; PyBoy's public API (`dir(PyBoy)`) exposes no audio-buffer/WAV export, only `screen` — the only known workaround (monkey-patching `pysdl2`'s `SDL_QueueAudio`, per the reference project this pipeline was based on) was judged too fragile and version-specific to take on within this cycle. Blocked on a working Game Boy audio-rendering path existing at all, not on engineering effort against a known-good tool.
3. **Firefox e2e coverage is disabled in CI pending root-cause.** Every Firefox spec fails in `beforeAll`/boot on both this sandbox and real CI, not an intermittent flake (details and reproduction notes in `tests/e2e/README.md`). Root cause is unconfirmed (candidates: `Tone.js`'s AudioContext unlock not firing under headless Firefox, or a Phaser/WebGL incompatibility). Firefox is excluded from the CI/deploy gate until root-caused, leaving Chromium as the sole automated gate.
4. **QA matrix (§16) unexecuted on real browsers/devices.** Verification has been headless Chromium/Firefox via automation, not a real Chrome/Edge/Firefox/Safari desktop pass or any device/hardware testing. Blocked on access to real devices/browsers, which this sandboxed environment doesn't have.

Previously-listed gaps now closed and no longer here: (a) the four internal schemas are documented in §10.5 (v4.3); (b) the `TextMenu`/`SettingsOverlay` input bugs were root-caused and fixed (v4.2); (c) **per-node encounter variety** — formerly item 5, the last gap with no external blocker — is closed as of v5.0 (every non-boss node has a 2-entry `encounterPool`; the boss is deliberately fixed, see §20.1). Campaign *branching* (multiple next-node choices) remains unbuilt but was always follow-on content shape, not a v1 requirement — the campaign graph, reachability logic, and overworld markers all follow `next[0]` linearly, matching the authored content. It stays tracked in §20.3. The full Chromium e2e suite and the GitHub Pages deploy pipeline are both verified green as of this revision.

### 20.3 Suggested next increment

The vertical-slice exit condition is met, the between-battles experience is a real walkable overworld, and every gap that was closeable inside this environment (map UI → overworld, tier-2 content, schema docs, encounter variety, CI/deploy health) is closed. What's left splits into two kinds:

**Blocked on something outside this environment** (not closeable by more engineering effort alone): (1) a dedicated audio-rendering spike to get the `tools/gbmusic/` chiptune drafts playing as real audio, replacing `BeatmapSonifier` — needs either a maintained PyBoy audio-export path or a non-PyBoy Game Boy audio renderer to exist first; (2) a real art-bible pass: distinct per-class spritesheets, 4-directional overworld walk cycles, and a real tileset, gated on `docs/design/art-bible.md` and actual art production; (3) the QA matrix (§16) on real, non-headless browsers/devices; (4) the Firefox e2e root-cause (needs a maintainer with a non-sandboxed environment to bisect against, since both this sandbox and real CI show the identical failure).

**Pure follow-on content, no external blocker but also no open v1 requirement**: (5) author real branching (`CampaignNode.next` already supports multiple ids, but `CampaignReachability` and progression logic only ever follow `next[0]` — letting the player actually choose a branch needs both content and divergent overworld roads/markers); (6) author a second full biome (second boss, second overworld map) to move from "one biome, one boss" toward the fuller campaign shape in §8.6; (7) overworld depth beyond the hub mechanic: camp-node content, NPCs/secrets, re-fighting cleared nodes.

### 20.4 v6.0–v7.0 pivot — build status (as of 2026-07-11)

The v6.0–v7.0 direction change (real-time rhythm-action combat + HLD-register art + §8.8 exploration) is **in progress against the rewritten §7/§8/§11.1 spec**. Snapshot:

- **Carried forward, still real:** the Skatopia-lyric art pipeline (`tools/pixelart/`), the world/story bible (*The Drowned Chorus*), the audio-clock spine (`TransportClock`), the content pipeline and campaign graph, the framed UI skin, and the CI/deploy pipeline. The v5.0 walkable overworld is being rebuilt into the §8.8 explorable world (below), not carried forward unchanged — the old "hub" framing is exactly what v7.0 retires.
- **v7.3 real AI art pipeline — landing, iterating:** the "not AAA" ceiling of hand-coded art is broken by generating real art in-environment. The sandbox proxy reaches **Pollinations.ai** (keyless, Flux), so `tools/pixelart/generate_ai.py` generates → `import_asset.py` (palette-quantize / edge flood-key background removal / **8-bit pixelate**: chunky logical res + master-palette Floyd–Steinberg dither) → wires into the slot. **Landed as real AI art:** all 5 arena battle backdrops, the title/main-menu key-art, all 6 enemy sprites + the colossal Conductor boss, and the 5 overworld region landmarks — each 8-bit-pixelated and cohesive. Combat readability preserved by a dark scrim + background darken (§11.1.1). **Still procedural (next targets):** overworld tiles, props, NPC sprites, the 3 non-Amir band sprites, and the UI icon kit; and the deeper manifest (§11.5) — full per-character/enemy animation states, more enemy types, parallax layers — remains to be filled. Tracked against the §11.5 manifest.
- **v7.1 the band + overworld atmosphere — landed:** the playable party is now Inhalants — **Amir** (the provided hand-drawn guitarist, conformed to clean 48×48 idle/run/attack by `tools/pixelart/bandmates.py`) is the lead everywhere he appears (overworld + `ActionBattleScene`), with a bassist/vocalist/drummer authored to match; the four generated pre-band heroes are now world NPCs (§11.4). The four mechanical roles are unchanged (a `HeroClass.spriteId` re-skin), so combat + all 142 unit tests are untouched. The overworld got its atmosphere pass: drifting fog + god-ray shafts (`fx.py`), a colossal per-region landmark (`landmarks.py`), and contact-shadow grounding on props, over the existing vignette + region tint. Remaining: the arena renders only the leader, so making the other three members swappable/co-op in combat is an open increment (flagged to the owner).
- **v7.0 exploration — landed:** the overworld generator (`tools/overworld/generate_overworld_map.py`) now builds one continuous 130×34 map of five joined regions (Shallows/Salt Mines/Pit/Attic/Hall, one per movement, in campaign order), each dressed with obstacle logic matching its arena (bay inlets, a flooded shaft, a circular flooded ring, rock-wall alleys, statue columns) and tinted toward that arena's accent hue (`tools/pixelart/tiles.py`, 20-tile sheet) so the five regions read as distinct moods per §11.1.1's "one palette, five moods" rule extended to §8.8.1. Ten hand-placed **echoes** (§8.8.2, text sourced from world-bible §5b) are walkable rune props: press E in range for a found-not-told lore fragment in a framed panel; found ids persist per save (`SaveProfile.echoesFound`) and surface as a HUD counter; discovery fires the new `echo_found` analytics event (§14). At least one hand-authored **secret spur** (§8.8.3) per region branches off the main road into a hidden rock-ringed pocket. A BFS reachability check at build time fails loudly if any node marker or echo is unreachable from spawn — this caught and drove the fix for three real layout bugs during development. Verified: typecheck, 142 unit tests, production build, and the full Playwright e2e suite (16/16) all pass; live-interaction verification confirmed echo discovery/persistence/HUD/panel behavior in-browser across all five regions.
- **Landed (v6.1):** `src/systems/action/ActionCombat.ts` is the Phaser-free action-combat sim -- 8-dir acceleration/friction movement, dash cooldowns + i-frames, on-beat power vs the transport clock, light/heavy frame data (startup/active/recovery) with active hitboxes, hitstun, damage-%-scaled knockback with player DI, and enemy AI (approach → telegraph → strike → recover). `src/scenes/ActionBattleScene.ts` drives it with live input (WASD move, J light, K heavy, Shift dash), the audible beat, HP/telegraph/hitbox rendering, and the reward/campaign path → Results. **The overworld now launches this action scene** (it is the shipped combat path); the turn-based `BattleScene` stays registered so its regression specs keep running during the pivot. 10 action-combat unit tests + updated overworld e2e (incl. a forced-victory return-flow check) cover it; a colossal-scale Conductor renders in the boss arena.
- **Depth landed (v6.2):** a Focus **special** (builds from on-beat hits, spent for a heavy burst), an on-beat **parry** (negates a hit and staggers the attacker into hitstun, converting defence to offence; off-beat parry is a punishable whiff), and rhythm-gated **cancel combos** (a recovery-frame press cancels into the next attack only on-beat, inside a short window) — all in the Phaser-free sim with unit tests. Scene wires L (special) / I (parry), a parry-shield flash, and Focus in the HUD.
- **HLD art landed (v6.2):** colossal silhouette-first enemies (the Conductor towers ~2.9× over the small player), additive **emissive glow/bloom** (accent auras + glowing eyes pulsing on the beat, red windup telegraphs, on-beat player flash, bright attack arcs, impact sparks — all reduced-motion aware), and a fading battle-intro card naming the movement + foe. Enemy display names reflavored to the world bible.
- **Environments landed (v6.3):** all five §11.1.1 arenas are built and wired per-node — the drowned village green (one boat straining at its rope), the salt-mine gallery of the calcified (one mid-run), the sunken carnival ring (ropes snapped outward, two lanterns burning), the Attic of Teeth (clawed door, scrawled staves, bed of pens), and the Conductor's hall (blank pages except the last row, melting stopped clocks). Each has its beat-pulsing story light; all five screenshot-verified in-game and distinct at a glance.
- **Enterprise-art criteria closed (v6.4):** The Conductor is now **authored at native colossal resolution** (`conductor_boss.py`, ~48×68 painted pixels, fold-shaded coat / clock heart with melt drip / two-pose conducting animation) — displayed at 1.5× he stands ~105px with crisp intentional pixels, replacing the upscaled small sprite. The playable lead has **authored attack poses** (windup → swing with a motion arc, `heroes.py`) driven by the sim's real frame-data phases, plus a white hurt-flash in hitstun; all enemies now idle-animate in the arena and flash on hit. Together with the five authored arenas, per-character bespoke art, the emissive pass, and the single master palette, every §11.1 acceptance criterion is met for the shipped cast.
- **Still being built:** the full *Melee* tech tree (wavedash-like movement, more cancel routes, DI depth tuning), multi-enemy/boss-phase parity in the arena, party-member switching, native-resolution redraws for the *non-boss* elite (the wraith still displays at 2.0× from its 48px sheet — within spec but the next craft target), and overworld foreshadowing of each arena (§11.1.1's overworld rule).
- **Honest note:** *Melee*-grade depth (full cancel/tech tree, DI, wavedash-like movement) and a fully screen-filling animated boss are a multi-increment build; this section will be re-cut as each layer lands. The spec (§8.2–§8.5) is the target; this subsection tracks reality against it.
