import { test, expect } from "@playwright/test";
import { bootToOverworld, isSceneActive, passAudioGate, waitForScene } from "./helpers";

// Not imported from src/config/GameConfig: that module imports the `phaser`
// package, which assumes a browser/DOM environment and throws when loaded
// directly by Playwright's Node-based test loader (confirmed live).
const BASE_WIDTH = 320;
const BASE_HEIGHT = 180;

test.describe("boot flow", () => {
  test("boots through audio gate, save creation, and calibration to the campaign map with no console errors", async ({ page }) => {
    const pageErrors: string[] = [];
    page.on("pageerror", (err) => pageErrors.push(err.message));

    await bootToOverworld(page);

    expect(await isSceneActive(page, "OverworldScene")).toBe(true);
    expect(pageErrors).toEqual([]);
  });

  test("persists calibration to the save profile and survives a page reload", async ({ page }) => {
    await bootToOverworld(page);

    const beforeReload = await page.evaluate(() => window.__meterfallDebug.GameContext.activeProfile);
    expect(beforeReload?.calibrationDone).toBe(true);
    const slotId = beforeReload!.slotId;

    await page.reload();
    await page.waitForFunction(() => Boolean(window.__meterfallDebug));

    // Audio gate again (a fresh page load re-suspends the AudioContext), then load the same slot.
    await passAudioGate(page);
    await page.keyboard.press("Enter"); // Start/Continue -> SaveScene
    await waitForScene(page, "SaveScene");

    const loaded = await page.evaluate(async (slotId) => {
      const profile = await window.__meterfallDebug.GameContext.saveManager.load(slotId);
      return profile;
    }, slotId);

    expect(loaded?.calibrationDone).toBe(true);
    expect(typeof loaded?.calibrationOffsetMs).toBe("number");
  });

  test("completes calibration with pointer taps, not just keyboard (real bug: calibration had no pointer input path at all)", async ({ page }) => {
    await page.goto("/");
    await passAudioGate(page);
    await page.keyboard.press("Enter"); // Start/Continue -> SaveScene
    await waitForScene(page, "SaveScene");
    await page.keyboard.press("Enter"); // + New Save -> CalibrationScene
    await waitForScene(page, "CalibrationScene");

    for (let i = 0; i < 8; i++) {
      await page.mouse.click(BASE_WIDTH / 2, BASE_HEIGHT / 2);
      await page.waitForTimeout(600); // real calibration BPM is 100 -> 600ms/beat
    }

    await waitForScene(page, "OverworldScene");
    expect(await isSceneActive(page, "OverworldScene")).toBe(true);
  });
});
