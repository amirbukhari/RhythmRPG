import Phaser from "phaser";
import { GameContext } from "../../state/GameContext";
import { getEncounter, getBeatmap, getEnemy, getCampaignNode, songMaps, bossPhaseConfigs } from "../../data/ContentRegistry";
import { TransportClock } from "../../systems/audio/TransportClock";
import { BeatTick } from "../../systems/audio/BeatTick";
import { SfxPlayer } from "../../systems/audio/SfxPlayer";
import { applyRelics } from "../../systems/progression/Relics";
import { music } from "../../systems/audio/SongPlayer";
import { tierAt, tierForOffset, beatIndexAt } from "../../systems/audio/SongBeat";
import type { SongMap } from "../../data/schemas/SongMap";
import { BASE_WIDTH, BASE_HEIGHT } from "../../config/GameConfig";
import {
  createArena,
  step,
  player as getPlayer,
  enemies as getEnemies,
  ULTIMATE_GROOVE_COST,
  type Arena,
  type BeatTier,
  type FrameInput,
} from "../../systems/action/ActionCombat";

/** Remappable combat actions (PRD §9.3) with their default key names. */
type CombatAction = "light" | "heavy" | "special" | "parry" | "dash" | "ultimate";
const DEFAULT_ACTION_KEYS: Record<CombatAction, string> = { light: "J", heavy: "K", special: "L", parry: "I", dash: "SHIFT", ultimate: "U" };

/** Resolve a stored KeyboardEvent.key binding ("z", "Shift", " ") to a
 * Phaser key name, falling back to the default when unset/unmappable. */
function keyNameFor(binding: string | undefined, fallback: string): string {
  if (!binding) return fallback;
  const name = binding === " " ? "SPACE" : binding.toUpperCase();
  return name in Phaser.Input.Keyboard.KeyCodes ? name : fallback;
}

const FACING_LUNGE: Record<string, { x: number; y: number }> = {
  up: { x: 0, y: -1 },
  down: { x: 0, y: 1 },
  left: { x: -1, y: 0 },
  right: { x: 1, y: 0 },
};

const TIER_LABEL: Record<Exclude<BeatTier, "off">, { text: string; color: string }> = {
  perfect: { text: "PERFECT", color: "#f4d27a" },
  great: { text: "GREAT", color: "#49c6bd" },
  good: { text: "GOOD", color: "#9fb0c0" },
};

/**
 * In-world combat (PRD §8.2 v7.6, owner: "the boss arenas shouldn't be
 * different places... it should be part of the overall world"). A fight no
 * longer loads a separate arena scene: when the player walks into a foe, the
 * camera locks to a screen-sized room of the ACTUAL overworld around it and
 * the action sim runs right there -- same ground, same props, same world.
 * ActionCombat is Phaser-free, so the sim's arena is simply mapped onto a
 * world-space rectangle. On any outcome the same rewards/Results flow as
 * before runs (restarting the scene cleans everything up).
 */

// world-proportioned foe scales (72px frames; conductor uses his colossal sheet)
// sheets are baked to fight size (bake_cast.py) -- everyone renders at 1.0
const FIGHT_SCALE: Record<string, number> = { the_conductor: 1.0, elite_wraith: 1.0, drifter: 1.0, slime: 1.0 };
const FIGHT_ACCENT: Record<string, number> = {
  the_conductor: 0xf0a648,
  elite_wraith: 0x49c6bd,
  drifter: 0x9fe8e0,
  slime: 0x9aca43,
};

export interface WorldFightHost {
  scene: Phaser.Scene;
  playerSprite: Phaser.GameObjects.Sprite;
  /** Tile walkability in WORLD pixels -- impassable tiles become sim obstacles. */
  isWorldWalkable(px: number, py: number): boolean;
}

export class WorldFight {
  private scene: Phaser.Scene;
  private host: WorldFightHost;
  private playerSprite: Phaser.GameObjects.Sprite;
  private rect: Phaser.Geom.Rectangle;
  private clock = new TransportClock();
  private tick: BeatTick | null = null;
  private sfx: SfxPlayer | null = null;
  private prevPlayerHp = -1;
  private prevLogLen = 0;
  private wasDashing = false;
  private arena: Arena | null = null; // null until the async clock is up
  private beatSeconds = 0.5; // file-time seconds per beat (HUD/fallback pacing)
  private songMap: SongMap | null = null;
  private gameSpeed = 1;
  private lastBeatIdx = -1;
  private tierPopup: Phaser.GameObjects.Text | null = null;
  private caption: Phaser.GameObjects.Text | null = null;
  private captionUntil = 0;
  private prevGroove = 0;
  private grooveWasFull = false;
  private wasWindup = new Set<string>();
  private deadHandled = new Set<string>();
  // Boss phases (§8.7): HP thresholds -> escalation + song-section jumps.
  private phaseThresholds: { hpThreshold: number; section?: string }[] = [];
  private phaseIdx = 0;
  private sightread: Phaser.GameObjects.Graphics | null = null;
  private encounterId: string;
  private nodeId: string | null;
  private isBoss = false;
  private finished = false;

  private cursors: Phaser.Types.Input.Keyboard.CursorKeys;
  private moveKeys: Record<"W" | "A" | "S" | "D", Phaser.Input.Keyboard.Key>;
  private spaceKey: Phaser.Input.Keyboard.Key;
  private actionKeys: Record<CombatAction, Phaser.Input.Keyboard.Key>;

  private sprites = new Map<string, Phaser.GameObjects.Sprite>();
  private shadows = new Map<string, Phaser.GameObjects.Ellipse>();
  private auras = new Map<string, Phaser.GameObjects.Image>();
  private accents = new Map<string, number>();
  private enemyIds = new Map<string, string>();
  private lastEnemyHp = new Map<string, number>();
  private fx: Phaser.GameObjects.Graphics;
  private bars: Phaser.GameObjects.Graphics;
  private plate: Phaser.GameObjects.Graphics;
  private beatPulse: Phaser.GameObjects.Arc;
  private attackGlow: Phaser.GameObjects.Image;
  private hud: Phaser.GameObjects.GameObject[] = [];
  /** Persistent ground-scuff decals stamped at every hit -- the fight scars
   * the ground it happens on (the HLD boss-room "battle happened here"
   * read), rather than resetting to pristine after every impact spark. */
  private groundDecals: Phaser.GameObjects.RenderTexture | null = null;
  private decalStamp: Phaser.GameObjects.Image | null = null;

  constructor(host: WorldFightHost, nodeId: string, encounterId: string, nodeWorldX: number, nodeWorldY: number) {
    this.scene = host.scene;
    this.host = host;
    this.playerSprite = host.playerSprite;
    this.encounterId = encounterId;
    this.nodeId = nodeId;
    const encounter = getEncounter(encounterId);
    this.isBoss = encounter.encounterId.startsWith("boss_");

    // a screen-sized room of the real world around the foe, clamped to the map
    const cam = this.scene.cameras.main;
    const bounds = cam.getBounds();
    const rx = Phaser.Math.Clamp(nodeWorldX - BASE_WIDTH / 2, bounds.x, bounds.right - BASE_WIDTH);
    const ry = Phaser.Math.Clamp(nodeWorldY - BASE_HEIGHT / 2, bounds.y, bounds.bottom - BASE_HEIGHT);
    this.rect = new Phaser.Geom.Rectangle(rx, ry, BASE_WIDTH, BASE_HEIGHT);
    cam.stopFollow();
    cam.pan(this.rect.centerX, this.rect.centerY, 320, "Sine.easeInOut");

    const kb = this.scene.input.keyboard!;
    this.cursors = kb.createCursorKeys();
    this.moveKeys = kb.addKeys("W,A,S,D") as WorldFight["moveKeys"];
    this.spaceKey = kb.addKey("SPACE");
    // Combat bindings are remappable (PRD §9.3); defaults J/K/L/I/SHIFT/U.
    const bindings = GameContext.activeProfile?.settings.keyBindings ?? {};
    this.actionKeys = Object.fromEntries(
      (Object.keys(DEFAULT_ACTION_KEYS) as CombatAction[]).map((action) => [
        action,
        kb.addKey(keyNameFor(bindings[action], DEFAULT_ACTION_KEYS[action])),
      ])
    ) as WorldFight["actionKeys"];

    this.fx = this.scene.add.graphics().setDepth(8);
    this.bars = this.scene.add.graphics().setDepth(8.5);
    this.attackGlow = this.scene.add.image(0, 0, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(0xf4d27a).setDepth(7).setAlpha(0);
    // ground scars: depth 3 sits above the painted plate/venue dressing (<=2.6)
    // and below every fighter's shadow/sprite (>=3.5), so scuffs read as part
    // of the ground, not a decal floating over the fight.
    this.groundDecals = this.scene.add.renderTexture(this.rect.x, this.rect.y, BASE_WIDTH, BASE_HEIGHT).setOrigin(0, 0).setDepth(3);
    this.decalStamp = this.scene.add.image(0, 0, "glow").setVisible(false);

    // HUD: the camera is locked to this.rect for the whole fight, so
    // screen-space UI is simply placed at rect + design offset (the retina
    // zoom made scrollFactor-0 drift under scrolled cameras -- see
    // OverworldScene.pinToScreen for the moving-camera variant).
    const ox = this.rect.x;
    const oy = this.rect.y;
    const plateBg = this.scene.add
      .nineslice(ox + 3, oy + BASE_HEIGHT - 33, "ui_panel", undefined, 96, 30, 5, 5, 5, 5)
      .setOrigin(0, 0)
      .setDepth(20)
      .setAlpha(0.94);
    const plateName = this.scene.add
      .text(ox + 9, oy + BASE_HEIGHT - 30, "MIR", { fontFamily: "monospace", fontSize: "6px", color: "#9fe8e0" })
      .setDepth(21);
    this.beatPulse = this.scene.add.circle(ox + 90, oy + BASE_HEIGHT - 26, 3, 0x49c6bd).setDepth(21);
    // graphics draw in design coords; positioning the object at the room's
    // corner maps them into the visible rect
    this.plate = this.scene.add.graphics().setDepth(21).setPosition(ox, oy);
    this.hud.push(plateBg, plateName, this.beatPulse, this.plate);
    if (this.isBoss) {
      const name = getEnemy(encounter.enemyWave[0]).name.toUpperCase();
      this.hud.push(
        this.scene.add
          .nineslice(ox + BASE_WIDTH / 2 - 71, oy + 4, "ui_panel_boss", undefined, 142, 22, 5, 5, 5, 5)
          .setOrigin(0, 0)
          .setDepth(20)
          .setAlpha(0.94),
        this.scene.add
          .text(ox + BASE_WIDTH / 2, oy + 8, name, { fontFamily: "monospace", fontSize: "6px", color: "#f0a648" })
          .setOrigin(0.5, 0)
          .setDepth(21)
      );
    }

    void this.start(encounter.enemyWave, nodeWorldX, nodeWorldY);
  }

  private async start(enemyWave: string[], foeX: number, foeY: number): Promise<void> {
    const encounter = getEncounter(this.encounterId);
    const settings = GameContext.activeProfile!.settings;
    this.gameSpeed = settings.gameSpeed;

    // BEAT TRUTH (PRD §8.3): the judged beat is the playing song's authored
    // beat grid, read from the element's own position. Game speed scales the
    // song's playbackRate and the sim together (the grid lives in file-time,
    // so heard and judged beat cannot diverge under any speed setting).
    music.setVolume(settings.volumeMusic);
    music.setRate(this.gameSpeed);
    music.setMode(this.isBoss ? "boss" : "combat");
    music.start();
    const songId = music.currentSongId();
    this.songMap = songId ? (songMaps.get(songId) ?? null) : null;

    // Fallback grid for when the song is not audible (blocked autoplay,
    // headless test runs): the transport at the song's fitted tempo -- or,
    // with no song map at all, the encounter's legacy beatmap tempo.
    const fileBpm = this.songMap?.bpm ?? getBeatmap(encounter.trackId).bpm;
    this.beatSeconds = 60 / fileBpm;
    await this.clock.start(fileBpm * this.gameSpeed);
    if (this.finished) return; // torn down while the clock spun up

    // The always-on sonifier click is retired (it clicked a grid unrelated
    // to the music); the audible tick is now the opt-in §9.3 assist.
    if (settings.beatTickEnabled) {
      this.tick = new BeatTick();
      this.tick.setVolume(settings.volumeMusic * 0.5);
    }
    this.sfx = new SfxPlayer();
    this.sfx.setVolume(settings.volumeSfx);
    GameContext.analytics.track("battle_started", { encounterId: this.encounterId });

    // Fight text layer: tier popups (§11.3 judgment feedback) + captions
    // for musically meaningful events (§9.3, when enabled).
    this.tierPopup = this.scene.add
      .text(0, 0, "", { fontFamily: "monospace", fontSize: "8px", color: "#f4d27a", stroke: "#05060a", strokeThickness: 3 })
      .setOrigin(0.5, 1)
      .setDepth(22)
      .setAlpha(0);
    this.caption = this.scene.add
      .text(this.rect.x + BASE_WIDTH / 2, this.rect.y + BASE_HEIGHT - 42, "", {
        fontFamily: "monospace",
        fontSize: "7px",
        color: "#d8ceb6",
        stroke: "#05060a",
        strokeThickness: 3,
      })
      .setOrigin(0.5, 1)
      .setDepth(22)
      .setAlpha(0);
    this.hud.push(this.caption);
    if (settings.sightreadEnabled) {
      this.sightread = this.scene.add.graphics().setDepth(21).setPosition(this.rect.x, this.rect.y);
      this.hud.push(this.sightread);
    }

    // One-time controls hint with the player's actual (possibly remapped)
    // bindings; practice mode announces its no-fail state (§9.3).
    const b = GameContext.activeProfile?.settings.keyBindings ?? {};
    const keyOf = (a: CombatAction): string => keyNameFor(b[a], DEFAULT_ACTION_KEYS[a]);
    this.showCaption(
      `${keyOf("light")} light  ${keyOf("heavy")} heavy  ${keyOf("special")} special  ${keyOf("parry")} parry  ${keyOf("dash")} dash  ${keyOf("ultimate")} ultimate`,
      5
    );

    // Boss phases (§8.7): HP thresholds -> aggression + song-section jumps.
    if (this.isBoss) {
      const config = bossPhaseConfigs.get(this.encounterId);
      if (config) this.phaseThresholds = config.phases.map((p) => ({ hpThreshold: p.hpThreshold, section: p.section }));
    }

    const enemyHps = encounter.enemyWave.map((id) => getEnemy(id).maxHp);
    const arena = createArena(this.rect.width, this.rect.height, enemyHps);
    // Relics (§8.5) apply their real effects at fight start.
    applyRelics(arena, GameContext.activeProfile?.relicInventory ?? []);
    // Practice mode (§9.3): the sim floors player HP at 1 -- no fail state.
    if (settings.practiceMode) {
      arena.practice = true;
      this.showCaption("PRACTICE — THE CHORUS HOLDS YOU UP (no fail state)", 4);
    }

    // impassable terrain (water/rock tiles) becomes sim obstacles, one 16px
    // box per blocked tile, so fighters fight on the actual walkable ground
    const TILE = 16;
    const obstacles: { x: number; y: number; w: number; h: number }[] = [];
    for (let ty = Math.floor(this.rect.y / TILE) * TILE; ty < this.rect.bottom; ty += TILE) {
      for (let tx = Math.floor(this.rect.x / TILE) * TILE; tx < this.rect.right; tx += TILE) {
        if (!this.host.isWorldWalkable(tx + TILE / 2, ty + TILE / 2)) {
          obstacles.push({ x: tx - this.rect.x, y: ty - this.rect.y, w: TILE, h: TILE });
        }
      }
    }
    arena.obstacles = obstacles;

    // the player fights from where they actually stand; the foe wave spawns
    // around where the foe actually stood -- the world does not rearrange
    const p = getPlayer(arena);
    p.pos.x = Phaser.Math.Clamp(this.playerSprite.x - this.rect.x, 12, this.rect.width - 12);
    p.pos.y = Phaser.Math.Clamp(this.playerSprite.y - this.rect.y, 12, this.rect.height - 12);
    getEnemies(arena).forEach((e, i) => {
      e.pos.x = Phaser.Math.Clamp(foeX - this.rect.x + (i - (enemyWave.length - 1) / 2) * 34, 16, this.rect.width - 16);
      e.pos.y = Phaser.Math.Clamp(foeY - this.rect.y + (i % 2) * 12, 16, this.rect.height - 16);

      const enemyId = enemyWave[i];
      // §8.6 curriculum: per-foe tempo/damage from authored content
      const def = getEnemy(enemyId);
      e.aggr = def.action?.aggression;
      e.strikeDamage = def.action?.damage;
      const colossal = enemyId === "the_conductor";
      const tex = colossal ? "conductor_colossal" : `enemy_${enemyId}`;
      const scale = FIGHT_SCALE[enemyId] ?? 0.5;
      const accent = FIGHT_ACCENT[enemyId] ?? 0xffffff;
      this.accents.set(e.id, accent);
      this.enemyIds.set(e.id, enemyId);
      this.lastEnemyHp.set(e.id, e.hp);
      const wx = this.rect.x + e.pos.x;
      const wy = this.rect.y + e.pos.y;
      this.shadows.set(e.id, this.scene.add.ellipse(wx, wy, 26 * scale, 8 * scale, 0x05060a, 0.42).setDepth(4.3));
      this.auras.set(
        e.id,
        this.scene.add.image(wx, wy - 8, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(accent).setDepth(4.32).setScale(scale).setAlpha(0.35)
      );
      const animKey = `wf_idle_${tex}`;
      if (!this.scene.anims.exists(animKey)) {
        this.scene.anims.create({
          key: animKey,
          frames: this.scene.anims.generateFrameNumbers(tex, { start: 0, end: 1 }),
          frameRate: colossal ? 1.2 : 1.6,
          repeat: -1,
        });
      }
      const s = this.scene.add.sprite(wx, wy, tex, 0).setOrigin(0.5, colossal ? 0.95 : 0.9).setScale(scale).setDepth(4.6);
      s.play(animKey);
      this.sprites.set(e.id, s);
    });
    this.arena = arena;
  }

  /** Full §8.3 four-tier judgment of "now" against the audible song's grid
   * (file-time windows, so reduced game speed widens them in real time);
   * transport-grid fallback when nothing is audible. */
  private judgeTier(): BeatTier {
    const calibMs = GameContext.activeProfile?.calibrationOffsetMs ?? 0;
    const assist = GameContext.activeProfile?.settings.assistedTimingWindows ? 1.5 : 1;

    const pos = music.position();
    if (this.songMap && pos !== null) return tierAt(this.songMap, pos, calibMs, assist);

    // Fallback: nothing audible (blocked autoplay / headless) -- judge on
    // the transport grid at the same tempo, as before beat maps existed.
    const t = this.clock.currentTime - calibMs / 1000;
    const beatSec = this.beatSeconds / this.gameSpeed; // transport runs in real time
    const phase = ((t % beatSec) + beatSec) % beatSec;
    return tierForOffset(Math.min(phase, beatSec - phase), assist);
  }

  private isOnBeat(): boolean {
    const tier = this.judgeTier();
    return tier === "perfect" || tier === "great";
  }

  /** Stamps 2-3 small dark scuffs into the ground at a hit's WORLD position --
   * a persistent scar, not a transient spark. Reduced-motion still gets the
   * scuffs (they're static ground detail, not motion) but photosensitivity
   * safe mode skips them (rapid stamping during a flurry is still "flashing
   * new content" territory). Coordinates are LOCAL to the render texture,
   * which sits at this.rect's origin. */
  private stampScuff(worldX: number, worldY: number, color: number): void {
    if (!this.groundDecals || !this.decalStamp) return;
    if (GameContext.activeProfile?.settings.photosensitivitySafeMode) return;
    const lx = worldX - this.rect.x;
    const ly = worldY - this.rect.y;
    const n = 2 + Math.floor(Math.random() * 2);
    for (let i = 0; i < n; i++) {
      const dx = (Math.random() - 0.5) * 14;
      const dy = (Math.random() - 0.5) * 8 + 3; // biased toward the feet, not the head
      this.decalStamp
        .setTint(color)
        .setAlpha(0.55 + Math.random() * 0.25)
        .setScale(0.13 + Math.random() * 0.06)
        .setAngle(Math.random() * 360);
      this.groundDecals.draw(this.decalStamp, lx + dx, ly + dy);
    }
  }

  /** §11.3 judgment feedback: a brief tier label above the player. Off-tier
   * presses show nothing (information, not punishment). */
  private showTierPopup(tier: BeatTier): void {
    if (tier === "off" || !this.tierPopup) return;
    const p = this.arena ? getPlayer(this.arena) : null;
    if (!p) return;
    const label = TIER_LABEL[tier];
    this.tierPopup
      .setText(label.text)
      .setColor(label.color)
      .setPosition(Math.round(this.rect.x + p.pos.x), Math.round(this.rect.y + p.pos.y - 18))
      .setAlpha(1);
    this.scene.tweens.killTweensOf(this.tierPopup);
    this.scene.tweens.add({ targets: this.tierPopup, alpha: 0, y: this.tierPopup.y - 6, duration: 420 });
  }

  /** Caption line for musically meaningful events (§9.3). The controls hint
   * and practice notice always show; event captions require the setting. */
  private showCaption(text: string, seconds: number): void {
    if (!this.caption) return;
    this.caption.setText(text).setAlpha(1);
    this.captionUntil = this.scene.time.now + seconds * 1000;
  }

  private readInput(): FrameInput {
    const m = this.moveKeys;
    const left = this.cursors.left.isDown || m.A.isDown;
    const right = this.cursors.right.isDown || m.D.isDown;
    const up = this.cursors.up.isDown || m.W.isDown;
    const down = this.cursors.down.isDown || m.S.isDown;
    const move = { x: (right ? 1 : 0) - (left ? 1 : 0), y: (down ? 1 : 0) - (up ? 1 : 0) };
    const JD = Phaser.Input.Keyboard.JustDown;
    const k = this.actionKeys;
    const light = JD(k.light) || JD(this.spaceKey);
    const heavy = JD(k.heavy);
    const special = JD(k.special);
    const dash = JD(k.dash);
    const parry = JD(k.parry);
    const ultimate = JD(k.ultimate);
    const acted = light || heavy || special || dash || parry || ultimate;
    let tier: BeatTier = "off";
    if (acted) {
      tier = this.judgeTier();
      // Per-tier events feed the §5 on-beat-rate KPI (binary pair kept for
      // continuity with the pre-tier data).
      const tierEvent = { perfect: "judgment_perfect", great: "judgment_great", good: "judgment_good", off: "judgment_off" } as const;
      GameContext.analytics.track(tierEvent[tier], { encounterId: this.encounterId });
      GameContext.analytics.track(tier === "perfect" || tier === "great" ? "judgment_onbeat" : "judgment_offbeat", {
        encounterId: this.encounterId,
      });
      this.showTierPopup(tier);
    }
    const onBeat = tier === "perfect" || tier === "great";
    return { move, dash, light, heavy, special, ultimate, parry, onBeat, tier };
  }

  /** Test seam: the live sim (null until the audio clock is up). */
  get simArena(): Arena | null {
    return this.arena;
  }

  /** Drive one frame. Returns true while the fight is live. */
  update(deltaMs: number): boolean {
    if (this.finished) return false;
    if (!this.arena) return true; // clock still starting
    // Game speed slows the whole fight with the slowed song (§8.3.3).
    const dt = Math.min(deltaMs / 1000, 1 / 30) * this.gameSpeed;
    this.prevGroove = this.arena.groove;
    step(this.arena, this.readInput(), dt);
    if (this.tick && this.songMap) {
      const pos = music.position();
      if (pos !== null) {
        const idx = beatIndexAt(this.songMap, pos);
        if (idx !== this.lastBeatIdx) {
          if (idx >= 0 && this.lastBeatIdx !== -1) this.tick.trigger();
          this.lastBeatIdx = idx;
        }
      }
    }

    const settings = GameContext.activeProfile?.settings;
    // Battle SFX from sim state transitions (never from render state).
    const p = getPlayer(this.arena);
    if (this.prevPlayerHp >= 0 && p.hp < this.prevPlayerHp - 0.01) {
      this.sfx?.hurt();
      this.stampScuff(this.playerSprite.x, this.playerSprite.y, 0x8a2020);
    }
    this.prevPlayerHp = p.hp;
    const reduced = Boolean(settings?.reducedMotion);
    if (p.state === "dash" && !this.wasDashing) {
      this.sfx?.dash();
      // dash after-images: two teal ghosts of the leader, fading fast
      if (!reduced) {
        for (let i = 0; i < 2; i++) {
          const ghost = this.scene.add
            .image(this.playerSprite.x, this.playerSprite.y, this.playerSprite.texture.key, this.playerSprite.frame.name)
            .setFlipX(this.playerSprite.flipX)
            .setScale(this.playerSprite.scaleX, this.playerSprite.scaleY)
            .setTint(0x49c6bd)
            .setAlpha(0.45 - i * 0.15)
            .setDepth(4.5);
          this.scene.tweens.add({ targets: ghost, alpha: 0, duration: 180 + i * 90, onComplete: () => ghost.destroy() });
        }
      }
    }
    this.wasDashing = p.state === "dash";
    if (this.arena.log.length > this.prevLogLen) {
      if (this.arena.log[this.arena.log.length - 1] === "parry!") {
        this.sfx?.parry();
        // parry burst: an expanding cyan ring at the player (§11.5 VFX)
        if (!reduced) {
          const ring = this.scene.add.circle(this.playerSprite.x, this.playerSprite.y - 6, 7).setStrokeStyle(2, 0x9fe8e0, 1).setDepth(9);
          this.scene.tweens.add({ targets: ring, scale: 3, alpha: 0, duration: 260, onComplete: () => ring.destroy() });
        }
      }
      this.prevLogLen = this.arena.log.length;
    }

    // Ultimate went off this tick (§8.5): the full-Groove verse.
    if (this.prevGroove >= ULTIMATE_GROOVE_COST && this.arena.groove <= this.prevGroove - ULTIMATE_GROOVE_COST) {
      GameContext.analytics.track("ultimate_used", { encounterId: this.encounterId });
      this.sfx?.ultimate();
      if (!settings?.reducedMotion && !settings?.photosensitivitySafeMode) this.scene.cameras.main.shake(280, 0.012);
      if (settings?.captionsEnabled) this.showCaption("♪ ULTIMATE — THE VERSE BREAKS THE SONG", 2);
      this.grooveWasFull = false;
    } else if (!this.grooveWasFull && this.arena.groove >= ULTIMATE_GROOVE_COST) {
      this.grooveWasFull = true;
      if (settings?.captionsEnabled) this.showCaption("GROOVE FULL — ULTIMATE READY", 2.5);
    } else if (this.arena.groove < ULTIMATE_GROOVE_COST) {
      this.grooveWasFull = false;
    }

    this.checkBossPhase();
    if (this.caption && this.caption.alpha > 0 && this.scene.time.now > this.captionUntil) {
      this.caption.setAlpha(Math.max(0, this.caption.alpha - deltaMs / 300));
    }
    this.render();
    if (this.arena.outcome !== "ongoing") {
      this.finished = true;
      this.finish(this.arena.outcome);
      return false;
    }
    return true;
  }

  /** §8.7: advance the boss phase when its HP crosses the next authored
   * threshold -- playback jumps to the phase's bound song section (the
   * judged grid follows automatically: it IS the same grid), the enemy
   * tempo escalates, and the transition is announced. */
  private checkBossPhase(): void {
    if (!this.isBoss || !this.arena || this.phaseIdx >= this.phaseThresholds.length - 1) return;
    const boss = getEnemies(this.arena)[0];
    if (!boss || boss.state === "dead") return;
    const next = this.phaseThresholds[this.phaseIdx + 1];
    if (boss.hp / boss.maxHp > next.hpThreshold) return;

    this.phaseIdx += 1;
    this.arena.enemyAggression = 1 + 0.35 * this.phaseIdx;
    const section = next.section ? this.songMap?.sections?.find((s) => s.name === next.section) : undefined;
    if (section) music.seek(section.startMs / 1000);
    GameContext.analytics.track("boss_phase_reached", { encounterId: this.encounterId, phase: this.phaseIdx + 1 });
    const numeral = ["I", "II", "III", "IV"][this.phaseIdx] ?? String(this.phaseIdx + 1);
    const settings = GameContext.activeProfile?.settings;
    if (settings?.captionsEnabled) this.showCaption(`♪ THE MUSIC SHIFTS — MOVEMENT ${numeral}`, 3);
    if (!settings?.reducedMotion && !settings?.photosensitivitySafeMode) this.scene.cameras.main.shake(220, 0.008);
  }

  /** Test seam: current boss phase index (0-based). */
  get bossPhaseIndex(): number {
    return this.phaseIdx;
  }

  private render(): void {
    const arena = this.arena!;
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const p = getPlayer(arena);

    // player: drive the leader's actual world sprite
    const pwx = this.rect.x + p.pos.x;
    const pwy = this.rect.y + p.pos.y;
    this.playerSprite.setPosition(Math.round(pwx), Math.round(pwy));
    if (p.facing === "left") this.playerSprite.setFlipX(false);
    else if (p.facing === "right") this.playerSprite.setFlipX(true);
    if (p.attack) {
      const frame = p.attack.phase === "startup" ? 0 : p.attack.phase === "active" ? 1 : 2;
      if (this.playerSprite.anims.isPlaying) this.playerSprite.anims.stop();
      this.playerSprite.setTexture("band_mir_attack", frame);
    } else {
      // run while the sim is moving him, breathe when standing
      const moving = Math.hypot(p.vel.x, p.vel.y) > 12;
      const want = moving ? "leader_walk" : "leader_idle";
      if (this.playerSprite.anims.getName() !== want || !this.playerSprite.anims.isPlaying) this.playerSprite.play(want);
    }
    if (p.state === "hitstun" && !reduced) this.playerSprite.setTintFill(0xffffff);
    else this.playerSprite.clearTint();
    this.playerSprite.setAlpha(p.iframes > 0 && !reduced ? (Math.floor(this.scene.time.now / 60) % 2 ? 0.4 : 1) : 1);

    // attack glow arc
    if (p.attack?.phase === "active") {
      const d = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[p.facing];
      this.attackGlow
        .setPosition(pwx + d[0] * p.attack.def.reach, pwy + d[1] * p.attack.def.reach)
        .setScale((p.attack.def.radius / 48) * (p.attack.onBeat ? 1.5 : 1))
        .setAlpha(p.attack.onBeat ? 0.9 : 0.6);
    } else {
      this.attackGlow.setAlpha(0);
    }

    // enemies
    this.fx.clear();
    for (const e of getEnemies(arena)) {
      const s = this.sprites.get(e.id);
      if (!s) continue;
      const wx = this.rect.x + e.pos.x;
      const wy = this.rect.y + e.pos.y;
      if (e.state === "dead") {
        // death dissolve (§11.5 VFX): one burst + a sink-and-fade, once
        if (!this.deadHandled.has(e.id)) {
          this.deadHandled.add(e.id);
          this.auras.get(e.id)?.setAlpha(0);
          this.shadows.get(e.id)?.setAlpha(0);
          if (!reduced) {
            for (let i = 0; i < 3; i++) {
              const spark = this.scene.add
                .image(s.x + (i - 1) * 6, s.y - 10 - i * 4, "spark")
                .setBlendMode(Phaser.BlendModes.ADD)
                .setDepth(9)
                .setScale(0.3)
                .setTint(this.accents.get(e.id) ?? 0xfff4d0);
              this.scene.tweens.add({ targets: spark, scale: 1.3, alpha: 0, angle: 70, duration: 380 + i * 80, onComplete: () => spark.destroy() });
            }
            this.scene.tweens.add({ targets: s, alpha: 0.08, y: s.y + 3, duration: 550 });
          } else {
            s.setAlpha(0.08);
          }
        }
        continue;
      }
      // Animation-state motion where per-frame art is absent (§11.5 /
      // v7.4 spec): windup crouches (anticipation), the strike's active
      // frames lunge and stretch toward the player (impact), recovery
      // settles back. Squash-and-stretch on the base scale, never baked in.
      const base = FIGHT_SCALE[this.enemyIds.get(e.id) ?? ""] ?? 0.5;
      let sx = base;
      let sy = base;
      let lunge = 0;
      if (e.ai?.mode === "windup") {
        sx = base * 1.08;
        sy = base * 0.9;
      } else if (e.attack?.phase === "active") {
        sx = base * 0.92;
        sy = base * 1.1;
        lunge = 4;
      } else if (e.attack?.phase === "startup") {
        sx = base * 1.05;
        sy = base * 0.94;
      }
      const d = FACING_LUNGE[e.facing] ?? { x: 0, y: 0 };
      s.setScale(sx, sy);
      s.setPosition(Math.round(wx + d.x * lunge), Math.round(wy + d.y * lunge)).setDepth(4.6 + e.pos.y / 1000);
      this.shadows.get(e.id)?.setPosition(Math.round(wx), Math.round(wy));
      const windup = e.ai?.mode === "windup";
      if (windup && !this.wasWindup.has(e.id)) {
        this.wasWindup.add(e.id);
        if (GameContext.activeProfile?.settings.captionsEnabled) {
          const side = e.pos.x < getPlayer(arena).pos.x ? "LEFT" : "RIGHT";
          this.showCaption(`⚠ ATTACK INCOMING — ${side}`, 1.2);
        }
      } else if (!windup) {
        this.wasWindup.delete(e.id);
      }
      const accent = this.accents.get(e.id) ?? 0xffffff;
      this.auras
        .get(e.id)
        ?.setPosition(wx, wy - 8)
        .setTint(windup ? 0xc22f34 : accent)
        .setAlpha(windup ? 0.7 : 0.3);
      if (windup) this.fx.lineStyle(2, 0xc22f34, 0.9).strokeCircle(wx, wy - 4, 12);
      if (e.state === "hitstun" && !reduced) s.setTintFill(0xffffff);
      else s.clearTint();
      const prev = this.lastEnemyHp.get(e.id) ?? e.hp;
      if (e.hp < prev - 0.01) {
        this.sfx?.hit(p.attack?.onBeat ?? false);
        // darken the foe's accent toward black -- a bruise/ichor stain in
        // its colour family, not a bright paint splash
        const r = (accent >> 16) & 0xff, g = (accent >> 8) & 0xff, b = accent & 0xff;
        const bruise = ((r * 0.6) << 16) | ((g * 0.6) << 8) | (b * 0.6);
        this.stampScuff(wx, wy, bruise);
        if (!reduced) {
          const spark = this.scene.add.image(wx, wy - 8, "spark").setBlendMode(Phaser.BlendModes.ADD).setDepth(9).setScale(0.35).setTint(0xfff4d0);
          this.scene.tweens.add({ targets: spark, scale: 1.1, alpha: 0, angle: 40, duration: 220, onComplete: () => spark.destroy() });
        }
      }
      this.lastEnemyHp.set(e.id, e.hp);
    }

    // bars + plate
    this.bars.clear();
    const foes = getEnemies(arena);
    for (let i = 0; i < foes.length; i++) {
      const f = foes[i];
      if (f.state === "dead") continue;
      if (this.isBoss && i === 0) continue; // boss bar is screen-space below
      const s = this.sprites.get(f.id);
      const w = 16;
      const x = Math.round(this.rect.x + f.pos.x - w / 2);
      const y = Math.round(this.rect.y + f.pos.y - (s ? s.displayHeight * 0.95 : 24));
      this.bars.fillStyle(0x05060a, 0.8).fillRect(x - 1, y - 1, w + 2, 3);
      this.bars.fillStyle(0xc22f34, 1).fillRect(x, y, Math.max(0, Math.round((f.hp / f.maxHp) * w)), 1);
    }

    this.beatPulse.setScale(this.isOnBeat() ? 1.7 : 1).setFillStyle(this.isOnBeat() ? 0xf4d27a : 0x49c6bd);
    const g = this.plate;
    g.clear();
    const px0 = 9;
    const hpY = BASE_HEIGHT - 22;
    const hpW = 78;
    g.fillStyle(0x05060a, 0.9).fillRect(px0 - 1, hpY - 1, hpW + 2, 5);
    g.fillStyle(0x7d1b20, 1).fillRect(px0, hpY, hpW, 3);
    g.fillStyle(0x49c6bd, 1).fillRect(px0, hpY, Math.max(0, Math.round((p.hp / p.maxHp) * hpW)), 3);
    for (let i = 0; i < 5; i++) g.fillStyle(i < arena.focus ? 0xf4d27a : 0x2a3138, 1).fillRect(px0 + i * 7, hpY + 7, 5, 3);
    const grW = 40;
    g.fillStyle(0x2a3138, 1).fillRect(px0 + 38, hpY + 7, grW, 3);
    // Groove: pulses bright when the ultimate is ready (§8.5).
    const grooveReady = arena.groove >= ULTIMATE_GROOVE_COST;
    const pulse = grooveReady && Math.floor(this.scene.time.now / 220) % 2 === 0;
    g.fillStyle(pulse ? 0xf4d27a : 0xb98fca, 1).fillRect(px0 + 38, hpY + 7, Math.round((arena.groove / 100) * grW), 3);
    if (this.isBoss && foes[0] && foes[0].state !== "dead") {
      const bw = 130;
      const bx = BASE_WIDTH / 2 - bw / 2;
      g.fillStyle(0x1a0507, 1).fillRect(bx, 18, bw, 4);
      g.fillStyle(0xe04434, 1).fillRect(bx, 18, Math.max(0, Math.round((foes[0].hp / foes[0].maxHp) * bw)), 4);
      // authored phase markers on the trough (§8.7)
      for (let i = 1; i < this.phaseThresholds.length; i++) {
        g.fillStyle(0x05060a, 1).fillRect(bx + Math.round(this.phaseThresholds[i].hpThreshold * bw) - 1, 17, 1, 6);
      }
    }

    this.drawSightread(arena);
  }

  /** Sightread (§8.4): the "see the music" forecast lane -- the next ~2.5s
   * of song beats scroll toward a now-line, with telegraphed enemy strikes
   * marked in red so the player reads the fight before it lands. */
  private drawSightread(arena: Arena): void {
    if (!this.sightread) return;
    const g = this.sightread;
    g.clear();
    const pos = music.position();
    if (!this.songMap || pos === null) return;
    const laneW = 92;
    const laneX = BASE_WIDTH - laneW - 6;
    const laneY = BASE_HEIGHT - 12;
    const horizon = 2.5; // seconds of forecast, in file-time
    g.fillStyle(0x05060a, 0.72).fillRect(laneX - 3, laneY - 5, laneW + 6, 10);
    g.fillStyle(0xf4d27a, 1).fillRect(laneX, laneY - 4, 1, 8); // the now-line
    // upcoming beats from the grid (loop-aware into the next pass)
    const beats = this.songMap.beatTimesMs;
    const posMs = pos * 1000;
    for (let pass = 0; pass < 2; pass++) {
      const shift = pass * this.songMap.durationMs;
      for (const b of beats) {
        const dt = (b + shift - posMs) / 1000;
        if (dt < 0) continue;
        if (dt > horizon) break;
        const x = laneX + (dt / horizon) * laneW;
        g.fillStyle(0x49c6bd, 0.9).fillRect(Math.round(x), laneY - 2, 1, 4);
      }
      if (beats.length > 0 && (beats[0] + shift - posMs) / 1000 > horizon) break;
    }
    // telegraphed enemy strikes: windup remainder + attack startup, sim-time
    // (sim and song both run at gameSpeed, so the axes agree)
    for (const e of getEnemies(arena)) {
      if (e.state === "dead" || e.ai?.mode !== "windup") continue;
      const dt = Math.max(0, e.ai.timer) + 0.28; // ENEMY_STRIKE startup
      if (dt > horizon) continue;
      const x = laneX + (dt / horizon) * laneW;
      g.fillStyle(0xc22f34, 1).fillRect(Math.round(x) - 1, laneY - 4, 3, 8);
    }
  }

  /** Rewards + campaign progression (ported from the retired arena scene's
   * finishBattle) -> ResultsScene; restarting scenes cleans everything up. */
  private finish(outcome: "victory" | "defeat"): void {
    this.clock.stop();
    this.tick?.dispose();
    this.sfx?.dispose();
    music.setRate(1); // the world outside the fight runs (and sounds) at 1x
    const profile = GameContext.activeProfile!;
    const encounter = getEncounter(this.encounterId);
    const victory = outcome === "victory";
    const newlyUnlockedSkills: string[] = [];

    if (victory) {
      profile.campaignProgress.xp += encounter.victoryRewards.xp;
      profile.campaignProgress.currency += encounter.victoryRewards.currency;
      if (this.nodeId) {
        if (!profile.campaignProgress.clearedNodeIds.includes(this.nodeId)) profile.campaignProgress.clearedNodeIds.push(this.nodeId);
        const node = getCampaignNode(this.nodeId);
        if (node.next.length > 0) profile.campaignProgress.currentNodeId = node.next[0];
        if (node.type === "boss") {
          for (const classId of ["warrior", "tank", "mage", "healer"]) {
            const skillId = `${classId}_tier2`;
            if (!profile.unlockedSkills.includes(skillId)) {
              profile.unlockedSkills.push(skillId);
              newlyUnlockedSkills.push(skillId);
            }
          }
          // The FINAL boss: route the results screen into the ending.
          if (node.next.length === 0) {
            GameContext.campaignJustCompleted = true;
            profile.campaignCompletedAt ??= Date.now();
          }
        }
      }
      GameContext.analytics.track("encounter_cleared", { encounterId: this.encounterId });
    } else {
      GameContext.analytics.track("encounter_failed", { encounterId: this.encounterId });
    }

    const relicChoices = victory
      ? (encounter.victoryRewards.relicChoices ?? []).filter((id) => !profile.relicInventory.includes(id))
      : [];

    GameContext.lastBattleResult = {
      outcome: victory ? "victory" : "defeat",
      encounterId: this.encounterId,
      xp: victory ? encounter.victoryRewards.xp : 0,
      currency: victory ? encounter.victoryRewards.currency : 0,
      relicChoices,
      unlockedSkills: newlyUnlockedSkills,
    };
    GameContext.pendingEncounterId = null;
    GameContext.returnToNodeId = this.nodeId;
    GameContext.pendingNodeId = null;

    void GameContext.persistActiveProfile().then(() => this.scene.scene.start("ResultsScene"));
  }

  /** Immediate teardown (scene shutdown while a fight is live). */
  destroy(): void {
    this.finished = true;
    this.clock.stop();
    this.tick?.dispose();
    this.sfx?.dispose();
    music.setRate(1);
  }
}
