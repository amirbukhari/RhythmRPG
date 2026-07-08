import Phaser from "phaser";

/** XP, relic, and unlock summary after a battle. See PRD §8.5. */
export class ResultsScene extends Phaser.Scene {
  constructor() {
    super("ResultsScene");
  }

  create(): void {
    // TODO: apply victoryRewards, present relic choice, then -> MapScene.
  }
}
