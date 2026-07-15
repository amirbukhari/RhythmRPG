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
import dressingData from "../data/content/overworld/dressing.json";
import { worldScaleFor } from "./env/WorldScale";

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
const REGION_BIOMES = ["shallows", "saltmines", "pit", "attic", "hall"];

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
  /** Full-screen whisper of the local region's accent colour (updated per
   * frame from the camera's position) -- each region OWNS its light. */
  private regionGrade: Phaser.GameObjects.Rectangle | null = null;

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
      composeWorldVenue(
        this,
        marker.nodeId,
        marker.col * TILE_SIZE + TILE_SIZE / 2,
        marker.row * TILE_SIZE + TILE_SIZE / 2,
        // scale/placement audit: venue set pieces must stand on land (grass
        // or path) -- offsets that land in water/rock skip the piece. The
        // baked fight-ground clearing (paint_ground.py) counts as land even
        // where the tiles beneath are water (the boss ring bridges the lake).
        (x, y) => {
          const discR = marker.nodeId === "boss_1" ? 108 : 58; // matches paint_ground radii
          const ddx = x - marker.col * TILE_SIZE - TILE_SIZE / 2;
          const ddy = y - marker.row * TILE_SIZE - TILE_SIZE / 2;
          if (ddx * ddx + ddy * ddy < discR * discR) return true;
          const gid = ground.getTileAt(Math.floor(x / TILE_SIZE), Math.floor(y / TILE_SIZE))?.index;
          if (gid == null || gid <= 0) return false;
          const local = (gid - 1) % 4; // 0 grass 1 path 2 water 3 rock
          return local === 0 || local === 1;
        }
      );
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
          .setAlpha(0.3)
          .setDisplaySize(width * 1.2, height);
        this.tweens.add({ targets: rays, alpha: 0.46, duration: 4200, yoyo: true, repeat: -1, ease: "Sine.inOut" });

        // A second, DIAGONAL shaft slicing the whole scene (the HLD shot's
        // signature move): rotated, wider than the screen, slow sway.
        const slice = this.pinToScreen(this.add.image(width * 0.68, height * 0.4, "fx_godray"), width * 0.68, height * 0.4)
          .setDepth(14)
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(0xc8f0dc)
          .setAlpha(0.16)
          .setRotation(0.42)
          .setDisplaySize(width * 0.9, height * 2.2);
        this.tweens.add({ targets: slice, alpha: 0.26, rotation: 0.36, duration: 6400, yoyo: true, repeat: -1, ease: "Sine.inOut" });

        // Ambient light motes (the HLD comparison: their air is ALIVE) --
        // a dozen tiny additive specks drifting up-screen, screen-pinned so
        // they read wherever the camera is. Deterministic layout.
        for (let i = 0; i < 12; i++) {
          const mx = ((i * 73 + 29) % 100) / 100 * width;
          const my = ((i * 41 + 13) % 100) / 100 * height;
          const mote = this.pinToScreen(
            this.add.image(mx, my, "glow").setScale(0.05 + (i % 3) * 0.02),
            mx,
            my
          )
            .setDepth(13.5)
            .setBlendMode(Phaser.BlendModes.ADD)
            .setTint(i % 4 === 0 ? 0xf0c078 : 0x9fe8e0)
            .setAlpha(0);
          this.tweens.add({
            targets: mote,
            alpha: { from: 0, to: 0.35 + (i % 3) * 0.1 },
            duration: 1600 + i * 230,
            yoyo: true,
            repeat: -1,
            delay: i * 420,
            ease: "Sine.inOut",
          });
        }
      }
    }

    // (A foreground corner-foliage layer was tried here -- HLD's depth
    // trick -- but every canopy asset reads as an occluding sheet at frame
    // scale, not a fringe. The depth layering is carried by the canopy
    // overhangs in-world, the diagonal shaft, and the motes instead.)

    // per-region ambient grade: a low-alpha additive wash of the local
    // accent, tint updated as the camera crosses regions
    this.regionGrade = this.pinToScreen(
      this.add.rectangle(0, 0, width, height, 0xffffff, 0.05).setOrigin(0, 0),
      0,
      0
    )
      .setBlendMode(Phaser.BlendModes.ADD)
      .setDepth(12.5) as Phaser.GameObjects.Rectangle;

    const g = this.pinToScreen(this.add.graphics().setDepth(15), 0, 0);
    // cold overcast tint
    g.fillStyle(0x0b1420, 0.06).fillRect(0, 0, width, height);
    // vignette: nested translucent frames, darker toward the edge
    const steps = 10;
    for (let i = 0; i < steps; i++) {
      const t = i / steps;
      g.fillStyle(0x05060a, 0.06);
      const inset = Math.round((t * Math.min(width, height)) / 4.6);
      g.fillRect(0, 0, width, inset); // top
      g.fillRect(0, height - inset, width, inset); // bottom
      g.fillRect(0, 0, inset, height); // left
      g.fillRect(width - inset, 0, inset, height); // right
    }
  }

  update(_time: number, deltaMs: number): void {
    if (!this.player) return;
    this.repositionPinned();
    if (this.regionGrade) {
      const ACCENTS = [0x49c6bd, 0xf0a648, 0x9a5cbd, 0xc25424, 0x7a4eb4];
      const ri = Math.min(4, Math.max(0, Math.floor(this.cameras.main.midPoint.x / (26 * TILE_SIZE))));
      this.regionGrade.fillColor = ACCENTS[ri];
    }
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
        // the trampled fight-ground clearing is BAKED into the painted plate
        // at every node (paint_ground.py), so this circle is always fightable
        // even where the map tiles underneath are water/rock -- every fight
        // gets a real room that IS the world, not an overlay
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

    void isGrassGid;
    void spawnTile;
    const shore = this.add.graphics().setDepth(1);

    // Every prop in the world is placed BY HAND (owner: "items need to be
    // placed with intention. none of this scattering shit") -- authored
    // vignettes, singletons, and landmark landforms in dressing.json. The
    // hash-scatter system is deleted.
    this.placeAuthoredDressing(shore);
    this.placeRegionGates(map, ground, shore);
    this.addLivingDetail(map, ground);
  }

  /**
   * The world moves (the HLD bar: their air is alive; ours must be MORE so):
   * teal glints pulse on open water and every canopy crown sways. All of it
   * deterministic and skipped under reduced motion.
   */
  private addLivingDetail(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer): void {
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    if (reduced) return;
    // water glints: sparse hash-picked open-water tiles get a slow pulse
    for (let row = 2; row < map.height - 2; row++) {
      for (let col = 2; col < map.width - 2; col++) {
        const gid = ground.getTileAt(col, row)?.index;
        if (gid == null || (gid - 1) % 4 !== 2) continue;
        const h = ((col * 40503) ^ (row * 2654435761)) >>> 0;
        if (h % 100 >= 4) continue;
        const gx = col * TILE_SIZE + ((h >> 5) % TILE_SIZE);
        const gy = row * TILE_SIZE + ((h >> 9) % TILE_SIZE);
        const glint = this.add
          .image(gx, gy, "glow")
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(0x9fe8e0)
          .setScale(0.06)
          .setAlpha(0)
          .setDepth(1.2);
        this.tweens.add({
          targets: glint,
          alpha: { from: 0, to: 0.4 },
          scaleX: 0.1,
          duration: 1800 + (h % 1400),
          yoyo: true,
          repeat: -1,
          delay: h % 2600,
          ease: "Sine.inOut",
        });
      }
    }
    // canopy sway: every overhanging crown breathes
    for (const c of this.canopies) {
      this.tweens.add({
        targets: c,
        angle: (c.x + c.y) % 2 === 0 ? 1.3 : -1.2,
        duration: 4200 + ((c.x * 7 + c.y * 13) % 1800),
        yoyo: true,
        repeat: -1,
        ease: "Sine.inOut",
      });
    }
  }

  /**
   * Authored set-dressing: composed mini-scenes (a fled camp, a shrine, a
   * wrecked cart) where every piece has a story reason to be where it is,
   * plus lone singletons and landmark landforms. Data-driven from
   * dressing.json; each piece appears at most twice per region, so the art
   * library reads as a world, not a repeating texture.
   */
  private placeAuthoredDressing(shore: Phaser.GameObjects.Graphics): void {
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const file = dressingData as {
      regions: {
        region: string;
        placements: { vignette: string; key: string; col: number; row: number; dx: number; dy: number; scale: number; flip: boolean }[];
      }[];
    };
    for (const region of file.regions) {
      const ri = REGION_BIOMES.indexOf(region.region);
      if (ri < 0) continue;
      const base = ri * 26;
      for (const p of region.placements) {
        if (!this.textures.exists(p.key)) continue;
        const x = (base + p.col) * TILE_SIZE + TILE_SIZE / 2 + p.dx;
        const y = p.row * TILE_SIZE + TILE_SIZE + p.dy;
        const canopy = /landform_canopy/.test(p.key);
        const landform = /landform_/.test(p.key);
        shore
          .fillStyle(0x05060a, landform ? 0.3 : 0.28)
          .fillEllipse(x, y - 2, landform ? (canopy ? 34 : 46) : 12, landform ? 10 : 4);
        // canonical world scale wins over the authored value (one unit for
        // the whole world -- a chair can never outgrow a building again)
        const scale = worldScaleFor(p.key, this.textures.get(p.key).getSourceImage().height) ?? p.scale;
        const img = this.add
          .image(x, y, p.key)
          .setOrigin(0.5, 1)
          .setScale(scale)
          .setFlipX(p.flip)
          .setTint(0xd6dce6)
          .setDepth(canopy ? 6.5 : landform ? 2.5 : 2);
        if (canopy) this.canopies.push(img);
        // emissive pieces cast their light -- the night world reads lit
        if (/lantern|crystal|tidepool|brazier|candle|torch|dockpost|votives|belljar|lamp$|geode|hourglass|campfire/.test(p.key)) {
          const teal = /tidepool|belljar|dockpost/.test(p.key);
          const tint = teal ? 0x49c6bd : 0xf0a648;
          this.add
            .image(x, y - 6, "glow")
            .setBlendMode(Phaser.BlendModes.ADD)
            .setTint(tint)
            .setScale(0.4)
            .setAlpha(0.32)
            .setDepth(2.1);
          // fireflies: 2-3 sparks orbit every flame (alive, not decorated).
          // Deterministic per position; skipped under reduced motion.
          if (!reduced) {
            const h = ((p.col * 92821) ^ (p.row * 68917)) >>> 0;
            for (let i = 0; i < 2 + (h % 2); i++) {
              const spark = this.add
                .image(x + ((h >> (i * 4)) % 9) - 4, y - 8 - ((h >> (i * 3)) % 6), "glow")
                .setBlendMode(Phaser.BlendModes.ADD)
                .setTint(tint)
                .setScale(0.05)
                .setAlpha(0)
                .setDepth(5.5);
              this.tweens.add({
                targets: spark,
                y: spark.y - 7 - (i * 3),
                x: spark.x + (i % 2 === 0 ? 3 : -3),
                alpha: { from: 0, to: 0.5 },
                duration: 1500 + ((h >> i) % 900),
                yoyo: true,
                repeat: -1,
                delay: i * 520 + (h % 400),
                ease: "Sine.inOut",
              });
            }
          }
        }
      }
    }
  }

  /**
   * Region-entry vistas (goal: intentional): where the main road crosses a
   * region boundary, the NEXT region announces itself -- its most iconic
   * landform stands north of the road and one of its lit props flanks the
   * south side, so every border crossing reads as a composed gateway instead
   * of a tint change.
   */
  private placeRegionGates(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer, shore: Phaser.GameObjects.Graphics): void {
    const GATE_PROPS: Record<string, string> = {
      saltmines: "env_saltmines_scatter_lantern",
      pit: "env_pit_scatter_torch",
      attic: "env_attic_scatter_lamp",
      hall: "env_hall_scatter_candelabra",
    };
    for (let k = 1; k < REGION_BIOMES.length; k++) {
      const bcol = k * 26;
      const rows: number[] = [];
      for (let r = 1; r < map.height - 1; r++) {
        const gid = ground.getTileAt(bcol, r)?.index;
        if (gid != null && gid > 0 && (gid - 1) % 4 === 1) rows.push(r);
      }
      if (rows.length === 0) continue;
      const row = rows[Math.floor(rows.length / 2)];
      const biome = REGION_BIOMES[k];
      const gx = bcol * TILE_SIZE + TILE_SIZE / 2;
      const outcrop = `env_${biome}_landform_outcrop2`;
      if (this.textures.exists(outcrop)) {
        const oy = (row - 3) * TILE_SIZE;
        shore.fillStyle(0x05060a, 0.3).fillEllipse(gx, oy - 2, 42, 9);
        this.add.image(gx, oy, outcrop).setOrigin(0.5, 1).setScale(1).setDepth(2.5).setTint(0xd6dce6);
      }
      const prop = GATE_PROPS[biome];
      if (prop && this.textures.exists(prop)) {
        const py = (row + 4) * TILE_SIZE;
        const ps = worldScaleFor(prop, this.textures.get(prop).getSourceImage().height) ?? 0.7;
        shore.fillStyle(0x05060a, 0.28).fillEllipse(gx, py - 1, 12, 4);
        this.add.image(gx, py, prop).setOrigin(0.5, 1).setScale(ps).setDepth(2).setTint(0xd6dce6);
        this.add
          .image(gx, py - 8, "glow")
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(0xf0a648)
          .setScale(0.45)
          .setAlpha(0.38)
          .setDepth(2.1);
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
        .setAlpha(0.09);
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
      // 0.58: townsfolk stand a hair SHORTER than the 25px hero (audit:
      // at 0.72 they towered over the player and each other inconsistently)
      const s = this.add.sprite(x, y, "ow_npcs", npc.frame).setOrigin(0.5, 0.9).setScale(0.58).setDepth(3);
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
      // past the frontier: a dark, motionless silhouette waiting in the fog.
      // A faint additive accent rim behind it keeps the shade's hue identity
      // (design-audit-3: a flat black cutout read as a rendering bug, and
      // every locked foe looked the same).
      const rim = this.add
        .sprite(x, footY, tex, 0)
        .setOrigin(0.5, 1)
        .setScale((colossal ? 0.8 : 0.4) * 1.07)
        .setBlendMode(Phaser.BlendModes.ADD)
        .setTint(accent)
        .setAlpha(0.22)
        .setDepth(4.45);
      foe.setTint(0x232c40).setAlpha(0.95);
      this.nodeFoeVisuals.get(marker.nodeId)!.push(rim);
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
      this.add.image(x, y, "env_shared_save_obelisk").setOrigin(0.5, 1).setScale(1).setDepth(4);
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
