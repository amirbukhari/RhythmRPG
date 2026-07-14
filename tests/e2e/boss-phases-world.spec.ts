import { test, expect, type Page } from "@playwright/test";
import { bootToOverworld, isSceneActive } from "./helpers";

/**
 * §8.7 boss phases ON THE SHIPPED PATH: the Conductor is fought in the
 * world (WorldFight), phases advance on authored HP thresholds, playback
 * jumps to the bound section of Quotience, and the enemy tempo escalates.
 * (The legacy boss-phases.spec.ts covers the retired BattleScene until its
 * deletion; THIS spec is the release-gate #3 coverage that counts.)
 */

interface WorldSeams {
  fight: {
    simArena: { fighters: { team: string; hp: number; maxHp: number }[] } | null;
    bossPhaseIndex: number;
  } | null;
  debugTeleportToNode(nodeId: string): void;
}

async function startBossFight(page: Page): Promise<void> {
  await bootToOverworld(page);
  await page.evaluate(() => {
    const dbg = window.__meterfallDebug;
    dbg.GameContext.activeProfile!.campaignProgress.clearedNodeIds = ["opening_1", "mid_1", "mid_2", "mid_3"];
    dbg.GameContext.activeProfile!.campaignProgress.currentNodeId = "boss_1";
    const scene = dbg.game.scene.getScene("OverworldScene") as unknown as Phaser.Scene;
    scene.scene.restart(); // re-derive markers/foes from the new progress
  });
  await page.waitForFunction(() => {
    const dbg = window.__meterfallDebug;
    return dbg.game.scene.isActive("OverworldScene");
  });
  await page.waitForTimeout(400); // let create() finish placing foes
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as WorldSeams;
    scene.debugTeleportToNode("boss_1");
  });
  await page.waitForFunction(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { fight: { simArena: unknown } | null };
    return Boolean(scene.fight && scene.fight.simArena);
  });
}

/** Set the boss's HP fraction through the sim seam. */
async function setBossHpFraction(page: Page, fraction: number): Promise<void> {
  await page.evaluate((frac) => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as WorldSeams;
    const boss = scene.fight!.simArena!.fighters.find((f) => f.team === "enemy")!;
    boss.hp = boss.maxHp * frac;
  }, fraction);
}

test("the in-world Conductor fight advances phases on authored HP thresholds", async ({ page }) => {
  await startBossFight(page);
  expect(await isSceneActive(page, "OverworldScene")).toBe(true);
  expect(await isSceneActive(page, "ActionBattleScene")).toBe(false);
  expect(await isSceneActive(page, "BattleScene")).toBe(false);

  const phase = () =>
    page.evaluate(() => (window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as WorldSeams).fight?.bossPhaseIndex ?? -1);

  expect(await phase()).toBe(0);

  // Crossing the 0.66 threshold -> movement II.
  await setBossHpFraction(page, 0.6);
  await page.waitForFunction(
    () => ((window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { fight: { bossPhaseIndex: number } | null }).fight?.bossPhaseIndex ?? -1) === 1
  );

  // If the boss song is audibly playing, playback must have jumped to the
  // bound movement_2 section (28.189s into Quotience).
  const posAfterP2 = await page.evaluate(() => window.__meterfallDebug.music.position());
  if (posAfterP2 !== null) expect(posAfterP2).toBeGreaterThanOrEqual(28.0);

  // Crossing the 0.33 threshold -> movement III.
  await setBossHpFraction(page, 0.3);
  await page.waitForFunction(
    () => ((window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { fight: { bossPhaseIndex: number } | null }).fight?.bossPhaseIndex ?? -1) === 2
  );
  const posAfterP3 = await page.evaluate(() => window.__meterfallDebug.music.position());
  if (posAfterP3 !== null) expect(posAfterP3).toBeGreaterThanOrEqual(74.0);

  // Escalation reached the sim.
  const aggression = await page.evaluate(
    () =>
      (window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { fight: { simArena: { enemyAggression?: number } } }).fight.simArena
        .enemyAggression
  );
  expect(aggression).toBeGreaterThan(1.5);
});
