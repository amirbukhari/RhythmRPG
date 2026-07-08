import { describe, expect, it } from "vitest";
import { ContentValidationError, loadAbility, loadBeatmap, loadEncounter } from "../../src/data/ContentLoader";

describe("ContentLoader", () => {
  it("accepts a valid beatmap", () => {
    const beatmap = loadBeatmap({
      trackId: "test_track",
      bpm: 120,
      meterSequence: [{ startBar: 1, bars: 4, num: 4, den: 4 }],
      subdivision: 16,
      events: [{ bar: 1, step: 0, type: "downbeat" }],
    });
    expect(beatmap.bpm).toBe(120);
  });

  it("rejects a beatmap missing required fields", () => {
    expect(() => loadBeatmap({ trackId: "bad" })).toThrow(ContentValidationError);
  });

  it("rejects a beatmap with an invalid time signature denominator", () => {
    expect(() =>
      loadBeatmap({
        trackId: "bad_den",
        bpm: 120,
        meterSequence: [{ startBar: 1, bars: 4, num: 4, den: 3 }],
        subdivision: 16,
        events: [],
      })
    ).toThrow(ContentValidationError);
  });

  it("accepts a valid ability", () => {
    const ability = loadAbility({
      abilityId: "warrior_slash_chain",
      role: "warrior",
      focusCost: 1,
      phraseLengthBars: 1,
      inputPattern: ["tap", "tap"],
      timingTemplate: ["1.1", "1.3"],
      effects: [{ type: "damage", value: 10 }],
    });
    expect(ability.role).toBe("warrior");
  });

  it("rejects an ability with an unknown role", () => {
    expect(() =>
      loadAbility({
        abilityId: "bad_role",
        role: "necromancer",
        focusCost: 1,
        phraseLengthBars: 1,
        inputPattern: ["tap"],
        timingTemplate: ["1.1"],
        effects: [{ type: "damage" }],
      })
    ).toThrow(ContentValidationError);
  });

  it("accepts a valid encounter", () => {
    const encounter = loadEncounter({
      encounterId: "test_encounter",
      trackId: "test_track",
      enemyWave: ["slime"],
      accentProfile: null,
      victoryRewards: { xp: 10, currency: 5 },
    });
    expect(encounter.enemyWave).toEqual(["slime"]);
  });

  it("rejects an encounter with an empty enemy wave", () => {
    expect(() =>
      loadEncounter({
        encounterId: "empty_wave",
        trackId: "test_track",
        enemyWave: [],
        victoryRewards: { xp: 10, currency: 5 },
      })
    ).toThrow(ContentValidationError);
  });
});
