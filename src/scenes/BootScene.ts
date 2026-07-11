import Phaser from "phaser";
import battleAbyssUrl from "../../assets/backgrounds/battle_abyss.png";
import battleConductorUrl from "../../assets/backgrounds/battle_conductor.png";
import warriorBattleUrl from "../../assets/sprites/heroes/warrior/side.png";
import tankBattleUrl from "../../assets/sprites/heroes/tank/side.png";
import mageBattleUrl from "../../assets/sprites/heroes/mage/side.png";
import healerBattleUrl from "../../assets/sprites/heroes/healer/side.png";
import slimeUrl from "../../assets/sprites/enemies/slime.png";
import drifterUrl from "../../assets/sprites/enemies/drifter.png";
import luchadorGruntUrl from "../../assets/sprites/enemies/luchador_grunt.png";
import luchadorMaskUrl from "../../assets/sprites/enemies/luchador_mask.png";
import eliteWraithUrl from "../../assets/sprites/enemies/elite_wraith.png";
import conductorUrl from "../../assets/sprites/enemies/the_conductor.png";

// All battle art (Skatopia pixel-art pipeline, tools/pixelart/) is loaded
// once here so every scene's texture manager has it. Heroes are 20x24
// 4-frame strips; enemies are 48x48 2-frame idle strips.
const HERO_BATTLE_URLS: Record<string, string> = {
  warrior: warriorBattleUrl,
  tank: tankBattleUrl,
  mage: mageBattleUrl,
  healer: healerBattleUrl,
};
const ENEMY_URLS: Record<string, string> = {
  slime: slimeUrl,
  drifter: drifterUrl,
  luchador_grunt: luchadorGruntUrl,
  luchador_mask: luchadorMaskUrl,
  elite_wraith: eliteWraithUrl,
  the_conductor: conductorUrl,
};

/** Loads the asset manifest and verifies browser support. See PRD §10.6. */
export class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  preload(): void {
    this.load.image("bg_battle_abyss", battleAbyssUrl);
    this.load.image("bg_battle_conductor", battleConductorUrl);
    for (const [role, url] of Object.entries(HERO_BATTLE_URLS)) {
      this.load.spritesheet(`hero_${role}`, url, { frameWidth: 20, frameHeight: 24 });
    }
    for (const [name, url] of Object.entries(ENEMY_URLS)) {
      this.load.spritesheet(`enemy_${name}`, url, { frameWidth: 48, frameHeight: 48 });
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
