import { describe, expect, it } from "vitest";
import { resolveEncounterId } from "../../src/systems/progression/CampaignSelection";
import type { CampaignNode } from "../../src/data/schemas/CampaignNode";

function node(overrides: Partial<CampaignNode>): CampaignNode {
  return { nodeId: "n", type: "battle", next: [], ...overrides };
}

describe("resolveEncounterId", () => {
  it("returns the fixed encounterId when there is no pool", () => {
    expect(resolveEncounterId(node({ encounterId: "fixed_01" }))).toBe("fixed_01");
  });

  it("returns undefined for a camp node with neither encounterId nor encounterPool", () => {
    expect(resolveEncounterId(node({ type: "camp" }))).toBeUndefined();
  });

  it("always returns one of the pool's entries", () => {
    const pool = ["a", "b", "c"];
    for (let i = 0; i < 50; i++) {
      expect(pool).toContain(resolveEncounterId(node({ encounterPool: pool })));
    }
  });

  it("eventually selects every entry in the pool across many calls (real randomness, not always the first)", () => {
    const pool = ["a", "b", "c"];
    const seen = new Set<string>();
    for (let i = 0; i < 200; i++) {
      seen.add(resolveEncounterId(node({ encounterPool: pool }))!);
    }
    expect(seen).toEqual(new Set(pool));
  });
});
