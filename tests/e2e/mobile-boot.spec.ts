import { test, expect, devices } from "@playwright/test";

/**
 * Mobile playability floor (PRD §9.2 Tier 2; owner report 2026-07-14:
 * "doesn't even start on mobile... click any button thing is broken").
 * Runs the chromium project with Pixel 5 emulation (touch, coarse pointer,
 * mobile viewport): the game must boot to the audio gate, a TAP must pass
 * the gate, and the touch control layer must mount. Real-device (iOS
 * Safari) verification remains manual per the PRD's Tier-2 bar; this pins
 * the emulatable floor so a regression can't ship silently.
 */

test.use({ ...devices["Pixel 5"] });

test("boots on a phone: tap passes the audio gate and touch controls mount", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));

  await page.goto("/");
  await page.waitForFunction(() => window.__meterfallDebug?.game?.scene?.isActive("AudioGateScene"));

  // The on-screen controls exist (coarse-pointer device) incl. the ultimate button.
  await expect(page.locator("#touch-controls")).toHaveCount(1);
  await expect(page.locator("#touch-controls .tc-ult")).toHaveCount(1);

  // A plain TAP in the open centre must pass the gate (the front door).
  const viewport = page.viewportSize()!;
  await page.touchscreen.tap(viewport.width / 2, viewport.height / 2);
  await page.waitForFunction(() => window.__meterfallDebug.game.scene.isActive("MainMenuScene"));

  // No uncaught errors anywhere in the boot path.
  expect(pageErrors).toEqual([]);

  // And no fatal-crash overlay was painted (src/main.ts error reporter).
  await expect(page.locator("#fatal-overlay")).toHaveCount(0);
});
