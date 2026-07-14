import { describe, expect, it } from "vitest";
import {
  createArena,
  player,
  enemies,
  step,
  tierMultiplier,
  tierGroove,
  onBeatMultiplier,
  LIGHT,
  ULTIMATE,
  ULTIMATE_GROOVE_COST,
  type Arena,
  type BeatTier,
  type FrameInput,
} from "../../src/systems/action/ActionCombat";
import { tierForOffset, TIER_WINDOWS } from "../../src/systems/audio/SongBeat";

const IDLE: FrameInput = { move: { x: 0, y: 0 }, dash: false, light: false, heavy: false, special: false, parry: false, onBeat: false };

function tick(a: Arena, input: Partial<FrameInput>, dt = 1 / 60): void {
  step(a, { ...IDLE, ...input }, dt);
}

/** player adjacent to one enemy so a facing attack connects. */
function duel(enemyHp = 60): Arena {
  const a = createArena(200, 120, [enemyHp]);
  player(a).pos = { x: 100, y: 60 };
  enemies(a)[0].pos = { x: 100, y: 40 };
  return a;
}

function landLight(a: Arena, tier: BeatTier): void {
  tick(a, { move: { x: 0, y: -1 }, light: true, tier, onBeat: tier === "perfect" || tier === "great" });
  for (let i = 0; i < 30; i++) tick(a, {});
}

describe("§8.3 judgment tiers", () => {
  it("tierForOffset grades the four windows, and assist widens them", () => {
    expect(tierForOffset(0.02)).toBe("perfect");
    expect(tierForOffset(0.06)).toBe("great");
    expect(tierForOffset(0.12)).toBe("good");
    expect(tierForOffset(0.2)).toBe("off");
    // assist ×1.5 admits what the base window rejects
    expect(tierForOffset(0.06, 1.5)).toBe("perfect");
    expect(tierForOffset(0.12, 1.5)).toBe("great");
    expect(TIER_WINDOWS.perfect).toBeLessThan(TIER_WINDOWS.great);
  });

  it("multiplier and groove are strictly ordered perfect > great > good > off", () => {
    expect(tierMultiplier("perfect")).toBeGreaterThan(tierMultiplier("great"));
    expect(tierMultiplier("great")).toBeGreaterThan(tierMultiplier("good"));
    expect(tierMultiplier("good")).toBeGreaterThan(tierMultiplier("off"));
    expect(tierGroove("perfect")).toBeGreaterThan(tierGroove("great"));
    expect(tierGroove("great")).toBeGreaterThan(tierGroove("good"));
    expect(tierGroove("off")).toBe(0);
    // legacy binary view maps on-beat to "great"
    expect(onBeatMultiplier(true)).toBe(tierMultiplier("great"));
  });

  it("a perfect hit deals more damage and builds more groove than a great one", () => {
    const perfect = duel();
    landLight(perfect, "perfect");
    const great = duel();
    landLight(great, "great");
    const good = duel();
    landLight(good, "good");
    expect(enemies(perfect)[0].hp).toBeLessThan(enemies(great)[0].hp);
    expect(enemies(great)[0].hp).toBeLessThan(enemies(good)[0].hp);
    expect(perfect.groove).toBeGreaterThan(great.groove);
    expect(great.groove).toBeGreaterThan(good.groove);
  });

  it("a good-tier hit still empowers over off, but grants no focus", () => {
    const good = duel();
    landLight(good, "good");
    const off = duel();
    landLight(off, "off");
    expect(enemies(good)[0].hp).toBeLessThan(enemies(off)[0].hp);
    expect(good.focus).toBe(0);
    expect(good.groove).toBeGreaterThan(0);
    expect(off.groove).toBe(0);
  });

  it("perfect dashes get the longest i-frames", () => {
    const perfect = duel();
    tick(perfect, { move: { x: 1, y: 0 }, dash: true, tier: "perfect", onBeat: true });
    const off = duel();
    tick(off, { move: { x: 1, y: 0 }, dash: true, tier: "off" });
    expect(player(perfect).iframes).toBeGreaterThan(player(off).iframes);
  });
});

describe("§8.5 ultimate (full-Groove spend)", () => {
  it("does nothing below the full meter", () => {
    const a = duel();
    a.groove = ULTIMATE_GROOVE_COST - 1;
    tick(a, { ultimate: true, tier: "off" });
    expect(a.groove).toBe(ULTIMATE_GROOVE_COST - 1);
    expect(player(a).attack).toBeNull();
  });

  it("spends the FULL meter and hits everything in its radius", () => {
    const a = createArena(200, 120, [200, 200]);
    player(a).pos = { x: 100, y: 60 };
    enemies(a)[0].pos = { x: 60, y: 60 };
    enemies(a)[1].pos = { x: 140, y: 60 };
    a.groove = 100;
    tick(a, { ultimate: true, tier: "great", onBeat: true });
    expect(a.groove).toBe(0);
    expect(player(a).attack?.def).toBe(ULTIMATE);
    for (let i = 0; i < 40; i++) tick(a, {});
    // both enemies were struck by the burst (radius 64 from centre)
    expect(enemies(a)[0].hp).toBeLessThan(200);
    expect(enemies(a)[1].hp).toBeLessThan(200);
  });

  it("armors the player through startup+active", () => {
    const a = duel();
    a.groove = 100;
    tick(a, { ultimate: true, tier: "off" });
    // one tick of decay (dt) has already elapsed inside the same step
    expect(player(a).iframes).toBeGreaterThanOrEqual(ULTIMATE.startup + ULTIMATE.active - 1 / 30);
  });
});

describe("§9.3 practice mode (no fail state)", () => {
  it("floors player HP at 1 instead of dying", () => {
    const a = duel();
    a.practice = true;
    const p = player(a);
    p.hp = 3;
    const e = enemies(a)[0];
    e.attack = { def: { ...LIGHT, reach: 0, radius: 60, damage: 50 }, phase: "active", timer: 0.08, onBeat: false, tier: "off", hitIds: [] };
    tick(a, {});
    expect(p.hp).toBe(1);
    expect(p.state).not.toBe("dead");
    expect(a.outcome).toBe("ongoing");
  });

  it("without practice the same hit is lethal", () => {
    const a = duel();
    const p = player(a);
    p.hp = 3;
    const e = enemies(a)[0];
    e.attack = { def: { ...LIGHT, reach: 0, radius: 60, damage: 50 }, phase: "active", timer: 0.08, onBeat: false, tier: "off", hitIds: [] };
    tick(a, {});
    expect(a.outcome).toBe("defeat");
  });
});

describe("§8.7 boss-phase aggression", () => {
  it("higher aggression telegraphs for less time before striking", () => {
    const timeToStrike = (aggr: number): number => {
      const a = duel();
      a.enemyAggression = aggr;
      // keep player passive and adjacent; count ticks until enemy attacks
      let t = 0;
      for (let i = 0; i < 600 && !enemies(a)[0].attack; i++) {
        tick(a, {});
        t += 1 / 60;
      }
      return t;
    };
    expect(timeToStrike(1.7)).toBeLessThan(timeToStrike(1));
  });
});
