import Phaser from "phaser";
import heroPlaceholderUrl from "../../assets/sprites/heroes/placeholder/Amir CrouchWait.png";

/** Loads the asset manifest and verifies browser support. See PRD §10.6. */
export class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  preload(): void {
    // The only real (if placeholder-quality, PRD §11.4/§20.2) art asset in
    // the repo -- loaded once here so every scene's texture manager has it.
    this.load.image("hero_placeholder", heroPlaceholderUrl);
  }

  create(): void {
    const hasWebAudio = typeof window !== "undefined" && ("AudioContext" in window || "webkitAudioContext" in window);
    if (!hasWebAudio) {
      this.add
        .text(160, 90, "This browser does not support Web Audio.\nPlease use a current Chrome, Edge, Firefox, or Safari.", {
          fontFamily: "monospace",
          fontSize: "8px",
          color: "#ff5555",
          align: "center",
          wordWrap: { width: 300 },
        })
        .setOrigin(0.5);
      return;
    }
    this.scene.start("AudioGateScene");
  }
}
