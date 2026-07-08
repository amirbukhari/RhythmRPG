import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";
import { TextMenu } from "../ui/components/TextMenu";

/** XP, relic, and unlock summary after a battle. See PRD §8.5. */
export class ResultsScene extends Phaser.Scene {
  constructor() {
    super("ResultsScene");
  }

  create(): void {
    const result = GameContext.lastBattleResult;
    GameContext.lastBattleResult = null;

    if (!result) {
      this.scene.start("MapScene");
      return;
    }

    const headline = result.outcome === "victory" ? "VICTORY" : "DEFEAT";
    const color = result.outcome === "victory" ? "#ffe066" : "#ff5555";
    this.add.text(BASE_WIDTH / 2, 40, headline, { fontFamily: "monospace", fontSize: "16px", color }).setOrigin(0.5);

    const detail =
      result.outcome === "victory"
        ? `+${result.xp} XP   +${result.currency} Gold${result.relicChoices.length ? `\nRelic choices: ${result.relicChoices.join(", ")}` : ""}`
        : "The party was defeated. No rewards this run.";
    this.add
      .text(BASE_WIDTH / 2, 70, detail, { fontFamily: "monospace", fontSize: "8px", color: "#ffffff", align: "center", wordWrap: { width: BASE_WIDTH - 20 } })
      .setOrigin(0.5, 0);

    new TextMenu(this, BASE_WIDTH / 2 - 30, BASE_HEIGHT - 40, [{ label: "Continue", onSelect: () => this.scene.start("MapScene") }]);
  }
}
