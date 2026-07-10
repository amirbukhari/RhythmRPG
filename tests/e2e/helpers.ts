import type { Page } from "@playwright/test";

/**
 * The game is a canvas-rendered Phaser app -- there's no DOM to query for
 * game state. Every helper here drives real keyboard/pointer input (the
 * same inputs a player uses) and asserts against window.__meterfallDebug
 * (src/main.ts, stripped from production builds), which exposes the live
 * Phaser SceneManager and GameContext singleton for deterministic checks.
 */

type Debug = {
  game: Phaser.Game;
  GameContext: typeof import("../../src/state/GameContext").GameContext;
};

declare global {
  interface Window {
    __meterfallDebug: Debug;
  }
}

export async function isSceneActive(page: Page, key: string): Promise<boolean> {
  return page.evaluate((key) => window.__meterfallDebug.game.scene.isActive(key), key);
}

export async function waitForScene(page: Page, key: string): Promise<void> {
  await page.waitForFunction((key) => window.__meterfallDebug?.game?.scene?.isActive(key), key);
}

/** Clicks to satisfy the mandatory user-gesture audio unlock (PRD §10.4), then waits for the main menu. */
export async function passAudioGate(page: Page): Promise<void> {
  await waitForScene(page, "AudioGateScene");
  await page.mouse.click(160, 90);
  await waitForScene(page, "MainMenuScene");
}

/** From the main menu: creates a new save and completes the 8-tap calibration, landing on the map. */
export async function createSaveAndCalibrate(page: Page): Promise<void> {
  await page.keyboard.press("Enter"); // Start/Continue -> SaveScene
  await waitForScene(page, "SaveScene");
  await page.keyboard.press("Enter"); // + New Save -> CalibrationScene
  await waitForScene(page, "CalibrationScene");

  for (let i = 0; i < 8; i++) {
    await page.keyboard.press("Space");
    await page.waitForTimeout(600); // real calibration BPM is 100 -> 600ms/beat
  }
  await waitForScene(page, "MapScene");
}

/** Full boot sequence through to a fresh, calibrated save on the campaign map. */
export async function bootToMap(page: Page): Promise<void> {
  await page.goto("/");
  await passAudioGate(page);
  await createSaveAndCalibrate(page);
}

/**
 * Jumps directly to a battle, bypassing map navigation -- for specs that
 * test battle mechanics, not map UX. Resolves only once the NEW battle's
 * async create() has fully finished (combat object replaced + command
 * stage reached): Phaser marks the scene active while create() is still
 * awaiting audio preload/clock start, and because the same Scene instance
 * is reused across battles, stale `stage`/`combat` fields from a previous
 * battle can otherwise satisfy a naive wait and let a spec send input
 * before the new battle is listening.
 */
export async function jumpToEncounter(page: Page, nodeId: string, encounterId: string): Promise<void> {
  await page.evaluate(
    ({ nodeId, encounterId }) => {
      const dbg = window.__meterfallDebug;
      const scene = dbg.game.scene.getScene("BattleScene") as unknown as { combat?: unknown };
      (window as unknown as { __prevCombat: unknown }).__prevCombat = scene?.combat ?? null;
      dbg.GameContext.pendingNodeId = nodeId;
      dbg.GameContext.pendingEncounterId = encounterId;
      dbg.game.scene.stop("MapScene");
      dbg.game.scene.start("BattleScene");
    },
    { nodeId, encounterId }
  );
  await page.waitForFunction(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { combat?: unknown; stage?: string };
    const prev = (window as unknown as { __prevCombat: unknown }).__prevCombat;
    return !!scene.combat && scene.combat !== prev && scene.stage === "command";
  });
}

/**
 * Launches SettingsOverlay in parallel over MapScene, exactly as MapScene's
 * own "Settings" menu item does. Note: `launch` lives on a scene instance's
 * own ScenePlugin (`this.scene.launch(...)` from inside a Scene), not on
 * the global SceneManager (`game.scene`) -- caught by tsc once tests were
 * added to the typecheck include list, since `game.scene.launch(...)` looks
 * plausible but doesn't type-check.
 */
export async function openSettingsFromMap(page: Page): Promise<void> {
  await page.evaluate(() => {
    const mapScene = window.__meterfallDebug.game.scene.getScene("MapScene") as unknown as Phaser.Scene;
    mapScene.scene.launch("SettingsOverlay", { returnTo: "MapScene" });
  });
  await waitForScene(page, "SettingsOverlay");
}

/**
 * Stops SettingsOverlay directly (equivalent to its own "Back" item, which
 * just calls `this.scene.stop()`) and waits for the underlying scene to
 * resume. Real bug this guards against: launching SettingsOverlay again
 * while a previous instance is still open (e.g. a test that never closes
 * it) stacks a second live instance on top of the first rather than
 * replacing it, which corrupts the paused/resumed state of the scene
 * underneath and was observed to eventually crash the browser after enough
 * accumulated state.
 *
 * Must call `.stop()` on the scene's OWN ScenePlugin (`settingsScene.scene`),
 * not `game.scene.stop(key)` on the global SceneManager -- the same class of
 * bug already documented on `openSettingsFromMap`'s use of `.launch()`.
 * Confirmed live: going through the global manager left the underlying
 * scene's queued `resume()` never processed, hanging every caller forever.
 */
export async function closeSettings(page: Page, returnTo: string): Promise<void> {
  await page.evaluate(() => {
    const settingsScene = window.__meterfallDebug.game.scene.getScene("SettingsOverlay") as unknown as Phaser.Scene;
    settingsScene.scene.stop();
  });
  await waitForScene(page, returnTo);
}

/**
 * State of BattleScene's ChiptuneMusicPlayer: whether a rendered battle
 * track is actually playing (as opposed to the sonifier-only fallback that
 * kicks in when a trackId has no rendered audio or the buffer fails to
 * load). `state` is the underlying Tone.Player's "started"/"stopped".
 */
export async function getMusicState(page: Page): Promise<{ hasPlayer: boolean; state: string | null }> {
  return page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as Record<string, unknown>;
    const music = scene.music as { player: { state: string } | null } | undefined;
    return {
      hasPlayer: !!music?.player,
      state: music?.player?.state ?? null,
    };
  });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function getBattleSceneState(page: Page): Promise<any> {
  return page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as Record<string, unknown>;
    const combat = scene.combat as { heroes: unknown[]; enemies: unknown[]; round: number; outcome: string; groove: number };
    return {
      stage: scene.stage,
      beatmapTrackId: (scene.beatmap as { trackId: string }).trackId,
      effectiveBpm: scene.effectiveBpm,
      currentPhaseIndex: scene.currentPhaseIndex,
      heroes: combat.heroes,
      enemies: combat.enemies,
      round: combat.round,
      outcome: combat.outcome,
      groove: combat.groove,
    };
  });
}
