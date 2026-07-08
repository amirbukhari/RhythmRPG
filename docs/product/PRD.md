# Product Requirements Document — Project Meterfall

## Document Control

| Field | Value |
|---|---|
| Document title | Project Meterfall — Browser Rhythm RPG PRD |
| Codename | Project Meterfall |
| Status | Draft v1.1 — pending stakeholder sign-off |
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

### 11.2 Music and audio content spec

Each battle track ships with: full mix preview, runtime stems (drums, bass, harmony, lead, FX), tempo map, meter map, bar markers, an authoring-only click reference (never shipped to players), and a battle SFX pack. Music is authored externally in a DAW and exported as bar-aligned stems.

**Tooling note:** [`tools/gbmusic/`](../../tools/gbmusic/README.md) converts a mixed reference track into a Game Boy (LSDJ) chiptune project — stem-separating into vocals/bass/drums/other and mapping them onto the Game Boy's four hardware channels (pulse/pulse/wave/noise). This is a prototyping aid for exploring an authentic 8-bit sound direction against real hardware constraints, not a replacement for the DAW-authored stem pipeline above; output is a hand-tunable LSDJ draft, not a shippable asset.

### 11.3 UX rules

The battle UI must always show: current measure and beat, phrase lane for the active action, next-downbeat indicator, enemy intent iconography, and clearly separated HP / Focus / Groove values. Critical information must never rely on color alone.

### 11.4 Current asset inventory (as of 2026-07-08)

The repository already contains pre-PRD reference material and one pipeline output. None of it satisfies §11.1/§11.2 spec and none of it counts toward the vertical-slice exit condition (§15) — it is listed here so the status is explicit rather than assumed.

| Asset | Location | Status |
|---|---|---|
| 7 placeholder hero spritesheets ("Amir" run/crouch/dash/stand animations) | `assets/sprites/heroes/placeholder/` | Reference only. Predates the art bible; does not conform to the 48×48 combat-sprite / master-palette spec in §11.1. Useful for animation-timing reference, not usable as a final hero sprite. |
| 2 animation reference GIFs (crouch, dash-to-run) | `assets/reference/animation-gifs/` | Reference only. Same source as the placeholder spritesheets above; superseded once real hero art is authored. |
| Demo audio master ("AmirsMaster...WithBabyVocals.mp3", ~22 min, kept local/gitignored — see `assets/reference/README.md`) | `assets/reference/audio-demo/` | Personal reference track, not a battle-track composition. Useful only as a tone/mood reference for the composer brief in §11.2; does not meet the stem/tempo-map/meter-map delivery spec. |
| Example `.lsdsng` chiptune draft (30–60s clip of the demo track, run through `tools/gbmusic/`) | `tools/gbmusic/output/amirs_master_clip_30-60s.lsdsng` | Proof-of-concept output of the pipeline in §11.2's tooling note. Machine-transcribed and untuned (see pipeline limitations in `tools/gbmusic/README.md`); requires manual LSDJ editing before it could inform sound direction, and is not a candidate shippable stem. |

Action item for pre-production exit (§15): the art bible and music direction docs (`docs/design/`, currently stubs) should explicitly state whether any of the above material carries forward as style reference, or is fully superseded once real art/audio production starts.

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
