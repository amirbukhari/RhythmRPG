/**
 * On-screen touch controls for phones/tablets. The whole game reads keyboard
 * input (OverworldScene: WASD/arrows + E; ActionBattleScene: WASD + J/K/L/I +
 * Shift), so rather than teach every scene about pointers we synthesize the
 * exact keyboard events Phaser already listens for on `window`. Nothing in the
 * scenes changes; a held button = a held key.
 *
 * Layout: a left analog thumbstick (8-directional -> W/A/S/D) for movement,
 * and a right cluster of action buttons. Shown only on touch/coarse-pointer
 * devices, and only in the bottom corners so menu/canvas taps (audio unlock,
 * TextMenu selection) still pass straight through the open centre.
 */

interface KeySpec {
  key: string;
  code: string;
  keyCode: number;
}

const KEYS: Record<string, KeySpec> = {
  W: { key: "w", code: "KeyW", keyCode: 87 },
  A: { key: "a", code: "KeyA", keyCode: 65 },
  S: { key: "s", code: "KeyS", keyCode: 83 },
  D: { key: "d", code: "KeyD", keyCode: 68 },
  J: { key: "j", code: "KeyJ", keyCode: 74 },
  K: { key: "k", code: "KeyK", keyCode: 75 },
  L: { key: "l", code: "KeyL", keyCode: 76 },
  I: { key: "i", code: "KeyI", keyCode: 73 },
  E: { key: "e", code: "KeyE", keyCode: 69 },
  U: { key: "u", code: "KeyU", keyCode: 85 },
  SHIFT: { key: "Shift", code: "ShiftLeft", keyCode: 16 },
};

const held = new Set<string>();

function dispatchKey(type: "keydown" | "keyup", spec: KeySpec): void {
  const ev = new KeyboardEvent(type, { key: spec.key, code: spec.code, bubbles: true, cancelable: true });
  // Phaser reads the deprecated keyCode/which; KeyboardEvent's constructor
  // ignores them, so define them explicitly.
  Object.defineProperty(ev, "keyCode", { get: () => spec.keyCode });
  Object.defineProperty(ev, "which", { get: () => spec.keyCode });
  window.dispatchEvent(ev);
}

function pressKey(name: keyof typeof KEYS): void {
  if (held.has(name)) return;
  held.add(name);
  dispatchKey("keydown", KEYS[name]);
}

function releaseKey(name: keyof typeof KEYS): void {
  if (!held.has(name)) return;
  held.delete(name);
  dispatchKey("keyup", KEYS[name]);
}

/** True on phones/tablets (coarse pointer or a touch stack), false on desktop. */
function isTouchDevice(): boolean {
  return (
    (typeof matchMedia === "function" && matchMedia("(pointer: coarse)").matches) ||
    "ontouchstart" in window ||
    navigator.maxTouchPoints > 0
  );
}

const STYLE = `
#touch-controls { position: fixed; inset: 0; z-index: 50; pointer-events: none;
  touch-action: none; -webkit-user-select: none; user-select: none; }
#touch-controls .tc-stick { position: absolute; left: 16px; bottom: 16px;
  width: 132px; height: 132px; border-radius: 50%; pointer-events: auto;
  background: radial-gradient(circle, rgba(20,32,40,0.42), rgba(5,6,10,0.30));
  border: 2px solid rgba(159,232,224,0.35); touch-action: none; }
#touch-controls .tc-knob { position: absolute; left: 50%; top: 50%;
  width: 54px; height: 54px; margin: -27px 0 0 -27px; border-radius: 50%;
  background: radial-gradient(circle, rgba(159,232,224,0.85), rgba(73,198,189,0.55));
  border: 2px solid rgba(5,6,10,0.5); transition: transform 0.02s linear; }
#touch-controls .tc-actions { position: absolute; right: 14px; bottom: 14px;
  width: 190px; height: 170px; pointer-events: none; }
#touch-controls .tc-btn { position: absolute; pointer-events: auto; touch-action: none;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%; font: 700 13px/1 monospace; color: #05060a;
  border: 2px solid rgba(5,6,10,0.55); box-shadow: 0 2px 6px rgba(0,0,0,0.4); }
#touch-controls .tc-btn:active { filter: brightness(1.25); transform: scale(0.94); }
/* primary attack (big), then a ring of secondaries */
#touch-controls .tc-atk  { right: 8px;  bottom: 8px;  width: 74px; height: 74px; font-size: 15px;
  background: radial-gradient(circle at 40% 35%, #f4d27a, #f0a648); }
#touch-controls .tc-hvy  { right: 92px; bottom: 30px; width: 52px; height: 52px;
  background: radial-gradient(circle at 40% 35%, #e2a86d, #a8431c); }
#touch-controls .tc-dash { right: 20px; bottom: 92px; width: 52px; height: 52px;
  background: radial-gradient(circle at 40% 35%, #b5b4b4, #586470); }
#touch-controls .tc-sp   { right: 96px; bottom: 100px; width: 46px; height: 46px;
  background: radial-gradient(circle at 40% 35%, #b98fca, #8a52a0); }
#touch-controls .tc-par  { right: 150px; bottom: 62px; width: 46px; height: 46px;
  background: radial-gradient(circle at 40% 35%, #9fe8e0, #49c6bd); }
#touch-controls .tc-int  { right: 150px; bottom: 6px; width: 50px; height: 50px;
  background: radial-gradient(circle at 40% 35%, #79b855, #426e33); color: #f4efe2; }
#touch-controls .tc-ult  { right: 152px; bottom: 118px; width: 44px; height: 44px;
  background: radial-gradient(circle at 40% 35%, #e0b3f0, #b98fca); }
@media (min-height: 520px) { #touch-controls .tc-stick { bottom: 40px; } #touch-controls .tc-actions { bottom: 40px; } }
`;

/**
 * Mounts the touch overlay. No-op on desktop. Safe to call once at startup.
 */
export function initTouchControls(): void {
  if (!isTouchDevice()) return;
  if (document.getElementById("touch-controls")) return;

  const style = document.createElement("style");
  style.textContent = STYLE;
  document.head.appendChild(style);

  const root = document.createElement("div");
  root.id = "touch-controls";

  // --- movement thumbstick (8-dir -> W/A/S/D) ---
  const stick = document.createElement("div");
  stick.className = "tc-stick";
  const knob = document.createElement("div");
  knob.className = "tc-knob";
  stick.appendChild(knob);
  root.appendChild(stick);

  let stickPointer: number | null = null;
  const dirKeys = ["W", "A", "S", "D"] as const;

  const setStickFromDelta = (dx: number, dy: number): void => {
    const radius = 46;
    const mag = Math.hypot(dx, dy);
    const clamped = Math.min(mag, radius);
    const nx = mag > 0 ? dx / mag : 0;
    const ny = mag > 0 ? dy / mag : 0;
    knob.style.transform = `translate(${nx * clamped}px, ${ny * clamped}px)`;

    const dead = 14;
    const want = new Set<(typeof dirKeys)[number]>();
    if (mag > dead) {
      // 8-way: engage any axis whose component clears ~40% so diagonals hold two keys
      if (ny < -0.38) want.add("W");
      if (ny > 0.38) want.add("S");
      if (nx < -0.38) want.add("A");
      if (nx > 0.38) want.add("D");
    }
    for (const k of dirKeys) (want.has(k) ? pressKey(k) : releaseKey(k));
  };

  const releaseStick = (): void => {
    stickPointer = null;
    knob.style.transform = "translate(0px, 0px)";
    for (const k of dirKeys) releaseKey(k);
  };

  const capture = (el: HTMLElement, id: number): void => {
    try {
      el.setPointerCapture(id);
    } catch {
      /* synthetic/test pointers have no active capture target -- ignore */
    }
  };

  stick.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    stickPointer = e.pointerId;
    capture(stick, e.pointerId);
    const r = stick.getBoundingClientRect();
    setStickFromDelta(e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2));
  });
  stick.addEventListener("pointermove", (e) => {
    if (e.pointerId !== stickPointer) return;
    e.preventDefault();
    const r = stick.getBoundingClientRect();
    setStickFromDelta(e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2));
  });
  const endStick = (e: PointerEvent): void => {
    if (e.pointerId !== stickPointer) return;
    e.preventDefault();
    releaseStick();
  };
  stick.addEventListener("pointerup", endStick);
  stick.addEventListener("pointercancel", endStick);

  // --- action buttons ---
  const actions = document.createElement("div");
  actions.className = "tc-actions";
  const buttons: [string, string, keyof typeof KEYS][] = [
    ["tc-atk", "ATK", "J"],
    ["tc-hvy", "HVY", "K"],
    ["tc-dash", "DASH", "SHIFT"],
    ["tc-sp", "SP", "L"],
    ["tc-par", "PAR", "I"],
    ["tc-int", "E", "E"],
    ["tc-ult", "ULT", "U"],
  ];
  for (const [cls, label, keyName] of buttons) {
    const btn = document.createElement("div");
    btn.className = `tc-btn ${cls}`;
    btn.textContent = label;
    const down = (e: PointerEvent): void => {
      e.preventDefault();
      capture(btn, e.pointerId);
      pressKey(keyName);
    };
    const up = (e: PointerEvent): void => {
      e.preventDefault();
      releaseKey(keyName);
    };
    btn.addEventListener("pointerdown", down);
    btn.addEventListener("pointerup", up);
    btn.addEventListener("pointercancel", up);
    btn.addEventListener("pointerleave", up);
    actions.appendChild(btn);
  }
  root.appendChild(actions);

  document.body.appendChild(root);

  // Portrait phones letterbox the 16:9 stage into a small band -- nudge
  // (never block) toward landscape. Pure DOM, auto-hides on rotate.
  const hint = document.createElement("div");
  hint.id = "rotate-hint";
  hint.textContent = "↻ rotate for the full stage";
  hint.style.cssText =
    "position:fixed;top:8px;left:50%;transform:translateX(-50%);z-index:60;" +
    "background:rgba(5,6,10,0.8);color:#9fe8e0;font:11px monospace;padding:4px 10px;" +
    "border:1px solid rgba(73,198,189,0.4);border-radius:10px;pointer-events:none;";
  document.body.appendChild(hint);
  const updateHint = (): void => {
    hint.style.display = window.innerHeight > window.innerWidth ? "block" : "none";
  };
  updateHint();
  window.addEventListener("resize", updateHint);

  // A dropped touch (tab hidden, context lost) must not leave a key stuck down.
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      releaseStick();
      for (const name of Object.keys(KEYS) as (keyof typeof KEYS)[]) releaseKey(name);
    }
  });
}
