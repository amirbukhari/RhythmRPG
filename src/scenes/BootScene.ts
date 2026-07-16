import Phaser from "phaser";
import { retinaCamera } from "../config/GameConfig";

// The playable character -- Mir (v10.0 solo pivot; tools/pixelart/newband.py).
// He ships three strips: idle, run, attack. Loaded once here as
// `band_mir` (idle) / `band_mir_run` / `band_mir_attack` (the `band_` key
// prefix is kept so nothing downstream churns).
const BAND_URLS = import.meta.glob("../../assets/sprites/band/*/*.png", {
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
import uiPanelUrl from "../../assets/ui/panel.png";
import wordmarkUrl from "../../assets/ui/wordmark.png";
import groundPlateUrl from "../../assets/tilemaps/ground_plate.png";
import uiPanelBossUrl from "../../assets/ui/panel_boss.png";
import glowUrl from "../../assets/fx/glow.png";
import sparkUrl from "../../assets/fx/spark.png";
import hazeUrl from "../../assets/fx/haze.png";
import godrayUrl from "../../assets/fx/godray.png";
import slimeUrl from "../../assets/sprites/enemies/slime.png";
import drifterUrl from "../../assets/sprites/enemies/drifter.png";
import eliteWraithUrl from "../../assets/sprites/enemies/elite_wraith.png";
import conductorUrl from "../../assets/sprites/enemies/the_conductor.png";
import conductorColossalUrl from "../../assets/sprites/enemies/conductor_colossal.png";

// HD painterly foes (hd_cast.py, v11.0) ship 4x frames, rendered at 0.25; the
// Conductor's small sheet is legacy 48x48 (his fights use the colossal sheet).
const ENEMY_URLS: Record<string, { url: string; frame: number }> = {
  // HD frames at 4x the world size (hd_cast.py): render scale 0.25
  slime: { url: slimeUrl, frame: 128 },
  drifter: { url: drifterUrl, frame: 140 },
  elite_wraith: { url: eliteWraithUrl, frame: 180 },
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
    this.load.image("ground_plate", groundPlateUrl);
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
      // HD painterly strips: 200px frames (hd_cast.py), rendered at 0.125
      this.load.spritesheet(key, url, { frameWidth: 200, frameHeight: 200 });
    }
    // Environment kitbash pieces: `.../env/shallows/rock_a.png` -> env_shallows_rock_a
    for (const [path, url] of Object.entries(ENV_URLS)) {
      const m = /env\/([^/]+)\/([^/]+)\.png$/.exec(path);
      if (m) this.load.image(`env_${m[1]}_${m[2]}`, url);
    }
    for (const [name, spec] of Object.entries(ENEMY_URLS)) {
      this.load.spritesheet(`enemy_${name}`, spec.url, { frameWidth: spec.frame, frameHeight: spec.frame });
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
