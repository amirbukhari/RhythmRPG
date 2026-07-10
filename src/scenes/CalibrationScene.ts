import Phaser from "phaser";
import { TransportClock } from "../systems/audio/TransportClock";
import { CALIBRATION_BPM, CALIBRATION_BEAT_SECONDS, CALIBRATION_TAP_COUNT, computeCalibrationOffsetMs } from "../systems/audio/Calibration";
import { GameContext } from "../state/GameContext";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";

/** AV sync test and global timing offset save. See PRD §9.3, §10.3. */
export class CalibrationScene extends Phaser.Scene {
  private clock = new TransportClock();
  private pulse!: Phaser.GameObjects.Arc;
  private statusText!: Phaser.GameObjects.Text;
  private taps: number[] = [];
  private scheduleId: number | null = null;
  private tapKey = " ";
  private gentleFlash = false;

  constructor() {
    super("CalibrationScene");
  }

  async create(): Promise<void> {
    const settings = GameContext.activeProfile?.settings;
    this.tapKey = settings?.keyBindings.tap ?? " ";
    // PRD §9.3/W3C photosensitivity guidance: no full-brightness flashing
    // when reduced motion or photosensitivity-safe mode is on.
    this.gentleFlash = Boolean(settings?.reducedMotion || settings?.photosensitivitySafeMode);
    const keyLabel = this.tapKey === " " ? "SPACE" : this.tapKey.toUpperCase();

    this.add
      .text(BASE_WIDTH / 2, 20, `CALIBRATION\nTap ${keyLabel} on every beat`, {
        fontFamily: "monospace",
        fontSize: "9px",
        color: "#ffffff",
        align: "center",
      })
      .setOrigin(0.5);

    this.pulse = this.add.circle(BASE_WIDTH / 2, BASE_HEIGHT / 2, 10, 0x4444ff);
    this.statusText = this.add
      .text(BASE_WIDTH / 2, BASE_HEIGHT - 30, `Taps: 0 / ${CALIBRATION_TAP_COUNT}`, {
        fontFamily: "monospace",
        fontSize: "8px",
        color: "#aaaaaa",
      })
      .setOrigin(0.5);

    await this.clock.start(CALIBRATION_BPM);
    this.scheduleId = this.clock.scheduleRepeat(() => this.flashPulse(), "4n");

    this.input.keyboard?.on("keydown", (event: KeyboardEvent) => {
      if (event.key === this.tapKey) this.registerTap();
    });
    // Real bug found via live play: this scene is the very first mandatory,
    // unskippable input the player must give, and it accepted keyboard-only
    // taps while every other interactive screen (AudioGateScene, TextMenu)
    // accepts pointer input too. A player who clicks/taps instead of
    // pressing a physical key -- e.g. on a touch device, or just by habit --
    // got completely stuck here with no feedback and no way to proceed.
    this.input.on("pointerdown", () => this.registerTap());

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.cleanup());
  }

  private flashPulse(): void {
    // Gentle mode: gradual color shift only, no bright flash. Default mode:
    // a full-brightness flash, but at ~1.67Hz (100 BPM quarter notes), well
    // under the 3/second seizure-risk threshold W3C flags.
    this.pulse.setFillStyle(this.gentleFlash ? 0x8888ff : 0xffffff);
    this.time.delayedCall(100, () => this.pulse.setFillStyle(0x4444ff));
  }

  private registerTap(): void {
    if (this.taps.length >= CALIBRATION_TAP_COUNT) return;
    this.taps.push(this.clock.currentTime);
    this.statusText.setText(`Taps: ${this.taps.length} / ${CALIBRATION_TAP_COUNT}`);

    if (this.taps.length >= CALIBRATION_TAP_COUNT) {
      void this.finish();
    }
  }

  private async finish(): Promise<void> {
    const offsetMs = computeCalibrationOffsetMs(this.taps, CALIBRATION_BEAT_SECONDS);
    const profile = GameContext.activeProfile;
    if (profile) {
      profile.calibrationOffsetMs = offsetMs;
      profile.calibrationDone = true;
      await GameContext.persistActiveProfile();
    }
    GameContext.analytics.track("calibration_completed", { offsetMs });
    this.scene.start("OverworldScene");
  }

  private cleanup(): void {
    if (this.scheduleId !== null) this.clock.clearSchedule(this.scheduleId);
    this.clock.stop();
  }
}
