import Phaser from "phaser";
import { retinaCamera } from "../config/GameConfig";

// The cast -- authored on the 2D rig in `tools/art/` (v16.3). Mir ships nine
// strips (idle/run/attack/heavy/dash/parry/hurt/down/pick) and Nari five
// (idle/run/reach/sit/hide); every foe ships the six states §11.5 asks for.
// Loaded once here as `band_mir` (idle) / `band_mir_<state>` (the `band_` key
// prefix is kept so nothing downstream churns).
const BAND_URLS = import.meta.glob("../../assets/sprites/band/*/*.png", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

// Foes ship one directory per foe: `enemies/slime/telegraph.png`. The old flat
// `enemies/slime.png` was a single frame that the engine faked five states out
// of with scale tweens, which is why a fight read as two blobs pulsing.
const ENEMY_STATE_URLS = import.meta.glob("../../assets/sprites/enemies/*/*.png", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

// Kitbash environment pieces (PRD §11.1): assets/sprites/env/<biome>/<piece>.png
// -> texture key `env_<biome>_<piece>` (used by ArenaComposer).
const ENV_URLS = import.meta.glob("../../assets/sprites/env/*/*.png", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;
// v15.0: the ~10x world's painted ground ships as a GRID of chunk PNGs
// (tools/overworld/paint_ground.py) -- one texture would exceed WebGL's max
// size. Loaded here as `ground_chunk_<r>_<c>`; OverworldScene places + culls them.
const GROUND_CHUNK_URLS = import.meta.glob("../../assets/tilemaps/ground_plate_*_*.png", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;
import uiPanelUrl from "../../assets/ui/panel.png";
import wordmarkUrl from "../../assets/ui/wordmark.png";
import uiPanelBossUrl from "../../assets/ui/panel_boss.png";
import glowUrl from "../../assets/fx/glow.png";
import sparkUrl from "../../assets/fx/spark.png";
import hazeUrl from "../../assets/fx/haze.png";
import godrayUrl from "../../assets/fx/godray.png";
import conductorUrl from "../../assets/sprites/enemies/the_conductor.png";
import conductorColossalUrl from "../../assets/sprites/enemies/conductor_colossal.png";

// Authored frame size per foe -- must match `tools/art/contract.py` SCALE.
// Everything renders at 0.25, so these are 4x their world size.
const ENEMY_FRAME: Record<string, number> = {
  slime: 128,
  drifter: 140,
  elite_wraith: 180,
};
// The Conductor is retired canon (world-bible v16.0 replaced him with the
// Harrow) and still has only a legacy flat sheet; his slots go with the §8.7
// finale rework.
const LEGACY_ENEMY_URLS: Record<string, { url: string; frame: number }> = {
  the_conductor: { url: conductorUrl, frame: 192 },
};

/** Loads the asset manifest and verifies browser support. See PRD §10.6. */
export class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  preload(): void {
    // Colossal boss art at 4x density (hd_cast.py), rendered at 0.25.
    this.load.spritesheet("conductor_colossal", conductorColossalUrl, { frameWidth: 208, frameHeight: 288 });
    this.load.image("ui_panel", uiPanelUrl);
    this.load.image("ui_panel_boss", uiPanelBossUrl);
    this.load.image("wordmark", wordmarkUrl);
    // Ground chunks: `.../ground_plate_2_3.png` -> key `ground_chunk_2_3`.
    for (const [path, url] of Object.entries(GROUND_CHUNK_URLS)) {
      const m = /ground_plate_(\d+)_(\d+)\.png$/.exec(path);
      if (m) this.load.image(`ground_chunk_${m[1]}_${m[2]}`, url);
    }
    this.load.image("glow", glowUrl);
    this.load.image("spark", sparkUrl);
    // Overworld atmosphere: seamless drifting fog, raking god-ray shafts, and
    this.load.image("fx_haze", hazeUrl);
    this.load.image("fx_godray", godrayUrl);
    // Cast sprites: `band/mir/idle.png` -> key `band_mir`; `.../run.png` ->
    // `band_mir_run`; `.../attack.png` -> `band_mir_attack`.
    for (const [path, url] of Object.entries(BAND_URLS)) {
      const m = /band\/([^/]+)\/([^/]+)\.png$/.exec(path);
      if (!m) continue;
      const [, member, anim] = m;
      const key = anim === "idle" ? `band_${member}` : `band_${member}_${anim}`;
      // Authored rig strips: 200px frames (tools/art/contract.py), at 0.125
      this.load.spritesheet(key, url, { frameWidth: 200, frameHeight: 200 });
    }
    // Environment kitbash pieces: `.../env/shallows/rock_a.png` -> env_shallows_rock_a
    for (const [path, url] of Object.entries(ENV_URLS)) {
      const m = /env\/([^/]+)\/([^/]+)\.png$/.exec(path);
      if (m) this.load.image(`env_${m[1]}_${m[2]}`, url);
    }
    for (const [name, spec] of Object.entries(LEGACY_ENEMY_URLS)) {
      this.load.spritesheet(`enemy_${name}`, spec.url, { frameWidth: spec.frame, frameHeight: spec.frame });
    }
    // Foe states: `.../enemies/slime/telegraph.png` -> `enemy_slime_telegraph`;
    // `idle` keeps the bare `enemy_slime` key so existing call sites hold.
    for (const [path, url] of Object.entries(ENEMY_STATE_URLS)) {
      const m = /enemies\/([^/]+)\/([^/]+)\.png$/.exec(path);
      if (!m) continue;
      const [, foe, state] = m;
      const frame = ENEMY_FRAME[foe];
      if (!frame) continue;
      const key = state === "idle" ? `enemy_${foe}` : `enemy_${foe}_${state}`;
      this.load.spritesheet(key, url, { frameWidth: frame, frameHeight: frame });
    }
  }

  create(): void {
    retinaCamera(this);
    const hasWebAudio = typeof window !== "undefined" && ("AudioContext" in window || "webkitAudioContext" in window);
    if (!hasWebAudio) {
      this.add
        .text(160, 90, "This browser does not support Web Audio.\nPlease use a current Chrome, Edge, Firefox, or Safari.", {
          fontFamily: "monospace",
          fontSize: "8px",
          color: "#ff5555",
          align: "center",
          wordWrap: { width: 300 },
        })
        .setOrigin(0.5);
      return;
    }
    this.scene.start("AudioGateScene");
  }
}
