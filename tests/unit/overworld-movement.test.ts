import { describe, expect, it } from "vitest";
import { stepTarget, isWalkable, type Direction } from "../../src/systems/overworld/OverworldMovement";

describe("stepTarget", () => {
  it.each<[Direction, number, number]>([
    ["up", 3, 2],
    ["down", 3, 4],
    ["left", 2, 3],
    ["right", 4, 3],
  ])("moves one tile %s", (dir, col, row) => {
    expect(stepTarget({ col: 3, row: 3 }, dir)).toEqual({ col, row });
  });

  it("does not mutate the input position", () => {
    const pos = { col: 5, row: 5 };
    stepTarget(pos, "up");
    expect(pos).toEqual({ col: 5, row: 5 });
  });

  it("is pure math: happily steps off-grid (walkability is a separate check)", () => {
    expect(stepTarget({ col: 0, row: 0 }, "left")).toEqual({ col: -1, row: 0 });
  });
});

describe("isWalkable", () => {
  // [row][col]: a 3x3 grid with a blocked center.
  const grid = [
    [true, true, true],
    [true, false, true],
    [true, true, true],
  ];

  it("allows walkable tiles", () => {
    expect(isWalkable(grid, { col: 0, row: 0 })).toBe(true);
    expect(isWalkable(grid, { col: 2, row: 1 })).toBe(true);
  });

  it("blocks colliding tiles", () => {
    expect(isWalkable(grid, { col: 1, row: 1 })).toBe(false);
  });

  it("blocks everything outside the grid, on all four sides", () => {
    expect(isWalkable(grid, { col: -1, row: 0 })).toBe(false);
    expect(isWalkable(grid, { col: 3, row: 0 })).toBe(false);
    expect(isWalkable(grid, { col: 0, row: -1 })).toBe(false);
    expect(isWalkable(grid, { col: 0, row: 3 })).toBe(false);
  });
});
