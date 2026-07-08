import type { CampaignNode } from "../../data/schemas/CampaignNode";

/**
 * Picks the node's fixed encounterId, or one at random from its
 * encounterPool for real per-visit replay variety (PRD §8.6/§20.2) rather
 * than the same single authored fight every run. Pure so the random
 * selection itself is directly testable without touching Phaser.
 */
export function resolveEncounterId(node: CampaignNode): string | undefined {
  if (node.encounterPool && node.encounterPool.length > 0) {
    return node.encounterPool[Math.floor(Math.random() * node.encounterPool.length)];
  }
  return node.encounterId;
}
