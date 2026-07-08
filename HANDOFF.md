# Handoff notes — paused 2026-07-08

Session paused at the user's request. This file is the single place to look
when picking this project back up. Read this before doing anything else.

## The standing `/goal` (now cancelled)

A `/goal` was set earlier in this session:

> implement the PRD to an enterprise standard. it should be perfect.

This was cancelled at the user's explicit request in this session (paused,
then asked to record notes and cancel the goal) because it could not be
satisfied by continued implementation work alone — see "Why the goal was
cancelled" below. If you want to resume pushing toward it, re-set it
explicitly and decide first whether to scope it down (see that section).

## Where the code actually is

Latest commit on `master`: `348a6c8` — "Fix critical first-run blocker:
calibration was keyboard-only".

- PRD: `docs/product/PRD.md`, currently **Draft v4.4**, status line says
  "pending stakeholder sign-off." Its own §20 ("Implementation Status") is
  the authoritative, up-to-date snapshot of what's built vs. open — read
  that section first, it's kept current on purpose.
- 102 unit tests passing (`npm test`), Chromium e2e suite green (12 specs,
  `npx playwright test --project=chromium`), production build succeeds
  (`npm run build`), typecheck clean (`npm run typecheck`).
- Full rhythm-combat engine: turn-based battles synced to an audio clock
  (`Tone.Transport`, never `setTimeout`), 5-node campaign, a 3-phase boss
  with live meter changes (5/4→7/8→4/4→3/4), tier-2 abilities per role,
  functional relics, a visual (circles-on-a-path) campaign map, real
  per-node encounter variety on 1 of 5 nodes (`encounterPool`).
- Two real, previously-hidden bugs found and fixed this session:
  1. `TextMenu` could double/triple-fire a single physical keypress
     (Phaser's shared keyboard queue reprocessing) — fixed in
     `src/ui/components/TextMenu.ts`.
  2. Re-opening `SettingsOverlay` a second time crashed and permanently
     soft-locked the player (stale reference to already-destroyed
     GameObjects) — fixed in `src/scenes/SettingsOverlay.ts`.
  3. **Most important, found via real user testing on the live deploy**:
     `CalibrationScene` — the very first mandatory, unskippable screen —
     only accepted keyboard taps, not clicks/pointer. Anyone who clicked
     instead of pressing a physical key got completely stuck with zero
     feedback. Fixed in `src/scenes/CalibrationScene.ts` (added a
     `pointerdown` handler). Also reworded `AudioGateScene`'s misleading
     "PRESS ANY KEY TO START AUDIO" text (read as "music will play," but
     no screen in the game ever plays music on its own).

## ⚠️ Known unresolved issue: last deploy may not be live

As of commit `348a6c8`, CI's `build` job (tests/typecheck/e2e/build) passed
green, but the `deploy` job's `actions/deploy-pages@v4` step **failed**
(fast failure, ~1s — looked like a transient GitHub-side hiccup, not a code
problem; no deeper logs were accessible without repo admin rights). This
means **the live GitHub Pages site may still be serving the previous build
without the calibration fix.**

**First thing to do when resuming:** check
`https://github.com/amirbukhari/RhythmRPG/actions` for the latest "Deploy to
GitHub Pages" run against `348a6c8` (or whatever is on `master` by then). If
it's still failed/stale, either push an empty/trivial commit to retrigger,
or use `workflow_dispatch` (the workflow supports manual re-run — see
`.github/workflows/deploy-pages.yml`).

## Why the goal was cancelled

The repeated stop-hook rejections all cited the same PRD §20.2 gap list.
Four of five remaining gaps are blocked on resources that don't exist in
this environment, not on more engineering effort:

1. **Art** — placeholder only, not a final art-bible pass. Blocked on real
   art production (no image-generation tool is available here).
2. **Music** — `BeatmapSonifier`'s synth blips are scratch sonification,
   not the real soundtrack. The `.lsdsng` chiptune drafts in
   `tools/gbmusic/` were never rendered to playable audio — investigated
   via PyBoy 2.4.1, which has no audio-buffer/WAV export API. Blocked on a
   working Game Boy audio-rendering path existing at all.
3. **Firefox e2e** — every Firefox spec fails in `beforeAll`/boot, on both
   this sandbox and real CI. Root cause unconfirmed; excluded from the
   CI/deploy gate (Chromium-only). Blocked on someone with a
   non-sandboxed environment to bisect against.
4. **QA matrix (§16)** — unexecuted on real, non-headless browsers/devices.
   Blocked on physical device access this environment doesn't have.
5. **Content depth** — only 1 of 5 campaign nodes (`mid_2`) has real
   per-visit encounter variety (`encounterPool`); the other 4 are still a
   single fixed fight each, and there's no branching path anywhere in the
   campaign graph. This one **is** pure engineering effort with no
   external blocker — see the "Straightforward next steps" section below
   if you want to keep closing this one specifically.

Given 4 of 5 gaps genuinely cannot be closed by more work in this
environment, the "perfect enterprise standard" condition as originally
phrased could not terminate. If you re-set a goal, consider scoping it to
what's actually achievable here (e.g. "close gap 5 to N/5 nodes" or "resolve
the Pages deploy issue") rather than "perfect."

## New scope decision from this session: add a walkable overworld

Separately from the goal/PRD gaps: the user tried the live game and raised
two real concerns:
1. Got stuck at calibration (see bug #3 above — now fixed).
2. **"Is this a text-based game? I wanted a beautiful pixel art game I
   could run around in."** — the current game is a rhythm-*combat* RPG
   (turn-based battles between a text/shape-based node-select map), not an
   explorable overworld. This was the original scope from the start of the
   project (per the PRD's own decisions), but it wasn't what the user
   expected when actually playing it.

Asked directly, the user chose: **add a real walkable pixel-art overworld**
(tilemap, movement, collision, camera-follow) to replace the current
text-menu map screen, while keeping the existing rhythm-battle engine
completely unchanged — classic JRPG structure (walk around → battle
triggers → back to the overworld).

**Important constraint already surfaced to the user and agreed:** there is
no image-generation tool available in this environment. This work can
deliver a real, working overworld *mechanic* (tilemap, movement, collision,
camera, encounter triggering) but not "beautiful" original art — visuals
would be programmatically-generated placeholder tiles (ImageMagick/Pillow
are both available) plus the existing unused `Amir Run.png` spritesheet
(8 real walk-cycle frames, currently unused) for a walking animation. Real
art quality is still blocked the same way battle art is (§20.2 item 1).

This was fully investigated and planned (two Explore agents + one Plan
agent) but **zero code was written** — session was paused right as planning
finished. Full plan preserved below so no re-investigation is needed.

### Full overworld implementation plan (ready to execute when resumed)

**Scope**: Replace `src/scenes/MapScene.ts` with a new
`src/scenes/OverworldScene.ts`. Player moves a character around a tilemap;
walking onto an enemy/node marker triggers `BattleScene` (unchanged). One
map covers all 5 current campaign nodes for v1.

**1. Tilemap approach** — Tiled-JSON format + a script-generated flat-color
tileset PNG (Python/Pillow, run once, committed as a real asset).
- Tileset: `assets/tilemaps/overworld_tileset.png`, 16×16 tiles, one row of
  4 tiles (grass/path=walkable, water/rock=obstacle via a per-tile
  `collides: true` custom property in the Tiled tileset JSON).
- Tilemap: `assets/tilemaps/overworld.json`, orthogonal, 16×16 tiles,
  ~40×24 map (640×384px, bigger than the 320×180 viewport so
  camera-follow/bounds actually matter). Two layers: `ground` (tile layer)
  and `markers` (**object layer**, one point per campaign node with a
  custom `nodeId` string property, plus one `spawn` point) — object layer
  chosen over special tile GIDs because it lets each marker carry an
  arbitrary string property directly.
- Load via `this.load.image(...)` + `this.load.tilemapTiledJSON(...)` in a
  new scene-local `preload()` (first one in the codebase — today only
  `BootScene` preloads anything globally). Build with
  `this.make.tilemap(...)` / `map.addTilesetImage(...)` /
  `map.createLayer(...)`.

**2. Movement & collision** — manual tile-snapped 4-directional movement,
**no Arcade/Matter physics** (none configured today in
`src/config/GameConfig.ts`; adding a physics system for a feature that
needs none of what it buys is unnecessary blast radius). New pure module
`src/systems/overworld/OverworldMovement.ts`:
- `stepTarget(col, row, dir): {col, row}` — pure grid math.
- `isWalkable(...)` — pure lookup against a `boolean[][]` grid built once
  from the tilemap's `collides` properties.
Both fully unit-testable, no Phaser dependency (mirrors
`src/systems/progression/CampaignSelection.ts`'s established style).
Scene-side: track `{col,row}` + a `moving` flag; on input, compute target
tile, check walkability, tween the sprite (`this.tweens.add(...)`,
~160ms) between tile centers; block new input until the tween completes.
No input buffering for v1. New input surface (arrow keys/WASD) — does
**not** reuse `settings.keyBindings.tap` (that's the battle-timing remap,
unrelated).

**3. Camera** — `cameras.main.startFollow(playerSprite, true, 1, 1)`,
`setRoundPixels(true)` (crisp pixel art), `setBounds(0, 0, map.widthInPixels,
map.heightInPixels)`.

**4. Encounter triggering** — walk-onto-marker (no separate confirm key).
Extract the reachability/status logic that `MapScene.reachableNodeIds`
already computes into a new pure module
`src/systems/progression/CampaignReachability.ts`:
```ts
export type NodeStatus = "locked" | "unlocked" | "cleared";
export function reachableNodeIds(campaign, currentNodeId): Set<string>
export function nodeStatus(campaign, progress, nodeId): NodeStatus
```
Parameterized on plain data (not the `ContentRegistry`/`GameContext`
singletons) for direct unit testing, same style as `CampaignSelection.ts`.
On landing on an `unlocked` marker's tile: call the existing
`resolveEncounterId(node)` (`src/systems/progression/CampaignSelection.ts`,
unchanged), set `GameContext.pendingEncounterId`/`pendingNodeId` exactly as
`MapScene` does today, `this.scene.start("BattleScene")`. `locked`/`cleared`
markers are a no-op on touch (v1).

**5. Scene rename** — rename both the Phaser scene key and the class/file
to `OverworldScene` (not just a new key on the same class) since this is a
full behavioral rewrite, not a tweak. All confirmed touch points:
- `src/main.ts` (scene import + array)
- `src/scenes/OverworldScene.ts` (new, replaces `MapScene.ts`)
- `src/scenes/SaveScene.ts:33`
- `src/scenes/CalibrationScene.ts:91` (line number will shift slightly
  after this session's pointerdown-handler fix — re-check)
- `src/scenes/ResultsScene.ts` (two call sites, ~lines 20 and 57)
- `src/scenes/BattleScene.ts:89` (no-pending-encounter guard-clause
  redirect)
- `src/state/GameContext.ts:24` (doc comment only)
- `tests/e2e/helpers.ts` (`createSaveAndCalibrate`, `jumpToEncounter`,
  `openSettingsFromMap` all reference `"MapScene"` literally)
- `tests/e2e/boot-flow.spec.ts` and `tests/e2e/settings.spec.ts` (literal
  `"MapScene"` strings — note `boot-flow.spec.ts` gained a new pointer-tap
  calibration test this session, check it too)

Settings overlay: bind `ESC` in `OverworldScene` to
`this.scene.launch("SettingsOverlay", { returnTo: "OverworldScene" })`
(SettingsOverlay is already fully generic on `returnTo`, no changes needed
there) plus a small always-visible HUD hint text.

**6. Return-from-battle** — reappear at the node just fought (not a fixed
spawn point), since nodes lie along a path and forcing backtracking after
every fight has no benefit. Problem: `GameContext.pendingNodeId` is nulled
inside `BattleScene.endBattle()` before `ResultsScene` even runs, and
`GameContext.lastBattleResult` is nulled at the top of `ResultsScene.create()`
before `OverworldScene` ever runs — neither survives today. Fix: add
`returnToNodeId: string | null` to `GameContext`; in `BattleScene.endBattle()`
capture the finishing `pendingNodeId` into it before the existing clear
(works for both victory and defeat); in `OverworldScene.create()` read it,
clear immediately, spawn there if it matches a marker, else fall back to
the map's `spawn` object.

**7. Explicitly punted for v1** — branching paths (`next[1+]` stays
unimplemented, matches today's behavior exactly), multiple biomes/maps (one
map for all 5 nodes), NPCs/dialogue/secrets/items, real 4-directional
character art (only one run-cycle strip exists; left = `setFlipX(true)` on
the same frames, up/down reuse the same animation unflipped — a visible
placeholder-art limitation, not a bug), overworld movement key remapping,
re-fighting cleared nodes, locked-node feedback beyond a no-op, input
buffering/queued movement.

**8. Testing plan**
- Unit (Vitest, Phaser-free): `tests/unit/campaign-reachability.test.ts`
  (new, mirrors `campaign-selection.test.ts`'s style) and
  `tests/unit/overworld-movement.test.ts` (new; `stepTarget`/`isWalkable`
  on plain data).
- e2e (Playwright, via the existing `window.__meterfallDebug` hook):
  pixel-perfect keyboard pathing across a real map is slow/flaky in
  automation (the existing suite already avoids exactly this via
  `jumpToEncounter`'s direct-state-mutation shortcut). Recommend adding two
  small dev-only seams to `OverworldScene`: a readable
  `playerGridPosition` (`{col,row}`), and a `debugTeleportToNode(nodeId)`
  helper that snaps the player onto a marker and re-runs the trigger check
  — same spirit as the existing debug hook, same `import.meta.env.DEV`
  gating. New `tests/e2e/overworld.spec.ts`: boot → assert
  `OverworldScene` active → real arrow-key movement asserted via
  `playerGridPosition` → teleport-to-node → assert `BattleScene` starts →
  after battle, assert return lands back at the fought node's tile.

**9. Rollout sequencing** (small, independently verifiable steps — build →
unit test → e2e → screenshot → commit → push, matching this project's
established discipline throughout):
1. Static map render only (tileset+tilemap load, camera bounds, no player
   sprite/movement yet). Verify via screenshot.
2. Player sprite (load `Amir Run.png` as a spritesheet, `frameWidth: 128,
   frameHeight: 128`) + movement + collision (`OverworldMovement.ts` +
   its unit tests). Verify via screenshot/manual play.
3. Encounter markers + `CampaignReachability.ts` + battle trigger +
   `returnToNodeId` return flow. Verify by manually walking into a node
   and completing a battle round-trip.
4. Full rewire (all `"MapScene"` → `"OverworldScene"` touch points from
   §5), delete old `MapScene.ts`, ESC-to-settings binding, debug seams,
   `overworld.spec.ts` + fix the existing 3 specs' literals. Verify: full
   `npm run build` + `npx vitest run` + `npx playwright test
   --project=chromium` all green, plus a manual full-loop screenshot
   walkthrough (boot → overworld → battle → results → overworld).

## Straightforward next steps if resuming without the overworld work

If the overworld isn't the priority when this resumes, the cheapest
remaining wins (pure engineering, no external blocker) are, in order:
1. Verify/fix the Pages deploy issue above.
2. Extend `encounterPool` variety to the other 4 campaign nodes (currently
   only `mid_2` has it) — see `src/data/content/campaign/opening_biome.json`
   and `src/systems/progression/CampaignSelection.ts` for the pattern
   established this session.
3. Investigate the Firefox e2e root cause properly (candidates already
   noted in `tests/e2e/README.md`: `Tone.js` AudioContext unlock not firing
   under headless Firefox, or a Phaser/WebGL incompatibility).
