import { FOCUS_MAX, player, type Arena } from "../action/ActionCombat";

/**
 * PRD §8.5: "Equipment is limited to a single relic slot per hero and one
 * shared party charm." Only three relic ids are referenced anywhere in
 * authored content (encounter victoryRewards.relicChoices), so this is a
 * small typed registry rather than a full JSON content pipeline -- adding a
 * fourth relic to the ContentRegistry/schema pattern is a natural follow-up
 * once there are enough of them to warrant it (see PRD §20).
 *
 * v8.3: re-targeted from the retired turn-based CombatState to the action
 * Arena -- the post-pivot build had relics selectable and persisted but
 * mechanically inert (the §12 "pivot regression" risk, caught in cleanup).
 */
export interface RelicDefinition {
  name: string;
  description: string;
  /** Mutates a freshly-created Arena once, at fight start. */
  apply: (arena: Arena) => void;
}

export const RELICS: Record<string, RelicDefinition> = {
  focus_loop: {
    name: "Focus Loop",
    description: "Enter every fight with 2 Focus already burning.",
    apply: (arena) => {
      arena.focus = Math.min(FOCUS_MAX, arena.focus + 2);
    },
  },
  counter_charm: {
    name: "Counter Charm",
    description: "Start every fight steeled: brief guard the moment it begins.",
    apply: (arena) => {
      const p = player(arena);
      p.iframes = Math.max(p.iframes, 1.2); // an opening breath no ambush can steal
    },
  },
  groove_amp: {
    name: "Groove Amp",
    description: "Start every fight with 20 Groove already banked.",
    apply: (arena) => {
      arena.groove = Math.min(100, arena.groove + 20);
    },
  },
};

/** Applies every relic in a save profile's inventory to a freshly-created arena. */
export function applyRelics(arena: Arena, relicIds: string[]): void {
  for (const id of relicIds) {
    RELICS[id]?.apply(arena);
  }
}
