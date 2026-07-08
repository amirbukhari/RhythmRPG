import Phaser from "phaser";

/**
 * All combat logic and UI. See PRD §8.2–§8.7.
 * Turn structure: intent -> command (untimed) -> performance (audio-clock timed) -> resolution -> next combatant -> round end.
 * Judgment must be computed from TransportClock, never setTimeout/setInterval/requestAnimationFrame. See PRD §10.2.
 */
export class BattleScene extends Phaser.Scene {
  constructor() {
    super("BattleScene");
  }

  create(): void {
    // TODO: load Encounter + Beatmap, drive TurnManager and JudgmentSystem against TransportClock.
  }
}
