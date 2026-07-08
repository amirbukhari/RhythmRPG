# Project Meterfall

A single-player, browser-based, pixel-art rhythm RPG. Combat is turn-based; every
action is executed as a timed phrase against an authored musical track, with a
final boss built around live time-signature changes.

Codename only — see [Open Questions](docs/product/PRD.md#18-open-questions) for
naming status.

## Start here

- **[Product Requirements Document](docs/product/PRD.md)** — the source of truth for scope, requirements, architecture, and release gates.
- [Deep research report](docs/research/deep-research-report.md) — rationale and citations behind the PRD's design decisions.
- [Data schemas](docs/technical/schemas/) — beatmap, ability, and encounter JSON schemas, mirrored as TypeScript types in `src/data/schemas/`.

## Repository structure

```
docs/
  product/      PRD (source of truth)
  research/     research backing the PRD
  technical/    JSON schemas for data-driven content
  design/       art bible, narrative bible, music direction (pre-production deliverables)
  qa/           test plan, accessibility checklist, release-gate sign-off

src/
  main.ts       Phaser app entry point, fixed scene stack
  config/       engine/canvas configuration
  scenes/       one file per scene in the fixed scene stack (PRD §10.6)
  systems/
    audio/         Tone.js Transport wrapper — the single source of timing truth
    combat/        turn structure and judgment-window logic
    persistence/    IndexedDB save manager
    accessibility/  day-one accessibility settings model
  data/
    schemas/      TypeScript types mirroring docs/technical/schemas/
    content/      authored beatmaps/abilities/encounters (empty — populated during production)
  ui/           shared UI components (battle HUD, phrase lane, etc.)

assets/
  sprites/      final game sprites (currently placeholder-only, see assets/sprites/heroes/placeholder/README.md)
  audio/        music/sfx/stems (empty — populated per PRD §11.2)
  reference/    pre-PRD reference material, not shippable as-is

tests/
  unit/         unit tests (judgment windows, schema validation, save manager)
  e2e/          end-to-end browser tests (audio gate, calibration persistence, boss meter transitions)
```

## Getting started

```bash
npm install
npm run dev        # starts Vite dev server
npm run typecheck  # tsc --noEmit
npm run build       # production build to dist/
```

The scene stack currently boots through `BootScene → AudioGateScene → MainMenuScene`
with stub `create()` methods — see inline `TODO`s and the PRD sections referenced
in each file's docblock before implementing.

## Non-negotiable architecture rule

All gameplay timing judgment must be derived from `TransportClock`
(`src/systems/audio/TransportClock.ts`, wrapping `Tone.Transport`) — never from
`setTimeout`, `setInterval`, or `requestAnimationFrame`. See PRD §10.2.
