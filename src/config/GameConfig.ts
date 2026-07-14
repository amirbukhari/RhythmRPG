import Phaser from "phaser";

// Logical design space stays 320x180 (all scene layout/positions), but the
// CANVAS renders at 2x (640x360) with every camera zoomed 2x (design-audit-3
// "way too pixelly"): art whose source texels are denser than the old canvas
// (the 72px foes/band at ~0.5 scale, the 32px-per-tile ground plate, all AI
// pieces) finally shows its real detail instead of being crushed to 320-wide.
export const BASE_WIDTH = 320;
export const BASE_HEIGHT = 180;
export const RENDER_SCALE = 2;

/** Apply the 2x retina camera to a scene laid out in 320x180 design space.
 * Call first thing in create(). The camera then shows exactly the design
 * rect, so every existing coordinate keeps working. */
export function retinaCamera(scene: Phaser.Scene): void {
  scene.cameras.main.setZoom(RENDER_SCALE);
  scene.cameras.main.centerOn(BASE_WIDTH / 2, BASE_HEIGHT / 2);
}

export const gameConfig: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: BASE_WIDTH * RENDER_SCALE,
  height: BASE_HEIGHT * RENDER_SCALE,
  pixelArt: true,
  antialias: false,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  parent: "app",
  backgroundColor: "#000000",
};
