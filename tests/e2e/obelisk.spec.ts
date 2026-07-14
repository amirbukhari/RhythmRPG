import { test, expect } from "@playwright/test";
import { bootToOverworld } from "./helpers";

/**
 * Save-obelisks (PRD §8.8 / v7.7): every fight node has an obelisk on a
 * nearby walkable tile; standing beside it and pressing E rests -- persisting
 * the save -- without triggering the fight. The foe itself now STANDS at the
 * node (areas-not-arenas), so this also guards that drawing the world's foes
 * doesn't crash on any node status (unlocked/locked/cleared all render).
 */
test("resting at a save-obelisk persists the save and does not start the fight", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await bootToOverworld(page);

  // Stand one tile beside the first fight node: within reach of its obelisk
  // (placed two tiles out) but NOT on the fight-trigger tile itself.
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as {
      getMarkerGridPosition(id: string): { col: number; row: number };
      playerPos: { col: number; row: number };
      snapPlayerToGrid(): void;
    };
    const m = scene.getMarkerGridPosition("opening_1");
    scene.playerPos = { col: m.col - 1, row: m.row };
    scene.snapPlayerToGrid();
  });
  await page.waitForTimeout(300);

  // mutate the live profile, then rest -- the persisted copy must pick it up
  await page.evaluate(() => {
    window.__meterfallDebug.GameContext.activeProfile!.campaignProgress.currency = 777;
  });
  await page.keyboard.press("e");
  await page.waitForTimeout(600);

  // still exploring, not fighting
  expect(await page.evaluate(() => window.__meterfallDebug.game.scene.isActive("OverworldScene"))).toBe(true);
  expect(await page.evaluate(() => Boolean(window.__meterfallDebug.game.scene.isActive("ActionBattleScene")))).toBe(false);

  // the rest persisted the profile (read back through the real SaveManager)
  const persisted = await page.evaluate(async () => {
    const ctx = window.__meterfallDebug.GameContext as unknown as {
      activeProfile: { slotId: string };
      saveManager: { load(slotId: string): Promise<{ campaignProgress: { currency: number } } | undefined> };
    };
    const saved = await ctx.saveManager.load(ctx.activeProfile.slotId);
    return saved?.campaignProgress.currency;
  });
  expect(persisted).toBe(777);
  expect(errors, errors.join("\n")).toEqual([]);
});
