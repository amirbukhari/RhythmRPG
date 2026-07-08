import type { MeterSegment } from "../../data/schemas/Beatmap";

/**
 * Walks a beatmap's meterSequence to answer "what bar/beat/meter is it right
 * now" and "when does bar N start" -- the piece PRD §8.7's live meter
 * changes and release gate #3 ("the final boss reliably executes authored
 * meter changes on bar boundary without drift") actually depend on.
 * BattleScene previously read only meterSequence[0].num once and used it for
 * the whole encounter, which is correct for a straight-4/4 fight but cannot
 * represent a meter change at all. Pure and Phaser-free, like the rest of
 * the combat/timing modules, so it's directly unit-testable.
 *
 * The authored meterSequence covers one pattern cycle; once elapsed time
 * exceeds it, the cycle loops (matching BeatmapSonifier's audio looping)
 * while the reported bar number keeps counting up globally.
 */

export function totalPatternBars(meterSequence: MeterSegment[]): number {
  return meterSequence.reduce((sum, s) => sum + s.bars, 0);
}

/** Seconds from the start of the pattern to the start of `localBar` (1-indexed, may be totalBars+1 to get the full loop length). */
function cumulativeBarStartSeconds(meterSequence: MeterSegment[], localBar: number, bpm: number): number {
  let seconds = 0;
  for (const segment of meterSequence) {
    const segmentEndBar = segment.startBar + segment.bars; // exclusive
    if (localBar <= segment.startBar) break;
    const barsInThisSegment = Math.min(localBar, segmentEndBar) - segment.startBar;
    const secondsPerBar = (60 / bpm) * segment.num;
    seconds += barsInThisSegment * secondsPerBar;
    if (localBar <= segmentEndBar) break;
  }
  return seconds;
}

function segmentForLocalBar(meterSequence: MeterSegment[], localBar: number): MeterSegment {
  for (const segment of meterSequence) {
    if (localBar >= segment.startBar && localBar < segment.startBar + segment.bars) return segment;
  }
  return meterSequence[meterSequence.length - 1];
}

export interface MeterPosition {
  /** Global, ever-increasing bar number (does not reset when the pattern loops). */
  bar: number;
  /** 1-indexed beat within the current bar. */
  beat: number;
  beatsPerBar: number;
  den: number;
  secondsIntoBar: number;
}

export function positionAtSeconds(meterSequence: MeterSegment[], elapsedSeconds: number, bpm: number): MeterPosition {
  const patternBars = totalPatternBars(meterSequence);
  const patternLengthSeconds = cumulativeBarStartSeconds(meterSequence, patternBars + 1, bpm);
  const safeElapsed = Math.max(0, elapsedSeconds);
  const loopIndex = patternLengthSeconds > 0 ? Math.floor(safeElapsed / patternLengthSeconds) : 0;
  const localSeconds = safeElapsed - loopIndex * patternLengthSeconds;

  // Find the local bar containing localSeconds by walking cumulative bar starts.
  let localBar = 1;
  let barStart = 0;
  for (let candidate = 1; candidate <= patternBars; candidate++) {
    const nextBarStart = cumulativeBarStartSeconds(meterSequence, candidate + 1, bpm);
    if (localSeconds < nextBarStart || candidate === patternBars) {
      localBar = candidate;
      barStart = cumulativeBarStartSeconds(meterSequence, candidate, bpm);
      break;
    }
  }

  const segment = segmentForLocalBar(meterSequence, localBar);
  const secondsPerBeat = 60 / bpm;
  const secondsIntoBar = localSeconds - barStart;
  const beat = Math.floor(secondsIntoBar / secondsPerBeat) + 1;

  return {
    bar: loopIndex * patternBars + localBar,
    beat: Math.min(beat, segment.num),
    beatsPerBar: segment.num,
    den: segment.den,
    secondsIntoBar,
  };
}

/** Absolute transport seconds at which the next bar boundary (relative to `fromSeconds`) begins, always at least one instant in the future. */
export function nextBarBoundarySeconds(meterSequence: MeterSegment[], fromSeconds: number, bpm: number): number {
  const patternBars = totalPatternBars(meterSequence);
  const patternLengthSeconds = cumulativeBarStartSeconds(meterSequence, patternBars + 1, bpm);
  const loopIndex = patternLengthSeconds > 0 ? Math.floor(Math.max(0, fromSeconds) / patternLengthSeconds) : 0;
  const loopBase = loopIndex * patternLengthSeconds;

  for (let candidate = 1; candidate <= patternBars + 1; candidate++) {
    const boundary = loopBase + cumulativeBarStartSeconds(meterSequence, candidate, bpm);
    if (boundary > fromSeconds) return boundary;
  }
  return loopBase + patternLengthSeconds; // fallback: start of next loop
}

/** The meter (num/den) in effect at the given global bar's local equivalent. */
export function meterAtBar(meterSequence: MeterSegment[], globalBar: number): { num: number; den: number } {
  const patternBars = totalPatternBars(meterSequence);
  const localBar = ((globalBar - 1) % patternBars) + 1;
  const segment = segmentForLocalBar(meterSequence, localBar);
  return { num: segment.num, den: segment.den };
}

/** Total seconds for one full loop of the authored pattern, meter-changes included. */
export function patternLengthSeconds(meterSequence: MeterSegment[], bpm: number): number {
  return cumulativeBarStartSeconds(meterSequence, totalPatternBars(meterSequence) + 1, bpm);
}

/**
 * Converts a beatmap event's (bar, step-at-subdivision-resolution) into
 * pattern-relative seconds, using whichever meter segment covers that bar --
 * the meter-aware replacement for a flat beatsPerBar assumption. `bar` here
 * is the beatmap's own authored (local, un-looped) bar number.
 */
export function eventSeconds(meterSequence: MeterSegment[], bar: number, step: number, subdivision: number, bpm: number): number {
  const segment = segmentForLocalBar(meterSequence, bar);
  const barStart = cumulativeBarStartSeconds(meterSequence, bar, bpm);
  const secondsPerBar = (60 / bpm) * segment.num;
  const secondsPerStep = secondsPerBar / subdivision;
  return barStart + step * secondsPerStep;
}
