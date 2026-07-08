import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { getEncounter, getBeatmap, getHeroClass, getAbility, getBossPhaseConfig, getCampaignNode } from "../data/ContentRegistry";
import type { BossPhase } from "../data/schemas/BossPhaseConfig";
import { createCombat, queueHeroAction, resolveHeroPerformance, type CombatState } from "../systems/combat/CombatController";
import { TransportClock } from "../systems/audio/TransportClock";
import { BeatmapSonifier } from "../systems/audio/BeatmapSonifier";
import { timingTemplateToSeconds } from "../systems/combat/PhraseTiming";
import { positionAtSeconds, nextBarBoundarySeconds, meterAtBar } from "../systems/combat/MeterSequence";
import { upcomingEvents } from "../systems/combat/Forecast";
import { judge, type JudgmentTier } from "../systems/combat/JudgmentSystem";
import { BASE_WIDTH } from "../config/GameConfig";
import type { Beatmap } from "../data/schemas/Beatmap";

/** How long past a step's target time we wait before auto-recording a miss. */
const AUTO_MISS_GRACE_SECONDS = 0.35;

type InputStage = "command" | "select-target" | "count-in" | "awaiting-input" | "ended";

/**
 * All combat logic and UI. See PRD §8.2-§8.7.
 * Turn structure: intent -> command (untimed) -> performance (audio-clock timed) -> resolution -> next combatant -> round end.
 * Judgment is computed from TransportClock, never setTimeout/setInterval/requestAnimationFrame (PRD §10.2).
 */
export class BattleScene extends Phaser.Scene {
  private clock = new TransportClock();
  private sonifier!: BeatmapSonifier;
  private combat!: CombatState;
  private beatmap!: Beatmap;
  private effectiveBpm = 120;
  private calibrationOffsetSeconds = 0;

  private stage: InputStage = "command";
  private activeAbilityIds: string[] = [];
  private timingTargets: number[] = [];
  private capturedTiers: JudgmentTier[] = [];
  private stepIndex = 0;
  private pendingAbilityId: string | null = null;
  private targetableEnemyIds: string[] = [];

  private hpText!: Phaser.GameObjects.Text;
  private enemyText!: Phaser.GameObjects.Text;
  private beatText!: Phaser.GameObjects.Text;
  private promptText!: Phaser.GameObjects.Text;
  private logText!: Phaser.GameObjects.Text;
  private forecastText!: Phaser.GameObjects.Text;
  private forecastExpiresRound: number | null = null;
  private tapKey = " ";
  private captionsEnabled = true;
  private isBossFight = false;
  private lastRenderedBeatsPerBar: number | null = null;
  private lastRenderedDen: number | null = null;

  // Boss multi-phase support (PRD §8.7). phaseStartSeconds is the absolute
  // transport time treated as the *current* beatmap's own bar-1-beat-1 --
  // all meter/position math is relative to it, so a phase change partway
  // through a fight doesn't require the new beatmap to somehow start at
  // transport zero.
  private bossPhases: BossPhase[] = [];
  private currentPhaseIndex = 0;
  private phaseStartSeconds = 0;
  private phaseTransitionScheduled = false;

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
    this.beatmap = beatmap;
    this.isBossFight = encounter.encounterId.startsWith("boss_");
    this.bossPhases = getBossPhaseConfig(encounter.encounterId)?.phases ?? [];
    this.currentPhaseIndex = 0;
    this.effectiveBpm = beatmap.bpm * settings.gameSpeed;
    this.calibrationOffsetSeconds = GameContext.activeProfile.calibrationOffsetMs / 1000;
    this.tapKey = settings.keyBindings.tap ?? " ";
    this.captionsEnabled = settings.captionsEnabled;

    GameContext.analytics.track("battle_started", { encounterId });

    this.hpText = this.add.text(8, 8, "", { fontFamily: "monospace", fontSize: "8px", color: "#ffffff" });
    this.enemyText = this.add.text(8, 60, "", { fontFamily: "monospace", fontSize: "8px", color: "#ff8888" });
    this.beatText = this.add.text(8, 80, "", { fontFamily: "monospace", fontSize: "8px", color: "#88ff88" });
    this.forecastText = this.add.text(8, 92, "", { fontFamily: "monospace", fontSize: "7px", color: "#66ddff", wordWrap: { width: BASE_WIDTH - 16 } });
    this.promptText = this.add
      .text(BASE_WIDTH / 2, 110, "", { fontFamily: "monospace", fontSize: "8px", color: "#ffe066", align: "center", wordWrap: { width: BASE_WIDTH - 16 } })
      .setOrigin(0.5, 0);
    this.logText = this.add.text(8, 150, "", { fontFamily: "monospace", fontSize: "7px", color: "#888888" });

    await this.clock.start(this.effectiveBpm);
    this.phaseStartSeconds = this.clock.currentTime;
    this.sonifier = new BeatmapSonifier(this.clock);
    this.sonifier.setVolume(settings.volumeMusic);
    this.sonifier.start(beatmap, this.effectiveBpm, this.phaseStartSeconds);
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
    this.renderForecast();

    if (this.stage === "awaiting-input") {
      this.checkForAutoMiss();
    }
  }

  /** Transport time relative to the current phase's own bar-1-beat-1. */
  private get elapsedInPhase(): number {
    return this.clock.currentTime - this.phaseStartSeconds;
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
    } else if (this.stage === "select-target") {
      const index = ["1", "2", "3", "4", "5"].indexOf(event.key);
      if (index === -1 || index >= this.targetableEnemyIds.length) return;
      this.beginPerformance(this.pendingAbilityId!, this.targetableEnemyIds[index]);
    } else if (this.stage === "awaiting-input") {
      if (event.key === this.tapKey) this.captureInput();
    }
  }

  /** Ability effects that need an enemy target -- if more than one enemy is alive, the player must pick one. */
  private abilityNeedsEnemyTarget(abilityId: string): boolean {
    return getAbility(abilityId).effects.some((e) => e.type === "damage" || e.type === "debuff" || e.type === "interrupt");
  }

  private selectAbility(abilityId: string): void {
    const heroId = this.activeHeroId;
    if (!heroId) return;

    const aliveEnemies = this.combat.enemies.filter((e) => e.hp > 0);
    if (aliveEnemies.length > 1 && this.abilityNeedsEnemyTarget(abilityId)) {
      this.pendingAbilityId = abilityId;
      this.targetableEnemyIds = aliveEnemies.map((e) => e.instanceId);
      this.stage = "select-target";
      const labels = aliveEnemies.map((e, i) => `${i + 1}: ${e.name} (${e.hp}/${e.maxHp} HP)`).join("  ");
      this.promptText.setText(`${heroId.toUpperCase()}: choose a target\n${labels}`);
      return;
    }

    this.beginPerformance(abilityId);
  }

  private beginPerformance(abilityId: string, targetEnemyId?: string): void {
    const heroId = this.activeHeroId;
    if (!heroId) return;
    try {
      queueHeroAction(this.combat, heroId, abilityId, targetEnemyId ? { targetEnemyId } : {});
    } catch (err) {
      this.promptText.setText(String((err as Error).message));
      this.stage = "command";
      return;
    }
    const ability = getAbility(abilityId);
    GameContext.analytics.track("ability_used", { abilityId, heroId });
    // Count-in and meter lookup are computed relative to the current
    // phase's own origin, then converted back to absolute transport time
    // for the actual judgment targets (see elapsedInPhase docblock).
    const relativePhraseStart = nextBarBoundarySeconds(this.beatmap.meterSequence, this.elapsedInPhase, this.effectiveBpm);
    const phraseStart = this.phaseStartSeconds + relativePhraseStart;
    // A 1-2 bar phrase is interpreted in whatever meter is in effect at its
    // own start bar -- correct for PRD §8.7's boss, where meter changes
    // every few bars but a phrase itself doesn't straddle one mid-flight.
    const phraseStartBar = positionAtSeconds(this.beatmap.meterSequence, relativePhraseStart, this.effectiveBpm).bar;
    const phraseBeatsPerBar = meterAtBar(this.beatmap.meterSequence, phraseStartBar).num;
    this.timingTargets = timingTemplateToSeconds(ability.timingTemplate, phraseStart, this.effectiveBpm, phraseBeatsPerBar);
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
        this.revealForecast();
      }
      resolveHeroPerformance(this.combat, this.capturedTiers);
      this.appendLog();
      this.enterCommandStage();
    }
  }

  /**
   * The actual implementation of healer_sightread's forecastReveal effect
   * (PRD §8.4): a real upcoming-events lane, not just a log line. Stays
   * visible for the same duration as the ability's partyBuff effect.
   */
  private revealForecast(): void {
    const ability = getAbility("healer_sightread");
    const forecastEffect = ability.effects.find((e) => e.type === "forecastReveal");
    const bars = forecastEffect?.bars ?? 2;
    const buffDuration = ability.effects.find((e) => e.type === "partyBuff")?.durationRounds ?? 2;

    const currentBar = positionAtSeconds(this.beatmap.meterSequence, this.elapsedInPhase, this.effectiveBpm).bar;
    const events = upcomingEvents(this.beatmap, currentBar, bars);

    if (events.length === 0) {
      this.forecastText.setText(`SIGHTREAD: next ${bars} bars look clear.`);
    } else {
      const summary = events.map((e) => `bar ${e.bar} ${e.type}${e.payload ? `:${e.payload}` : ""}`).join(", ");
      this.forecastText.setText(`SIGHTREAD (next ${bars} bars): ${summary}`);
    }
    this.forecastExpiresRound = this.combat.round + buffDuration;
  }

  private renderForecast(): void {
    if (this.forecastExpiresRound !== null && this.combat.round > this.forecastExpiresRound) {
      this.forecastText.setText("");
      this.forecastExpiresRound = null;
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
    const pos = positionAtSeconds(this.beatmap.meterSequence, this.elapsedInPhase, this.effectiveBpm);
    const meterChanged = pos.beatsPerBar !== this.lastRenderedBeatsPerBar || pos.den !== this.lastRenderedDen;
    if (meterChanged) {
      // A caption for any in-beatmap meter change (mid_biome_1's 3/4->6/8,
      // or a boss phase's own internal alternation) -- distinct from a full
      // phase transition (a different beatmap entirely), which announces
      // itself in performPhaseTransition.
      if (this.lastRenderedBeatsPerBar !== null) {
        this.combat.log.push({ round: this.combat.round, message: `Meter shifts to ${pos.beatsPerBar}/${pos.den}.` });
        this.appendLog();
      }
      this.lastRenderedBeatsPerBar = pos.beatsPerBar;
      this.lastRenderedDen = pos.den;
    }
    this.beatText.setText(`Round ${this.combat.round}   Bar ${pos.bar}  Beat ${pos.beat}/${pos.beatsPerBar}  (${pos.beatsPerBar}/${pos.den})`);

    if (this.isBossFight) this.checkBossPhaseTransition();
  }

  /**
   * PRD §8.7: the boss's meter changes are driven by its HP fraction
   * crossing each phase's authored threshold. The actual beatmap swap is
   * quantized to the next bar boundary (release gate #3: "on bar boundary
   * without drift"), not applied instantly mid-bar.
   */
  private checkBossPhaseTransition(): void {
    if (this.phaseTransitionScheduled) return;
    const nextPhaseIndex = this.currentPhaseIndex + 1;
    if (nextPhaseIndex >= this.bossPhases.length) return;

    const boss = this.combat.enemies[0];
    if (!boss || boss.maxHp <= 0) return;
    const hpFraction = boss.hp / boss.maxHp;
    if (hpFraction > this.bossPhases[nextPhaseIndex].hpThreshold) return;

    this.phaseTransitionScheduled = true;
    const relativeBoundary = nextBarBoundarySeconds(this.beatmap.meterSequence, this.elapsedInPhase, this.effectiveBpm);
    const transitionTime = this.phaseStartSeconds + relativeBoundary;
    // NOTE: unlike BeatmapSonifier's triggerAttackRelease(note, dur, time),
    // the `time` Tone.Transport.schedule() passes into its callback is
    // AudioContext time, not Transport-position seconds -- it must NOT be
    // used as phaseStartSeconds, which is compared against
    // TransportClock.currentTime (Transport.seconds) everywhere else.
    // Mixing the two clocks was a real bug caught live: it silently broke
    // the second boss phase transition. transitionTime (computed in
    // Transport-seconds) is what performPhaseTransition needs here.
    this.clock.scheduleAt(transitionTime, () => this.performPhaseTransition(nextPhaseIndex, transitionTime));
  }

  private performPhaseTransition(phaseIndex: number, startAtSeconds: number): void {
    const phase = this.bossPhases[phaseIndex];
    const newBeatmap = getBeatmap(phase.trackId);
    const gameSpeed = GameContext.activeProfile?.settings.gameSpeed ?? 1;

    this.currentPhaseIndex = phaseIndex;
    this.beatmap = newBeatmap;
    this.effectiveBpm = newBeatmap.bpm * gameSpeed;
    this.phaseStartSeconds = startAtSeconds;
    this.phaseTransitionScheduled = false;

    this.sonifier.start(newBeatmap, this.effectiveBpm, startAtSeconds);

    GameContext.analytics.track("boss_phase_reached", { phase: phaseIndex + 1, trackId: phase.trackId });
    this.combat.log.push({ round: this.combat.round, message: `The Conductor enters phase ${phaseIndex + 1}.` });
    this.appendLog();
  }

  private endBattle(): void {
    if (this.stage === "ended") return;
    this.stage = "ended";
    this.clock.stop();

    const profile = GameContext.activeProfile!;
    const encounterId = GameContext.pendingEncounterId!;
    const nodeId = GameContext.pendingNodeId;
    const encounter = getEncounter(encounterId);
    const victory = this.combat.outcome === "victory";

    if (victory) {
      profile.campaignProgress.xp += encounter.victoryRewards.xp;
      profile.campaignProgress.currency += encounter.victoryRewards.currency;
      // clearedNodeIds tracks campaign nodes, not encounters -- they're
      // different id spaces (a node references an encounter, not the other
      // way around), so this must key off nodeId, not encounterId.
      if (nodeId) {
        if (!profile.campaignProgress.clearedNodeIds.includes(nodeId)) {
          profile.campaignProgress.clearedNodeIds.push(nodeId);
        }
        const node = getCampaignNode(nodeId);
        if (node.next.length > 0) profile.campaignProgress.currentNodeId = node.next[0];
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
    GameContext.pendingNodeId = null;

    void GameContext.persistActiveProfile().then(() => this.scene.start("ResultsScene"));
  }
}
