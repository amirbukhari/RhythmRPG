import { describe, expect, it } from "vitest";
import { upcomingEvents } from "../../src/systems/combat/Forecast";
import type { Beatmap } from "../../src/data/schemas/Beatmap";

const BEATMAP: Beatmap = {
  trackId: "test",
  bpm: 120,
  meterSequence: [{ startBar: 1, bars: 4, num: 4, den: 4 }],
  subdivision: 16,
  events: [
    { bar: 1, step: 0, type: "downbeat" },
    { bar: 2, step: 0, type: "downbeat" },
    { bar: 2, step: 8, type: "enemyTelegraph", payload: "slam" },
    { bar: 3, step: 0, type: "downbeat" },
    { bar: 4, step: 0, type: "downbeat" },
    { bar: 4, step: 4, type: "syncopationAccent", payload: "clave" },
  ],
};

describe("Forecast.upcomingEvents", () => {
  it("excludes downbeats -- they're not forecast-worthy information", () => {
    const events = upcomingEvents(BEATMAP, 1, 4);
    expect(events.every((e) => e.type !== "downbeat")).toBe(true);
  });

  it("finds the telegraph within the forecast window", () => {
    const events = upcomingEvents(BEATMAP, 1, 2);
    expect(events).toEqual([{ bar: 2, type: "enemyTelegraph", payload: "slam" }]);
  });

  it("returns an empty list when nothing non-downbeat falls in the window", () => {
    expect(upcomingEvents(BEATMAP, 1, 1)).toEqual([]);
  });

  it("wraps correctly past the end of the authored pattern (4 bars total)", () => {
    // From global bar 4, 2 bars ahead covers local bar 4 and local bar 1 (wrap).
    const events = upcomingEvents(BEATMAP, 4, 2);
    expect(events).toEqual([{ bar: 4, type: "syncopationAccent", payload: "clave" }]);
  });

  it("handles a forecast window entirely past one loop (global bar > pattern length)", () => {
    // Global bar 6 -> local bar 2 (since pattern is 4 bars: bar 5=local1, bar 6=local2).
    const events = upcomingEvents(BEATMAP, 6, 1);
    expect(events).toEqual([{ bar: 2, type: "enemyTelegraph", payload: "slam" }]);
  });

  it("orders multiple events within the same bar by step", () => {
    const multiEventBeatmap: Beatmap = {
      ...BEATMAP,
      events: [
        { bar: 2, step: 8, type: "enemyTelegraph", payload: "second" },
        { bar: 2, step: 2, type: "syncopationAccent", payload: "first" },
      ],
    };
    const events = upcomingEvents(multiEventBeatmap, 2, 1);
    expect(events.map((e) => e.payload)).toEqual(["first", "second"]);
  });
});
