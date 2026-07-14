import Phaser from "phaser";
import { GameContext } from "../../state/GameContext";
import { getEncounter, getBeatmap, getEnemy, getCampaignNode } from "../../data/ContentRegistry";
import { TransportClock } from "../../systems/audio/TransportClock";
import { BeatmapSonifier } from "../../systems/audio/BeatmapSonifier";
import { music } from "../../systems/audio/SongPlayer";
import { BASE_WIDTH, BASE_HEIGHT } from "../../config/GameConfig";
import {
  createArena,
  step,
  player as getPlayer,
  enemies as getEnemies,
  type Arena,
  type FrameInput,
} from "../../systems/action/ActionCombat";

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
const FIGHT_SCALE: Record<string, number> = { the_conductor: 1.0, elite_wraith: 0.62, drifter: 0.48, slime: 0.45 };
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
  private sonifier: BeatmapSonifier | null = null;
  private arena: Arena | null = null; // null until the async clock is up
  private beatSeconds = 0.5;
  private encounterId: string;
  private nodeId: string | null;
  private isBoss = false;
  private finished = false;

  private cursors: Phaser.Types.Input.Keyboard.CursorKeys;
  private keys: Record<"W" | "A" | "S" | "D" | "J" | "K" | "L" | "I" | "SHIFT" | "SPACE", Phaser.Input.Keyboard.Key>;

  private sprites = new Map<string, Phaser.GameObjects.Sprite>();
  private shadows = new Map<string, Phaser.GameObjects.Ellipse>();
  private auras = new Map<string, Phaser.GameObjects.Image>();
  private accents = new Map<string, number>();
  private lastEnemyHp = new Map<string, number>();
  private fx: Phaser.GameObjects.Graphics;
  private bars: Phaser.GameObjects.Graphics;
  private plate: Phaser.GameObjects.Graphics;
  private beatPulse: Phaser.GameObjects.Arc;
  private attackGlow: Phaser.GameObjects.Image;
  private hud: Phaser.GameObjects.GameObject[] = [];

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
    this.keys = kb.addKeys("W,A,S,D,J,K,L,I,SHIFT,SPACE") as WorldFight["keys"];

    this.fx = this.scene.add.graphics().setDepth(8);
    this.bars = this.scene.add.graphics().setDepth(8.5);
    this.attackGlow = this.scene.add.image(0, 0, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(0xf4d27a).setDepth(7).setAlpha(0);

    // HUD (screen-space): the same INHALANTS plate as before + boss bar
    const plateBg = this.scene.add
      .nineslice(3, BASE_HEIGHT - 33, "ui_panel", undefined, 96, 30, 5, 5, 5, 5)
      .setOrigin(0, 0)
      .setScrollFactor(0)
      .setDepth(20)
      .setAlpha(0.94);
    const plateName = this.scene.add
      .text(9, BASE_HEIGHT - 30, "INHALANTS", { fontFamily: "monospace", fontSize: "6px", color: "#9fe8e0" })
      .setScrollFactor(0)
      .setDepth(21);
    this.beatPulse = this.scene.add.circle(90, BASE_HEIGHT - 26, 3, 0x49c6bd).setScrollFactor(0).setDepth(21);
    this.plate = this.scene.add.graphics().setDepth(21).setScrollFactor(0);
    this.hud.push(plateBg, plateName, this.beatPulse, this.plate);
    if (this.isBoss) {
      const name = getEnemy(encounter.enemyWave[0]).name.toUpperCase();
      this.hud.push(
        this.scene.add
          .nineslice(BASE_WIDTH / 2 - 71, 4, "ui_panel_boss", undefined, 142, 22, 5, 5, 5, 5)
          .setOrigin(0, 0)
          .setScrollFactor(0)
          .setDepth(20)
          .setAlpha(0.94),
        this.scene.add
          .text(BASE_WIDTH / 2, 8, name, { fontFamily: "monospace", fontSize: "6px", color: "#f0a648" })
          .setOrigin(0.5, 0)
          .setScrollFactor(0)
          .setDepth(21)
      );
    }
    this.bars.setScrollFactor(1); // enemy bars live in world space

    void this.start(encounter.enemyWave, nodeWorldX, nodeWorldY);
  }

  private async start(enemyWave: string[], foeX: number, foeY: number): Promise<void> {
    const encounter = getEncounter(this.encounterId);
    const beatmap = getBeatmap(encounter.trackId);
    const settings = GameContext.activeProfile!.settings;
    const bpm = beatmap.bpm * settings.gameSpeed;
    this.beatSeconds = 60 / bpm;

    await this.clock.start(bpm);
    if (this.finished) return; // torn down while the clock spun up
    this.sonifier = new BeatmapSonifier(this.clock);
    this.sonifier.setVolume(settings.volumeMusic * 0.22);
    music.setVolume(settings.volumeMusic);
    music.setMode(this.isBoss ? "boss" : "combat");
    music.start();
    this.sonifier.start(beatmap, bpm, this.clock.currentTime);
    GameContext.analytics.track("battle_started", { encounterId: this.encounterId });

    const enemyHps = encounter.enemyWave.map((id) => getEnemy(id).maxHp);
    const arena = createArena(this.rect.width, this.rect.height, enemyHps);

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
      const colossal = enemyId === "the_conductor";
      const tex = colossal ? "conductor_colossal" : `enemy_${enemyId}`;
      const scale = FIGHT_SCALE[enemyId] ?? 0.5;
      const accent = FIGHT_ACCENT[enemyId] ?? 0xffffff;
      this.accents.set(e.id, accent);
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

  private isOnBeat(): boolean {
    const t = this.clock.currentTime - (GameContext.activeProfile?.calibrationOffsetMs ?? 0) / 1000;
    const phase = ((t % this.beatSeconds) + this.beatSeconds) % this.beatSeconds;
    const off = Math.min(phase, this.beatSeconds - phase);
    const assist = GameContext.activeProfile?.settings.assistedTimingWindows ? 1.5 : 1;
    return off < 0.09 * assist;
  }

  private readInput(): FrameInput {
    const k = this.keys;
    const left = this.cursors.left.isDown || k.A.isDown;
    const right = this.cursors.right.isDown || k.D.isDown;
    const up = this.cursors.up.isDown || k.W.isDown;
    const down = this.cursors.down.isDown || k.S.isDown;
    const move = { x: (right ? 1 : 0) - (left ? 1 : 0), y: (down ? 1 : 0) - (up ? 1 : 0) };
    const JD = Phaser.Input.Keyboard.JustDown;
    const light = JD(k.J) || JD(k.SPACE);
    const heavy = JD(k.K);
    const special = JD(k.L);
    const dash = JD(k.SHIFT);
    const parry = JD(k.I);
    const onBeat = (light || heavy || special || dash || parry) && this.isOnBeat();
    return { move, dash, light, heavy, special, parry, onBeat };
  }

  /** Test seam: the live sim (null until the audio clock is up). */
  get simArena(): Arena | null {
    return this.arena;
  }

  /** Drive one frame. Returns true while the fight is live. */
  update(deltaMs: number): boolean {
    if (this.finished) return false;
    if (!this.arena) return true; // clock still starting
    const dt = Math.min(deltaMs / 1000, 1 / 30);
    step(this.arena, this.readInput(), dt);
    this.render();
    if (this.arena.outcome !== "ongoing") {
      this.finished = true;
      this.finish(this.arena.outcome);
      return false;
    }
    return true;
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
      this.playerSprite.setTexture("band_amir_attack", frame);
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
        s.setAlpha(0.1);
        this.auras.get(e.id)?.setAlpha(0);
        this.shadows.get(e.id)?.setAlpha(0);
        continue;
      }
      s.setPosition(Math.round(wx), Math.round(wy)).setDepth(4.6 + e.pos.y / 1000);
      this.shadows.get(e.id)?.setPosition(Math.round(wx), Math.round(wy));
      const windup = e.ai?.mode === "windup";
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
      if (e.hp < prev - 0.01 && !reduced) {
        const spark = this.scene.add.image(wx, wy - 8, "spark").setBlendMode(Phaser.BlendModes.ADD).setDepth(9).setScale(0.35).setTint(0xfff4d0);
        this.scene.tweens.add({ targets: spark, scale: 1.1, alpha: 0, angle: 40, duration: 220, onComplete: () => spark.destroy() });
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
    g.fillStyle(0xb98fca, 1).fillRect(px0 + 38, hpY + 7, Math.round((arena.groove / 100) * grW), 3);
    if (this.isBoss && foes[0] && foes[0].state !== "dead") {
      const bw = 130;
      const bx = BASE_WIDTH / 2 - bw / 2;
      g.fillStyle(0x1a0507, 1).fillRect(bx, 18, bw, 4);
      g.fillStyle(0xe04434, 1).fillRect(bx, 18, Math.max(0, Math.round((foes[0].hp / foes[0].maxHp) * bw)), 4);
    }
  }

  /** Rewards + campaign progression (ported from the retired arena scene's
   * finishBattle) -> ResultsScene; restarting scenes cleans everything up. */
  private finish(outcome: "victory" | "defeat"): void {
    this.clock.stop();
    this.sonifier?.dispose();
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
    this.sonifier?.dispose();
  }
}
