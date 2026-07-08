import type { Ability, AbilityEffect } from "../../data/schemas/Ability";
import type { Encounter } from "../../data/schemas/Encounter";
import type { Enemy, EnemyIntent } from "../../data/schemas/Enemy";
import type { HeroClass } from "../../data/schemas/HeroClass";
import { getAbility, getEnemy } from "../../data/ContentRegistry";
import { TIER_GROOVE_GAIN, TIER_POTENCY, type JudgmentTier } from "./JudgmentSystem";

/**
 * Pure, Phaser-free implementation of the turn structure in PRD §8.2 and the
 * resource model in §8.5. BattleScene is responsible for turning real
 * TransportClock-timed input into JudgmentTier[] (via JudgmentSystem.judge)
 * and calling resolveHeroPerformance with the result -- this module never
 * touches Web Audio, DOM, or wall-clock time, so it's fully unit-testable.
 */

export interface StatusEffect {
  stat: string;
  value: number;
  remainingRounds: number;
  sourceAbilityId: string;
}

export interface HeroState {
  heroId: string;
  classId: string;
  role: HeroClass["role"];
  hp: number;
  maxHp: number;
  focus: number;
  maxFocus: number;
  statusEffects: StatusEffect[];
}

export interface EnemyState {
  instanceId: string;
  enemyId: string;
  name: string;
  hp: number;
  maxHp: number;
  statusEffects: StatusEffect[];
  currentIntent: EnemyIntent | null;
  intentCursor: number;
}

export type CombatPhase = "intent" | "command" | "performance" | "enemyResolution" | "roundEnd";
export type CombatOutcome = "ongoing" | "victory" | "defeat";

export interface PendingAction {
  heroId: string;
  ability: Ability;
  targetEnemyId?: string;
  targetHeroId?: string;
}

export interface CombatLogEntry {
  round: number;
  message: string;
}

export interface CombatState {
  round: number;
  phase: CombatPhase;
  outcome: CombatOutcome;
  heroes: HeroState[];
  enemies: EnemyState[];
  heroTurnQueue: string[];
  pendingAction: PendingAction | null;
  groove: number;
  grooveStreak: number;
  log: CombatLogEntry[];
}

const GROOVE_MAX = 100;

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function log(state: CombatState, message: string): void {
  state.log.push({ round: state.round, message });
}

function aliveHeroes(state: CombatState): HeroState[] {
  return state.heroes.filter((h) => h.hp > 0);
}

function aliveEnemies(state: CombatState): EnemyState[] {
  return state.enemies.filter((e) => e.hp > 0);
}

function tickStatusEffects(effects: StatusEffect[]): StatusEffect[] {
  return effects.map((e) => ({ ...e, remainingRounds: e.remainingRounds - 1 })).filter((e) => e.remainingRounds > 0);
}

function statValue(effects: StatusEffect[], stat: string): number {
  return effects.filter((e) => e.stat === stat).reduce((sum, e) => sum + e.value, 0);
}

function rollIntent(enemy: EnemyState, enemyDef: Enemy): EnemyIntent {
  const intent = enemyDef.intents[enemy.intentCursor % enemyDef.intents.length];
  enemy.intentCursor += 1;
  return intent;
}

function rollAllIntents(state: CombatState): void {
  for (const enemy of aliveEnemies(state)) {
    enemy.currentIntent = rollIntent(enemy, getEnemy(enemy.enemyId));
  }
}

export function createCombat(heroClasses: HeroClass[], encounter: Encounter): CombatState {
  const heroes: HeroState[] = heroClasses.map((hc) => ({
    heroId: hc.heroId,
    classId: hc.heroId,
    role: hc.role,
    hp: hc.maxHp,
    maxHp: hc.maxHp,
    focus: 0,
    maxFocus: hc.maxFocus,
    statusEffects: [],
  }));

  const enemies: EnemyState[] = encounter.enemyWave.map((enemyId, index) => {
    const def = getEnemy(enemyId);
    return {
      instanceId: `${enemyId}_${index}`,
      enemyId,
      name: def.name,
      hp: def.maxHp,
      maxHp: def.maxHp,
      statusEffects: [],
      currentIntent: null,
      intentCursor: 0,
    };
  });

  const state: CombatState = {
    round: 1,
    phase: "intent",
    outcome: "ongoing",
    heroes,
    enemies,
    heroTurnQueue: heroes.map((h) => h.heroId),
    pendingAction: null,
    groove: 0,
    grooveStreak: 0,
    log: [{ round: 1, message: `Encounter "${encounter.encounterId}" started.` }],
  };

  rollAllIntents(state);
  state.phase = "command";
  return state;
}

export function queueHeroAction(
  state: CombatState,
  heroId: string,
  abilityId: string,
  targets: { targetEnemyId?: string; targetHeroId?: string } = {}
): void {
  if (state.outcome !== "ongoing") throw new Error("Combat has already ended.");
  if (state.phase !== "command") throw new Error(`Cannot queue an action during phase "${state.phase}".`);
  if (!state.heroTurnQueue.includes(heroId)) throw new Error(`Hero "${heroId}" is not up to act this round.`);

  const hero = state.heroes.find((h) => h.heroId === heroId);
  if (!hero || hero.hp <= 0) throw new Error(`Hero "${heroId}" cannot act.`);

  const ability = getAbility(abilityId);
  if (ability.role !== hero.role) {
    throw new Error(`Ability "${abilityId}" belongs to role "${ability.role}", not "${hero.role}".`);
  }
  if (hero.focus < ability.focusCost) {
    throw new Error(`Hero "${heroId}" has ${hero.focus} focus, needs ${ability.focusCost} for "${abilityId}".`);
  }

  hero.focus -= ability.focusCost;
  state.pendingAction = { heroId, ability, ...targets };
  state.phase = "performance";
}

function pickDefaultEnemyTarget(state: CombatState): EnemyState | undefined {
  return aliveEnemies(state)[0];
}

function pickDefaultHealTarget(state: CombatState): HeroState | undefined {
  return aliveHeroes(state).slice().sort((a, b) => a.hp / a.maxHp - b.hp / b.maxHp)[0];
}

function applyAbilityEffect(state: CombatState, effect: AbilityEffect, potency: number, hasMiss: boolean, pending: PendingAction): void {
  const actingHero = state.heroes.find((h) => h.heroId === pending.heroId)!;

  // Damage/heal scale continuously with potency (partial credit for a mixed
  // performance), but a single missed step fully fails a status-application
  // effect -- otherwise timing wouldn't matter at all for guard/buff/debuff/
  // interrupt/forecast abilities, undermining "accuracy determines potency"
  // (PRD §8.3) for the exact abilities where hitting the beat is the point.
  if (hasMiss && effect.type !== "damage" && effect.type !== "heal") {
    log(state, `${pending.heroId}'s ${pending.ability.abilityId} fizzles (missed timing).`);
    return;
  }

  switch (effect.type) {
    case "damage": {
      const target = pending.targetEnemyId
        ? state.enemies.find((e) => e.instanceId === pending.targetEnemyId)
        : pickDefaultEnemyTarget(state);
      if (!target || target.hp <= 0) return;
      const dealt = Math.round((effect.value ?? 0) * potency);
      target.hp = clamp(target.hp - dealt, 0, target.maxHp);
      log(state, `${pending.heroId} hits ${target.name} with ${pending.ability.abilityId} for ${dealt} (${Math.round(potency * 100)}% potency).`);
      break;
    }
    case "heal": {
      const target = pending.targetHeroId
        ? state.heroes.find((h) => h.heroId === pending.targetHeroId)
        : pickDefaultHealTarget(state);
      if (!target || target.hp <= 0) return;
      const healed = Math.round((effect.value ?? 0) * potency);
      target.hp = clamp(target.hp + healed, 0, target.maxHp);
      log(state, `${pending.heroId} heals ${target.heroId} with ${pending.ability.abilityId} for ${healed}.`);
      break;
    }
    case "guard": {
      actingHero.statusEffects.push({
        stat: "guard",
        value: effect.value ?? 0,
        remainingRounds: (effect.durationRounds ?? 1) + 1,
        sourceAbilityId: pending.ability.abilityId,
      });
      log(state, `${pending.heroId} raises guard (${Math.round((effect.value ?? 0) * 100)}% reduction).`);
      break;
    }
    case "buff": {
      actingHero.statusEffects.push({
        stat: effect.stat ?? "unknown",
        value: effect.value ?? 0,
        remainingRounds: (effect.durationRounds ?? 1) + 1,
        sourceAbilityId: pending.ability.abilityId,
      });
      break;
    }
    case "partyBuff": {
      for (const hero of aliveHeroes(state)) {
        hero.statusEffects.push({
          stat: effect.stat ?? "unknown",
          value: effect.value ?? 0,
          remainingRounds: (effect.durationRounds ?? 1) + 1,
          sourceAbilityId: pending.ability.abilityId,
        });
      }
      break;
    }
    case "debuff": {
      const target = pending.targetEnemyId
        ? state.enemies.find((e) => e.instanceId === pending.targetEnemyId)
        : pickDefaultEnemyTarget(state);
      if (!target || target.hp <= 0) return;
      target.statusEffects.push({
        stat: effect.stat ?? "unknown",
        value: effect.value ?? 0,
        remainingRounds: (effect.durationRounds ?? 1) + 1,
        sourceAbilityId: pending.ability.abilityId,
      });
      break;
    }
    case "interrupt": {
      const target = pending.targetEnemyId
        ? state.enemies.find((e) => e.instanceId === pending.targetEnemyId)
        : pickDefaultEnemyTarget(state);
      if (!target) return;
      target.currentIntent = null;
      log(state, `${pending.heroId} interrupts ${target.name}'s action.`);
      break;
    }
    case "forecastReveal": {
      // Informational only (drives BattleScene's beat-lane forecast UI per
      // PRD §8.4's Sightread description) -- no combat-state effect here.
      log(state, `${pending.heroId} reveals the next ${effect.bars ?? 1} bar(s) of upcoming cues.`);
      break;
    }
  }
}

export function resolveHeroPerformance(state: CombatState, tiers: JudgmentTier[]): CombatState {
  if (state.phase !== "performance" || !state.pendingAction) {
    throw new Error(`Cannot resolve performance during phase "${state.phase}".`);
  }
  const pending = state.pendingAction;
  if (tiers.length !== pending.ability.inputPattern.length) {
    throw new Error(
      `Expected ${pending.ability.inputPattern.length} judgment tiers for "${pending.ability.abilityId}", got ${tiers.length}.`
    );
  }

  const potency = tiers.reduce((sum, t) => sum + TIER_POTENCY[t], 0) / tiers.length;
  const hasMiss = tiers.some((t) => t === "miss");
  const grooveGain = tiers.reduce((sum, t) => sum + TIER_GROOVE_GAIN[t], 0);

  state.groove = clamp(state.groove + grooveGain, 0, GROOVE_MAX);
  state.grooveStreak = hasMiss ? 0 : state.grooveStreak + tiers.length;

  for (const effect of pending.ability.effects) {
    applyAbilityEffect(state, effect, potency, hasMiss, pending);
  }

  state.heroTurnQueue = state.heroTurnQueue.filter((id) => id !== pending.heroId);
  state.pendingAction = null;

  if (state.heroTurnQueue.length > 0) {
    state.phase = "command";
  } else {
    state.phase = "enemyResolution";
    resolveEnemyActions(state);
    advanceRound(state);
  }

  return state;
}

function resolveEnemyActions(state: CombatState): void {
  for (const enemy of aliveEnemies(state)) {
    const intent = enemy.currentIntent;
    if (!intent) continue;

    if (intent.effect.type === "damage") {
      const pool = intent.effect.target === "lowestHpHero" ? [pickDefaultHealTarget(state)].filter(Boolean) as HeroState[] : aliveHeroes(state);
      const target = pool.length ? pool[Math.floor(Math.random() * pool.length)] : undefined;
      if (!target) continue;
      const guardReduction = statValue(target.statusEffects, "guard");
      const dealt = Math.round(intent.effect.value * (1 - clamp(guardReduction, 0, 1)));
      target.hp = clamp(target.hp - dealt, 0, target.maxHp);
      log(state, `${enemy.name} uses ${intent.telegraph} on ${target.heroId} for ${dealt}${guardReduction > 0 ? " (guarded)" : ""}.`);
    } else if (intent.effect.type === "debuff") {
      const target = aliveHeroes(state)[0];
      if (!target) continue;
      target.statusEffects.push({
        stat: "enemyDebuff",
        value: intent.effect.value,
        remainingRounds: 2,
        sourceAbilityId: intent.telegraph,
      });
    }
  }
}

function advanceRound(state: CombatState): void {
  state.phase = "roundEnd";

  for (const hero of state.heroes) hero.statusEffects = tickStatusEffects(hero.statusEffects);
  for (const enemy of state.enemies) enemy.statusEffects = tickStatusEffects(enemy.statusEffects);

  if (aliveEnemies(state).length === 0) {
    state.outcome = "victory";
    log(state, "Victory.");
    return;
  }
  if (aliveHeroes(state).length === 0) {
    state.outcome = "defeat";
    log(state, "Defeat.");
    return;
  }

  state.round += 1;
  for (const hero of aliveHeroes(state)) hero.focus = clamp(hero.focus + 1, 0, hero.maxFocus);
  rollAllIntents(state);
  state.heroTurnQueue = aliveHeroes(state).map((h) => h.heroId);
  state.phase = "command";
}
