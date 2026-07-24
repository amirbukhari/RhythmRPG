import Phaser from "phaser";
import { BASE_WIDTH, BASE_HEIGHT, retinaCamera } from "../config/GameConfig";
import { GameContext } from "../state/GameContext";
import { cutsceneById, Cutscene, CutsceneFrame, StageKind } from "../data/content/cutscenes";

/**
 * Scripted story beats (owner: "we also need cutscenes"). A CutsceneScene plays
 * one {@link Cutscene}: staged, spare, minimal-text -- the same "found not told"
 * register as the echoes and the finale (world-bible §"How the story is told").
 *
 * It is launched as an OVERLAY over a paused scene (usually the overworld) so
 * that scene's state -- the player's position, the follower, progress -- is
 * preserved. On finish it sets the cutscene's flag on the save (so it never
 * replays) and resumes the paused scene.
 *
 * Trigger it with the static {@link CutsceneScene.play} helper.
 */
export class CutsceneScene extends Phaser.Scene {
  private cutscene!: Cutscene;
  private resumeKey!: string;
  private frameIdx = 0;
  private lineIdx = 0;
  private stageLayer!: Phaser.GameObjects.Container;
  private textLayer!: Phaser.GameObjects.Container;
  private advancing = false;

  constructor() {
    super("CutsceneScene");
  }

  /** Pause `from` and overlay the named cutscene; resume `from` when it ends.
   *  Returns false (and does nothing) if the cutscene is unknown or already seen. */
  static play(from: Phaser.Scene, cutsceneId: string): boolean {
    // Cutscenes pause the world under a full-screen overlay. The e2e suite
    // drives the game through the DEV-only debug seam and boots straight into a
    // controllable overworld, so an auto-playing cutscene would block it. Gate
    // auto-play to the shipped build; the deployed game the player runs is prod.
    if (import.meta.env.DEV) return false;
    const cut = cutsceneById(cutsceneId);
    if (!cut) return false;
    const flags = GameContext.activeProfile?.storyFlags ?? [];
    if (flags.includes(cut.flag)) return false;
    from.scene.pause();
    from.scene.launch("CutsceneScene", { cutsceneId, resumeKey: from.scene.key });
    from.scene.bringToTop("CutsceneScene");
    return true;
  }

  init(data: { cutsceneId: string; resumeKey: string }): void {
    this.cutscene = cutsceneById(data.cutsceneId)!;
    this.resumeKey = data.resumeKey;
    this.frameIdx = 0;
    this.lineIdx = 0;
    this.advancing = false;
  }

  create(): void {
    retinaCamera(this);
    this.add.rectangle(0, 0, BASE_WIDTH, BASE_HEIGHT, 0x05060a, 1).setOrigin(0, 0).setDepth(0);
    this.stageLayer = this.add.container(0, 0).setDepth(1);
    this.textLayer = this.add.container(0, 0).setDepth(2);

    // a quiet skip affordance
    this.add
      .text(BASE_WIDTH - 4, BASE_HEIGHT - 9, "ESC: skip", { fontFamily: "monospace", fontSize: "6px", color: "#5a6472" })
      .setOrigin(1, 0.5)
      .setDepth(3);

    this.input.keyboard?.on("keydown-ESC", () => this.finish());
    this.input.keyboard?.on("keydown-E", () => this.advance());
    this.input.keyboard?.on("keydown-SPACE", () => this.advance());
    this.input.keyboard?.on("keydown-ENTER", () => this.advance());
    this.input.on("pointerdown", () => this.advance());

    // Defensive: a cutscene must NEVER leave the overworld paused. If drawing a
    // frame throws, bail straight to finish() (which resumes the paused scene).
    try {
      this.showFrame();
    } catch (e) {
      console.error("[cutscene] failed, resuming world:", e);
      this.finish();
    }
  }

  private reduced(): boolean {
    return Boolean(GameContext.activeProfile?.settings.reducedMotion);
  }

  /** Draw the frame's staged backdrop and reveal its first line. */
  private showFrame(): void {
    const frame = this.cutscene.frames[this.frameIdx];
    this.lineIdx = 0;
    this.stageLayer.removeAll(true);
    try {
      this.drawStage(frame);
    } catch (e) {
      console.error("[cutscene] stage draw failed:", e); // the lines still play
    }
    this.textLayer.removeAll(true);
    this.showLine(frame);
  }

  private showLine(frame: CutsceneFrame): void {
    const text = frame.lines[this.lineIdx];
    const t = this.add
      .text(BASE_WIDTH / 2, BASE_HEIGHT - 42 + this.visibleLineCount() * 11, text, {
        fontFamily: "monospace",
        fontSize: "8px",
        color: "#e4dcc8",
        align: "center",
        stroke: "#05060a",
        strokeThickness: 3,
        wordWrap: { width: BASE_WIDTH - 40 },
      })
      .setOrigin(0.5, 0)
      .setAlpha(this.reduced() ? 1 : 0);
    this.textLayer.add(t);
    if (!this.reduced()) this.tweens.add({ targets: t, alpha: 1, duration: 650 });
  }

  private visibleLineCount(): number {
    return this.textLayer.length;
  }

  /** E / click: reveal the next line, or advance to the next frame, or finish. */
  private advance(): void {
    if (this.advancing) return;
    const frame = this.cutscene.frames[this.frameIdx];
    if (this.lineIdx < frame.lines.length - 1) {
      this.lineIdx++;
      this.showLine(frame);
      return;
    }
    // next frame (fade the whole panel out first, unless reduced)
    if (this.frameIdx < this.cutscene.frames.length - 1) {
      this.advancing = true;
      const step = () => {
        this.frameIdx++;
        this.advancing = false;
        this.showFrame();
      };
      if (this.reduced()) return step();
      this.tweens.add({ targets: [this.textLayer, this.stageLayer], alpha: 0, duration: 400, onComplete: () => {
        this.textLayer.setAlpha(1);
        this.stageLayer.setAlpha(1);
        step();
      } });
      return;
    }
    this.finish();
  }

  /** Set the once-only flag, then resume the scene we overlaid. */
  private finish(): void {
    const profile = GameContext.activeProfile;
    if (profile) {
      const flags = profile.storyFlags ?? (profile.storyFlags = []);
      if (!flags.includes(this.cutscene.flag)) {
        flags.push(this.cutscene.flag);
        void GameContext.persistActiveProfile();
      }
    }
    this.scene.resume(this.resumeKey);
    this.scene.stop();
  }

  // --- staged backdrops (procedural, sprite-free -- v11.2 register) --------
  private drawStage(frame: CutsceneFrame): void {
    const cx = BASE_WIDTH / 2;
    const cy = BASE_HEIGHT / 2 - 12;
    const g = this.add.graphics();
    this.stageLayer.add(g);
    const glow = (x: number, y: number, s: number, tint: number, a: number) => {
      const im = this.add.image(x, y, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(tint).setScale(s).setAlpha(a);
      this.stageLayer.add(im);
      if (!this.reduced()) this.tweens.add({ targets: im, alpha: a * 1.5, duration: 1600, yoyo: true, repeat: -1, ease: "Sine.inOut" });
    };
    const tint = frame.tint;
    switch (frame.stage as StageKind) {
      case "fold": {
        g.fillStyle(0x0e2430, 1).fillRect(0, cy - 40, BASE_WIDTH, 120);
        g.fillStyle(0x123038, 0.6);
        for (let i = 0; i < 6; i++) g.fillEllipse(30 + i * 50, cy + 40 + (i % 2) * 8, 44, 12);
        glow(cx, cy - 6, 1.1, tint ?? 0x49c6bd, 0.1);
        break;
      }
      case "obelisk": {
        g.fillStyle(0x0a1820, 1).fillRect(0, 0, BASE_WIDTH, BASE_HEIGHT);
        g.fillStyle(0x1c2e38, 1).fillRect(cx - 10, cy - 54, 20, 108); // the monolith
        g.fillStyle(0x2a4650, 1).fillRect(cx - 2, cy - 50, 4, 100); // the glyph seam
        glow(cx, cy - 48, 0.7, tint ?? 0x49c6bd, 0.5); // crown-light
        break;
      }
      case "litho": {
        g.fillStyle(0x0a1218, 1).fillRect(0, 0, BASE_WIDTH, BASE_HEIGHT);
        // a small, baby-shaped stone: a rounded head over a squat body
        g.fillStyle(0x6a6660, 1).fillCircle(cx, cy - 8, 12);
        g.fillStyle(0x5c5852, 1).fillEllipse(cx, cy + 10, 22, 22);
        // no-breath eyes: two dark hollows
        g.fillStyle(0x0a0a0c, 1).fillCircle(cx - 4, cy - 9, 2).fillCircle(cx + 4, cy - 9, 2);
        glow(cx, cy, 0.9, tint ?? 0xd9c39a, 0.4);
        break;
      }
      case "waterline": {
        g.fillStyle(0x0c2630, 1).fillRect(0, cy, BASE_WIDTH, BASE_HEIGHT - cy); // dark water below
        g.fillStyle(0x2c3a44, 1).fillRect(0, 0, BASE_WIDTH, cy); // pale sky above
        g.lineStyle(2, 0xd9f2ea, 0.7).beginPath();
        for (let x = 0; x <= BASE_WIDTH; x += 6) g.lineTo(x, cy + Math.sin(x / 14) * 3);
        g.strokePath();
        glow(cx, cy, 1.0, tint ?? 0x9fe8e0, 0.12);
        break;
      }
      case "scar": {
        g.fillStyle(0x1c1210, 1).fillRect(0, 0, BASE_WIDTH, BASE_HEIGHT);
        g.lineStyle(1, 0x40241c, 0.8);
        for (let i = 0; i < 7; i++) {
          g.beginPath();
          g.moveTo(20 + i * 40, cy - 30);
          g.lineTo(30 + i * 40, cy + 40);
          g.strokePath();
        }
        glow(cx, cy, 1.2, tint ?? 0xc25424, 0.14);
        break;
      }
      case "rain": {
        g.fillStyle(0x10161c, 1).fillRect(0, 0, BASE_WIDTH, BASE_HEIGHT);
        g.lineStyle(1, 0x9fb0c0, 0.4);
        for (let i = 0; i < 40; i++) {
          const x = (i * 47) % BASE_WIDTH;
          g.lineBetween(x, (i * 31) % BASE_HEIGHT, x + 3, ((i * 31) % BASE_HEIGHT) + 10);
        }
        glow(cx, 20, 1.4, tint ?? 0xc8f0dc, 0.12);
        break;
      }
      default:
        g.fillStyle(0x05060a, 1).fillRect(0, 0, BASE_WIDTH, BASE_HEIGHT);
    }
  }
}
