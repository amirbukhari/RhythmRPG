import Phaser from "phaser";

/**
 * Mandatory "Press Any Key to Start Audio" gate.
 * Creates/resumes the AudioContext on user gesture per PRD §10.4 — must run
 * before any menu is interactive, and must never attempt autoplay.
 */
export class AudioGateScene extends Phaser.Scene {
  constructor() {
    super("AudioGateScene");
  }

  create(): void {
    // TODO: render "Press Any Key to Start Audio" prompt.
    // TODO: on first input, create/resume Tone.js AudioContext, then:
    // this.scene.start("MainMenuScene");
  }
}
