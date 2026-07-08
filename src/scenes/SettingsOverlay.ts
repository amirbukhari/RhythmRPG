import Phaser from "phaser";

/**
 * Always-available settings modal: remapping, volume sliders, captions,
 * reduced motion, photosensitivity-safe mode, game speed, assisted timing
 * windows, practice mode toggle. Mandatory day-one per PRD §9.3.
 */
export class SettingsOverlay extends Phaser.Scene {
  constructor() {
    super("SettingsOverlay");
  }

  create(): void {
    // TODO: render accessibility + AV settings, persist via SaveManager/AccessibilitySettings.
  }
}
