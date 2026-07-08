import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { getEncounter, getBeatmap, getHeroClass, getAbility } from "../data/ContentRegistry";
import { createCombat, queueHeroAction, resolveHeroPerformance, type CombatState } from "../systems/combat/CombatController";
import { TransportClock } from "../systems/audio/TransportClock";
import { BeatmapSonifier } from "../systems/audio/BeatmapSonifier";
import { nextBarBoundary, timingTemplateToSeconds } from "../systems/combat/PhraseTiming";
import { judge, type JudgmentTier } from "../systems/combat/JudgmentSystem";
import { BASE_WIDTH } from "../config/GameConfig";

/** How long past a step's target time we wait before auto-recording a miss. */
const AUTO_MISS_GRACE_SECONDS = 0.35;

type InputStage = "command" | "count-in" | "awaiting-input" | "ended";

/**
 * All combat logic and UI. See PRD §8.2-§8.7.
 * Turn structure: intent -> command (untimed) -> performance (audio-clock timed) -> resolution -> next combatant -> round end.
 * Judgment is computed from TransportClock, never setTimeout/setInterval/requestAnimationFrame (PRD §10.2).
 */
export class BattleScene extends Phaser.Scene {
  private clock = new TransportClock();
  private sonifier!: BeatmapSonifier;
  private combat!: CombatState;
  private beatsPerBar = 4;
  private effectiveBpm = 120;
  private calibrationOffsetSeconds = 0;

  private stage: InputStage = "command";
  private activeAbilityIds: string[] = [];
  private timingTargets: number[] = [];
  private capturedTiers: JudgmentTier[] = [];
  private stepIndex = 0;
  private pendingAbilityId: string | null = null;

  private hpText!: Phaser.GameObjects.Text;
  private enemyText!: Phaser.GameObjects.Text;
  private beatText!: Phaser.GameObjects.Text;
  private promptText!: Phaser.GameObjects.Text;
  private logText!: Phaser.GameObjects.Text;
  private tapKey = " ";
  private captionsEnabled = true;

  constructor() {
    super("BattleScene");
  }

  async create(): Promise<void> {
    const encounterId = GameContext.pendingEncounterId;
    if (!encounterId || !GameContext.activeProfile) {
      this.scene.start("MapScene");
      return;
    }

    const encounter = getEncounter(encounterId);
    const beatmap = getBeatmap(encounter.trackId);
    const heroes = ["warrior", "tank", "mage", "healer"].map((id) => getHeroClass(id));

    const settings = GameContext.activeProfile.settings;
    this.combat = createCombat(heroes, encounter, { practiceMode: settings.practiceMode });
    this.beatsPerBar = beatmap.meterSequence[0]?.num ?? 4;
    this.effectiveBpm = beatmap.bpm * settings.gameSpeed;
    this.calibrationOffsetSeconds = GameContext.activeProfile.calibrationOffsetMs / 1000;
    this.tapKey = settings.keyBindings.tap ?? " ";
    this.captionsEnabled = settings.captionsEnabled;

    GameContext.analytics.track("battle_started", { encounterId });

    this.hpText = this.add.text(8, 8, "", { fontFamily: "monospace", fontSize: "8px", color: "#ffffff" });
    this.enemyText = this.add.text(8, 60, "", { fontFamily: "monospace", fontSize: "8px", color: "#ff8888" });
    this.beatText = this.add.text(8, 80, "", { fontFamily: "monospace", fontSize: "8px", color: "#88ff88" });
    this.promptText = this.add
      .text(BASE_WIDTH / 2, 110, "", { fontFamily: "monospace", fontSize: "8px", color: "#ffe066", align: "center", wordWrap: { width: BASE_WIDTH - 16 } })
      .setOrigin(0.5, 0);
    this.logText = this.add.text(8, 150, "", { fontFamily: "monospace", fontSize: "7px", color: "#888888" });

    await this.clock.start(this.effectiveBpm);
    this.sonifier = new BeatmapSonifier(this.clock);
    this.sonifier.setVolume(settings.volumeMusic);
    this.sonifier.start(beatmap, this.effectiveBpm);
    this.input.keyboard?.on("keydown", (event: KeyboardEvent) => this.onKeyDown(event));

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      this.sonifier.dispose();
      this.clock.stop();
    });

    this.appendLog();
    this.enterCommandStage();
  }

  update(): void {
    if (!this.combat) return;
    this.renderHeroes();
    this.renderEnemies();
    this.renderBeat();

    if (this.stage === "awaiting-input") {
      this.checkForAutoMiss();
    }
  }

  private get activeHeroId(): string | undefined {
    return this.combat.heroTurnQueue[0];
  }

  private enterCommandStage(): void {
    if (this.combat.outcome !== "ongoing") {
      this.endBattle();
      return;
    }
    const heroId = this.activeHeroId;
    if (!heroId) return; // enemy resolution already advanced the round internally
    this.stage = "command";
    this.activeAbilityIds = getHeroClass(heroId).abilityIds;
    const labels = this.activeAbilityIds.map((id, i) => `${i + 1}: ${getAbility(id).abilityId} (${getAbility(id).focusCost}f)`).join("  ");
    this.promptText.setText(`${heroId.toUpperCase()}'s turn — choose an ability\n${labels}`);
  }

  private onKeyDown(event: KeyboardEvent): void {
    if (this.stage === "command") {
      const index = ["1", "2", "3"].indexOf(event.key);
      if (index === -1 || index >= this.activeAbilityIds.length) return;
      this.selectAbility(this.activeAbilityIds[index]);
    } else if (this.stage === "awaiting-input") {
      if (event.key === this.tapKey) this.captureInput();
    }
  }

  private selectAbility(abilityId: string): void {
    const heroId = this.activeHeroId;
    if (!heroId) return;
    try {
      queueHeroAction(this.combat, heroId, abilityId);
    } catch (err) {
      this.promptText.setText(String((err as Error).message));
      return;
    }
    const ability = getAbility(abilityId);
    GameContext.analytics.track("ability_used", { abilityId, heroId });
    const phraseStart = nextBarBoundary(this.clock.currentTime, this.effectiveBpm, this.beatsPerBar);
    this.timingTargets = timingTemplateToSeconds(ability.timingTemplate, phraseStart, this.effectiveBpm, this.beatsPerBar);
    this.capturedTiers = [];
    this.stepIndex = 0;
    this.pendingAbilityId = abilityId;
    this.stage = "awaiting-input";
    const keyLabel = this.tapKey === " " ? "SPACE" : this.tapKey.toUpperCase();
    this.promptText.setText(`${heroId.toUpperCase()}: ${ability.abilityId}\nPress ${keyLabel} on each beat (${ability.inputPattern.length} steps)`);
  }

  private captureInput(): void {
    if (this.stepIndex >= this.timingTargets.length) return;
    const measuredTime = this.clock.currentTime - this.calibrationOffsetSeconds;
    const target = this.timingTargets[this.stepIndex];
    const deltaMs = (measuredTime - target) * 1000;
    const tier = judge(deltaMs, { assistMultiplier: GameContext.activeProfile?.settings.assistedTimingWindows ? 1.5 : 1 });
    this.recordTier(tier);
  }

  private checkForAutoMiss(): void {
    if (this.stepIndex >= this.timingTargets.length) return;
    if (this.clock.currentTime > this.timingTargets[this.stepIndex] + AUTO_MISS_GRACE_SECONDS) {
      this.recordTier("miss");
    }
  }

  private recordTier(tier: JudgmentTier): void {
    this.capturedTiers.push(tier);
    this.stepIndex += 1;
    if (tier === "perfect") GameContext.analytics.track("judgment_perfect");
    if (tier === "miss") GameContext.analytics.track("judgment_miss");

    if (this.stepIndex >= this.timingTargets.length) {
      const hasMiss = this.capturedTiers.includes("miss");
      if (this.pendingAbilityId === "healer_sightread" && !hasMiss) {
        GameContext.analytics.track("sightread_used");
      }
      resolveHeroPerformance(this.combat, this.capturedTiers);
      this.appendLog();
      this.enterCommandStage();
    }
  }

  private appendLog(): void {
    // PRD §9.3: captions must be able to convey musically meaningful events
    // without sound; this log is that channel, so it's the one thing gated
    // on captionsEnabled rather than always shown.
    if (!this.captionsEnabled) {
      this.logText.setText("");
      return;
    }
    const lines = this.combat.log.slice(-4).map((e) => e.message);
    this.logText.setText(lines.join("\n"));
  }

  private renderHeroes(): void {
    const lines = this.combat.heroes.map((h) => {
      const marker = h.heroId === this.activeHeroId && this.stage !== "ended" ? "> " : "  ";
      const dead = h.hp <= 0 ? " [DOWN]" : "";
      return `${marker}${h.heroId.padEnd(8)} HP ${h.hp}/${h.maxHp}  Focus ${h.focus}/${h.maxFocus}${dead}`;
    });
    lines.push(`Groove: ${this.combat.groove}/100 (streak ${this.combat.grooveStreak})`);
    this.hpText.setText(lines.join("\n"));
  }

  private renderEnemies(): void {
    const lines = this.combat.enemies.map((e) => `${e.name} HP ${e.hp}/${e.maxHp}  Intent: ${e.currentIntent?.telegraph ?? "-"}`);
    this.enemyText.setText(lines.join("\n"));
  }

  private renderBeat(): void {
    const secondsPerBeat = 60 / this.effectiveBpm;
    const barLength = secondsPerBeat * this.beatsPerBar;
    const t = Math.max(0, this.clock.currentTime);
    const bar = Math.floor(t / barLength) + 1;
    const beat = Math.floor((t % barLength) / secondsPerBeat) + 1;
    this.beatText.setText(`Round ${this.combat.round}   Bar ${bar}  Beat ${beat}/${this.beatsPerBar}`);
  }

  private endBattle(): void {
    if (this.stage === "ended") return;
    this.stage = "ended";
    this.clock.stop();

    const profile = GameContext.activeProfile!;
    const encounterId = GameContext.pendingEncounterId!;
    const encounter = getEncounter(encounterId);
    const victory = this.combat.outcome === "victory";

    if (victory) {
      profile.campaignProgress.xp += encounter.victoryRewards.xp;
      profile.campaignProgress.currency += encounter.victoryRewards.currency;
      if (!profile.campaignProgress.clearedNodeIds.includes(encounterId)) {
        profile.campaignProgress.clearedNodeIds.push(encounterId);
      }
      GameContext.analytics.track("encounter_cleared", { encounterId });
    } else {
      GameContext.analytics.track("encounter_failed", { encounterId });
    }

    GameContext.lastBattleResult = {
      outcome: victory ? "victory" : "defeat",
      encounterId,
      xp: victory ? encounter.victoryRewards.xp : 0,
      currency: victory ? encounter.victoryRewards.currency : 0,
      relicChoices: victory ? encounter.victoryRewards.relicChoices ?? [] : [],
    };
    GameContext.pendingEncounterId = null;

    void GameContext.persistActiveProfile().then(() => this.scene.start("ResultsScene"));
  }
}
