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

  constructor() {
    super("CalibrationScene");
  }

  async create(): Promise<void> {
    this.add
      .text(BASE_WIDTH / 2, 20, "CALIBRATION\nTap SPACE on every beat", {
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

    this.input.keyboard?.on("keydown-SPACE", () => this.registerTap());

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.cleanup());
  }

  private flashPulse(): void {
    this.pulse.setFillStyle(0xffffff);
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
    this.scene.start("MapScene");
  }

  private cleanup(): void {
    if (this.scheduleId !== null) this.clock.clearSchedule(this.scheduleId);
    this.clock.stop();
  }
}
