import { describe, expect, it } from "vitest";
import { createActionCombat, judgeAction, startAttack, startDash, tickActionCombat } from "../../src/systems/combat/ActionCombat";

describe("ActionCombat", () => {
  it("judges real-time actions against the nearest beat", () => {
    const state = createActionCombat(["slime"], { beatIntervalSeconds: 0.5 });
    expect(judgeAction(state, 1.003)).toBe("perfect");
    expect(judgeAction(state, 1.12)).toBe("good");
    expect(judgeAction(state, 1.24)).toBe("miss");
  });

  it("gives on-beat dashes extra i-frames and cooldown refund", () => {
    const perfect = createActionCombat(["slime"]);
    const off = createActionCombat(["slime"]);
    expect(startDash(perfect, { x: 1, y: 0 }, 1.0)).toBe(true);
    expect(startDash(off, { x: 1, y: 0 }, 1.24)).toBe(true);
    expect(perfect.hero.invulnerableFrames).toBeGreaterThan(off.hero.invulnerableFrames);
    expect(perfect.hero.dashCooldownFrames).toBeLessThan(off.hero.dashCooldownFrames);
  });

  it("resolves frame-data attacks into hitstun and damage-percent knockback", () => {
    const state = createActionCombat(["slime"]);
    state.enemies[0].position = { x: 104, y: 118 };
    expect(startAttack(state, "light", 1.0)).toBe(true);
    for (let i = 0; i < 8; i++) tickActionCombat(state);
    expect(state.enemies[0].hp).toBeLessThan(state.enemies[0].maxHp);
    expect(state.enemies[0].hitstunFrames).toBeGreaterThan(0);
    expect(state.enemies[0].damagePercent).toBeGreaterThan(0);
    expect(Math.abs(state.enemies[0].velocity.x)).toBeGreaterThan(0);
  });

  it("spends Focus and Groove gates for special and ultimate", () => {
    const state = createActionCombat(["slime"]);
    expect(startAttack(state, "special", 1.0)).toBe(true);
    expect(state.hero.focus).toBe(1);
    state.hero.action = "idle";
    expect(startAttack(state, "ultimate", 1.0)).toBe(false);
    state.hero.groove = 100;
    expect(startAttack(state, "ultimate", 1.0)).toBe(true);
    expect(state.hero.groove).toBeLessThan(100);
  });
});
