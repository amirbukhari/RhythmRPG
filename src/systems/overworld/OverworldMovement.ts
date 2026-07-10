// Pure grid-movement math for the walkable overworld -- no Phaser imports,
// same testability rationale as src/systems/progression/CampaignSelection.ts.
// The scene owns tweens/sprites/input; this module owns "where would this
// step land" and "is that tile legal", which is everything worth unit-testing.

export type Direction = "up" | "down" | "left" | "right";

export interface GridPosition {
  col: number;
  row: number;
}

const STEP: Record<Direction, GridPosition> = {
  up: { col: 0, row: -1 },
  down: { col: 0, row: 1 },
  left: { col: -1, row: 0 },
  right: { col: 1, row: 0 },
};

/** The tile one step from `pos` in `dir`. Pure math; does not check walkability. */
export function stepTarget(pos: GridPosition, dir: Direction): GridPosition {
  return { col: pos.col + STEP[dir].col, row: pos.row + STEP[dir].row };
}

/**
 * Whether `pos` is a legal tile to stand on. `walkable` is indexed
 * [row][col] (built once by the scene from the tilemap's per-tile
 * `collides` properties); anything outside the grid is not walkable, so a
 * map without a solid border still can't be walked off.
 */
export function isWalkable(walkable: boolean[][], pos: GridPosition): boolean {
  return walkable[pos.row]?.[pos.col] === true;
}
