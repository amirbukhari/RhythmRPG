import { describe, expect, it } from "vitest";
import { createArena, player, enemies, step, type Arena, type BeatTier, type FrameInput } from "../../src/systems/action/ActionCombat";
import { encounters, getEnemy } from "../../src/data/ContentRegistry";

/**
 * P5 balance harness (PRD §15/§16): every authored encounter must be
 * WINNABLE by a merely competent player, and the §8.6 curriculum must
 * actually ascend. A scripted bot plays each fight in the pure sim --
 * approach, strike on the beat when in reach, dash out of telegraphs --
 * at a fixed 120bpm beat. If content tuning ever makes a fight unwinnable
 * or flat, this fails before a player ever feels it.
 */

const DT = 1 / 60;
const BEAT = 0.5; // 120bpm bot metronome

interface BotResult {
  outcome: Arena["outcome"];
  seconds: number;
  playerHp: number;
}

function playBot(enemyIds: string[], maxSeconds = 120): BotResult {
  const defs = enemyIds.map((id) => getEnemy(id));
  const arena = createArena(320, 180, defs.map((d) => d.maxHp));
  enemies(arena).forEach((e, i) => {
    e.aggr = defs[i].action?.aggression;
    e.strikeDamage = defs[i].action?.damage;
  });

  let t = 0;
  while (arena.outcome === "ongoing" && t < maxSeconds) {
    const p = player(arena);
    const foes = enemies(arena).filter((e) => e.state !== "dead");
    const target = foes.reduce((a, b) => {
      const da = Math.hypot(a.pos.x - p.pos.x, a.pos.y - p.pos.y);
      const db = Math.hypot(b.pos.x - p.pos.x, b.pos.y - p.pos.y);
      return da <= db ? a : b;
    }, foes[0]);
    const dx = target.pos.x - p.pos.x;
    const dy = target.pos.y - p.pos.y;
    const dist = Math.hypot(dx, dy);

    // on-beat window: the bot presses within one tick of its metronome
    const phase = t % BEAT;
    const onBeat = phase < DT * 2 || BEAT - phase < DT * 2;
    const tier: BeatTier = onBeat ? "great" : "off";

    const danger = foes.some((e) => e.ai?.mode === "windup" && e.ai.timer < 0.18 && Math.hypot(e.pos.x - p.pos.x, e.pos.y - p.pos.y) < 40);

    const input: FrameInput = {
      move: { x: 0, y: 0 },
      dash: false,
      light: false,
      heavy: false,
      special: false,
      parry: false,
      onBeat,
      tier,
    };
    if (danger && p.dashCd <= 0 && p.state !== "hitstun") {
      // dash away from the striker
      input.dash = true;
      input.move = { x: dist > 0 ? -dx / dist : 1, y: dist > 0 ? -dy / dist : 0 };
    } else if (dist > 24) {
      input.move = { x: dx / dist, y: dy / dist };
    } else if (onBeat) {
      input.light = true;
      input.move = { x: dx / dist, y: dy / dist };
    }
    step(arena, input, DT);
    t += DT;
  }
  return { outcome: arena.outcome, seconds: t, playerHp: player(arena).hp };
}

function waveOf(encounterId: string): string[] {
  const e = encounters.get(encounterId);
  if (!e) throw new Error(`unknown encounter ${encounterId}`);
  return e.enemyWave;
}

describe("balance: every authored encounter is winnable (P5)", () => {
  for (const [id, encounter] of encounters) {
    it(`${id} is winnable by the scripted bot`, () => {
      const r = playBot(encounter.enemyWave);
      expect(r.outcome, `${id} ended ${r.outcome} at ${r.seconds.toFixed(1)}s with ${r.playerHp.toFixed(0)} hp`).toBe("victory");
    });
  }

  it("the §8.6 curriculum ascends: the boss takes meaningfully longer than the opener", () => {
    const opener = playBot(waveOf("opening_biome_slime_01"));
    const boss = playBot(waveOf("boss_conductor_01"), 180);
    expect(opener.outcome).toBe("victory");
    expect(boss.outcome).toBe("victory");
    expect(boss.seconds).toBeGreaterThan(opener.seconds * 1.5);
  });
});
