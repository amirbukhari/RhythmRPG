import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { campaign, getCampaignNode } from "../data/ContentRegistry";
import { resolveEncounterId } from "../systems/progression/CampaignSelection";
import { nodeStatus, type NodeStatus } from "../systems/progression/CampaignReachability";
import { stepTarget, isWalkable, type Direction, type GridPosition } from "../systems/overworld/OverworldMovement";
import tilesetUrl from "../../assets/tilemaps/overworld_tileset.png";
import tilemapUrl from "../../assets/tilemaps/overworld.json?url";
import leaderDownUrl from "../../assets/sprites/heroes/warrior/down.png";
import leaderSideUrl from "../../assets/sprites/heroes/warrior/side.png";
import leaderUpUrl from "../../assets/sprites/heroes/warrior/up.png";
import propsUrl from "../../assets/sprites/overworld/props.png";

// The party leader shown on the overworld (the Deereater/warrior). Frames are
// authored at this size by tools/pixelart/heroes.py.
const HERO_FRAME_W = 20;
const HERO_FRAME_H = 24;

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
    const sheet = { frameWidth: HERO_FRAME_W, frameHeight: HERO_FRAME_H };
    if (!this.textures.exists("leader_down")) this.load.spritesheet("leader_down", leaderDownUrl, sheet);
    if (!this.textures.exists("leader_side")) this.load.spritesheet("leader_side", leaderSideUrl, sheet);
    if (!this.textures.exists("leader_up")) this.load.spritesheet("leader_up", leaderUpUrl, sheet);
    if (!this.textures.exists("ow_props")) this.load.spritesheet("ow_props", propsUrl, { frameWidth: 20, frameHeight: 24 });
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
    const spawnTile = { col: Math.floor(spawnObject.x! / TILE_SIZE), row: Math.floor(spawnObject.y! / TILE_SIZE) };
    this.decorate(map, ground, spawnTile);
    for (const marker of this.markers) this.drawMarker(profile, marker);

    // One 4-frame walk cycle per facing (down/side/up); left reuses side
    // flipped. Frame 0 of each is the standing pose.
    for (const facing of ["down", "side", "up"] as const) {
      if (!this.anims.exists(`leader_walk_${facing}`)) {
        this.anims.create({
          key: `leader_walk_${facing}`,
          frames: this.anims.generateFrameNumbers(`leader_${facing}`, { start: 0, end: 3 }),
          frameRate: 8,
          repeat: -1,
        });
      }
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

    this.player = this.add.sprite(0, 0, "leader_down", 0);
    // Frames are 20x24 with the figure ~22px tall (feet near the bottom).
    // Origin at the feet so the character stands on the tile centre, at
    // native scale -- ~1.4 tiles tall against 16px tiles, classic JRPG.
    this.player.setOrigin(0.5, 0.92);
    this.player.setDepth(5);
    this.snapPlayerToGrid();

    this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    this.cameras.main.startFollow(this.player, true, 1, 1);
    this.cameras.main.setRoundPixels(true);

    const keyboard = this.input.keyboard!;
    this.cursors = keyboard.createCursorKeys();
    this.wasd = keyboard.addKeys("W,A,S,D") as OverworldScene["wasd"];
    keyboard.on("keydown-ESC", () => this.scene.launch("SettingsOverlay", { returnTo: "OverworldScene" }));

    this.addAtmosphere();

    // HUD hint on a dark strip so it stays legible over the busy ground.
    this.add.rectangle(0, 0, this.scale.width, 12, 0x05060a, 0.72).setOrigin(0, 0).setScrollFactor(0).setDepth(19);
    this.add
      .text(4, 3, "Arrows/WASD: move   ESC: settings", { fontFamily: "monospace", fontSize: "7px", color: "#d8ceb6" })
      .setScrollFactor(0)
      .setDepth(20);
  }

  /**
   * A screen-space vignette (darkened edges) plus a faint cold overcast --
   * cheap, camera-locked, and the single biggest "this feels like a mood,
   * not a tech demo" win. Skipped under photosensitivity-safe mode.
   */
  private addAtmosphere(): void {
    if (GameContext.activeProfile?.settings.photosensitivitySafeMode) return;
    const { width, height } = this.scale;
    const g = this.add.graphics().setScrollFactor(0).setDepth(15);
    // cold overcast tint
    g.fillStyle(0x0b1420, 0.18).fillRect(0, 0, width, height);
    // vignette: nested translucent frames, darker toward the edge
    const steps = 10;
    for (let i = 0; i < steps; i++) {
      const t = i / steps;
      g.fillStyle(0x05060a, 0.06);
      const inset = Math.round((t * Math.min(width, height)) / 2.4);
      g.fillRect(0, 0, width, inset); // top
      g.fillRect(0, height - inset, width, inset); // bottom
      g.fillRect(0, 0, inset, height); // left
      g.fillRect(width - inset, 0, inset, height); // right
    }
  }

  update(): void {
    if (this.moving || !this.player) return;
    const dir = this.heldDirection();
    if (dir) this.tryStep(dir);
    else if (this.player.anims.isPlaying) {
      this.player.anims.stop();
      this.player.setFrame(0); // standing pose of whatever facing we last set
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
    // Point the sprite the way we're walking. Real per-facing art for
    // up/down/side (heroes.py); left is side flipped horizontally.
    this.faceDirection(dir);

    const target = stepTarget(this.playerPos, dir);
    if (!isWalkable(this.walkable, target)) return;

    this.moving = true;
    this.playerPos = target;
    const anim = `leader_walk_${this.facingKey(dir)}`;
    if (this.player.anims.getName() !== anim || !this.player.anims.isPlaying) this.player.play(anim);
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

  private facingKey(dir: Direction): "down" | "up" | "side" {
    if (dir === "up") return "up";
    if (dir === "down") return "down";
    return "side";
  }

  /** Sets the correct facing texture + flip without necessarily animating. */
  private faceDirection(dir: Direction): void {
    const key = this.facingKey(dir);
    this.player.setFlipX(dir === "left");
    if (this.player.texture.key !== `leader_${key}`) this.player.setTexture(`leader_${key}`, 0);
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

  /**
   * Dresses the map so it doesn't read as hard-cut tile blocks: a bright foam
   * line + dark bank wherever water meets land, and gothic props (bones,
   * tombstones, dead trees, fungus, reeds, obelisk shards) scattered
   * deterministically on grass, clear of node markers, the spawn, and the
   * road. Purely decorative -- props don't affect walkability.
   */
  private decorate(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer, spawnTile: GridPosition): void {
    const GRASS = 1;
    const WATER = 3;
    const keyOf = (c: number, r: number) => `${c},${r}`;
    const blocked = new Set<string>();
    for (const t of [...this.markers.map((m) => ({ col: m.col, row: m.row })), spawnTile]) {
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) blocked.add(keyOf(t.col + dc, t.row + dr));
    }

    const shore = this.add.graphics().setDepth(1);
    const FOAM = 0x9fe8e0;
    const BANK = 0x14384f;
    const isLand = (c: number, r: number) => {
      const n = ground.getTileAt(c, r)?.index;
      return n !== undefined && n !== WATER;
    };

    for (let row = 0; row < map.height; row++) {
      for (let col = 0; col < map.width; col++) {
        const idx = ground.getTileAt(col, row)?.index;
        const px = col * TILE_SIZE;
        const py = row * TILE_SIZE;
        if (idx === WATER) {
          if (isLand(col, row - 1)) shore.fillStyle(FOAM, 0.7).fillRect(px, py, TILE_SIZE, 1).fillStyle(BANK, 0.5).fillRect(px, py + 1, TILE_SIZE, 1);
          if (isLand(col, row + 1)) shore.fillStyle(FOAM, 0.55).fillRect(px, py + TILE_SIZE - 1, TILE_SIZE, 1);
          if (isLand(col - 1, row)) shore.fillStyle(FOAM, 0.5).fillRect(px, py, 1, TILE_SIZE);
          if (isLand(col + 1, row)) shore.fillStyle(FOAM, 0.5).fillRect(px + TILE_SIZE - 1, py, 1, TILE_SIZE);
        } else if (idx === GRASS && !blocked.has(keyOf(col, row))) {
          const h = ((col * 73856093) ^ (row * 19349663)) >>> 0;
          if (h % 100 < 11) {
            this.add.image(px + TILE_SIZE / 2, py + TILE_SIZE + 2, "ow_props", h % 6).setOrigin(0.5, 1).setDepth(2);
          }
        }
      }
    }
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
