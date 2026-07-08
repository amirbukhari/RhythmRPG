# Project Meterfall

A single-player, browser-based, pixel-art rhythm RPG. Combat is turn-based; every
action is executed as a timed phrase against an authored musical track, with a
final boss built around live time-signature changes.

**Play it live:** https://amirbukhari.github.io/RhythmRPG/ (auto-deployed from
`master`). The full vertical slice is playable today: a 5-node campaign —
opening biome → 3 mid-biome encounters (including a multi-enemy clave-accent
fight) → a real 3-phase final boss with live meter changes — see
[§20 of the PRD](docs/product/PRD.md#20-implementation-status-as-of-2026-07-08)
for exactly what's built vs. still open (art and real music are the two big
remaining pieces).

Codename only — see [Open Questions](docs/product/PRD.md#18-open-questions) for
naming status.

## Start here

- **[Product Requirements Document](docs/product/PRD.md)** — the source of truth for scope, requirements, architecture, and release gates. **[§20 Implementation Status](docs/product/PRD.md#20-implementation-status-as-of-2026-07-08)** is the current build-vs-spec snapshot — read that first if you're picking this up.
- [Deep research report](docs/research/deep-research-report.md) — rationale and citations behind the PRD's design decisions.
- [Data schemas](docs/technical/schemas/) — beatmap, ability, and encounter JSON schemas, mirrored as TypeScript types in `src/data/schemas/`.
- [gbmusic pipeline](tools/gbmusic/README.md) — converts a mixed audio track into a Game Boy (LSDJ) chiptune project; drafts exist but aren't wired into the game yet (PRD §20.2).
- [Music direction](docs/design/music-direction.md) — which master-track slice feeds each battle-track stage.

## Repository structure

```
docs/
  product/      PRD (source of truth) + §20 implementation status
  research/     research backing the PRD
  technical/    JSON schemas for data-driven content
  design/       music-direction.md (written); art bible, narrative bible (not yet written)
  qa/           test plan, accessibility checklist, release-gate sign-off (not yet written)

src/
  main.ts       Phaser app entry point, fixed scene stack, dev-only debug hook (window.__meterfallDebug)
  config/       engine/canvas configuration
  scenes/       all 9 scenes are real (not stubs) -- Boot/AudioGate/MainMenu/Save/
                Calibration/Map/Battle/Results/SettingsOverlay
  state/        GameContext -- cross-scene singleton (save profile, analytics, handoffs)
  systems/
    audio/         TransportClock (Tone.Transport wrapper), Calibration math, BeatmapSonifier
    combat/        CombatController, JudgmentSystem, PhraseTiming, MeterSequence (live meter
                   changes), Forecast (Sightread) -- all unit tested, Phaser-free
    persistence/   IndexedDB SaveManager
    accessibility/ day-one accessibility settings model, functionally wired throughout
    analytics/     consent-gated event tracking (PRD §14)
    progression/   Relics -- real mechanical effects applied at battle start
  data/
    schemas/      TypeScript types for all schemas, including four internal ones
                   (Enemy/HeroClass/CampaignNode/BossPhaseConfig) the PRD's three canonical
                   schemas don't cover
    content/      12 abilities, 7 beatmaps, 5 encounters, 7 enemies, 4 hero classes,
                   a 5-node campaign, and a 3-phase boss config -- see PRD §20.1
  ui/           TextMenu -- shared keyboard+pointer menu component used by every menu scene

assets/
  sprites/      final game sprites (still placeholder-only, not yet rendered in-engine)
  audio/        music/sfx/stems (empty -- battle audio is currently a scratch Tone.js
                sonifier, not the real soundtrack; see PRD §20.2)
  reference/    pre-PRD reference material that carries forward as production basis (PRD §11.4)

tests/
  unit/         94 tests: JudgmentSystem, PhraseTiming, MeterSequence, Forecast, CombatController,
                Relics, ContentLoader/Registry, SaveManager, Analytics, Calibration
  e2e/          11 committed Playwright specs (Chromium + Firefox) -- boot/calibration/reload,
                battle mechanics, the boss's 3-phase mechanic, settings regressions.
                See tests/e2e/README.md for a documented sandbox-specific flakiness caveat.

tools/
  gbmusic/      audio -> Game Boy (LSDJ) chiptune conversion pipeline (Python, separate from the game's toolchain)
```

## Getting started

```bash
npm install
npm run dev        # starts Vite dev server
npm run typecheck  # tsc --noEmit
npm test           # vitest run -- 94 unit tests
npm run test:e2e   # playwright test -- 11 e2e specs (Chromium + Firefox)
npm run build      # production build to dist/
```

Play through: audio-unlock gate → main menu → create a save → AV calibration
(tap along to the pulse) → campaign map → 5 chained encounters ending in a real
3-phase boss (keyboard: 1/2/3 picks an ability, arrow keys + 1/2/3 pick a
target when more than one enemy is alive, Space hits the beat) → results, with
real relic and skill-unlock rewards. Settings are reachable from the main menu
or map screen and are fully functional, not placeholders.

## Non-negotiable architecture rule

All gameplay timing judgment must be derived from `TransportClock`
(`src/systems/audio/TransportClock.ts`, wrapping `Tone.Transport`) — never from
`setTimeout`, `setInterval`, or `requestAnimationFrame`. See PRD §10.2. This is
enforced in practice today: `BattleScene`'s judgment, the boss's live meter
changes (`MeterSequence`), and `BeatmapSonifier`'s audible playback all read
from the same transport clock.
