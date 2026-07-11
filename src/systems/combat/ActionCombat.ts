import { judge, type JudgmentTier } from "./JudgmentSystem";

export interface Vec2 { x: number; y: number }
export type Facing = "up" | "down" | "left" | "right";
export type ActionKind = "idle" | "run" | "dash" | "light" | "heavy" | "special" | "ultimate" | "parry" | "hitstun";

export interface ActionFighter {
  id: string;
  name: string;
  team: "hero" | "enemy";
  position: Vec2;
  velocity: Vec2;
  facing: Facing;
  hp: number;
  maxHp: number;
  damagePercent: number;
  focus: number;
  groove: number;
  action: ActionKind;
  actionFrame: number;
  invulnerableFrames: number;
  hitstunFrames: number;
  dashCooldownFrames: number;
  alreadyHitByAction: string[];
}

export interface AttackFrameData {
  startup: number;
  active: number;
  recovery: number;
  damage: number;
  knockback: number;
  hitstun: number;
  range: number;
  width: number;
  focusCost?: number;
  grooveCost?: number;
}

export interface ActionCombatState {
  frame: number;
  arena: { width: number; height: number };
  beatIntervalSeconds: number;
  calibrationOffsetSeconds: number;
  assistMultiplier: number;
  hero: ActionFighter;
  enemies: ActionFighter[];
  currentAttack: AttackFrameData | null;
  lastJudgment: JudgmentTier | null;
  log: string[];
  outcome: "ongoing" | "victory" | "defeat";
}

export const ACTION_ATTACKS: Record<"light" | "heavy" | "special" | "ultimate", AttackFrameData> = {
  light: { startup: 5, active: 4, recovery: 10, damage: 7, knockback: 90, hitstun: 14, range: 28, width: 20 },
  heavy: { startup: 13, active: 5, recovery: 20, damage: 16, knockback: 170, hitstun: 24, range: 34, width: 24 },
  special: { startup: 8, active: 7, recovery: 18, damage: 13, knockback: 130, hitstun: 20, range: 42, width: 26, focusCost: 1 },
  ultimate: { startup: 18, active: 12, recovery: 32, damage: 34, knockback: 260, hitstun: 42, range: 72, width: 58, grooveCost: 100 },
};

const FRAME_SECONDS = 1 / 60;
const RUN_ACCEL = 820;
const FRICTION = 0.82;
const MAX_SPEED = 86;
const DASH_SPEED = 230;

export function createActionCombat(enemyNames: string[], options: Partial<Pick<ActionCombatState, "beatIntervalSeconds" | "calibrationOffsetSeconds" | "assistMultiplier">> = {}): ActionCombatState {
  return {
    frame: 0,
    arena: { width: 320, height: 180 },
    beatIntervalSeconds: options.beatIntervalSeconds ?? 0.5,
    calibrationOffsetSeconds: options.calibrationOffsetSeconds ?? 0,
    assistMultiplier: options.assistMultiplier ?? 1,
    hero: fighter("hero", "hero", "the Deereater", { x: 78, y: 118 }),
    enemies: enemyNames.map((name, i) => fighter(`enemy-${i}`, "enemy", name, { x: 216 + i * 34, y: 106 + i * 14 })),
    currentAttack: null,
    lastJudgment: null,
    log: ["Action arena online: run, dash, strike on the beat."],
    outcome: "ongoing",
  };
}

function fighter(id: string, team: "hero" | "enemy", name: string, position: Vec2): ActionFighter {
  return { id, team, name, position: { ...position }, velocity: { x: 0, y: 0 }, facing: team === "hero" ? "right" : "left", hp: team === "hero" ? 120 : 42, maxHp: team === "hero" ? 120 : 42, damagePercent: 0, focus: team === "hero" ? 2 : 0, groove: 0, action: "idle", actionFrame: 0, invulnerableFrames: 0, hitstunFrames: 0, dashCooldownFrames: 0, alreadyHitByAction: [] };
}

export function judgeAction(state: ActionCombatState, transportSeconds: number): JudgmentTier {
  const beat = state.beatIntervalSeconds;
  const adjusted = transportSeconds - state.calibrationOffsetSeconds;
  const nearestBeat = Math.round(adjusted / beat) * beat;
  const tier = judge((adjusted - nearestBeat) * 1000, { assistMultiplier: state.assistMultiplier });
  state.lastJudgment = tier;
  return tier;
}

export function startDash(state: ActionCombatState, direction: Vec2, transportSeconds: number): boolean {
  const h = state.hero;
  if (h.dashCooldownFrames > 0 || h.action === "dash" || h.hitstunFrames > 0) return false;
  const tier = judgeAction(state, transportSeconds);
  const len = Math.hypot(direction.x, direction.y) || 1;
  h.velocity = { x: (direction.x / len) * DASH_SPEED, y: (direction.y / len) * DASH_SPEED };
  h.action = "dash"; h.actionFrame = 0; h.dashCooldownFrames = tier === "perfect" || tier === "great" ? 10 : 26; h.invulnerableFrames = tier === "perfect" ? 16 : tier === "great" ? 12 : 8;
  h.groove = Math.min(100, h.groove + (tier === "perfect" ? 5 : tier === "great" ? 3 : 0));
  state.log.push(`${tier} dash: ${h.invulnerableFrames} i-frames.`);
  return true;
}

export function startAttack(state: ActionCombatState, kind: "light" | "heavy" | "special" | "ultimate", transportSeconds: number): boolean {
  const h = state.hero, data = ACTION_ATTACKS[kind];
  if (h.hitstunFrames > 0 || ["light", "heavy", "special", "ultimate"].includes(h.action)) return false;
  if (data.focusCost && h.focus < data.focusCost) return false;
  if (data.grooveCost && h.groove < data.grooveCost) return false;
  const tier = judgeAction(state, transportSeconds);
  if (data.focusCost) h.focus -= data.focusCost;
  if (data.grooveCost) h.groove -= data.grooveCost;
  state.currentAttack = empower(data, tier);
  h.action = kind; h.actionFrame = 0; h.alreadyHitByAction = [];
  h.groove = Math.min(100, h.groove + (tier === "perfect" ? 8 : tier === "great" ? 5 : tier === "good" ? 2 : 0));
  state.log.push(`${tier} ${kind}: startup ${state.currentAttack.startup}f, active ${state.currentAttack.active}f.`);
  return true;
}

function empower(data: AttackFrameData, tier: JudgmentTier): AttackFrameData {
  const m = tier === "perfect" ? 1.35 : tier === "great" ? 1.2 : tier === "good" ? 1.08 : 1;
  return { ...data, damage: Math.round(data.damage * m), knockback: data.knockback * m, hitstun: Math.round(data.hitstun * m) };
}

export function tickActionCombat(state: ActionCombatState, input: Vec2 = { x: 0, y: 0 }, di: Vec2 = { x: 0, y: 0 }): void {
  if (state.outcome !== "ongoing") return;
  state.frame++;
  updateHeroMovement(state, input);
  for (const f of [state.hero, ...state.enemies]) {
    f.position.x = Math.max(16, Math.min(state.arena.width - 16, f.position.x + f.velocity.x * FRAME_SECONDS));
    f.position.y = Math.max(42, Math.min(state.arena.height - 22, f.position.y + f.velocity.y * FRAME_SECONDS));
    if (f.invulnerableFrames > 0) f.invulnerableFrames--;
    if (f.dashCooldownFrames > 0) f.dashCooldownFrames--;
    if (f.hitstunFrames > 0) { f.hitstunFrames--; f.velocity.x += di.x * 18; f.velocity.y += di.y * 18; }
    f.velocity.x *= FRICTION; f.velocity.y *= FRICTION;
    if (f.action !== "idle" && f.action !== "run") f.actionFrame++;
  }
  resolveHitboxes(state);
  if (state.hero.action === "dash" && state.hero.actionFrame > 12) state.hero.action = "idle";
  if (state.currentAttack && state.hero.actionFrame > state.currentAttack.startup + state.currentAttack.active + state.currentAttack.recovery) { state.hero.action = "idle"; state.currentAttack = null; }
  state.enemies = state.enemies.filter((e) => e.hp > 0);
  if (state.enemies.length === 0) state.outcome = "victory";
  if (state.hero.hp <= 0) state.outcome = "defeat";
}

function updateHeroMovement(state: ActionCombatState, input: Vec2): void {
  const h = state.hero;
  if (h.hitstunFrames > 0 || h.action === "dash") return;
  const len = Math.hypot(input.x, input.y);
  if (len > 0 && !state.currentAttack) {
    h.velocity.x += (input.x / len) * RUN_ACCEL * FRAME_SECONDS; h.velocity.y += (input.y / len) * RUN_ACCEL * FRAME_SECONDS;
    const speed = Math.hypot(h.velocity.x, h.velocity.y);
    if (speed > MAX_SPEED) { h.velocity.x = (h.velocity.x / speed) * MAX_SPEED; h.velocity.y = (h.velocity.y / speed) * MAX_SPEED; }
    h.facing = Math.abs(input.x) > Math.abs(input.y) ? (input.x < 0 ? "left" : "right") : input.y < 0 ? "up" : "down";
    h.action = "run";
  } else if (!state.currentAttack) h.action = "idle";
}

function resolveHitboxes(state: ActionCombatState): void {
  const attack = state.currentAttack, h = state.hero;
  if (!attack || h.actionFrame < attack.startup || h.actionFrame >= attack.startup + attack.active) return;
  for (const e of state.enemies) {
    if (e.invulnerableFrames > 0 || h.alreadyHitByAction.includes(e.id)) continue;
    const dx = e.position.x - h.position.x, dy = e.position.y - h.position.y;
    const forward = h.facing === "right" ? dx : h.facing === "left" ? -dx : h.facing === "down" ? dy : -dy;
    const lateral = h.facing === "right" || h.facing === "left" ? Math.abs(dy) : Math.abs(dx);
    if (forward >= 0 && forward <= attack.range && lateral <= attack.width) {
      e.hp -= attack.damage; e.damagePercent += attack.damage;
      const scale = 1 + e.damagePercent / 100;
      e.velocity.x += Math.sign(dx || 1) * attack.knockback * scale; e.velocity.y += Math.sign(dy || -0.25) * attack.knockback * 0.35 * scale;
      e.hitstunFrames = attack.hitstun;
      h.alreadyHitByAction.push(e.id);
      state.log.push(`${e.name} took ${attack.damage}; ${e.hitstunFrames}f hitstun, ${Math.round(e.damagePercent)}%.`);
    }
  }
}
