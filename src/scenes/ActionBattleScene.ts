import Phaser from "phaser";
import { BASE_HEIGHT, BASE_WIDTH } from "../config/GameConfig";
import { getCampaignNode, getEncounter } from "../data/ContentRegistry";
import { GameContext } from "../state/GameContext";
import { createActionCombat, startAttack, startDash, tickActionCombat, type ActionCombatState, type Vec2 } from "../systems/combat/ActionCombat";
import { TransportClock } from "../systems/audio/TransportClock";

/** v6.0 real-time rhythm-action arena: movement, dash i-frames, frame-data attacks, hitstun/knockback, and on-beat power. */
export class ActionBattleScene extends Phaser.Scene {
  private state!: ActionCombatState;
  private clock = new TransportClock();
  private hero!: Phaser.GameObjects.Sprite;
  private enemies = new Map<string, Phaser.GameObjects.Sprite>();
  private hud!: Phaser.GameObjects.Text;
  private log!: Phaser.GameObjects.Text;
  private keys!: Record<string, Phaser.Input.Keyboard.Key>;

  constructor() { super("ActionBattleScene"); }

  async create(): Promise<void> {
    const encounterId = GameContext.pendingEncounterId;
    const profile = GameContext.activeProfile;
    if (!encounterId || !profile) { this.scene.start("OverworldScene"); return; }
    const encounter = getEncounter(encounterId);
    const isBoss = encounter.encounterId.startsWith("boss_");
    this.add.image(BASE_WIDTH / 2, BASE_HEIGHT / 2, isBoss ? "bg_battle_conductor" : "bg_battle_abyss").setDepth(-10);
    this.add.rectangle(0, 0, BASE_WIDTH, BASE_HEIGHT, 0x061018, 0.28).setOrigin(0, 0).setDepth(-9);
    this.state = createActionCombat(encounter.enemyWave, { calibrationOffsetSeconds: profile.calibrationOffsetMs / 1000, assistMultiplier: profile.settings.assistedTimingWindows ? 1.5 : 1 });
    this.hero = this.add.sprite(this.state.hero.position.x, this.state.hero.position.y, "hero_warrior", 0).setScale(1.35).setDepth(5);
    for (const enemy of this.state.enemies) {
      const key = enemy.name === "the_conductor" ? "enemy_the_conductor" : `enemy_${enemy.name}`;
      const sprite = this.add.sprite(enemy.position.x, enemy.position.y, key, 0).setScale(isBoss ? 2.2 : 1.15).setDepth(isBoss ? 4 : 5).setOrigin(0.5, 1);
      this.enemies.set(enemy.id, sprite);
    }
    this.hud = this.add.text(6, 4, "", { fontFamily: "monospace", fontSize: "8px", color: "#d8ceb6" }).setDepth(20);
    this.log = this.add.text(6, 142, "", { fontFamily: "monospace", fontSize: "7px", color: "#79b855", wordWrap: { width: BASE_WIDTH - 12 } }).setDepth(20);
    this.keys = this.input.keyboard!.addKeys("W,A,S,D,UP,DOWN,LEFT,RIGHT,SPACE,J,K,L,I") as Record<string, Phaser.Input.Keyboard.Key>;
    await this.clock.start(120 * profile.settings.gameSpeed);
    GameContext.analytics.track("battle_started", { encounterId, mode: "action" });
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.clock.stop());
  }

  update(): void {
    if (!this.state) return;
    const input = this.readMove();
    if (Phaser.Input.Keyboard.JustDown(this.keys.SPACE)) startDash(this.state, input.x || input.y ? input : this.facingVector(), this.clock.currentTime);
    if (Phaser.Input.Keyboard.JustDown(this.keys.J)) startAttack(this.state, "light", this.clock.currentTime);
    if (Phaser.Input.Keyboard.JustDown(this.keys.K)) startAttack(this.state, "heavy", this.clock.currentTime);
    if (Phaser.Input.Keyboard.JustDown(this.keys.L)) startAttack(this.state, "special", this.clock.currentTime);
    if (Phaser.Input.Keyboard.JustDown(this.keys.I)) startAttack(this.state, "ultimate", this.clock.currentTime);
    tickActionCombat(this.state, input);
    this.render();
    if (this.state.outcome !== "ongoing") this.endBattle();
  }

  private readMove(): Vec2 { return { x: (this.keys.D.isDown || this.keys.RIGHT.isDown ? 1 : 0) - (this.keys.A.isDown || this.keys.LEFT.isDown ? 1 : 0), y: (this.keys.S.isDown || this.keys.DOWN.isDown ? 1 : 0) - (this.keys.W.isDown || this.keys.UP.isDown ? 1 : 0) }; }
  private facingVector(): Vec2 { return this.state.hero.facing === "left" ? { x: -1, y: 0 } : this.state.hero.facing === "right" ? { x: 1, y: 0 } : this.state.hero.facing === "up" ? { x: 0, y: -1 } : { x: 0, y: 1 }; }

  private render(): void {
    this.hero.setPosition(this.state.hero.position.x, this.state.hero.position.y).setFlipX(this.state.hero.facing === "left").setAlpha(this.state.hero.invulnerableFrames > 0 ? 0.55 : 1);
    for (const enemy of this.state.enemies) this.enemies.get(enemy.id)?.setPosition(enemy.position.x, enemy.position.y).setAlpha(enemy.hitstunFrames > 0 ? 0.7 : 1);
    for (const [id, sprite] of this.enemies) if (!this.state.enemies.some((e) => e.id === id)) { sprite.destroy(); this.enemies.delete(id); }
    this.hud.setText(`ACTION ARENA  HP ${this.state.hero.hp}/${this.state.hero.maxHp}  %${Math.round(this.state.hero.damagePercent)}  Focus ${this.state.hero.focus}  Groove ${this.state.hero.groove}\nWASD/Arrows move  Space dash  J light  K heavy  L special  I ultimate  Beat: ${this.state.lastJudgment ?? "--"}`);
    this.log.setText(this.state.log.slice(-4).join("\n"));
  }

  private endBattle(): void {
    const profile = GameContext.activeProfile!, encounterId = GameContext.pendingEncounterId!, nodeId = GameContext.pendingNodeId, encounter = getEncounter(encounterId), victory = this.state.outcome === "victory";
    const unlockedSkills: string[] = [];
    if (victory) {
      profile.campaignProgress.xp += encounter.victoryRewards.xp; profile.campaignProgress.currency += encounter.victoryRewards.currency;
      if (nodeId && !profile.campaignProgress.clearedNodeIds.includes(nodeId)) profile.campaignProgress.clearedNodeIds.push(nodeId);
      if (nodeId) { const node = getCampaignNode(nodeId); if (node.next.length > 0) profile.campaignProgress.currentNodeId = node.next[0]; if (node.type === "boss") for (const role of ["warrior", "tank", "mage", "healer"]) { const skill = `${role}_tier2`; if (!profile.unlockedSkills.includes(skill)) { profile.unlockedSkills.push(skill); unlockedSkills.push(skill); } } }
      GameContext.analytics.track("encounter_cleared", { encounterId, mode: "action" });
    } else GameContext.analytics.track("encounter_failed", { encounterId, mode: "action" });
    GameContext.lastBattleResult = { outcome: victory ? "victory" : "defeat", encounterId, xp: victory ? encounter.victoryRewards.xp : 0, currency: victory ? encounter.victoryRewards.currency : 0, relicChoices: victory ? (encounter.victoryRewards.relicChoices ?? []).filter((id) => !profile.relicInventory.includes(id)) : [], unlockedSkills };
    GameContext.pendingEncounterId = null; GameContext.returnToNodeId = nodeId; GameContext.pendingNodeId = null;
    void GameContext.persistActiveProfile().then(() => this.scene.start("ResultsScene"));
  }
}
