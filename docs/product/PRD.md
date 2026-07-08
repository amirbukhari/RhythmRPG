# Product Requirements Document — Project Meterfall

## Document Control

| Field | Value |
|---|---|
| Document title | Project Meterfall — Browser Rhythm RPG PRD |
| Codename | Project Meterfall |
| Status | Draft v2.0 — engine + vertical-slice groundwork implemented; pending stakeholder sign-off |
| Owner | Amir Bukhari |
| Author | Amir Bukhari (compiled from concept notes and deep research) |
| Created | 2026-07-08 |
| Last updated | 2026-07-08 |
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
| Scope shape | Campaign map + battles + bosses. No free-roam overworld. |
| Aesthetic | 8-bit-inspired pixel art with modern readability. |
| Camera / layout | Side-view battles, node-based campaign map, static/parallax backgrounds. |
| Narrative | Light, character-driven framing. Minimal text burden. |
| Session target | 10–20 minute sessions; 2–3 hour first-completion campaign. |

### 7.2 Out of scope (v1)

Online features, user-generated beatmaps, procedural soundtrack generation, voice acting, full world exploration, controller rumble as a required channel, live beat detection from arbitrary/imported songs, monetization plumbing.

### 7.3 Product pillars

1. **Rhythm clarity before difficulty** — every mechanic must make the beat more legible, never less.
2. **Turn-based strategy with rhythmic execution** — the game is an RPG first, a reflex gauntlet second; this also aligns with accessibility guidance favoring turn-based structures to reduce real-time pressure.
3. **Musical variety without musical confusion** — content starts in 4/4, differentiates via accents/subdivisions, and introduces true meter changes deliberately, never disguising a rhythmic pattern (clave) as a time signature.

---

## 8. Functional Requirements

### 8.1 Core loop

Boot → audio-gesture unlock → save slot select/create → optional AV calibration → node-based campaign map (battle / elite / camp / boss nodes) → node reward → repeat until final boss cleared.

### 8.2 Battle loop and turn structure

Combat is strictly turn-based (not ATB, not real-time):

1. **Intent phase** — enemy intents displayed.
2. **Command phase** — player selects one action for the active hero; untimed in normal play.
3. **Performance phase** — action executes as an authored rhythmic phrase over a one-bar count-in.
4. **Resolution phase** — damage/healing/status/resource changes apply.
5. **Next combatant** — turn advances.
6. **Round end** — end-of-round effects trigger after all living combatants have acted.

### 8.3 Timing model

- Every action maps to an authored phrase (1–2 measures) against the active track's beatmap; timing is never discovered by blind trial.
- The UI always displays current measure, current beat, next downbeat, and the active phrase lane.
- Judgment tiers (pre-accessibility-modifier):

| Tier | Window | Result |
|---|---:|---|
| Perfect | ±45 ms | 100% base potency + streak gain |
| Great | ±90 ms | 85% base potency |
| Good | ±140 ms | 65% base potency |
| Miss | outside Good | 0% potency, combo break |

- Story mode widens all windows by 25%. Calibration offsets apply globally, before judgment.

### 8.4 Party and role kits

| Role | Combat purpose | Core abilities (v1) | Signature mechanic |
|---|---|---|---|
| Warrior | Burst damage | Slash Chain, Rising Break, Finisher | Longer, higher-reward combo phrases |
| Tank | Mitigation / interruption | Guard Pulse, Taunt Stomp, Iron Wall | Downbeat-based guard and interrupt windows |
| Mage | Debuff / pattern disruption | Arc Flash, Hex Syncopation, Static Field | Offbeat and syncopated phrase design |
| Healer | Sustain / visibility | Mend Cadence, Purify Hymn, Sightread | Reveals future cues and meter changes |

**Sightread** (healer) is the canonical realization of the source concept's "see the music" idea: it reveals the next two measures of enemy telegraph glyphs, syncopation markers, and upcoming meter changes. Without it, players still see the current phrase lane and barline — there is no scenario where the baseline beat UI is hidden.

### 8.5 Resources and progression

- Each hero has HP and Focus; Focus is earned by accurate play and spent on advanced skills.
- The party shares a **Groove** meter, built from streaks, spent on ultimates. Missed inputs reduce Groove gain but never remove existing Focus.
- Progression is deterministic, not loot-driven: one new skill per hero per biome boss. Equipment limited to one relic slot per hero plus one shared party charm.

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
| MapScene | Campaign progression and rewards |
| BattleScene | All combat logic and UI |
| ResultsScene | XP, relic, unlocks |
| SettingsOverlay | Always-available settings modal |

### 10.7 Storage and persistence

All save data lives in **IndexedDB**: player settings, calibration offsets, campaign progress, unlocked skills, relic inventory, analytics consent state.

---

## 11. Content and UX Requirements

### 11.1 Art direction

| Asset type | Spec |
|---|---|
| Base resolution | 320×180 |
| Tile size | 16×16 |
| Hero combat sprite | 48×48 |
| Enemy combat sprite | 48×48 to 64×64 |
| UI icons | 16×16 |
| Battle backgrounds | 320×180, layered, parallax optional |
| Animation rate | 8–12 fps authored; engine interpolation reserved for camera/UI only |
| Palette policy | One global master palette + per-biome accent extension |

**Carried-forward basis:** the placeholder "Amir" hero spritesheets and animation GIFs (§11.4) are the visual and animation-timing basis for the hero character going forward — final hero art is a redraw/rework of this character to the resolution, sprite-size, and palette spec above, not a replacement with a different design. The art bible (`docs/design/`) should be written as a spec-conformant extension of this reference, not from a blank slate.

### 11.2 Music and audio content spec

Each battle track ships with: full mix preview, runtime stems (drums, bass, harmony, lead, FX), tempo map, meter map, bar markers, an authoring-only click reference (never shipped to players), and a battle SFX pack. Music is authored externally in a DAW and exported as bar-aligned stems.

**Carried-forward basis:** the demo audio master (§11.4) and its Game Boy chiptune derivative are the music-direction basis, not disposable reference. [`tools/gbmusic/`](../../tools/gbmusic/README.md) — which stem-separates a mixed track into vocals/bass/drums/other and maps them onto the Game Boy's four hardware channels (pulse/pulse/wave/noise) — is the intended production path for turning this track into authentic Game Boy chiptune material: run the pipeline, then hand-tune the resulting `.lsdsng` in LSDJ, then render/record real Game Boy audio as the shippable stem set per the spec above. The DAW-authored-stems requirement still stands for tracks that don't originate from this pipeline; this is the path for tracks that do.

**Track sourcing decision:** all v1 battle tracks are sliced from this single ~22-minute demo master (`--start`/`--duration` per segment in `tools/gbmusic/convert.py`), not composed as separate new material per biome. Each stage in the §8.6 encounter progression and each final-boss phase (§8.7) gets its own slice, its own independent `gbmusic` run, and its own hand-tuning pass — they are distinct `.lsdsng` projects/renders even though they share one source recording. Meter changes for the final boss are still hand-authored in the beatmap JSON per §10.5/§8.7 regardless of which audio slice underlies them — slicing determines the audio content, not the authored meter/event data layered on top of it.

Which timestamp ranges map to which stage is recorded in [`docs/design/music-direction.md`](../design/music-direction.md): ranges were chosen algorithmically (rhythmic-density/energy scoring, ascending complexity to match the §8.6 difficulty curve), not by ear, so treat the mapping as a starting point pending a human listening pass, not a locked decision. All seven `.lsdsng` drafts exist at `tools/gbmusic/output/{opening_biome,mid_biome_1,mid_biome_2_clave,mid_biome_3_syncopated,boss_phase_1,boss_phase_2,boss_phase_3}.lsdsng`.

### 11.3 UX rules

The battle UI must always show: current measure and beat, phrase lane for the active action, next-downbeat indicator, enemy intent iconography, and clearly separated HP / Focus / Groove values. Critical information must never rely on color alone.

### 11.4 Current asset inventory (as of 2026-07-08)

**Decision: this material carries forward** as the style/direction basis for production (confirmed 2026-07-08) — it is not disposable placeholder to be discarded once "real" production starts. None of it meets §11.1/§11.2 delivery spec yet in its current form, and none of it counts toward the vertical-slice exit condition (§15) as-is, but it is the thing final assets are derived from, not replaced by.

| Asset | Location | Status |
|---|---|---|
| 7 placeholder hero spritesheets ("Amir" run/crouch/dash/stand animations) | `assets/sprites/heroes/placeholder/` | Carries forward as the hero's visual/animation basis. Does not yet conform to the 48×48 combat-sprite / master-palette spec in §11.1 — needs redrawing to spec, not replacing with a different character. |
| 2 animation reference GIFs (crouch, dash-to-run) | `assets/reference/animation-gifs/` | Carries forward as animation-timing reference for the same character; superseded by the spritesheets above wherever they overlap. |
| Demo audio master ("AmirsMaster...WithBabyVocals.mp3", ~22 min, kept local/gitignored — see `assets/reference/README.md`) | `assets/reference/audio-demo/` | Carries forward as the sole source track for all v1 battle music. Not itself a battle-track deliverable (too long, not stem/tempo/meter-mapped) — every stage/boss-phase track is a distinct slice of this master run through `tools/gbmusic/` (§11.2), not separately composed material. |
| Example `.lsdsng` chiptune draft (30–60s clip of the demo track, run through `tools/gbmusic/`) | `tools/gbmusic/output/amirs_master_clip_30-60s.lsdsng` | Carries forward as the first working proof of the music-direction pipeline. Machine-transcribed and untuned (see limitations in `tools/gbmusic/README.md`) — needs hand-tuning in LSDJ before it's a candidate shippable stem, but it is the direction, not a discardable prototype. |
| 7 stage/boss-phase `.lsdsng` drafts, one per row of the table in `docs/design/music-direction.md` | `tools/gbmusic/output/{opening_biome,mid_biome_1,mid_biome_2_clave,mid_biome_3_syncopated,boss_phase_1,boss_phase_2,boss_phase_3}.lsdsng` | The full v1 battle-track set, sliced and converted per the track-sourcing decision above. Same caveats as the example draft: machine-transcribed, untuned, not yet auditioned by a human, not shippable as-is. |

Action item for pre-production exit (§15): the art bible and music direction docs (`docs/design/`, currently stubs) should be written as spec-conformant extensions of this carried-forward material — i.e., document how the "Amir" character and the chiptune-via-`gbmusic` approach get taken to shippable quality, not propose alternatives to them.

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

`audio_gate_completed`, `calibration_completed`, `battle_started`, `ability_used`, `judgment_perfect`, `judgment_miss`, `assist_mode_enabled`, `sightread_used`, `encounter_failed`, `encounter_cleared`, `boss_phase_reached`, `save_loaded`.

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

## 20. Implementation Status (as of 2026-07-08)

This section is a factual snapshot of what exists in the repository against this PRD, kept separate from the spec itself so the spec stays a stable target while this section is expected to go stale and get re-cut periodically. Where this section and earlier sections disagree on what's "done," this section is authoritative for current reality; the numbered sections above remain authoritative for what's *required*.

### 20.1 Built, tested, and verified live

Everything below was checked with `npm run typecheck`, `npm test` (67 unit tests passing), and `npm run build`, and additionally driven end-to-end in headless Chrome (scripted keyboard/pointer input against a running `vite dev` server, with screenshots and console/error inspection) — not just typechecked in isolation.

| Area | Status |
|---|---|
| Full scene stack (§10.6) | All 9 scenes are real, not stubs: Boot → AudioGate → MainMenu → Save → Calibration → Map → Battle → Results, plus the SettingsOverlay modal. Verified by playing through the entire loop live. |
| Audio-clock authority (§10.2) | `TransportClock` wraps `Tone.Transport`; all judgment timing in `BattleScene` is computed from it, never from `setTimeout`/`setInterval`/`requestAnimationFrame`. |
| Timing model (§8.3) | `JudgmentSystem.judge()` implements the exact four-tier windows, story-mode and assist multipliers; `PhraseTiming` converts a `bar.beat` timing template plus the one-bar count-in into transport seconds. 14 direct unit tests between the two. |
| Combat engine (§8.2, §8.5) | `CombatController` is a Phaser-free state machine implementing the full turn structure, HP/Focus/Groove/streak resources, and every ability effect type (damage/heal/guard/buff/partyBuff/debuff/interrupt/forecastReveal). 18 unit tests, including two regression tests for a real bug caught live (a full miss was still applying non-damage effects). |
| Practice mode (§9.3) | Genuinely removes the fail state (party revives at 1 HP) rather than being a cosmetic flag — implemented in `CombatController`, not just stored. |
| Accessibility settings (§9.3) | Every mandatory day-one setting is functionally wired, not just persisted: game speed actually scales playback tempo (and the audible sonifier stays in sync with it), assisted timing windows actually widen judgment, captions actually toggle the on-screen event log, reduced motion / photosensitivity-safe mode actually change `CalibrationScene`'s flash behavior, tap-key remapping is a real captured rebind used by both `BattleScene` and `CalibrationScene`, and "Recalibrate" re-enters `CalibrationScene`. Two real UI bugs (selection reset on every settings change; a paused scene's menu still reacting to keypresses) were found and fixed via live testing, not caught by unit tests. |
| Data-driven content pipeline (§10.5) | `ContentRegistry` loads all content via `import.meta.glob` and validates every item against the canonical JSON Schemas through `ContentLoader` (ajv) before a scene ever sees it. 15 unit tests, including cross-reference integrity (encounter → beatmap → enemy telegraphs). |
| Audible battle timing | `BeatmapSonifier` schedules real Tone.js synth hits for a beatmap's downbeat/telegraph events, looped for the encounter's duration, volume- and game-speed-aware. This is scratch sonification for playtesting feel, not the shipped soundtrack (see §20.2). |
| Persistence (§10.7) | `SaveManager` (IndexedDB) supports create/load/delete/list; save profiles round-trip correctly (5 unit tests with `fake-indexeddb`). |
| Analytics (§14) | 11 of the 12 specified events are wired into real gameplay code paths (consent-gated, per `Analytics`). `boss_phase_reached` has no call site yet because no boss encounter exists (§20.2). |
| Deployment | `.github/workflows/deploy-pages.yml` builds, tests, typechecks, then deploys to GitHub Pages on every push to `master`. |

### 20.2 Explicitly not done — real gaps, not oversights

Enumerated so nobody mistakes "the engine works" for "the game is content-complete." None of these are hidden; each is a concrete, scoped next increment.

1. **Content volume.** Only one encounter exists (`opening_biome_slime_01`, one enemy, one beatmap). The full §8.6 progression (mid biomes 1–3, accent/syncopation teaching) and the three-phase final boss with live meter changes (§8.7) are unauthored. The vertical-slice exit condition in §15 ("one full biome, one boss") is not yet met — what exists is a single playable encounter proving the architecture, not a biome or a boss.
2. **No visual art in-engine.** `BattleScene` and every other scene are text/shape rendering only. The placeholder "Amir" sprites (§11.4) are not loaded or drawn anywhere; the 320×180 pixel-art pipeline (§11.1, §10.6) is configured (`GameConfig.ts`) but has no actual sprite content exercising it yet.
3. **Music is placeholder sonification, not the real soundtrack.** `BeatmapSonifier`'s synth blips are a scratch layer for feeling the beat, not shippable audio. The seven `tools/gbmusic/` chiptune drafts (§11.2/§11.4) are not wired into the game at all — they'd need to be rendered from `.lsdsng` to playable audio first (that step was never automated; see `tools/gbmusic/README.md`'s auditioning instructions).
4. **`tests/e2e/` is empty.** All end-to-end verification this session was manual: ad hoc Puppeteer scripts run against a local dev server, not committed as a repeatable automated suite. Given how much this caught (three real bugs unit tests couldn't see), turning those throwaway scripts into a maintained Playwright/Puppeteer suite under `tests/e2e/` is a high-value next step, not optional polish.
5. **Enemy/encounter variety.** One enemy type (slime) exists. The luchador/clave-accent enemy family (§8.6) and "The Conductor" final boss (§8.7) are unimplemented.
6. **Relics and skill unlocks are not mechanically real yet.** `victoryRewards.relicChoices` is displayed on `ResultsScene` but nothing lets a player equip a relic or apply its effect; `SaveProfile.unlockedSkills` exists but nothing ever writes to it, because no boss (the unlock trigger, §8.5) exists yet.
7. **Targeting is always automatic.** With only one enemy in the game, `CombatController`'s default-target logic (first alive enemy / lowest-HP hero) has never been exercised against a real choice. Multi-enemy encounters will need actual target-selection UI in `BattleScene`, which doesn't exist yet.
8. **Sightread's forecast is a log line, not a UI lane.** The ability's `forecastReveal` effect logs a message; it doesn't yet draw the "next two measures of telegraph glyphs" UI the PRD (§8.4) describes, which matters more once the final boss's meter changes exist for it to forecast.
9. **QA matrix (§16) unexecuted.** Verification this session was one headless Chromium instance via automation. The Chrome/Edge/Firefox/Safari desktop matrix, and any real device/hardware pass, have not been run.
10. **`Enemy`, `HeroClass`, and `CampaignNode` are undocumented-by-PRD internal schemas.** This is a deliberate, documented scope decision (see the rationale comments in `src/data/schemas/`), not scope creep — the PRD's three canonical schemas (beatmap/ability/encounter) intentionally don't cover combat stats or map topology, and something had to for combat to be runnable at all.

### 20.3 Suggested next increment

Per §15's own phasing, the next bounded increment that would satisfy the vertical-slice exit condition is: author one additional biome's worth of encounters (using the `mid_biome_1`/`mid_biome_2_clave` chiptune drafts already in `tools/gbmusic/output/`), author "The Conductor" as a real three-phase boss with hard-authored meter changes in its beatmap, and convert this session's throwaway Puppeteer scripts into a committed `tests/e2e/` suite. Art integration (real sprites replacing text) is a separate, parallel track gated on the art bible (`docs/design/art-bible.md`) still being unwritten.
