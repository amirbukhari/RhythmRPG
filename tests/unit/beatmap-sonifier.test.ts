import { describe, expect, it } from "vitest";
import { beatmapEventSeconds } from "../../src/systems/audio/BeatmapSonifier";

describe("beatmapEventSeconds", () => {
  it("places bar 1 step 0 at zero", () => {
    expect(beatmapEventSeconds(1, 0, 120, 4, 16)).toBe(0);
  });

  it("advances by one full bar per bar increment at 120 BPM 4/4", () => {
    // 120 BPM -> 0.5s/beat -> 2s/bar.
    expect(beatmapEventSeconds(2, 0, 120, 4, 16)).toBe(2);
    expect(beatmapEventSeconds(3, 0, 120, 4, 16)).toBe(4);
  });

  it("divides a bar evenly across its subdivision steps", () => {
    // 2s/bar over 16 steps -> 0.125s/step.
    expect(beatmapEventSeconds(1, 8, 120, 4, 16)).toBeCloseTo(1.0, 5);
    expect(beatmapEventSeconds(1, 16, 120, 4, 16)).toBeCloseTo(2.0, 5);
  });

  it("scales with effective (speed-adjusted) BPM, not just the authored BPM", () => {
    const fullSpeed = beatmapEventSeconds(2, 0, 120, 4, 16);
    const halfSpeed = beatmapEventSeconds(2, 0, 60, 4, 16);
    expect(halfSpeed).toBeCloseTo(fullSpeed * 2, 5);
  });
});
