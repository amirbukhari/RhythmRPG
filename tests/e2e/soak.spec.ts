import { test, expect } from "@playwright/test";
import { bootToOverworld, openSettingsFromOverworld, closeSettings, waitForScene, isSceneActive } from "./helpers";

/**
 * P5 soak (PRD §15/§16.1): several minutes of continuous real play --
 * boot, wander every direction, two full fights (one forced loss, one
 * win), settings churn mid-session, an obelisk-free reload -- with ZERO
 * uncaught errors and no fatal overlay. Leaks and cross-scene teardown
 * bugs (tweens on destroyed objects, listeners surviving restarts) show
 * up here before a player finds them.
 */

test("soak: extended session with zero uncaught errors", async ({ page }) => {
  test.setTimeout(240_000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 300)));

  await bootToOverworld(page);

  // Wander hard in all directions (input churn + camera + canopy fades).
  for (const key of ["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp", "ArrowRight"]) {
    await page.keyboard.down(key);
    await page.waitForTimeout(1500);
    await page.keyboard.up(key);
  }

  // Settings churn mid-session.
  await openSettingsFromOverworld(page);
  for (let i = 0; i < 3; i++) {
    await page.keyboard.press("Enter"); // cycle game speed 3x -> back to 100%
    await page.waitForTimeout(150);
  }
  await closeSettings(page, "OverworldScene");

  // Fight 1: enter and LOSE (defeat path + Results + respawn).
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { debugTeleportToNode(id: string): void };
    scene.debugTeleportToNode("opening_1");
  });
  await page.waitForFunction(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { fight: { simArena: unknown } | null };
    return Boolean(scene.fight && scene.fight.simArena);
  });
  await page.waitForTimeout(2500); // let the fight actually run (SFX, VFX, tiers)
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as {
      fight: { simArena: { fighters: { team: string; hp: number; state: string }[] } };
    };
    const p = scene.fight.simArena.fighters[0];
    p.hp = 0;
    p.state = "dead";
  });
  await waitForScene(page, "ResultsScene");
  await page.keyboard.press("Enter");
  await waitForScene(page, "OverworldScene");

  // Fight 2: enter and WIN (victory + relic choice + respawn).
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { debugTeleportToNode(id: string): void };
    scene.debugTeleportToNode("opening_1");
  });
  await page.waitForFunction(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { fight: { simArena: unknown } | null };
    return Boolean(scene.fight && scene.fight.simArena);
  });
  await page.waitForTimeout(2000);
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
  for (let i = 0; i < 3; i++) {
    if (await isSceneActive(page, "OverworldScene")) break;
    await page.keyboard.press("Enter");
    await page.waitForTimeout(400);
  }
  await waitForScene(page, "OverworldScene");

  // Reload: persistence survives, world comes back clean.
  await page.reload();
  await waitForScene(page, "AudioGateScene");
  await page.mouse.click(160, 90);
  await waitForScene(page, "MainMenuScene");

  expect(errors, errors.join("\n")).toEqual([]);
  await expect(page.locator("#fatal-overlay")).toHaveCount(0);
});
