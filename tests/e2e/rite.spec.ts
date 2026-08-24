import { test, expect } from "@playwright/test";
import { passAudioGate, isSceneActive, waitForScene } from "./helpers";

/**
 * The Rite is the beat that seats the entire premise: the obelisk opens, the
 * stone child speaks the year's rule, and the rule condemns Nari. world-bible
 * §6.1 -- everything the player later does is a response to this.
 *
 * It is the ONE spec that must not pass `?nocutscenes=1`. It exists because the
 * beat was invisible for a long time and nothing caught it: `CutsceneScene.play`
 * used to return false in any dev build, so the story beats were the only part
 * of the game that could never be seen outside a production bundle. The trigger
 * in OverworldScene was correct the whole time -- there was simply no test that
 * a new game shows it.
 */
test.describe("the Rite (world-bible §6.1)", () => {
  test("fires unprompted on a new game, paints its plates, and seats the premise", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    page.on("pageerror", (e) => errors.push(String(e)));

    // deliberately NOT ?nocutscenes=1 -- this is the spec that watches it play
    await page.goto("/");
    await passAudioGate(page);

    // Calibration is driven inline rather than through `createSaveAndCalibrate`,
    // and the reason is worth writing down: Phaser's `scene.isActive()` is FALSE
    // for a PAUSED scene, and the Rite pauses the overworld ~20ms after it
    // starts. So the shared helper -- which ends by waiting for an *active*
    // OverworldScene -- can never succeed while cutscenes play. That is exactly
    // why `bootToOverworld` opts out of them.
    await page.keyboard.press("Enter"); // Start/Continue -> SaveScene
    await waitForScene(page, "SaveScene");
    await page.keyboard.press("Enter"); // + New Save -> CalibrationScene
    await waitForScene(page, "CalibrationScene");
    // Tap until calibration hands off. Stop pressing the moment it does, so no
    // stray Space advances a cutscene line before it has been looked at.
    for (let i = 0; i < 20 && (await isSceneActive(page, "CalibrationScene")); i++) {
      await page.keyboard.press("Space");
      await page.waitForTimeout(400);
    }

    // It self-gates on the "seen_rite" story flag and is deferred one tick past
    // create(), so it arrives just after the overworld does -- unprompted.
    await waitForScene(page, "CutsceneScene");

    // Every stage the Rite stages must be a painted plate (tools/art/plates.py),
    // not the procedural fallback: the stone child was two grey circles with two
    // dark dots for eyes, against world-bible §0's "an abstraction is not an image."
    const stages = await page.evaluate(() => {
      const s = window.__meterfallDebug.game.scene.getScene("CutsceneScene") as unknown as {
        cutscene: { id: string; frames: { stage: string }[] };
      };
      const textures = window.__meterfallDebug.game.textures;
      return s.cutscene.frames.map((f) => ({ stage: f.stage, painted: textures.exists(`plate_${f.stage}`) }));
    });
    expect(stages.length).toBeGreaterThan(3);
    expect(stages.every((s) => s.painted)).toBe(true);
    // and it must reach the house -- the silence beat, where neither of them
    // has the argument (world-bible §6.1: "That is the point.")
    expect(stages.map((s) => s.stage)).toContain("house");

    // Play it through on real input. Every line advances on a key; the scene
    // stops itself at the end and resumes the world underneath.
    for (let i = 0; i < 60 && (await isSceneActive(page, "CutsceneScene")); i++) {
      await page.keyboard.press("Space");
      await page.waitForTimeout(220);
    }
    expect(await isSceneActive(page, "CutsceneScene")).toBe(false);
    await waitForScene(page, "OverworldScene");

    // It sets its flag, so it never plays twice.
    const flags = await page.evaluate(() => window.__meterfallDebug.GameContext.activeProfile?.storyFlags ?? []);
    expect(flags).toContain("seen_rite");

    expect(errors).toEqual([]);
  });
});
