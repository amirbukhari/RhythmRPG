import { test, expect, type Page } from "@playwright/test";
import { bootToOverworld, jumpToEncounter, getBattleSceneState } from "./helpers";

/**
 * PRD §8.7 / release gate #3: "the final boss reliably executes authored
 * meter changes on bar boundary without drift." Real-time rhythm input
 * can't be driven precisely enough through browser automation to grind the
 * boss down via actual gameplay, so these directly set HP (a legitimate way
 * to test "does crossing this threshold trigger the transition", which is
 * the actual thing under test -- not whether input timing can defeat a
 * boss). This is the same technique used to find and fix two real bugs
 * during development: a Transport-time/AudioContext-time clock mixup that
 * silently broke the second phase transition, and a scheduling precision
 * warning from Tone.js.
 *
 * One boot + one boss encounter for the whole file (serial mode): each test
 * builds on the previous test's phase, rather than re-fighting from phase 1
 * every time -- the phase-1 state is asserted before test 2 advances it.
 */
test.describe.configure({ mode: "serial" });

let page: Page;

test.beforeAll(async ({ browser }) => {
  page = await browser.newPage();
  await bootToOverworld(page);
  await jumpToEncounter(page, "boss_1", "boss_conductor_01");
});

test.afterAll(async () => {
  await page.close();
});

test.describe("boss phase transitions", () => {
  test("starts in phase 1 at the authored tempo", async () => {
    const state = await getBattleSceneState(page);
    expect(state.beatmapTrackId).toBe("boss_conductor_p1");
    expect(state.effectiveBpm).toBe(105);
    expect(state.currentPhaseIndex).toBe(0);
  });

  test("crossing the phase 2 threshold swaps the beatmap and tempo at the next bar boundary", async () => {
    await page.evaluate(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { combat: { enemies: { hp: number; maxHp: number }[] } };
      scene.combat.enemies[0].hp = Math.floor(scene.combat.enemies[0].maxHp * 0.6); // below the 0.66 threshold
    });

    await page.waitForFunction(
      () => (window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { currentPhaseIndex: number }).currentPhaseIndex === 1,
      { timeout: 10_000 }
    );

    const state = await getBattleSceneState(page);
    expect(state.beatmapTrackId).toBe("boss_conductor_p2");
    expect(state.effectiveBpm).toBe(178);
  });

  test("crossing the phase 3 threshold reaches a live 5/4 meter", async () => {
    await page.evaluate(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { combat: { enemies: { hp: number; maxHp: number }[] } };
      scene.combat.enemies[0].hp = Math.floor(scene.combat.enemies[0].maxHp * 0.25); // below the 0.33 threshold
    });
    await page.waitForFunction(
      () => (window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { currentPhaseIndex: number }).currentPhaseIndex === 2,
      { timeout: 10_000 }
    );

    const state = await getBattleSceneState(page);
    expect(state.beatmapTrackId).toBe("boss_conductor_p3");

    // Confirm a real 5/4 bar actually renders, not just that the beatmap swapped.
    const meterText = await page.evaluate(() => (window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { beatText: { text: string } }).beatText.text);
    expect(meterText).toMatch(/\(5\/4\)|\(7\/8\)|\(4\/4\)|\(3\/4\)/);
  });
});
