import { test, expect } from "@playwright/test";
import { bootToMap, isSceneActive, passAudioGate, waitForScene } from "./helpers";

test.describe("boot flow", () => {
  test("boots through audio gate, save creation, and calibration to the campaign map with no console errors", async ({ page }) => {
    const pageErrors: string[] = [];
    page.on("pageerror", (err) => pageErrors.push(err.message));

    await bootToMap(page);

    expect(await isSceneActive(page, "MapScene")).toBe(true);
    expect(pageErrors).toEqual([]);
  });

  test("persists calibration to the save profile and survives a page reload", async ({ page }) => {
    await bootToMap(page);

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
});
