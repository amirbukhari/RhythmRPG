/**
 * IndexedDB-backed local save profile. See PRD §10.7 — never use localStorage
 * for save data.
 */
export interface SaveProfile {
  slotId: string;
  settings: Record<string, unknown>;
  calibrationOffsetMs: number;
  campaignProgress: Record<string, unknown>;
  unlockedSkills: string[];
  relicInventory: string[];
  analyticsConsent: boolean;
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
}
