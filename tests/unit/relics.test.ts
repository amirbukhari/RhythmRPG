import { describe, expect, it } from "vitest";
import { applyRelics } from "../../src/systems/progression/Relics";
import { createCombat } from "../../src/systems/combat/CombatController";
import { partyRoster, getEncounter } from "../../src/data/ContentRegistry";

function freshCombat() {
  return createCombat(partyRoster(), getEncounter("opening_biome_slime_01"));
}

describe("Relics.applyRelics", () => {
  it("focus_loop raises every hero's max focus by 1 and fills the new capacity", () => {
    const state = freshCombat();
    const before = state.heroes.map((h) => h.maxFocus);
    applyRelics(state, ["focus_loop"]);
    state.heroes.forEach((h, i) => {
      expect(h.maxFocus).toBe(before[i] + 1);
      expect(h.focus).toBe(1);
    });
  });

  it("counter_charm gives the tank a permanent guard status", () => {
    const state = freshCombat();
    applyRelics(state, ["counter_charm"]);
    const tank = state.heroes.find((h) => h.role === "tank")!;
    expect(tank.statusEffects).toContainEqual(expect.objectContaining({ stat: "guard", value: 0.25 }));
  });

  it("groove_amp banks 20 groove at battle start", () => {
    const state = freshCombat();
    expect(state.groove).toBe(0);
    applyRelics(state, ["groove_amp"]);
    expect(state.groove).toBe(20);
  });

  it("caps groove_amp at the groove maximum", () => {
    const state = freshCombat();
    state.groove = 95;
    applyRelics(state, ["groove_amp"]);
    expect(state.groove).toBe(100);
  });

  it("applies multiple relics together", () => {
    const state = freshCombat();
    applyRelics(state, ["focus_loop", "groove_amp"]);
    expect(state.groove).toBe(20);
    expect(state.heroes[0].maxFocus).toBeGreaterThan(0);
  });

  it("silently ignores an unknown relic id instead of throwing", () => {
    const state = freshCombat();
    expect(() => applyRelics(state, ["not_a_real_relic"])).not.toThrow();
  });
});
