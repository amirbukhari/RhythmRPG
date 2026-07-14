import Phaser from "phaser";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";
import { TextMenu } from "../ui/components/TextMenu";
import { addBackdrop } from "../ui/Backdrop";
import { music } from "../systems/audio/SongPlayer";
import { GameContext } from "../state/GameContext";

/** Start, continue, settings. See PRD §10.6. */
export class MainMenuScene extends Phaser.Scene {
  constructor() {
    super("MainMenuScene");
  }

  create(): void {
    // Start the procedural soundtrack (PRD §11.2). The AudioContext was
    // unlocked in AudioGateScene, so it can play from here on.
    music.setVolume(GameContext.activeProfile?.settings.volumeMusic ?? 0.7);
    music.setMode("menu");
    music.start();

    // AI-generated title key-art (the band on the drowned pier); fall back to
    // the shared backdrop if it somehow isn't loaded. A soft top scrim keeps
    // the wordmark legible over the art.
    if (this.textures.exists("bg_title")) {
      this.add.image(BASE_WIDTH / 2, BASE_HEIGHT / 2, "bg_title").setDepth(-10);
      this.add.rectangle(0, 0, BASE_WIDTH, 92, 0x05060a, 0.42).setOrigin(0, 0).setDepth(-9);
      this.add.rectangle(0, 96, BASE_WIDTH, BASE_HEIGHT - 96, 0x05060a, 0.3).setOrigin(0, 0).setDepth(-9);
    } else {
      addBackdrop(this, 0.55);
    }

    // The hand-lettered wordmark (tools/pixelart/wordmark.py) -- the AAA
    // audit's M1: a monospace headline isn't a logo. Drawn at 2x pixels in
    // the asset; 0.5 scale lands it back on the 320x180 logical grid.
    this.add.image(BASE_WIDTH / 2, 46, "wordmark").setScale(0.5);
    this.add
      .text(BASE_WIDTH / 2, 78, "· a rhythm of rust and tide ·", {
        fontFamily: "monospace",
        fontSize: "8px",
        color: "#d8ceb6",
      })
      .setOrigin(0.5);

    // framed menu panel
    this.add.nineslice(BASE_WIDTH / 2, 116, "ui_panel", undefined, 132, 42, 5, 5, 5, 5).setDepth(0);
    new TextMenu(this, BASE_WIDTH / 2 - 48, 102, [
      { label: "Start / Continue", onSelect: () => this.scene.start("SaveScene") },
      { label: "Settings", onSelect: () => this.scene.launch("SettingsOverlay", { returnTo: "MainMenuScene" }) },
    ]);
  }
}
