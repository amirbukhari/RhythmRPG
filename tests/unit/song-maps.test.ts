import { describe, expect, it } from "vitest";
import { songMaps, getSongMap } from "../../src/data/ContentRegistry";
import { ContentValidationError, loadSongMap } from "../../src/data/ContentLoader";

/** Every song SongPlayer can pick (mode -> song, PRD §11.2). */
const SHIPPED_SONGS = ["sunshine_sally", "deereater", "glassriff", "johns_anus", "truckers_for_christ", "quotience"];

describe("song beat maps (PRD §8.3)", () => {
  it("ships a validated beat map for every song the game can play", () => {
    expect(songMaps.size).toBe(SHIPPED_SONGS.length);
    for (const id of SHIPPED_SONGS) expect(getSongMap(id).songId).toBe(id);
  });

  it("every combat-capable song has a dense, plausible grid", () => {
    // combat rotation + boss: the songs fights are judged against
    for (const id of ["glassriff", "johns_anus", "truckers_for_christ", "quotience"]) {
      const map = getSongMap(id);
      expect(map.bpm).toBeGreaterThan(60);
      expect(map.bpm).toBeLessThan(200);
      // grid spans essentially the whole file (no dead judgment stretches):
      const last = map.beatTimesMs[map.beatTimesMs.length - 1];
      expect(last).toBeGreaterThan(map.durationMs * 0.95);
      // and is roughly one beat per 60/bpm seconds
      const expected = (map.durationMs / 1000) * (map.bpm / 60);
      expect(map.beatTimesMs.length).toBeGreaterThan(expected * 0.8);
      expect(map.beatTimesMs.length).toBeLessThan(expected * 1.2);
    }
  });

  it("rejects a non-monotonic grid", () => {
    expect(() =>
      loadSongMap({
        songId: "bad",
        bpm: 120,
        firstBeatOffsetMs: 0,
        durationMs: 10000,
        beatTimesMs: [0, 500, 400, 1500, 2000, 2500, 3000, 3500],
      })
    ).toThrow(ContentValidationError);
  });

  it("rejects a grid whose first beat disagrees with firstBeatOffsetMs", () => {
    expect(() =>
      loadSongMap({
        songId: "bad",
        bpm: 120,
        firstBeatOffsetMs: 250,
        durationMs: 10000,
        beatTimesMs: [0, 500, 1000, 1500, 2000, 2500, 3000, 3500],
      })
    ).toThrow(ContentValidationError);
  });

  it("rejects beats past the end of the file", () => {
    expect(() =>
      loadSongMap({
        songId: "bad",
        bpm: 120,
        firstBeatOffsetMs: 0,
        durationMs: 3000,
        beatTimesMs: [0, 500, 1000, 1500, 2000, 2500, 3000, 3500],
      })
    ).toThrow(ContentValidationError);
  });
});
