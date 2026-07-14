import { describe, expect, it } from "vitest";
import { nearestBeatDistanceSeconds, isOnBeat, beatIndexAt } from "../../src/systems/audio/SongBeat";
import type { SongMap } from "../../src/data/schemas/SongMap";

/** A 120bpm-ish grid with real-recording drift baked in (uneven intervals). */
const drifty: SongMap = {
  songId: "test",
  bpm: 120,
  firstBeatOffsetMs: 250,
  durationMs: 3000,
  beatTimesMs: [250, 750, 1260, 1750, 2240, 2750],
};

describe("SongBeat (PRD §8.3 beat truth)", () => {
  it("distance is zero exactly on a grid beat", () => {
    expect(nearestBeatDistanceSeconds(drifty, 0.25)).toBe(0);
    expect(nearestBeatDistanceSeconds(drifty, 1.26)).toBeCloseTo(0, 6);
  });

  it("snaps to the NEAREST beat of an uneven (drifty) grid, not a constant-bpm line", () => {
    // 1.5s sits between the 1.26 and 1.75 drifted beats; a constant 120bpm
    // line anchored at 0.25 would call 1.25 a beat and 1.5 a 0-distance
    // half-beat error. The grid math must use the real tracked times.
    expect(nearestBeatDistanceSeconds(drifty, 1.5)).toBeCloseTo(0.24, 6);
    expect(nearestBeatDistanceSeconds(drifty, 1.3)).toBeCloseTo(0.04, 6);
  });

  it("wraps across the loop point: just before the end, next loop's first beat is near", () => {
    // At 2.95s, last beat (2.75) is 0.2 away, but beat 0 of the next loop
    // (0.25 + 3.0 = 3.25) is 0.3 away -- nearest is still 0.2. At 3.2 (i.e.
    // an element that reports slightly past duration pre-wrap) beat 0 of the
    // next loop is 0.05 away.
    expect(nearestBeatDistanceSeconds(drifty, 2.95)).toBeCloseTo(0.2, 6);
    expect(nearestBeatDistanceSeconds(drifty, 3.2)).toBeCloseTo(0.05, 6);
  });

  it("wraps across the loop point: just after a loop restart, previous loop's last beat is near", () => {
    // At 0.05s the first beat (0.25) is 0.2 away; the previous loop's last
    // beat (2.75 - 3.0 = -0.25) is 0.3 away -- nearest 0.2. At 0.01 the
    // previous loop's last beat is 0.26 away vs first beat 0.24.
    expect(nearestBeatDistanceSeconds(drifty, 0.05)).toBeCloseTo(0.2, 6);
    expect(nearestBeatDistanceSeconds(drifty, 0.01)).toBeCloseTo(0.24, 6);
  });

  it("isOnBeat applies the calibration offset before judgment (same semantics as the transport path)", () => {
    // Position 0.30 is 50ms late of the 0.25 beat: on-beat inside a 90ms
    // window. With calibration +100ms the judged time becomes 0.20 (50ms
    // early) -- still on-beat; with +250ms it becomes 0.05 -- off.
    expect(isOnBeat(drifty, 0.3, 0, 0.09)).toBe(true);
    expect(isOnBeat(drifty, 0.3, 100, 0.09)).toBe(true);
    expect(isOnBeat(drifty, 0.3, 250, 0.09)).toBe(false);
  });

  it("a widened (assist) window admits what the base window rejects", () => {
    // 1.5s is 0.24 from the nearest beat: off at 90ms, off at 135ms
    // (0.09 * 1.5 assist), on with a deliberately huge window.
    expect(isOnBeat(drifty, 1.5, 0, 0.09)).toBe(false);
    expect(isOnBeat(drifty, 1.5, 0, 0.09 * 1.5)).toBe(false);
    expect(isOnBeat(drifty, 1.5, 0, 0.25)).toBe(true);
  });

  it("beatIndexAt reports the last crossed beat (-1 before the first)", () => {
    expect(beatIndexAt(drifty, 0.0)).toBe(-1);
    expect(beatIndexAt(drifty, 0.25)).toBe(0);
    expect(beatIndexAt(drifty, 0.5)).toBe(0);
    expect(beatIndexAt(drifty, 1.26)).toBe(2);
    expect(beatIndexAt(drifty, 2.9)).toBe(5);
  });
});
