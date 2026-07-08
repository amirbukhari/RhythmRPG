import { describe, expect, it } from "vitest";
import { judge, JUDGMENT_WINDOWS_MS, STORY_MODE_WINDOW_MULTIPLIER, TIER_POTENCY, TIER_GROOVE_GAIN } from "../../src/systems/combat/JudgmentSystem";

describe("JudgmentSystem.judge", () => {
  it("classifies a dead-on-time input as perfect", () => {
    expect(judge(0)).toBe("perfect");
  });

  it("is symmetric around zero (early and late by the same amount match the same tier)", () => {
    expect(judge(-30)).toBe(judge(30));
    expect(judge(-100)).toBe(judge(100));
  });

  it("matches the exact PRD §8.3 tier boundaries", () => {
    expect(judge(JUDGMENT_WINDOWS_MS.perfect)).toBe("perfect");
    expect(judge(JUDGMENT_WINDOWS_MS.perfect + 1)).toBe("great");
    expect(judge(JUDGMENT_WINDOWS_MS.great)).toBe("great");
    expect(judge(JUDGMENT_WINDOWS_MS.great + 1)).toBe("good");
    expect(judge(JUDGMENT_WINDOWS_MS.good)).toBe("good");
    expect(judge(JUDGMENT_WINDOWS_MS.good + 1)).toBe("miss");
  });

  it("widens every window by exactly 25% in story mode", () => {
    const justOutsideNormalGood = JUDGMENT_WINDOWS_MS.good + 1;
    expect(judge(justOutsideNormalGood)).toBe("miss");
    expect(judge(justOutsideNormalGood, { storyMode: true })).toBe("good");
    expect(judge(JUDGMENT_WINDOWS_MS.good * STORY_MODE_WINDOW_MULTIPLIER, { storyMode: true })).toBe("good");
  });

  it("applies an assist multiplier on top of (not instead of) story mode", () => {
    const combined = JUDGMENT_WINDOWS_MS.good * STORY_MODE_WINDOW_MULTIPLIER * 2;
    expect(judge(combined, { storyMode: true, assistMultiplier: 2 })).toBe("good");
    expect(judge(combined + 1, { storyMode: true, assistMultiplier: 2 })).toBe("miss");
  });

  it("never returns a tier for a miss-range input regardless of assist", () => {
    expect(judge(100000, { assistMultiplier: 1.5 })).toBe("miss");
  });
});

describe("JudgmentSystem tier tables", () => {
  it("has strictly descending potency from perfect to miss", () => {
    expect(TIER_POTENCY.perfect).toBeGreaterThan(TIER_POTENCY.great);
    expect(TIER_POTENCY.great).toBeGreaterThan(TIER_POTENCY.good);
    expect(TIER_POTENCY.good).toBeGreaterThan(TIER_POTENCY.miss);
    expect(TIER_POTENCY.miss).toBe(0);
    expect(TIER_POTENCY.perfect).toBe(1);
  });

  it("has strictly descending groove gain from perfect to miss, with miss contributing nothing", () => {
    expect(TIER_GROOVE_GAIN.perfect).toBeGreaterThan(TIER_GROOVE_GAIN.great);
    expect(TIER_GROOVE_GAIN.great).toBeGreaterThan(TIER_GROOVE_GAIN.good);
    expect(TIER_GROOVE_GAIN.good).toBeGreaterThan(TIER_GROOVE_GAIN.miss);
    expect(TIER_GROOVE_GAIN.miss).toBe(0);
  });
});
