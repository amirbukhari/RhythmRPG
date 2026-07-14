import { test, expect, type Page } from "@playwright/test";
import { bootToOverworld, isSceneActive } from "./helpers";

/**
 * BEAT TRUTH (PRD §8.3, release gate #1a): in the shipped in-world fight, the
 * judged beat must be derived from the song that is actually playing -- its
 * authored beat grid read through the live element's position -- and game
 * speed must scale the song's playbackRate together with judgment.
 *
 * Headless Chromium plays media (muted) with real currentTime advance, and
 * the audio gate is passed with a real key gesture, so autoplay policy is
 * satisfied and the full audible path is exercised here -- not the fallback.
 */

interface FightSeams {
  fight: {
    songMap: { songId: string; beatTimesMs: number[] } | null;
    isOnBeat(): boolean;
  } | null;
  debugTeleportToNode(nodeId: string): void;
}

const COMBAT_SONGS = ["glassriff", "johns_anus", "truckers_for_christ"];

async function startFirstFight(page: Page): Promise<void> {
  await page.evaluate(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as FightSeams;
    scene.debugTeleportToNode("opening_1");
  });
  await page.waitForFunction(() => {
    const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as { fight: { simArena: unknown } | null };
    return Boolean(scene.fight && scene.fight.simArena);
  });
}

test.describe("beat truth (PRD §8.3)", () => {
  test("the fight judges against the beat map of the song that is audibly playing", async ({ page }) => {
    await bootToOverworld(page);

    // Exploring plays the explore song for real (audio gate was a genuine
    // key gesture, so play() was allowed): position must advance. Generous
    // timeout: the first play() triggers the element's first fetch of a
    // multi-MB MP3 from a cold preview server (observed slow once in CI-like
    // conditions), and that latency is delivery, not a beat-truth failure.
    await page.waitForFunction(() => window.__meterfallDebug.music.currentSongId() === "deereater", undefined, { timeout: 45_000 });
    await page.waitForFunction(
      () => {
        const p = window.__meterfallDebug.music.position();
        return p !== null && p > 0.1;
      },
      undefined,
      { timeout: 45_000 }
    );

    await startFirstFight(page);
    expect(await isSceneActive(page, "OverworldScene")).toBe(true);

    // The fight resolved the PLAYING combat song's beat map -- not a beatmap
    // grid unrelated to the audio (the pre-P1 two-clock bug).
    const state = await page.evaluate(() => {
      const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as FightSeams;
      return {
        songMapId: scene.fight!.songMap?.songId ?? null,
        playingId: window.__meterfallDebug.music.currentSongId(),
        beats: scene.fight!.songMap?.beatTimesMs.length ?? 0,
      };
    });
    expect(state.songMapId).not.toBeNull();
    expect(state.songMapId).toBe(state.playingId);
    expect(COMBAT_SONGS).toContain(state.songMapId);
    expect(state.beats).toBeGreaterThan(100);

    // And the judged beat actually flips with the playing song: sampled
    // across a beat interval, isOnBeat() must be true near beats and false
    // between them (a constant answer means judgment is not tracking audio).
    const samples = await page.evaluate(async () => {
      const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as FightSeams;
      const seen: boolean[] = [];
      for (let i = 0; i < 30; i++) {
        seen.push(scene.fight!.isOnBeat());
        await new Promise((r) => setTimeout(r, 33));
      }
      return seen;
    });
    expect(samples).toContain(true);
    expect(samples).toContain(false);
  });

  test("game speed scales the song's playbackRate together with judgment (§8.3.3)", async ({ page }) => {
    await bootToOverworld(page);
    await page.evaluate(() => {
      window.__meterfallDebug.GameContext.activeProfile!.settings.gameSpeed = 0.7;
    });
    await startFirstFight(page);

    const rate = await page.evaluate(() => {
      const m = window.__meterfallDebug.music as unknown as { current: HTMLAudioElement | null };
      return m.current?.playbackRate ?? null;
    });
    expect(rate).toBeCloseTo(0.7, 5);

    // The judged grid lives in file-time, so with the element slowed the
    // heard and judged beat stay one thing by construction; nothing else to
    // assert beyond the coupling itself -- but the fight must still judge:
    const flips = await page.evaluate(async () => {
      const scene = window.__meterfallDebug.game.scene.getScene("OverworldScene") as unknown as FightSeams;
      const seen = new Set<boolean>();
      for (let i = 0; i < 40; i++) {
        seen.add(scene.fight!.isOnBeat());
        await new Promise((r) => setTimeout(r, 33));
      }
      return [...seen];
    });
    expect(flips).toContain(true);
    expect(flips).toContain(false);
  });
});
