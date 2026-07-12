import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { getEncounter, getBeatmap, getEnemy, getCampaignNode } from "../data/ContentRegistry";
import { TransportClock } from "../systems/audio/TransportClock";
import { BeatmapSonifier } from "../systems/audio/BeatmapSonifier";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";
import {
  createArena,
  step,
  player as getPlayer,
  enemies as getEnemies,
  type Arena,
  type FrameInput,
} from "../systems/action/ActionCombat";

const ARENA_W = BASE_WIDTH;
const ARENA_H = 168;
const ENEMY_SCALE: Record<string, number> = { the_conductor: 2.4, elite_wraith: 1.7 };

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
  private hpBars!: Phaser.GameObjects.Graphics;
  private fx!: Phaser.GameObjects.Graphics;
  private beatText!: Phaser.GameObjects.Text;
  private resourceText!: Phaser.GameObjects.Text;
  private beatPulse!: Phaser.GameObjects.Arc;

  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private keys!: Record<"W" | "A" | "S" | "D" | "J" | "K" | "SHIFT" | "SPACE", Phaser.Input.Keyboard.Key>;

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

    // backdrop
    this.add.image(BASE_WIDTH / 2, BASE_HEIGHT / 2, this.isBoss ? "bg_battle_conductor" : "bg_battle_abyss").setDepth(-10);

    // build the sim from the encounter's enemy wave
    const enemyHps = encounter.enemyWave.map((id) => getEnemy(id).maxHp);
    this.arena = createArena(ARENA_W, ARENA_H, enemyHps);

    // player sprite (the party leader)
    const p = getPlayer(this.arena);
    const pSprite = this.add.sprite(p.pos.x, p.pos.y, "hero_warrior", 0).setOrigin(0.5, 0.8).setScale(1.3).setDepth(5);
    this.sprites.set(p.id, pSprite);

    // enemy sprites, mapped 1:1 with the sim's enemy fighters
    getEnemies(this.arena).forEach((e, i) => {
      const enemyId = encounter.enemyWave[i];
      const scale = ENEMY_SCALE[enemyId] ?? 1.25;
      const s = this.add.sprite(e.pos.x, e.pos.y, `enemy_${enemyId}`, 0).setOrigin(0.5, 0.85).setScale(scale).setDepth(4);
      this.sprites.set(e.id, s);
    });

    this.hpBars = this.add.graphics().setDepth(15);
    this.fx = this.add.graphics().setDepth(6);

    // HUD
    this.add.nineslice(-6, -6, this.isBoss ? "ui_panel_boss" : "ui_panel", undefined, BASE_WIDTH + 12, 18, 5, 5, 5, 5).setOrigin(0, 0).setDepth(20);
    this.beatText = this.add.text(6, 3, "", { fontFamily: "monospace", fontSize: "8px", color: "#79b855" }).setDepth(21);
    this.beatPulse = this.add.circle(BASE_WIDTH - 12, 7, 3, 0x49c6bd).setDepth(21);
    this.resourceText = this.add
      .text(6, BASE_HEIGHT - 10, "", { fontFamily: "monospace", fontSize: "7px", color: "#d8ceb6", stroke: "#05060a", strokeThickness: 3 })
      .setDepth(21);
    this.add
      .text(BASE_WIDTH - 6, BASE_HEIGHT - 10, "WASD move  J light  K heavy  Shift dash", {
        fontFamily: "monospace",
        fontSize: "7px",
        color: "#877d70",
        stroke: "#05060a",
        strokeThickness: 3,
      })
      .setOrigin(1, 0.5)
      .setDepth(21);

    // Wire input BEFORE the async clock.start() below: create() is async and
    // the scene reports active (and its update() loop starts) the moment it's
    // added, so a frame running during `await` must not touch undefined keys.
    const kb = this.input.keyboard!;
    this.cursors = kb.createCursorKeys();
    this.keys = kb.addKeys("W,A,S,D,J,K,SHIFT,SPACE") as ActionBattleScene["keys"];

    // audio clock + audible beat
    await this.clock.start(bpm);
    this.sonifier = new BeatmapSonifier(this.clock);
    this.sonifier.setVolume(settings.volumeMusic);
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
    const dash = JD(k.SHIFT);
    // on-beat is evaluated at the instant of an action press
    const onBeat = (light || heavy || dash) && this.isOnBeat();
    return { move, dash, light, heavy, onBeat };
  }

  private render(): void {
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    for (const f of this.arena.fighters) {
      const s = this.sprites.get(f.id);
      if (!s) continue;
      if (f.state === "dead") {
        s.setAlpha(0.12);
        continue;
      }
      s.setPosition(Math.round(f.pos.x), Math.round(f.pos.y));
      s.setDepth(4 + f.pos.y / 100);
      if (f.team === "player") s.setFlipX(f.facing === "left");
      // i-frame blink (skipped under reduced motion); windup telegraph is in fx
      s.setAlpha(f.iframes > 0 && !reduced ? (Math.floor(this.time.now / 60) % 2 ? 0.4 : 1) : 1);
    }

    // fx: enemy telegraph rings + player active hitbox arc
    this.fx.clear();
    for (const e of getEnemies(this.arena)) {
      if (e.ai?.mode === "windup" && e.state !== "dead") {
        this.fx.lineStyle(2, 0xc22f34, 0.9).strokeCircle(e.pos.x, e.pos.y - 6, 14);
      }
    }
    const p = getPlayer(this.arena);
    if (p.attack?.phase === "active") {
      const d = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[p.facing];
      const cx = p.pos.x + d[0] * p.attack.def.reach;
      const cy = p.pos.y + d[1] * p.attack.def.reach;
      const glow = p.attack.onBeat ? 0xf4d27a : 0xd8ceb6;
      this.fx.fillStyle(glow, 0.5).fillCircle(cx, cy, p.attack.def.radius);
    }

    this.drawHpBars();

    const beat = Math.floor((this.clock.currentTime / this.beatSeconds) % 4) + 1;
    this.beatText.setText(`Beat ${beat}/4`);
    this.beatPulse.setScale(this.isOnBeat() ? 1.7 : 1).setFillStyle(this.isOnBeat() ? 0xf4d27a : 0x49c6bd);
    this.resourceText.setText(`HP ${Math.ceil(p.hp)}/${p.maxHp}   DMG ${Math.round(p.damagePct)}%   Groove ${Math.round(this.arena.groove)}/100`);
  }

  private drawHpBars(): void {
    this.hpBars.clear();
    for (const f of this.arena.fighters) {
      if (f.state === "dead") continue;
      const w = f.team === "player" ? 24 : 20;
      const x = Math.round(f.pos.x - w / 2);
      const y = Math.round(f.pos.y - (f.team === "player" ? 22 : 30));
      this.hpBars.fillStyle(0x05060a, 0.8).fillRect(x - 1, y - 1, w + 2, 4);
      this.hpBars.fillStyle(0x7d1b20, 1).fillRect(x, y, w, 2);
      this.hpBars.fillStyle(f.team === "player" ? 0x49c6bd : 0xc22f34, 1).fillRect(x, y, Math.max(0, Math.round((f.hp / f.maxHp) * w)), 2);
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
