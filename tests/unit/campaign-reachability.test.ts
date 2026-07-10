import { describe, expect, it } from "vitest";
import { reachableNodeIds, nodeStatus } from "../../src/systems/progression/CampaignReachability";
import type { CampaignDefinition } from "../../src/data/schemas/CampaignNode";

// Mirrors the real opening_biome.json shape: a linear 4-node chain.
const campaign: CampaignDefinition = {
  startNodeId: "a",
  nodes: [
    { nodeId: "a", type: "battle", encounterId: "e_a", next: ["b"] },
    { nodeId: "b", type: "battle", encounterId: "e_b", next: ["c"] },
    { nodeId: "c", type: "elite", encounterId: "e_c", next: ["d"] },
    { nodeId: "d", type: "boss", encounterId: "e_d", next: [] },
  ],
};

describe("reachableNodeIds", () => {
  it("includes every node from start up to and including the current node", () => {
    expect(reachableNodeIds(campaign, "c")).toEqual(new Set(["a", "b", "c"]));
  });

  it("is just the start node on a fresh save", () => {
    expect(reachableNodeIds(campaign, "a")).toEqual(new Set(["a"]));
  });

  it("covers the whole chain at the final node", () => {
    expect(reachableNodeIds(campaign, "d")).toEqual(new Set(["a", "b", "c", "d"]));
  });

  it("stops at the end of the chain even if currentNodeId is unknown", () => {
    expect(reachableNodeIds(campaign, "nonexistent")).toEqual(new Set(["a", "b", "c", "d"]));
  });
});

describe("nodeStatus", () => {
  const progress = { currentNodeId: "b", clearedNodeIds: ["a"] };

  it("marks cleared nodes cleared, even though they are also reachable", () => {
    expect(nodeStatus(campaign, progress, "a")).toBe("cleared");
  });

  it("marks the current frontier node unlocked", () => {
    expect(nodeStatus(campaign, progress, "b")).toBe("unlocked");
  });

  it("marks nodes past the frontier locked", () => {
    expect(nodeStatus(campaign, progress, "c")).toBe("locked");
    expect(nodeStatus(campaign, progress, "d")).toBe("locked");
  });
});
