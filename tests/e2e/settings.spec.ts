import { test, expect, type Page } from "@playwright/test";
import { bootToOverworld, openSettingsFromOverworld, closeSettings } from "./helpers";

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
 * SettingsOverlay fresh (cheap, not a real boot) so they stay independent --
 * which requires actually closing it before the next test launches it again
 * (see closeSettings in helpers.ts). Leaving a previous instance open and
 * launching a second one on top of it left the underlying scene's
 * paused/resumed state corrupted and reliably crashed the browser partway
 * through the next test.
 */
test.describe.configure({ mode: "serial" });

let page: Page;

test.beforeAll(async ({ browser }) => {
  page = await browser.newPage();
  await bootToOverworld(page);
});

test.afterAll(async () => {
  await page.close();
});

test.describe("settings", () => {
  test("keyboard selection survives multiple sequential toggles without resetting or double-handling input", async () => {
    await openSettingsFromOverworld(page);

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

    await closeSettings(page, "OverworldScene");
  });

  test("remapping keys (tap + combat bindings, §9.3) persists", async () => {
    await openSettingsFromOverworld(page);

    // Enter the "Audio & Controls" subpage (index 9 on the main page).
    for (let i = 0; i < 9; i++) {
      await page.keyboard.press("ArrowDown");
      await page.waitForTimeout(80); // avoid outrunning the menu's own input handling
    }
    await page.keyboard.press("Enter");
    await page.waitForTimeout(120);

    // Navigate to "Remap Tap" (index 3 on the controls page; selection
    // resets to the top on a page switch).
    for (let i = 0; i < 3; i++) {
      await page.keyboard.press("ArrowDown");
      await page.waitForTimeout(80);
    }
    await page.keyboard.press("Enter"); // begin remap capture
    await page.waitForTimeout(150); // SettingsOverlay deliberately delays attaching the capture listener by 50ms
    await page.keyboard.press("KeyZ");
    await page.waitForFunction(() => window.__meterfallDebug.GameContext.activeProfile?.settings.keyBindings.tap === "z");

    // And a COMBAT binding (the §9.3 gap this page closes): remap Light.
    await page.keyboard.press("ArrowDown"); // -> Remap Light Attack
    await page.waitForTimeout(80);
    await page.keyboard.press("Enter");
    await page.waitForTimeout(150);
    await page.keyboard.press("KeyP");
    await page.waitForFunction(() => window.__meterfallDebug.GameContext.activeProfile?.settings.keyBindings.light === "p");

    const bindings = await page.evaluate(() => window.__meterfallDebug.GameContext.activeProfile!.settings.keyBindings);
    expect(bindings.tap).toBe("z");
    expect(bindings.light).toBe("p");
  });
});
