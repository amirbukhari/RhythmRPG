import Phaser from "phaser";
import { gameConfig } from "./config/GameConfig";
import { BootScene } from "./scenes/BootScene";
import { AudioGateScene } from "./scenes/AudioGateScene";
import { MainMenuScene } from "./scenes/MainMenuScene";
import { SaveScene } from "./scenes/SaveScene";
import { CalibrationScene } from "./scenes/CalibrationScene";
import { OverworldScene } from "./scenes/OverworldScene";
import { BattleScene } from "./scenes/BattleScene";
import { ActionBattleScene } from "./scenes/ActionBattleScene";
import { ResultsScene } from "./scenes/ResultsScene";
import { SettingsOverlay } from "./scenes/SettingsOverlay";
import { GameContext } from "./state/GameContext";
import { initTouchControls } from "./ui/TouchControls";
import { music } from "./systems/audio/SongPlayer";

// Fixed scene stack per PRD §10.6. ActionBattleScene (v6.0 real-time combat)
// is the one the overworld launches; BattleScene (turn-based) remains
// registered during the pivot so its regression coverage still runs.
const game = new Phaser.Game({
  ...gameConfig,
  scene: [
    BootScene,
    AudioGateScene,
    MainMenuScene,
    SaveScene,
    CalibrationScene,
    OverworldScene,
    ActionBattleScene,
    BattleScene,
    ResultsScene,
    SettingsOverlay,
  ],
});

// On-screen controls for phones/tablets (no-op on desktop). Synthesizes the
// keyboard events every scene already reads, so the game is playable by touch.
initTouchControls();

// A boot crash on a phone is otherwise an undebuggable black screen -- paint
// the first uncaught error into the DOM so a player report can say WHAT broke.
function showFatalOverlay(message: string): void {
  if (document.getElementById("fatal-overlay")) return;
  const el = document.createElement("div");
  el.id = "fatal-overlay";
  el.style.cssText =
    "position:fixed;left:8px;right:8px;bottom:8px;z-index:99;background:rgba(10,6,8,0.92);" +
    "color:#e8b4b8;font:11px/1.4 monospace;padding:8px 10px;border:1px solid #7d1b20;border-radius:4px;white-space:pre-wrap;";
  el.textContent = "The chorus hit a wrong note (please report this):\n" + message.slice(0, 400);
  document.body.appendChild(el);
}
window.addEventListener("error", (e) => showFatalOverlay(String(e.error?.stack ?? e.message)));
window.addEventListener("unhandledrejection", (e) => showFatalOverlay(String((e.reason as Error)?.stack ?? e.reason)));

// Dev-only debug hook: exposes app state for the tests/e2e/ Playwright suite
// and manual debugging. Stripped from production builds by Vite's dead-code
// elimination on import.meta.env.DEV -- never present in the shipped game.
if (import.meta.env.DEV) {
  (window as unknown as { __meterfallDebug: unknown }).__meterfallDebug = { game, GameContext, music };
}
