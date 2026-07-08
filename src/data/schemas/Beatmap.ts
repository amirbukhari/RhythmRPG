// Mirrors docs/technical/schemas/beatmap.schema.json — keep in sync.

export interface MeterSegment {
  startBar: number;
  bars: number;
  num: number;
  den: 2 | 4 | 8 | 16;
}

export type BeatEventType =
  | "downbeat"
  | "enemyTelegraph"
  | "phaseTransition"
  | "forecastMarker"
  | "syncopationAccent";

export interface BeatEvent {
  bar: number;
  step: number;
  type: BeatEventType;
  payload?: unknown;
}

export interface Beatmap {
  trackId: string;
  bpm: number;
  meterSequence: MeterSegment[];
  subdivision: 4 | 8 | 16 | 32;
  events: BeatEvent[];
}
