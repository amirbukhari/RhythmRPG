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
  /** Action-combat tuning (§8.6 curriculum, v8.6): how this foe fights in
   * the real-time sim. Omitted fields use the sim defaults. */
  action?: {
    /** Tempo multiplier: <1 lumbers (longer telegraphs), >1 presses. */
    aggression?: number;
    /** Strike damage override (sim default 9). */
    damage?: number;
  };
}
