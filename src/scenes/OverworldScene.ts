import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { campaign, getCampaignNode } from "../data/ContentRegistry";
import { resolveEncounterId } from "../systems/progression/CampaignSelection";
import { nodeStatus, type NodeStatus } from "../systems/progression/CampaignReachability";
import { stepTarget, isWalkable, type Direction, type GridPosition } from "../systems/overworld/OverworldMovement";
import tilesetUrl from "../../assets/tilemaps/overworld_tileset.png";
import tilemapUrl from "../../assets/tilemaps/overworld.json?url";
import propsUrl from "../../assets/sprites/overworld/props.png";
import { BASE_WIDTH, BASE_HEIGHT } from "../config/GameConfig";

const TILE_SIZE = 16;
const STEP_DURATION_MS = 160;
const MARKER_COLORS: Record<NodeStatus, number> = { cleared: 0x44cc66, unlocked: 0xffe066, locked: 0x444444 };
const NODE_TYPE_LABEL: Record<string, string> = { battle: "B", elite: "E", boss: "!", camp: "C" };

interface Marker {
  nodeId: string;
  col: number;
  row: number;
}

interface Echo {
  id: string;
  title: string;
  text: string;
  col: number;
  row: number;
}

// Decorative props (props.py PROPS, minus the reserved "echo_rune" marker
// appended last) are frames 0..DECORATIVE_PROP_COUNT-1 on the shared sheet;
// the echo marker is always the frame right after them.
const DECORATIVE_PROP_COUNT = 6;
const ECHO_RUNE_FRAME = DECORATIVE_PROP_COUNT;

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
  private echoes: Echo[] = [];
  private echoGlows = new Map<string, Phaser.GameObjects.Image>();
  private echoFoundIds = new Set<string>();
  private echoCountText!: Phaser.GameObjects.Text;
  private echoPanel: Phaser.GameObjects.Container | null = null;
  private nearbyEcho: Echo | null = null;
  private interactHint!: Phaser.GameObjects.Text;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private wasd!: Record<"W" | "A" | "S" | "D", Phaser.Input.Keyboard.Key>;
  private interactKey!: Phaser.Input.Keyboard.Key;
  private fog: Phaser.GameObjects.TileSprite | null = null;

  constructor() {
    super("OverworldScene");
  }

  preload(): void {
    // First scene-local preload in the codebase (BootScene only preloads
    // the shared hero portrait); guarded so a scene restart doesn't try to
    // re-register live cache keys.
    if (!this.textures.exists("overworld_tiles")) this.load.image("overworld_tiles", tilesetUrl);
    if (!this.cache.tilemap.exists("overworld")) this.load.tilemapTiledJSON("overworld", tilemapUrl);
    // The leader (Amir) and the old-hero NPC sprites are loaded centrally in
    // BootScene (band_* and hero_*); nothing hero-related to preload here.
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

    // Discoverable lore fragments scattered off the critical path (PRD
    // §8.8.2). Title/text/region are authored once, in the map data itself
    // (tools/overworld/generate_overworld_map.py), so the world and its
    // found-text can never drift apart.
    this.echoFoundIds = new Set(profile.echoesFound);
    this.echoes = (map.getObjectLayer("echoes")?.objects ?? []).map((o) => {
      const props = (o.properties as { name: string; value: string }[]) ?? [];
      const get = (name: string) => props.find((p) => p.name === name)?.value ?? "";
      return {
        id: o.name,
        title: get("title"),
        text: get("text"),
        col: Math.floor(o.x! / TILE_SIZE),
        row: Math.floor(o.y! / TILE_SIZE),
      };
    });

    this.decorate(map, ground, spawnTile);
    this.drawLandmarks();
    this.drawNpcs(spawnTile);
    for (const marker of this.markers) this.drawMarker(profile, marker);
    for (const echo of this.echoes) this.drawEcho(echo);

    // The party leader on the map is Amir, the band's guitarist (his real
    // hand-drawn art, tools/pixelart/bandmates.py). His sheets are side-facing
    // only, so one run cycle serves every direction (flipped for left); the
    // idle is his breathing stand. Frame counts are read off the loaded
    // textures so re-authoring the sheets can't desync the ranges.
    const lastFrame = (key: string) => this.textures.get(key).frameTotal - 2; // -1 for __BASE
    if (!this.anims.exists("leader_walk")) {
      this.anims.create({
        key: "leader_walk",
        frames: this.anims.generateFrameNumbers("band_amir_run", { start: 0, end: lastFrame("band_amir_run") }),
        frameRate: 12,
        repeat: -1,
      });
    }
    if (!this.anims.exists("leader_idle")) {
      this.anims.create({
        key: "leader_idle",
        frames: this.anims.generateFrameNumbers("band_amir", { start: 0, end: lastFrame("band_amir") }),
        frameRate: 5,
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

    this.player = this.add.sprite(0, 0, "band_amir", 0);
    // Amir's frames are 48x48 with the figure ~37px tall; scaled to ~0.52 he
    // stands ~1.2 tiles against the 16px tiles (feet-anchored so he sits on
    // the tile centre). Idle breathes until the player moves.
    this.player.setOrigin(0.5, 0.9).setScale(0.52);
    this.player.setDepth(5);
    this.player.play("leader_idle");
    this.snapPlayerToGrid();

    this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    this.cameras.main.startFollow(this.player, true, 1, 1);
    this.cameras.main.setRoundPixels(true);

    const keyboard = this.input.keyboard!;
    this.cursors = keyboard.createCursorKeys();
    this.wasd = keyboard.addKeys("W,A,S,D") as OverworldScene["wasd"];
    this.interactKey = keyboard.addKey("E");
    keyboard.on("keydown-ESC", () => this.scene.launch("SettingsOverlay", { returnTo: "OverworldScene" }));

    this.addAtmosphere();

    // HUD hint on a dark strip so it stays legible over the busy ground.
    this.add.rectangle(0, 0, this.scale.width, 12, 0x05060a, 0.72).setOrigin(0, 0).setScrollFactor(0).setDepth(19);
    this.add
      .text(4, 3, "Arrows/WASD: move   E: interact   ESC: settings", { fontFamily: "monospace", fontSize: "7px", color: "#d8ceb6" })
      .setScrollFactor(0)
      .setDepth(20);
    this.echoCountText = this.add
      .text(BASE_WIDTH - 4, 3, "", { fontFamily: "monospace", fontSize: "7px", color: "#49c6bd" })
      .setOrigin(1, 0)
      .setScrollFactor(0)
      .setDepth(20);
    this.updateEchoCountText();

    // A quiet prompt near the player, shown only when an undiscovered echo is close.
    this.interactHint = this.add
      .text(0, 0, "E: read", { fontFamily: "monospace", fontSize: "7px", color: "#f4d27a", stroke: "#05060a", strokeThickness: 3 })
      .setOrigin(0.5, 1)
      .setDepth(21)
      .setVisible(false);
  }

  private updateEchoCountText(): void {
    this.echoCountText.setText(`Echoes ${this.echoFoundIds.size}/${this.echoes.length}`);
  }

  /**
   * A screen-space vignette (darkened edges) plus a faint cold overcast --
   * cheap, camera-locked, and the single biggest "this feels like a mood,
   * not a tech demo" win. Skipped under photosensitivity-safe mode.
   */
  private addAtmosphere(): void {
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const safe = Boolean(GameContext.activeProfile?.settings.photosensitivitySafeMode);
    const { width, height } = this.scale;

    if (!safe) {
      // Drifting fog: a seamless haze tile scrolled slowly over the world for
      // depth. Screen-locked and additive at low alpha so it reads as light
      // haze, never a grey wash. Held still (just present) under reduced motion.
      this.fog = this.add
        .tileSprite(0, 0, width, height, "fx_haze")
        .setOrigin(0, 0)
        .setScrollFactor(0)
        .setDepth(13)
        .setBlendMode(Phaser.BlendModes.SCREEN)
        .setAlpha(reduced ? 0.05 : 0.1);

      // Raking god-ray shafts across the top -- additive, faint, evocative of
      // light falling through a drowned sky. Skipped under reduced motion.
      if (!reduced) {
        const rays = this.add
          .image(width / 2, 0, "fx_godray")
          .setOrigin(0.5, 0)
          .setScrollFactor(0)
          .setDepth(14)
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(0x9fe8e0)
          .setAlpha(0.22)
          .setDisplaySize(width * 1.2, height);
        this.tweens.add({ targets: rays, alpha: 0.34, duration: 4200, yoyo: true, repeat: -1, ease: "Sine.inOut" });
      }
    }

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
    if (!this.player) return;
    if (this.fog && !GameContext.activeProfile?.settings.reducedMotion) {
      this.fog.tilePositionX += 0.08;
      this.fog.tilePositionY -= 0.03;
    }
    this.updateNearbyEcho();
    if (Phaser.Input.Keyboard.JustDown(this.interactKey) && this.nearbyEcho && !this.echoPanel) {
      this.discoverEcho(this.nearbyEcho);
    }
    if (this.moving) return;
    const dir = this.heldDirection();
    if (dir) this.tryStep(dir);
    else if (this.player.anims.getName() !== "leader_idle") {
      this.player.play("leader_idle"); // drop back to the breathing stand
    }
  }

  /** Finds the closest undiscovered echo within one tile of the player and shows/hides the "E: read" prompt. */
  private updateNearbyEcho(): void {
    this.nearbyEcho =
      this.echoes.find(
        (e) => !this.echoFoundIds.has(e.id) && Math.abs(e.col - this.playerPos.col) <= 1 && Math.abs(e.row - this.playerPos.row) <= 1
      ) ?? null;
    if (this.nearbyEcho) {
      this.interactHint.setPosition(this.nearbyEcho.col * TILE_SIZE + TILE_SIZE / 2, this.nearbyEcho.row * TILE_SIZE - 4).setVisible(true);
    } else {
      this.interactHint.setVisible(false);
    }
  }

  /**
   * Marks an echo found, persists it to the save (so it stays found across
   * sessions -- PRD §8.8.2), and shows its one-line fragment in a framed
   * panel until the player dismisses it or walks away.
   */
  private discoverEcho(echo: Echo): void {
    const profile = GameContext.activeProfile;
    if (!profile) return;
    if (!this.echoFoundIds.has(echo.id)) {
      this.echoFoundIds.add(echo.id);
      profile.echoesFound.push(echo.id);
      void GameContext.persistActiveProfile();
      GameContext.analytics.track("echo_found", { echoId: echo.id });
      this.updateEchoCountText();
      const glow = this.echoGlows.get(echo.id);
      if (glow) {
        this.tweens.killTweensOf(glow);
        glow.setScale(0.3).setAlpha(0.12);
      }
    }
    this.showEchoPanel(echo);
  }

  private showEchoPanel(echo: Echo): void {
    this.echoPanel?.destroy();
    const panelW = Math.min(BASE_WIDTH - 24, 220);
    const panel = this.add.nineslice(0, 0, "ui_panel", undefined, panelW, 40, 5, 5, 5, 5);
    const title = this.add
      .text(0, -12, echo.title.toUpperCase(), { fontFamily: "monospace", fontSize: "7px", color: "#f4d27a" })
      .setOrigin(0.5, 0.5);
    const body = this.add
      .text(0, 2, echo.text, { fontFamily: "monospace", fontSize: "7px", color: "#e8e2d4", align: "center", wordWrap: { width: panelW - 16 } })
      .setOrigin(0.5, 0);
    this.echoPanel = this.add
      .container(BASE_WIDTH / 2, BASE_HEIGHT - 30, [panel, title, body])
      .setScrollFactor(0)
      .setDepth(25);
    this.time.delayedCall(3800, () => this.dismissEchoPanel());
  }

  private dismissEchoPanel(): void {
    this.echoPanel?.destroy();
    this.echoPanel = null;
  }

  /** Grid position test seam, read via the DEV-only __meterfallDebug hook. */
  getPlayerGridPosition(): GridPosition {
    return { ...this.playerPos };
  }

  /** Test seam: a node marker's tile position, so e2e specs never have to hardcode map coordinates. */
  getMarkerGridPosition(nodeId: string): GridPosition {
    const marker = this.markers.find((m) => m.nodeId === nodeId);
    if (!marker) throw new Error(`No overworld marker for node "${nodeId}"`);
    return { col: marker.col, row: marker.row };
  }

  /** Test seam: total map row count, so e2e specs never have to hardcode map dimensions. */
  getMapRowCount(): number {
    return this.walkable.length;
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
    // Amir's art is side-facing; face the walk direction (flip for left) and
    // run the one walk cycle for every direction.
    this.faceDirection(dir);

    const target = stepTarget(this.playerPos, dir);
    if (!isWalkable(this.walkable, target)) return;

    this.moving = true;
    this.playerPos = target;
    if (this.player.anims.getName() !== "leader_walk" || !this.player.anims.isPlaying) this.player.play("leader_walk");
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

  /** Flips Amir to face the walk direction. Only horizontal moves change the
   * flip; up/down keep the last-faced side (his art is side-only). */
  private faceDirection(dir: Direction): void {
    if (dir === "left") this.player.setFlipX(true);
    else if (dir === "right") this.player.setFlipX(false);
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
    this.scene.start("ActionBattleScene"); // v6.0 real-time combat
  }

  /**
   * Dresses the map so it doesn't read as hard-cut tile blocks: a bright foam
   * line + dark bank wherever water meets land, and gothic props (bones,
   * tombstones, dead trees, fungus, reeds, obelisk shards) scattered
   * deterministically on grass, clear of node markers, the spawn, and the
   * road. Purely decorative -- props don't affect walkability.
   */
  private decorate(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer, spawnTile: GridPosition): void {
    // Every region contributes 4 tiles (grass/path/water/rock, in that
    // order -- tools/pixelart/tiles.py region_tiles) at GID region*4+local+1,
    // so the local kind is always (gid-1) % 4 regardless of which of the
    // five regions a tile belongs to (tools/overworld/generate_overworld_map.py).
    const localKind = (gid: number) => (gid - 1) % 4;
    const isWaterGid = (gid: number | undefined) => gid !== undefined && localKind(gid) === 2;
    const isGrassGid = (gid: number | undefined) => gid !== undefined && localKind(gid) === 0;

    const keyOf = (c: number, r: number) => `${c},${r}`;
    const blocked = new Set<string>();
    for (const t of [
      ...this.markers.map((m) => ({ col: m.col, row: m.row })),
      ...this.echoes.map((e) => ({ col: e.col, row: e.row })),
      spawnTile,
    ]) {
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) blocked.add(keyOf(t.col + dc, t.row + dr));
    }

    const shore = this.add.graphics().setDepth(1);
    const FOAM = 0x9fe8e0;
    const BANK = 0x14384f;
    const isLand = (c: number, r: number) => {
      const n = ground.getTileAt(c, r)?.index;
      return n !== undefined && !isWaterGid(n);
    };

    for (let row = 0; row < map.height; row++) {
      for (let col = 0; col < map.width; col++) {
        const idx = ground.getTileAt(col, row)?.index;
        const px = col * TILE_SIZE;
        const py = row * TILE_SIZE;
        if (isWaterGid(idx)) {
          if (isLand(col, row - 1)) shore.fillStyle(FOAM, 0.7).fillRect(px, py, TILE_SIZE, 1).fillStyle(BANK, 0.5).fillRect(px, py + 1, TILE_SIZE, 1);
          if (isLand(col, row + 1)) shore.fillStyle(FOAM, 0.55).fillRect(px, py + TILE_SIZE - 1, TILE_SIZE, 1);
          if (isLand(col - 1, row)) shore.fillStyle(FOAM, 0.5).fillRect(px, py, 1, TILE_SIZE);
          if (isLand(col + 1, row)) shore.fillStyle(FOAM, 0.5).fillRect(px + TILE_SIZE - 1, py, 1, TILE_SIZE);
        } else if (isGrassGid(idx) && !blocked.has(keyOf(col, row))) {
          const h = ((col * 73856093) ^ (row * 19349663)) >>> 0;
          if (h % 100 < 11) {
            const cx = px + TILE_SIZE / 2;
            const cy = py + TILE_SIZE + 2;
            shore.fillStyle(0x05060a, 0.28).fillEllipse(cx, cy - 1, 12, 4); // contact shadow
            this.add.image(cx, cy, "ow_props", h % DECORATIVE_PROP_COUNT).setOrigin(0.5, 1).setDepth(2);
          }
        }
      }
    }
  }

  /**
   * One colossal set-piece per region (landmarks.py) placed off the road for
   * scale + untold story (PRD §8.8.1): the drowned ship, salt headframe,
   * carnival wheel, leaning tenement, and the Conductor's spire. Frame index
   * == region index. Drawn behind gameplay with a soft contact shadow, big
   * enough to tower over the 16px tiles.
   */
  private drawLandmarks(): void {
    // (regionIndex, col, row) -- edge-of-region scenic spots clear of the road.
    const spots: [number, number, number][] = [
      [0, 21, 6],   // shallows: wrecked ship by the bay
      [1, 44, 7],   // salt mines: winding headframe
      [2, 66, 28],  // pit: drowned carnival wheel
      [3, 90, 7],   // attic: leaning tenement
      [4, 120, 27], // hall: the Conductor's spire
    ];
    for (const [frame, col, row] of spots) {
      const x = col * TILE_SIZE + TILE_SIZE / 2;
      const y = row * TILE_SIZE + TILE_SIZE;
      this.add.ellipse(x, y, 44, 12, 0x05060a, 0.4).setDepth(0); // grounding shadow
      this.add.image(x, y, "ow_landmarks", frame).setOrigin(0.5, 1).setScale(2.2).setDepth(1);
    }
  }

  /**
   * The four generated pre-band adventurers (warrior/tank/mage/healer) now
   * live in the world as NPCs -- bystanders near the shore, not the party.
   * Placed on the nearest walkable grass to a few offsets from spawn, each
   * with a slow idle bob so they read as alive, but no interaction in v1.
   */
  private drawNpcs(spawnTile: GridPosition): void {
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const npcs: { key: string; dc: number; dr: number }[] = [
      { key: "hero_tank", dc: 4, dr: -3 },
      { key: "hero_mage", dc: 7, dr: -1 },
      { key: "hero_healer", dc: 5, dr: 3 },
      { key: "hero_warrior", dc: 9, dr: 2 },
    ];
    for (const npc of npcs) {
      const col = spawnTile.col + npc.dc;
      const row = spawnTile.row + npc.dr;
      if (!isWalkable(this.walkable, { col, row })) continue;
      const x = col * TILE_SIZE + TILE_SIZE / 2;
      const y = row * TILE_SIZE + TILE_SIZE / 2;
      this.add.ellipse(x, y + 2, 12, 5, 0x05060a, 0.35).setDepth(2); // contact shadow
      const s = this.add.sprite(x, y, npc.key, 0).setOrigin(0.5, 0.9).setDepth(3);
      s.setFlipX((col + row) % 2 === 0);
      if (!reduced) {
        this.tweens.add({ targets: s, y: y - 1, duration: 1100 + (col * 37) % 400, yoyo: true, repeat: -1, ease: "Sine.inOut" });
      }
    }
  }

  /** Draws an undiscovered echo's rune + a soft additive glow pulse (found ones stay marked but dim). */
  private drawEcho(echo: Echo): void {
    const x = echo.col * TILE_SIZE + TILE_SIZE / 2;
    const y = echo.row * TILE_SIZE + TILE_SIZE / 2;
    const found = this.echoFoundIds.has(echo.id);
    this.add.image(x, y, "ow_props", ECHO_RUNE_FRAME).setOrigin(0.5, 1).setDepth(2).setAlpha(found ? 0.55 : 1);

    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const glow = this.add
      .image(x, y - 10, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0x49c6bd)
      .setScale(found ? 0.3 : 0.45)
      .setAlpha(found ? 0.12 : 0.4)
      .setDepth(2);
    this.echoGlows.set(echo.id, glow);
    if (!found && !reduced) {
      this.tweens.add({ targets: glow, scale: 0.6, alpha: 0.65, yoyo: true, repeat: -1, duration: 900 });
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
