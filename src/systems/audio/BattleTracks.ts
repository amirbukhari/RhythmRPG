// Rendered chiptune battle tracks (PRD §11.2), produced from the committed
// tools/gbmusic .lsdsng drafts by tools/gbmusic/render_all_tracks.py. Each
// file is rendered at its beatmap's authored BPM and cut to an exact whole
// multiple of the beatmap's pattern loop length, so looping the buffer stays
// bar-aligned with the judgment grid indefinitely.
//
// Vite's `?url` import gives back the served asset URL; this module is the
// single place a beatmap trackId maps to an audio file. A trackId with no
// entry here simply has no rendered track yet -- BattleScene falls back to
// sonifier-only, which is also why this is a lookup function rather than a
// direct record access anywhere else.
import openingBiome01 from "../../../assets/audio/battle/opening_biome_01.ogg?url";
import midBiome101 from "../../../assets/audio/battle/mid_biome_1_01.ogg?url";
import midBiome2Clave01 from "../../../assets/audio/battle/mid_biome_2_clave_01.ogg?url";
import midBiome3Syncopated01 from "../../../assets/audio/battle/mid_biome_3_syncopated_01.ogg?url";
import bossConductorP1 from "../../../assets/audio/battle/boss_conductor_p1.ogg?url";
import bossConductorP2 from "../../../assets/audio/battle/boss_conductor_p2.ogg?url";
import bossConductorP3 from "../../../assets/audio/battle/boss_conductor_p3.ogg?url";

const TRACK_URLS: Record<string, string> = {
  opening_biome_01: openingBiome01,
  mid_biome_1_01: midBiome101,
  mid_biome_2_clave_01: midBiome2Clave01,
  mid_biome_3_syncopated_01: midBiome3Syncopated01,
  boss_conductor_p1: bossConductorP1,
  boss_conductor_p2: bossConductorP2,
  boss_conductor_p3: bossConductorP3,
};

export function battleTrackUrl(trackId: string): string | undefined {
  return TRACK_URLS[trackId];
}

export function knownBattleTrackIds(): string[] {
  return Object.keys(TRACK_URLS);
}
