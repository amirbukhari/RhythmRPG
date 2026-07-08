import Phaser from "phaser";

/** Start, continue, settings. See PRD §10.6. */
export class MainMenuScene extends Phaser.Scene {
  constructor() {
    super("MainMenuScene");
  }

  create(): void {
    // TODO: Start -> SaveScene, Continue -> MapScene (if save exists), Settings -> SettingsOverlay.
  }
}
