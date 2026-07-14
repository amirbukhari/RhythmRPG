// Real-time action-combat simulation for The Drowned Chorus (PRD §8.2, v6.0).
// Phaser-free and tick-based so the whole fight -- movement/momentum, dashes
// with i-frames, frame-data attacks, hitstun, damage-%-scaled knockback, DI,
// on-beat power, and enemy AI -- is deterministic and unit-testable. The
// scene (ActionBattleScene) owns sprites/input/audio-clock; this owns "what
// happens this tick". All timing is in seconds (dt-driven), never wall-clock.

export interface Vec {
  x: number;
  y: number;
}
export type Facing = "up" | "down" | "left" | "right";
export type FighterState = "idle" | "run" | "dash" | "attack" | "hitstun" | "dead";

export interface AttackDef {
  startup: number;
  active: number;
  recovery: number;
  damage: number;
  knockback: number; // base launch speed (px/s) at 0 damage%
  reach: number; // how far the hitbox centre sits ahead of the body
  radius: number; // hitbox radius
}

/** The player's attacks (PRD §8.2). Special costs Focus; Ultimate costs the
 * full Groove meter (§8.5) -- a screen-shaking burst centred on the player. */
export const LIGHT: AttackDef = { startup: 0.05, active: 0.08, recovery: 0.13, damage: 6, knockback: 110, reach: 15, radius: 12 };
export const HEAVY: AttackDef = { startup: 0.19, active: 0.1, recovery: 0.28, damage: 14, knockback: 250, reach: 20, radius: 14 };
export const SPECIAL: AttackDef = { startup: 0.12, active: 0.1, recovery: 0.22, damage: 20, knockback: 210, reach: 22, radius: 16 };
export const ULTIMATE: AttackDef = { startup: 0.32, active: 0.18, recovery: 0.5, damage: 34, knockback: 380, reach: 0, radius: 64 };
export const ENEMY_STRIKE: AttackDef = { startup: 0.28, active: 0.12, recovery: 0.4, damage: 9, knockback: 160, reach: 16, radius: 13 };

export const SPECIAL_FOCUS_COST = 1;
export const FOCUS_MAX = 5;
export const ULTIMATE_GROOVE_COST = 100;
const PARRY_WINDOW = 0.16; // active parry frames after an on-beat guard
const PARRY_CD = 0.45;
// A press during an attack's recovery can cancel into the next attack, but
// only inside this window AND on-beat -- the rhythm-gated combo/gatling layer.
const CANCEL_WINDOW = 0.12;

const MOVE_ACCEL = 900;
const MAX_SPEED = 92;
const FRICTION = 780;
const DASH_SPEED = 250;
const DASH_TIME = 0.16;
const DASH_IFRAMES = 0.13;
const DASH_IFRAMES_ONBEAT = 0.22;
const DASH_CD = 0.5;
const DASH_CD_ONBEAT = 0.3;

/** The four §8.3 judgment tiers grading a real-time action against the
 * playing song's nearest beat. Off-beat actions still execute, weaker. */
export type BeatTier = "perfect" | "great" | "good" | "off";

/** Power multiplier per judgment tier (§8.3 table). "great" keeps the
 * pre-tier on-beat value (1.5) so the established feel is the middle rung;
 * "perfect" sits above it. */
export function tierMultiplier(tier: BeatTier): number {
  return tier === "perfect" ? 1.75 : tier === "great" ? 1.5 : tier === "good" ? 1.2 : 1;
}

/** Groove gained when a player hit lands, per the tier it was thrown at. */
export function tierGroove(tier: BeatTier): number {
  return tier === "perfect" ? 12 : tier === "great" ? 8 : tier === "good" ? 3 : 0;
}

export interface ActiveAttack {
  def: AttackDef;
  phase: "startup" | "active" | "recovery";
  timer: number;
  onBeat: boolean; // tier is great-or-better (drives the strong visual read)
  tier: BeatTier;
  hitIds: string[]; // targets already struck this swing (one hit per active window)
}

export interface Fighter {
  id: string;
  team: "player" | "enemy";
  pos: Vec;
  vel: Vec;
  facing: Facing;
  hp: number;
  maxHp: number;
  damagePct: number; // Melee-style: scales incoming knockback
  radius: number;
  state: FighterState;
  stateTimer: number; // committed lock (hitstun / dash) countdown
  iframes: number;
  dashCd: number;
  parryTimer: number; // >0 = an on-beat parry is active this instant
  parryCd: number;
  attack: ActiveAttack | null;
  ai?: { mode: "approach" | "windup" | "recover"; timer: number };
}

export interface FrameInput {
  move: Vec; // desired direction, components in [-1,1]
  dash: boolean; // edge-triggered (just pressed)
  light: boolean;
  heavy: boolean;
  special: boolean;
  ultimate?: boolean; // edge-triggered; consumes the full Groove meter (§8.5)
  parry: boolean;
  onBeat: boolean; // was this press inside the on-beat window (§8.3)
  /** Full §8.3 judgment tier of this press. Optional for callers that only
   * know the binary window (retired scene): onBeat maps to "great". */
  tier?: BeatTier;
}

/** An impassable axis-aligned box (world-fight terrain: water, rock). */
export interface Obstacle {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Arena {
  width: number;
  height: number;
  fighters: Fighter[];
  groove: number; // 0..100, player's shared meter
  focus: number;
  outcome: "ongoing" | "victory" | "defeat";
  log: string[];
  /** Impassable terrain inside the arena (in-world fights, PRD v7.13). */
  obstacles?: Obstacle[];
  /** Practice mode (PRD §9.3): the player cannot fall -- HP floors at 1. */
  practice?: boolean;
  /** Boss-phase escalation (§8.7): scales enemy tempo. 1 = base; higher =
   * shorter telegraphs, faster approach, shorter recovers. */
  enemyAggression?: number;
}

const FACING_VEC: Record<Facing, Vec> = {
  up: { x: 0, y: -1 },
  down: { x: 0, y: 1 },
  left: { x: -1, y: 0 },
  right: { x: 1, y: 0 },
};

// --- pure helpers (directly unit-tested) -----------------------------------

export function circlesOverlap(a: Vec, ar: number, b: Vec, br: number): boolean {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return dx * dx + dy * dy <= (ar + br) * (ar + br);
}

/** Knockback grows with the victim's accumulated damage% (Melee-style). */
export function knockbackSpeed(base: number, damagePct: number): number {
  return base * (1 + damagePct / 100);
}

export function hitstunSeconds(damage: number, damagePct: number): number {
  return Math.min(0.6, 0.12 + damage * 0.018 + damagePct * 0.0015);
}

/** Legacy binary view of the tier table (retired scene + old tests): the
 * boolean on-beat window maps to the "great" tier. */
export function onBeatMultiplier(onBeat: boolean): number {
  return tierMultiplier(onBeat ? "great" : "off");
}

export function hitboxCentre(f: Fighter, reach: number): Vec {
  const d = FACING_VEC[f.facing];
  return { x: f.pos.x + d.x * reach, y: f.pos.y + d.y * reach };
}

function facingFromMove(move: Vec, current: Facing): Facing {
  if (move.x === 0 && move.y === 0) return current;
  if (Math.abs(move.x) >= Math.abs(move.y)) return move.x < 0 ? "left" : "right";
  return move.y < 0 ? "up" : "down";
}

function clampToArena(f: Fighter, w: number, h: number): void {
  f.pos.x = Math.max(f.radius, Math.min(w - f.radius, f.pos.x));
  f.pos.y = Math.max(f.radius, Math.min(h - f.radius, f.pos.y));
}

/** Push a fighter's centre out of any obstacle box along the axis of least
 * penetration (and kill that velocity component) -- terrain in in-world
 * fights (water, rock) is impassable for every fighter. Exported for tests. */
export function resolveObstacles(f: Fighter, obstacles: Obstacle[] | undefined): void {
  if (!obstacles) return;
  for (const o of obstacles) {
    const nx = Math.max(o.x, Math.min(o.x + o.w, f.pos.x));
    const ny = Math.max(o.y, Math.min(o.y + o.h, f.pos.y));
    const dx = f.pos.x - nx;
    const dy = f.pos.y - ny;
    const d2 = dx * dx + dy * dy;
    if (d2 >= f.radius * f.radius) continue;
    if (d2 > 1e-6) {
      // centre outside the box: push out along the contact normal
      const d = Math.sqrt(d2);
      f.pos.x = nx + (dx / d) * f.radius;
      f.pos.y = ny + (dy / d) * f.radius;
    } else {
      // centre inside the box: exit along the smallest penetration axis
      const left = f.pos.x - o.x;
      const right = o.x + o.w - f.pos.x;
      const top = f.pos.y - o.y;
      const bottom = o.y + o.h - f.pos.y;
      const m = Math.min(left, right, top, bottom);
      if (m === left) f.pos.x = o.x - f.radius;
      else if (m === right) f.pos.x = o.x + o.w + f.radius;
      else if (m === top) f.pos.y = o.y - f.radius;
      else f.pos.y = o.y + o.h + f.radius;
    }
    if (Math.abs(f.pos.x - nx) > Math.abs(f.pos.y - ny)) f.vel.x = 0;
    else f.vel.y = 0;
  }
}

// --- construction ----------------------------------------------------------

export function createFighter(id: string, team: "player" | "enemy", pos: Vec, maxHp: number): Fighter {
  return {
    id,
    team,
    pos: { ...pos },
    vel: { x: 0, y: 0 },
    facing: team === "player" ? "up" : "down",
    hp: maxHp,
    maxHp,
    damagePct: 0,
    radius: team === "player" ? 8 : 11,
    state: "idle",
    stateTimer: 0,
    iframes: 0,
    dashCd: 0,
    parryTimer: 0,
    parryCd: 0,
    attack: null,
    ai: team === "enemy" ? { mode: "approach", timer: 0 } : undefined,
  };
}

export function createArena(width: number, height: number, enemyHps: number[]): Arena {
  const player = createFighter("player", "player", { x: width / 2, y: height - 30 }, 100);
  const fighters: Fighter[] = [player];
  enemyHps.forEach((hp, i) => {
    const x = width * ((i + 1) / (enemyHps.length + 1));
    fighters.push(createFighter(`enemy${i}`, "enemy", { x, y: 34 }, hp));
  });
  return { width, height, fighters, groove: 0, focus: 0, outcome: "ongoing", log: [] };
}

export function player(a: Arena): Fighter {
  return a.fighters[0];
}
export function enemies(a: Arena): Fighter[] {
  return a.fighters.filter((f) => f.team === "enemy");
}

// --- the tick --------------------------------------------------------------

function applyHit(a: Arena, attacker: Fighter, def: AttackDef, target: Fighter, tier: BeatTier, di: Vec): void {
  if (target.iframes > 0 || target.state === "dead") return;
  // On-beat parry: negate the hit and stagger the attacker into hitstun,
  // knocked back off the target -- defence converted into offence (PRD §8.2).
  if (target.parryTimer > 0) {
    target.parryTimer = 0;
    let bx = attacker.pos.x - target.pos.x;
    let by = attacker.pos.y - target.pos.y;
    const bl = Math.hypot(bx, by) || 1;
    attacker.vel = { x: (bx / bl) * 180, y: (by / bl) * 180 };
    attacker.state = "hitstun";
    attacker.stateTimer = 0.45;
    attacker.attack = null;
    if (attacker.ai) attacker.ai.mode = "approach";
    a.groove = Math.min(100, a.groove + 14);
    a.focus = Math.min(FOCUS_MAX, a.focus + 1);
    a.log.push("parry!");
    return;
  }
  const mult = tierMultiplier(tier);
  const dmg = def.damage * mult;
  target.hp -= dmg;
  target.damagePct += dmg;
  // Practice mode (PRD §9.3): no fail state -- the player's HP floors at 1.
  if (a.practice && target.team === "player" && target.hp < 1) target.hp = 1;
  // knockback direction: from attacker to target, nudged by DI (defender input)
  let dx = target.pos.x - attacker.pos.x;
  let dy = target.pos.y - attacker.pos.y;
  const len = Math.hypot(dx, dy) || 1;
  dx = dx / len + di.x * 0.4;
  dy = dy / len + di.y * 0.4;
  const dl = Math.hypot(dx, dy) || 1;
  const speed = knockbackSpeed(def.knockback, target.damagePct) * mult;
  target.vel = { x: (dx / dl) * speed, y: (dy / dl) * speed };
  target.state = "hitstun";
  target.stateTimer = hitstunSeconds(dmg, target.damagePct);
  target.attack = null;
  if (attacker.team === "player") {
    a.groove = Math.min(100, a.groove + tierGroove(tier));
    if (tier === "perfect" || tier === "great") a.focus = Math.min(FOCUS_MAX, a.focus + 1);
  }
  if (target.hp <= 0) {
    target.hp = 0;
    target.state = "dead";
    target.vel = { x: 0, y: 0 };
    a.log.push(`${target.id} falls`);
  }
}

function startAttack(f: Fighter, def: AttackDef, tier: BeatTier): void {
  const onBeat = tier === "perfect" || tier === "great";
  f.attack = { def, phase: "startup", timer: def.startup, onBeat, tier, hitIds: [] };
  f.state = "attack";
  f.stateTimer = def.startup + def.active + def.recovery;
}

function advanceAttack(a: Arena, f: Fighter, dt: number, di: Vec): void {
  const atk = f.attack;
  if (!atk) return;
  atk.timer -= dt;
  if (atk.phase === "active") {
    const centre = hitboxCentre(f, atk.def.reach);
    for (const other of a.fighters) {
      if (other.team === f.team || other.state === "dead" || atk.hitIds.includes(other.id)) continue;
      if (circlesOverlap(centre, atk.def.radius, other.pos, other.radius)) {
        atk.hitIds.push(other.id);
        applyHit(a, f, atk.def, other, atk.tier, di);
      }
    }
  }
  if (atk.timer <= 0) {
    if (atk.phase === "startup") {
      atk.phase = "active";
      atk.timer = atk.def.active;
    } else if (atk.phase === "active") {
      atk.phase = "recovery";
      atk.timer = atk.def.recovery;
    } else {
      f.attack = null;
      if (f.state === "attack") f.state = "idle";
    }
  }
}

function stepPlayer(a: Arena, f: Fighter, input: FrameInput, dt: number): void {
  const busy = f.state === "hitstun" || f.state === "attack" || f.state === "dash";
  const tier: BeatTier = input.tier ?? (input.onBeat ? "great" : "off");
  const onBeat = tier === "perfect" || tier === "great";

  // On-beat parry (guard): opens a negate-and-stagger window graded by tier.
  // Off-beat presses still spend the cooldown -- a punishable whiff (§8.2).
  if (input.parry && !busy && f.parryCd <= 0) {
    f.parryTimer = onBeat ? PARRY_WINDOW : tier === "good" ? 0.1 : 0.04;
    f.parryCd = PARRY_CD;
    f.facing = facingFromMove(input.move, f.facing);
    return;
  }

  // A press during an attack's recovery can cancel into the next attack, but
  // only on-beat and inside the cancel window -- rhythm-gated combo strings.
  const inCancelWindow = f.state === "attack" && f.attack?.phase === "recovery" && onBeat && f.attack.timer <= CANCEL_WINDOW;

  // dash (i-frame burst) -- only from a free state; i-frames grade by tier
  if (input.dash && !busy && f.dashCd <= 0) {
    f.facing = facingFromMove(input.move, f.facing);
    const d = input.move.x || input.move.y ? input.move : FACING_VEC[f.facing];
    const dl = Math.hypot(d.x, d.y) || 1;
    f.vel = { x: (d.x / dl) * DASH_SPEED, y: (d.y / dl) * DASH_SPEED };
    f.state = "dash";
    f.stateTimer = DASH_TIME;
    f.iframes = tier === "perfect" ? 0.24 : tier === "great" ? DASH_IFRAMES_ONBEAT : tier === "good" ? 0.16 : DASH_IFRAMES;
    f.dashCd = onBeat ? DASH_CD_ONBEAT : tier === "good" ? 0.4 : DASH_CD;
  } else if (input.ultimate && (f.state === "idle" || f.state === "run" || inCancelWindow) && a.groove >= ULTIMATE_GROOVE_COST) {
    // ULTIMATE (§8.5): spends the FULL Groove meter for a burst centred on
    // the player (reach 0) that hits everything in a wide radius; armored
    // through startup+active so the verse cannot be interrupted.
    a.groove -= ULTIMATE_GROOVE_COST;
    f.facing = facingFromMove(input.move, f.facing);
    startAttack(f, ULTIMATE, tier);
    f.iframes = Math.max(f.iframes, ULTIMATE.startup + ULTIMATE.active);
    a.log.push("ultimate!");
  } else if (input.special && (f.state === "idle" || f.state === "run" || inCancelWindow) && a.focus >= SPECIAL_FOCUS_COST) {
    a.focus -= SPECIAL_FOCUS_COST;
    f.facing = facingFromMove(input.move, f.facing);
    startAttack(f, SPECIAL, tier);
  } else if ((input.light || input.heavy) && (f.state === "idle" || f.state === "run" || inCancelWindow)) {
    f.facing = facingFromMove(input.move, f.facing);
    startAttack(f, input.light ? LIGHT : HEAVY, tier);
  } else if (f.state === "idle" || f.state === "run") {
    // free movement with momentum
    const m = input.move;
    if (m.x || m.y) {
      const ml = Math.hypot(m.x, m.y) || 1;
      f.vel.x += (m.x / ml) * MOVE_ACCEL * dt;
      f.vel.y += (m.y / ml) * MOVE_ACCEL * dt;
      const sp = Math.hypot(f.vel.x, f.vel.y);
      if (sp > MAX_SPEED) {
        f.vel.x = (f.vel.x / sp) * MAX_SPEED;
        f.vel.y = (f.vel.y / sp) * MAX_SPEED;
      }
      f.facing = facingFromMove(m, f.facing);
      f.state = "run";
    } else {
      f.state = "idle";
    }
  }
  if (f.attack) advanceAttack(a, f, dt, { x: 0, y: 0 });
}

function stepEnemy(a: Arena, f: Fighter, dt: number, di: Vec): void {
  if (f.state === "dead") return;
  const target = player(a);
  const ai = f.ai!;
  if (f.state === "hitstun") {
    if (f.attack) f.attack = null;
    return; // momentum carries; timers handled in integrate
  }
  const dx = target.pos.x - f.pos.x;
  const dy = target.pos.y - f.pos.y;
  const dist = Math.hypot(dx, dy) || 1;
  f.facing = facingFromMove({ x: dx, y: dy }, f.facing);

  if (f.attack) {
    advanceAttack(a, f, dt, di);
    return;
  }

  ai.timer -= dt;
  // Boss-phase escalation (§8.7): aggression > 1 shortens telegraphs and
  // recovers and quickens the approach -- the phase raises the tempo.
  const aggr = a.enemyAggression ?? 1;
  if (ai.mode === "approach") {
    if (dist > 26) {
      f.vel.x = (dx / dist) * 46 * aggr;
      f.vel.y = (dy / dist) * 46 * aggr;
      f.state = "run";
    } else {
      f.vel.x *= 0.6;
      f.vel.y *= 0.6;
      ai.mode = "windup";
      ai.timer = 0.35 / aggr; // telegraph
    }
  } else if (ai.mode === "windup") {
    f.vel.x = 0;
    f.vel.y = 0;
    if (ai.timer <= 0) {
      startAttack(f, ENEMY_STRIKE, "off");
      ai.mode = "recover";
      ai.timer = (ENEMY_STRIKE.startup + ENEMY_STRIKE.active + ENEMY_STRIKE.recovery + 0.4) / aggr;
    }
  } else {
    if (ai.timer <= 0) ai.mode = "approach";
  }
}

/** Advance the whole arena by dt seconds. `di` is the defender's held direction (for player DI during hitstun). */
export function step(a: Arena, input: FrameInput, dt: number): Arena {
  if (a.outcome !== "ongoing") return a;

  const p = player(a);
  if (p.state !== "dead") stepPlayer(a, p, input, dt);
  // The player's held direction is their DI: it nudges the knockback of any
  // enemy strike that lands on them this tick (PRD §8.2).
  for (const e of enemies(a)) stepEnemy(a, e, dt, input.move);

  // integrate + timers
  for (const f of a.fighters) {
    if (f.state === "dead") continue;
    // friction when not driving movement
    const driving = f.state === "run" || f.state === "dash";
    if (!driving) {
      const sp = Math.hypot(f.vel.x, f.vel.y);
      if (sp > 0) {
        const drop = (f.state === "hitstun" ? FRICTION * 1.4 : FRICTION) * dt;
        const ns = Math.max(0, sp - drop);
        f.vel.x = (f.vel.x / sp) * ns;
        f.vel.y = (f.vel.y / sp) * ns;
      }
    }
    f.pos.x += f.vel.x * dt;
    f.pos.y += f.vel.y * dt;
    clampToArena(f, a.width, a.height);
    resolveObstacles(f, a.obstacles);

    f.iframes = Math.max(0, f.iframes - dt);
    f.dashCd = Math.max(0, f.dashCd - dt);
    f.parryTimer = Math.max(0, f.parryTimer - dt);
    f.parryCd = Math.max(0, f.parryCd - dt);
    if (f.stateTimer > 0) {
      f.stateTimer -= dt;
      if (f.stateTimer <= 0 && (f.state === "dash" || f.state === "hitstun")) f.state = "idle";
    }
  }

  if (p.state === "dead") a.outcome = "defeat";
  else if (enemies(a).every((e) => e.state === "dead")) a.outcome = "victory";
  return a;
}
