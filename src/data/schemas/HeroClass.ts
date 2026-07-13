import type { HeroRole } from "./Ability";

// Not a PRD §10.5 canonical schema (see Enemy.ts for the same rationale) --
// base hero stats/kit composition, needed to run combat, aren't specified
// by beatmap/ability/encounter.
export interface HeroClass {
  heroId: string;
  role: HeroRole;
  name: string;
  /**
   * Which band member's art (tools/pixelart/bandmates.py) renders this slot:
   * `band_<spriteId>` idle / `band_<spriteId>_run` / `band_<spriteId>_attack`.
   * The four mechanical roles are re-skinned to Inhalants -- Amir (lead
   * guitar) leads the party; bass, vocals, drums fill the others.
   */
  spriteId: string;
  maxHp: number;
  maxFocus: number;
  abilityIds: string[];
}
