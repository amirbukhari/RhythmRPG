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
 *
 * Call setItems() to relabel/rebind in place (e.g. a settings screen whose
 * labels show live values) -- destroying and recreating a new TextMenu on
 * every change resets keyboard selection back to the top item, which is a
 * real UX bug this was built to avoid.
 */
export class TextMenu {
  private texts: Phaser.GameObjects.Text[] = [];
  private items: TextMenuItem[] = [];
  private selectedIndex = 0;
  private keyHandler: (event: KeyboardEvent) => void;
  private pointerMoveHandler: () => void;
  /**
   * Phaser hit-tests newly-created interactive objects against the pointer's
   * last known position and fires pointerover even without real OS mouse
   * movement -- e.g. right after a scene transition, if the pointer happens
   * to rest over wherever a menu item gets created. Without this guard that
   * silently hijacks keyboard-driven selection. Confirmed live: it was
   * changing the selected settings item mid keyboard-navigation.
   */
  private pointerHasMoved = false;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly x: number,
    private readonly y: number,
    items: TextMenuItem[],
    private readonly lineHeight = 14
  ) {
    this.setItems(items);

    this.keyHandler = (event: KeyboardEvent) => {
      // Belt-and-suspenders: a paused scene's keyboard listeners can still
      // fire in Phaser, so every menu independently refuses to act unless
      // its own scene is the active one.
      if (!this.scene.sys.isActive()) return;
      if (event.key === "ArrowDown") this.moveSelection(1);
      else if (event.key === "ArrowUp") this.moveSelection(-1);
      else if (event.key === "Enter" || event.key === " ") this.select(this.selectedIndex);
    };
    scene.input.keyboard?.on("keydown", this.keyHandler);

    this.pointerMoveHandler = () => (this.pointerHasMoved = true);
    scene.input.on("pointermove", this.pointerMoveHandler);

    scene.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  /** Replaces labels/handlers in place, preserving the current selection. */
  setItems(items: TextMenuItem[]): void {
    this.items = items;

    if (this.texts.length !== items.length) {
      this.texts.forEach((t) => t.destroy());
      this.texts = items.map((_, index) =>
        this.scene.add
          .text(this.x, this.y + index * this.lineHeight, "", { fontFamily: "monospace", fontSize: "10px", color: NORMAL_COLOR })
          .setOrigin(0, 0.5)
      );
      this.texts.forEach((text, index) => {
        text.on("pointerover", () => {
          if (this.pointerHasMoved && !this.items[index].disabled) this.setSelected(index);
        });
        text.on("pointerdown", () => {
          if (!this.items[index].disabled) this.select(index);
        });
      });
    }

    this.texts.forEach((text, index) => text.setInteractive({ useHandCursor: !items[index].disabled }));

    const enabledIndices = items.map((_, i) => i).filter((i) => !items[i].disabled);
    if (!enabledIndices.includes(this.selectedIndex)) {
      this.selectedIndex = enabledIndices[0] ?? 0;
    }

    this.render();
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
    this.scene.input.off("pointermove", this.pointerMoveHandler);
    this.texts.forEach((t) => t.destroy());
  }
}
