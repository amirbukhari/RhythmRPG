// Not a PRD §10.5 canonical schema -- same rationale as Enemy.ts/HeroClass.ts.
// The node-based campaign map (PRD §8.1) needs a graph structure that none
// of the three fixed schemas describe.

export type CampaignNodeType = "battle" | "elite" | "camp" | "boss";

export interface CampaignNode {
  nodeId: string;
  type: CampaignNodeType;
  /** Required for battle/elite/boss nodes unless encounterPool is set; absent for camp nodes. */
  encounterId?: string;
  /**
   * When set, one encounterId is chosen at random from this pool each time
   * the node is entered, instead of the fixed `encounterId` -- real
   * per-node replay variety (PRD §8.6/§20.2) rather than the same single
   * authored fight every run. Mutually exclusive with `encounterId` in
   * practice, though both being present is harmless (pool wins).
   */
  encounterPool?: string[];
  next: string[];
}

export interface CampaignDefinition {
  startNodeId: string;
  nodes: CampaignNode[];
}
