import { test } from "@playwright/test";
import { waitForScene, passAudioGate, createSaveAndCalibrate } from "./helpers";

test("audit: capture every screen", async ({ page }) => {
  await page.goto("/");
  await waitForScene(page, "AudioGateScene");
  await page.screenshot({ path: "test-results/audit-1-gate.png" });
  await page.mouse.click(160, 90);
  await waitForScene(page, "MainMenuScene");
  await page.waitForTimeout(600);
  await page.screenshot({ path: "test-results/audit-2-menu.png" });
  await page.keyboard.press("Enter");
  await waitForScene(page, "SaveScene");
  await page.screenshot({ path: "test-results/audit-3-save.png" });
  await page.keyboard.press("Enter");
  await waitForScene(page, "CalibrationScene");
  await page.screenshot({ path: "test-results/audit-4-calibration.png" });
  for (let i = 0; i < 16 && !(await page.evaluate(() => window.__meterfallDebug.game.scene.isActive("OverworldScene"))); i++) {
    await page.keyboard.press("Space");
    await page.waitForTimeout(400);
  }
  await waitForScene(page, "OverworldScene");
  await page.waitForTimeout(500);
  await page.screenshot({ path: "test-results/audit-5-overworld.png" });
  // walk around a bit for the follower/foe view
  await page.keyboard.down("d");
  await page.waitForTimeout(1200);
  await page.keyboard.up("d");
  await page.screenshot({ path: "test-results/audit-6-overworld-walk.png" });
  // fight
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { debugTeleportToNode(id: string): void };
    scene.debugTeleportToNode("opening_1");
  });
  await waitForScene(page, "ActionBattleScene");
  await page.waitForTimeout(2200);
  await page.screenshot({ path: "test-results/audit-7-battle.png" });
  // attack a few times on-beat-ish
  for (let i = 0; i < 6; i++) {
    await page.keyboard.press("j");
    await page.waitForTimeout(260);
  }
  await page.screenshot({ path: "test-results/audit-8-battle-attack.png" });
  // boss arena
  await page.evaluate(() => {
    const dbg = window.__meterfallDebug;
    dbg.GameContext.activeProfile!.campaignProgress.clearedNodeIds = ["opening_1", "mid_1", "mid_2", "mid_3"];
    dbg.GameContext.activeProfile!.campaignProgress.currentNodeId = "boss_1";
    dbg.game.scene.getScene("ActionBattleScene").scene.start("OverworldScene");
  });
  await waitForScene(page, "OverworldScene");
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { debugTeleportToNode(id: string): void };
    scene.debugTeleportToNode("boss_1");
  });
  await waitForScene(page, "ActionBattleScene");
  await page.waitForTimeout(2200);
  await page.screenshot({ path: "test-results/audit-9-boss.png" });
});
