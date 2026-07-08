import type { HeroRole } from "./Ability";

// Not a PRD §10.5 canonical schema (see Enemy.ts for the same rationale) --
// base hero stats/kit composition, needed to run combat, aren't specified
// by beatmap/ability/encounter.
export interface HeroClass {
  heroId: string;
  role: HeroRole;
  name: string;
  maxHp: number;
  maxFocus: number;
  abilityIds: string[];
}
