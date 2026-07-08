# Browser Rhythm RPG PRD Based on the Supplied Concept Notes

## What the supplied concept notes actually confirm

The three screenshots define a clear core concept. The game is a **turn-based RPG** whose attacks are performed through **rhythm-based combinations tied to battle music**. The party uses four classic roles: **warrior, healer, tank, and mage**. Most encounters are expected to sit in **4/4**, while the **final boss uses changing time meters**. The notes also propose a mechanic where certain spells let the player **“see” the music** to anticipate pattern or meter changes. Enemy variety is explicitly part of the concept, including an example of **luchador-themed enemies** tied to a **2–3 or 3–2 clave-style rhythm pattern**. The screenshots also explicitly float a **browser delivery target**, an **old-school 8-bit / pixel-art aesthetic**, original **soundtrack work**, and “sick movesets.”

Several product-critical items are **unknown** in the source notes and must therefore be fixed by this PRD rather than left open: the game name, narrative setting, total campaign length, monetization model, multiplayer status, supported devices, exact combat timing rules, save system, and how visible the beat UI should be by default. If those items remain undefined, developers will have to stop and ask product questions. This PRD resolves them explicitly.

The PRD therefore fixes the following defaults for version one: **desktop browser-first**, **single-player only**, **no monetization**, **no account system**, **local save only**, **pixel-art presentation**, **one campaign of roughly 2–3 hours**, and **battle-focused progression rather than a large explorable world**. Those are product decisions, not facts from the screenshots.

## Research findings that should change the design before development starts

The concept is genre-valid. Official game materials already prove that rhythm-based combat hybrids work when the beat is made legible. *Crypt of the NecroDancer* is officially described as a roguelike rhythm game where players “move to the music” and “deliver beatdowns to the beat,” while *Cadence of Hyrule* states that every beat is a chance to move, attack, defend, and cast spells, and explicitly calls out an **on-screen beat bar** for rhythmic combat. *Hi-Fi RUSH* likewise markets a combat world that “syncs to the music.” The design implication is direct: players will accept a music-driven combat system, but successful implementations do **not** rely on hidden timing alone; they surface timing through readable world sync, beat bars, or both. citeturn8view5turn8view6turn1search2

The music theory in the source notes needs one correction so the game system is musically coherent. A **time signature** defines how many beats are in a measure and which note value gets the beat. By contrast, **3–2 or 2–3 son clave** is an Afro-Cuban rhythmic pattern spread across two measures, not a time signature by itself. Berklee identifies clave as a repeated foundational rhythmic pattern, and Open Music Theory plus the University of Puget Sound material describe 3–2 son clave as a pattern with **three attacks in the first bar and two in the second**. The design consequence is that “luchador enemies in 2/3 clave” should be implemented as **accent logic over a base meter**, most naturally over 4/4 or cut time, while actual **meter changes** should be reserved for boss and advanced encounter design. citeturn8view8turn8view7turn14view0

The browser target is technically viable, but only if timing is architected around the **audio clock**, not around normal UI timers. The Web Audio API exposes a high-precision hardware-driven `currentTime` clock, and web.dev’s scheduling guidance states that JavaScript timer callbacks can drift by **tens of milliseconds or more** because of layout, rendering, and garbage collection on the main thread. Tone.js exists specifically to schedule musical events against exact time values instead of relying on `setInterval` or `requestAnimationFrame`. This means the combat judge, metronome, barline transitions, and boss meter shifts must be authored and executed against **Web Audio / Tone transport time**, with the visual layer following the audio timeline rather than the other way around. citeturn9view1turn9view2turn8view1turn8view3

A browser rhythm game must also account for platform audio restrictions and persistence rules. MDN documents that Web Audio contexts generally must be started from a **user gesture**, not autoplayed on page load, and also identifies **IndexedDB** as the correct browser storage layer for significant structured local data and offline-capable apps. The product implication is that the build needs a mandatory **“Click to Start Audio”** gate before the title menu becomes interactive, plus a **local IndexedDB save profile** rather than `localStorage`. citeturn15search1turn15search0turn8view9turn11view2

The accessibility implication is even more important than the genre implication. Microsoft’s Xbox Accessibility Guideline 103 says key visual and audio cues should be expressed through **multiple sensory methods**, and XAG 104 explicitly cites captions like **“music intensifies”** as a way to expose musically meaningful information to players who cannot hear it. Game Accessibility Guidelines also recommend **not making precise timing the only path to success**, adding speed controls, practice modes, and alternatives. W3C further warns against flashing content above seizure-risk thresholds, and Microsoft’s photosensitivity guidance says all games should be tested for seizure triggers. This means the original “you can only hear the music unless a spell reveals it” idea should be modified: a hidden beat UI as the default would directly conflict with current accessibility practice. The correct implementation is a **baseline readable beat interface for everyone**, with “see the music” spells upgraded into **forecast mechanics** that reveal *future* cadence changes, syncopations, or enemy intent earlier than normal. citeturn17view0turn17view1turn17view3turn12view1turn12view0turn13search2

## Product definition

This PRD defines a browser-first product with the working codename **Project Meterfall**. The codename is a placeholder so every discipline can work against a stable identifier.

### Product statement

Project Meterfall is a **single-player, browser-based, pixel-art rhythm RPG** in which the player controls a fixed party of four heroes—warrior, tank, mage, and healer—and wins battles by executing timed attack phrases against an authored musical timeline. The game teaches rhythm gradually through mostly 4/4 encounters, then expands into accent-driven enemy families and curated meter-change boss fights, culminating in a final battle built around live meter changes.

### Product decisions that are now fixed

| Area | Decision |
|---|---|
| Platform | Desktop web only for v1. Chrome, Edge, Firefox, Safari current stable versions. Mobile/touch is unsupported in v1. |
| Delivery | Browser-first static web app. No launcher. No native wrapper in v1. |
| Mode | Single-player only. No co-op, no PvP, no chat. |
| Business model | None in v1. No ads, no IAP, no login, no account creation. |
| Save model | Local saves in-browser only. |
| Scope shape | Campaign map + battles + bosses. No free-roam overworld. |
| Aesthetic | 8-bit-inspired pixel art with modern readability. |
| Camera / layout | Side-view battles, node-based campaign map, static/parallax backgrounds. |
| Narrative | Light, character-driven framing. Minimal text burden. |
| Session target | 10–20 minute play sessions; 2–3 hour first-completion campaign. |

### Product pillars

The first pillar is **rhythm clarity before difficulty**. The music system is the product, so every mechanic must make the beat more legible, not less legible.

The second pillar is **turn-based strategy with rhythmic execution**. The game must feel like an RPG first and a reflex gauntlet second. That preserves the source concept and also aligns with accessibility practice around time pressure mitigation. W3C explicitly uses turn-based interaction as an example of reducing barriers created by real-time pressure. citeturn12view0

The third pillar is **musical variety without musical confusion**. Most content starts in 4/4, enemy families are differentiated through accents and subdivisions, and actual meter changes are introduced deliberately and taught before they become punitive. That sequencing follows basic music theory distinctions between meter and pattern, and avoids using “clave” as a fake meter. citeturn8view8turn8view7turn14view0

### Out-of-scope items

Version one excludes online features, user-generated beatmaps, procedural soundtrack generation, voice acting, full world exploration, controller rumble in the browser as a required channel, live beat detection from arbitrary songs, imported MP3 gameplay, and monetization plumbing.

## Gameplay and systems PRD

### Core loop

The player enters the game through an audio unlock screen, selects or creates a local save, optionally runs audio/video calibration, then advances through a **node-based campaign map** made of battle nodes, elite nodes, camp nodes, and boss nodes. Each cleared node grants XP, currency, and one deterministic reward choice. The campaign ends when the final boss is defeated.

The battle loop is fixed as follows. The player enters a battle against one authored enemy group attached to one authored track and beatmap. The game presents enemy intents. The player selects one action for one hero at a time in turn order. On action confirm, the game gives a **one-bar count-in** and then runs the action phrase over the current battle music. Accuracy determines potency. Enemy actions then resolve with optional defense prompts. The loop repeats until one side is defeated.

### Turn structure

Combat is strictly **turn-based**, not ATB and not fully real-time. The order of operations is:

1. **Intent phase**: enemy intents are shown.
2. **Command phase**: the player chooses one action for the active hero. This phase is untimed in normal play.
3. **Performance phase**: the selected action executes over one authored rhythmic phrase.
4. **Resolution phase**: damage, healing, status changes, and resource changes apply.
5. **Next combatant**: turn advances.
6. **Round end**: end-of-round effects trigger after all living combatants act.

This keeps the product faithful to the screenshots’ “turn-based RPG” language while still making rhythmic execution central.

### Timing model

Every combat action maps to an **authored phrase** defined against the active track’s beatmap. A phrase is one or two measures long. The player never has to discover timing by blind trial. The UI always shows the current measure, current beat, next downbeat, and phrase lane. The special “see the music” spells reveal **advanced information** rather than the basic beat itself.

Accuracy uses four judgment tiers:

| Tier | Window | Result |
|---|---:|---|
| Perfect | ±45 ms | 100% base potency + streak gain |
| Great | ±90 ms | 85% base potency |
| Good | ±140 ms | 65% base potency |
| Miss | outside Good | 0% step potency and combo break |

These thresholds are before accessibility modifiers. Story mode widens all windows by 25%. Calibration offsets are applied globally before judgment.

### Party and role kits

The party has four fixed roles with authored, non-random kits.

| Role | Combat purpose | Core abilities in v1 | Signature mechanic |
|---|---|---|---|
| Warrior | burst damage | Slash Chain, Rising Break, Finisher | longer combo phrases with high reward |
| Tank | mitigation and interruption | Guard Pulse, Taunt Stomp, Iron Wall | downbeat-based guard and interrupt windows |
| Mage | debuff and pattern disruption | Arc Flash, Hex Syncopation, Static Field | offbeat and syncopated phrase design |
| Healer | sustain and visibility tools | Mend Cadence, Purify Hymn, Sightread | reveals future cues and meter changes |

The healer’s **Sightread** spell is the canonical implementation of the screenshots’ “see the music” idea. When active, it reveals the next two measures of enemy telegraph glyphs, syncopation markers, and upcoming meter changes. Without Sightread, the player still sees the current phrase lane and current barline; they simply do not get extra future forecast.

### Resources and progression

Each hero has HP and Focus. Focus is earned by accurate play and spent on advanced skills. The party also shares a **Groove meter** that builds from streaks and is spent on ultimates. Missing timed inputs reduces Groove gain but does not remove existing Focus. This keeps misses punitive without causing total collapse.

Character progression is deterministic, not loot-driven. Each hero unlocks one new skill after each biome boss. Equipment is limited to a single relic slot per hero and one shared party charm. That is a deliberate scope control decision.

### Encounter design

Encounter design is structured to teach meter and accent ideas progressively.

| Stage | Musical design | Mechanical purpose |
|---|---|---|
| Opening biome | mostly 4/4 straight subdivisions | tutorializes timing, count-ins, and role identities |
| Mid biome one | 3/4 and 6/8 introductory fights | teaches non-quadruple feel without chaos |
| Mid biome two | 4/4 with clave-accent enemies | teaches cross-accent recognition |
| Mid biome three | syncopated elite encounters | teaches forecast and defense layering |
| Final boss | live meter changes across authored phases | culmination of full system |

The source notes specifically give “luchadors” as an example. In this PRD, the luchador faction uses **2–3 and 3–2 son-clave accent maps over 4/4-based fights**, with throws and counters on the accent hits. That preserves the original idea while keeping the music theory correct. citeturn8view7turn14view0

### Final boss specification

The final boss is a three-phase encounter named **The Conductor** for internal production use.

**Phase one** uses stable 4/4 with deceptive syncopation.  
**Phase two** alternates 4/4 and 3/4 every four bars.  
**Phase three** cycles 5/4, 7/8, 4/4, and 3/4 with explicit visual forecast if Sightread is active and reduced forecast if it is not.

Meter changes are hard-authored in the battle beatmap. They are not improvised, not generated, and not inferred from audio. Tone.js transport support for time changes and exact event-time callbacks makes this scheduling model appropriate for a browser implementation. citeturn8view1turn6search2

## Technical architecture PRD

### Required stack

The recommended stack is **TypeScript + Phaser + Tone.js + Web Audio API**.

That recommendation is evidence-based. Phaser is actively maintained and officially supports HTML5 games across desktop and mobile web browsers with WebGL and Canvas rendering and TypeScript support. Tone.js is explicitly designed for interactive music in the browser and provides a transport that schedules events against exact time values rather than UI timers. MDN documents Web Audio as broadly available and suitable for advanced game audio, including dynamic music and precise timing. citeturn10view0turn8view1turn6search2turn8view3turn11view1

### Authoritative timing rule

**No gameplay judgment may be derived from `setTimeout`, `setInterval`, or `requestAnimationFrame` alone.** Those APIs may drive visuals, but the source of truth for musical state is the audio timeline. web.dev documents that JavaScript timers can skew by tens of milliseconds on the main thread, while the Web Audio clock is hardware-driven and precise enough for sample-level scheduling. citeturn9view1turn9view2

### Audio subsystem

The audio subsystem must support the following:

| Requirement | Implementation |
|---|---|
| master timeline | Tone.Transport as global musical clock |
| exact event scheduling | Web Audio clock time passed into callbacks |
| custom low-latency analysis / click / metronome if needed | AudioWorklet |
| battle music system | authored stem playback aligned to bar/beat markers |
| state-reactive mix | mute/unmute stems and automate parameters on phase changes |
| calibration | user-adjustable global AV sync offset |

MDN’s game audio guidance explicitly recommends Web Audio for dynamic game music and notes that separate tracks or loops can be synchronized and brought in and out to react to game state. AudioWorklet exists for custom processing on a separate audio thread with low latency. citeturn11view1turn11view0

### Audio startup requirement

The very first screen after boot must be **Press Any Key to Start Audio**. This screen has one job: create or resume the AudioContext on user gesture, because browsers commonly suspend Web Audio until user initiation. The game must not attempt to autoplay the soundtrack before that point. citeturn15search1turn15search0

### Data-driven content architecture

All gameplay content is data-driven. No encounter timing may be hardcoded in scene logic.

#### Beatmap schema

```json
{
  "trackId": "boss_conductor_p3",
  "bpm": 152,
  "meterSequence": [
    { "startBar": 1, "bars": 4, "num": 5, "den": 4 },
    { "startBar": 5, "bars": 4, "num": 7, "den": 8 },
    { "startBar": 9, "bars": 4, "num": 4, "den": 4 }
  ],
  "subdivision": 16,
  "events": [
    { "bar": 1, "step": 0, "type": "downbeat" },
    { "bar": 1, "step": 6, "type": "enemyTelegraph", "payload": "slam" }
  ]
}
```

#### Ability schema

```json
{
  "abilityId": "healer_sightread",
  "role": "healer",
  "focusCost": 2,
  "phraseLengthBars": 1,
  "inputPattern": ["tap", "tap", "hold"],
  "timingTemplate": ["1.1", "1.3", "1.4"],
  "effects": [
    { "type": "forecastReveal", "bars": 2 },
    { "type": "partyBuff", "stat": "accuracy", "value": 0.1, "durationRounds": 2 }
  ]
}
```

#### Encounter schema

```json
{
  "encounterId": "arena_luchador_elite",
  "trackId": "arena_clave_01",
  "enemyWave": ["luchador_grunt", "luchador_mask", "manager"],
  "accentProfile": "son_clave_2_3",
  "victoryRewards": {
    "xp": 150,
    "currency": 60,
    "relicChoices": ["counter_charm", "focus_loop"]
  }
}
```

### Rendering and scene architecture

The build uses a fixed internal resolution of **320×180** in a 16:9 canvas, scaled by integer multiples where possible. MDN’s pixel-art guidance recommends using a low-resolution canvas and CSS `image-rendering: pixelated` so pixels upscale without smoothing. citeturn18view0

The scene stack is fixed:

| Scene | Purpose |
|---|---|
| BootScene | load manifest, verify browser support |
| AudioGateScene | user gesture, create/resume audio context |
| MainMenuScene | start, continue, settings |
| SaveScene | slot create/load/delete |
| CalibrationScene | AV sync test and offset save |
| MapScene | campaign progression and rewards |
| BattleScene | all combat logic and UI |
| ResultsScene | XP, relic, unlocks |
| SettingsOverlay | always-available settings modal |

### Storage and persistence

All save data lives in **IndexedDB**. Save objects include player settings, calibration offsets, campaign progress, unlocked skills, relic inventory, and analytics consent state. MDN documents IndexedDB as the correct browser API for significant structured client-side storage and notes that it supports offline-capable app behavior. citeturn8view9turn11view2

### Performance requirements

The battle scene must target **60 FPS** on supported desktop browsers. Audio scheduling must remain stable if rendering stutters. Combat should remain rhythm-correct even when the visual frame rate dips temporarily, because audio is authoritative. That requirement follows directly from Web Audio scheduling guidance. citeturn9view2

## Content, UX, and accessibility PRD

### Art direction specification

The game uses an **8-bit-inspired**, not historically literal, pixel-art style. The internal rules are fixed:

| Asset type | Spec |
|---|---|
| base resolution | 320×180 |
| tile size | 16×16 |
| hero combat sprite | 48×48 |
| enemy combat sprite | 48×48 to 64×64 |
| UI icons | 16×16 |
| battle backgrounds | 320×180 layered, parallax optional |
| animation rate | 8–12 fps authored, interpolated by engine only for camera/UI |
| palette policy | one global master palette plus per-biome accent extension |

The canvas must render with crisp scaling, not smoothing. MDN specifically recommends low-resolution canvas rendering plus `image-rendering: pixelated` for this use case. citeturn18view0

### Music and audio content specification

Each battle track must ship with:

| Audio asset | Required |
|---|---|
| full mix preview | yes |
| runtime stems | drums, bass, harmony, lead, FX |
| tempo map | yes |
| meter map | yes |
| bar markers | yes |
| click reference for authoring only | yes, not shipped for player |
| battle SFX pack | yes |

Music is authored externally in a DAW and exported with bar-aligned stems. MDN’s game-audio guidance explicitly notes that separate loops or tracks can be synchronized and brought in or out dynamically, which is the correct model for phase transitions, ultimates, and boss states. citeturn11view1

### UX rules

The battle UI must always show:

- current measure and beat,
- phrase lane for the active action,
- next downbeat indicator,
- enemy intent iconography,
- clearly separated HP / Focus / Groove values.

The UI must **not** require color alone to distinguish critical information. XAG 103 specifically warns against relying on a single sensory channel or color-only distinction for important cues. citeturn17view0

### Accessibility requirements

Accessibility is not optional in this design because the original concept is inherently timing-heavy.

The build must ship with these settings on day one:

| Setting | Required reason |
|---|---|
| remappable controls | input accessibility baseline citeturn17view3turn12view1 |
| keyboard-only play with no required simultaneous button presses | digital accessibility baseline citeturn12view1turn17view3 |
| separate volume sliders for music / SFX / UI | recommended game accessibility baseline citeturn12view1 |
| subtitles / captions for dialogue and musically meaningful events | musical information must be perceivable without hearing citeturn17view1 |
| reduced motion mode | visual distraction mitigation citeturn12view1turn12view0 |
| photosensitivity-safe VFX mode | flashing risk control citeturn12view0turn13search2 |
| game speed options 70% / 85% / 100% | timing accessibility citeturn12view1turn17view3 |
| assisted timing windows | precise timing cannot be the only viable path for all users citeturn12view1 |
| practice mode with no fail state | recommended accessibility support citeturn12view1 |
| AV calibration screen | hardware and browser variability mitigation citeturn9view1turn15search1 |

Subtitles must include musically important state changes such as **“meter shifts,” “music intensifies,” “enemy chant left,”** and **“downbeat incoming.”** XAG 104 explicitly gives “music intensifies” as an example of meaningful caption content. citeturn17view1

Haptic cues may be added later for controller users, but they are strictly additive. XAG 110 says haptics should not be the only method of conveying information. citeturn17view2

Full-screen flashes above seizure-risk thresholds are banned. W3C notes that flashing above three times per second can trigger seizures if large and bright enough, and Microsoft’s photosensitivity guidance says games should be tested for those triggers. citeturn12view0turn13search2

## Delivery plan, QA, and acceptance gates

### Production phases

| Phase | Length | Exit condition |
|---|---:|---|
| pre-production | 4 weeks | approved combat prototype, locked schemas, locked art bible |
| vertical slice | 6 weeks | one full biome, one boss, one complete track pipeline, calibration working |
| content production | 8 weeks | full campaign content implemented and playable end-to-end |
| alpha | 4 weeks | all features complete, only bug fixing and balance left |
| beta | 3 weeks | browser matrix passes, accessibility matrix passes, save stability passes |
| release candidate | 2 weeks | no blocker defects, balance approved, legal/audio asset checks complete |

### QA matrix

QA must cover:

| Area | Mandatory test |
|---|---|
| timing | scheduler remains accurate under forced rendering load |
| browser support | Chrome, Edge, Firefox, Safari current stable desktop |
| saves | create, overwrite, delete, corruption recovery |
| calibration | offset persists and applies correctly after refresh |
| encounter data | invalid beatmaps fail validation before runtime |
| meter changes | boss phase transitions occur on exact authored barlines |
| accessibility | reduced motion, speed assist, captions, remap, contrast, practice mode |
| photosensitivity | no banned flashing patterns in default or boss VFX modes |

### Analytics events

Version one should emit anonymous local-or-consented telemetry for the following events:

- `audio_gate_completed`
- `calibration_completed`
- `battle_started`
- `ability_used`
- `judgment_perfect`
- `judgment_miss`
- `assist_mode_enabled`
- `sightread_used`
- `encounter_failed`
- `encounter_cleared`
- `boss_phase_reached`
- `save_loaded`

This event set is enough to tune hit windows, encounter spikes, and whether players are using the forecast mechanic as intended.

### Release gates

The product is not releasable unless all of the following are true:

1. All combat timing is driven by audio-authoritative scheduling, never by visual timers alone. That is a hard technical requirement because browser UI timers are not stable enough for musical judgment. citeturn9view1turn9view2  
2. The game boots into a user-gesture audio gate and never attempts prohibited autoplay behavior. citeturn15search1turn15search0  
3. The final boss reliably executes authored meter changes on bar boundary without drift. Tone transport and Web Audio scheduling support this model. citeturn8view1turn8view3  
4. Pixel art remains crisp at supported resolutions through low-resolution canvas scaling and `image-rendering: pixelated`. citeturn18view0  
5. Accessibility features listed above are present, discoverable, and functional, including captions for musically meaningful cues, adjustable speed, remapping, and reduced motion. citeturn17view0turn17view1turn12view1turn12view0  
6. Save data persists correctly in IndexedDB across refreshes and browser restarts. citeturn8view9turn11view2  

### Final implementation summary

The supplied concept is strong, but it only becomes production-ready if it is interpreted this way: **browser-first**, **turn-based**, **audio-clock-driven**, **pixel-art**, **mostly 4/4 onboarding**, **clave as accent family rather than fake meter**, **final boss as true meter-shift showcase**, and **baseline readable rhythm UI with spells that reveal future music rather than making music visible from nothing**. That interpretation is the most faithful version of the screenshots that is also technically robust, musically correct, and aligned with current accessibility guidance. citeturn8view5turn8view6turn8view7turn8view8turn9view1turn17view0turn12view1