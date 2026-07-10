// Mirrors docs/technical/schemas/ability.schema.json — keep in sync.

export type HeroRole = "warrior" | "tank" | "mage" | "healer";
export type InputStep = "tap" | "hold" | "release";
export type EffectType =
  | "damage"
  | "heal"
  | "buff"
  | "debuff"
  | "guard"
  | "interrupt"
  | "forecastReveal"
  | "partyBuff";

export interface AbilityEffect {
  type: EffectType;
  stat?: string;
  value?: number;
  durationRounds?: number;
  bars?: number;
}

export interface Ability {
  abilityId: string;
  role: HeroRole;
  focusCost: number;
  /** Shared party Groove spent to use this ability (PRD §8.5 ultimates). Omitted/0 for normal abilities. */
  grooveCost?: number;
  phraseLengthBars: 1 | 2;
  inputPattern: InputStep[];
  /** One entry per inputPattern step, formatted "bar.beat" relative to phrase start. */
  timingTemplate: string[];
  effects: AbilityEffect[];
}
