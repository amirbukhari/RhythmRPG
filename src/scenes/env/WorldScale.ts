/**
 * ONE world unit (owner: "the scale of everything is totally wrong... why is
 * a chair bigger than a building"). Every environment piece was authored at
 * an ad-hoc "readable" pixel size across many generation batches, so relative
 * scale between pieces was noise. This table is the single source of truth:
 * real-world heights in METERS, anchored to the player (25px tall ~= 1.7m,
 * so ~15px per meter). The runtime computes each piece's render scale from
 * its texture height, so art regeneration can never break world scale again.
 *
 * Small items get a readability boost (a 0.2m goblet at true scale would be
 * 3px) with a hard floor; landforms keep their authored scale -- they are
 * deliberately monumental.
 */

const PX_PER_METER = 15;
const MIN_PX = 9;
const MAX_SCALE = 1.6;
const MIN_SCALE = 0.28;

/** First matching pattern wins. Height of the OBJECT as drawn (metres). */
const METERS: [RegExp, number][] = [
  // -- the Fold's town kit (tools/art/env_fold.py). First, because these are
  // exact keys and several looser patterns below would otherwise claim them
  // (`/scatter_lamp$/` and `/plinth/` in particular). Mir is 1.7m, so a 7m
  // house stands about four times his height -- a town, not a diorama.
  // The town obelisk: "a massive obelisk" (world-bible §2), and the tallest
  // thing in the Fold by a long way -- 9m is five Mirs.
  [/^env_fold_obelisk$/, 9.0],
  [/^env_fold_house_tall$/, 9.0],
  [/^env_fold_house_row$/, 6.5], // a terrace of three: 13m long to the eaves
  [/^env_fold_house_a$/, 7.0],
  [/^env_fold_house_b$/, 5.0],
  [/^env_fold_arch$/, 5.0],
  [/^env_fold_lamp$/, 2.6],
  [/^env_fold_shrine$/, 2.2],
  [/^env_fold_well$/, 1.9],
  [/^env_fold_cart$/, 1.3],
  [/^env_fold_crate_stack$/, 1.1],
  [/^env_fold_bench$/, 0.9],
  [/^env_fold_ring_stone$/, 0.45],
  // -- the Kelp Shelf's kit (tools/art/env_shelf.py). EXACT keys, and they have
  // to come before the loose patterns further down or the region collapses:
  // `/kelp|stone$|nodule/` would claim `kelp_stand` at 0.5m, `/rail/` would
  // claim `rail_bend` at 0.3m, and `/ladder/`, `/winch/` and `/ore_cart/` all
  // have looser entries below. A 14-metre shipwreck matched by a 0.5m pattern
  // ships at the size of a teacup, which is exactly the class of bug this whole
  // table was written to end.
  //
  // Every piece here is authored at ~30 px per metre so `worldScaleFor` lands
  // on 0.5 and the art downsamples once, through the renderer's own 4x
  // supersampling, instead of being resized twice. The declared metres only
  // have to put `target/texHeight` inside [0.25, 0.75) for that to hold, which
  // is a wide band -- so these are honest heights, not tuned ones.
  // These four were 14.0 / 11.5 / 10.0 / 8.0 and the numbers were honest -- a
  // ship's hull really is fourteen metres. They shipped a region the player
  // could not see: the scale floor is 0.5, so 14m at 30 px/m arrived as 226
  // world px, FOURTEEN TILES, in a viewport eleven tiles high. The prow was
  // permanently off-frame. The art is now authored at 2x and halved on the way
  // out (tools/art/env_shelf.py SHRINK), and the metres come down to match, so
  // a wreck towers over a one-tile man with its whole silhouette in the frame.
  [/^env_shelf_hull$/, 7.5], // ~7 tiles: still the tallest thing after the obelisk
  [/^env_shelf_mast$/, 6.0],
  [/^env_shelf_headframe$/, 6.0],
  [/^env_shelf_hull_broken$/, 4.5],
  [/^env_shelf_kelp_stand$/, 4.0],
  [/^env_shelf_shack$/, 3.4],
  [/^env_shelf_ribs$/, 2.4],
  [/^env_shelf_lantern$/, 2.2], // a miner's safety lamp: the Shelf's gate light
  [/^env_shelf_winch$/, 1.4],
  [/^env_shelf_ore_cart$/, 1.4],
  [/^env_shelf_plank_bridge$/, 1.2],
  [/^env_shelf_rail_bend$/, 0.9],
  // -- the Breach's kit (tools/art/env_breach.py). EXACT keys, and they MUST
  // sit above the loose patterns below or the region deflates: `/boat$/` claims
  // `swing_boat` at 1.4m (a four-tile fairground ride arriving the size of a
  // rowboat's dinghy), `/ticket_booth/` claims the kiosk at 3.2m, and
  // `/carousel_horse/` claims the horse at 2.2m -- all three of those patterns
  // were written for the retired cosmology's fairground and none of them knows
  // this art exists.
  //
  // The numbers are the authoring rule stated plainly: the art is drawn at 32 px
  // per intended tile, so `metres = tiles` always lands the world scale on its
  // 0.5 floor and the piece ships exactly as tall as it was composed to be.
  [/^env_breach_wheel$/, 9.0], // the stopped Ferris wheel: the region's landmark
  [/^env_breach_tent_pole$/, 5.5],
  [/^env_breach_carousel$/, 5.0],
  [/^env_breach_strength_tester$/, 4.5],
  [/^env_breach_swing_boat$/, 4.0],
  [/^env_breach_tent$/, 3.2],
  [/^env_breach_ticket_booth$/, 2.8],
  [/^env_breach_booth$/, 2.6],
  [/^env_breach_festoon_lamp$/, 2.2], // the gate light where the Shelf hands off
  [/^env_breach_bunting$/, 2.0],
  [/^env_breach_carousel_horse$/, 1.6],
  [/^env_breach_boardwalk$/, 0.8],

  // -- the Scar's kit (tools/art/env_scar.py). EXACT keys, above the loose
  // patterns, same rule as the two blocks above. The near-misses here are worth
  // naming because two of them are one character away from being wrong:
  // `/bones/` (0.3m) does NOT claim `bone_pile` only because it is plural, and
  // `/scatter_frame/` does not claim `dig_frame` only because it is anchored to
  // its prefix. Neither of those is a safety margin. They are luck, and the
  // exact keys below are what actually makes it safe.
  //
  // metres == tiles, because the kit is authored at 32 px per intended tile --
  // see the SIZE CONVENTION note in env_scar.py. Every number here is a tile
  // count, and the tallest is the burnt spar at six, which is one tile shy of
  // the Shelf's hull and deliberately so: the Scar's scale comes from how much
  // GROUND it covers, not from height. It is the long middle.
  [/^env_scar_burnt_spar$/, 6.0],
  [/^env_scar_den_mouth$/, 5.5], // §6.4's den. It is a mine adit and that is the point.
  [/^env_scar_dig_frame$/, 4.5],
  [/^env_scar_burnt_stand$/, 3.5],
  [/^env_scar_windlass$/, 3.0],
  [/^env_scar_oasis_shoot$/, 2.8], // the only thing in the game with a next week
  [/^env_scar_cairn$/, 2.6],
  [/^env_scar_spoil_heap$/, 1.6], // the most-repeated piece: "picked-over" is a count. 1.6 on a 48px canvas = the angle of repose; 2.4 on 76px was a 50deg mountain
  [/^env_scar_dig_lamp$/, 2.2],  // GATE_PROPS names this for region 3's entrance
  [/^env_scar_bone_pile$/, 2.0],
  [/^env_scar_barrow$/, 1.6],
  [/^env_scar_oasis_spring$/, 1.4],
  [/^env_scar_pilgrim_pack$/, 0.8], // lies flat on a 46x24 canvas; 1.4 sized it by air
  [/^env_scar_trench$/, 1.2],
  [/^env_scar_oasis_rill$/, 1.0], // the overflow. It is the seam that makes the Oasis one place.

  // -- the Keep's kit (tools/art/env_keep.py). EXACT keys, and this block has to
  // sit above the loose patterns for the same reason every other kit's does --
  // `/melting_clock/` and `/plinth/` and `/scatter_chandelier/` are all down
  // there, and `/chair/` at 0.5m would ship a concert hall furnished in doll
  // furniture. `stopped_clock` in particular is one regex away from being
  // claimed by the 2.5m `/melting_clock/` entry, which would be nearly right
  // and therefore the worst kind of wrong: nobody would notice.
  //
  // metres == tiles, because this kit is authored at 32 px per intended tile,
  // same convention as the Scar. Every number here is a tile count.
  //
  // THE PROSCENIUM IS THE TALLEST BUILT THING IN THE GAME and it is only six
  // tiles, in an eleven-tile viewport, because §6.5's hall has to be legible in
  // ONE camera. The Fold's obelisk is nine metres and it is a spire; a six-tile
  // arch that is seven and a half tiles WIDE fills a frame far more than either.
  [/^env_keep_proscenium$/, 6.0],
  [/^env_keep_organ_pipes$/, 5.5],
  [/^env_keep_pillar$/, 5.0],
  [/^env_keep_hall_door$/, 4.0],
  [/^env_keep_harp$/, 3.2], // the most expensive object in the game
  [/^env_keep_stopped_clock$/, 3.0], // and Mir is a clock-keeper. Never flipped.
  [/^env_keep_seat_bank$/, 2.8], // 6 tiles WIDE: the audience, and it is empty
  [/^env_keep_candelabra$/, 2.4], // GATE_PROPS names this for region 4's entrance
  [/^env_keep_chandelier_down$/, 2.0], // lowered for its candles, and never raised
  [/^env_keep_music_stand$/, 2.0],
  [/^env_keep_timpani$/, 1.9],
  [/^env_keep_cello$/, 1.6], // the one thing in the hall that is lying down
  [/^env_keep_chair_row$/, 1.6],
  [/^env_keep_chair$/, 1.4],
  [/^env_keep_podium$/, 0.8],
  [/^env_keep_sheet_drift$/, 0.8], // the hall's own weather

  // -- buildings & monuments (these were reading SMALLER than furniture) --
  [/ticket_booth/, 3.2],
  [/tent_pole/, 3.4],
  [/carousel_horse/, 2.2],
  [/melting_clock/, 2.5],
  [/save_obelisk/, 2.4],
  [/calcified_miner/, 1.9],
  [/figurehead/, 1.9],
  [/dockpost/, 2.4],
  [/_lantern$/, 2.2], // the Shelf's miner's lamp, and any lamp on a stake after it
  [/scatter_lantern/, 0.5], // the miner's HAND lantern
  [/_pillar$/, 2.4],
  [/scatter_pillar/, 1.6],
  [/_timber$/, 2.4],
  [/oil_lamp/, 1.8],
  [/torch/, 1.9],
  [/scatter_scale/, 1.9],
  [/scatter_flag$/, 2.0],
  [/pennant/, 2.0],
  [/chandelier$/, 2.0], // hall standing candelabra tower (venue kit)
  [/scatter_chandelier/, 0.8], // the FALLEN one
  [/candelabra/, 1.7],
  [/harpoon/, 1.7],
  [/scatter_sign/, 1.7],
  [/salt_crystal/, 1.8],
  [/plinth/, 1.6],
  [/piling/, 1.6],
  [/scatter_bell$/, 1.6],
  [/telescope/, 1.5],
  [/scatter_lamp$/, 1.4], // tiffany standing lamp
  [/ladder/, 2.0],
  [/beam/, 1.8],
  [/harp$/, 1.5],
  [/crate_stack/, 1.5],
  [/music_stand/, 1.4],
  [/ringpost/, 1.4],
  [/stand$/, 1.3],
  [/cello/, 1.4],
  [/ore_cart/, 1.3],
  [/scatter_cart/, 1.3],
  [/winch/, 1.3],
  [/reedclump|reeds$/, 1.25],
  [/drawers/, 1.3],
  [/stalagmite/, 1.4],
  [/crystal/, 1.4],
  [/boat$/, 1.4],
  [/cage$/, 1.2],
  [/birdcage$/, 1.1],
  [/umbrellas/, 1.1],
  [/brazier/, 1.1],
  [/rocking_chair/, 1.1],
  [/oar/, 1.3],
  [/anchor/, 1.3],
  [/skiff/, 1.0],
  [/stake/, 1.0],
  [/chair/, 1.0],
  [/poster/, 1.5],
  [/globe/, 1.0],
  [/phonograph|gramophone/, 0.95],
  [/portraits/, 1.0],
  [/net$/, 1.0],
  [/pew|bench/, 0.9],
  [/barrel/, 0.9],
  [/drum/, 0.9],
  [/keg/, 0.8],
  [/wheel/, 0.9],
  [/ore_rock/, 0.9],
  [/pick$/, 0.9],
  [/sewing/, 0.9],
  [/pipe$/, 0.9],
  [/scatter_frame/, 0.95],
  [/bust/, 0.85],
  [/rockinghorse/, 0.8],
  [/crate$|seacrate/, 0.8],
  [/campfire/, 0.75],
  [/lyre/, 0.7],
  [/trunk|seachest/, 0.7],
  [/marble/, 0.7],
  [/buoy|lifering/, 0.65],
  [/coral/, 0.6],
  [/plaque/, 0.7],
  [/violin/, 0.6],
  [/gear$/, 0.6],
  [/horn$/, 0.6],
  [/sacks/, 0.65],
  [/chest$/, 0.55],
  [/kelp|stone$|nodule/, 0.5],
  [/geode|radio|hatbox|clock$|tub$|belljar|shiplantern|drape|rubble/, 0.5],
  [/mirror|plank|driftwood|ore$|rope$|rope_coil|bucket|weights|jar$|hourglass|tidepool|books/, 0.42],
  [/metronome|quill|megaphone|doll|musicbox|typewriter|candles/, 0.35],
  [/mask|bottle|glove|chain|bones|rail|candle$|shells|streamer/, 0.3],
  [/goblet|votives|baton|sheets|page_stack|operamask|ticket$|starfish|crab|teacup/, 0.22],
];

/**
 * Render scale for an environment piece, from its canonical real height and
 * its texture height. Returns null for pieces outside the system (landforms,
 * unknown keys) -- callers keep their authored scale.
 */
export function worldScaleFor(key: string, texHeightPx: number): number | null {
  if (/landform_/.test(key) || texHeightPx <= 0) return null;
  let meters = 0.5; // unmatched keys default to small-prop scale, never huge
  for (const [re, m] of METERS) {
    if (re.test(key)) {
      meters = m;
      break;
    }
  }
  const boost = meters <= 0.5 ? 1.5 : meters <= 1 ? 1.15 : 1;
  const target = Math.max(MIN_PX, meters * PX_PER_METER * boost);
  const raw = Math.min(MAX_SCALE, Math.max(MIN_SCALE, target / texHeightPx));
  // art is baked to canonical size (bake_world_scale.py), so this lands at
  // ~1.0; snap to halves so texels stay integer-sized on the 2x canvas --
  // uniform chunky pixels, never fractional shimmer
  return Math.max(0.5, Math.round(raw * 2) / 2);
}
