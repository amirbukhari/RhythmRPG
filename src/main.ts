import Phaser from "phaser";
import { gameConfig } from "./config/GameConfig";
import { BootScene } from "./scenes/BootScene";
import { AudioGateScene } from "./scenes/AudioGateScene";
import { MainMenuScene } from "./scenes/MainMenuScene";
import { SaveScene } from "./scenes/SaveScene";
import { CalibrationScene } from "./scenes/CalibrationScene";
import { OverworldScene } from "./scenes/OverworldScene";
import { BattleScene } from "./scenes/BattleScene";
import { ResultsScene } from "./scenes/ResultsScene";
import { SettingsOverlay } from "./scenes/SettingsOverlay";
import { GameContext } from "./state/GameContext";

// Fixed scene stack per PRD §10.6.
const game = new Phaser.Game({
  ...gameConfig,
  scene: [
    BootScene,
    AudioGateScene,
    MainMenuScene,
    SaveScene,
    CalibrationScene,
    OverworldScene,
    BattleScene,
    ResultsScene,
    SettingsOverlay,
  ],
});

// Dev-only debug hook: exposes app state for the tests/e2e/ Playwright suite
// and manual debugging. Stripped from production builds by Vite's dead-code
// elimination on import.meta.env.DEV -- never present in the shipped game.
if (import.meta.env.DEV) {
  (window as unknown as { __meterfallDebug: unknown }).__meterfallDebug = { game, GameContext };
}
