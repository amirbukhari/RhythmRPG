import Phaser from "phaser";
import { gameConfig } from "./config/GameConfig";
import { BootScene } from "./scenes/BootScene";
import { AudioGateScene } from "./scenes/AudioGateScene";
import { MainMenuScene } from "./scenes/MainMenuScene";
import { SaveScene } from "./scenes/SaveScene";
import { CalibrationScene } from "./scenes/CalibrationScene";
import { MapScene } from "./scenes/MapScene";
import { BattleScene } from "./scenes/BattleScene";
import { ResultsScene } from "./scenes/ResultsScene";
import { SettingsOverlay } from "./scenes/SettingsOverlay";

// Fixed scene stack per PRD §10.6.
new Phaser.Game({
  ...gameConfig,
  scene: [
    BootScene,
    AudioGateScene,
    MainMenuScene,
    SaveScene,
    CalibrationScene,
    MapScene,
    BattleScene,
    ResultsScene,
    SettingsOverlay,
  ],
});
