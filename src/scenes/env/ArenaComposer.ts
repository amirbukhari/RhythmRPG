import Phaser from "phaser";
import { BASE_WIDTH, BASE_HEIGHT } from "../../config/GameConfig";
import { worldScaleFor } from "./WorldScale";

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
  pieces: Placement[];
}

// Which authored venue dresses each fight node's spot IN the world.
export const NODE_VENUE: Record<string, string> = {
  opening_1: "arena_shallows",
  mid_1: "arena_saltmines",
  mid_2: "arena_pit",
  mid_3: "arena_attic",
  boss_1: "arena_hall",
};

/**
 * Dresses a fight node's spot IN the overworld with its authored venue
 * (owner: "what happened to the terrains you made for the boss fights? I
 * just wanted you to put those in the world"): the biome floor is painted
 * as an edge-faded patch blended into the surrounding map, and the kitbash
 * set pieces stand around the spot in world space. The fight then happens
 * on this exact ground (WorldFight locks its room here).
 */
export function composeWorldVenue(
  scene: Phaser.Scene,
  venueKey: string,
  cx: number,
  cy: number,
  canPlace?: (x: number, y: number) => boolean
): void {
  // v15.0: venues are keyed by BIOME ("arena_<biome>"), so all ~20 fight nodes
  // reuse the five authored kits (was a per-node-id table for the old 5 nodes).
  // focal stage-light: every fight reads as a lit stage from across the map,
  // even where the kit's set pieces have no shipped art yet.
  scene.add
    .image(cx, cy, "glow")
    .setBlendMode(Phaser.BlendModes.ADD)
    .setTint(0xf0c078)
    .setScale(1.5)
    .setAlpha(0.12)
    .setDepth(1.4);
  const layout = ARENA_LAYOUTS[venueKey];
  if (!layout) return;
  // NO floor patch: the venue is its SET PIECES standing on the real painted
  // ground; the world itself is the arena floor.
  // kit pieces, offset from the layout's arena space onto the node's spot
  const ox = cx - BASE_WIDTH / 2;
  const oy = cy - BASE_HEIGHT * 0.56;
  for (const p of layout.pieces) {
    if (/save_obelisk/.test(p.key)) continue; // the overworld places its own
    if (!scene.textures.exists(p.key)) continue;
    if (canPlace && !canPlace(ox + p.x, oy + p.y)) continue; // no props in the lake
    // canonical world scale (one unit everywhere); authored*0.55 only as fallback
    const s = worldScaleFor(p.key, scene.textures.get(p.key).getSourceImage().height) ?? (p.scale ?? 1) * 0.55;
    const px = ox + p.x;
    const py = oy + p.y;
    if (p.shadow !== false) scene.add.ellipse(px, py, 20 * s, 6 * s, 0x05060a, 0.35).setDepth(2.4);
    if (/campfire|lantern|lamp/.test(p.key)) {
      scene.add
        .image(px, py - 6, "glow")
        .setBlendMode(Phaser.BlendModes.ADD)
        .setTint(0xf0a648)
        .setScale(0.35)
        .setAlpha(0.45)
        .setDepth(2.6);
    }
    scene.add.image(px, py, p.key).setOrigin(0.5, 1).setScale(s).setFlipX(!!p.flip).setDepth(2.5 + py / 100000);
  }
}

/**
 * The Shallows arena, hand-composed from the env/shallows kit. Pieces ring the
 * edges/top and a campfire save point sits in a corner; the centre stays open
 * for the fight (fighters spawn around x 90-230, y 30-150).
 */
export const ARENA_LAYOUTS: Record<string, ArenaLayout> = {
  arena_shallows: {
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
      // scatter-kit dressing (design-audit-3: venues read sparse)
      { key: "env_shallows_scatter_anchor", x: 148, y: 174 },
      { key: "env_shallows_scatter_skiff", x: 208, y: 176 },
      { key: "env_shallows_scatter_piling", x: 12, y: 62 },
      { key: "env_shallows_scatter_buoy", x: 310, y: 42 },
    ],
  },
  arena_saltmines: {
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
      { key: "env_saltmines_scatter_brazier", x: 150, y: 30 },
      { key: "env_saltmines_scatter_geode", x: 306, y: 108 },
      { key: "env_saltmines_scatter_sacks", x: 66, y: 172 },
      { key: "env_saltmines_scatter_rail", x: 184, y: 176 },
    ],
  },
  arena_pit: {
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
      // ring corners: the pit is a fighting ring (§8.6 pit pack flavour)
      { key: "env_pit_scatter_torch", x: 86, y: 52 },
      { key: "env_pit_scatter_torch", x: 234, y: 52, flip: true },
      { key: "env_pit_scatter_drum", x: 308, y: 172 },
      { key: "env_pit_scatter_bench", x: 150, y: 178 },
    ],
  },
  arena_attic: {
    pieces: [
      { key: "env_attic_drawers", x: 58, y: 60 },
      { key: "env_attic_crate_stack", x: 286, y: 74, flip: true },
      { key: "env_attic_rocking_chair", x: 36, y: 120 },
      { key: "env_attic_birdcage", x: 300, y: 130 },
      { key: "env_attic_crate_stack", x: 26, y: 162 },
      { key: "env_attic_oil_lamp", x: 108, y: 36 },
      { key: "env_attic_oil_lamp", x: 272, y: 122 },
      { key: "env_shared_save_obelisk", x: 30, y: 172 },
      { key: "env_attic_scatter_lamp", x: 150, y: 32 },
      { key: "env_attic_scatter_trunk", x: 308, y: 170 },
      { key: "env_attic_scatter_rockinghorse", x: 224, y: 174 },
      { key: "env_attic_scatter_radio", x: 12, y: 128 },
    ],
  },
  arena_hall: {
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
      // the boss hall read sparse (design-audit-3): fallen finery rings it
      { key: "env_hall_scatter_chandelier", x: 150, y: 176 },
      { key: "env_hall_scatter_bust", x: 108, y: 34 },
      { key: "env_hall_scatter_cello", x: 310, y: 96 },
      { key: "env_hall_scatter_harp", x: 14, y: 128 },
      { key: "env_hall_scatter_candelabra", x: 222, y: 30 },
    ],
  },
};
