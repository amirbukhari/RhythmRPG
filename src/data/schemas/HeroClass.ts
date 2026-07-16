import type { HeroRole } from "./Ability";

// Not a PRD §10.5 canonical schema (see Enemy.ts for the same rationale) --
// base hero stats/kit composition, needed to run combat, aren't specified
// by beatmap/ability/encounter.
export interface HeroClass {
  heroId: string;
  role: HeroRole;
  name: string;
  /**
   * Which cast art renders this slot: `band_<spriteId>` idle /
   * `band_<spriteId>_run` / `band_<spriteId>_attack`. v10.0: the only live
   * spriteId is `mir` (legacy role JSON backs the retired path only).
   */
  spriteId: string;
  maxHp: number;
  maxFocus: number;
  abilityIds: string[];
}
