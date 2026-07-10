import { describe, expect, it } from "vitest";
import { beatmaps } from "../../src/data/ContentRegistry";
import { battleTrackUrl, knownBattleTrackIds } from "../../src/systems/audio/BattleTracks";

/**
 * Every authored beatmap should have a rendered chiptune track
 * (tools/gbmusic/render_all_tracks.py), and every rendered track should
 * correspond to a real beatmap -- a rename on either side must fail loudly
 * here instead of silently degrading a battle to sonifier-only audio.
 */
describe("BattleTracks", () => {
  it("has a rendered track URL for every content beatmap", () => {
    for (const trackId of beatmaps.keys()) {
      expect(battleTrackUrl(trackId), `beatmap "${trackId}" has no rendered battle track`).toBeTruthy();
    }
  });

  it("has no track entries pointing at nonexistent beatmaps", () => {
    for (const trackId of knownBattleTrackIds()) {
      expect(beatmaps.has(trackId), `battle track "${trackId}" has no matching beatmap`).toBe(true);
    }
  });

  it("returns undefined for unknown trackIds (sonifier-only fallback path)", () => {
    expect(battleTrackUrl("not_a_real_track")).toBeUndefined();
  });
});
