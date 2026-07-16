import Phaser from "phaser";

// Logical design space stays 320x180 (all scene layout/positions), but the
// CANVAS renders at 4x (1280x720) with every camera zoomed 4x (v11.0 beauty
// pivot: smooth painterly rendering -- dense HD art shows its real detail,
// and nothing snaps to a chunky texel grid anymore).
export const BASE_WIDTH = 320;
export const BASE_HEIGHT = 180;
export const RENDER_SCALE = 4;

/** Apply the retina camera to a scene laid out in 320x180 design space.
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
  // v11.0: the game is painterly, not pixel art -- smooth sampling everywhere
  pixelArt: false,
  antialias: true,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  parent: "app",
  backgroundColor: "#000000",
};
