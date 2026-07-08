import Phaser from "phaser";

/** Loads the asset manifest and verifies browser support. See PRD §10.6. */
export class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  preload(): void {
    // TODO: load asset manifest, verify WebGL/Web Audio support.
  }

  create(): void {
    this.scene.start("AudioGateScene");
  }
}
