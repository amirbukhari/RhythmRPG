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
  /** which designed floor motif to draw (AAA audit B1: no void floors). */
  motif: "sand" | "planks" | "dust" | "boards" | "marble";
  pieces: Placement[];
}

/**
 * Draws a DESIGNED per-biome floor into a canvas texture (AAA audit B1): the
 * old flat fill + invisible dapple read as a void. Layers: low-frequency tone
 * blotches -> biome motif (wet-sand ripples, mine planks, circus dust rings,
 * attic boards, marble checker) -> speckle -> radial centre light + edge
 * falloff. Deterministic per arena key.
 */
function paintFloor(scene: Phaser.Scene, key: string, layout: ArenaLayout): string {
  const texKey = `floor_${key}`;
  if (scene.textures.exists(texKey)) return texKey;
  const W = BASE_WIDTH;
  const H = BASE_HEIGHT;
  const tex = scene.textures.createCanvas(texKey, W, H)!;
  const ctx = tex.getContext();
  const img = ctx.createImageData(W, H);
  const d = img.data;

  let seed = 0;
  for (const ch of key) seed = (seed * 31 + ch.charCodeAt(0)) & 0x7fffffff;
  const rnd = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);

  const [base, dark, light] = layout.groundColors;
  const toRgb = (c: number) => [(c >> 16) & 255, (c >> 8) & 255, c & 255] as const;
  const [br, bg, bb] = toRgb(base);
  const [dr, dg, db] = toRgb(dark);
  const [lr, lg, lb] = toRgb(light);

  // low-frequency blotches: a handful of big soft tone shifts
  const blobs = Array.from({ length: 14 }, () => ({
    x: rnd() * W,
    y: rnd() * H,
    r: 26 + rnd() * 52,
    t: (rnd() - 0.5) * 0.5,
  }));

  const cx = W / 2;
  const cy = H * 0.56;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      // tone t in [-1, 1]: -1 = dark colour, +1 = light colour
      let t = 0;
      for (const b of blobs) {
        const dx = x - b.x;
        const dy = y - b.y;
        const q = 1 - (dx * dx + dy * dy) / (b.r * b.r);
        if (q > 0) t += b.t * q;
      }
      // biome motif
      switch (layout.motif) {
        case "sand": {
          // tide-ripple bands drifting with x
          const w1 = Math.sin(y * 0.55 + Math.sin(x * 0.045) * 2.2);
          if (w1 > 0.86) t += 0.22;
          break;
        }
        case "planks": {
          // vertical mine boards with seams + grain
          const px = (x + ((x / 26) | 0) * 7) % 26;
          if (px < 1.2) t -= 0.5;
          else t += Math.sin(y * 0.22 + ((x / 26) | 0) * 3.1) * 0.05;
          break;
        }
        case "dust": {
          // trampled fighting-ring circles around the centre
          const rr = Math.hypot(x - cx, y - cy);
          const ring = Math.abs((rr % 34) - 17);
          if (ring < 1.1 && rr > 20 && rr < 120) t -= 0.28;
          break;
        }
        case "boards": {
          // horizontal attic floorboards, staggered ends, wood grain
          const row = (y / 12) | 0;
          const py = y % 12;
          if (py < 1) t -= 0.5;
          else {
            const off = (row * 53) % 64;
            if ((x + off) % 64 < 1) t -= 0.4; // board end seam
            t += Math.sin(x * 0.18 + row * 2.7) * 0.06;
          }
          break;
        }
        case "marble": {
          // grand-hall checker + faint veins
          const cxk = ((x / 24) | 0) + ((y / 24) | 0);
          t += cxk % 2 === 0 ? 0.1 : -0.12;
          const vein = Math.sin(x * 0.12 + Math.sin(y * 0.07) * 3.5);
          if (vein > 0.965) t += 0.3;
          break;
        }
      }
      // fine speckle
      t += (rnd() - 0.5) * 0.16;

      // radial fight-light + edge falloff
      const dcx = (x - cx) / (W * 0.62);
      const dcy = (y - cy) / (H * 0.72);
      const rad = Math.sqrt(dcx * dcx + dcy * dcy);
      const lightBoost = Math.max(0, 1 - rad) * 0.24;
      const edge = Math.min(1, Math.max(0, (rad - 0.72) * 2.2)) * 0.5;

      let r: number, g: number, b: number;
      if (t >= 0) {
        r = br + (lr - br) * Math.min(1, t);
        g = bg + (lg - bg) * Math.min(1, t);
        b = bb + (lb - bb) * Math.min(1, t);
      } else {
        r = br + (dr - br) * Math.min(1, -t);
        g = bg + (dg - bg) * Math.min(1, -t);
        b = bb + (db - bb) * Math.min(1, -t);
      }
      const m = 1 + lightBoost - edge;
      const i = (y * W + x) * 4;
      d[i] = Math.max(0, Math.min(255, r * m));
      d[i + 1] = Math.max(0, Math.min(255, g * m));
      d[i + 2] = Math.max(0, Math.min(255, b * m));
      d[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  tex.refresh();
  return texKey;
}

/**
 * Draws a kitbashed arena: a calm PROCEDURAL top-down ground (never an AI
 * whole-scene image -- those read as busy concept art) plus hand-placed
 * environment pieces. Pieces sit BEHIND the fighters (depth < 4) unless
 * flagged `fg`, so the fight always reads.
 */
export function composeArena(scene: Phaser.Scene, layout: ArenaLayout, key = "arena"): void {
  // designed per-biome floor (AAA audit B1) -- never a flat void
  const floorKey = paintFloor(scene, key, layout);
  scene.add.image(0, 0, floorKey).setOrigin(0, 0).setDepth(-10);
  // central walkable light-pool (the fight's focus)
  scene.add
    .image(BASE_WIDTH / 2, BASE_HEIGHT * 0.56, "glow")
    .setBlendMode(Phaser.BlendModes.ADD)
    .setTint(layout.pool ?? 0x2f5f86)
    .setScale(2.4)
    .setAlpha(0.14)
    .setDepth(-9.5);

  for (const p of layout.pieces) {
    if (!scene.textures.exists(p.key)) continue;
    const s = p.scale ?? 1;
    if (p.shadow !== false) {
      scene.add.ellipse(p.x, p.y, 20 * s, 7 * s, 0x05060a, 0.4).setDepth(p.fg ? 8 : -8 + p.y / 1000);
    }
    // save points (campfire / obelisk) and lanterns get a warm/teal glow
    if (/campfire|obelisk|lantern|lamp/.test(p.key)) {
      const teal = /obelisk/.test(p.key);
      scene.add
        .image(p.x, p.y - 8 * s, "glow")
        .setBlendMode(Phaser.BlendModes.ADD)
        .setTint(teal ? 0x49c6bd : 0xf0a648)
        .setScale(0.5 * s)
        .setAlpha(0.5)
        .setDepth(2);
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
    motif: "sand",
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
      { key: "env_shared_save_obelisk", x: 30, y: 172 }, // save point (§8.8)
      { key: "env_shallows_campfire", x: 290, y: 172 },
    ],
  },
  arena_saltmines: {
    motif: "planks",
    groundColors: [0x2a1e0f, 0x140d05, 0x6e3316],
    pool: 0xf0a648,
    pieces: [
      { key: "env_saltmines_ore_cart", x: 60, y: 62 },
      { key: "env_saltmines_timber", x: 40, y: 120 },
      { key: "env_saltmines_timber", x: 288, y: 72, flip: true },
      { key: "env_saltmines_salt_crystal", x: 106, y: 36 },
      { key: "env_saltmines_salt_crystal", x: 300, y: 150 },
      { key: "env_saltmines_ore_rock", x: 26, y: 158 },
      { key: "env_saltmines_ore_rock", x: 210, y: 34, flip: true },
      { key: "env_saltmines_calcified_miner", x: 272, y: 120 },
      { key: "env_shared_save_obelisk", x: 30, y: 172 },
    ],
  },
  arena_pit: {
    motif: "dust",
    groundColors: [0x241432, 0x120a1c, 0x4b2a57],
    pool: 0xb98fca,
    pieces: [
      { key: "env_pit_ticket_booth", x: 58, y: 60 },
      { key: "env_pit_carousel_horse", x: 282, y: 72, flip: true },
      { key: "env_pit_tent_pole", x: 34, y: 118 },
      { key: "env_pit_plum_rubble", x: 26, y: 160 },
      { key: "env_pit_plum_rubble", x: 300, y: 150, flip: true },
      { key: "env_pit_rope_coil", x: 108, y: 36 },
      { key: "env_pit_rope_coil", x: 205, y: 34 },
      { key: "env_pit_tent_pole", x: 274, y: 128, flip: true },
      { key: "env_shared_save_obelisk", x: 30, y: 172 },
    ],
  },
  arena_attic: {
    motif: "boards",
    groundColors: [0x241a12, 0x120b06, 0x6e3316],
    pool: 0xe07030,
    pieces: [
      { key: "env_attic_drawers", x: 58, y: 60 },
      { key: "env_attic_crate_stack", x: 286, y: 74, flip: true },
      { key: "env_attic_rocking_chair", x: 36, y: 120 },
      { key: "env_attic_birdcage", x: 300, y: 130 },
      { key: "env_attic_crate_stack", x: 26, y: 162 },
      { key: "env_attic_oil_lamp", x: 108, y: 36 },
      { key: "env_attic_oil_lamp", x: 272, y: 122 },
      { key: "env_shared_save_obelisk", x: 30, y: 172 },
    ],
  },
  arena_hall: {
    motif: "marble",
    groundColors: [0x141026, 0x0a0716, 0x3a2450],
    pool: 0x8a52a0,
    pieces: [
      { key: "env_hall_plinth", x: 58, y: 60 },
      { key: "env_hall_plinth", x: 286, y: 68, flip: true },
      { key: "env_hall_melting_clock", x: 36, y: 122 },
      { key: "env_hall_music_stand", x: 300, y: 128 },
      { key: "env_hall_chandelier", x: 150, y: 34 },
      { key: "env_hall_page_stack", x: 26, y: 162 },
      { key: "env_hall_page_stack", x: 288, y: 168, flip: true },
      { key: "env_hall_music_stand", x: 274, y: 120 },
      { key: "env_shared_save_obelisk", x: 34, y: 172 },
    ],
  },
};
