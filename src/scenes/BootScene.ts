import Phaser from "phaser";
import { retinaCamera } from "../config/GameConfig";
import battleAbyssUrl from "../../assets/backgrounds/battle_abyss.png";
import titleUrl from "../../assets/backgrounds/bg_title.png";

// The band -- Inhalants (tools/pixelart/bandmates.py). Amir is the provided
// hand-drawn guitarist; the other three are authored to match. Every member
// ships three 48x48 strips: idle, run, attack. Loaded once here as
// `band_<member>` (idle) / `band_<member>_run` / `band_<member>_attack`.
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
import landmarksUrl from "../../assets/sprites/overworld/landmarks.png";
import slimeUrl from "../../assets/sprites/enemies/slime.png";
import drifterUrl from "../../assets/sprites/enemies/drifter.png";
import eliteWraithUrl from "../../assets/sprites/enemies/elite_wraith.png";
import conductorUrl from "../../assets/sprites/enemies/the_conductor.png";
import conductorColossalUrl from "../../assets/sprites/enemies/conductor_colossal.png";

// Regenerated foes (newfoes.py) ship 72x72 frames for legibility; the
// Conductor's small sheet is legacy 48x48 (his fights use the colossal sheet).
const ENEMY_URLS: Record<string, { url: string; frame: number }> = {
  // foe sheets baked to their fight size (bake_cast.py): render scale 1.0
  slime: { url: slimeUrl, frame: 32 },
  drifter: { url: drifterUrl, frame: 35 },
  elite_wraith: { url: eliteWraithUrl, frame: 45 },
  the_conductor: { url: conductorUrl, frame: 48 },
};

/** Loads the asset manifest and verifies browser support. See PRD §10.6. */
export class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  preload(): void {
    this.load.image("bg_battle_abyss", battleAbyssUrl);
    this.load.image("bg_title", titleUrl);
    // Native colossal boss art (PRD §11.1: authored at size, never upscaled).
    this.load.spritesheet("conductor_colossal", conductorColossalUrl, { frameWidth: 52, frameHeight: 72 });
    this.load.image("ui_panel", uiPanelUrl);
    this.load.image("ui_panel_boss", uiPanelBossUrl);
    this.load.image("wordmark", wordmarkUrl);
    this.load.image("ground_plate", groundPlateUrl);
    this.load.image("glow", glowUrl);
    this.load.image("spark", sparkUrl);
    // Overworld atmosphere: seamless drifting fog, raking god-ray shafts, and
    // one colossal set-piece landmark per region (30x40 frames).
    this.load.image("fx_haze", hazeUrl);
    this.load.image("fx_godray", godrayUrl);
    this.load.spritesheet("ow_landmarks", landmarksUrl, { frameWidth: 64, frameHeight: 80 });
    // Band sprites: `band_amir/idle.png` -> key `band_amir`; `.../run.png` ->
    // `band_amir_run`; `.../attack.png` -> `band_amir_attack`. All 72x72
    // (newband.py legibility pass).
    for (const [path, url] of Object.entries(BAND_URLS)) {
      const m = /band\/([^/]+)\/([^/]+)\.png$/.exec(path);
      if (!m) continue;
      const [, member, anim] = m;
      const key = anim === "idle" ? `band_${member}` : `band_${member}_${anim}`;
      // band strips baked to 50px frames (bake_cast.py: one pixel register)
      this.load.spritesheet(key, url, { frameWidth: 50, frameHeight: 50 });
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
