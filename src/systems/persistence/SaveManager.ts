import type { AccessibilitySettings } from "../accessibility/AccessibilitySettings";
import { DEFAULT_ACCESSIBILITY_SETTINGS } from "../accessibility/AccessibilitySettings";

export interface CampaignProgress {
  currentNodeId: string;
  clearedNodeIds: string[];
  xp: number;
  currency: number;
}

/**
 * IndexedDB-backed local save profile. See PRD §10.7 — never use localStorage
 * for save data.
 */
export interface SaveProfile {
  slotId: string;
  settings: AccessibilitySettings;
  calibrationOffsetMs: number;
  calibrationDone: boolean;
  campaignProgress: CampaignProgress;
  unlockedSkills: string[];
  relicInventory: string[];
  analyticsConsent: boolean;
  /** Discoverable environmental-lore fragments found in the explorable world (PRD §8.8.2). Ids like "echo_0". */
  echoesFound: string[];
  /** Epoch ms of the first campaign completion (the Conductor's fall). Absent until then. */
  campaignCompletedAt?: number;
  /** Epoch ms of the moment Nari was lost on the surface (v12.0 loss beat). Absent while he still follows. */
  nariLostAt?: number;
  /** Epoch ms of the moment Mir first climbed out of the Fold, where the campaign begins (v14.0). Absent while still in the underwater town. */
  leftFoldAt?: number;
  /** Narrative flags: cutscenes already played ("seen_rite") and NPC side-story progress ("met_sella"). See content/cutscenes.ts + content/dialogue.ts. */
  storyFlags?: string[];
}

export function createDefaultSaveProfile(slotId: string, startNodeId: string): SaveProfile {
  return {
    slotId,
    settings: { ...DEFAULT_ACCESSIBILITY_SETTINGS },
    calibrationOffsetMs: 0,
    calibrationDone: false,
    campaignProgress: { currentNodeId: startNodeId, clearedNodeIds: [], xp: 0, currency: 0 },
    unlockedSkills: [],
    relicInventory: [],
    analyticsConsent: false,
    echoesFound: [],
    storyFlags: [],
  };
}

const DB_NAME = "meterfall-saves";
const STORE_NAME = "profiles";

export class SaveManager {
  private dbPromise: Promise<IDBDatabase>;

  constructor() {
    this.dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => {
        request.result.createObjectStore(STORE_NAME, { keyPath: "slotId" });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async save(profile: SaveProfile): Promise<void> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      tx.objectStore(STORE_NAME).put(profile);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async load(slotId: string): Promise<SaveProfile | undefined> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const request = tx.objectStore(STORE_NAME).get(slotId);
      request.onsuccess = () => resolve(request.result as SaveProfile | undefined);
      request.onerror = () => reject(request.error);
    });
  }

  async delete(slotId: string): Promise<void> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      tx.objectStore(STORE_NAME).delete(slotId);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async listSlots(): Promise<string[]> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const request = tx.objectStore(STORE_NAME).getAllKeys();
      request.onsuccess = () => resolve(request.result as string[]);
      request.onerror = () => reject(request.error);
    });
  }
}
