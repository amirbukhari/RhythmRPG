import { test, expect } from "@playwright/test";
import { bootToOverworld, isSceneActive, waitForScene } from "./helpers";

/**
 * Overworld coverage: boot lands on the walkable map, real keyboard
 * movement works, collision blocks, walking onto an unlocked node marker
 * starts its battle, and after the battle the player respawns at that node.
 *
 * Movement asserts use the scene's getPlayerGridPosition() seam; the
 * battle-trigger tests use debugTeleportToNode(), which snaps the player
 * onto a marker and re-runs the same trigger check a real step performs --
 * pixel-perfect keyboard pathing across the whole map is exactly the
 * slow/flaky automation this suite already avoids (see jumpToEncounter).
 */

type OverworldSeams = {
  getPlayerGridPosition(): { col: number; row: number };
  debugTeleportToNode(nodeId: string): void;
};

async function playerGridPosition(page: import("@playwright/test").Page): Promise<{ col: number; row: number }> {
  return page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as OverworldSeams;
    return scene.getPlayerGridPosition();
  });
}

test.describe("overworld", () => {
  test("boot lands on the overworld; arrow keys move the player; the map edge blocks", async ({ page }) => {
    await bootToOverworld(page);
    expect(await isSceneActive(page, "OverworldScene")).toBe(true);

    const spawn = await playerGridPosition(page);

    // Hold right long enough for several 160ms tile steps.
    await page.keyboard.down("ArrowRight");
    await page.waitForTimeout(700);
    await page.keyboard.up("ArrowRight");
    const afterRight = await playerGridPosition(page);
    expect(afterRight.col).toBeGreaterThan(spawn.col);
    expect(afterRight.row).toBe(spawn.row);

    // Hold down long past what open ground would allow: the solid rock
    // border (last map row) must stop the player short of the map edge.
    await page.keyboard.down("ArrowDown");
    await page.waitForTimeout(1200);
    await page.keyboard.up("ArrowDown");
    const afterDown = await playerGridPosition(page);
    expect(afterDown.row).toBeLessThan(23); // map is 24 rows; row 23 is the border wall
  });

  test("walking onto the unlocked first node starts its battle with the right pending state", async ({ page }) => {
    await bootToOverworld(page);

    await page.evaluate(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as OverworldSeams;
      scene.debugTeleportToNode("opening_1");
    });
    await waitForScene(page, "ActionBattleScene"); // v6.0 real-time combat

    const pending = await page.evaluate(() => ({
      encounterId: window.__meterfallDebug.GameContext.pendingEncounterId,
      nodeId: window.__meterfallDebug.GameContext.pendingNodeId,
    }));
    expect(pending.nodeId).toBe("opening_1");
    // opening_1 resolves randomly from its encounterPool each visit.
    expect(["opening_biome_slime_01", "opening_biome_slime_02"]).toContain(pending.encounterId);
  });

  test("locked and cleared markers do not trigger battles", async ({ page }) => {
    await bootToOverworld(page);

    // mid_2 is past the fresh save's frontier: locked, must be a no-op.
    await page.evaluate(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as OverworldSeams;
      scene.debugTeleportToNode("mid_2");
    });
    await page.waitForTimeout(500);
    expect(await isSceneActive(page, "ActionBattleScene")).toBe(false);
    expect(await isSceneActive(page, "OverworldScene")).toBe(true);

    // Mark opening_1 cleared (as a won battle would) and stand on it: no re-fight.
    await page.evaluate(() => {
      const profile = window.__meterfallDebug.GameContext.activeProfile!;
      profile.campaignProgress.clearedNodeIds.push("opening_1");
      profile.campaignProgress.currentNodeId = "mid_1";
      const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as OverworldSeams;
      scene.debugTeleportToNode("opening_1");
    });
    await page.waitForTimeout(500);
    expect(await isSceneActive(page, "ActionBattleScene")).toBe(false);
    expect(await isSceneActive(page, "OverworldScene")).toBe(true);
  });

  test("after a victory the player respawns at the node just fought, not the spawn point", async ({ page }) => {
    await bootToOverworld(page);
    const spawn = await playerGridPosition(page);

    await page.evaluate(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as OverworldSeams;
      scene.debugTeleportToNode("opening_1");
    });
    await waitForScene(page, "ActionBattleScene");

    // Force the win by emptying the arena's enemy HP; the sim detects victory
    // on the next tick and runs the real finishBattle()/reward path. Playing a
    // full real-time fight with live input is the manual-verification job.
    await page.evaluate(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("ActionBattleScene") as unknown as {
        arena: { fighters: { team: string; hp: number; state: string }[] };
      };
      for (const f of scene.arena.fighters) {
        if (f.team === "enemy") {
          f.hp = 0;
          f.state = "dead";
        }
      }
    });
    await waitForScene(page, "ResultsScene");

    // Step through results (relic choice if offered, then continue).
    for (let i = 0; i < 3; i++) {
      if (await isSceneActive(page, "OverworldScene")) break;
      await page.keyboard.press("Enter");
      await page.waitForTimeout(400);
    }
    await waitForScene(page, "OverworldScene");

    const back = await playerGridPosition(page);
    expect(back).not.toEqual(spawn);
    // opening_1's marker tile, from assets/tilemaps/overworld.json.
    expect(back).toEqual({ col: 8, row: 19 });
  });
});
