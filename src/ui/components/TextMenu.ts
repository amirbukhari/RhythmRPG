import Phaser from "phaser";

export interface TextMenuItem {
  label: string;
  onSelect: () => void;
  disabled?: boolean;
}

const NORMAL_COLOR = "#ffffff";
const SELECTED_COLOR = "#ffe066";
const DISABLED_COLOR = "#666666";

/**
 * Minimal keyboard + pointer navigable vertical text menu. PRD §9.3 requires
 * keyboard-only play with no required simultaneous presses everywhere, so
 * every menu in the game is built on this rather than ad hoc per-scene
 * pointer-only buttons.
 */
export class TextMenu {
  private texts: Phaser.GameObjects.Text[] = [];
  private selectedIndex = 0;
  private keyHandler: (event: KeyboardEvent) => void;

  constructor(
    private readonly scene: Phaser.Scene,
    x: number,
    y: number,
    private readonly items: TextMenuItem[],
    lineHeight = 14
  ) {
    this.items.forEach((item, index) => {
      const text = scene.add
        .text(x, y + index * lineHeight, item.label, {
          fontFamily: "monospace",
          fontSize: "10px",
          color: item.disabled ? DISABLED_COLOR : NORMAL_COLOR,
        })
        .setOrigin(0, 0.5)
        .setInteractive({ useHandCursor: !item.disabled });

      text.on("pointerover", () => {
        if (!item.disabled) this.setSelected(index);
      });
      text.on("pointerdown", () => {
        if (!item.disabled) this.select(index);
      });
      this.texts.push(text);
    });

    this.render();

    this.keyHandler = (event: KeyboardEvent) => {
      if (event.key === "ArrowDown") this.moveSelection(1);
      else if (event.key === "ArrowUp") this.moveSelection(-1);
      else if (event.key === "Enter" || event.key === " ") this.select(this.selectedIndex);
    };
    scene.input.keyboard?.on("keydown", this.keyHandler);
    scene.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  private moveSelection(delta: number): void {
    const enabledIndices = this.items.map((_, i) => i).filter((i) => !this.items[i].disabled);
    if (enabledIndices.length === 0) return;
    const currentPos = enabledIndices.indexOf(this.selectedIndex);
    const nextPos = (currentPos + delta + enabledIndices.length) % enabledIndices.length;
    this.setSelected(enabledIndices[nextPos]);
  }

  private setSelected(index: number): void {
    this.selectedIndex = index;
    this.render();
  }

  private select(index: number): void {
    const item = this.items[index];
    if (!item || item.disabled) return;
    item.onSelect();
  }

  private render(): void {
    this.texts.forEach((text, index) => {
      const item = this.items[index];
      text.setColor(item.disabled ? DISABLED_COLOR : index === this.selectedIndex ? SELECTED_COLOR : NORMAL_COLOR);
      text.setText(index === this.selectedIndex && !item.disabled ? `> ${item.label}` : `  ${item.label}`);
    });
  }

  destroy(): void {
    this.scene.input.keyboard?.off("keydown", this.keyHandler);
    this.texts.forEach((t) => t.destroy());
  }
}
