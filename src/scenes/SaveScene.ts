import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { createDefaultSaveProfile } from "../systems/persistence/SaveManager";
import { campaign } from "../data/ContentRegistry";
import {BASE_WIDTH, retinaCamera } from "../config/GameConfig";
import { TextMenu } from "../ui/components/TextMenu";

/** Save slot create/load/delete against IndexedDB. See PRD §10.7. */
export class SaveScene extends Phaser.Scene {
  constructor() {
    super("SaveScene");
  }

  async create(): Promise<void> {
    retinaCamera(this);
    this.add.text(BASE_WIDTH / 2, 20, "SELECT SAVE SLOT", { fontFamily: "monospace", fontSize: "10px", color: "#ffffff" }).setOrigin(0.5);

    const slots = await GameContext.saveManager.listSlots();
    const items = slots.map((slotId) => ({
      label: `Load: ${slotId}`,
      onSelect: () => void this.loadSlot(slotId),
    }));
    items.push({ label: "+ New Save", onSelect: () => void this.createSlot() });

    new TextMenu(this, 40, 50, items);
  }

  private async loadSlot(slotId: string): Promise<void> {
    const profile = await GameContext.saveManager.load(slotId);
    if (!profile) return;
    GameContext.activeProfile = profile;
    GameContext.analytics.setConsent(profile.analyticsConsent);
    GameContext.analytics.track("save_loaded", { slotId });
    this.scene.start(profile.calibrationDone ? "OverworldScene" : "CalibrationScene");
  }

  private async createSlot(): Promise<void> {
    const slotId = `save-${Date.now()}`;
    const profile = createDefaultSaveProfile(slotId, campaign.startNodeId);
    await GameContext.saveManager.save(profile);
    GameContext.activeProfile = profile;
    this.scene.start("CalibrationScene");
  }
}
