import { describe, expect, it } from "vitest";
import { Analytics } from "../../src/systems/analytics/Analytics";

describe("Analytics", () => {
  it("drops events when consent hasn't been granted", () => {
    const analytics = new Analytics(() => 1000);
    analytics.track("battle_started");
    expect(analytics.getRecords()).toHaveLength(0);
  });

  it("records events once consent is granted", () => {
    const analytics = new Analytics(() => 1000);
    analytics.setConsent(true);
    analytics.track("battle_started", { encounterId: "opening_biome_slime_01" });
    expect(analytics.getRecords()).toEqual([
      { event: "battle_started", payload: { encounterId: "opening_biome_slime_01" }, timestampMs: 1000 },
    ]);
  });

  it("stops recording if consent is revoked", () => {
    const analytics = new Analytics(() => 1000);
    analytics.setConsent(true);
    analytics.track("save_loaded");
    analytics.setConsent(false);
    analytics.track("save_loaded");
    expect(analytics.getRecords()).toHaveLength(1);
  });

  it("clears recorded events", () => {
    const analytics = new Analytics(() => 1000);
    analytics.setConsent(true);
    analytics.track("save_loaded");
    analytics.clear();
    expect(analytics.getRecords()).toHaveLength(0);
  });
});
