# Project Meterfall

A single-player, browser-based, pixel-art rhythm RPG. Combat is turn-based; every
action is executed as a timed phrase against an authored musical track, with a
final boss built around live time-signature changes.

**Play it live:** https://amirbukhari.github.io/RhythmRPG/ (auto-deployed from
`master`). One playable encounter exists today (opening biome, one enemy) —
see [§20 of the PRD](docs/product/PRD.md#20-implementation-status-as-of-2026-07-08)
for exactly what's built vs. still open.

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
  main.ts       Phaser app entry point, fixed scene stack
  config/       engine/canvas configuration
  scenes/       all 9 scenes are real (not stubs) -- Boot/AudioGate/MainMenu/Save/
                Calibration/Map/Battle/Results/SettingsOverlay
  state/        GameContext -- cross-scene singleton (save profile, analytics, handoffs)
  systems/
    audio/         TransportClock (Tone.Transport wrapper), Calibration math, BeatmapSonifier
    combat/        CombatController, JudgmentSystem, PhraseTiming (all unit tested, Phaser-free)
    persistence/   IndexedDB SaveManager
    accessibility/ day-one accessibility settings model, functionally wired throughout
    analytics/     consent-gated event tracking (PRD §14)
  data/
    schemas/      TypeScript types for all schemas, including three internal ones
                   (Enemy/HeroClass/CampaignNode) the PRD's three canonical schemas don't cover
    content/      authored abilities (12), one beatmap, one encounter, one enemy,
                   four hero classes, one campaign node -- real but minimal, see PRD §20.2
  ui/           TextMenu -- shared keyboard+pointer menu component used by every menu scene

assets/
  sprites/      final game sprites (still placeholder-only, not yet rendered in-engine)
  audio/        music/sfx/stems (empty -- battle audio is currently a scratch Tone.js
                sonifier, not the real soundtrack; see PRD §20.2)
  reference/    pre-PRD reference material that carries forward as production basis (PRD §11.4)

tests/
  unit/         67 tests: JudgmentSystem, PhraseTiming, CombatController, ContentLoader/
                Registry, SaveManager, Analytics, Calibration, BeatmapSonifier
  e2e/          empty -- all E2E verification so far was ad hoc, uncommitted Puppeteer
                scripts against a local dev server (PRD §20.2 names this as the
                highest-value next testing investment)

tools/
  gbmusic/      audio -> Game Boy (LSDJ) chiptune conversion pipeline (Python, separate from the game's toolchain)
```

## Getting started

```bash
npm install
npm run dev        # starts Vite dev server
npm run typecheck  # tsc --noEmit
npm test           # vitest run -- 67 unit tests
npm run build       # production build to dist/
```

Play through: audio-unlock gate → main menu → create a save → AV calibration
(tap along to the pulse) → campaign map → the one authored battle (keyboard:
1/2/3 picks an ability for the active hero, Space hits the beat) → results.
Settings are reachable from the main menu or map screen and are fully
functional, not placeholders.

## Non-negotiable architecture rule

All gameplay timing judgment must be derived from `TransportClock`
(`src/systems/audio/TransportClock.ts`, wrapping `Tone.Transport`) — never from
`setTimeout`, `setInterval`, or `requestAnimationFrame`. See PRD §10.2. This is
enforced in practice today: `BattleScene`'s judgment and `BeatmapSonifier`'s
audible playback both read from the same transport clock.
