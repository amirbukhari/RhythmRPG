import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { RELICS } from "../systems/progression/Relics";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";
import { TextMenu } from "../ui/components/TextMenu";
import { addBackdrop } from "../ui/Backdrop";

/** XP, relic, and unlock summary after a battle. See PRD §8.5. */
export class ResultsScene extends Phaser.Scene {
  private menu: TextMenu | null = null;

  constructor() {
    super("ResultsScene");
  }

  create(): void {
    const result = GameContext.lastBattleResult;
    GameContext.lastBattleResult = null;

    if (!result) {
      this.scene.start("OverworldScene");
      return;
    }

    addBackdrop(this, 0.55);

    const headline = result.outcome === "victory" ? "VICTORY" : "DEFEAT";
    const color = result.outcome === "victory" ? "#ffe066" : "#ff5555";
    this.add.text(BASE_WIDTH / 2, 30, headline, { fontFamily: "monospace", fontSize: "16px", color }).setOrigin(0.5);

    const lines: string[] = [];
    if (result.outcome === "victory") {
      lines.push(`+${result.xp} XP   +${result.currency} Gold`);
      if (result.unlockedSkills.length > 0) {
        lines.push(`Unlocked: ${result.unlockedSkills.join(", ")}`);
      }
    } else {
      lines.push("The party was defeated. No rewards this run.");
    }
    this.add
      .text(BASE_WIDTH / 2, 55, lines.join("\n"), {
        fontFamily: "monospace",
        fontSize: "8px",
        color: "#ffffff",
        align: "center",
        wordWrap: { width: BASE_WIDTH - 20 },
      })
      .setOrigin(0.5, 0);

    this.renderMenu(result.relicChoices);
  }

  private renderMenu(relicChoices: string[]): void {
    const items =
      relicChoices.length > 0
        ? relicChoices.map((relicId) => ({
            label: `Take: ${RELICS[relicId]?.name ?? relicId} -- ${RELICS[relicId]?.description ?? ""}`,
            onSelect: () => this.chooseRelic(relicId),
          }))
        : [{ label: "Continue", onSelect: () => this.continueOut() }];

    if (this.menu) this.menu.setItems(items);
    else this.menu = new TextMenu(this, 16, BASE_HEIGHT - 60, items, 14);
  }

  /** The final boss's victory continues into the ending, exactly once. */
  private continueOut(): void {
    if (GameContext.campaignJustCompleted) {
      GameContext.campaignJustCompleted = false;
      this.scene.start("FinaleScene");
    } else {
      this.scene.start("OverworldScene");
    }
  }

  private chooseRelic(relicId: string): void {
    const profile = GameContext.activeProfile;
    if (profile && !profile.relicInventory.includes(relicId)) {
      profile.relicInventory.push(relicId);
      void GameContext.persistActiveProfile();
    }
    this.renderMenu([]); // collapse to a single "Continue" once a relic is chosen
  }
}
