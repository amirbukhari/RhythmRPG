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
  /** texture key, e.g. "env_shelf_hull" */
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

// There is no `arena_fold`, and there was one for an afternoon. Fight venues are
// keyed by BIOME and dressed at fight-node markers -- and the Fold contains no
// fight nodes at all: of the 22 markers in overworld.json, the only two inside
// region 0 are `spawn` and `town_obelisk`. That is canon, not an oversight (§6.1:
// the Fold is the one place the player "should like it here"), so the Fold's kit
// lives entirely in `dressing.json` and a fight layout for it would be art no
// player could ever reach.
//
// The per-node `NODE_VENUE` table was deleted with it: nothing had read it since
// venues became biome-keyed in v15.0, and it still mapped `opening_1` to a
// region-0 venue when that node stands in the Kelp Shelf.

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
  // The biome names are the world-bible's (fold/shelf/breach/scar/keep); the
  // retired ones (saltmines/pit/attic/hall) named a cosmology that is gone.
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
    if (/campfire|lantern|lamp|shrine/.test(p.key)) {
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
 * The authored fight venues, one per biome, kitbashed from `env/<biome>` kits.
 * Pieces ring the edges and the centre stays open for the fight (fighters spawn
 * around x 90-230, y 30-150). See the note above for why the Fold has none.
 */
export const ARENA_LAYOUTS: Record<string, ArenaLayout> = {
  // THE KELP SHELF. Every key here resolves -- which is worth saying, because
  // the table this replaced did not have a single one that did. It named
  // `env_saltmines_ore_rock`, `env_saltmines_salt_crystal`,
  // `env_saltmines_calcified_miner` and nine more from a kit that was never
  // built, and `composeWorldVenue` skips a piece whose texture is missing
  // (line ~77), so every fight in this region has been happening on a bare
  // floor since v15.0. The same was true of the three venues below.
  //
  // THE CENTRE IS EMPTY ON PURPOSE. Fighters spawn across x 90-230, y 30-150,
  // so nothing has a base inside that box: the wrecks are BACKDROP, ringing the
  // spot and towering over it (a hull is 226px tall in a 180px-high arena, and
  // that is the intended feeling -- you fight in the shadow of one).
  arena_shelf: {
    pieces: [
      { key: "env_shelf_hull", x: 28, y: 44 },
      { key: "env_shelf_hull", x: 298, y: 60, flip: true },
      { key: "env_shelf_mast", x: 252, y: 26 },
      { key: "env_shelf_hull_broken", x: 20, y: 88 },
      { key: "env_shelf_headframe", x: 68, y: 174 },
      { key: "env_shelf_shack", x: 274, y: 178, flip: true },
      { key: "env_shelf_ore_cart", x: 44, y: 120 },
      { key: "env_shelf_winch", x: 302, y: 134 },
      { key: "env_shelf_rail_bend", x: 152, y: 179 },
      { key: "env_shelf_plank_bridge", x: 58, y: 98 },
      { key: "env_shelf_kelp_stand", x: 16, y: 152 },
      { key: "env_shelf_kelp_stand", x: 32, y: 164 },
      { key: "env_shelf_kelp_stand", x: 314, y: 98 },
      { key: "env_shelf_ribs", x: 106, y: 26 },
      { key: "env_shelf_ribs", x: 216, y: 24, flip: true },
      // the two lamps are the only warm light in the venue, and they are the
      // reason the fight reads as happening at a WORKED place
      { key: "env_shelf_lantern", x: 96, y: 22 },
      { key: "env_shelf_lantern", x: 230, y: 20, flip: true },
      { key: "env_shared_save_obelisk", x: 30, y: 172 },
    ],
  },
  // The Breach's venue is the MIDWAY, not a fighting ring. The old layout here
  // dressed a pit -- torches at the corners, a drum, a bench, spectators implied
  // -- which belonged to a cosmology where region 2 was a place people fought
  // for sport. §6.3 says it is a carnival that kept performing after the water
  // came, and the pack that jumps him here is jumping him between the stalls.
  //
  // So: stalls on the flanks with their bulbs still lit, bunting over the top
  // AND the bottom of the frame so the fight reads as happening under it,
  // duckboards underfoot including one right through the middle where the
  // fighters stand, and the swing boat held off plumb at the west edge -- the
  // one thing in the venue that nothing else in it explains.
  arena_breach: {
    pieces: [
      { key: "env_breach_booth", x: 52, y: 56 },
      { key: "env_breach_booth", x: 274, y: 64, flip: true },
      { key: "env_breach_ticket_booth", x: 24, y: 100 },
      { key: "env_breach_tent", x: 300, y: 122, flip: true },
      { key: "env_breach_tent_pole", x: 96, y: 24 },
      { key: "env_breach_tent_pole", x: 232, y: 22, flip: true },
      { key: "env_breach_carousel", x: 264, y: 176, flip: true },
      { key: "env_breach_carousel_horse", x: 122, y: 174 },
      { key: "env_breach_strength_tester", x: 308, y: 42 },
      // the one wrong note: a pendulum held twenty degrees over
      { key: "env_breach_swing_boat", x: 62, y: 164 },
      { key: "env_breach_bunting", x: 160, y: 18 },
      { key: "env_breach_bunting", x: 158, y: 179 },
      // duckboards, and the middle one is UNDER the fight on purpose
      { key: "env_breach_boardwalk", x: 74, y: 132 },
      { key: "env_breach_boardwalk", x: 160, y: 152 },
      { key: "env_breach_boardwalk", x: 250, y: 140 },
      // the only warm light in the venue, and it is still working
      { key: "env_breach_festoon_lamp", x: 88, y: 44 },
      { key: "env_breach_festoon_lamp", x: 240, y: 42, flip: true },
      { key: "env_shared_save_obelisk", x: 30, y: 172 },
    ],
  },
  // The Scar's venue is DUG-OVER GROUND. The old layout here was an ATTIC --
  // drawers, a crate stack, a rocking chair, a birdcage, oil lamps -- furniture
  // from the retired cosmology, where region 3 was somebody's loft. §6.4 is
  // "gouged, burned, pitted, picked-over", and the fight that happens here
  // happens between the holes.
  //
  // NO `den_mouth` IN THE VENUE, and that is deliberate. There is exactly one
  // den in this region and it stands at the top of the col-288 road where the
  // road dead-ends (see tools/overworld/place_scar.py). Putting a second one at
  // every fight node would turn §6.4's landmark into wallpaper and spend the
  // reveal eleven times before the player reaches it.
  //
  // What the venue DOES carry is the evidence: four spoil heaps, a trench, a
  // windlass, a barrow, a dropped pack and a cairn. Every fight in the long
  // middle is fought standing in the proof, and the player will not read it
  // until §5.
  arena_scar: {
    pieces: [
      { key: "env_scar_burnt_spar", x: 86, y: 26 },
      { key: "env_scar_burnt_spar", x: 238, y: 22, flip: true },
      { key: "env_scar_burnt_stand", x: 28, y: 60 },
      { key: "env_scar_burnt_stand", x: 296, y: 66, flip: true },
      { key: "env_scar_spoil_heap", x: 52, y: 98 },
      { key: "env_scar_spoil_heap", x: 274, y: 104 },
      { key: "env_scar_spoil_heap", x: 66, y: 170 },
      { key: "env_scar_spoil_heap", x: 286, y: 174 },
      { key: "env_scar_trench", x: 152, y: 179 },
      { key: "env_scar_windlass", x: 306, y: 132 },
      { key: "env_scar_cairn", x: 22, y: 124 },
      { key: "env_scar_bone_pile", x: 116, y: 175 },
      { key: "env_scar_barrow", x: 206, y: 177, flip: true },
      { key: "env_scar_pilgrim_pack", x: 62, y: 142 },
      // the only warm light in the venue, and somebody is using it to look at
      // the ground -- see the dig_lamp docstring
      { key: "env_scar_dig_lamp", x: 96, y: 44 },
      { key: "env_scar_dig_lamp", x: 226, y: 48, flip: true },
      { key: "env_shared_save_obelisk", x: 30, y: 172 },
    ],
  },
  // THE LAST VENUE IN THE GAME, and every key in it was DEAD. Fourteen
  // `env_hall_*` pieces, and there is no `assets/sprites/env/hall/` directory in
  // this build -- so the boss arena, the one fight the whole campaign is walking
  // toward, has been composing itself out of fourteen texture keys that resolve
  // to nothing. `tsc` cannot see it (they are strings), the palette gate cannot
  // see it (it reads shipped PNGs, and there were none), and the arena still
  // rendered, just empty. The only thing that catches this class of bug is
  // looking at the room.
  //
  // §6.5: "an orchestra that drowned mid-performance -- beautiful, and NOBODY'S
  // story." So this arena is dressed as a HALL, not as a battlefield: nothing
  // overturned, nothing smashed, the instruments still on their stands, the
  // chairs square. The player fights Lunal in a room somebody was working in.
  //
  // AND THE PROSCENIUM IS BEHIND HER. It is the tallest built thing in the game
  // (six tiles) and it goes upstage centre, so the fight is framed by it -- the
  // one composition in the campaign where the arena has a focal point that is
  // not a combatant. The two candelabra flank the downstage edge, which puts the
  // only warm light in the venue between the player and the door they came in
  // by, and leaves her side of the room in the dark.
  arena_keep: {
    pieces: [
      { key: "env_keep_proscenium", x: 160, y: 30 },
      { key: "env_keep_pillar", x: 22, y: 52 },
      { key: "env_keep_pillar", x: 298, y: 58, flip: true },
      { key: "env_keep_organ_pipes", x: 268, y: 34 },
      // the orchestra, still on their stands
      { key: "env_keep_harp", x: 42, y: 104 },
      { key: "env_keep_cello", x: 286, y: 112, flip: true },
      { key: "env_keep_timpani", x: 62, y: 138 },
      { key: "env_keep_music_stand", x: 108, y: 128 },
      { key: "env_keep_music_stand", x: 208, y: 132, flip: true },
      { key: "env_keep_chair_row", x: 130, y: 152 },
      // the one chair that is on its own, downstage, facing the wrong way
      { key: "env_keep_chair", x: 244, y: 158, flip: true },
      { key: "env_keep_stopped_clock", x: 90, y: 62 },
      // the hall's own weather: paper the water pushed to the walls
      { key: "env_keep_sheet_drift", x: 30, y: 176 },
      { key: "env_keep_sheet_drift", x: 292, y: 180, flip: true },
      { key: "env_keep_sheet_drift", x: 176, y: 172 },
      // the only two lit things in the room, and they are behind the player
      { key: "env_keep_candelabra", x: 74, y: 170 },
      { key: "env_keep_candelabra", x: 250, y: 174, flip: true },
      { key: "env_shared_save_obelisk", x: 34, y: 172 },
    ],
  },
};
