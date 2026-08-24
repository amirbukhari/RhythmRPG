import { defineConfig, devices } from "@playwright/test";

// ---------------------------------------------------------------------------
// NODE VERSION GUARD -- do not remove.
//
// @playwright/test 1.44 HANGS SILENTLY on Node >= 22: `playwright test` (even
// `--list`, which launches no browser) produces zero bytes of output and never
// exits. It cost most of a session to find, because every symptom points at the
// game -- an empty log reads as "the suite is slow" or "WebGL is stuck", not as
// "the runner never started". Node 20.x runs the identical suite fine.
//
// So: fail loudly in one line instead of hanging. A silent hang is the only
// failure mode worse than a red test.
const MAJOR = Number(process.versions.node.split(".")[0]);
if (MAJOR >= 22) {
  console.error(
    `\n@playwright/test 1.44 hangs on Node ${process.versions.node}.\n` +
      `Run the e2e gate on Node 20, e.g.:\n\n` +
      `  PATH="$HOME/.nvm/versions/node/v20.20.1/bin:$PATH" npm run test:e2e\n\n` +
      `(or upgrade @playwright/test to >=1.50, which supports current Node.)\n`,
  );
  process.exit(1);
}
// ---------------------------------------------------------------------------

// E2E suite for a canvas-rendered Phaser game: there's no queryable DOM for
// game state, so specs drive the game via keyboard/pointer input and assert
// against the dev-only window.__meterfallDebug hook (src/main.ts), not DOM
// selectors. See tests/e2e/helpers.ts.
//
// Plain .mjs, not .ts: the pinned Node (20.x -- see the guard above) can't natively load a .ts
// Playwright config (the same class of issue that forced pinning vitest to
// 1.x -- recent tooling versions assume newer Node's native TS support).
export default defineConfig({
  testDir: "./tests/e2e",
  // 120s (was 60s, was 30s): the game renders real pixel-art scenes (painted
  // battle backdrops, per-scene backdrops, sprite sheets) under this sandbox's
  // *software* WebGL, so scene loads/transitions are genuinely slower here
  // than on a GPU. The waits are for real state, not arbitrary sleeps; the
  // extra ceiling just stops a slow software-rendered frame from tripping a
  // wait. The in-world fight sim in particular runs at only a few FPS on the
  // slowest CI runners (measured: ~3 FPS under a 6x CPU throttle), where the
  // real-time fight specs (beat-truth, boss-phases, finale) wait on game-time
  // progression; 60s was too tight for those there. Real hardware is far under.
  timeout: 120_000,
  fullyParallel: false, // each test drives one shared game instance's page lifecycle; keep runs predictable
  workers: 1, // headless WebGL under software rendering in this environment is resource-heavy; concurrency caused real flakiness
  retries: 2, // timing-sensitive input/rhythm specs under software WebGL occasionally drop a synthetic input or run a slow frame; retries absorb it (see tests/e2e/README.md)
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
