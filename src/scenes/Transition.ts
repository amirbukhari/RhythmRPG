import Phaser from "phaser";
import { RENDER_SCALE } from "../config/GameConfig";
import { GameContext } from "../state/GameContext";

/**
 * Scene transitions -- the game used to CUT.
 *
 * Thirteen `scene.start` calls, zero fades: every boundary in the game (menu →
 * save → calibration → world, world → results → world, the whole finale) was a
 * single-frame jump. Nothing else in the build reads as cheaply as a hard cut,
 * and it is the one polish item that costs almost nothing and touches every
 * screen the player sees.
 *
 * WHY THE CAMERA AND NOT A CURTAIN
 * A `Graphics` curtain has to sit above everything, and "everything" is a
 * different depth in every scene (WorldFight's HUD is at 21, the overworld's
 * canopies at 6.5), and it has to be pinned under a camera that is zoomed 4x
 * and, in the overworld, scrolling. `camera.fadeOut` is depth-independent,
 * scroll-independent and survives `scene.restart()`, which the boss spec uses.
 *
 * WHY IT IS NOT A PLAIN BLACK FADE
 * Two details do all the work of making this read as authored rather than
 * mechanical:
 *
 *   1. It fades to INK (0x05060a), the palette's darkest value, not to pure
 *      black. Black is the absence of a picture; ink is lightless water, which
 *      is where this game is set.
 *   2. It is ASYMMETRIC -- out fast, in slower -- and the outgoing camera
 *      drifts 3% closer while it goes. Sinking is quick and surfacing is slow,
 *      and a symmetric fade in both directions is the thing that reads as a
 *      screen wipe rather than as a place changing.
 *
 * Reduced motion gets the state change with no fade and no drift: the setting
 * exists so the player is never moved without asking, and a 4x-zoomed camera
 * push is exactly that.
 */
const INK: [number, number, number] = [0x05, 0x06, 0x0a];
const OUT_MS = 230;
const IN_MS = 380;

function reduced(): boolean {
  return Boolean(GameContext.activeProfile?.settings.reducedMotion);
}

/**
 * Leave for another scene. Fades the current camera down, then starts `key`.
 *
 * Guarded against double-fire: the fade runs for a fifth of a second, which is
 * long enough for a second Enter press, and starting a scene twice tears down
 * the one that is mid-create.
 */
export function sceneGoto(scene: Phaser.Scene, key: string, data?: object): void {
  const s = scene as Phaser.Scene & { __leaving?: boolean };
  if (s.__leaving) return;
  s.__leaving = true;
  if (reduced()) {
    scene.scene.start(key, data);
    return;
  }
  const cam = scene.cameras.main;
  const z = cam.zoom;
  scene.tweens.add({ targets: cam, zoom: z * 1.03, duration: OUT_MS, ease: "Quad.easeIn" });
  cam.once(Phaser.Cameras.Scene2D.Events.FADE_OUT_COMPLETE, () => {
    cam.setZoom(z); // the next scene may be this one again (scene.restart)
    scene.scene.start(key, data);
  });
  cam.fadeOut(OUT_MS, ...INK);
}

/**
 * Arrive. Call at the top of `create()`, straight after `retinaCamera`.
 *
 * Also clears the leaving guard, because Phaser reuses the Scene instance
 * across starts -- without this, a scene you return to can never leave again.
 */
export function sceneEnter(scene: Phaser.Scene, opts?: { zoom?: boolean }): void {
  (scene as Phaser.Scene & { __leaving?: boolean }).__leaving = false;
  if (reduced()) return;
  const cam = scene.cameras.main;
  // `zoom: false` for the overworld. Its camera is not a static design-space
  // camera: it follows the player, it is zoomed by the region, and WorldFight
  // locks it to an arena rect and shakes it. A zoom tween on arrival races all
  // three -- the fade alone is the part that carries the transition anyway.
  if (opts?.zoom !== false) {
    const z = cam.zoom || RENDER_SCALE;
    cam.setZoom(z * 1.02);
    scene.tweens.add({ targets: cam, zoom: z, duration: IN_MS + 120, ease: "Quad.easeOut" });
  }
  cam.fadeIn(IN_MS, ...INK);
}
