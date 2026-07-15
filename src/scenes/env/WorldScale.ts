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
  // -- buildings & monuments (these were reading SMALLER than furniture) --
  [/ticket_booth/, 3.2],
  [/tent_pole/, 3.4],
  [/carousel_horse/, 2.2],
  [/melting_clock/, 2.5],
  [/save_obelisk/, 2.4],
  [/calcified_miner/, 1.9],
  [/figurehead/, 1.9],
  [/dockpost/, 2.4],
  [/_lantern$/, 2.2], // shallows standing lantern post
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
