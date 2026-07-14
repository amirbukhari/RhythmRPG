# The Drowned Chorus

A single-player, browser-based, top-down **rhythm-action RPG**. You lead
Inhalants — a four-piece band — through one continuous hand-authored drowned
world of five regions. Fights happen **in the world**: walk into a foe and the
camera locks to a room of the actual overworld around it, where a real-time
action fight runs — momentum movement, dashes with i-frames, frame-data
attacks, hitstun and damage-scaled knockback, on-beat parries — with actions
timed to the beat empowered. The soundtrack is six real recorded Inhalants
tracks; the art is in the *Hyper Light Drifter* register.

**Play it live:** https://amirbukhari.github.io/RhythmRPG/ (auto-deployed from
`master`).

*(Historical codename: Project Meterfall. The game began as a turn-based
rhythm RPG and pivoted twice — to real-time action combat at PRD v6.0 and to
first-class exploration at v7.0. The retired turn-based code remains in-repo
for regression coverage only.)*

## Start here

- **[Product Requirements Document](docs/product/PRD.md)** — v8.0, the source
  of truth for scope, requirements, architecture, and release gates.
  **[§20 Implementation Status](docs/product/PRD.md#20-implementation-status-as-of-2026-07-14-v80-re-cut)**
  is the current build-vs-spec snapshot — read that first if you're picking
  this up. The #1 open item is **beat truth** (PRD §8.3): syncing the judged
  beat to the actually-playing track.
- [PRD audit (2026-07-14)](docs/product/prd-audit-2026-07-14.md) — the
  line-by-line spec-vs-build audit that drove the v8.0 rewrite.
- [AAA art audit](docs/design/aaa-audit.md) — the screen-by-screen art review
  and its burn-down status.
- [World bible](docs/design/world-bible.md) · [art bible](docs/design/art-bible.md)
  · [art prompts](docs/design/art-prompts.md) — narrative canon and the art
  pipeline's per-slot catalog.
- [Data schemas](docs/technical/schemas/) — beatmap/encounter/ability JSON
  schemas, mirrored as TypeScript types in `src/data/schemas/`.
- [Deep research report](docs/research/deep-research-report.md) — rationale
  and citations behind the original design decisions.

## Repository structure

```
docs/
  product/      PRD v8.0 (source of truth) + the 2026-07-14 PRD audit
  research/     research backing the PRD
  technical/    JSON schemas for data-driven content
  design/       world bible, art bible, art-prompt catalog, AAA art audit,
                music-direction (historical)

src/
  main.ts       Phaser entry, scene stack, touch-controls init, debug hook
  scenes/       Boot / AudioGate / MainMenu / Save / Calibration / Results /
                SettingsOverlay, and the product path:
                OverworldScene + overworld/WorldFight.ts (in-world fights) +
                env/ArenaComposer.ts (venues composed into the map).
                BattleScene + ActionBattleScene are RETIRED from the product
                path (registered for regression coverage only — PRD §10.6)
  systems/
    action/        ActionCombat.ts -- the Phaser-free real-time sim (frame data,
                   hitstun, knockback+DI, parry, cancels, obstacles)
    audio/         SongPlayer (the six-track soundtrack), TransportClock,
                   Calibration, BeatmapSonifier (to become an opt-in tick)
    combat/        RETIRED turn-based systems (CombatController, JudgmentSystem,
                   MeterSequence, Forecast) -- pending §8.7 re-implementation
    persistence/   IndexedDB SaveManager
    accessibility/ settings model
    analytics/     consent-gated local event tracking (PRD §14)
    progression/   Relics, CampaignSelection, CampaignReachability
    overworld/     OverworldMovement -- pure tile-step/walkability math
  ui/           TouchControls (mobile), TextMenu, Backdrop
  data/
    schemas/      TS types incl. internal Enemy/HeroClass/CampaignNode/BossPhaseConfig
    content/      campaign (5 nodes, encounter pools), 9 encounters, 4 foes,
                  beatmaps (gaining real per-track beat maps -- PRD §8.3)

assets/
  sprites/band/       the four playable Inhalants (AI-generated, one register)
  sprites/enemies/    slime, drifter, elite wraith + the colossal Conductor
  sprites/env/        5 biome venue kits + shared pieces (28 total)
  sprites/overworld/  landmarks, ambient NPCs, props
  tilemaps/           the 130x34 five-region world (BFS-validated generator)
  audio/              the six Inhalants MP3s (lazy-loaded; ~45MB never loads up front)
  reference/          archived historical material (pre-band art, gbmusic drafts)

tests/
  unit/         145 tests across 16 files (action sim, timing, persistence,
                content validation, progression, retired-path coverage)
  e2e/          7 Playwright spec files (18 tests, Chromium gate): boot/
                calibration/persistence, overworld + in-world fight, obelisk
                save, settings regressions, art-audit captures.
                Firefox is excluded pending root-cause (PRD §20.2)

tools/
  pixelart/     the art pipeline: AI generation (generate_ai.py) + import/
                cleanup/downscale passes + procedural fallbacks; regenerate
                with python3 tools/pixelart/generate_all.py
  overworld/    deterministic five-region world generator
  gbmusic/      HISTORICAL: audio -> Game Boy chiptune pipeline (superseded by
                the real recorded soundtrack at PRD v7.7)
```

## Getting started

```bash
npm install
npm run dev        # Vite dev server
npm run typecheck  # tsc --noEmit
npm test           # vitest run -- 145 unit tests
npm run test:e2e   # playwright test -- Chromium e2e gate
npm run build      # production build to dist/
```

Play through: audio-unlock gate → main menu → create a save → AV calibration →
the drowned world. **WASD/arrows** to move (the band follows you). Walk up to
the foe standing at each region's venue to start its in-world fight:
**J** light, **K** heavy, **L** special (Focus), **I** parry (on-beat!),
**Shift** dash. **E** interacts — rest at a save-obelisk, read an echo. On
mobile, an on-screen thumbstick and action buttons appear. Settings (ESC) are
fully functional: assist windows, game speed, reduced motion, volumes,
calibration.

## Non-negotiable architecture rules

1. **Audio-clock authority (PRD §10.2):** gameplay timing judgment derives from
   `TransportClock` (`src/systems/audio/TransportClock.ts`) — never from
   `setTimeout` / `setInterval` / `requestAnimationFrame`.
2. **Beat truth (PRD §8.3, release gate #1a — in progress):** the judged beat
   must be the beat of the *actually playing* track, via authored per-track
   beat maps. This is the current top engineering priority; until it lands,
   the judged beat is a beatmap BPM that the streamed songs are not synced to.
