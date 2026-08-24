/**
 * In-fight capture harness -- look at game FEEL before calling it done.
 *
 *   npm run dev -- --port 5180 --strictPort &
 *   node tools/fight.mjs                 # opening_1
 *   NODE_ID=boss_1 node tools/fight.mjs
 *
 * WHY THIS EXISTS, SEPARATELY FROM tools/capture.mjs
 * `capture.mjs` moves the camera around a static overworld, which is the right
 * tool for art and useless for impact. Hitstop, the impact-frame ghost, sparks,
 * squash and shake only exist for ~80ms after a hit lands, and they are exactly
 * the thing a unit test cannot see: `ActionCombat` is pure and knows nothing
 * about any of it (§10.2 -- the sim must never pause, so all of this is
 * render-only and lives in GameFeel). A green test suite and a fight that feels
 * like two sprites overlapping are completely compatible states.
 *
 * So this drives real input, polls the sim's `events` array every 30ms, and
 * screenshots the tick a HitEvent lands on -- which is the only moment in the
 * frame budget where there is anything to look at.
 *
 * NODE 20 ONLY -- @playwright/test 1.44 hangs silently on Node >= 22.
 */
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";

if (Number(process.versions.node.split(".")[0]) >= 22) {
  console.error(`@playwright/test 1.44 hangs on Node ${process.versions.node}; run this on Node 20.`);
  process.exit(1);
}
const OUT = process.env.OUT ?? "tools/overworld/.preview/fight";
const NODE_ID = process.env.NODE_ID ?? "opening_1";
const URL = process.env.URL ?? "http://localhost:5180/?nocutscenes=1";
const WANT = Number(process.env.SHOTS ?? 4);

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
page.on("pageerror", (e) => errors.push("PAGEERROR " + e.message));

await page.goto(URL);
await page.waitForFunction(() => window.__meterfallDebug?.game?.scene?.isActive("AudioGateScene"));
await page.mouse.click(160, 90);
await page.waitForFunction(() => window.__meterfallDebug.game.scene.isActive("MainMenuScene"));
await page.waitForTimeout(500);   // the arrival fade; the menu is live under it
// WAIT ON THE SCENE, NOT THE CLOCK. This walked the boot flow on fixed 600ms
// sleeps, which was already tight (SaveScene's create() is async -- it awaits
// the slot list before its menu accepts input) and broke outright the moment
// scene transitions added a 230ms fade in front of every start: the second
// Enter landed on a menu that did not exist yet, and the harness sat on the
// save screen sending calibration taps until it timed out 30s later.
const waitScene = (key) =>
  page.waitForFunction((k) => window.__meterfallDebug.game.scene.isActive(k), key, { timeout: 30000 });

await page.keyboard.press("Enter");
await waitScene("SaveScene");
await page.waitForTimeout(400); // the async slot list, then the menu binds keys
await page.keyboard.press("Enter");
await waitScene("CalibrationScene");
// the 8-tap calibration; a couple of spares in case one lands outside a window
for (let i = 0; i < 10; i++) {
  await page.keyboard.press("Space");
  await page.waitForTimeout(420);
}
await waitScene("OverworldScene");
await page.waitForTimeout(800);

// Straight into the fight through the same sim seam boss-phases-world.spec uses.
// Walking to a node is slow and can resolve a different encounter from the pool.
await page.evaluate((id) => {
  window.__meterfallDebug.game.scene.getScene("OverworldScene").debugTeleportToNode(id);
}, NODE_ID);
await page.waitForFunction(
  () => {
    const sc = window.__meterfallDebug.game.scene.getScene("OverworldScene");
    return Boolean(sc.fight && sc.fight.simArena);
  },
  null,
  { timeout: 20000 }
);
await page.waitForTimeout(1200);
await page.screenshot({ path: `${OUT}/00_enter.png` });

// CLOSE THE DISTANCE FIRST, and read the direction from the sim. The first cut
// of this just held ArrowRight, which walked Mir AWAY from the foes (they spawn
// on whichever side the node is approached from) -- 140 swings landed nothing
// but the enemy's counter-attacks, and the harness reported "1 impact frame" on
// a fight where the player never connected once.
// ---------------------------------------------------------------------------
// FREEZE ON THE IMPACT FRAME.
//
// Two things make this harder than it looks, and both cost a run to find.
//
// 1. `step()` CLEARS `arena.events` at the top of every tick, so the array is
//    only non-empty for the one frame the hit happened on. Polling it from the
//    harness at 150ms intervals catches a hit by luck: a run that landed six
//    attacks (the foe went 60 -> 46.8 HP) reported "0 impact frames".
//    So the listener lives IN the page, on the scene's POST_UPDATE -- which
//    fires after Scene.update, and therefore after the sim step, and therefore
//    while the events are still there.
//
// 2. The whole thing being looked at lasts 82ms at most (GameFeel's longest
//    hitstop, on a Perfect). A round-trip screenshot does not fit inside that.
//    So the page SLEEPS THE GAME LOOP two frames after the hit -- far enough in
//    for the ghost, the sparks and the shove to have rendered, still inside the
//    freeze -- and then the harness has all the time it needs.
await page.evaluate(() => {
  const sc = window.__meterfallDebug.game.scene.getScene("OverworldScene");
  const F = { log: [], pending: 0, frozen: false, armed: true };
  window.__frz = F;
  sc.events.on("postupdate", () => {
    if (F.pending > 0) {
      if (--F.pending === 0) {
        window.__meterfallDebug.game.loop.sleep();
        F.frozen = true;
      }
      return;
    }
    if (!F.armed || F.frozen) return;
    const a = sc.fight && sc.fight.simArena;
    const ev = a && a.events;
    if (ev && ev.length) {
      F.log.push(
        ev.map((e) => `${e.kind}/${e.tier}${e.heavy ? "/heavy" : ""} ${Math.round(e.damage)} on ${e.targetTeam}`).join(" + ")
      );
      F.pending = 2;
    }
  });
});

let shots = 0;
for (let i = 0; i < 200 && shots < WANT; i++) {
  const nav = await page.evaluate(() => {
    const a = window.__meterfallDebug.game.scene.getScene("OverworldScene").fight?.simArena;
    if (!a) return null;
    // A Fighter's position is `pos`, NOT `x`/`y` -- reading `f.x` gives NaN, and
    // `NaN > 17` is false, so an earlier cut of this stood still pressing J.
    const me = a.fighters.find((f) => f.team === "player");
    const foes = a.fighters.filter((f) => f.team === "enemy" && f.hp > 0);
    if (!me || !foes.length) return null;
    const dist = (f) => Math.hypot(f.pos.x - me.pos.x, f.pos.y - me.pos.y);
    let best = foes[0];
    for (const f of foes) if (dist(f) < dist(best)) best = f;
    return {
      dx: best.pos.x - me.pos.x,
      dy: best.pos.y - me.pos.y,
      d: dist(best),
      hp: a.fighters.map((f) => `${f.team}:${Math.round(f.hp)}/${f.maxHp}`),
      out: a.outcome,
    };
  });
  if (!nav) break;
  if (nav.out && nav.out !== "ongoing") {
    console.log("outcome: " + nav.out + "  " + nav.hp.join(" "));
    break;
  }
  const keys = [];
  if (nav.d > 17) {
    if (Math.abs(nav.dx) > 5) keys.push(nav.dx > 0 ? "ArrowRight" : "ArrowLeft");
    if (Math.abs(nav.dy) > 5) keys.push(nav.dy > 0 ? "ArrowDown" : "ArrowUp");
  }
  for (const k of keys) await page.keyboard.down(k);
  await page.waitForTimeout(keys.length ? 110 : 40);
  for (const k of keys) await page.keyboard.up(k);
  // Heavy every fourth swing: the tier scaling is the point, and a light hit
  // and a heavy hit are supposed to be visibly different amounts of violence.
  await page.keyboard.press(i % 4 === 3 ? "KeyK" : "KeyJ");
  await page.waitForTimeout(70);

  const frz = await page.evaluate(() => (window.__frz.frozen ? window.__frz.log[window.__frz.log.length - 1] : null));
  if (frz) {
    shots++;
    await page.screenshot({ path: `${OUT}/${String(shots).padStart(2, "0")}_impact.png` });
    console.log(`${String(shots).padStart(2, "0")}  ${frz}   [${nav.hp.join(" ")}]`);
    // LIST=1 dumps the arena's display list. Same reason capture.mjs grew
    // CAP_WINDOW: a thing in the frame can come from the venue composer, the
    // overworld's dressing, a scatter pass or the fight itself, and only the
    // live display list knows which. Sorted by depth, because the question is
    // usually "what is on top of the foe".
    if (process.env.LIST) {
      const list = await page.evaluate(() => {
        const sc = window.__meterfallDebug.game.scene.getScene("OverworldScene");
        const r = sc.fight.rect;
        return sc.children.list
          .filter((o) => o.x !== undefined && o.x > r.x - 20 && o.x < r.x + r.width + 20 && o.y > r.y - 60 && o.y < r.y + r.height + 20)
          .map((o) => ({
            t: o.type,
            key: String(o.texture?.key ?? ""),
            x: Math.round(o.x - r.x),
            y: Math.round(o.y - r.y),
            w: Math.round(o.displayWidth ?? 0),
            h: Math.round(o.displayHeight ?? 0),
            a: Number((o.alpha ?? 1).toFixed(2)),
            d: o.depth,
          }))
          .sort((a, b) => a.d - b.d);
      });
      for (const o of list) {
        console.log(`     d${String(o.d).padStart(6)} ${o.t.padEnd(9)} ${o.key.padEnd(26)} (${o.x},${o.y}) ${o.w}x${o.h} a${o.a}`);
      }
    }
    await page.evaluate(() => {
      window.__frz.frozen = false;
      window.__meterfallDebug.game.loop.wake();
    });
    await page.waitForTimeout(120);
  }
}
await page.evaluate(() => {
  window.__frz.armed = false;
  if (window.__frz.frozen) window.__meterfallDebug.game.loop.wake();
});
await page.waitForTimeout(200);
await page.screenshot({ path: `${OUT}/99_end.png` });
console.log(`${shots} impact frames -> ${OUT}`);
console.log("console errors: " + (errors.length ? JSON.stringify(errors.slice(0, 8), null, 1) : "none"));
await browser.close();
