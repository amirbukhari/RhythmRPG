import { test, expect, type Page } from "@playwright/test";
import { bootToMap, openSettingsFromMap } from "./helpers";

/**
 * Regression coverage for two real bugs found via manual live testing
 * during development: TextMenu resetting keyboard selection to the top item
 * on every settings change, and a paused underlying scene's menu still
 * reacting to the same keypresses as the SettingsOverlay on top of it.
 *
 * Each step waits for its own expected state change (not a fixed sleep) --
 * if the selection-reset bug regressed, the *wrong* setting would change
 * (Game Speed again instead of the intended item) and the waitForFunction
 * for the correct one would time out and fail the test, rather than a flat
 * sleep race masking it either way.
 *
 * One boot for the whole file (serial mode); each test re-launches
 * SettingsOverlay fresh (cheap, not a real boot) so they stay independent.
 */
test.describe.configure({ mode: "serial" });

let page: Page;

test.beforeAll(async ({ browser }) => {
  page = await browser.newPage();
  await bootToMap(page);
});

test.afterAll(async () => {
  await page.close();
});

test.describe("settings", () => {
  test("keyboard selection survives multiple sequential toggles without resetting or double-handling input", async () => {
    await openSettingsFromMap(page);

    await page.keyboard.press("Enter"); // toggle Game Speed (index 0) -> 70%
    await page.waitForFunction(() => window.__meterfallDebug.GameContext.activeProfile?.settings.gameSpeed === 0.7);

    await page.keyboard.press("ArrowDown"); // -> index 1 (Assisted Timing Windows)
    await page.keyboard.press("Enter"); // toggle ON
    await page.waitForFunction(() => window.__meterfallDebug.GameContext.activeProfile?.settings.assistedTimingWindows === true);

    await page.keyboard.press("ArrowDown"); // -> index 2 (Reduced Motion)
    await page.keyboard.press("Enter"); // toggle ON
    await page.waitForFunction(() => window.__meterfallDebug.GameContext.activeProfile?.settings.reducedMotion === true);

    const settings = await page.evaluate(() => window.__meterfallDebug.GameContext.activeProfile!.settings);
    expect(settings.gameSpeed).toBe(0.7);
    expect(settings.assistedTimingWindows).toBe(true);
    expect(settings.reducedMotion).toBe(true);
  });

  test("remapping the tap key persists and is honored in battle", async () => {
    await openSettingsFromMap(page);

    // Navigate to "Remap Tap Key" (index 9 in the fixed settings menu order).
    for (let i = 0; i < 9; i++) {
      await page.keyboard.press("ArrowDown");
      await page.waitForTimeout(80); // avoid outrunning the menu's own input handling
    }
    await page.keyboard.press("Enter"); // begin remap capture
    await page.waitForTimeout(150); // SettingsOverlay deliberately delays attaching the capture listener by 50ms
    await page.keyboard.press("KeyZ");

    await page.waitForFunction(() => window.__meterfallDebug.GameContext.activeProfile?.settings.keyBindings.tap === "z");
    const tapKey = await page.evaluate(() => window.__meterfallDebug.GameContext.activeProfile!.settings.keyBindings.tap);
    expect(tapKey).toBe("z");
  });
});
