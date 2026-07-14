import { describe, expect, it } from "vitest";
import { RELICS, applyRelics } from "../../src/systems/progression/Relics";
import { createArena, player, FOCUS_MAX } from "../../src/systems/action/ActionCombat";
import { encounters } from "../../src/data/ContentRegistry";

describe("relics (PRD §8.5, action-arena effects)", () => {
  it("every relic id referenced by encounter rewards exists in the registry", () => {
    for (const encounter of encounters.values()) {
      for (const id of encounter.victoryRewards.relicChoices ?? []) {
        expect(RELICS[id], `relic "${id}"`).toBeDefined();
      }
    }
  });

  it("focus_loop banks starting Focus, capped at the maximum", () => {
    const a = createArena(200, 120, [30]);
    applyRelics(a, ["focus_loop"]);
    expect(a.focus).toBe(2);
    a.focus = FOCUS_MAX;
    applyRelics(a, ["focus_loop"]);
    expect(a.focus).toBe(FOCUS_MAX);
  });

  it("groove_amp banks starting Groove, capped at 100", () => {
    const a = createArena(200, 120, [30]);
    applyRelics(a, ["groove_amp"]);
    expect(a.groove).toBe(20);
    a.groove = 95;
    applyRelics(a, ["groove_amp"]);
    expect(a.groove).toBe(100);
  });

  it("counter_charm grants opening i-frames", () => {
    const a = createArena(200, 120, [30]);
    expect(player(a).iframes).toBe(0);
    applyRelics(a, ["counter_charm"]);
    expect(player(a).iframes).toBeGreaterThan(1);
  });

  it("unknown relic ids are ignored, and effects stack across the inventory", () => {
    const a = createArena(200, 120, [30]);
    applyRelics(a, ["nonsense", "focus_loop", "groove_amp"]);
    expect(a.focus).toBe(2);
    expect(a.groove).toBe(20);
  });
});
