import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { campaign, getEncounter } from "../data/ContentRegistry";
import { BASE_WIDTH } from "../config/GameConfig";
import { TextMenu } from "../ui/components/TextMenu";

/** Node-based campaign map: battle / elite / camp / boss nodes. See PRD §8.1. */
export class MapScene extends Phaser.Scene {
  constructor() {
    super("MapScene");
  }

  create(): void {
    const profile = GameContext.activeProfile;
    if (!profile) {
      this.scene.start("SaveScene");
      return;
    }

    this.add
      .text(BASE_WIDTH / 2, 16, "CAMPAIGN MAP", { fontFamily: "monospace", fontSize: "10px", color: "#ffffff" })
      .setOrigin(0.5);
    this.add
      .text(BASE_WIDTH / 2, 30, `XP: ${profile.campaignProgress.xp}   Gold: ${profile.campaignProgress.currency}`, {
        fontFamily: "monospace",
        fontSize: "8px",
        color: "#aaaaaa",
      })
      .setOrigin(0.5);

    const items = campaign.nodes.map((node) => {
      const cleared = profile.campaignProgress.clearedNodeIds.includes(node.nodeId);
      const label = `[${node.type.toUpperCase()}] ${node.encounterId ? getEncounter(node.encounterId).encounterId : node.nodeId}${cleared ? " (cleared)" : ""}`;
      return {
        label,
        onSelect: () => {
          if (!node.encounterId) return;
          GameContext.pendingEncounterId = node.encounterId;
          this.scene.start("BattleScene");
        },
      };
    });
    items.push({ label: "Settings", onSelect: () => this.scene.launch("SettingsOverlay", { returnTo: "MapScene" }) });

    new TextMenu(this, 30, 60, items);
  }
}
