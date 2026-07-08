import Phaser from "phaser";

// Fixed internal resolution + crisp pixel scaling. See PRD §10.6.
export const BASE_WIDTH = 320;
export const BASE_HEIGHT = 180;

export const gameConfig: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: BASE_WIDTH,
  height: BASE_HEIGHT,
  pixelArt: true,
  antialias: false,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  parent: "app",
  backgroundColor: "#000000",
};
