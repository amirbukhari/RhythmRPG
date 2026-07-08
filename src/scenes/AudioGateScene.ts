import Phaser from "phaser";
import * as Tone from "tone";
import { GameContext } from "../state/GameContext";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";

/**
 * Mandatory "Press Any Key to Start Audio" gate.
 * Creates/resumes the AudioContext on user gesture per PRD §10.4 — must run
 * before any menu is interactive, and must never attempt autoplay.
 */
export class AudioGateScene extends Phaser.Scene {
  private starting = false;

  constructor() {
    super("AudioGateScene");
  }

  create(): void {
    this.add
      .text(BASE_WIDTH / 2, BASE_HEIGHT / 2, "PRESS ANY KEY OR CLICK TO CONTINUE", {
        fontFamily: "monospace",
        fontSize: "10px",
        color: "#ffffff",
        align: "center",
        wordWrap: { width: BASE_WIDTH - 20 },
      })
      .setOrigin(0.5);

    this.input.keyboard?.once("keydown", () => this.startAudio());
    this.input.once("pointerdown", () => this.startAudio());
  }

  private async startAudio(): Promise<void> {
    if (this.starting) return;
    this.starting = true;
    // Web Audio contexts must be created/resumed from a user gesture (PRD
    // §10.4) -- this is that gesture. No audio is scheduled or played here.
    await Tone.start();
    GameContext.analytics.track("audio_gate_completed");
    this.scene.start("MainMenuScene");
  }
}
