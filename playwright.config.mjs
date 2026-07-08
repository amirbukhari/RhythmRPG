import { defineConfig, devices } from "@playwright/test";

// E2E suite for a canvas-rendered Phaser game: there's no queryable DOM for
// game state, so specs drive the game via keyboard/pointer input and assert
// against the dev-only window.__meterfallDebug hook (src/main.ts), not DOM
// selectors. See tests/e2e/helpers.ts.
//
// Plain .mjs, not .ts: this Node version (20.5.1) can't natively load a .ts
// Playwright config (the same class of issue that forced pinning vitest to
// 1.x -- recent tooling versions assume newer Node's native TS support).
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  fullyParallel: false, // each test drives one shared game instance's page lifecycle; keep runs predictable
  workers: 1, // headless WebGL under software rendering in this environment is resource-heavy; concurrency caused real flakiness
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5180",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev -- --port 5180 --strictPort",
    url: "http://localhost:5180",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], launchOptions: { args: ["--autoplay-policy=no-user-gesture-required"] } },
    },
    {
      // Firefox has no equivalent CLI flag; autoplay policy is a preference.
      name: "firefox",
      use: { ...devices["Desktop Firefox"], launchOptions: { firefoxUserPrefs: { "media.autoplay.default": 0 } } },
    },
  ],
});
