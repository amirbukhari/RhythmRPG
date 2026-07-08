// Mirrors docs/technical/schemas/encounter.schema.json — keep in sync.

export interface VictoryRewards {
  xp: number;
  currency: number;
  relicChoices?: string[];
}

export interface Encounter {
  encounterId: string;
  trackId: string;
  enemyWave: string[];
  /** Rhythmic accent pattern (e.g. "son_clave_2_3") layered over the beatmap's meter. Never a substitute for meterSequence. */
  accentProfile?: string | null;
  victoryRewards: VictoryRewards;
}
