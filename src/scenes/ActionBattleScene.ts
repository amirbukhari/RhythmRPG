import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { getEncounter, getBeatmap, getEnemy, getCampaignNode } from "../data/ContentRegistry";
import { TransportClock } from "../systems/audio/TransportClock";
import { BeatmapSonifier } from "../systems/audio/BeatmapSonifier";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";
import { composeArena, ARENA_LAYOUTS } from "./env/ArenaComposer";
import { music } from "../systems/audio/SongPlayer";
import {
  createArena,
  step,
  player as getPlayer,
  enemies as getEnemies,
  type Arena,
  type FrameInput,
} from "../systems/action/ActionCombat";

// Top-down HLD arena: the whole screen is the walkable field. Arenas with a
// kitbash layout (ArenaComposer) are composed from individual environment
// pieces; others fall back to a single backdrop image. HORIZON is 0 -- fighters
// use the full field (kept as a named constant for the render offset).
const HORIZON = 0;
const ARENA_W = BASE_WIDTH;
const ARENA_H = BASE_HEIGHT;
// Colossal, imposing scale contrast (HLD, PRD §11.1) -- the player is small.
const ENEMY_SCALE: Record<string, number> = {
  the_conductor: 2.9,
  elite_wraith: 2.0,
  drifter: 1.5,
  slime: 1.4,
};
// The campaign nodes as movements of the drowned chorus (docs/design/world-bible.md).
const NODE_MOVEMENT: Record<string, string> = {
  opening_1: "The Shallows",
  mid_1: "The Salt Mines",
  mid_2: "The Pit Below",
  mid_3: "The Attic of Teeth",
  boss_1: "The Conductor's Hall",
};

// Per-movement arena backdrop + its story light: the one point in each place
// that visibly answers the music (PRD §11.1.1 rule 4), pulsing on the beat.
const NODE_ARENA: Record<string, { key: string; light: { x: number; y: number; color: number } }> = {
  opening_1: { key: "arena_shallows", light: { x: 202, y: 68, color: 0xf0a648 } }, // the leaning spire's lamp
  mid_1: { key: "arena_saltmines", light: { x: 258, y: 106, color: 0xf0a648 } }, // the singing tunnel mouth
  mid_2: { key: "arena_pit", light: { x: 142, y: 32, color: 0xf4d27a } }, // the lantern still burning
  mid_3: { key: "arena_attic", light: { x: 265, y: 57, color: 0xf0a648 } }, // the keyhole
  boss_1: { key: "arena_hall", light: { x: 161, y: 91, color: 0xf0a648 } }, // the podium flame
};
const DEFAULT_ARENA = { key: "arena_shallows", light: { x: 202, y: 68, color: 0xf0a648 } };

// Emissive accent per enemy for the additive glow (eyes / aura / telegraph).
const ENEMY_ACCENT: Record<string, number> = {
  the_conductor: 0xf0a648,
  elite_wraith: 0x49c6bd,
  drifter: 0x9fe8e0,
  slime: 0x9aca43,
};

/**
 * Real-time action-combat arena (PRD §8.2, v6.0). Run around, dash with
 * i-frames, and attack on the beat. All fight logic lives in the Phaser-free
 * ActionCombat sim (unit-tested); this scene owns input, sprites, the audio
 * clock, and rendering. Timing (on-beat power) derives from TransportClock,
 * never wall-clock (PRD §10.2).
 */
export class ActionBattleScene extends Phaser.Scene {
  private clock = new TransportClock();
  private sonifier!: BeatmapSonifier;
  private arena!: Arena;
  private beatSeconds = 0.5;
  private encounterId = "";
  private nodeId: string | null = null;
  private isBoss = false;
  private finished = false;

  private sprites = new Map<string, Phaser.GameObjects.Sprite>();
  private auras = new Map<string, Phaser.GameObjects.Image>();
  private eyes = new Map<string, Phaser.GameObjects.Image>();
  private groundShadows = new Map<string, Phaser.GameObjects.Ellipse>();
  private accents = new Map<string, number>();
  private lastEnemyHp = new Map<string, number>();
  private beatGlow!: Phaser.GameObjects.Image;
  private attackGlow!: Phaser.GameObjects.Image;
  private storyLight!: Phaser.GameObjects.Image;
  private hpBars!: Phaser.GameObjects.Graphics;
  private plate!: Phaser.GameObjects.Graphics;
  private dmgText!: Phaser.GameObjects.Text;
  private fx!: Phaser.GameObjects.Graphics;
  private beatPulse!: Phaser.GameObjects.Arc;

  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private keys!: Record<"W" | "A" | "S" | "D" | "J" | "K" | "L" | "I" | "SHIFT" | "SPACE", Phaser.Input.Keyboard.Key>;

  constructor() {
    super("ActionBattleScene");
  }

  async create(): Promise<void> {
    const encounterId = GameContext.pendingEncounterId;
    if (!encounterId || !GameContext.activeProfile) {
      this.scene.start("OverworldScene");
      return;
    }
    this.finished = false;
    this.encounterId = encounterId;
    this.nodeId = GameContext.pendingNodeId;
    const encounter = getEncounter(encounterId);
    const beatmap = getBeatmap(encounter.trackId);
    this.isBoss = encounter.encounterId.startsWith("boss_");
    const settings = GameContext.activeProfile.settings;
    const bpm = beatmap.bpm * settings.gameSpeed;
    this.beatSeconds = 60 / bpm;

    // the movement's own arena (PRD §11.1.1), now framed HLD-style: the AI
    // scene is the distant backdrop across the top HORIZON band; the rest is a
    // top-down walkable floor. The scene fills the whole screen behind, but a
    // top-down floor plane is painted over the bottom 3/4 so the backdrop reads
    // as horizon/atmosphere and the fight happens on the ground.
    const arenaDef = (this.nodeId && NODE_ARENA[this.nodeId]) || DEFAULT_ARENA;
    const layout = ARENA_LAYOUTS[arenaDef.key];
    if (layout) {
      // Intentional top-down arena kitbashed from individual environment pieces.
      composeArena(this, layout, arenaDef.key);
    } else {
      // Fallback: a single AI backdrop (top-down HLD-detail) + a light scrim so
      // fighters read against it.
      this.add.image(BASE_WIDTH / 2, BASE_HEIGHT / 2, arenaDef.key).setDepth(-10);
      this.add.graphics().setDepth(-9).fillStyle(0x05060a, 0.32).fillRect(0, 0, BASE_WIDTH, BASE_HEIGHT);
    }

    this.storyLight = this.add
      .image(arenaDef.light.x, arenaDef.light.y, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(arenaDef.light.color)
      .setScale(0.4)
      .setAlpha(0.28)
      .setDepth(-9);

    // build the sim from the encounter's enemy wave
    const enemyHps = encounter.enemyWave.map((id) => getEnemy(id).maxHp);
    this.arena = createArena(ARENA_W, ARENA_H, enemyHps);

    const ADD = Phaser.BlendModes.ADD;

    // on-beat flash under the player + the player's active-attack glow arc
    this.beatGlow = this.add.image(0, 0, "glow").setBlendMode(ADD).setTint(0x49c6bd).setDepth(4).setAlpha(0).setScale(1.3);
    this.attackGlow = this.add.image(0, 0, "glow").setBlendMode(ADD).setTint(0xf4d27a).setDepth(7).setAlpha(0).setScale(0.6);

    // player sprite (the party leader -- Amir, the band's guitarist). His
    // 48x48 art is scaled to sit small in the arena for the HLD size contrast.
    const p = getPlayer(this.arena);
    this.groundShadows.set(p.id, this.add.ellipse(p.pos.x, p.pos.y + HORIZON, 16, 6, 0x05060a, 0.4).setDepth(3));
    const pSprite = this.add.sprite(p.pos.x, p.pos.y + HORIZON, "band_amir", 0).setOrigin(0.5, 0.82).setScale(0.62).setDepth(5);
    if (!this.anims.exists("amir_idle")) {
      this.anims.create({
        key: "amir_idle",
        frames: this.anims.generateFrameNumbers("band_amir", { start: 0, end: this.textures.get("band_amir").frameTotal - 2 }),
        frameRate: 5,
        repeat: -1,
      });
    }
    pSprite.play("amir_idle");
    this.sprites.set(p.id, pSprite);

    // enemy sprites (colossal), each with an emissive aura + glowing eyes.
    // The Conductor uses his NATIVE colossal sheet (52x72 authored at size,
    // PRD §11.1) with a real 2-pose conducting animation -- never an
    // upscaled small sprite.
    getEnemies(this.arena).forEach((e, i) => {
      const enemyId = encounter.enemyWave[i];
      const colossal = enemyId === "the_conductor";
      const texKey = colossal ? "conductor_colossal" : `enemy_${enemyId}`;
      const scale = colossal ? 1.5 : (ENEMY_SCALE[enemyId] ?? 1.25);
      const accent = ENEMY_ACCENT[enemyId] ?? 0xffffff;
      this.accents.set(e.id, accent);
      this.lastEnemyHp.set(e.id, e.hp);
      const ey = e.pos.y + HORIZON;
      this.groundShadows.set(e.id, this.add.ellipse(e.pos.x, ey, 22 * scale, 8 * scale, 0x05060a, 0.42).setDepth(3));
      const aura = this.add.image(e.pos.x, ey, "glow").setBlendMode(ADD).setTint(accent).setDepth(3).setScale(scale * (colossal ? 1.6 : 1.1)).setAlpha(0.4);
      const eye = this.add.image(e.pos.x, ey, "glow").setBlendMode(ADD).setTint(accent).setDepth(6).setScale(scale * 0.4).setAlpha(0.85);
      this.auras.set(e.id, aura);
      this.eyes.set(e.id, eye);
      const animKey = `arena_idle_${texKey}`;
      if (!this.anims.exists(animKey)) {
        this.anims.create({ key: animKey, frames: this.anims.generateFrameNumbers(texKey, { start: 0, end: 1 }), frameRate: colossal ? 1.2 : 1.6, repeat: -1 });
      }
      const s = this.add.sprite(e.pos.x, ey, texKey, 0).setOrigin(0.5, colossal ? 0.95 : 0.85).setScale(scale).setDepth(4);
      s.play(animKey);
      this.sprites.set(e.id, s);
    });

    this.hpBars = this.add.graphics().setDepth(21); // above HUD frames (20)
    this.fx = this.add.graphics().setDepth(6);

    // --- HUD (AAA audit B4/B5): framed player plate + boss bar, no raw text
    // strips over the arena. The old full-width top band is gone -- the arena
    // gets the whole frame.
    this.add.nineslice(3, BASE_HEIGHT - 33, "ui_panel", undefined, 96, 30, 5, 5, 5, 5).setOrigin(0, 0).setDepth(20).setAlpha(0.94);
    this.add.text(9, BASE_HEIGHT - 30, "INHALANTS", { fontFamily: "monospace", fontSize: "6px", color: "#9fe8e0" }).setDepth(21);
    this.beatPulse = this.add.circle(90, BASE_HEIGHT - 26, 3, 0x49c6bd).setDepth(21);
    this.plate = this.add.graphics().setDepth(21);
    this.dmgText = this.add
      .text(92, BASE_HEIGHT - 12, "", { fontFamily: "monospace", fontSize: "6px", color: "#d8ceb6" })
      .setOrigin(1, 1)
      .setDepth(21);

    if (this.isBoss) {
      // top-centre boss bar with the foe's name above it (drawn in drawHpBars)
      const bossName = getEnemy(encounter.enemyWave[0]).name.toUpperCase();
      this.add.nineslice(BASE_WIDTH / 2 - 71, 4, "ui_panel_boss", undefined, 142, 22, 5, 5, 5, 5).setOrigin(0, 0).setDepth(20).setAlpha(0.94);
      this.add.text(BASE_WIDTH / 2, 8, bossName, { fontFamily: "monospace", fontSize: "6px", color: "#f0a648" }).setOrigin(0.5, 0).setDepth(21);
    }

    // controls hint: teach (top of frame, clear of the plate), then get out
    // of the way
    const hint = this.add
      .text(BASE_WIDTH / 2, this.isBoss ? 30 : 8, "WASD move · J/K atk · L special · I parry · Shift dash", {
        fontFamily: "monospace",
        fontSize: "7px",
        color: "#877d70",
        stroke: "#05060a",
        strokeThickness: 3,
      })
      .setOrigin(0.5, 0)
      .setDepth(21);
    this.tweens.add({ targets: hint, alpha: 0, delay: 6000, duration: 900 });

    this.showBattleIntro(encounter.enemyWave);

    // Wire input BEFORE the async clock.start() below: create() is async and
    // the scene reports active (and its update() loop starts) the moment it's
    // added, so a frame running during `await` must not touch undefined keys.
    const kb = this.input.keyboard!;
    this.cursors = kb.createCursorKeys();
    this.keys = kb.addKeys("W,A,S,D,J,K,L,I,SHIFT,SPACE") as ActionBattleScene["keys"];

    // audio clock + audible beat
    await this.clock.start(bpm);
    this.sonifier = new BeatmapSonifier(this.clock);
    // The real Inhalants track is the soundtrack now (SongPlayer); the beatmap
    // sonifier stays only as a quiet rhythm-cue tick so it doesn't clash.
    this.sonifier.setVolume(settings.volumeMusic * 0.22);
    music.setVolume(settings.volumeMusic);
    music.setMode(this.isBoss ? "boss" : "combat");
    music.start();
    this.sonifier.start(beatmap, bpm, this.clock.currentTime);
    GameContext.analytics.track("battle_started", { encounterId });

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      this.sonifier.dispose();
      this.clock.stop();
    });
  }

  update(_time: number, deltaMs: number): void {
    if (!this.arena || this.finished || !this.cursors) return;
    const dt = Math.min(deltaMs / 1000, 1 / 30); // clamp spikes so physics stays stable

    const input = this.readInput();
    step(this.arena, input, dt);

    this.render();

    if (this.arena.outcome !== "ongoing") {
      this.finished = true;
      this.finishBattle(this.arena.outcome);
    }
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
    // on-beat is evaluated at the instant of an action press
    const onBeat = (light || heavy || special || dash || parry) && this.isOnBeat();
    return { move, dash, light, heavy, special, parry, onBeat };
  }

  private render(): void {
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const beatWave = 0.5 + 0.5 * Math.sin((this.clock.currentTime / this.beatSeconds) * Math.PI * 2);

    // the arena's story light answers the music (PRD §11.1.1 rule 4)
    this.storyLight.setAlpha(reduced ? 0.3 : 0.18 + 0.32 * beatWave).setScale(reduced ? 0.5 : 0.42 + 0.16 * beatWave);
    for (const f of this.arena.fighters) {
      const s = this.sprites.get(f.id);
      if (!s) continue;
      if (f.state === "dead") {
        s.setAlpha(0.12);
        this.auras.get(f.id)?.setAlpha(0);
        this.eyes.get(f.id)?.setAlpha(0);
        this.groundShadows.get(f.id)?.setAlpha(0);
        continue;
      }
      const ry = f.pos.y + HORIZON; // render y on the floor
      s.setPosition(Math.round(f.pos.x), Math.round(ry));
      s.setDepth(4 + f.pos.y / 100);
      // Ground the shadow at the sprite's actual feet (origin isn't the bottom
      // edge), so it sits under the character instead of floating at its waist.
      const feetY = ry + s.displayHeight * (1 - s.originY);
      this.groundShadows.get(f.id)?.setPosition(Math.round(f.pos.x), Math.round(feetY)).setDepth(3);
      if (f.team === "player") {
        // Amir's hand-drawn art natively faces LEFT; flip for right, and keep
        // the last side on up/down facings (his art is side-only).
        if (f.facing === "left") s.setFlipX(false);
        else if (f.facing === "right") s.setFlipX(true);
        // Amir's authored guitar-swing poses: windup (startup) -> swing
        // (active) -> follow-through (recovery); breathing idle otherwise.
        if (f.attack) {
          const frame = f.attack.phase === "startup" ? 0 : f.attack.phase === "active" ? 1 : 2;
          if (s.anims.isPlaying) s.anims.stop();
          s.setTexture("band_amir_attack", frame);
        } else if (s.anims.getName() !== "amir_idle" || !s.anims.isPlaying) {
          s.play("amir_idle");
        }
      }
      // hurt: hard white impact flash while in hitstun (everyone)
      if (f.state === "hitstun" && !reduced) s.setTintFill(0xffffff);
      else s.clearTint();
      // i-frame blink (skipped under reduced motion); windup telegraph is in fx
      s.setAlpha(f.iframes > 0 && !reduced ? (Math.floor(this.time.now / 60) % 2 ? 0.4 : 1) : 1);
    }

    // emissive glow: enemy auras/eyes pulse with the beat and flare red on windup
    for (const e of getEnemies(this.arena)) {
      const aura = this.auras.get(e.id);
      const eye = this.eyes.get(e.id);
      if (!aura || !eye || e.state === "dead") continue;
      const accent = this.accents.get(e.id) ?? 0xffffff;
      const windup = e.ai?.mode === "windup";
      const enemySprite = this.sprites.get(e.id)!;
      const ery = e.pos.y + HORIZON;
      const headY = ery - enemySprite.displayHeight * 0.55;
      aura
        .setPosition(e.pos.x, ery - 6)
        .setTint(windup ? 0xc22f34 : accent)
        .setAlpha((windup ? 0.75 : 0.3) + (reduced ? 0 : 0.12 * beatWave))
        .setScale((windup ? 1.5 : 1.1) * enemySprite.scaleX);
      eye.setPosition(e.pos.x, headY).setTint(windup ? 0xffd27a : accent).setAlpha(0.7 + (reduced ? 0 : 0.25 * beatWave));
      // hit spark when this enemy's HP drops
      const prev = this.lastEnemyHp.get(e.id) ?? e.hp;
      if (e.hp < prev - 0.01) this.spawnSpark(e.pos.x, ery - 8);
      this.lastEnemyHp.set(e.id, e.hp);
    }

    // fx graphics: crisp telegraph ring (kept alongside the soft glow)
    this.fx.clear();
    for (const e of getEnemies(this.arena)) {
      if (e.ai?.mode === "windup" && e.state !== "dead") this.fx.lineStyle(2, 0xc22f34, 0.9).strokeCircle(e.pos.x, e.pos.y + HORIZON - 6, 15);
    }

    // player: parry shield flash > on-beat flash > active-attack glow arc
    const p = getPlayer(this.arena);
    this.beatGlow.setPosition(p.pos.x, p.pos.y + HORIZON - 4);
    if (p.parryTimer > 0 && !reduced) this.beatGlow.setTint(0xeaf6ff).setScale(1.7).setAlpha(0.75);
    else this.beatGlow.setTint(0x49c6bd).setScale(1.3).setAlpha(this.isOnBeat() && !reduced ? 0.35 : 0.08);
    if (p.attack?.phase === "active") {
      const d = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[p.facing];
      const cx = p.pos.x + d[0] * p.attack.def.reach;
      const cy = p.pos.y + HORIZON + d[1] * p.attack.def.reach;
      this.attackGlow.setPosition(cx, cy).setTint(p.attack.onBeat ? 0xf4d27a : 0xd8ceb6).setScale((p.attack.def.radius / 32) * (p.attack.onBeat ? 1.5 : 1)).setAlpha(p.attack.onBeat ? 1 : 0.7);
    } else {
      this.attackGlow.setAlpha(0);
    }

    this.drawHpBars();
    this.beatPulse.setScale(this.isOnBeat() ? 1.7 : 1).setFillStyle(this.isOnBeat() ? 0xf4d27a : 0x49c6bd);
    this.dmgText.setText(p.damagePct > 0.5 ? `${Math.round(p.damagePct)}%` : "");

    // player plate: HP bar, Focus pips, Groove bar (drawn, not printed)
    const g = this.plate;
    g.clear();
    const px0 = 9;
    const hpY = BASE_HEIGHT - 22;
    const hpW = 78;
    g.fillStyle(0x05060a, 0.9).fillRect(px0 - 1, hpY - 1, hpW + 2, 5);
    g.fillStyle(0x7d1b20, 1).fillRect(px0, hpY, hpW, 3);
    g.fillStyle(0x49c6bd, 1).fillRect(px0, hpY, Math.max(0, Math.round((p.hp / p.maxHp) * hpW)), 3);
    for (let i = 0; i < 5; i++) {
      g.fillStyle(i < this.arena.focus ? 0xf4d27a : 0x2a3138, 1).fillRect(px0 + i * 7, hpY + 7, 5, 3);
    }
    const grW = 40;
    g.fillStyle(0x2a3138, 1).fillRect(px0 + 38, hpY + 7, grW, 3);
    g.fillStyle(0xb98fca, 1).fillRect(px0 + 38, hpY + 7, Math.round((this.arena.groove / 100) * grW), 3);
  }

  /** A fading title card naming the movement (biome) and the foe -- narrative flavor. */
  private showBattleIntro(enemyWave: string[]): void {
    const movement = (this.nodeId && NODE_MOVEMENT[this.nodeId]) || "The Drowned Chorus";
    const foes = [...new Set(enemyWave.map((id) => getEnemy(id).name))].join(" · ");
    const title = this.add
      .text(BASE_WIDTH / 2, 70, movement, { fontFamily: "monospace", fontSize: "16px", color: "#f4efe2", fontStyle: "bold", stroke: "#05060a", strokeThickness: 4 })
      .setOrigin(0.5)
      .setDepth(30);
    const sub = this.add
      .text(BASE_WIDTH / 2, 88, foes, { fontFamily: "monospace", fontSize: "8px", color: "#49c6bd", stroke: "#05060a", strokeThickness: 3 })
      .setOrigin(0.5)
      .setDepth(30);
    this.tweens.add({ targets: [title, sub], alpha: 0, delay: 1400, duration: 900, onComplete: () => { title.destroy(); sub.destroy(); } });
  }

  /** A brief additive impact star where a hit lands (skipped under reduced motion). */
  private spawnSpark(x: number, y: number): void {
    if (GameContext.activeProfile?.settings.reducedMotion) return;
    const s = this.add.image(x, y, "spark").setBlendMode(Phaser.BlendModes.ADD).setDepth(9).setScale(0.4).setTint(0xfff4d0);
    this.tweens.add({ targets: s, scale: 1.3, alpha: 0, angle: 40, duration: 220, onComplete: () => s.destroy() });
  }

  private drawHpBars(): void {
    // Player HP lives on the plate; a boss's HP lives on the top bar; only
    // regular foes keep a small bar hugging the sprite (AAA audit B4).
    this.hpBars.clear();
    const enemies = getEnemies(this.arena);
    for (let i = 0; i < enemies.length; i++) {
      const f = enemies[i];
      if (f.state === "dead") continue;
      if (this.isBoss && i === 0) {
        // top-centre boss bar (frame drawn once in create); bright fill on a
        // near-black trough so the remaining HP always reads
        const bw = 130;
        const bx = BASE_WIDTH / 2 - bw / 2;
        this.hpBars.fillStyle(0x1a0507, 1).fillRect(bx, 18, bw, 4);
        this.hpBars.fillStyle(0xe04434, 1).fillRect(bx, 18, Math.max(0, Math.round((f.hp / f.maxHp) * bw)), 4);
        continue;
      }
      const sprite = this.sprites.get(f.id);
      const w = 16;
      const x = Math.round(f.pos.x - w / 2);
      const y = Math.round(f.pos.y + HORIZON - (sprite ? sprite.displayHeight * 0.78 : 24));
      this.hpBars.fillStyle(0x05060a, 0.8).fillRect(x - 1, y - 1, w + 2, 3);
      this.hpBars.fillStyle(0xc22f34, 1).fillRect(x, y, Math.max(0, Math.round((f.hp / f.maxHp) * w)), 1);
    }
  }

  /** Victory/defeat rewards + campaign progression, mirroring the prior turn-based endBattle so the overworld loop is unchanged. */
  private finishBattle(outcome: "victory" | "defeat"): void {
    this.clock.stop();
    const profile = GameContext.activeProfile!;
    const encounter = getEncounter(this.encounterId);
    const victory = outcome === "victory";
    let newlyUnlockedSkills: string[] = [];

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

    void GameContext.persistActiveProfile().then(() => this.scene.start("ResultsScene"));
  }
}
