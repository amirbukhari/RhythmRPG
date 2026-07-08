# E2E test suite

Real, committed Playwright coverage — replacing the ad hoc, uncommitted smoke
scripts used throughout early development. Run with:

```bash
npx playwright test --project=chromium   # the CI/deploy gate
npm run test:e2e                          # both browsers, local-only (see caveat below)
```

CI (`deploy-pages.yml`) gates on Chromium only. Firefox is configured and
runnable locally but is not part of the deploy gate — see the caveat below.

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

Real bugs found and fixed using this exact technique — now permanent
regression coverage:

1. `TextMenu` reset keyboard selection to the top item every time its labels
   were rebuilt, so sequential settings toggles silently hit the wrong item
   (`settings.spec.ts`).
2. Pausing a scene doesn't stop its keyboard listeners in Phaser; a paused
   underlying scene's menu kept reacting to the same keypresses as an
   overlay on top of it (`settings.spec.ts`).
3. Mixing Tone.js's AudioContext-time scheduled-callback parameter with
   Transport-position time silently broke the second boss phase transition
   (`boss-phases.spec.ts`).
4. `TextMenu` could double- or triple-fire a single physical keypress:
   Phaser's shared keyboard queue gets reprocessed by a scene's
   `KeyboardPlugin` on every subsequent keydown before the queue flushes at
   end-of-frame, and Phaser's own consecutive-only dedup guard doesn't cover
   that case. Only reachable with fast, unspaced input — which is exactly
   what automated `press()` calls do — fixed with a `WeakSet` of
   already-handled native `Event` objects (`settings.spec.ts`).
5. Re-opening `SettingsOverlay` a second time reused a stale menu left over
   from the first session, whose GameObjects Phaser had already destroyed on
   shutdown, threw, and permanently soft-locked the player behind a paused
   map — Phaser reuses one persistent Scene instance across stop/relaunch
   cycles, so state set after construction has to be explicitly reset in
   `create()` (`settings.spec.ts`).

Items 4 and 5 were originally misdiagnosed as sandbox-environment flakiness
(browser crashes, inconsistent failures) before being root-caused as real,
deterministic product bugs — see git history on this file and on
`settings.spec.ts` for the investigation. Don't reach for "environment
flakiness" as an explanation without first confirming a failure is genuinely
non-deterministic across many runs of the *exact same* input sequence in
isolation, the way items 4 and 5 turned out not to be.

## Known environment caveat

Running many sequential headless-WebGL browser sessions can still cause
occasional, genuinely non-deterministic browser crashes / resource
exhaustion (`Target page, context or browser has been closed`) unrelated to
the game's own code. `playwright.config.mjs` pins `workers: 1` to minimize
this. Chromium is reliably stable serially; when it does fail, a re-run
typically passes.

**Firefox is not just flakier — it currently fails outright.** Every Firefox
spec fails in `beforeAll`/boot (not an intermittent single-test flake) both
in this sandbox and, after fixing an unrelated CI infra issue (a runner-image
mismatch with the pinned Playwright version), on a real GitHub Actions
runner too. That rules out "constrained sandbox" as the sole explanation.
Root cause is unconfirmed (candidates: the `--autoplay-policy` workaround
used for Chromium has no Firefox equivalent beyond a preference that may not
be sufficient for `Tone.js`'s AudioContext unlock; or a Phaser/WebGL-in-
headless-Firefox incompatibility). Until root-caused, Firefox is excluded
from the CI/deploy gate (see `deploy-pages.yml`) so it can't block shipping;
it remains configured and runnable locally as a project for whoever picks up
that investigation.

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
