import Phaser from "phaser";
import { gameConfig, RENDER_SCALE } from "./config/GameConfig";

// v11.0 beauty pivot: cameras zoom the 320x180 design space up to the 4x
// canvas, and Phaser rasterizes Text at style resolution 1 by default --
// which the zoom then blurs. Default every scene's add.text/make.text to
// canvas resolution so ALL existing UI text stays crisp without touching
// every call site.
const textFactory = Phaser.GameObjects.GameObjectFactory.prototype.text;
Phaser.GameObjects.GameObjectFactory.prototype.text = function (
  this: Phaser.GameObjects.GameObjectFactory,
  x: number,
  y: number,
  text: string | string[],
  style?: Phaser.Types.GameObjects.Text.TextStyle
) {
  return textFactory.call(this, x, y, text, { resolution: RENDER_SCALE, ...style });
};
const textCreator = Phaser.GameObjects.GameObjectCreator.prototype.text;
Phaser.GameObjects.GameObjectCreator.prototype.text = function (
  this: Phaser.GameObjects.GameObjectCreator,
  config: Phaser.Types.GameObjects.Text.TextConfig,
  addToScene?: boolean
) {
  return textCreator.call(this, { ...config, style: { resolution: RENDER_SCALE, ...config.style } }, addToScene);
};
import { BootScene } from "./scenes/BootScene";
import { AudioGateScene } from "./scenes/AudioGateScene";
import { MainMenuScene } from "./scenes/MainMenuScene";
import { SaveScene } from "./scenes/SaveScene";
import { CalibrationScene } from "./scenes/CalibrationScene";
import { OverworldScene } from "./scenes/OverworldScene";
import { ResultsScene } from "./scenes/ResultsScene";
import { FinaleScene } from "./scenes/FinaleScene";
import { CutsceneScene } from "./scenes/CutsceneScene";
import { SettingsOverlay } from "./scenes/SettingsOverlay";
import { GameContext } from "./state/GameContext";
import { initTouchControls } from "./ui/TouchControls";
import { music } from "./systems/audio/SongPlayer";

// Fixed scene stack per PRD §10.6. Combat happens IN the world: OverworldScene
// hosts WorldFight (v7.13) -- the retired BattleScene/ActionBattleScene were
// deleted at v8.3 (release gate #7: no retired scene reachable, or shipped).
const game = new Phaser.Game({
  ...gameConfig,
  scene: [
    BootScene,
    AudioGateScene,
    MainMenuScene,
    SaveScene,
    CalibrationScene,
    OverworldScene,
    ResultsScene,
    FinaleScene,
    CutsceneScene,
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
