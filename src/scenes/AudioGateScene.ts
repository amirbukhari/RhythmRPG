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

    // Belt-and-suspenders for real phones (the gate is the front door and
    // MUST never be missable): if Phaser's input pipeline drops the tap on
    // some mobile browser, plain DOM listeners still catch it. Removed on
    // first fire or scene shutdown.
    const domStart = (): void => {
      void this.startAudio();
    };
    for (const evt of ["pointerup", "touchend", "click"] as const) {
      document.addEventListener(evt, domStart, { once: true, passive: true });
    }
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      for (const evt of ["pointerup", "touchend", "click"] as const) {
        document.removeEventListener(evt, domStart);
      }
    });
  }

  private async startAudio(): Promise<void> {
    if (this.starting) return;
    this.starting = true;
    // Web Audio contexts must be created/resumed from a user gesture (PRD
    // §10.4) -- this is that gesture. No audio is scheduled or played here.
    // Guarded: on some mobile browsers AudioContext.resume() can hang or
    // throw -- the gate must advance regardless (the context unlocks on a
    // later gesture; every play()/trigger downstream is failure-tolerant).
    try {
      await Promise.race([Tone.start(), new Promise((resolve) => setTimeout(resolve, 2000))]);
    } catch {
      /* resume failed -- proceed; audio re-unlocks on the next gesture */
    }
    // Start the real soundtrack from INSIDE this gesture so mobile browsers
    // (which block audio until a user gesture) allow it; later scene changes
    // inherit the unlocked state. Volume comes from the active profile.
    music.setVolume(GameContext.activeProfile?.settings.volumeMusic ?? 0.7);
    music.setMode("menu");
    GameContext.analytics.track("audio_gate_completed");
    this.scene.start("MainMenuScene");
  }
}
