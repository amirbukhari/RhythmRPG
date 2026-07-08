import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { campaign, getEncounter, getCampaignNode } from "../data/ContentRegistry";
import type { CampaignNode } from "../data/schemas/CampaignNode";
import { BASE_WIDTH } from "../config/GameConfig";
import { TextMenu } from "../ui/components/TextMenu";

const NODE_COLOR_CLEARED = 0x44cc66;
const NODE_COLOR_UNLOCKED = 0xffe066;
const NODE_COLOR_LOCKED = 0x444444;
const NODE_TYPE_LABEL: Record<CampaignNode["type"], string> = { battle: "B", elite: "E", boss: "!", camp: "C" };

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
      .text(BASE_WIDTH / 2, 8, "CAMPAIGN MAP", { fontFamily: "monospace", fontSize: "10px", color: "#ffffff" })
      .setOrigin(0.5);
    this.add
      .text(BASE_WIDTH / 2, 20, `XP: ${profile.campaignProgress.xp}   Gold: ${profile.campaignProgress.currency}`, {
        fontFamily: "monospace",
        fontSize: "8px",
        color: "#aaaaaa",
      })
      .setOrigin(0.5);

    const unlocked = this.reachableNodeIds(profile.campaignProgress.currentNodeId);
    this.drawNodeGraph(profile, unlocked);

    const items = campaign.nodes.map((node) => {
      const cleared = profile.campaignProgress.clearedNodeIds.includes(node.nodeId);
      const isUnlocked = unlocked.has(node.nodeId);
      const status = cleared ? " (cleared)" : isUnlocked ? "" : " (locked)";
      const label = `[${node.type.toUpperCase()}] ${node.encounterId ? getEncounter(node.encounterId).encounterId : node.nodeId}${status}`;
      return {
        label,
        disabled: !node.encounterId || !isUnlocked,
        onSelect: () => {
          if (!node.encounterId) return;
          GameContext.pendingEncounterId = node.encounterId;
          GameContext.pendingNodeId = node.nodeId;
          this.scene.start("BattleScene");
        },
      };
    });
    items.push({ label: "Settings", disabled: false, onSelect: () => this.scene.launch("SettingsOverlay", { returnTo: "MapScene" }) });

    new TextMenu(this, 12, 105, items, 11);
  }

  /**
   * A real node-graph visualization (circles on a path, connected by
   * lines, color-coded by status) rather than text-only status labels --
   * the actual interaction still goes through the TextMenu below, since
   * syncing keyboard-hover state onto individual graph nodes is future
   * polish, not required for this to be a genuine visual map.
   */
  private drawNodeGraph(profile: NonNullable<typeof GameContext.activeProfile>, unlocked: Set<string>): void {
    const nodes = campaign.nodes;
    const margin = 28;
    const spacing = nodes.length > 1 ? (BASE_WIDTH - margin * 2) / (nodes.length - 1) : 0;
    const y = 55;
    const positions = nodes.map((_, i) => margin + i * spacing);

    const lines = this.add.graphics();
    lines.lineStyle(2, 0x666666, 1);
    for (let i = 0; i < positions.length - 1; i++) {
      lines.lineBetween(positions[i], y, positions[i + 1], y);
    }

    nodes.forEach((node, i) => {
      const cleared = profile.campaignProgress.clearedNodeIds.includes(node.nodeId);
      const isUnlocked = unlocked.has(node.nodeId);
      const color = cleared ? NODE_COLOR_CLEARED : isUnlocked ? NODE_COLOR_UNLOCKED : NODE_COLOR_LOCKED;
      const radius = node.type === "boss" ? 10 : 7;

      this.add.circle(positions[i], y, radius, color);
      this.add
        .text(positions[i], y, NODE_TYPE_LABEL[node.type], { fontFamily: "monospace", fontSize: "7px", color: "#000000" })
        .setOrigin(0.5);
    });
  }

  /** Every node from campaign start up to and including currentNodeId, following the linear `next` chain. */
  private reachableNodeIds(currentNodeId: string): Set<string> {
    const visited = new Set<string>();
    let node = getCampaignNode(campaign.startNodeId);
    while (true) {
      visited.add(node.nodeId);
      if (node.nodeId === currentNodeId || node.next.length === 0) break;
      node = getCampaignNode(node.next[0]);
    }
    return visited;
  }
}
