import { describe, expect, it } from "vitest";
import {
  abilities,
  abilitiesForRole,
  beatmaps,
  encounters,
  enemies,
  getEncounter,
  campaign,
  getCampaignNode,
  bossPhaseConfigs,
  getBossPhaseConfig,
} from "../../src/data/ContentRegistry";

describe("ContentRegistry", () => {
  it("loads and validates all shipped ability files", () => {
    expect(abilities.size).toBe(16);
  });

  it("has the 3 core PRD §8.4 abilities plus 1 tier-2 unlock ability per role", () => {
    for (const role of ["warrior", "tank", "mage", "healer"] as const) {
      expect(abilitiesForRole(role)).toHaveLength(4);
    }
  });

  it("includes the canonical healer_sightread forecast ability", () => {
    const sightread = abilitiesForRole("healer").find((a) => a.abilityId === "healer_sightread");
    expect(sightread?.effects.some((e) => e.type === "forecastReveal")).toBe(true);
  });

  it("gives every role a tier-2 ability, keyed to match the boss-clear unlock id", () => {
    for (const role of ["warrior", "tank", "mage", "healer"] as const) {
      expect(abilities.has(`${role}_tier2`)).toBe(true);
    }
  });

  it("loads the opening biome beatmap and encounter", () => {
    expect(beatmaps.has("opening_biome_01")).toBe(true);
    expect(encounters.has("opening_biome_slime_01")).toBe(true);
  });

  it("loads every encounter's referenced beatmap and enemies, with every enemyTelegraph payload backed by a real enemy intent", () => {
    expect(encounters.size).toBeGreaterThanOrEqual(5); // opening + 3 mid-biome + boss
    for (const encounter of encounters.values()) {
      const beatmap = beatmaps.get(encounter.trackId);
      expect(beatmap, `encounter "${encounter.encounterId}" references missing beatmap "${encounter.trackId}"`).toBeDefined();

      for (const enemyId of encounter.enemyWave) {
        expect(enemies.has(enemyId), `encounter "${encounter.encounterId}" references missing enemy "${enemyId}"`).toBe(true);
      }

      const telegraphPayloads = new Set(beatmap!.events.filter((e) => e.type === "enemyTelegraph").map((e) => e.payload));
      const enemyTelegraphs = new Set(encounter.enemyWave.flatMap((enemyId) => enemies.get(enemyId)?.intents.map((i) => i.telegraph) ?? []));
      for (const payload of telegraphPayloads) {
        expect(enemyTelegraphs.has(payload as string), `encounter "${encounter.encounterId}" beatmap references unknown telegraph "${payload}"`).toBe(true);
      }
    }
  });

  it("loads a valid campaign whose start node exists and references a real encounter", () => {
    const start = getCampaignNode(campaign.startNodeId);
    expect(start.type).toBe("battle");
    expect(encounters.has(start.encounterId!)).toBe(true);
  });

  it("chains every campaign node to a real next node, ending in the boss", () => {
    for (const node of campaign.nodes) {
      for (const nextId of node.next) {
        expect(() => getCampaignNode(nextId)).not.toThrow();
      }
    }
    const bossNodes = campaign.nodes.filter((n) => n.type === "boss");
    expect(bossNodes).toHaveLength(1);
    expect(bossNodes[0].next).toEqual([]); // boss is the terminal node
  });

  it("reaches the boss node by following `next` from the start node", () => {
    const visited: string[] = [];
    let current = getCampaignNode(campaign.startNodeId);
    while (true) {
      visited.push(current.nodeId);
      if (current.next.length === 0) break;
      current = getCampaignNode(current.next[0]);
    }
    expect(current.type).toBe("boss");
    expect(new Set(visited).size).toBe(visited.length); // no cycles
  });

  it("throws a clear error for an unknown campaign node", () => {
    expect(() => getCampaignNode("does_not_exist")).toThrow(/Unknown campaign node/);
  });

  it("loads a boss phase config for the boss encounter with strictly decreasing, valid thresholds", () => {
    expect(bossPhaseConfigs.size).toBeGreaterThanOrEqual(1);
    const bossNode = campaign.nodes.find((n) => n.type === "boss")!;
    const config = getBossPhaseConfig(bossNode.encounterId!);
    expect(config).toBeDefined();
    expect(config!.phases.length).toBeGreaterThanOrEqual(2); // a "multi-phase" boss needs at least 2

    let previous = Infinity;
    for (const phase of config!.phases) {
      expect(phase.hpThreshold).toBeLessThan(previous);
      expect(beatmaps.has(phase.trackId), `boss phase references missing beatmap "${phase.trackId}"`).toBe(true);
      previous = phase.hpThreshold;
    }
  });

  it("gives the boss encounter's default trackId matching its first phase", () => {
    const bossNode = campaign.nodes.find((n) => n.type === "boss")!;
    const encounter = getEncounter(bossNode.encounterId!);
    const config = getBossPhaseConfig(bossNode.encounterId!)!;
    expect(encounter.trackId).toBe(config.phases[0].trackId);
  });

  it("has a real meter change authored in at least one boss phase beatmap (PRD §8.7)", () => {
    const bossNode = campaign.nodes.find((n) => n.type === "boss")!;
    const config = getBossPhaseConfig(bossNode.encounterId!)!;
    const hasMeterChange = config.phases.some((phase) => beatmaps.get(phase.trackId)!.meterSequence.length > 1);
    expect(hasMeterChange).toBe(true);
  });
});
