// Not a PRD §10.5 canonical schema -- same rationale as Enemy.ts/HeroClass.ts.
// The node-based campaign map (PRD §8.1) needs a graph structure that none
// of the three fixed schemas describe.

export type CampaignNodeType = "battle" | "elite" | "camp" | "boss";

export interface CampaignNode {
  nodeId: string;
  type: CampaignNodeType;
  /** Required for battle/elite/boss nodes; absent for camp nodes. */
  encounterId?: string;
  next: string[];
}

export interface CampaignDefinition {
  startNodeId: string;
  nodes: CampaignNode[];
}
