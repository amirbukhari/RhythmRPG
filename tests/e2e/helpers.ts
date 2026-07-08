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

/** Jumps directly to a battle, bypassing map navigation -- for specs that test battle mechanics, not map UX. */
export async function jumpToEncounter(page: Page, nodeId: string, encounterId: string): Promise<void> {
  await page.evaluate(
    ({ nodeId, encounterId }) => {
      const dbg = window.__meterfallDebug;
      dbg.GameContext.pendingNodeId = nodeId;
      dbg.GameContext.pendingEncounterId = encounterId;
      dbg.game.scene.stop("MapScene");
      dbg.game.scene.start("BattleScene");
    },
    { nodeId, encounterId }
  );
  await waitForScene(page, "BattleScene");
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
