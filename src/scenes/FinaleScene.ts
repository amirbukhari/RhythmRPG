import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import {BASE_WIDTH, BASE_HEIGHT, retinaCamera } from "../config/GameConfig";
import { addBackdrop } from "../ui/Backdrop";
import { TextMenu } from "../ui/components/TextMenu";
import { music } from "../systems/audio/SongPlayer";

/**
 * The ending. Beating the Conductor used to dump the player straight back
 * onto the overworld with a "+150 XP" toast -- a releasable game closes its
 * story. Same found-not-told voice as the echoes (PRD §7.3 pillar 4): a few
 * staged lines — the Lunal reveal and finding Nari (PRD §8.7 v10.0) — the
 * wordmark, and the credits. The world stays open
 * afterwards (echoes remain findable), so "Return to the world" is the
 * primary action, not a hard stop.
 */
export class FinaleScene extends Phaser.Scene {
  constructor() {
    super("FinaleScene");
  }

  create(): void {
    retinaCamera(this);
    addBackdrop(this, 0.35);
    music.setMode("menu"); // Sunshine Sally carries the credits

    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);

    // The last three lines of the untold story, surfacing one at a time.
    const lines = [
      "The hall falls silent. A mask clatters where the huntress stood.",
      "Then -- not silence. Rain, far above. And under it, small: a laugh.",
      "Nari. Found. The chorus rests.",
    ];
    lines.forEach((line, i) => {
      const t = this.add
        .text(BASE_WIDTH / 2, 26 + i * 12, line, { fontFamily: "monospace", fontSize: "7px", color: "#d8ceb6", stroke: "#05060a", strokeThickness: 3 })
        .setOrigin(0.5)
        .setAlpha(reduced ? 1 : 0);
      if (!reduced) this.tweens.add({ targets: t, alpha: 1, delay: 600 + i * 1400, duration: 900 });
    });

    const wordmark = this.add.image(BASE_WIDTH / 2, 88, "wordmark").setScale(0.5).setAlpha(reduced ? 1 : 0);
    if (!reduced) this.tweens.add({ targets: wordmark, alpha: 1, delay: 4800, duration: 1200 });

    const credits = [
      "starring  Mir · Nari · Lunal · the Conductor",
      "music by INHALANTS",
      "songs  Sunshine Sally · Deereater · Glassriff",
      "John's Anus · Truckers for Christ · Quotience",
    ].join("\n");
    const creditText = this.add
      .text(BASE_WIDTH / 2, 112, credits, {
        fontFamily: "monospace",
        fontSize: "6px",
        color: "#9fb0c0",
        align: "center",
        stroke: "#05060a",
        strokeThickness: 2,
      })
      .setOrigin(0.5, 0)
      .setAlpha(reduced ? 1 : 0);
    if (!reduced) this.tweens.add({ targets: creditText, alpha: 1, delay: 5600, duration: 1200 });

    new TextMenu(
      this,
      BASE_WIDTH / 2 - 62,
      BASE_HEIGHT - 22,
      [
        { label: "Return to the drowned world", onSelect: () => this.scene.start("OverworldScene") },
        { label: "Main menu", onSelect: () => this.scene.start("MainMenuScene") },
      ],
      10
    );
  }
}
