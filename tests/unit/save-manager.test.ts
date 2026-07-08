import { describe, expect, it } from "vitest";
import { SaveManager, createDefaultSaveProfile } from "../../src/systems/persistence/SaveManager";

// fake-indexeddb persists for the process, so each test uses a unique slotId
// to avoid cross-test interference.

describe("SaveManager", () => {
  it("round-trips a save profile", async () => {
    const manager = new SaveManager();
    const profile = createDefaultSaveProfile("slot-a", "opening_1");
    await manager.save(profile);
    const loaded = await manager.load("slot-a");
    expect(loaded).toEqual(profile);
  });

  it("returns undefined for a slot that was never saved", async () => {
    const manager = new SaveManager();
    const loaded = await manager.load("slot-never-saved");
    expect(loaded).toBeUndefined();
  });

  it("deletes a slot", async () => {
    const manager = new SaveManager();
    await manager.save(createDefaultSaveProfile("slot-b", "opening_1"));
    await manager.delete("slot-b");
    expect(await manager.load("slot-b")).toBeUndefined();
  });

  it("lists all saved slot ids", async () => {
    const manager = new SaveManager();
    await manager.save(createDefaultSaveProfile("slot-c", "opening_1"));
    await manager.save(createDefaultSaveProfile("slot-d", "opening_1"));
    const slots = await manager.listSlots();
    expect(slots).toEqual(expect.arrayContaining(["slot-c", "slot-d"]));
  });

  it("creates a default profile with accessibility defaults and zeroed progress", () => {
    const profile = createDefaultSaveProfile("slot-e", "opening_1");
    expect(profile.campaignProgress).toEqual({ currentNodeId: "opening_1", clearedNodeIds: [], xp: 0, currency: 0 });
    expect(profile.settings.gameSpeed).toBe(1.0);
    expect(profile.analyticsConsent).toBe(false);
  });
});
