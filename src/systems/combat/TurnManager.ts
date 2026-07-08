export type TurnPhase = "intent" | "command" | "performance" | "resolution" | "roundEnd";

/** Drives the fixed turn structure defined in PRD §8.2. Untimed except performance phase. */
export class TurnManager {
  phase: TurnPhase = "intent";

  advance(): TurnPhase {
    const order: TurnPhase[] = ["intent", "command", "performance", "resolution", "roundEnd"];
    const next = order[(order.indexOf(this.phase) + 1) % order.length];
    this.phase = next;
    return next;
  }
}
