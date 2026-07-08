// Not one of the PRD §10.5 canonical schemas (beatmap/ability/encounter) --
// those describe timing and rewards but intentionally leave enemy combat
// data undefined. This is the minimal internal data model needed to make
// the turn-based loop in PRD §8.2 actually runnable; it's content-team
// owned data, not engine code, so it lives here alongside the other
// schemas rather than hardcoded into CombatController.

export interface EnemyIntentEffect {
  type: "damage" | "debuff";
  value: number;
  target?: "randomHero" | "lowestHpHero";
}

export interface EnemyIntent {
  /** Matches a beatmap's enemyTelegraph event payload (see Beatmap.ts). */
  telegraph: string;
  effect: EnemyIntentEffect;
}

export interface Enemy {
  enemyId: string;
  name: string;
  maxHp: number;
  intents: EnemyIntent[];
}
