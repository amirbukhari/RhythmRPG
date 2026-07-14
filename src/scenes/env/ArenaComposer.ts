import Phaser from "phaser";
import { BASE_WIDTH, BASE_HEIGHT } from "../../config/GameConfig";

/**
 * Kitbashed top-down arenas (PRD §11.1 / §8.2). Instead of one AI-generated
 * "whole scene" image (which reads as uncontrollable concept art), each arena
 * is an INTENTIONAL layout: a ground base plus individually-generated, isolated
 * environment pieces (rocks, ruins, reeds, a campfire save point...) placed by
 * hand. This is how HLD-style top-down environments are actually built -- a
 * library of pieces, kitbashed. Pieces are loaded as `env_<biome>_<piece>`.
 */

export interface Placement {
  /** texture key, e.g. "env_shallows_rock_a" */
  key: string;
  x: number;
  y: number; // the piece's base (feet), origin is bottom-centre
  scale?: number;
  flip?: boolean;
  /** true = a foreground piece drawn in front of the fighters */
  fg?: boolean;
  shadow?: boolean;
}

export interface ArenaLayout {
  /** [base, dark, light] top-down ground colours (procedural -- a calm,
   * intentional canvas; the detail comes from the kitbashed pieces). */
  groundColors: [number, number, number];
  /** warm accent for the central floor light-pool (the fight's focus). */
  pool?: number;
  pieces: Placement[];
}

/**
 * Draws a kitbashed arena: a calm PROCEDURAL top-down ground (never an AI
 * whole-scene image -- those read as busy concept art) plus hand-placed
 * environment pieces. Pieces sit BEHIND the fighters (depth < 4) unless
 * flagged `fg`, so the fight always reads.
 */
export function composeArena(scene: Phaser.Scene, layout: ArenaLayout): void {
  const [base, dark, light] = layout.groundColors;
  const g = scene.add.graphics().setDepth(-10);
  g.fillStyle(base, 1).fillRect(0, 0, BASE_WIDTH, BASE_HEIGHT);
  // deterministic ground texture: soft dark/light dapple so it isn't a flat fill
  let seed = 1337;
  const rnd = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
  for (let i = 0; i < 260; i++) {
    const x = Math.floor(rnd() * BASE_WIDTH);
    const y = Math.floor(rnd() * BASE_HEIGHT);
    const s = 1 + Math.floor(rnd() * 3);
    g.fillStyle(rnd() < 0.5 ? dark : light, 0.14 + rnd() * 0.16).fillRect(x, y, s, s);
  }
  // central walkable light-pool (the fight's focus)
  scene.add
    .image(BASE_WIDTH / 2, BASE_HEIGHT * 0.56, "glow")
    .setBlendMode(Phaser.BlendModes.ADD)
    .setTint(layout.pool ?? 0x2f5f86)
    .setScale(2.4)
    .setAlpha(0.16)
    .setDepth(-9.5);

  // atmospheric edge vignette for depth + to frame the play space
  const v = scene.add.graphics().setDepth(-9);
  const band = 22;
  v.fillStyle(0x05060a, 0.5);
  v.fillRect(0, 0, BASE_WIDTH, band).fillRect(0, BASE_HEIGHT - band, BASE_WIDTH, band);
  v.fillRect(0, 0, band, BASE_HEIGHT).fillRect(BASE_WIDTH - band, 0, band, BASE_HEIGHT);
  v.fillStyle(0x05060a, 0.25).fillRect(0, band, BASE_WIDTH, 10);

  for (const p of layout.pieces) {
    if (!scene.textures.exists(p.key)) continue;
    const s = p.scale ?? 1;
    if (p.shadow !== false) {
      scene.add.ellipse(p.x, p.y, 20 * s, 7 * s, 0x05060a, 0.4).setDepth(p.fg ? 8 : -8 + p.y / 1000);
    }
    scene.add
      .image(p.x, p.y, p.key)
      .setOrigin(0.5, 1)
      .setScale(s)
      .setFlipX(!!p.flip)
      .setDepth(p.fg ? 9 : 1 + p.y / 400);
  }
}

/**
 * The Shallows arena, hand-composed from the env/shallows kit. Pieces ring the
 * edges/top and a campfire save point sits in a corner; the centre stays open
 * for the fight (fighters spawn around x 90-230, y 30-150).
 */
export const ARENA_LAYOUTS: Record<string, ArenaLayout> = {
  arena_shallows: {
    groundColors: [0x123240, 0x0b2233, 0x1f6f77],
    pool: 0x2f7f8f,
    pieces: [
      { key: "env_shallows_boat", x: 62, y: 58, scale: 1 },
      { key: "env_shallows_pillar", x: 34, y: 118 },
      { key: "env_shallows_pillar", x: 292, y: 74, flip: true },
      { key: "env_shallows_rock_a", x: 26, y: 158 },
      { key: "env_shallows_rock_a", x: 300, y: 150, flip: true },
      { key: "env_shallows_rock_a", x: 256, y: 40 },
      { key: "env_shallows_rock_b", x: 104, y: 36 },
      { key: "env_shallows_rock_b", x: 205, y: 32 },
      { key: "env_shallows_reeds", x: 16, y: 86 },
      { key: "env_shallows_reeds", x: 305, y: 108, flip: true },
      { key: "env_shallows_reeds", x: 74, y: 172 },
      { key: "env_shallows_lantern", x: 272, y: 120 },
      { key: "env_shallows_campfire", x: 290, y: 172 }, // save point corner
    ],
  },
};
