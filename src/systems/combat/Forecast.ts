import type { Beatmap, BeatEvent } from "../../data/schemas/Beatmap";
import { totalPatternBars } from "./MeterSequence";

export interface ForecastEntry {
  /** The authored (local, un-looped) bar this event falls on. */
  bar: number;
  type: BeatEvent["type"];
  payload?: unknown;
}

/**
 * The concrete implementation behind healer_sightread's forecastReveal
 * effect (PRD §8.4): "reveals the next two measures of enemy telegraph
 * glyphs, syncopation markers, and upcoming meter changes." Pure and
 * loop-aware -- if the forecast window wraps past the end of the authored
 * pattern, it correctly continues from bar 1 rather than returning nothing.
 */
export function upcomingEvents(beatmap: Beatmap, fromGlobalBar: number, barsAhead: number): ForecastEntry[] {
  const totalBars = totalPatternBars(beatmap.meterSequence);
  const localFromBar = ((fromGlobalBar - 1) % totalBars) + 1;

  const targetLocalBars: number[] = [];
  for (let i = 0; i < barsAhead; i++) {
    targetLocalBars.push(((localFromBar - 1 + i) % totalBars) + 1);
  }

  const entries: ForecastEntry[] = [];
  for (const localBar of targetLocalBars) {
    const barEvents = beatmap.events
      .filter((e) => e.bar === localBar && e.type !== "downbeat")
      .sort((a, b) => a.step - b.step);
    for (const event of barEvents) {
      entries.push({ bar: event.bar, type: event.type, payload: event.payload });
    }
  }
  return entries;
}
