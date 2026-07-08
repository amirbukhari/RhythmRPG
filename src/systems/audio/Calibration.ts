/**
 * Pure calibration math, kept separate from CalibrationScene so it's
 * testable without Tone.js/Phaser. Given a fixed beat interval and the
 * transport-clock timestamps of the player's taps, computes each tap's
 * offset from its nearest beat and returns the clamped average -- the
 * global AV sync offset applied to all judgment (PRD §8.3, §9.3).
 */

export const CALIBRATION_BPM = 100;
export const CALIBRATION_BEAT_SECONDS = 60 / CALIBRATION_BPM;
export const CALIBRATION_TAP_COUNT = 8;
export const CALIBRATION_MAX_OFFSET_MS = 150;

export function offsetFromNearestBeat(tapTransportSeconds: number, beatIntervalSeconds: number): number {
  const nearestBeat = Math.round(tapTransportSeconds / beatIntervalSeconds) * beatIntervalSeconds;
  return (tapTransportSeconds - nearestBeat) * 1000;
}

export function computeCalibrationOffsetMs(tapTransportSecondsList: number[], beatIntervalSeconds = CALIBRATION_BEAT_SECONDS): number {
  if (tapTransportSecondsList.length === 0) return 0;
  const offsets = tapTransportSecondsList.map((t) => offsetFromNearestBeat(t, beatIntervalSeconds));
  const average = offsets.reduce((sum, o) => sum + o, 0) / offsets.length;
  return Math.max(-CALIBRATION_MAX_OFFSET_MS, Math.min(CALIBRATION_MAX_OFFSET_MS, Math.round(average)));
}
