import type { CombatState } from "../combat/CombatController";

/**
 * PRD §8.5: "Equipment is limited to a single relic slot per hero and one
 * shared party charm." Only three relic ids are referenced anywhere in
 * authored content (encounter victoryRewards.relicChoices), so this is a
 * small typed registry rather than a full JSON content pipeline -- adding a
 * fourth relic to the ContentRegistry/schema pattern is a natural follow-up
 * once there are enough of them to warrant it (see PRD §20).
 */
export interface RelicDefinition {
  name: string;
  description: string;
  /** Mutates a freshly-created CombatState once, at battle start. */
  apply: (state: CombatState) => void;
}

export const RELICS: Record<string, RelicDefinition> = {
  focus_loop: {
    name: "Focus Loop",
    description: "+1 max Focus for every hero, filled at the start of each battle.",
    apply: (state) => {
      for (const hero of state.heroes) {
        hero.maxFocus += 1;
        hero.focus = Math.min(hero.focus + 1, hero.maxFocus);
      }
    },
  },
  counter_charm: {
    name: "Counter Charm",
    description: "The tank starts every battle with a permanent 25% guard.",
    apply: (state) => {
      const tank = state.heroes.find((h) => h.role === "tank");
      if (!tank) return;
      tank.statusEffects.push({ stat: "guard", value: 0.25, remainingRounds: Number.MAX_SAFE_INTEGER, sourceAbilityId: "relic_counter_charm" });
    },
  },
  groove_amp: {
    name: "Groove Amp",
    description: "Start every battle with 20 Groove already banked.",
    apply: (state) => {
      state.groove = Math.min(100, state.groove + 20);
    },
  },
};

/** Applies every relic in a save profile's inventory to a freshly-created combat state. */
export function applyRelics(state: CombatState, relicIds: string[]): void {
  for (const id of relicIds) {
    RELICS[id]?.apply(state);
  }
}
