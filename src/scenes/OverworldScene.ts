import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { campaign, getCampaignNode, getEncounter } from "../data/ContentRegistry";
import { resolveEncounterId } from "../systems/progression/CampaignSelection";
import { nodeStatus, type NodeStatus } from "../systems/progression/CampaignReachability";
import { stepTarget, isWalkable, type Direction, type GridPosition } from "../systems/overworld/OverworldMovement";
import tilesetUrl from "../../assets/tilemaps/overworld_tileset.png";
import tilemapUrl from "../../assets/tilemaps/overworld.json?url";
import propsUrl from "../../assets/sprites/overworld/props.png";
import npcsUrl from "../../assets/sprites/overworld/npcs.png";
import { BASE_WIDTH, BASE_HEIGHT, RENDER_SCALE } from "../config/GameConfig";
import { music } from "../systems/audio/SongPlayer";
import { WorldFight } from "./overworld/WorldFight";
import { composeWorldVenue } from "./env/ArenaComposer";

const TILE_SIZE = 16;
const STEP_DURATION_MS = 160;
const MARKER_COLORS: Record<NodeStatus, number> = { cleared: 0x44cc66, unlocked: 0xffe066, locked: 0x444444 };
const NODE_TYPE_LABEL: Record<string, string> = { battle: "B", elite: "E", boss: "!", camp: "C" };
// Emissive accent per foe for its overworld aura (mirrors ActionBattleScene).
const FOE_ACCENT: Record<string, number> = {
  the_conductor: 0xf0a648,
  elite_wraith: 0x49c6bd,
  drifter: 0x9fe8e0,
  slime: 0x9aca43,
};

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
  private playerShadow!: Phaser.GameObjects.Ellipse;
  private playerGlow!: Phaser.GameObjects.Image;
  private playerPos: GridPosition = { col: 0, row: 0 };
  /** The rest of Inhalants walking with Amir (visual party, PRD §7.1). */
  private followers: { member: string; sprite: Phaser.GameObjects.Sprite; shadow: Phaser.GameObjects.Ellipse }[] = [];
  /** Recently vacated tiles, newest first; follower i walks history[i]. */
  private stepHistory: GridPosition[] = [];
  private moving = false;
  private walkable: boolean[][] = [];
  private markers: Marker[] = [];
  private echoes: Echo[] = [];
  private echoGlows = new Map<string, Phaser.GameObjects.Image>();
  private echoFoundIds = new Set<string>();
  private echoCountText!: Phaser.GameObjects.Text;
  private echoPanel: Phaser.GameObjects.Container | null = null;
  private nearbyEcho: Echo | null = null;
  private obelisks: { col: number; row: number; glow: Phaser.GameObjects.Image }[] = [];
  private nearbyObelisk: { col: number; row: number; glow: Phaser.GameObjects.Image } | null = null;
  /** Live in-world fight (areas-not-arenas); null while exploring. */
  private fight: WorldFight | null = null;
  /** Canopy landforms drawn ABOVE the player (PRD v7.15); they alpha-fade
   * when the player walks beneath so the map keeps its sense of height. */
  private canopies: Phaser.GameObjects.Image[] = [];
  /** Screen-space UI pinned to the camera's visible rect. Under the 2x
   * retina zoom (RENDER_SCALE) with a scrolled follow camera, Phaser's
   * scrollFactor-0 transform drifts, so UI is pinned to worldView per frame
   * instead -- deterministic under any zoom. */
  private pinned: { obj: Phaser.GameObjects.GameObject & { setPosition(x: number, y: number): unknown; active: boolean }; dx: number; dy: number }[] = [];
  /** The standing foe's visuals per node, hidden when its fight goes live. */
  private nodeFoeVisuals = new Map<string, Phaser.GameObjects.GameObject[]>();
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
    if (!this.textures.exists("ow_props")) this.load.spritesheet("ow_props", propsUrl, { frameWidth: 24, frameHeight: 32 });
    if (!this.textures.exists("ow_npcs")) this.load.spritesheet("ow_npcs", npcsUrl, { frameWidth: 32, frameHeight: 40 });
  }

  create(): void {
    const profile = GameContext.activeProfile;
    if (!profile) {
      this.scene.start("SaveScene");
      return;
    }

    this.moving = false;
    this.obelisks = [];
    this.fight = null;
    this.canopies = [];
    this.pinned = [];
    this.nodeFoeVisuals.clear();
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      this.fight?.destroy();
      this.fight = null;
    });
    music.setVolume(profile.settings.volumeMusic);
    music.setMode("explore");
    music.start();

    const map = this.make.tilemap({ key: "overworld" });
    const tileset = map.addTilesetImage("overworld_tileset", "overworld_tiles")!;
    const ground = map.createLayer("ground", tileset, 0, 0)!;
    // Design-audit-2 G1-G4: the ground is PAINTED, not stamped. The tile
    // layer stays authoritative for collision/terrain queries but its render
    // is replaced by the offline-painted plate (tools/overworld/paint_ground.py,
    // 2x texel density; rock as mesas, roads as ribbons, water as bodies) so
    // the ground lives in the same register as the AI-painted sprites.
    ground.setVisible(false);
    this.add.image(0, 0, "ground_plate").setOrigin(0).setScale(0.5).setDepth(0);

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
    this.softenSeamsAndDapple(map);
    this.drawLandmarks();
    this.drawNpcs(spawnTile);
    // each fight node's authored venue -- its biome floor blended into the
    // map + its kitbash set pieces -- stands IN the world, under the foe
    for (const marker of this.markers) {
      composeWorldVenue(this, marker.nodeId, marker.col * TILE_SIZE + TILE_SIZE / 2, marker.row * TILE_SIZE + TILE_SIZE / 2);
    }
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

    // Contact shadow grounds Amir like the props/foes around him, and a soft
    // teal under-glow lifts the playable characters a value step above the
    // scenery (AAA audit O4) so the eye finds them in the dark world.
    this.playerShadow = this.add.ellipse(0, 0, 13, 4, 0x05060a, 0.4).setDepth(4.4);
    this.playerGlow = this.add
      .image(0, 0, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0x49c6bd)
      .setScale(0.32)
      .setAlpha(0.2)
      .setDepth(4.35);
    this.player = this.add.sprite(0, 0, "band_amir", 0);
    // Amir's frames are 48x48 with the figure ~37px tall; scaled to ~0.52 he
    // stands ~1.2 tiles against the 16px tiles (feet-anchored so he sits on
    // the tile centre). Idle breathes until the player moves.
    this.player.setOrigin(0.5, 0.9).setScale(0.35);
    this.player.setDepth(5);
    this.player.play("leader_idle");
    this.snapPlayerToGrid();

    // The rest of the band walks with Amir: bassist, vocalist, drummer trail
    // him in a line (visual party -- the whole point is that Inhalants are the
    // main characters, PRD §7.1). Followers are decorative: they never block
    // tiles or trigger anything.
    this.followers = [];
    this.stepHistory = [];
    for (const member of ["bassist", "vocalist", "drummer"]) {
      const idleKey = `bm_idle_${member}`;
      const walkKey = `bm_walk_${member}`;
      if (this.textures.exists(`band_${member}`) && !this.anims.exists(idleKey)) {
        this.anims.create({ key: idleKey, frames: this.anims.generateFrameNumbers(`band_${member}`, { start: 0, end: lastFrame(`band_${member}`) }), frameRate: 4, repeat: -1 });
        this.anims.create({ key: walkKey, frames: this.anims.generateFrameNumbers(`band_${member}_run`, { start: 0, end: lastFrame(`band_${member}_run`) }), frameRate: 10, repeat: -1 });
      }
      if (!this.textures.exists(`band_${member}`)) continue;
      const shadow = this.add.ellipse(0, 0, 12, 4, 0x05060a, 0.35).setDepth(4.3);
      const sprite = this.add.sprite(0, 0, `band_${member}`, 0).setOrigin(0.5, 0.9).setScale(0.33).setDepth(4.6);
      sprite.play(idleKey);
      sprite.setPosition(this.playerPos.col * TILE_SIZE + TILE_SIZE / 2, this.playerPos.row * TILE_SIZE + TILE_SIZE / 2);
      this.followers.push({ member, sprite, shadow });
    }

    // Retina render (design-audit-3): the canvas is 2x; zooming the camera
    // keeps every world coordinate identical while art renders at its real
    // texel density (the follow camera centers, so no centerOn needed).
    this.cameras.main.setZoom(RENDER_SCALE);
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
    this.pinToScreen(this.add.rectangle(0, 0, BASE_WIDTH, 12, 0x05060a, 0.72).setOrigin(0, 0).setDepth(19), 0, 0);
    this.pinToScreen(
      this.add.text(4, 3, "Arrows/WASD: move   E: interact   ESC: settings", { fontFamily: "monospace", fontSize: "7px", color: "#d8ceb6" }).setDepth(20),
      4,
      3
    );
    this.echoCountText = this.pinToScreen(
      this.add.text(BASE_WIDTH - 4, 3, "", { fontFamily: "monospace", fontSize: "7px", color: "#49c6bd" }).setOrigin(1, 0).setDepth(20),
      BASE_WIDTH - 4,
      3
    );
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
    const width = BASE_WIDTH;
    const height = BASE_HEIGHT;

    if (!safe) {
      // Drifting fog: a seamless haze tile scrolled slowly over the world for
      // depth. Screen-locked and additive at low alpha so it reads as light
      // haze, never a grey wash. Held still (just present) under reduced motion.
      this.fog = this.pinToScreen(
        this.add.tileSprite(0, 0, width, height, "fx_haze").setOrigin(0, 0),
        0,
        0
      )
        .setDepth(13)
        .setBlendMode(Phaser.BlendModes.SCREEN)
        .setAlpha(reduced ? 0.05 : 0.1);

      // Raking god-ray shafts across the top -- additive, faint, evocative of
      // light falling through a drowned sky. Skipped under reduced motion.
      if (!reduced) {
        const rays = this.pinToScreen(this.add.image(width / 2, 0, "fx_godray").setOrigin(0.5, 0), width / 2, 0)
          .setDepth(14)
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(0x9fe8e0)
          .setAlpha(0.22)
          .setDisplaySize(width * 1.2, height);
        this.tweens.add({ targets: rays, alpha: 0.34, duration: 4200, yoyo: true, repeat: -1, ease: "Sine.inOut" });
      }
    }

    const g = this.pinToScreen(this.add.graphics().setDepth(15), 0, 0);
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

  update(_time: number, deltaMs: number): void {
    if (!this.player) return;
    this.repositionPinned();
    this.playerShadow.setPosition(this.player.x, this.player.y + 2);
    this.playerGlow.setPosition(this.player.x, this.player.y - 6);
    // Canopy overhangs go translucent while the player is beneath them (the
    // fade is legibility, not decoration -- kept under reduced motion). The
    // trigger zone is the sprite's real footprint, not a fixed radius.
    for (const c of this.canopies) {
      const d = Phaser.Math.Distance.Between(this.player.x, this.player.y, c.x, c.y - c.displayHeight * 0.5);
      const target = d < Math.max(42, c.displayWidth * 0.65) ? 0.35 : 1;
      c.alpha += (target - c.alpha) * Math.min(1, deltaMs / 120);
    }
    if (this.fight) {
      // a fight is live IN the world: the sim drives the player; tile
      // movement, interactions, and the conga line pause until it resolves
      if (!this.fight.update(deltaMs)) this.fight = null;
      return;
    }
    for (const f of this.followers) {
      f.shadow.setPosition(f.sprite.x, f.sprite.y + 2);
      // drop a follower back to its idle when it has stopped moving
      if (!this.tweens.isTweening(f.sprite) && f.sprite.anims.getName() !== `bm_idle_${f.member}`) {
        f.sprite.play(`bm_idle_${f.member}`);
      }
    }
    if (this.fog && !GameContext.activeProfile?.settings.reducedMotion) {
      this.fog.tilePositionX += 0.08;
      this.fog.tilePositionY -= 0.03;
    }
    this.updateNearbyEcho();
    if (Phaser.Input.Keyboard.JustDown(this.interactKey) && !this.echoPanel) {
      if (this.nearbyEcho) this.discoverEcho(this.nearbyEcho);
      else if (this.nearbyObelisk) this.restAtObelisk(this.nearbyObelisk);
    }
    if (this.moving) return;
    const dir = this.heldDirection();
    if (dir) this.tryStep(dir);
    else if (this.player.anims.getName() !== "leader_idle") {
      this.player.play("leader_idle"); // drop back to the breathing stand
    }
  }

  /** Finds the closest interactable within one tile of the player (an
   * undiscovered echo, else a save-obelisk) and points the "E:" prompt at it. */
  private updateNearbyEcho(): void {
    this.nearbyEcho =
      this.echoes.find(
        (e) => !this.echoFoundIds.has(e.id) && Math.abs(e.col - this.playerPos.col) <= 1 && Math.abs(e.row - this.playerPos.row) <= 1
      ) ?? null;
    this.nearbyObelisk =
      this.obelisks.find((o) => Math.abs(o.col - this.playerPos.col) <= 1 && Math.abs(o.row - this.playerPos.row) <= 1) ?? null;
    if (this.nearbyEcho) {
      this.interactHint
        .setText("E: read")
        .setPosition(this.nearbyEcho.col * TILE_SIZE + TILE_SIZE / 2, this.nearbyEcho.row * TILE_SIZE - 4)
        .setVisible(true);
    } else if (this.nearbyObelisk) {
      this.interactHint
        .setText("E: rest")
        .setPosition(this.nearbyObelisk.col * TILE_SIZE + TILE_SIZE / 2, this.nearbyObelisk.row * TILE_SIZE - 8)
        .setVisible(true);
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
    this.echoPanel = this.pinToScreen(
      this.add.container(BASE_WIDTH / 2, BASE_HEIGHT - 30, [panel, title, body]).setDepth(25),
      BASE_WIDTH / 2,
      BASE_HEIGHT - 30
    );
    this.repositionPinned();
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

    // the tile the leader vacates becomes the next follower waypoint
    this.stepHistory.unshift({ ...this.playerPos });
    if (this.stepHistory.length > 8) this.stepHistory.pop();

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
    this.stepFollowers();
  }

  /** Each bandmate walks to where the member ahead just was (conga line). */
  private stepFollowers(): void {
    this.followers.forEach((f, i) => {
      const spot = this.stepHistory[i];
      if (!spot) return;
      const tx = spot.col * TILE_SIZE + TILE_SIZE / 2;
      const ty = spot.row * TILE_SIZE + TILE_SIZE / 2;
      if (Math.abs(f.sprite.x - tx) < 0.5 && Math.abs(f.sprite.y - ty) < 0.5) return;
      // band art natively faces LEFT: flip when moving right
      if (tx > f.sprite.x) f.sprite.setFlipX(true);
      else if (tx < f.sprite.x) f.sprite.setFlipX(false);
      const walkKey = `bm_walk_${f.member}`;
      if (f.sprite.anims.getName() !== walkKey || !f.sprite.anims.isPlaying) f.sprite.play(walkKey);
      this.tweens.add({ targets: f.sprite, x: tx, y: ty, duration: STEP_DURATION_MS });
    });
  }

  /** Flips Amir to face the walk direction. Only horizontal moves change the
   * flip; up/down keep the last-faced side (his art is side-only). His
   * hand-drawn sheets natively face LEFT (see the run cycle's lean), so
   * moving right is the flipped side -- getting this backwards makes him
   * moonwalk everywhere. */
  private faceDirection(dir: Direction): void {
    if (dir === "left") this.player.setFlipX(false);
    else if (dir === "right") this.player.setFlipX(true);
  }

  /**
   * Walking onto an unlocked marker starts its fight IN PLACE (areas, not
   * arenas -- PRD §8.2 v7.6): the camera locks to a screen-sized room of the
   * actual world around the foe and the action sim runs right there. No
   * separate battle scene loads. Cleared and locked markers are walk-over
   * no-ops: cleared nodes sit on the road onward, and v1 has no re-fighting.
   */
  private checkEncounterTrigger(): void {
    const profile = GameContext.activeProfile;
    if (!profile || this.fight) return;
    const marker = this.markers.find((m) => m.col === this.playerPos.col && m.row === this.playerPos.row);
    if (!marker) return;
    if (nodeStatus(campaign, profile.campaignProgress, marker.nodeId) !== "unlocked") return;

    const encounterId = resolveEncounterId(getCampaignNode(marker.nodeId));
    if (!encounterId) return; // camp nodes have no encounter
    GameContext.pendingEncounterId = encounterId;
    GameContext.pendingNodeId = marker.nodeId;
    // the standing foe hands over to the live fight
    for (const o of this.nodeFoeVisuals.get(marker.nodeId) ?? []) (o as Phaser.GameObjects.Sprite).setVisible(false);
    const nodeX = marker.col * TILE_SIZE + TILE_SIZE / 2;
    const nodeY = marker.row * TILE_SIZE + TILE_SIZE / 2;
    this.fight = new WorldFight(
      {
        scene: this,
        playerSprite: this.player,
        // the venue floor (composeWorldVenue) covers the ground around the
        // node, so that circle is always fightable even where the map tiles
        // underneath are water/rock -- every fight gets a real room
        isWorldWalkable: (px, py) => {
          const dx = px - nodeX;
          const dy = py - nodeY;
          if (dx * dx + dy * dy < 64 * 64) return true;
          return isWalkable(this.walkable, { col: Math.floor(px / TILE_SIZE), row: Math.floor(py / TILE_SIZE) });
        },
      },
      marker.nodeId,
      encounterId,
      nodeX,
      nodeY
    );
  }

  /** Test seam: whether an in-world fight is currently live. */
  isFightActive(): boolean {
    return this.fight !== null;
  }

  /** Test seam: the live fight's sim arena (null while exploring). */
  getFightArena(): unknown {
    return this.fight?.simArena ?? null;
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

    // Shorelines, banks, and rock elevation are BAKED into the painted
    // ground plate (paint_ground.py) -- runtime decoration is now only the
    // prop scatter, with per-prop jitter so nothing sits on a perfect grid
    // (design-audit-2 G5).
    for (let row = 0; row < map.height; row++) {
      for (let col = 0; col < map.width; col++) {
        const idx = ground.getTileAt(col, row)?.index;
        const px = col * TILE_SIZE;
        const py = row * TILE_SIZE;
        if (isGrassGid(idx) && !blocked.has(keyOf(col, row))) {
          const h = ((col * 73856093) ^ (row * 19349663)) >>> 0;
          // CLUSTERED scatter (AAA audit O3): real places group -- graveyards,
          // reed banks, camps -- with clearings between. A low-frequency cell
          // hash decides where clusters live; density is high inside, near
          // zero outside.
          const cellH = ((((col >> 3) + 7) * 2654435761) ^ (((row >> 3) + 3) * 40503)) >>> 0;
          const chance = cellH % 100 < 28 ? 32 : 2;
          if (h % 100 < chance) {
            const cx = px + TILE_SIZE / 2 + (((h >> 5) % 11) - 5);
            const cy = py + TILE_SIZE + 2 + (((h >> 9) % 7) - 3);
            shore.fillStyle(0x05060a, 0.28).fillEllipse(cx, cy - 1, 12, 4); // contact shadow
            // scenery sits a value-step darker than characters (audit O4)
            this.add.image(cx, cy, "ow_props", h % DECORATIVE_PROP_COUNT).setOrigin(0.5, 1).setScale(0.72).setDepth(2).setTint(0xb2b9c6);
          }
        }
      }
    }

    this.placeLandforms(map, ground, shore, blocked, isGrassGid);
  }

  /**
   * LANDSCAPE-scale forms over the scene (PRD v7.15 direction: "giant rocks
   * and hills and trees over the scene, like Hyper Light Drifter"). Per
   * sparse low-frequency cell: either a colossal OUTCROP that breaks the map
   * silhouette (scenery layer, below the player) or a CANOPY tree whose
   * crown OVERHANGS the play space -- drawn ABOVE the player layer and
   * alpha-fading when the player walks beneath (the HLD height trick).
   * Deterministic (same hash discipline as prop clustering), kept clear of
   * markers/echoes/spawn and their venue circles.
   */
  private placeLandforms(
    map: Phaser.Tilemaps.Tilemap,
    ground: Phaser.Tilemaps.TilemapLayer,
    shadowLayer: Phaser.GameObjects.Graphics,
    blocked: Set<string>,
    isGrassGid: (gid: number | undefined) => boolean
  ): void {
    const REGION_BIOMES = ["shallows", "saltmines", "pit", "attic", "hall"];
    const REGION_W = 26; // tiles per region (generate_overworld_map.py)
    const CELL = 8;
    const clearOfLandmarks = (col: number, row: number): boolean => {
      for (const t of [...this.markers, ...this.echoes]) {
        if (Math.abs(t.col - col) <= 3 && Math.abs(t.row - row) <= 3) return false;
      }
      return true;
    };
    for (let cr = 0; cr * CELL < map.height; cr++) {
      for (let cc = 0; cc * CELL < map.width; cc++) {
        const ch = (((cc + 11) * 2654435761) ^ ((cr + 5) * 97002721)) >>> 0;
        const kind = ch % 100;
        if (kind >= 38) continue; // ~38% of cells attempt one landform
        // several jittered candidates per cell: a busy map (roads, water,
        // marker clearance) rejects most single throws
        let col = -1;
        let row = -1;
        for (let attempt = 0; attempt < 6; attempt++) {
          const c = cc * CELL + 1 + ((ch >> (4 + attempt * 3)) % Math.max(1, CELL - 2));
          const r = cr * CELL + 1 + ((ch >> (6 + attempt * 3)) % Math.max(1, CELL - 2));
          if (blocked.has(`${c},${r}`) || !clearOfLandmarks(c, r)) continue;
          if (!isGrassGid(ground.getTileAt(c, r)?.index)) continue;
          col = c;
          row = r;
          break;
        }
        if (col < 0) continue;
        const biome = REGION_BIOMES[Math.min(REGION_BIOMES.length - 1, Math.floor(col / REGION_W))];
        const canopy = kind < 16; // ~16% canopy, ~22% outcrop of cells
        const key = `env_${biome}_landform_${canopy ? "canopy" : "outcrop"}`;
        if (!this.textures.exists(key)) continue;
        const x = col * TILE_SIZE + TILE_SIZE / 2;
        const y = row * TILE_SIZE + TILE_SIZE;
        shadowLayer.fillStyle(0x05060a, 0.3).fillEllipse(x, y - 2, canopy ? 34 : 46, 10);
        const img = this.add.image(x, y, key).setOrigin(0.5, 1).setScale(0.8).setTint(0xb2b9c6);
        if (canopy) {
          img.setDepth(6.5); // above the player (5): the crown overhangs
          this.canopies.push(img);
        } else {
          img.setDepth(2.5);
        }
      }
    }
  }

  /**
   * Two cheap, static, world-space passes that kill the last "flat tilemap"
   * tells: (1) a soft cross-fade band at each region boundary so the five
   * moods bleed into one another instead of meeting on a razor-straight line;
   * (2) a large-scale shadow-dapple overlay (the fog texture, world-space,
   * dark, low alpha) so the repeated grass stamp dissolves under organic
   * light variation far larger than the 16px grid.
   */
  private softenSeamsAndDapple(map: Phaser.Tilemaps.Tilemap): void {
    // Region cross-fade is BAKED into the painted ground plate now
    // (paint_ground.py blends the region bases over a wide band); only the
    // organic shadow dapple remains a runtime layer.
    if (!GameContext.activeProfile?.settings.photosensitivitySafeMode) {
      // world-space shadow dapple: soft dark blobs, tiled large, breaking the grid
      this.add
        .tileSprite(0, 0, map.widthInPixels, map.heightInPixels, "fx_haze")
        .setOrigin(0, 0)
        .setDepth(1)
        .setTileScale(2.4)
        .setTint(0x05060a)
        .setAlpha(0.16);
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
      this.add.ellipse(x, y, 48, 12, 0x05060a, 0.4).setDepth(0); // grounding shadow
      this.add.image(x, y, "ow_landmarks", frame).setOrigin(0.5, 1).setScale(1.15).setDepth(1);
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
    // Real drowned-gothic townsfolk (ow_npcs: ferryman, widow, barker, chorister),
    // AI-generated, isolated pixel-art sprites (generate_ai.py).
    const npcs: { frame: number; dc: number; dr: number }[] = [
      { frame: 0, dc: 4, dr: -3 },
      { frame: 1, dc: 7, dr: -1 },
      { frame: 2, dc: 5, dr: 3 },
      { frame: 3, dc: 9, dr: 2 },
    ];
    for (const npc of npcs) {
      const col = spawnTile.col + npc.dc;
      const row = spawnTile.row + npc.dr;
      if (!isWalkable(this.walkable, { col, row })) continue;
      const x = col * TILE_SIZE + TILE_SIZE / 2;
      const y = row * TILE_SIZE + TILE_SIZE / 2;
      this.add.ellipse(x, y + 2, 14, 5, 0x05060a, 0.35).setDepth(2); // contact shadow
      const s = this.add.sprite(x, y, "ow_npcs", npc.frame).setOrigin(0.5, 0.9).setScale(0.72).setDepth(3);
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
    this.add.image(x, y, "ow_props", ECHO_RUNE_FRAME).setOrigin(0.5, 1).setScale(0.72).setDepth(2).setAlpha(found ? 0.55 : 1);

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

  /**
   * Areas, not arenas (PRD §8.2 v7.6): a fight node is not an abstract map
   * pin -- the foe itself STANDS in the world at its place, and the player
   * stumbles into it. Locked foes wait as dark silhouettes past the frontier;
   * cleared places keep only a faint released-soul ember. Camp nodes (no
   * encounter) keep the plain marker. Every fight node also gets a
   * save-obelisk placed on a nearby walkable tile (§8.8: rest + save before
   * the fight).
   */
  private drawMarker(profile: NonNullable<typeof GameContext.activeProfile>, marker: Marker): void {
    const status = nodeStatus(campaign, profile.campaignProgress, marker.nodeId);
    const x = marker.col * TILE_SIZE + TILE_SIZE / 2;
    const y = marker.row * TILE_SIZE + TILE_SIZE / 2;
    const node = getCampaignNode(marker.nodeId);
    const reduced = profile.settings.reducedMotion;

    // Representative foe: the first enemy of the node's first pool encounter.
    const encounterId = node.encounterPool?.[0];
    const foeId = encounterId ? getEncounter(encounterId).enemyWave[0] : null;

    if (!foeId) {
      // camp node: the old plain marker
      const circle = this.add.circle(x, y, 6, MARKER_COLORS[status]);
      this.add
        .text(x, y, NODE_TYPE_LABEL[node.type] ?? "?", { fontFamily: "monospace", fontSize: "7px", color: "#000000" })
        .setOrigin(0.5);
      if (status === "unlocked" && !reduced) {
        this.tweens.add({ targets: circle, scale: 1.25, yoyo: true, repeat: -1, duration: 500 });
      }
      return;
    }

    this.placeObelisk(marker);

    if (status === "cleared") {
      // the foe is gone; a released-soul ember marks where it stood
      const ember = this.add
        .image(x, y, "glow")
        .setBlendMode(Phaser.BlendModes.ADD)
        .setTint(0x49c6bd)
        .setScale(0.22)
        .setAlpha(0.22)
        .setDepth(2);
      if (!reduced) this.tweens.add({ targets: ember, alpha: 0.1, yoyo: true, repeat: -1, duration: 1600 });
      return;
    }

    const colossal = foeId === "the_conductor";
    const tex = colossal ? "conductor_colossal" : `enemy_${foeId}`;
    const accent = FOE_ACCENT[foeId] ?? 0xffffff;
    const footY = y + TILE_SIZE / 2 - 1;

    // contact shadow + emissive aura ground the foe in the world
    const foeShadow = this.add.ellipse(x, footY, colossal ? 30 : 20, colossal ? 9 : 6, 0x05060a, 0.4).setDepth(3);
    const aura = this.add
      .image(x, footY - 10, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(accent)
      .setScale(colossal ? 0.9 : 0.55)
      .setAlpha(status === "locked" ? 0.08 : 0.3)
      .setDepth(3);

    const foe = this.add.sprite(x, footY, tex, 0).setOrigin(0.5, 1).setScale(colossal ? 0.8 : 0.4).setDepth(4.5);
    // the live fight hides these when the player walks into the foe
    this.nodeFoeVisuals.set(marker.nodeId, [foe, aura, foeShadow]);
    if (status === "locked") {
      // past the frontier: a dark, motionless silhouette waiting in the fog
      foe.setTint(0x1a2230).setAlpha(0.9);
    } else {
      const animKey = `ow_foe_${tex}`;
      if (!this.anims.exists(animKey)) {
        this.anims.create({ key: animKey, frames: this.anims.generateFrameNumbers(tex, { start: 0, end: 1 }), frameRate: 1.6, repeat: -1 });
      }
      foe.play(animKey);
      if (!reduced) this.tweens.add({ targets: aura, alpha: 0.5, scale: aura.scale * 1.25, yoyo: true, repeat: -1, duration: 900 });
    }
  }

  /**
   * Places a save-obelisk on a walkable tile near a fight node (PRD §8.8:
   * rest + save before the fight). Two tiles out so standing beside the
   * obelisk never overlaps the fight-trigger tile itself.
   */
  private placeObelisk(marker: Marker): void {
    const candidates: GridPosition[] = [
      { col: marker.col - 2, row: marker.row },
      { col: marker.col + 2, row: marker.row },
      { col: marker.col, row: marker.row + 2 },
      { col: marker.col, row: marker.row - 2 },
      { col: marker.col - 2, row: marker.row + 1 },
      { col: marker.col + 2, row: marker.row + 1 },
    ];
    const spot = candidates.find(
      (c) => isWalkable(this.walkable, c) && !this.markers.some((m) => m.col === c.col && m.row === c.row)
    );
    if (!spot) return;
    const x = spot.col * TILE_SIZE + TILE_SIZE / 2;
    const y = spot.row * TILE_SIZE + TILE_SIZE - 1;
    this.add.ellipse(x, y, 16, 5, 0x05060a, 0.4).setDepth(3);
    const glow = this.add
      .image(x, y - 12, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0x49c6bd)
      .setScale(0.4)
      .setAlpha(0.35)
      .setDepth(3);
    if (this.textures.exists("env_shared_save_obelisk")) {
      this.add.image(x, y, "env_shared_save_obelisk").setOrigin(0.5, 1).setScale(0.34).setDepth(4);
    } else {
      // art not shipped yet: a simple standing stone so the save point still exists
      this.add.rectangle(x, y - 7, 6, 14, 0x2c3a4a).setDepth(4);
    }
    this.obelisks.push({ col: spot.col, row: spot.row, glow });
  }

  /** Rest at a save-obelisk: persist the save and acknowledge it in-world. */
  private restAtObelisk(obelisk: { col: number; row: number; glow: Phaser.GameObjects.Image }): void {
    void GameContext.persistActiveProfile();
    GameContext.analytics.track("obelisk_rest");
    if (!GameContext.activeProfile?.settings.reducedMotion) {
      this.tweens.add({ targets: obelisk.glow, alpha: 0.9, scale: 0.9, yoyo: true, duration: 350 });
    }
    this.showToast("THE CHORUS RESTS", "Progress saved.");
  }

  /** A small self-dismissing framed message (same visual family as the echo panel). */
  private showToast(title: string, body: string): void {
    this.echoPanel?.destroy();
    const panelW = 150;
    const panel = this.add.nineslice(0, 0, "ui_panel", undefined, panelW, 32, 5, 5, 5, 5);
    const t = this.add.text(0, -8, title, { fontFamily: "monospace", fontSize: "7px", color: "#49c6bd" }).setOrigin(0.5);
    const b = this.add.text(0, 4, body, { fontFamily: "monospace", fontSize: "7px", color: "#e8e2d4" }).setOrigin(0.5);
    this.echoPanel = this.pinToScreen(
      this.add.container(BASE_WIDTH / 2, BASE_HEIGHT - 26, [panel, t, b]).setDepth(25),
      BASE_WIDTH / 2,
      BASE_HEIGHT - 26
    );
    this.repositionPinned();
    this.time.delayedCall(2200, () => this.dismissEchoPanel());
  }

  /** Pin a UI object at a design-space offset from the camera's top-left. */
  pinToScreen<T extends Phaser.GameObjects.GameObject & { setPosition(x: number, y: number): unknown; active: boolean }>(
    obj: T,
    dx: number,
    dy: number
  ): T {
    this.pinned.push({ obj, dx, dy });
    return obj;
  }

  private repositionPinned(): void {
    const v = this.cameras.main.worldView;
    this.pinned = this.pinned.filter((p) => p.obj.active);
    for (const p of this.pinned) p.obj.setPosition(v.x + p.dx, v.y + p.dy);
  }

  private snapPlayerToGrid(): void {
    this.player.setPosition(this.playerPos.col * TILE_SIZE + TILE_SIZE / 2, this.playerPos.row * TILE_SIZE + TILE_SIZE / 2);
  }
}
