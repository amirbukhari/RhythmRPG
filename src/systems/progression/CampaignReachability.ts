import type { CampaignDefinition } from "../../data/schemas/CampaignNode";

// Extracted from MapScene.reachableNodeIds so the overworld's marker-status
// logic is a pure, directly unit-testable module (parameterized on plain
// data, not the ContentRegistry singleton) -- same style as
// CampaignSelection.ts.

export type NodeStatus = "locked" | "unlocked" | "cleared";

/** The subset of SaveProfile.campaignProgress this module needs. */
export interface CampaignProgressView {
  currentNodeId: string;
  clearedNodeIds: string[];
}

/**
 * Every node from campaign start up to and including currentNodeId,
 * following the linear `next` chain. (Branching -- next[1+] -- is still
 * unimplemented everywhere; see PRD §20.)
 */
export function reachableNodeIds(campaign: CampaignDefinition, currentNodeId: string): Set<string> {
  const byId = new Map(campaign.nodes.map((n) => [n.nodeId, n]));
  const visited = new Set<string>();
  let node = byId.get(campaign.startNodeId);
  while (node) {
    visited.add(node.nodeId);
    if (node.nodeId === currentNodeId || node.next.length === 0) break;
    node = byId.get(node.next[0]);
  }
  return visited;
}

/**
 * cleared > unlocked > locked. Cleared wins over unlocked so the overworld
 * can treat cleared markers as walk-over no-ops (v1 has no re-fighting) --
 * a cleared node sits *on* the road to the next one, so triggering it on
 * touch would force a re-fight just to walk past.
 */
export function nodeStatus(campaign: CampaignDefinition, progress: CampaignProgressView, nodeId: string): NodeStatus {
  if (progress.clearedNodeIds.includes(nodeId)) return "cleared";
  return reachableNodeIds(campaign, progress.currentNodeId).has(nodeId) ? "unlocked" : "locked";
}
