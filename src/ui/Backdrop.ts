import Phaser from "phaser";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";

/**
 * Shared moody backdrop for the menu/flow scenes so the whole game sits in
 * one world instead of the battlefield being beautiful and everything else
 * being text-on-black. Draws the title key-art dimmed, with a vignette —
 * the same painterly-ink register as the world (the old smooth-gradient
 * battle_abyss was the last pre-pipeline art a player could see; art
 * cohesion audit C1). Cheap, static, and safe to call from any scene once
 * BootScene has loaded "bg_title".
 */
export function addBackdrop(scene: Phaser.Scene, dim = 0.5): void {
  if (scene.textures.exists("bg_title")) {
    scene.add.image(BASE_WIDTH / 2, BASE_HEIGHT / 2, "bg_title").setDisplaySize(BASE_WIDTH, BASE_HEIGHT).setDepth(-10);
  } else {
    scene.add.rectangle(0, 0, BASE_WIDTH, BASE_HEIGHT, 0x0b1420).setOrigin(0, 0).setDepth(-10);
  }
  scene.add.rectangle(0, 0, BASE_WIDTH, BASE_HEIGHT, 0x05060a, dim).setOrigin(0, 0).setDepth(-9);

  // vignette
  const g = scene.add.graphics().setDepth(-8);
  const steps = 8;
  for (let i = 0; i < steps; i++) {
    const inset = Math.round(((i / steps) * Math.min(BASE_WIDTH, BASE_HEIGHT)) / 2.6);
    g.fillStyle(0x05060a, 0.08);
    g.fillRect(0, 0, BASE_WIDTH, inset);
    g.fillRect(0, BASE_HEIGHT - inset, BASE_WIDTH, inset);
    g.fillRect(0, 0, inset, BASE_HEIGHT);
    g.fillRect(BASE_WIDTH - inset, 0, inset, BASE_HEIGHT);
  }
}
