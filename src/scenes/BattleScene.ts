import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { getEncounter, getBeatmap, getHeroClass, getAbility, getBossPhaseConfig, getCampaignNode } from "../data/ContentRegistry";
import type { BossPhase } from "../data/schemas/BossPhaseConfig";
import { createCombat, queueHeroAction, resolveHeroPerformance, heroTimingWindowMultiplier, type CombatState } from "../systems/combat/CombatController";
import { TransportClock } from "../systems/audio/TransportClock";
import { BeatmapSonifier } from "../systems/audio/BeatmapSonifier";
import { timingTemplateToSeconds } from "../systems/combat/PhraseTiming";
import { positionAtSeconds, nextBarBoundarySeconds, meterAtBar } from "../systems/combat/MeterSequence";
import { upcomingEvents } from "../systems/combat/Forecast";
import { applyRelics } from "../systems/progression/Relics";
import { judge, type JudgmentTier } from "../systems/combat/JudgmentSystem";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";
import type { Beatmap } from "../data/schemas/Beatmap";
import type { HeroRole } from "../data/schemas/Ability";

/** How long past a step's target time we wait before auto-recording a miss. */
const AUTO_MISS_GRACE_SECONDS = 0.35;

/**
 * Only one character's placeholder art exists (PRD §11.4/§20.2) -- the same
 * sprite stands in for all four heroes, tinted per role for visual
 * distinction, until real per-hero art exists. Displayed at the PRD §11.1
 * spec size (48x48) even though the art content itself is placeholder.
 */
const ROLE_TINTS: Record<HeroRole, number> = {
  warrior: 0xff6666,
  tank: 0x6699ff,
  mage: 0xcc88ff,
  healer: 0x77ff99,
};

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

  private heroSprites: Phaser.GameObjects.Sprite[] = [];
  private heroSpriteBaseScale = 1.3; // heroes are 20x24; scaled up for battle presence
  private enemySprites: Phaser.GameObjects.Sprite[] = [];
  private enemyLabels: Phaser.GameObjects.Text[] = [];
  private caustics: Phaser.GameObjects.TileSprite | null = null;
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
      this.scene.start("OverworldScene");
      return;
    }

    const encounter = getEncounter(encounterId);
    const beatmap = getBeatmap(encounter.trackId);
    const heroes = ["warrior", "tank", "mage", "healer"].map((id) => getHeroClass(id));

    const settings = GameContext.activeProfile.settings;
    this.combat = createCombat(heroes, encounter, { practiceMode: settings.practiceMode });
    applyRelics(this.combat, GameContext.activeProfile.relicInventory);
    this.beatmap = beatmap;
    this.isBossFight = encounter.encounterId.startsWith("boss_");
    this.bossPhases = getBossPhaseConfig(encounter.encounterId)?.phases ?? [];
    this.currentPhaseIndex = 0;
    this.effectiveBpm = beatmap.bpm * settings.gameSpeed;
    this.calibrationOffsetSeconds = GameContext.activeProfile.calibrationOffsetMs / 1000;
    this.tapKey = settings.keyBindings.tap ?? " ";
    this.captionsEnabled = settings.captionsEnabled;

    GameContext.analytics.track("battle_started", { encounterId });

    this.buildBattlefield();

    // --- HUD: top beat strip + bottom command panel over the scene ---------
    this.add.rectangle(0, 0, BASE_WIDTH, 13, 0x05060a, 0.7).setOrigin(0, 0).setDepth(20);
    this.add.rectangle(0, 124, BASE_WIDTH, BASE_HEIGHT - 124, 0x05060a, 0.82).setOrigin(0, 0).setDepth(20);
    this.add.rectangle(0, 123, BASE_WIDTH, 1, 0x8a52a0, 0.8).setOrigin(0, 0).setDepth(20); // amethyst divider

    this.beatText = this.add.text(6, 3, "", { fontFamily: "monospace", fontSize: "8px", color: "#79b855" }).setDepth(21);
    this.forecastText = this.add
      .text(6, 15, "", { fontFamily: "monospace", fontSize: "7px", color: "#49c6bd", wordWrap: { width: BASE_WIDTH - 12 } })
      .setDepth(6);
    this.hpText = this.add.text(6, 128, "", { fontFamily: "monospace", fontSize: "7px", color: "#d8ceb6" }).setDepth(21);
    this.promptText = this.add
      .text(150, 128, "", { fontFamily: "monospace", fontSize: "7px", color: "#f0a648", wordWrap: { width: BASE_WIDTH - 156 } })
      .setDepth(21);
    this.logText = this.add.text(150, 170, "", { fontFamily: "monospace", fontSize: "7px", color: "#877d70", wordWrap: { width: BASE_WIDTH - 156 } }).setDepth(21);
    // enemyText is kept as the aggregate intent readout but drawn off-screen;
    // per-enemy labels above each sprite are the visible version now.
    this.enemyText = this.add.text(0, -50, "", { fontFamily: "monospace", fontSize: "7px", color: "#c22f34" });

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

  /**
   * Draws the scene the combat plays out over: a painted backdrop (the boss
   * gets its clock-lined variant), the party standing lower-left facing the
   * foe, and the enemy wave on the floor to the right -- each with a soft
   * ground shadow and idle motion (party breathe-bob, enemy 2-frame idle).
   */
  private buildBattlefield(): void {
    const bgKey = this.isBossFight ? "bg_battle_conductor" : "bg_battle_abyss";
    this.add.image(BASE_WIDTH / 2, BASE_HEIGHT / 2, bgKey).setDepth(-10);

    // Slow underwater caustic shimmer over the water region (scrolled in update).
    this.caustics = this.add
      .tileSprite(0, 0, BASE_WIDTH, 118, "caustics")
      .setOrigin(0, 0)
      .setDepth(-9)
      .setAlpha(this.getReducedMotion() ? 0.18 : 0.4);

    // A few motes drifting up through the water for life.
    if (!this.getReducedMotion()) {
      for (let i = 0; i < 10; i++) {
        const mote = this.add.circle(Phaser.Math.Between(10, BASE_WIDTH - 10), Phaser.Math.Between(20, 110), 1, 0x9fe8e0, 0.6).setDepth(-8);
        this.tweens.add({
          targets: mote,
          y: mote.y - Phaser.Math.Between(24, 60),
          alpha: 0,
          duration: Phaser.Math.Between(3000, 6000),
          repeat: -1,
          delay: i * 300,
        });
      }
    }

    const FLOOR_Y = 116;
    // A receding diagonal so all four heroes are visible, warrior nearest.
    const heroHomes = [
      { x: 30, y: 134 },
      { x: 54, y: 127 },
      { x: 78, y: 120 },
      { x: 102, y: 113 },
    ];
    this.heroSprites = this.combat.heroes.map((hero, i) => {
      const home = heroHomes[i] ?? { x: 40 + i * 14, y: 120 };
      this.addShadow(home.x, home.y, 8, ROLE_TINTS[hero.role], 0.3);
      const sprite = this.add.sprite(home.x, home.y, `hero_${hero.classId}`, 0);
      sprite.setOrigin(0.5, 1).setScale(this.heroSpriteBaseScale).setDepth(2 + i);
      this.tweens.add({ targets: sprite, y: home.y - 1, duration: 900 + i * 90, yoyo: true, repeat: -1, ease: "Sine.inOut" });
      return sprite;
    });

    const n = this.combat.enemies.length;
    const spacing = 52;
    const groupCx = 232;
    this.enemySprites = [];
    this.enemyLabels = [];
    this.combat.enemies.forEach((enemy, i) => {
      const x = Math.round(groupCx + (i - (n - 1) / 2) * spacing);
      this.addShadow(x, FLOOR_Y, 15, 0x000000, 0.38);
      const key = `enemy_${enemy.enemyId}`;
      const animKey = `idle_${enemy.enemyId}`;
      if (!this.anims.exists(animKey)) {
        this.anims.create({ key: animKey, frames: this.anims.generateFrameNumbers(key, { start: 0, end: 1 }), frameRate: 1.6, repeat: -1 });
      }
      const sprite = this.add.sprite(x, FLOOR_Y + 2, key, 0).setOrigin(0.5, 1).setDepth(3);
      sprite.play(animKey);
      this.enemySprites.push(sprite);
      const label = this.add
        .text(x, FLOOR_Y - 48, "", {
          fontFamily: "monospace",
          fontSize: "7px",
          color: "#f4efe2",
          align: "center",
          stroke: "#05060a",
          strokeThickness: 3,
        })
        .setOrigin(0.5, 1)
        .setDepth(6);
      this.enemyLabels.push(label);
    });
  }

  private addShadow(x: number, y: number, rx: number, color: number, alpha: number): void {
    this.add.ellipse(x, y, rx * 2, rx, color, alpha).setDepth(1);
  }

  private getReducedMotion(): boolean {
    const s = GameContext.activeProfile?.settings;
    return Boolean(s?.reducedMotion || s?.photosensitivitySafeMode);
  }

  update(): void {
    if (!this.combat) return;
    if (this.caustics && !this.getReducedMotion()) {
      this.caustics.tilePositionX += 0.06;
      this.caustics.tilePositionY -= 0.1;
    }
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
    // Base kit (PRD §8.4) plus the tier-2 unlock ability once the boss that
    // grants it has been cleared (PRD §8.5, GameContext.activeProfile.unlockedSkills),
    // plus the role's Groove-spending ultimate (§8.5) -- always listed, since
    // its gate is the shared Groove meter, not a persistent unlock.
    const tier2Id = `${heroId}_tier2`;
    const unlocked = GameContext.activeProfile?.unlockedSkills.includes(tier2Id) ?? false;
    this.activeAbilityIds = [...getHeroClass(heroId).abilityIds, ...(unlocked ? [tier2Id] : []), `${heroId}_ultimate`];
    const labels = this.activeAbilityIds
      .map((id, i) => {
        const ability = getAbility(id);
        const cost = ability.grooveCost ? `${ability.grooveCost}g` : `${ability.focusCost}f`;
        return `${i + 1}: ${ability.abilityId} (${cost})`;
      })
      .join("  ");
    this.promptText.setText(`${heroId.toUpperCase()}'s turn — choose an ability\n${labels}`);
  }

  private onKeyDown(event: KeyboardEvent): void {
    if (this.stage === "command") {
      const index = ["1", "2", "3", "4", "5"].indexOf(event.key);
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
    // Accessibility assist and any active "accuracy" buff (e.g. Sightread's
    // party buff) both widen the windows -- multiplicative, both real.
    const assist = GameContext.activeProfile?.settings.assistedTimingWindows ? 1.5 : 1;
    const buff = this.combat.pendingAction ? heroTimingWindowMultiplier(this.combat, this.combat.pendingAction.heroId) : 1;
    const tier = judge(deltaMs, { assistMultiplier: assist * buff });
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
      const marker = h.heroId === this.activeHeroId && this.stage !== "ended" ? ">" : " ";
      const name = h.heroId.charAt(0).toUpperCase() + h.heroId.slice(1);
      const dead = h.hp <= 0 ? " DOWN" : "";
      return `${marker}${name.padEnd(8)} ${h.hp}/${h.maxHp}  F${h.focus}/${h.maxFocus}${dead}`;
    });
    lines.push(`Groove ${this.combat.groove}/100  streak ${this.combat.grooveStreak}`);
    this.hpText.setText(lines.join("\n"));

    this.combat.heroes.forEach((hero, i) => {
      const sprite = this.heroSprites[i];
      if (!sprite) return;
      const isActive = hero.heroId === this.activeHeroId && this.stage !== "ended";
      sprite.setAlpha(hero.hp <= 0 ? 0.25 : 1);
      sprite.setScale(this.heroSpriteBaseScale * (isActive ? 1.18 : 1));
      // dim/cool the inactive heroes so the acting one reads as "up".
      if (isActive || hero.hp <= 0) sprite.clearTint();
      else sprite.setTint(0x9aa0b0);
    });
  }

  private renderEnemies(): void {
    const lines = this.combat.enemies.map((e) => `${e.name} HP ${e.hp}/${e.maxHp}  Intent: ${e.currentIntent?.telegraph ?? "-"}`);
    this.enemyText.setText(lines.join("\n"));

    this.combat.enemies.forEach((enemy, i) => {
      const sprite = this.enemySprites[i];
      const label = this.enemyLabels[i];
      if (sprite) {
        const down = enemy.hp <= 0;
        sprite.setAlpha(down ? 0.12 : 1);
        if (down && sprite.anims.isPlaying) sprite.anims.stop();
      }
      if (label) {
        if (enemy.hp <= 0) {
          label.setText("");
        } else {
          // A single foe (boss) shows its name; a wave stays compact so the
          // labels don't collide -- the sprite already identifies each one.
          const short = (enemy.currentIntent?.telegraph ?? "-").split("_").slice(-1)[0];
          const nameLine = this.combat.enemies.length === 1 ? `${enemy.name}\n` : "";
          label.setText(`${nameLine}${enemy.hp}/${enemy.maxHp}\n${short}`);
        }
      }
    });
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

    let newlyUnlockedSkills: string[] = [];

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

        // PRD §8.5: "each hero unlocks one new skill after each biome boss."
        // The v1 kit table (PRD §8.4) only authors 3 abilities per role with
        // no tier-2 ability content yet, so this records the *unlock
        // trigger and persistence* honestly -- a real, working mechanism --
        // without inventing unauthorized new ability content to attach it
        // to. See PRD §20 for the content-authoring follow-up.
        if (node.type === "boss") {
          for (const hero of this.combat.heroes) {
            const skillId = `${hero.classId}_tier2`;
            if (!profile.unlockedSkills.includes(skillId)) {
              profile.unlockedSkills.push(skillId);
              newlyUnlockedSkills.push(skillId);
            }
          }
        }
      }
      GameContext.analytics.track("encounter_cleared", { encounterId });
    } else {
      GameContext.analytics.track("encounter_failed", { encounterId });
    }

    // Don't re-offer a relic the party already has (PRD §8.5: one relic slot per hero).
    const relicChoices = victory
      ? (encounter.victoryRewards.relicChoices ?? []).filter((id) => !profile.relicInventory.includes(id))
      : [];

    GameContext.lastBattleResult = {
      outcome: victory ? "victory" : "defeat",
      encounterId,
      xp: victory ? encounter.victoryRewards.xp : 0,
      currency: victory ? encounter.victoryRewards.currency : 0,
      relicChoices,
      unlockedSkills: newlyUnlockedSkills,
    };
    GameContext.pendingEncounterId = null;
    GameContext.returnToNodeId = nodeId; // survives the pending-field clears so the overworld can respawn the player here
    GameContext.pendingNodeId = null;

    void GameContext.persistActiveProfile().then(() => this.scene.start("ResultsScene"));
  }
}
