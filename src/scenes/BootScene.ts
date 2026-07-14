import Phaser from "phaser";
import battleAbyssUrl from "../../assets/backgrounds/battle_abyss.png";
import titleUrl from "../../assets/backgrounds/bg_title.png";
import battleConductorUrl from "../../assets/backgrounds/battle_conductor.png";
import causticsUrl from "../../assets/backgrounds/caustics.png";
import arenaShallowsUrl from "../../assets/backgrounds/arena_shallows.png";
import arenaSaltminesUrl from "../../assets/backgrounds/arena_saltmines.png";
import arenaPitUrl from "../../assets/backgrounds/arena_pit.png";
import arenaAtticUrl from "../../assets/backgrounds/arena_attic.png";
import arenaHallUrl from "../../assets/backgrounds/arena_hall.png";

// One authored arena per campaign movement (PRD §11.1.1) -- each a specific
// place with an untold story staged in its set pieces.
const ARENA_URLS: Record<string, string> = {
  arena_shallows: arenaShallowsUrl,
  arena_saltmines: arenaSaltminesUrl,
  arena_pit: arenaPitUrl,
  arena_attic: arenaAtticUrl,
  arena_hall: arenaHallUrl,
};

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
import uiPanelBossUrl from "../../assets/ui/panel_boss.png";
import uiIconsUrl from "../../assets/ui/icons.png";
import glowUrl from "../../assets/fx/glow.png";
import sparkUrl from "../../assets/fx/spark.png";
import hazeUrl from "../../assets/fx/haze.png";
import godrayUrl from "../../assets/fx/godray.png";
import landmarksUrl from "../../assets/sprites/overworld/landmarks.png";
import warriorBattleUrl from "../../assets/sprites/heroes/warrior/side.png";
import tankBattleUrl from "../../assets/sprites/heroes/tank/side.png";
import mageBattleUrl from "../../assets/sprites/heroes/mage/side.png";
import healerBattleUrl from "../../assets/sprites/heroes/healer/side.png";
import slimeUrl from "../../assets/sprites/enemies/slime.png";
import drifterUrl from "../../assets/sprites/enemies/drifter.png";
import eliteWraithUrl from "../../assets/sprites/enemies/elite_wraith.png";
import conductorUrl from "../../assets/sprites/enemies/the_conductor.png";
import conductorColossalUrl from "../../assets/sprites/enemies/conductor_colossal.png";
import warriorAttackUrl from "../../assets/sprites/heroes/warrior/attack.png";

// All battle art (Skatopia pixel-art pipeline, tools/pixelart/) is loaded
// once here so every scene's texture manager has it. Heroes are 20x24
// 4-frame strips; enemies are 48x48 2-frame idle strips.
const HERO_BATTLE_URLS: Record<string, string> = {
  warrior: warriorBattleUrl,
  tank: tankBattleUrl,
  mage: mageBattleUrl,
  healer: healerBattleUrl,
};
// Regenerated foes (newfoes.py) ship 72x72 frames for legibility; the
// Conductor's small sheet is legacy 48x48 (his fights use the colossal sheet).
const ENEMY_URLS: Record<string, { url: string; frame: number }> = {
  slime: { url: slimeUrl, frame: 72 },
  drifter: { url: drifterUrl, frame: 72 },
  elite_wraith: { url: eliteWraithUrl, frame: 72 },
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
    this.load.image("bg_battle_conductor", battleConductorUrl);
    this.load.image("caustics", causticsUrl);
    for (const [key, url] of Object.entries(ARENA_URLS)) this.load.image(key, url);
    // Native colossal boss art (PRD §11.1: authored at size, never upscaled)
    // and the playable lead's authored attack poses (windup -> swing).
    this.load.spritesheet("conductor_colossal", conductorColossalUrl, { frameWidth: 52, frameHeight: 72 });
    this.load.spritesheet("hero_warrior_attack", warriorAttackUrl, { frameWidth: 24, frameHeight: 24 });
    this.load.image("ui_panel", uiPanelUrl);
    this.load.image("ui_panel_boss", uiPanelBossUrl);
    this.load.image("wordmark", wordmarkUrl);
    this.load.spritesheet("ui_icons", uiIconsUrl, { frameWidth: 10, frameHeight: 10 });
    this.load.image("glow", glowUrl);
    this.load.image("spark", sparkUrl);
    // Overworld atmosphere: seamless drifting fog, raking god-ray shafts, and
    // one colossal set-piece landmark per region (30x40 frames).
    this.load.image("fx_haze", hazeUrl);
    this.load.image("fx_godray", godrayUrl);
    this.load.spritesheet("ow_landmarks", landmarksUrl, { frameWidth: 64, frameHeight: 80 });
    for (const [role, url] of Object.entries(HERO_BATTLE_URLS)) {
      this.load.spritesheet(`hero_${role}`, url, { frameWidth: 20, frameHeight: 24 });
    }
    // Band sprites: `band_amir/idle.png` -> key `band_amir`; `.../run.png` ->
    // `band_amir_run`; `.../attack.png` -> `band_amir_attack`. All 72x72
    // (newband.py legibility pass).
    for (const [path, url] of Object.entries(BAND_URLS)) {
      const m = /band\/([^/]+)\/([^/]+)\.png$/.exec(path);
      if (!m) continue;
      const [, member, anim] = m;
      const key = anim === "idle" ? `band_${member}` : `band_${member}_${anim}`;
      this.load.spritesheet(key, url, { frameWidth: 72, frameHeight: 72 });
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
