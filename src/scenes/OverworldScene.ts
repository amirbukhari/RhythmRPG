import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { campaign, getCampaignNode } from "../data/ContentRegistry";
import { resolveEncounterId } from "../systems/progression/CampaignSelection";
import { nodeStatus, type NodeStatus } from "../systems/progression/CampaignReachability";
import { stepTarget, isWalkable, type Direction, type GridPosition } from "../systems/overworld/OverworldMovement";
import tilesetUrl from "../../assets/tilemaps/overworld_tileset.png";
import tilemapUrl from "../../assets/tilemaps/overworld.json?url";
import runSheetUrl from "../../assets/sprites/heroes/placeholder/Amir Run.png";

const TILE_SIZE = 16;
const STEP_DURATION_MS = 160;
const MARKER_COLORS: Record<NodeStatus, number> = { cleared: 0x44cc66, unlocked: 0xffe066, locked: 0x444444 };
const NODE_TYPE_LABEL: Record<string, string> = { battle: "B", elite: "E", boss: "!", camp: "C" };

interface Marker {
  nodeId: string;
  col: number;
  row: number;
}

/**
 * Walkable pixel-art overworld (tilemap + tile-snapped movement + camera
 * follow), replacing the old text-menu MapScene as the between-battles hub.
 * Walking onto an unlocked campaign-node marker starts that node's battle;
 * the battle/results flow itself is unchanged. Movement is manual
 * tile-tweening, deliberately not Arcade/Matter physics -- nothing here
 * needs velocity, gravity, or swept collision, only "is the next tile
 * legal", which is pure grid math (OverworldMovement.ts).
 */
export class OverworldScene extends Phaser.Scene {
  private player!: Phaser.GameObjects.Sprite;
  private playerPos: GridPosition = { col: 0, row: 0 };
  private moving = false;
  private walkable: boolean[][] = [];
  private markers: Marker[] = [];
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private wasd!: Record<"W" | "A" | "S" | "D", Phaser.Input.Keyboard.Key>;

  constructor() {
    super("OverworldScene");
  }

  preload(): void {
    // First scene-local preload in the codebase (BootScene only preloads
    // the shared hero portrait); guarded so a scene restart doesn't try to
    // re-register live cache keys.
    if (!this.textures.exists("overworld_tiles")) this.load.image("overworld_tiles", tilesetUrl);
    if (!this.cache.tilemap.exists("overworld")) this.load.tilemapTiledJSON("overworld", tilemapUrl);
    if (!this.textures.exists("amir_run")) {
      this.load.spritesheet("amir_run", runSheetUrl, { frameWidth: 128, frameHeight: 128 });
    }
  }

  create(): void {
    const profile = GameContext.activeProfile;
    if (!profile) {
      this.scene.start("SaveScene");
      return;
    }

    this.moving = false;

    const map = this.make.tilemap({ key: "overworld" });
    const tileset = map.addTilesetImage("overworld_tileset", "overworld_tiles")!;
    const ground = map.createLayer("ground", tileset, 0, 0)!;

    this.walkable = [];
    for (let row = 0; row < map.height; row++) {
      const rowFlags: boolean[] = [];
      for (let col = 0; col < map.width; col++) {
        const tile = ground.getTileAt(col, row);
        const props = tile ? (tileset.getTileProperties(tile.index) as { collides?: boolean } | null) : null;
        rowFlags.push(!props?.collides);
      }
      this.walkable.push(rowFlags);
    }

    // Marker names in the tilemap ARE campaign node ids (plus one "spawn").
    const objects = map.getObjectLayer("markers")!.objects;
    const spawnObject = objects.find((o) => o.name === "spawn")!;
    this.markers = objects
      .filter((o) => o.name !== "spawn")
      .map((o) => ({ nodeId: o.name, col: Math.floor(o.x! / TILE_SIZE), row: Math.floor(o.y! / TILE_SIZE) }));
    for (const marker of this.markers) this.drawMarker(profile, marker);

    if (!this.anims.exists("amir_walk")) {
      this.anims.create({
        key: "amir_walk",
        frames: this.anims.generateFrameNumbers("amir_run", { start: 0, end: 7 }),
        frameRate: 12,
        repeat: -1,
      });
    }

    // Return to the node just fought rather than the fixed spawn point --
    // nodes sit along the road, so respawning at the start after every
    // battle would force pointless backtracking. Read-once, like the other
    // GameContext handoff fields.
    const returnMarker = this.markers.find((m) => m.nodeId === GameContext.returnToNodeId);
    GameContext.returnToNodeId = null;
    this.playerPos = returnMarker
      ? { col: returnMarker.col, row: returnMarker.row }
      : { col: Math.floor(spawnObject.x! / TILE_SIZE), row: Math.floor(spawnObject.y! / TILE_SIZE) };

    this.player = this.add.sprite(0, 0, "amir_run", 0);
    // The run-cycle frames are 128x128 but the figure itself only occupies
    // ~36px in the middle of each frame (bbox measured across all 8
    // frames), so the scale is set for the *figure* to stand ~22px --
    // about 1.4 tiles, classic JRPG proportions -- not the frame. The
    // origin puts the figure's feet (y=80/128 in-frame) on the tile center.
    this.player.setScale(0.6);
    this.player.setOrigin(0.52, 0.625);
    this.snapPlayerToGrid();

    this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    this.cameras.main.startFollow(this.player, true, 1, 1);
    this.cameras.main.setRoundPixels(true);

    const keyboard = this.input.keyboard!;
    this.cursors = keyboard.createCursorKeys();
    this.wasd = keyboard.addKeys("W,A,S,D") as OverworldScene["wasd"];
    keyboard.on("keydown-ESC", () => this.scene.launch("SettingsOverlay", { returnTo: "OverworldScene" }));

    this.add
      .text(4, 4, "Arrows/WASD: move   ESC: settings", { fontFamily: "monospace", fontSize: "7px", color: "#ffffff" })
      .setScrollFactor(0)
      .setDepth(10)
      .setAlpha(0.8);
  }

  update(): void {
    if (this.moving || !this.player) return;
    const dir = this.heldDirection();
    if (dir) this.tryStep(dir);
    else if (this.player.anims.isPlaying) {
      this.player.anims.stop();
      this.player.setFrame(0);
    }
  }

  /** Grid position test seam, read via the DEV-only __meterfallDebug hook. */
  getPlayerGridPosition(): GridPosition {
    return { ...this.playerPos };
  }

  /**
   * Test seam (reached via the DEV-only __meterfallDebug hook): snaps the
   * player onto a node's marker tile and re-runs the same encounter-trigger
   * check a real step onto it performs. Exists because pixel-perfect
   * keyboard pathing across the whole map is exactly the slow/flaky
   * automation the e2e suite already avoids (see jumpToEncounter).
   */
  debugTeleportToNode(nodeId: string): void {
    const marker = this.markers.find((m) => m.nodeId === nodeId);
    if (!marker) throw new Error(`No overworld marker for node "${nodeId}"`);
    this.playerPos = { col: marker.col, row: marker.row };
    this.snapPlayerToGrid();
    this.checkEncounterTrigger();
  }

  private heldDirection(): Direction | null {
    if (this.cursors.left.isDown || this.wasd.A.isDown) return "left";
    if (this.cursors.right.isDown || this.wasd.D.isDown) return "right";
    if (this.cursors.up.isDown || this.wasd.W.isDown) return "up";
    if (this.cursors.down.isDown || this.wasd.S.isDown) return "down";
    return null;
  }

  private tryStep(dir: Direction): void {
    // Only one horizontal art strip exists (PRD §11.4): left is the same
    // frames flipped; up/down reuse them unflipped. Placeholder-art
    // limitation, not a bug.
    if (dir === "left") this.player.setFlipX(true);
    if (dir === "right") this.player.setFlipX(false);

    const target = stepTarget(this.playerPos, dir);
    if (!isWalkable(this.walkable, target)) return;

    this.moving = true;
    if (!this.player.anims.isPlaying) this.player.play("amir_walk");
    this.playerPos = target;
    this.tweens.add({
      targets: this.player,
      x: target.col * TILE_SIZE + TILE_SIZE / 2,
      y: target.row * TILE_SIZE + TILE_SIZE / 2,
      duration: STEP_DURATION_MS,
      onComplete: () => {
        this.moving = false;
        this.checkEncounterTrigger();
      },
    });
  }

  /**
   * Walking onto an unlocked marker starts its battle immediately (no
   * separate confirm key). Cleared and locked markers are walk-over no-ops:
   * cleared nodes sit on the road onward, and v1 has no re-fighting.
   */
  private checkEncounterTrigger(): void {
    const profile = GameContext.activeProfile;
    if (!profile) return;
    const marker = this.markers.find((m) => m.col === this.playerPos.col && m.row === this.playerPos.row);
    if (!marker) return;
    if (nodeStatus(campaign, profile.campaignProgress, marker.nodeId) !== "unlocked") return;

    const encounterId = resolveEncounterId(getCampaignNode(marker.nodeId));
    if (!encounterId) return; // camp nodes have no encounter
    GameContext.pendingEncounterId = encounterId;
    GameContext.pendingNodeId = marker.nodeId;
    this.scene.start("BattleScene");
  }

  private drawMarker(profile: NonNullable<typeof GameContext.activeProfile>, marker: Marker): void {
    const status = nodeStatus(campaign, profile.campaignProgress, marker.nodeId);
    const x = marker.col * TILE_SIZE + TILE_SIZE / 2;
    const y = marker.row * TILE_SIZE + TILE_SIZE / 2;
    const node = getCampaignNode(marker.nodeId);

    const circle = this.add.circle(x, y, node.type === "boss" ? 8 : 6, MARKER_COLORS[status]);
    this.add
      .text(x, y, NODE_TYPE_LABEL[node.type] ?? "?", { fontFamily: "monospace", fontSize: "7px", color: "#000000" })
      .setOrigin(0.5);

    if (status === "unlocked" && !profile.settings.reducedMotion) {
      this.tweens.add({ targets: circle, scale: 1.25, yoyo: true, repeat: -1, duration: 500 });
    }
  }

  private snapPlayerToGrid(): void {
    this.player.setPosition(this.playerPos.col * TILE_SIZE + TILE_SIZE / 2, this.playerPos.row * TILE_SIZE + TILE_SIZE / 2);
  }
}
