import Phaser from "phaser";

/** AV sync test and global timing offset save. See PRD §9.3, §10.3. */
export class CalibrationScene extends Phaser.Scene {
  constructor() {
    super("CalibrationScene");
  }

  create(): void {
    // TODO: run AV calibration test, persist offset via SaveManager, then -> MapScene.
  }
}
