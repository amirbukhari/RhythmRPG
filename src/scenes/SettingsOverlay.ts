import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { DEFAULT_ACCESSIBILITY_SETTINGS, type AccessibilitySettings } from "../systems/accessibility/AccessibilitySettings";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";
import { TextMenu, type TextMenuItem } from "../ui/components/TextMenu";

const SPEED_STEPS: AccessibilitySettings["gameSpeed"][] = [0.7, 0.85, 1.0];
const VOLUME_STEPS = [0, 0.25, 0.5, 0.75, 1.0];

function nextInCycle<T>(steps: T[], current: T): T {
  const index = steps.indexOf(current);
  return steps[(index + 1) % steps.length];
}

/**
 * Always-available settings modal: remapping, volume sliders, captions,
 * reduced motion, photosensitivity-safe mode, game speed, assisted timing
 * windows, practice mode toggle. Mandatory day-one per PRD §9.3.
 */
const REMAP_ACTIONS = [
  { key: "tap", label: "Tap (menu/legacy)", fallback: "SPACE" },
  { key: "light", label: "Light Attack", fallback: "J" },
  { key: "heavy", label: "Heavy Attack", fallback: "K" },
  { key: "special", label: "Special", fallback: "L" },
  { key: "parry", label: "Parry", fallback: "I" },
  { key: "dash", label: "Dash", fallback: "SHIFT" },
  { key: "ultimate", label: "Ultimate", fallback: "U" },
] as const;

export class SettingsOverlay extends Phaser.Scene {
  private returnTo!: string;
  private settings!: AccessibilitySettings;
  private menu: TextMenu | null = null;
  private capturingBinding = false;
  private captureHandler?: (event: KeyboardEvent) => void;
  /** Two-page layout: gameplay/accessibility on "main", volumes + the
   * remappable bindings (PRD §9.3, incl. all combat actions) on "controls". */
  private page: "main" | "controls" = "main";
  private remapAction: string = "tap";

  constructor() {
    super("SettingsOverlay");
  }

  create(data: { returnTo: string }): void {
    // Phaser reuses one persistent Scene instance across stop/relaunch
    // cycles (create() runs again on the SAME object, it isn't
    // reconstructed) -- so every field touched after construction must be
    // reset here, not just declared with an initial value. Without this,
    // re-opening Settings a second time reused `this.menu` from the first
    // session, whose underlying Text GameObjects Phaser had already
    // destroyed on shutdown, and calling setItems() on them threw and left
    // the scene stuck mid-boot -- softlocking the player, since the
    // underlying scene's resume() (registered further down) never ran.
    this.menu = null;
    this.capturingBinding = false;
    this.captureHandler = undefined;
    this.page = "main";
    this.remapAction = "tap";

    this.returnTo = data.returnTo;
    const underlying = this.scene.get(this.returnTo);
    this.scene.pause(this.returnTo);
    // Pausing a scene stops its update/render loop but NOT its input
    // listeners -- confirmed live, this was letting the paused scene's own
    // TextMenu react to the same keypresses as this overlay's menu
    // (cascading double/triple-handling of every keystroke). input.enabled
    // alone only gates the pointer hit-test pipeline; the keyboard plugin
    // has its own independent enabled flag that must also be cleared.
    underlying.input.enabled = false;
    if (underlying.input.keyboard) underlying.input.keyboard.enabled = false;

    this.settings = GameContext.activeProfile ? GameContext.activeProfile.settings : { ...DEFAULT_ACCESSIBILITY_SETTINGS };

    this.add.rectangle(BASE_WIDTH / 2, BASE_HEIGHT / 2, BASE_WIDTH, BASE_HEIGHT, 0x000000, 0.85);
    this.add.text(BASE_WIDTH / 2, 6, "SETTINGS", { fontFamily: "monospace", fontSize: "10px", color: "#ffffff" }).setOrigin(0.5, 0);

    this.renderMenu();
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      underlying.input.enabled = true;
      if (underlying.input.keyboard) underlying.input.keyboard.enabled = true;
      this.scene.resume(this.returnTo);
    });
  }

  private renderMenu(resetSelection = false): void {
    const items = this.page === "main" ? this.mainItems() : this.controlsItems();
    if (this.menu) {
      this.menu.setItems(items, resetSelection);
    } else {
      this.menu = new TextMenu(this, 16, 24, items, 12);
    }
  }

  private switchPage(page: "main" | "controls"): void {
    this.page = page;
    this.renderMenu(true);
  }

  private mainItems(): TextMenuItem[] {
    const s = this.settings;
    const items: TextMenuItem[] = [
      { label: `Game Speed: ${Math.round(s.gameSpeed * 100)}%`, onSelect: () => this.update_(() => (s.gameSpeed = nextInCycle(SPEED_STEPS, s.gameSpeed))) },
      {
        label: `Assisted Timing Windows: ${s.assistedTimingWindows ? "ON" : "OFF"}`,
        onSelect: () =>
          this.update_(() => {
            s.assistedTimingWindows = !s.assistedTimingWindows;
            if (s.assistedTimingWindows) GameContext.analytics.track("assist_mode_enabled");
          }),
      },
      { label: `Reduced Motion: ${s.reducedMotion ? "ON" : "OFF"}`, onSelect: () => this.update_(() => (s.reducedMotion = !s.reducedMotion)) },
      { label: `Photosensitivity-Safe Mode: ${s.photosensitivitySafeMode ? "ON" : "OFF"}`, onSelect: () => this.update_(() => (s.photosensitivitySafeMode = !s.photosensitivitySafeMode)) },
      { label: `Captions: ${s.captionsEnabled ? "ON" : "OFF"}`, onSelect: () => this.update_(() => (s.captionsEnabled = !s.captionsEnabled)) },
      { label: `Practice Mode: ${s.practiceMode ? "ON" : "OFF"}`, onSelect: () => this.update_(() => (s.practiceMode = !s.practiceMode)) },
      { label: `Beat Tick (combat): ${s.beatTickEnabled ? "ON" : "OFF"}`, onSelect: () => this.update_(() => (s.beatTickEnabled = !s.beatTickEnabled)) },
      {
        label: `Sightread Forecast: ${s.sightreadEnabled ? "ON" : "OFF"}`,
        onSelect: () =>
          this.update_(() => {
            s.sightreadEnabled = !s.sightreadEnabled;
            if (s.sightreadEnabled) GameContext.analytics.track("sightread_enabled");
          }),
      },
      { label: "Audio & Controls...", onSelect: () => this.switchPage("controls") },
      { label: "Recalibrate Audio/Video Sync", onSelect: () => this.recalibrate() },
      { label: "Back", onSelect: () => this.close() },
    ];

    // Analytics consent (PRD §14) lives on the save profile root, not in
    // AccessibilitySettings, and only makes sense with an active profile --
    // without this toggle the player could never actually consent, leaving
    // the §14 event set permanently gated off in real play. v1 analytics
    // are local-only (no network), so "ON" only enables in-memory recording.
    const profile = GameContext.activeProfile;
    if (profile) {
      items.splice(items.length - 3, 0, {
        label: `Analytics (local-only): ${profile.analyticsConsent ? "ON" : "OFF"}`,
        onSelect: () =>
          this.update_(() => {
            profile.analyticsConsent = !profile.analyticsConsent;
            GameContext.analytics.setConsent(profile.analyticsConsent);
          }),
      });
    }
    return items;
  }

  /** Volumes + every remappable binding (§9.3): the legacy tap key plus all
   * six combat actions the in-world fight reads. */
  private controlsItems(): TextMenuItem[] {
    const s = this.settings;
    const items: TextMenuItem[] = [
      { label: `Music Volume: ${Math.round(s.volumeMusic * 100)}%`, onSelect: () => this.update_(() => (s.volumeMusic = nextInCycle(VOLUME_STEPS, s.volumeMusic))) },
      { label: `SFX Volume: ${Math.round(s.volumeSfx * 100)}%`, onSelect: () => this.update_(() => (s.volumeSfx = nextInCycle(VOLUME_STEPS, s.volumeSfx))) },
      { label: `UI Volume: ${Math.round(s.volumeUi * 100)}%`, onSelect: () => this.update_(() => (s.volumeUi = nextInCycle(VOLUME_STEPS, s.volumeUi))) },
      ...REMAP_ACTIONS.map(({ key, label, fallback }) => ({
        label:
          this.capturingBinding && this.remapAction === key
            ? `Remap ${label}: press any key...`
            : `Remap ${label}: ${((s.keyBindings[key] ?? "").trim() || fallback).toUpperCase()}`,
        onSelect: () => this.beginRemap(key),
      })),
      { label: "Back", onSelect: () => this.switchPage("main") },
    ];
    return items;
  }

  private update_(mutator: () => void): void {
    mutator();
    if (GameContext.activeProfile) void GameContext.persistActiveProfile();
    this.renderMenu();
  }

  private beginRemap(action: string): void {
    if (this.capturingBinding) return;
    this.capturingBinding = true;
    this.remapAction = action;
    this.renderMenu();

    this.captureHandler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        this.capturingBinding = false;
        this.cleanupCapture();
        this.renderMenu();
        return;
      }
      this.settings.keyBindings[this.remapAction] = event.key === " " ? " " : event.key;
      this.capturingBinding = false;
      this.cleanupCapture();
      if (GameContext.activeProfile) void GameContext.persistActiveProfile();
      this.renderMenu();
    };
    // Capture in the next tick so the Enter/Space that opened this menu item
    // doesn't immediately get captured as the new binding.
    this.time.delayedCall(50, () => {
      this.input.keyboard?.once("keydown", this.captureHandler!);
    });
  }

  private cleanupCapture(): void {
    if (this.captureHandler) this.input.keyboard?.off("keydown", this.captureHandler);
    this.captureHandler = undefined;
  }

  private recalibrate(): void {
    this.cleanupCapture();
    this.scene.stop(this.returnTo);
    this.scene.stop();
    this.scene.start("CalibrationScene");
  }

  private close(): void {
    this.cleanupCapture();
    this.scene.stop();
  }
}
