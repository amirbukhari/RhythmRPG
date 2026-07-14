import type { SongMap } from "../../data/schemas/SongMap";
import type { BeatTier } from "../action/ActionCombat";

/** §8.3 judgment windows (seconds from the nearest beat), pre-assist. */
export const TIER_WINDOWS = { perfect: 0.045, great: 0.09, good: 0.14 } as const;

/** Grade a distance-from-beat into the four §8.3 tiers. `assistMultiplier`
 * widens every window (accessibility assist, §9.3). */
export function tierForOffset(offsetSeconds: number, assistMultiplier = 1): BeatTier {
  const off = Math.abs(offsetSeconds);
  if (off < TIER_WINDOWS.perfect * assistMultiplier) return "perfect";
  if (off < TIER_WINDOWS.great * assistMultiplier) return "great";
  if (off < TIER_WINDOWS.good * assistMultiplier) return "good";
  return "off";
}

/** Grade a file position against the song grid (calibration applied first). */
export function tierAt(map: SongMap, positionSeconds: number, calibrationOffsetMs: number, assistMultiplier = 1): BeatTier {
  return tierForOffset(nearestBeatDistanceSeconds(map, positionSeconds - calibrationOffsetMs / 1000), assistMultiplier);
}

/**
 * Pure beat math over a SongMap grid (PRD §8.3 "beat truth").
 *
 * Everything here works in FILE-TIME seconds (the playing element's
 * `currentTime`), never wall-clock and never the transport: the judged beat
 * is derived from the position of the audio the player is actually hearing,
 * so playbackRate changes (game speed) and element loops can never split the
 * heard beat from the judged one.
 */

/** Insertion index of posMs in the (strictly increasing) grid. */
function lowerBound(beats: number[], posMs: number): number {
  let lo = 0;
  let hi = beats.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (beats[mid] < posMs) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

/**
 * Seconds from a file position to the nearest grid beat, loop-aware: the
 * element loops at durationMs, so just after the end the next loop's first
 * beat is near, and just after the start the previous loop's last beat is.
 */
export function nearestBeatDistanceSeconds(map: SongMap, positionSeconds: number): number {
  const beats = map.beatTimesMs;
  if (beats.length === 0) return Infinity;
  const posMs = positionSeconds * 1000;
  const i = lowerBound(beats, posMs);
  let best = Infinity;
  if (i < beats.length) best = Math.min(best, Math.abs(beats[i] - posMs));
  if (i > 0) best = Math.min(best, Math.abs(beats[i - 1] - posMs));
  if (map.durationMs > 0) {
    best = Math.min(best, Math.abs(beats[0] + map.durationMs - posMs)); // next loop's first beat
    best = Math.min(best, Math.abs(posMs + map.durationMs - beats[beats.length - 1])); // previous loop's last beat
  }
  return best / 1000;
}

/**
 * Is a file position on the beat? `calibrationOffsetMs` uses the same
 * semantics as the transport path always has (subtracted before judgment);
 * `windowSeconds` is the already-assist-scaled judgment window.
 */
export function isOnBeat(map: SongMap, positionSeconds: number, calibrationOffsetMs: number, windowSeconds: number): boolean {
  return nearestBeatDistanceSeconds(map, positionSeconds - calibrationOffsetMs / 1000) < windowSeconds;
}

/** Index of the last grid beat at or before the position (-1 before beat 0). */
export function beatIndexAt(map: SongMap, positionSeconds: number): number {
  return lowerBound(map.beatTimesMs, positionSeconds * 1000 + 0.5) - 1;
}
