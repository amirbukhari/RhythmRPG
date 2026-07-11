import Phaser from "phaser";
import { BASE_WIDTH } from "../config/GameConfig";
import { TextMenu } from "../ui/components/TextMenu";
import { addBackdrop } from "../ui/Backdrop";

/** Start, continue, settings. See PRD §10.6. */
export class MainMenuScene extends Phaser.Scene {
  constructor() {
    super("MainMenuScene");
  }

  create(): void {
    addBackdrop(this, 0.55);

    this.add
      .text(BASE_WIDTH / 2, 44, "METERFALL", {
        fontFamily: "monospace",
        fontSize: "26px",
        color: "#f4efe2",
        fontStyle: "bold",
        stroke: "#4b2a57",
        strokeThickness: 6,
      })
      .setOrigin(0.5)
      .setShadow(0, 2, "#05060a", 4, true, true);
    this.add
      .text(BASE_WIDTH / 2, 66, "· the drowned chorus ·", {
        fontFamily: "monospace",
        fontSize: "8px",
        color: "#49c6bd",
      })
      .setOrigin(0.5);

    new TextMenu(this, BASE_WIDTH / 2 - 44, 96, [
      { label: "Start / Continue", onSelect: () => this.scene.start("SaveScene") },
      { label: "Settings", onSelect: () => this.scene.launch("SettingsOverlay", { returnTo: "MainMenuScene" }) },
    ]);

    this.add
      .text(BASE_WIDTH / 2, 170, "a rhythm of rust and tide", { fontFamily: "monospace", fontSize: "7px", color: "#877d70" })
      .setOrigin(0.5);
  }
}
