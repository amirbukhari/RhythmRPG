import Phaser from "phaser";
import * as Tone from "tone";
import { GameContext } from "../state/GameContext";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";
import { addBackdrop } from "../ui/Backdrop";
import { music } from "../systems/audio/SongPlayer";

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
    addBackdrop(this, 0.45);
    this.add
      .text(BASE_WIDTH / 2, BASE_HEIGHT / 2, "PRESS ANY KEY OR CLICK TO CONTINUE", {
        fontFamily: "monospace",
        fontSize: "10px",
        color: "#f4efe2",
        align: "center",
        stroke: "#05060a",
        strokeThickness: 3,
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
    // Start the real soundtrack from INSIDE this gesture so mobile browsers
    // (which block audio until a user gesture) allow it; later scene changes
    // inherit the unlocked state. Volume comes from the active profile.
    music.setVolume(GameContext.activeProfile?.settings.volumeMusic ?? 0.7);
    music.setMode("menu");
    GameContext.analytics.track("audio_gate_completed");
    this.scene.start("MainMenuScene");
  }
}
