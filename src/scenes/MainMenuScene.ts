import Phaser from "phaser";
import { BASE_WIDTH } from "../config/GameConfig";
import { TextMenu } from "../ui/components/TextMenu";

/** Start, continue, settings. See PRD §10.6. */
export class MainMenuScene extends Phaser.Scene {
  constructor() {
    super("MainMenuScene");
  }

  create(): void {
    this.add
      .text(BASE_WIDTH / 2, 40, "PROJECT METERFALL", {
        fontFamily: "monospace",
        fontSize: "14px",
        color: "#ffffff",
      })
      .setOrigin(0.5);

    new TextMenu(this, BASE_WIDTH / 2 - 30, 90, [
      { label: "Start / Continue", onSelect: () => this.scene.start("SaveScene") },
      { label: "Settings", onSelect: () => this.scene.launch("SettingsOverlay", { returnTo: "MainMenuScene" }) },
    ]);
  }
}
