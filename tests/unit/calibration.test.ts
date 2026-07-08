import { describe, expect, it } from "vitest";
import { computeCalibrationOffsetMs, offsetFromNearestBeat, CALIBRATION_MAX_OFFSET_MS } from "../../src/systems/audio/Calibration";

describe("Calibration", () => {
  it("reports zero offset for a tap exactly on the beat", () => {
    expect(offsetFromNearestBeat(2.0, 0.5)).toBe(0);
  });

  it("reports a positive offset for a late tap", () => {
    expect(offsetFromNearestBeat(2.05, 0.5)).toBeCloseTo(50, 0);
  });

  it("reports a negative offset for an early tap", () => {
    expect(offsetFromNearestBeat(1.96, 0.5)).toBeCloseTo(-40, 0);
  });

  it("averages offsets across multiple taps", () => {
    // beats at 0, 0.5, 1.0, 1.5 (interval 0.5s); taps are +20ms, +20ms, +20ms, +20ms late
    const taps = [0.02, 0.52, 1.02, 1.52];
    expect(computeCalibrationOffsetMs(taps, 0.5)).toBe(20);
  });

  it("returns 0 for no taps instead of dividing by zero", () => {
    expect(computeCalibrationOffsetMs([], 0.5)).toBe(0);
  });

  it("clamps an extreme positive offset to the configured maximum", () => {
    expect(computeCalibrationOffsetMs([0.15], 0.5)).toBe(CALIBRATION_MAX_OFFSET_MS);
  });

  it("clamps an extreme negative offset to the configured minimum", () => {
    expect(computeCalibrationOffsetMs([0.35], 0.5)).toBe(-CALIBRATION_MAX_OFFSET_MS);
  });
});
