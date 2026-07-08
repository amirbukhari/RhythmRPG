import Phaser from "phaser";

/** Node-based campaign map: battle / elite / camp / boss nodes. See PRD §8.1. */
export class MapScene extends Phaser.Scene {
  constructor() {
    super("MapScene");
  }

  create(): void {
    // TODO: render node graph from campaign progress in save data, launch BattleScene on node select.
  }
}
