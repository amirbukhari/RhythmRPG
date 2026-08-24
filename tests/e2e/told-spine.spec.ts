import { test, expect } from "@playwright/test";
import { passAudioGate, isSceneActive, waitForScene } from "./helpers";

/**
 * The two told beats the finale depends on and that had no equivalent in the
 * old canon (world-bible §9 beats 5-6): The Den and The Sitting-Down. Like the
 * Rite, these must NOT run under `?nocutscenes=1` -- the whole risk they guard
 * against (style contract §4.10) is a story beat that silently never fires while
 * every gate stays green. So this spec drives the real triggers.
 */
test.describe("the told spine (world-bible §9 beats 5-6)", () => {
  // Boot to the overworld the long way (cutscenes live), playing the Rite
  // through so its flag is set and it will not re-fire when we restart the
  // scene below. Returns with an active OverworldScene.
  async function bootPastRite(page: import("@playwright/test").Page): Promise<void> {
    await page.goto("/");
    await passAudioGate(page);
    await page.keyboard.press("Enter"); // -> SaveScene
    await waitForScene(page, "SaveScene");
    await page.keyboard.press("Enter"); // -> CalibrationScene
    await waitForScene(page, "CalibrationScene");
    for (let i = 0; i < 20 && (await isSceneActive(page, "CalibrationScene")); i++) {
      await page.keyboard.press("Space");
      await page.waitForTimeout(400);
    }
    await waitForScene(page, "CutsceneScene"); // the Rite
    await page.evaluate(() => {
      const cs = window.__meterfallDebug.game.scene.getScene("CutsceneScene") as unknown as Phaser.Scene;
      (cs as unknown as { finish: () => void })["finish"]?.();
    });
    // If the private finish() seam ever moves, fall back to skipping on ESC.
    for (let i = 0; i < 40 && (await isSceneActive(page, "CutsceneScene")); i++) {
      await page.keyboard.press("Escape");
      await page.waitForTimeout(150);
    }
    await waitForScene(page, "OverworldScene");
  }

  test("The Den fires the moment the den's mouth (node_19) is cleared", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    page.on("pageerror", (e) => errors.push(String(e)));

    await bootPastRite(page);

    // Simulate returning from the node_19 victory: WorldFight sets
    // returnToNodeId and the scene re-creates onto it. OverworldScene.create
    // reads that node and, one tick later, fires The Den off it.
    await page.evaluate(() => {
      const dbg = window.__meterfallDebug;
      const flags = dbg.GameContext.activeProfile!.storyFlags ?? (dbg.GameContext.activeProfile!.storyFlags = []);
      if (!flags.includes("seen_rite")) flags.push("seen_rite");
      dbg.GameContext.returnToNodeId = "node_19";
      const map = dbg.game.scene.getScene("OverworldScene") as unknown as Phaser.Scene;
      map.scene.restart();
    });

    await waitForScene(page, "CutsceneScene");
    const id = await page.evaluate(() => {
      const s = window.__meterfallDebug.game.scene.getScene("CutsceneScene") as unknown as { cutscene: { id: string } };
      return s.cutscene.id;
    });
    expect(id).toBe("the_den");

    // Play it through on real input; it sets its flag and resumes the world.
    for (let i = 0; i < 40 && (await isSceneActive(page, "CutsceneScene")); i++) {
      await page.keyboard.press("Space");
      await page.waitForTimeout(200);
    }
    await waitForScene(page, "OverworldScene");
    const flags = await page.evaluate(() => window.__meterfallDebug.GameContext.activeProfile?.storyFlags ?? []);
    expect(flags).toContain("seen_den");
    expect(errors).toEqual([]);
  });

  test("The Sitting-Down plays through -- black-field finale and all -- and names her", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    page.on("pageerror", (e) => errors.push(String(e)));

    await bootPastRite(page);

    // Drive the beat directly over the overworld (its own region-4 trigger needs
    // a full Scar traversal). This proves the frames render -- including the
    // deliberate black-field final frame, which has no painted plate by design.
    await page.evaluate(() => {
      const map = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as Phaser.Scene;
      map.scene.launch("CutsceneScene", { cutsceneId: "the_sitting_down", resumeKey: "OverworldScene" });
    });
    await waitForScene(page, "CutsceneScene");

    const info = await page.evaluate(() => {
      const s = window.__meterfallDebug.game.scene.getScene("CutsceneScene") as unknown as {
        cutscene: { id: string; frames: { stage: string; lines: string[] }[] };
      };
      const last = s.cutscene.frames[s.cutscene.frames.length - 1];
      return { id: s.cutscene.id, lastLine: last.lines[last.lines.length - 1], stages: s.cutscene.frames.map((f) => f.stage) };
    });
    expect(info.id).toBe("the_sitting_down");
    expect(info.lastLine).toBe("Lunal.");
    expect(info.stages).toContain("black"); // the intentional void as he says the name

    for (let i = 0; i < 40 && (await isSceneActive(page, "CutsceneScene")); i++) {
      await page.keyboard.press("Space");
      await page.waitForTimeout(200);
    }
    await waitForScene(page, "OverworldScene");
    const flags = await page.evaluate(() => window.__meterfallDebug.GameContext.activeProfile?.storyFlags ?? []);
    expect(flags).toContain("seen_sitting");
    expect(errors).toEqual([]);
  });
});
