/**
 * In-browser capture harness -- look at the game before calling anything done.
 *
 *   npm run dev -- --port 5180 --strictPort &
 *   node tools/capture.mjs                          # the Fold's town, 5 views
 *   node tools/capture.mjs 33,161 12,178            # arbitrary tile targets
 *   OUT=/tmp/shots node tools/capture.mjs
 *
 * WHY THIS EXISTS
 * PRD §11.1.2 step 5 and the style contract's review gate both say the same
 * thing: nothing ships unlooked-at. Offline previews are not enough for world
 * art, because the overworld composites things a preview cannot -- additive
 * haze, god-rays, the region tint, the painted ground plate underneath, and
 * `worldScaleFor`. The Fold's houses previewed correctly and arrived in-game as
 * a pale grey-blue billboard; only a real frame showed it.
 *
 * It boots the real game through the real audio gate, save creation and
 * calibration, then MOVES THE CAMERA rather than the player: walking to a spot
 * is slow, hits collision, and cannot frame a rooftop at all.
 *
 * NODE 20 ONLY -- @playwright/test 1.44 hangs silently on Node >= 22. See the
 * guard at the top of playwright.config.mjs.
 *
 *   PATH="$HOME/.nvm/versions/node/v20.20.1/bin:$PATH" node tools/capture.mjs
 */
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";

const MAJOR = Number(process.versions.node.split(".")[0]);
if (MAJOR >= 22) {
  console.error(`@playwright/test 1.44 hangs on Node ${process.versions.node}; run this on Node 20.`);
  process.exit(1);
}

// `CAP_WINDOW=col,row,radiusPx` dumps every display object near that tile.
const capWindow = process.env.CAP_WINDOW
  ? (([c, r, rad]) => ({ x: Number(c) * 16 + 8, y: Number(r) * 16 + 8, r: Number(rad ?? 120) }))(process.env.CAP_WINDOW.split(","))
  : null;
const OUT = process.env.OUT ?? "tools/overworld/.preview";
const URL = process.env.URL ?? "http://localhost:5180/?nocutscenes=1";
// Default targets: the Fold's town (tools/overworld/place_fold.py).
const DEFAULT = [
  ["plaza", 26, 170],
  ["street", 33, 166],
  ["terrace", 33, 161],
  ["west", 12, 178],
  ["gate", 23, 162],
];
const targets = process.argv.slice(2).length
  ? process.argv.slice(2).map((a, i) => {
      const [c, r] = a.split(",").map(Number);
      return [`shot${i}_${c}_${r}`, c, r];
    })
  : DEFAULT;

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
page.on("pageerror", (e) => errors.push(String(e)));

// `isActive` goes true when the scene STARTS, which is before its `create()`
// has finished building a menu and binding the keyboard -- so a keypress sent
// the instant this resolves can be dropped on the floor. That was always a
// race; scene transitions (src/scenes/Transition.ts) made it a reliable one,
// because arriving now costs a 380ms fade-in on top of create(). Wait for the
// scene, then let it settle.
const active = async (key) => {
  await page.waitForFunction((k) => window.__meterfallDebug?.game?.scene?.isActive(k), key);
  await page.waitForTimeout(500);
};
await page.goto(URL);
await active("AudioGateScene");
await page.mouse.click(640, 360); // the mandatory user-gesture audio unlock (PRD §10.4)
await active("MainMenuScene");
await page.keyboard.press("Enter");
await active("SaveScene");
await page.keyboard.press("Enter");
await active("CalibrationScene");
// Calibration needs 8 taps. Tap until it advances rather than exactly 8 times:
// under software WebGL a synthetic keypress is occasionally dropped.
for (let i = 0; i < 16; i++) {
  if (await page.evaluate(() => window.__meterfallDebug.game.scene.isActive("OverworldScene"))) break;
  await page.keyboard.press("Space");
  await page.waitForTimeout(380);
}
await active("OverworldScene");
await page.waitForTimeout(2500);

if (capWindow) await page.evaluate((w) => { window.__capWindow = w; }, capWindow);

console.log(
  JSON.stringify(
    await page.evaluate(() => {
      const g = window.__meterfallDebug.game;
      const sc = g.scene.getScene("OverworldScene");
      const placed = sc.children.list.filter((o) => o.texture && String(o.texture.key).startsWith("env_"));
      const byKit = {};
      for (const o of placed) {
        const kit = String(o.texture.key).split("_")[1];
        byKit[kit] = (byKit[kit] ?? 0) + 1;
      }
      // Everything the scene actually drew inside a WINDOW around a tile --
      // the only way to answer "what IS that thing at the top right", because
      // a sprite can come from dressing.json, a scatter pass, or the venue
      // composer, and only the live display list knows which.
      const win = window.__capWindow;
      const inWindow = win
        ? sc.children.list
            .filter((o) => o.texture && o.x !== undefined)
            .filter((o) => Math.abs(o.x - win.x) < win.r && Math.abs(o.y - win.y) < win.r)
            .map((o) => ({
              key: String(o.texture.key),
              frame: String(o.frame?.name ?? ""),
              x: Math.round(o.x),
              y: Math.round(o.y),
              w: Math.round(o.displayWidth ?? 0),
              h: Math.round(o.displayHeight ?? 0),
              a: Number((o.alpha ?? 1).toFixed(2)),
              blend: o.blendMode,
              depth: o.depth,
            }))
            .sort((a, b) => a.y - b.y)
        : undefined;
      return { playerTile: sc.playerPos, envSpritesPlaced: placed.length, byKit, inWindow };
    }),
    null,
    1,
  ),
);

for (const [name, col, row] of targets) {
  await page.evaluate(
    ([c, r]) => {
      const sc = window.__meterfallDebug.game.scene.getScene("OverworldScene");
      sc.cameras.main.stopFollow();
      sc.cameras.main.centerOn(c * 16 + 8, r * 16 + 8);
    },
    [col, row],
  );
  await page.waitForTimeout(700);
  await page.screenshot({ path: `${OUT}/cap_${name}.png` });
  console.log(`${OUT}/cap_${name}.png  <- tile (${col},${row})`);
}

console.log("console errors:", errors.length ? errors.slice(0, 8) : "none");
await browser.close();
process.exit(errors.length ? 1 : 0);
