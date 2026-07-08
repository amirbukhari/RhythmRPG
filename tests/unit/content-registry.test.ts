import { describe, expect, it } from "vitest";
import { abilities, abilitiesForRole, beatmaps, encounters, enemies, getEncounter, campaign, getCampaignNode } from "../../src/data/ContentRegistry";

describe("ContentRegistry", () => {
  it("loads and validates all shipped ability files", () => {
    expect(abilities.size).toBe(12);
  });

  it("has exactly 3 abilities per role, matching PRD §8.4", () => {
    for (const role of ["warrior", "tank", "mage", "healer"] as const) {
      expect(abilitiesForRole(role)).toHaveLength(3);
    }
  });

  it("includes the canonical healer_sightread forecast ability", () => {
    const sightread = abilitiesForRole("healer").find((a) => a.abilityId === "healer_sightread");
    expect(sightread?.effects.some((e) => e.type === "forecastReveal")).toBe(true);
  });

  it("loads the opening biome beatmap and encounter", () => {
    expect(beatmaps.has("opening_biome_01")).toBe(true);
    expect(encounters.has("opening_biome_slime_01")).toBe(true);
  });

  it("loads the slime enemy referenced by the opening encounter", () => {
    expect(enemies.has("slime")).toBe(true);
  });

  it("cross-references cleanly: encounter -> beatmap -> enemy telegraphs", () => {
    const encounter = getEncounter("opening_biome_slime_01");
    const beatmap = beatmaps.get(encounter.trackId);
    expect(beatmap).toBeDefined();

    const telegraphPayloads = new Set(
      beatmap!.events.filter((e) => e.type === "enemyTelegraph").map((e) => e.payload)
    );
    const enemyTelegraphs = new Set(
      encounter.enemyWave.flatMap((enemyId) => enemies.get(enemyId)?.intents.map((i) => i.telegraph) ?? [])
    );
    for (const payload of telegraphPayloads) {
      expect(enemyTelegraphs.has(payload as string)).toBe(true);
    }
  });

  it("loads a valid campaign whose start node exists and references a real encounter", () => {
    const start = getCampaignNode(campaign.startNodeId);
    expect(start.type).toBe("battle");
    expect(encounters.has(start.encounterId!)).toBe(true);
  });

  it("throws a clear error for an unknown campaign node", () => {
    expect(() => getCampaignNode("does_not_exist")).toThrow(/Unknown campaign node/);
  });
});
