import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import {BASE_WIDTH, BASE_HEIGHT, retinaCamera } from "../config/GameConfig";
import { addBackdrop } from "../ui/Backdrop";
import { TextMenu } from "../ui/components/TextMenu";
import { music } from "../systems/audio/SongPlayer";
import { sceneGoto, sceneEnter } from "./Transition";

/**
 * The ending (world-bible §8). Getting past Lunal used to dump the player
 * straight back onto the overworld with a "+150 XP" toast -- a releasable game
 * closes its story. Same found-not-told voice as the echoes (PRD §7.3 pillar
 * 4): the three movements of §8 -- he picks the lock rather than breaking it
 * (the whole reason he has a sedentary trade), the boy does not know him at
 * once, and up top it rains and Nari asks the one question a child from the
 * Fold has never had -- then the wordmark and the credits. The world stays open
 * afterwards (echoes remain findable), so "Return to the world" is the
 * primary action, not a hard stop.
 */
export class FinaleScene extends Phaser.Scene {
  constructor() {
    super("FinaleScene");
  }

  create(): void {
    retinaCamera(this);
    sceneEnter(this);
    addBackdrop(this, 0.35);
    music.setMode("menu"); // Sunshine Sally carries the credits

    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);

    // The three movements of §8, surfacing one at a time. They wrap (the old
    // lines were one row each and these are not), so the block is laid out from
    // a measured top rather than a fixed 12px step, and it lands clear of the
    // wordmark at y=88.
    const lines = [
      "He does not break the cage. He kneels and picks the lock -- the small turning tool from the Fold, and hands that are wrecked now -- the way he has opened a thousand quiet things.",
      "Nari does not know him at first. That is the price of the climb, and it is allowed to be ugly for a while.",
      "They go up, and it rains, and he laughs -- he has never seen rain. And then he asks me where we are going. He has never asked that before. I don't know, Nari. Isn't it good?",
    ];
    let y = 12;
    lines.forEach((line, i) => {
      const t = this.add
        .text(BASE_WIDTH / 2, y, line, {
          fontFamily: "monospace",
          fontSize: "6px",
          color: "#d8ceb6",
          align: "center",
          stroke: "#05060a",
          strokeThickness: 3,
          wordWrap: { width: BASE_WIDTH - 44 },
        })
        .setOrigin(0.5, 0)
        .setAlpha(reduced ? 1 : 0);
      if (!reduced) this.tweens.add({ targets: t, alpha: 1, delay: 600 + i * 1600, duration: 900 });
      y += t.height + 4;
    });

    const wordmark = this.add.image(BASE_WIDTH / 2, 88, "wordmark").setScale(0.5).setAlpha(reduced ? 1 : 0);
    if (!reduced) this.tweens.add({ targets: wordmark, alpha: 1, delay: 4800, duration: 1200 });

    const credits = [
      "starring  Mir · Nari · Lunal · the Harrow",
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
        { label: "Return to the drowned world", onSelect: () => sceneGoto(this, "OverworldScene") },
        { label: "Main menu", onSelect: () => sceneGoto(this, "MainMenuScene") },
      ],
      10
    );
  }
}
