import { describe, expect, it } from "vitest";
import {
  circlesOverlap,
  knockbackSpeed,
  hitstunSeconds,
  onBeatMultiplier,
  hitboxCentre,
  createArena,
  createFighter,
  player,
  enemies,
  step,
  LIGHT,
  type Arena,
  type FrameInput,
} from "../../src/systems/action/ActionCombat";

const IDLE: FrameInput = { move: { x: 0, y: 0 }, dash: false, light: false, heavy: false, special: false, parry: false, onBeat: false };

function tick(a: Arena, input: Partial<FrameInput>, dt = 1 / 60): void {
  step(a, { ...IDLE, ...input }, dt);
}

describe("pure combat math", () => {
  it("circlesOverlap is true when bodies touch, false when apart", () => {
    expect(circlesOverlap({ x: 0, y: 0 }, 5, { x: 8, y: 0 }, 5)).toBe(true);
    expect(circlesOverlap({ x: 0, y: 0 }, 5, { x: 20, y: 0 }, 5)).toBe(false);
  });

  it("knockback scales with the victim's accumulated damage% (Melee-style)", () => {
    expect(knockbackSpeed(100, 0)).toBe(100);
    expect(knockbackSpeed(100, 100)).toBe(200);
    expect(knockbackSpeed(100, 50)).toBeGreaterThan(knockbackSpeed(100, 0));
  });

  it("hitstun grows with damage and damage%, capped", () => {
    expect(hitstunSeconds(6, 0)).toBeLessThan(hitstunSeconds(14, 0));
    expect(hitstunSeconds(6, 0)).toBeLessThan(hitstunSeconds(6, 80));
    expect(hitstunSeconds(999, 999)).toBeLessThanOrEqual(0.6);
  });

  it("on-beat actions are empowered over off-beat", () => {
    expect(onBeatMultiplier(true)).toBeGreaterThan(onBeatMultiplier(false));
  });

  it("hitbox sits ahead of the body in the facing direction", () => {
    const f = createFighter("p", "player", { x: 50, y: 50 }, 100);
    f.facing = "right";
    expect(hitboxCentre(f, 15)).toEqual({ x: 65, y: 50 });
    f.facing = "up";
    expect(hitboxCentre(f, 15)).toEqual({ x: 50, y: 35 });
  });
});

describe("arena simulation", () => {
  function duel(): Arena {
    // player and one enemy placed adjacent so a facing attack connects.
    const a = createArena(200, 120, [30]);
    player(a).pos = { x: 100, y: 60 };
    enemies(a)[0].pos = { x: 100, y: 46 }; // just above the player
    enemies(a)[0].ai!.mode = "recover"; // park the enemy AI so we test the player's hit cleanly
    enemies(a)[0].ai!.timer = 999;
    return a;
  }

  it("a facing light attack damages an adjacent enemy exactly once per swing", () => {
    const a = duel();
    const e = enemies(a)[0];
    const startHp = e.hp;
    // face up (toward the enemy) and throw a light attack
    tick(a, { move: { x: 0, y: -1 }, light: true });
    // advance through startup+active+recovery
    for (let i = 0; i < 40; i++) tick(a, {});
    expect(e.hp).toBeLessThan(startHp);
    expect(e.hp).toBeCloseTo(startHp - LIGHT.damage, 5); // exactly one hit, off-beat
    expect(e.damagePct).toBeCloseTo(LIGHT.damage, 5);
  });

  it("an on-beat attack deals more than an off-beat one", () => {
    const off = duel();
    tick(off, { move: { x: 0, y: -1 }, light: true, onBeat: false });
    for (let i = 0; i < 40; i++) tick(off, {});

    const on = duel();
    tick(on, { move: { x: 0, y: -1 }, light: true, onBeat: true });
    for (let i = 0; i < 40; i++) tick(on, {});

    const offDmg = enemies(off)[0].maxHp - enemies(off)[0].hp;
    const onDmg = enemies(on)[0].maxHp - enemies(on)[0].hp;
    expect(onDmg).toBeGreaterThan(offDmg);
  });

  it("a dash grants i-frames that negate a hit that lands during them", () => {
    const a = createArena(200, 120, [30]);
    const p = player(a);
    const e = enemies(a)[0];
    p.pos = { x: 100, y: 60 };
    e.pos = { x: 100, y: 74 };
    e.facing = "up";
    // dash to gain i-frames, then force an enemy strike onto the player mid-dash
    tick(a, { move: { x: 1, y: 0 }, dash: true, onBeat: true });
    expect(p.iframes).toBeGreaterThan(0);
    const hpBefore = p.hp;
    // manually stage an active enemy hitbox overlapping the (still invulnerable) player
    e.attack = { def: { ...LIGHT, reach: 0, radius: 40 }, phase: "active", timer: 0.08, onBeat: false, hitIds: [] };
    e.state = "attack";
    tick(a, {});
    expect(p.hp).toBe(hpBefore); // i-frames negated it
  });

  it("reports victory when every enemy is dead and defeat when the player dies", () => {
    const a = createArena(200, 120, [1]);
    enemies(a)[0].hp = 0;
    enemies(a)[0].state = "dead";
    tick(a, {});
    expect(a.outcome).toBe("victory");

    const b = createArena(200, 120, [30]);
    player(b).hp = 0;
    player(b).state = "dead";
    tick(b, {});
    expect(b.outcome).toBe("defeat");
  });

  it("keeps fighters inside the arena bounds", () => {
    const a = createArena(200, 120, [30]);
    const p = player(a);
    for (let i = 0; i < 120; i++) tick(a, { move: { x: -1, y: 0 } });
    expect(p.pos.x).toBeGreaterThanOrEqual(p.radius);
    expect(p.pos.x).toBeLessThanOrEqual(200 - p.radius);
  });
});

describe("depth mechanics (PRD §8.2)", () => {
  function duel(): Arena {
    const a = createArena(200, 120, [60]);
    player(a).pos = { x: 100, y: 60 };
    enemies(a)[0].pos = { x: 100, y: 46 };
    enemies(a)[0].ai!.mode = "recover";
    enemies(a)[0].ai!.timer = 999;
    return a;
  }

  it("a Focus special costs Focus, is gated when Focus is empty, and hits harder than a light", () => {
    const a = duel();
    expect(a.focus).toBe(0);
    tick(a, { move: { x: 0, y: -1 }, special: true }); // no focus -> refused, becomes nothing/movement
    expect(player(a).attack).toBeNull();

    a.focus = 2;
    tick(a, { move: { x: 0, y: -1 }, special: true });
    expect(a.focus).toBe(1); // spent one
    for (let i = 0; i < 40; i++) tick(a, {});
    const specialDmg = enemies(a)[0].maxHp - enemies(a)[0].hp;
    expect(specialDmg).toBeGreaterThan(LIGHT.damage); // 20 vs 6
  });

  it("an on-beat parry negates an enemy hit and staggers the attacker into hitstun", () => {
    const a = createArena(200, 120, [30]);
    const p = player(a);
    const e = enemies(a)[0];
    p.pos = { x: 100, y: 60 };
    e.pos = { x: 100, y: 74 };
    // open an on-beat parry
    tick(a, { parry: true, onBeat: true });
    expect(p.parryTimer).toBeGreaterThan(0);
    const hpBefore = p.hp;
    // stage an active enemy hitbox overlapping the player
    e.attack = { def: { ...LIGHT, reach: 0, radius: 40, damage: 10 }, phase: "active", timer: 0.08, onBeat: false, hitIds: [] };
    e.state = "attack";
    tick(a, {});
    expect(p.hp).toBe(hpBefore); // hit negated
    expect(e.state).toBe("hitstun"); // attacker staggered
    expect(a.groove).toBeGreaterThan(0); // reward
  });

  it("an off-beat parry gives only a whiff window (does not negate a hit landing after it closes)", () => {
    const a = createArena(200, 120, [30]);
    const p = player(a);
    const e = enemies(a)[0];
    p.pos = { x: 100, y: 60 };
    e.pos = { x: 100, y: 74 };
    tick(a, { parry: true, onBeat: false }); // tiny 0.04s window
    for (let i = 0; i < 6; i++) tick(a, {}); // ~0.1s later the window is closed
    expect(p.parryTimer).toBe(0);
    const hpBefore = p.hp;
    e.attack = { def: { ...LIGHT, reach: 0, radius: 40, damage: 10 }, phase: "active", timer: 0.08, onBeat: false, hitIds: [] };
    e.state = "attack";
    tick(a, {});
    expect(p.hp).toBeLessThan(hpBefore); // not parried
  });
});
