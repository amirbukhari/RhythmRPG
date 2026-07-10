import { test, expect, type Page } from "@playwright/test";
import { bootToMap, jumpToEncounter, getBattleSceneState, getMusicState } from "./helpers";

// One boot+calibration per file (not per test) -- each is ~5s of real
// calibration-tap wait time, and re-doing it for every test made the full
// two-browser suite too slow to run reliably in this environment. Safe here
// because every test jumps to a *fresh* BattleScene via jumpToEncounter,
// which is what's actually under test.
test.describe.configure({ mode: "serial" });

let page: Page;

test.beforeAll(async ({ browser }) => {
  page = await browser.newPage();
  await bootToMap(page);
});

test.afterAll(async () => {
  await page.close();
});

test.describe("battle basics", () => {
  test("starts a battle with the correct party, enemy, and command stage", async () => {
    await jumpToEncounter(page, "opening_1", "opening_biome_slime_01");

    const state = await getBattleSceneState(page);
    expect(state.stage).toBe("command");
    expect(state.heroes.map((h: { heroId: string }) => h.heroId)).toEqual(["warrior", "tank", "mage", "healer"]);
    expect(state.heroes.every((h: { hp: number; maxHp: number }) => h.hp === h.maxHp)).toBe(true);
    expect(state.enemies).toHaveLength(1);
    expect(state.enemies[0].enemyId).toBe("slime");
    expect(state.outcome).toBe("ongoing");
  });

  test("plays the rendered chiptune battle track, not just the sonifier", async () => {
    await jumpToEncounter(page, "opening_1", "opening_biome_slime_01");

    // PRD §20.2 item 2 (real music integration): the encounter's rendered
    // chiptune track (assets/audio/battle/) must actually be loaded and
    // playing -- a 404'd or undecodable asset degrades silently to
    // sonifier-only, which this would catch. Waits rather than asserting
    // immediately: the scene registers as active while its async create()
    // is still fetching/decoding the buffer.
    await page.waitForFunction(
      () => {
        const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { music?: { player: unknown } };
        return !!scene.music?.player;
      },
      { timeout: 10_000 }
    );
    const music = await getMusicState(page);
    expect(music.state).toBe("started");
  });

  test("selecting an ability enters the timed performance stage and accepts a tap", async () => {
    await jumpToEncounter(page, "opening_1", "opening_biome_slime_01");

    await page.keyboard.press("1"); // warrior_slash_chain, free, 3 taps
    await page.waitForFunction(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { stage: string };
      return scene.stage === "awaiting-input";
    });

    await page.keyboard.press("Space");
    const stepIndex = await page.evaluate(() => (window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { stepIndex: number }).stepIndex);
    expect(stepIndex).toBeGreaterThanOrEqual(1);
  });

  test("auto-miss safety net resolves a performance and advances the turn even with zero input", async () => {
    await jumpToEncounter(page, "opening_1", "opening_biome_slime_01");

    await page.keyboard.press("1"); // warrior_slash_chain, 3 taps
    // Don't press anything -- the auto-miss grace window (0.35s past each
    // target) must resolve the ability and return to the command stage for
    // the next hero, or this test times out.
    await page.waitForFunction(
      () => {
        const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { stage: string };
        return scene.stage === "command";
      },
      { timeout: 15_000 }
    );

    const state = await getBattleSceneState(page);
    expect(state.enemies[0].hp).toBe(state.enemies[0].maxHp); // an all-miss performance deals 0 damage
  });

  test("multi-enemy encounters require choosing a target before the timed performance begins", async () => {
    await jumpToEncounter(page, "mid_2", "mid_biome_2_luchadores_01");

    await page.keyboard.press("1"); // warrior_slash_chain -- deals damage, needs a target since 2 enemies are alive
    await page.waitForFunction(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { stage: string };
      return scene.stage === "select-target";
    });

    await page.keyboard.press("2"); // choose the second enemy
    await page.waitForFunction(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("BattleScene") as unknown as { stage: string };
      return scene.stage === "awaiting-input";
    });

    const state = await getBattleSceneState(page);
    expect(state.enemies).toHaveLength(2);
  });
});
