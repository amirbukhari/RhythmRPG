import Phaser from "phaser";

/** Save slot create/load/delete against IndexedDB. See PRD §10.7. */
export class SaveScene extends Phaser.Scene {
  constructor() {
    super("SaveScene");
  }

  create(): void {
    // TODO: list slots via SaveManager, wire create/load/delete, then -> CalibrationScene or MapScene.
  }
}
