import { describe, expect, it } from "vitest";
import { getEncounter, getHeroClass, partyRoster } from "../../src/data/ContentRegistry";
import {
  createCombat,
  queueHeroAction,
  resolveHeroPerformance,
  heroTimingWindowMultiplier,
  type CombatState,
} from "../../src/systems/combat/CombatController";

/**
 * Every stat that appears in authored content must be mechanically real --
 * this file pins each one's wiring (see the StatusEffect docblock in
 * CombatController.ts). These were all cosmetic no-ops before 2026-07-10.
 */

function soloCombat(heroId: string, encounterId = "opening_biome_slime_01"): CombatState {
  return createCombat([getHeroClass(heroId)], getEncounter(encounterId));
}

function forceEnemyDamageIntent(state: CombatState): number {
  // opening slime's only intent is slime_lunge (8 damage); make sure it's rolled.
  const enemy = state.enemies[0];
  enemy.currentIntent = { telegraph: "slime_lunge", effect: { type: "damage", value: 8, target: "randomHero" } };
  return 8;
}

describe("enemy-side stats", () => {
  it('"defense" debuffs increase the damage the enemy takes', () => {
    const state = soloCombat("warrior");
    state.enemies[0].statusEffects.push({ stat: "defense", value: -0.5, remainingRounds: 5, sourceAbilityId: "test" });
    queueHeroAction(state, "warrior", "warrior_slash_chain"); // 12 base damage
    resolveHeroPerformance(state, ["perfect", "perfect", "perfect"]);
    expect(state.enemies[0].hp).toBe(state.enemies[0].maxHp - 18); // 12 * (1 - (-0.5))
  });

  it('"accuracy" and "speed" debuffs on an enemy reduce its outgoing damage', () => {
    const state = soloCombat("tank");
    const base = forceEnemyDamageIntent(state);
    state.enemies[0].statusEffects.push(
      { stat: "accuracy", value: -0.25, remainingRounds: 5, sourceAbilityId: "test" },
      { stat: "speed", value: -0.25, remainingRounds: 5, sourceAbilityId: "test" }
    );
    const tank = state.heroes[0];
    queueHeroAction(state, "tank", "tank_guard_pulse");
    resolveHeroPerformance(state, ["miss"]); // guard fizzles on a miss; enemy still acts at round end
    expect(tank.maxHp - tank.hp).toBe(Math.round(base * 0.5)); // (1 - 0.25 - 0.25)
  });

  it('"targetFocus" (taunt) redirects the enemy onto the hero who applied it', () => {
    // Full party, but the enemy is taunted by the tank -- its attack must
    // hit the tank regardless of random target selection.
    const state = createCombat(partyRoster(), getEncounter("opening_biome_slime_01"));
    const base = forceEnemyDamageIntent(state);
    state.enemies[0].statusEffects.push({
      stat: "targetFocus",
      value: -1,
      remainingRounds: 5,
      sourceAbilityId: "tank_taunt_stomp",
      sourceHeroId: "tank",
    });
    for (const [heroId, ability, steps] of [
      ["warrior", "warrior_slash_chain", 3],
      ["tank", "tank_guard_pulse", 1],
      ["mage", "mage_arc_flash", 1],
      ["healer", "healer_mend_cadence", 1],
    ] as const) {
      queueHeroAction(state, heroId, ability);
      resolveHeroPerformance(state, Array(steps).fill("miss")); // misses so no enemy dies / no guard applies
    }
    const tank = state.heroes.find((h) => h.heroId === "tank")!;
    const others = state.heroes.filter((h) => h.heroId !== "tank");
    expect(tank.maxHp - tank.hp).toBe(base);
    for (const hero of others) expect(hero.hp).toBe(hero.maxHp);
  });
});

describe("hero-side stats", () => {
  it('"resist" shrinks the magnitude of incoming enemy debuffs', () => {
    const state = soloCombat("healer");
    state.enemies[0].currentIntent = { telegraph: "test_hex", effect: { type: "debuff", value: -0.2 } };
    const healer = state.heroes[0];
    healer.statusEffects.push({ stat: "resist", value: 0.5, remainingRounds: 5, sourceAbilityId: "healer_purify_hymn" });
    queueHeroAction(state, "healer", "healer_mend_cadence");
    resolveHeroPerformance(state, ["perfect"]);
    const applied = healer.statusEffects.find((e) => e.stat === "enemyDebuff")!;
    expect(applied.value).toBeCloseTo(-0.1); // -0.2 * (1 - 0.5)
  });

  it('enemy-applied "enemyDebuff" reduces the hero\'s outgoing damage', () => {
    const state = soloCombat("warrior");
    state.heroes[0].statusEffects.push({ stat: "enemyDebuff", value: -0.25, remainingRounds: 5, sourceAbilityId: "test" });
    queueHeroAction(state, "warrior", "warrior_slash_chain"); // 12 base
    resolveHeroPerformance(state, ["perfect", "perfect", "perfect"]);
    expect(state.enemies[0].hp).toBe(state.enemies[0].maxHp - 9); // 12 * 0.75
  });

  it('"accuracy" buffs widen the hero\'s judgment windows via heroTimingWindowMultiplier', () => {
    const state = createCombat(partyRoster(), getEncounter("opening_biome_slime_01"));
    expect(heroTimingWindowMultiplier(state, "mage")).toBe(1);
    for (const hero of state.heroes) {
      hero.statusEffects.push({ stat: "accuracy", value: 0.15, remainingRounds: 3, sourceAbilityId: "healer_tier2" });
    }
    expect(heroTimingWindowMultiplier(state, "mage")).toBeCloseTo(1.15);
    expect(heroTimingWindowMultiplier(state, "nobody")).toBe(1); // unknown hero: neutral
  });

  it("hero debuff abilities stamp sourceHeroId so taunts know their owner", () => {
    const state = createCombat(partyRoster(), getEncounter("opening_biome_slime_01"));
    // Give the tank 1 focus for taunt_stomp.
    state.heroes.find((h) => h.heroId === "tank")!.focus = 1;
    queueHeroAction(state, "tank", "tank_taunt_stomp", { targetEnemyId: state.enemies[0].instanceId });
    resolveHeroPerformance(state, ["perfect"]);
    const taunt = state.enemies[0].statusEffects.find((e) => e.stat === "targetFocus")!;
    expect(taunt.sourceHeroId).toBe("tank");
  });
});
