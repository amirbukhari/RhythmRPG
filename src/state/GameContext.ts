import { Analytics } from "../systems/analytics/Analytics";
import { SaveManager, type SaveProfile } from "../systems/persistence/SaveManager";

export interface BattleResult {
  outcome: "victory" | "defeat";
  encounterId: string;
  xp: number;
  currency: number;
  relicChoices: string[];
}

/**
 * Process-lifetime singleton for services and state that must survive scene
 * transitions (Phaser scenes are recreated/torn down independently). Kept
 * deliberately small: the save profile is the single source of truth for
 * anything persistent, everything else here is a stateless service handle.
 */
class GameContextImpl {
  readonly saveManager = new SaveManager();
  readonly analytics = new Analytics();

  activeProfile: SaveProfile | null = null;
  /** Set by MapScene before starting BattleScene; read once, then cleared. */
  pendingEncounterId: string | null = null;
  /** The campaign node backing pendingEncounterId -- distinct from it, since node ids and encounter ids are different id spaces. */
  pendingNodeId: string | null = null;
  /** Set by BattleScene before starting ResultsScene; read once, then cleared. */
  lastBattleResult: BattleResult | null = null;

  async persistActiveProfile(): Promise<void> {
    if (!this.activeProfile) throw new Error("No active save profile to persist.");
    await this.saveManager.save(this.activeProfile);
  }
}

export const GameContext = new GameContextImpl();
