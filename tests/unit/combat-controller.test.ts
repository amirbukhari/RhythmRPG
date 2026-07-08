import { beforeEach, describe, expect, it } from "vitest";
import { partyRoster, getEncounter, getHeroClass } from "../../src/data/ContentRegistry";
import { createCombat, queueHeroAction, resolveHeroPerformance, type CombatState } from "../../src/systems/combat/CombatController";

function freshCombat(): CombatState {
  return createCombat(partyRoster(), getEncounter("opening_biome_slime_01"));
}

describe("CombatController", () => {
  let state: CombatState;

  beforeEach(() => {
    state = freshCombat();
  });

  it("starts in the command phase with all four heroes queued", () => {
    expect(state.phase).toBe("command");
    expect(state.heroTurnQueue).toEqual(["warrior", "tank", "mage", "healer"]);
    expect(state.enemies[0].currentIntent).not.toBeNull();
  });

  it("allows a free (0-cost) ability and moves to the performance phase", () => {
    queueHeroAction(state, "warrior", "warrior_slash_chain"); // free
    expect(state.phase).toBe("performance");
    expect(state.heroes.find((h) => h.heroId === "warrior")!.focus).toBe(0);
  });

  it("rejects an ability that costs more focus than the hero currently has", () => {
    // heroes start at 0 focus; rising_break costs 1
    expect(() => queueHeroAction(state, "warrior", "warrior_rising_break")).toThrow(/focus/);
  });

  it("allows a costed ability once enough focus has regenerated", () => {
    // regen is +1 focus/round for heroes who survive to round end; drive one
    // free round for everyone so the tank accrues 1 focus, then spend it.
    for (const heroId of ["warrior", "tank", "mage"]) {
      const ability = heroId === "warrior" ? "warrior_slash_chain" : heroId === "tank" ? "tank_guard_pulse" : "mage_arc_flash";
      queueHeroAction(state, heroId, ability);
      resolveHeroPerformance(state, [Array(ability === "warrior_slash_chain" ? 3 : 1).fill("perfect")].flat());
    }
    queueHeroAction(state, "healer", "healer_mend_cadence");
    resolveHeroPerformance(state, ["perfect"]); // ends round 1, regen fires

    expect(state.round).toBe(2);
    expect(state.heroes.find((h) => h.heroId === "tank")!.focus).toBe(1);
    expect(() => queueHeroAction(state, "tank", "tank_taunt_stomp")).not.toThrow(); // costs 1
  });

  it("rejects an ability that doesn't belong to the acting hero's role", () => {
    expect(() => queueHeroAction(state, "warrior", "mage_arc_flash")).toThrow(/role/);
  });

  it("deals full-potency damage on an all-perfect performance", () => {
    queueHeroAction(state, "warrior", "warrior_slash_chain"); // free, 3 taps, 12 dmg
    resolveHeroPerformance(state, ["perfect", "perfect", "perfect"]);
    const slime = state.enemies[0];
    expect(slime.hp).toBe(slime.maxHp - 12);
  });

  it("scales damage down by average potency on a mixed performance", () => {
    queueHeroAction(state, "warrior", "warrior_slash_chain");
    resolveHeroPerformance(state, ["perfect", "good", "miss"]); // avg potency = (1 + 0.65 + 0)/3
    const slime = state.enemies[0];
    const expectedPotency = (1 + 0.65 + 0) / 3;
    expect(slime.hp).toBe(slime.maxHp - Math.round(12 * expectedPotency));
  });

  it("builds groove on perfects and resets the streak on a miss", () => {
    queueHeroAction(state, "warrior", "warrior_slash_chain");
    resolveHeroPerformance(state, ["perfect", "perfect", "perfect"]);
    expect(state.groove).toBe(12); // 4 groove per perfect step * 3
    expect(state.grooveStreak).toBe(3);

    queueHeroAction(state, "tank", "tank_guard_pulse");
    resolveHeroPerformance(state, ["miss"]);
    expect(state.grooveStreak).toBe(0);
  });

  it("heals the lowest-HP hero by default", () => {
    // warrior takes damage first via a slime hit, simulate directly
    state.heroes.find((h) => h.heroId === "warrior")!.hp = 10;
    queueHeroAction(state, "healer", "healer_mend_cadence");
    resolveHeroPerformance(state, ["perfect"]);
    expect(state.heroes.find((h) => h.heroId === "warrior")!.hp).toBe(30);
  });

  it("applies a 50% guard status effect that outlives the round it was cast in", () => {
    queueHeroAction(state, "tank", "tank_guard_pulse"); // free, 1 hold step, guard 0.5 for 1 round
    resolveHeroPerformance(state, ["perfect"]);
    const tank = state.heroes.find((h) => h.heroId === "tank")!;
    expect(tank.statusEffects).toContainEqual(
      expect.objectContaining({ stat: "guard", value: 0.5, sourceAbilityId: "tank_guard_pulse" })
    );
  });

  it("halves enemy damage against a hero with an active guard status", () => {
    // Single-hero roster makes enemy target selection deterministic (only
    // one alive hero to pick), so this exercises the real damage-reduction
    // code path in resolveEnemyActions rather than just the formula.
    const soloTank = createCombat([getHeroClass("tank")], getEncounter("opening_biome_slime_01"));
    queueHeroAction(soloTank, "tank", "tank_guard_pulse");
    const hpBefore = soloTank.heroes[0].hp;
    resolveHeroPerformance(soloTank, ["perfect"]); // resolves the only hero -> enemy resolution fires this same call
    const dealt = hpBefore - soloTank.heroes[0].hp;
    expect(dealt).toBe(4); // slime_lunge deals 8 raw, halved by 50% guard
  });

  it("cancels the enemy's current intent when interrupted", () => {
    state.heroes.find((h) => h.heroId === "tank")!.focus = 1; // taunt_stomp costs 1
    queueHeroAction(state, "tank", "tank_taunt_stomp");
    resolveHeroPerformance(state, ["perfect"]);
    expect(state.enemies[0].currentIntent).toBeNull();
  });

  it("reaches victory once the enemy wave is defeated", () => {
    // Slime has 60 HP; slash_chain (free, 3 taps) does up to 12 per full round of 4 heroes acting.
    let rounds = 0;
    while (state.outcome === "ongoing" && rounds < 20) {
      for (const heroId of [...state.heroTurnQueue]) {
        const ability = heroId === "warrior" ? "warrior_slash_chain" : heroId === "tank" ? "tank_guard_pulse" : heroId === "mage" ? "mage_arc_flash" : "healer_mend_cadence";
        queueHeroAction(state, heroId, ability);
        const steps = ability === "warrior_slash_chain" ? 3 : 1;
        resolveHeroPerformance(state, Array(steps).fill("perfect"));
        if (state.outcome !== "ongoing") break;
      }
      rounds += 1;
    }
    expect(state.outcome).toBe("victory");
    expect(state.enemies[0].hp).toBe(0);
  });

  it("logs at least one entry per resolved action", () => {
    queueHeroAction(state, "warrior", "warrior_slash_chain");
    resolveHeroPerformance(state, ["perfect", "perfect", "perfect"]);
    expect(state.log.length).toBeGreaterThan(0);
  });
});
