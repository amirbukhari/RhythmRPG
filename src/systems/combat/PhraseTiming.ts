/**
 * Converts an ability's "bar.beat" timingTemplate (PRD ability.schema.json)
 * into absolute Tone.Transport seconds, given when the phrase's one-bar
 * count-in ends (PRD §8.2). Pure and Phaser-free so it's directly testable;
 * BattleScene is the only caller that touches real transport time.
 */
export function parseBarBeat(token: string): { bar: number; beat: number } {
  const match = /^(\d+)\.(\d+)$/.exec(token);
  if (!match) throw new Error(`Invalid timing token "${token}", expected "bar.beat".`);
  return { bar: Number(match[1]), beat: Number(match[2]) };
}

export function timingTemplateToSeconds(
  timingTemplate: string[],
  phraseStartSeconds: number,
  bpm: number,
  beatsPerBar: number
): number[] {
  const secondsPerBeat = 60 / bpm;
  return timingTemplate.map((token) => {
    const { bar, beat } = parseBarBeat(token);
    const beatOffset = (bar - 1) * beatsPerBar + (beat - 1);
    return phraseStartSeconds + beatOffset * secondsPerBeat;
  });
}

/** The next bar boundary at or after `fromSeconds` -- the one-bar count-in target. */
export function nextBarBoundary(fromSeconds: number, bpm: number, beatsPerBar: number): number {
  const barLengthSeconds = (60 / bpm) * beatsPerBar;
  if (barLengthSeconds <= 0) return fromSeconds;
  const barsElapsed = Math.ceil(fromSeconds / barLengthSeconds);
  const boundary = barsElapsed * barLengthSeconds;
  // Always require at least one full bar of count-in, even if fromSeconds
  // lands exactly on a boundary.
  return boundary > fromSeconds ? boundary : boundary + barLengthSeconds;
}
