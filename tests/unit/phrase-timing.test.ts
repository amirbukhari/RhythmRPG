import { describe, expect, it } from "vitest";
import { nextBarBoundary, parseBarBeat, timingTemplateToSeconds } from "../../src/systems/combat/PhraseTiming";

describe("PhraseTiming", () => {
  it("parses bar.beat tokens", () => {
    expect(parseBarBeat("1.3")).toEqual({ bar: 1, beat: 3 });
    expect(parseBarBeat("2.1")).toEqual({ bar: 2, beat: 1 });
  });

  it("rejects a malformed token", () => {
    expect(() => parseBarBeat("bad")).toThrow();
  });

  it("converts a single-bar timing template to seconds at 120 BPM 4/4", () => {
    // 120 BPM -> 0.5s/beat. Phrase starts at t=10.
    const seconds = timingTemplateToSeconds(["1.1", "1.2", "1.3"], 10, 120, 4);
    expect(seconds).toEqual([10, 10.5, 11]);
  });

  it("carries bar offsets into a two-bar template", () => {
    const seconds = timingTemplateToSeconds(["1.1", "2.1"], 0, 120, 4);
    // bar 2 beat 1 = 4 beats after bar 1 beat 1 = 4 * 0.5s = 2s later.
    expect(seconds).toEqual([0, 2]);
  });

  it("scales with tempo", () => {
    const seconds = timingTemplateToSeconds(["1.1", "1.2"], 0, 60, 4); // 60 BPM -> 1s/beat
    expect(seconds).toEqual([0, 1]);
  });

  it("rounds up to the next full bar for the count-in, never the current instant", () => {
    // 120 BPM 4/4 -> bar length 2s. At t=0 exactly, still require a full bar.
    expect(nextBarBoundary(0, 120, 4)).toBe(2);
    // Mid-bar should round up to the upcoming boundary.
    expect(nextBarBoundary(1, 120, 4)).toBe(2);
    // Just past a boundary should round up to the next one, not the one just passed.
    expect(nextBarBoundary(2.01, 120, 4)).toBe(4);
  });
});
