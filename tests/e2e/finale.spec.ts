import { test, expect } from "@playwright/test";
import { bootToOverworld, waitForScene, isSceneActive } from "./helpers";

/**
 * The ending exists (v8.5): felling the FINAL boss routes Results ->
 * FinaleScene (wordmark + credits), completion is stamped on the save, and
 * the world stays open afterwards.
 */

test("beating the Conductor plays the finale and returns to an open world", async ({ page }) => {
  await bootToOverworld(page);

  // Stand the frontier at the boss and start his in-world fight.
  await page.evaluate(() => {
    const dbg = window.__meterfallDebug;
    dbg.GameContext.activeProfile!.campaignProgress.clearedNodeIds = ["opening_1", "mid_1", "mid_2", "mid_3"];
    dbg.GameContext.activeProfile!.campaignProgress.currentNodeId = "boss_1";
    (dbg.game.scene.getScene("OverworldScene") as unknown as Phaser.Scene).scene.restart();
  });
  await waitForScene(page, "OverworldScene");
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { debugTeleportToNode(id: string): void };
    scene.debugTeleportToNode("boss_1");
  });
  await page.waitForFunction(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { fight: { simArena: unknown } | null };
    return Boolean(scene.fight && scene.fight.simArena);
  });

  // Fell the Conductor through the sim seam; the real finish() path runs.
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as {
      fight: { simArena: { fighters: { team: string; hp: number; state: string }[] } };
    };
    for (const f of scene.fight.simArena.fighters) {
      if (f.team === "enemy") {
        f.hp = 0;
        f.state = "dead";
      }
    }
  });
  await waitForScene(page, "ResultsScene");

  // Step through results (relic choice if offered, then Continue) into the finale.
  for (let i = 0; i < 4; i++) {
    if (await isSceneActive(page, "FinaleScene")) break;
    await page.keyboard.press("Enter");
    await page.waitForTimeout(400);
  }
  await waitForScene(page, "FinaleScene");

  // Completion is stamped on the save.
  const completedAt = await page.evaluate(() => window.__meterfallDebug.GameContext.activeProfile!.campaignCompletedAt ?? null);
  expect(completedAt).not.toBeNull();

  // "Return to the drowned world" -> the world stays open post-game.
  await page.keyboard.press("Enter");
  await waitForScene(page, "OverworldScene");
  expect(await isSceneActive(page, "FinaleScene")).toBe(false);
});
