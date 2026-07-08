# E2E test suite

Real, committed Playwright coverage (Chromium + Firefox) — replacing the ad
hoc, uncommitted smoke scripts used throughout early development. Run with:

```bash
npm run test:e2e              # both browsers
npx playwright test --project=chromium   # one browser
```

## Why these tests look the way they do

The game is a canvas-rendered Phaser app: there is no DOM to query for game
state (no buttons, no text nodes). Every spec drives the game via real
keyboard/pointer input — the same inputs a player uses — and asserts against
`window.__meterfallDebug` (`src/main.ts`), a dev-only hook exposing the live
Phaser `SceneManager` and `GameContext` singleton. It's stripped from
production builds via `import.meta.env.DEV`, so it never ships.

For the boss-phase tests specifically: real-time rhythm input can't be
driven precisely enough through browser automation to actually grind a boss
down through gameplay. Those tests directly set enemy HP through the debug
hook and assert that crossing a threshold triggers the correct phase
transition — that's the actual thing under test (does the trigger work),
not whether scripted input can win a rhythm minigame.

## What this suite already caught

Three real bugs were found and fixed using this exact technique before the
suite existed (as ad hoc scripts) — now permanent regression coverage:

1. `TextMenu` reset keyboard selection to the top item every time its labels
   were rebuilt, so sequential settings toggles silently hit the wrong item
   (`settings.spec.ts`).
2. Pausing a scene doesn't stop its keyboard listeners in Phaser; a paused
   underlying scene's menu kept reacting to the same keypresses as an
   overlay on top of it (`settings.spec.ts`).
3. Mixing Tone.js's AudioContext-time scheduled-callback parameter with
   Transport-position time silently broke the second boss phase transition
   (`boss-phases.spec.ts`).

## Known environment caveat

In this sandboxed development VM specifically, running many sequential
headless-WebGL browser sessions causes occasional browser crashes / resource
exhaustion (`Target page, context or browser has been closed`) unrelated to
the game's own code — confirmed by extensive isolation testing (varying
worker count, boot redundancy, dev vs. production build, raw Playwright API
vs. the test runner). Firefox in particular is flakier here than Chromium.
`playwright.config.mjs` pins `workers: 1` to minimize this. A properly
resourced CI runner (not a constrained sandbox) is expected to be more
stable; treat sandbox-local flakiness here as an infrastructure signal, not
a product regression, and re-run before concluding otherwise.

## Structure

- `helpers.ts` — shared flows (`bootToMap`, `jumpToEncounter`, scene-state
  getters). `bootToMap` includes the full 8-tap calibration, which is real
  wall-clock time (~5s) -- specs that need multiple scenarios share one boot
  per file (`test.describe.configure({ mode: "serial" })` + `beforeAll`)
  rather than re-booting per test.
- `boot-flow.spec.ts` — boot through calibration to the map; save persistence across a reload.
- `battle-basics.spec.ts` — party/enemy setup, ability timing stage transitions, auto-miss safety net, multi-enemy targeting.
- `boss-phases.spec.ts` — the three-phase meter-change mechanic (PRD §8.7 / release gate #3).
- `settings.spec.ts` — the two regression bugs above.
