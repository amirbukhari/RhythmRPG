import { describe, expect, it } from "vitest";
import { positionAtSeconds, nextBarBoundarySeconds, meterAtBar, eventSeconds, patternLengthSeconds } from "../../src/systems/combat/MeterSequence";
import type { MeterSegment } from "../../src/data/schemas/Beatmap";

const STRAIGHT_4_4: MeterSegment[] = [{ startBar: 1, bars: 8, num: 4, den: 4 }];

// Mirrors the shape of mid_biome_1: 4 bars of 3/4 then 4 bars of 6/8.
const CHANGING: MeterSegment[] = [
  { startBar: 1, bars: 4, num: 3, den: 4 },
  { startBar: 5, bars: 4, num: 6, den: 8 },
];

describe("MeterSequence.positionAtSeconds", () => {
  it("starts at bar 1 beat 1", () => {
    const pos = positionAtSeconds(STRAIGHT_4_4, 0, 120);
    expect(pos.bar).toBe(1);
    expect(pos.beat).toBe(1);
    expect(pos.beatsPerBar).toBe(4);
  });

  it("advances beat by beat within a bar at 120 BPM (0.5s/beat)", () => {
    expect(positionAtSeconds(STRAIGHT_4_4, 0.5, 120).beat).toBe(2);
    expect(positionAtSeconds(STRAIGHT_4_4, 1.0, 120).beat).toBe(3);
    expect(positionAtSeconds(STRAIGHT_4_4, 1.5, 120).beat).toBe(4);
  });

  it("advances to bar 2 after a full 4/4 bar (2s at 120 BPM)", () => {
    const pos = positionAtSeconds(STRAIGHT_4_4, 2.0, 120);
    expect(pos.bar).toBe(2);
    expect(pos.beat).toBe(1);
  });

  it("loops the pattern and keeps the global bar counter increasing", () => {
    // 8 bars * 2s/bar = 16s per loop.
    const pos = positionAtSeconds(STRAIGHT_4_4, 16.0, 120);
    expect(pos.bar).toBe(9); // not reset to 1
    expect(pos.beat).toBe(1);
    expect(pos.beatsPerBar).toBe(4);
  });

  it("reports the correct meter before and after a mid-encounter meter change", () => {
    // 3/4 at 120 BPM -> 1.5s/bar. Bars 1-4 are 3/4 (0s to 6s).
    const inThreeFour = positionAtSeconds(CHANGING, 3.0, 120);
    expect(inThreeFour.beatsPerBar).toBe(3);
    expect(inThreeFour.den).toBe(4);
    expect(inThreeFour.bar).toBe(3);

    // Bar 5 begins the 6/8 section at t=6s.
    const inSixEight = positionAtSeconds(CHANGING, 6.0, 120);
    expect(inSixEight.bar).toBe(5);
    expect(inSixEight.beatsPerBar).toBe(6);
    expect(inSixEight.den).toBe(8);
  });

  it("clamps negative/garbage input to the pattern start instead of throwing", () => {
    expect(() => positionAtSeconds(STRAIGHT_4_4, -5, 120)).not.toThrow();
    expect(positionAtSeconds(STRAIGHT_4_4, -5, 120).bar).toBe(1);
  });
});

describe("MeterSequence.nextBarBoundarySeconds", () => {
  it("returns the start of the next bar, never the current instant", () => {
    expect(nextBarBoundarySeconds(STRAIGHT_4_4, 0, 120)).toBe(2);
    expect(nextBarBoundarySeconds(STRAIGHT_4_4, 1, 120)).toBe(2);
    expect(nextBarBoundarySeconds(STRAIGHT_4_4, 2.01, 120)).toBe(4);
  });

  it("correctly straddles a meter change boundary", () => {
    // At t=5.9s (still in bar 4, the last 3/4 bar), the next boundary is t=6s (bar 5, 6/8).
    expect(nextBarBoundarySeconds(CHANGING, 5.9, 120)).toBeCloseTo(6.0, 5);
  });

  it("wraps correctly across a pattern loop boundary", () => {
    const patternLength = 8 * 2; // 8 bars * 2s/bar for STRAIGHT_4_4 at 120 BPM
    expect(nextBarBoundarySeconds(STRAIGHT_4_4, patternLength - 0.5, 120)).toBeCloseTo(patternLength, 5);
  });
});

describe("MeterSequence.meterAtBar", () => {
  it("maps global bars back onto the looped local pattern", () => {
    expect(meterAtBar(CHANGING, 1)).toEqual({ num: 3, den: 4 });
    expect(meterAtBar(CHANGING, 5)).toEqual({ num: 6, den: 8 });
    // Pattern is 8 bars total; global bar 9 is local bar 1 again.
    expect(meterAtBar(CHANGING, 9)).toEqual({ num: 3, den: 4 });
    expect(meterAtBar(CHANGING, 13)).toEqual({ num: 6, den: 8 });
  });

  it("handles a boss-style four-meter cycle (5/4, 7/8, 4/4, 3/4)", () => {
    const bossPhase3: MeterSegment[] = [
      { startBar: 1, bars: 4, num: 5, den: 4 },
      { startBar: 5, bars: 4, num: 7, den: 8 },
      { startBar: 9, bars: 4, num: 4, den: 4 },
      { startBar: 13, bars: 4, num: 3, den: 4 },
    ];
    expect(meterAtBar(bossPhase3, 1)).toEqual({ num: 5, den: 4 });
    expect(meterAtBar(bossPhase3, 5)).toEqual({ num: 7, den: 8 });
    expect(meterAtBar(bossPhase3, 9)).toEqual({ num: 4, den: 4 });
    expect(meterAtBar(bossPhase3, 13)).toEqual({ num: 3, den: 4 });
    expect(meterAtBar(bossPhase3, 17)).toEqual({ num: 5, den: 4 }); // loops back
  });
});

describe("MeterSequence.eventSeconds / patternLengthSeconds", () => {
  it("places bar 1 step 0 at zero", () => {
    expect(eventSeconds(STRAIGHT_4_4, 1, 0, 16, 120)).toBe(0);
  });

  it("divides a 4/4 bar evenly across 16 steps at 120 BPM (2s/bar)", () => {
    expect(eventSeconds(STRAIGHT_4_4, 1, 8, 16, 120)).toBeCloseTo(1.0, 5);
    expect(eventSeconds(STRAIGHT_4_4, 2, 0, 16, 120)).toBeCloseTo(2.0, 5);
  });

  it("uses the correct segment's bar length across a meter change (this is what BeatmapSonifier used to get wrong)", () => {
    // Bars 1-4 are 3/4 (1.5s/bar at 120 BPM) = 6s total, so bar 5 (start of 6/8) begins at t=6s.
    expect(eventSeconds(CHANGING, 5, 0, 16, 120)).toBeCloseTo(6.0, 5);
    // A step halfway through bar 5 (6/8, 3s/bar) lands at 6 + 1.5 = 7.5s.
    expect(eventSeconds(CHANGING, 5, 8, 16, 120)).toBeCloseTo(7.5, 5);
  });

  it("computes the full loop length as the sum of every segment's duration", () => {
    // 4 bars * 1.5s (3/4) + 4 bars * 3s (6/8) = 6 + 12 = 18s.
    expect(patternLengthSeconds(CHANGING, 120)).toBeCloseTo(18.0, 5);
  });
});
